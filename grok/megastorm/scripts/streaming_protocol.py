"""Strict, descriptor-gated parsing for Grok streaming JSON.

The public Grok documentation does not currently define an event schema.  This
module therefore contains no descriptor claiming real-host conformance.  The
bundled descriptor is solely for deterministic fake-CLI tests.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping


class StreamingProtocolError(ValueError):
    """A fail-closed transport or protocol error with a stable classification."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class FixtureProvenance:
    source: str
    cli_version: str
    capture_command: tuple[str, ...]
    platform: str
    captured_at: str
    sha256: str


@dataclass(frozen=True)
class ProtocolDescriptor:
    descriptor_version: int
    dialect: str
    real_host_conformant: bool
    provenance: FixtureProvenance
    type_field: str
    id_field: str
    chunk_type: str
    chunk_text_field: str
    chunk_sequence_field: str
    tool_start_type: str
    tool_finish_type: str
    tool_id_field: str
    tool_status_field: str
    error_type: str
    error_message_field: str
    terminal_type: str
    terminal_status_field: str
    terminal_success_value: str

    def __post_init__(self) -> None:
        if self.descriptor_version < 1:
            raise ValueError("descriptor_version must be positive")
        if not self.dialect:
            raise ValueError("descriptor dialect must be non-empty")
        if self.provenance.source == "fake" and self.real_host_conformant:
            raise ValueError("a fake fixture cannot certify real-host conformance")
        if len(self.provenance.sha256) != 64 or any(
            character not in "0123456789abcdef" for character in self.provenance.sha256
        ):
            raise ValueError("fixture provenance requires a lowercase SHA-256")


FAKE_PROTOCOL_V1 = ProtocolDescriptor(
    descriptor_version=1,
    dialect="megastorm-fake-grok-stream-v1",
    real_host_conformant=False,
    provenance=FixtureProvenance(
        source="fake",
        cli_version="fake-test-double/1",
        capture_command=("fake-grok", "--output-format", "streaming-json"),
        platform="deterministic-test-fixture",
        captured_at="2026-07-18T00:00:00Z",
        sha256="0" * 64,
    ),
    type_field="type",
    id_field="id",
    chunk_type="assistant.chunk",
    chunk_text_field="text",
    chunk_sequence_field="sequence",
    tool_start_type="tool.start",
    tool_finish_type="tool.finish",
    tool_id_field="tool_call_id",
    tool_status_field="status",
    error_type="protocol.error",
    error_message_field="message",
    terminal_type="stream.terminal",
    terminal_status_field="status",
    terminal_success_value="success",
)


_ENVELOPE_SCHEMAS: dict[str, Mapping[str, Any]] = {
    "executor": {
        "type": "object",
        "required": ["kind", "status", "summary", "touched_paths"],
        "properties": {
            "kind": {"enum": ["executor"]},
            "status": {"enum": ["complete"]},
            "summary": {"type": "string", "minLength": 1},
            "touched_paths": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": True,
    },
    "supervisor": {
        "type": "object",
        "required": ["kind", "verdict", "summary"],
        "properties": {
            "kind": {"enum": ["supervisor"]},
            "verdict": {"enum": ["confirmed", "rejected"]},
            "summary": {"type": "string", "minLength": 1},
        },
        "additionalProperties": True,
    },
}


@dataclass(frozen=True)
class StreamingResult:
    envelope: Mapping[str, Any]
    chunks: tuple[str, ...]
    tool_events: tuple[Mapping[str, Any], ...]
    unknown_records: tuple[Mapping[str, Any], ...]
    terminal: Mapping[str, Any]
    exit_code: int


class StreamingParser:
    """Incrementally validate records, then finish with an exit status and role."""

    def __init__(self, descriptor: ProtocolDescriptor) -> None:
        self.descriptor = descriptor
        self._seen: dict[str, Mapping[str, Any]] = {}
        self._chunks: list[str] = []
        self._tool_events: list[Mapping[str, Any]] = []
        self._unknown: list[Mapping[str, Any]] = []
        self._open_tools: set[str] = set()
        self._terminal: Mapping[str, Any] | None = None
        self._next_chunk_sequence = 0

    def feed(self, record: Mapping[str, Any]) -> None:
        if self._terminal is not None:
            raise StreamingProtocolError("post_terminal", "record received after terminal")
        if not isinstance(record, dict):
            raise StreamingProtocolError("invalid_record", "event must be a JSON object")

        event_type = record.get(self.descriptor.type_field)
        if not isinstance(event_type, str) or not event_type:
            raise StreamingProtocolError("invalid_record", "event has no string type")

        known = event_type in {
            self.descriptor.chunk_type,
            self.descriptor.tool_start_type,
            self.descriptor.tool_finish_type,
            self.descriptor.error_type,
            self.descriptor.terminal_type,
        }
        if not known:
            self._unknown.append(dict(record))
            return

        event_id = record.get(self.descriptor.id_field)
        if not isinstance(event_id, str) or not event_id:
            raise StreamingProtocolError("invalid_event_id", "semantic event has no string id")
        previous = self._seen.get(event_id)
        if previous is not None:
            if previous == record:
                return
            raise StreamingProtocolError(
                "conflicting_duplicate", f"event id {event_id!r} has conflicting records"
            )
        self._seen[event_id] = dict(record)

        if event_type == self.descriptor.chunk_type:
            self._accept_chunk(record)
        elif event_type == self.descriptor.tool_start_type:
            self._accept_tool_start(record)
        elif event_type == self.descriptor.tool_finish_type:
            self._accept_tool_finish(record)
        elif event_type == self.descriptor.error_type:
            message = record.get(self.descriptor.error_message_field)
            safe_message = message if isinstance(message, str) else "unspecified protocol error"
            raise StreamingProtocolError("protocol_error", safe_message)
        else:
            self._accept_terminal(record)

    def _accept_chunk(self, record: Mapping[str, Any]) -> None:
        text = record.get(self.descriptor.chunk_text_field)
        sequence = record.get(self.descriptor.chunk_sequence_field)
        if not isinstance(text, str) or not isinstance(sequence, int) or isinstance(sequence, bool):
            raise StreamingProtocolError("invalid_chunk", "chunk text/sequence has invalid type")
        if sequence != self._next_chunk_sequence:
            raise StreamingProtocolError(
                "ordering", f"expected chunk sequence {self._next_chunk_sequence}, got {sequence}"
            )
        self._chunks.append(text)
        self._next_chunk_sequence += 1

    def _accept_tool_start(self, record: Mapping[str, Any]) -> None:
        tool_id = record.get(self.descriptor.tool_id_field)
        if not isinstance(tool_id, str) or not tool_id or tool_id in self._open_tools:
            raise StreamingProtocolError("tool_ordering", "invalid or already-open tool call")
        self._open_tools.add(tool_id)
        self._tool_events.append(dict(record))

    def _accept_tool_finish(self, record: Mapping[str, Any]) -> None:
        tool_id = record.get(self.descriptor.tool_id_field)
        status = record.get(self.descriptor.tool_status_field)
        if not isinstance(tool_id, str) or tool_id not in self._open_tools:
            raise StreamingProtocolError("tool_ordering", "tool finish has no matching start")
        if status not in {"success", "error"}:
            raise StreamingProtocolError("invalid_tool_status", "tool finish has unknown status")
        self._open_tools.remove(tool_id)
        self._tool_events.append(dict(record))

    def _accept_terminal(self, record: Mapping[str, Any]) -> None:
        if self._open_tools:
            raise StreamingProtocolError("tool_ordering", "terminal arrived with open tool calls")
        status = record.get(self.descriptor.terminal_status_field)
        if status != self.descriptor.terminal_success_value:
            raise StreamingProtocolError("terminal_failure", "terminal did not report success")
        self._terminal = dict(record)

    def finish(self, exit_code: int, role: str) -> StreamingResult:
        if exit_code != 0:
            raise StreamingProtocolError("nonzero_exit", f"Grok process exited with {exit_code}")
        if self._terminal is None:
            raise StreamingProtocolError("missing_terminal", "stream has no terminal success event")
        semantic_text = "".join(self._chunks)
        if not semantic_text:
            raise StreamingProtocolError("empty_result", "stream has no semantic assistant output")
        try:
            envelope = json.loads(semantic_text)
        except json.JSONDecodeError as error:
            raise StreamingProtocolError(
                "invalid_envelope_json", "assistant chunks do not assemble to JSON"
            ) from error
        schema = _ENVELOPE_SCHEMAS.get(role)
        if schema is None:
            raise StreamingProtocolError("unknown_role", f"unknown envelope role {role!r}")
        validation_error = _schema_error(envelope, schema, "$")
        if validation_error is not None:
            raise StreamingProtocolError("invalid_envelope", validation_error)
        return StreamingResult(
            envelope=envelope,
            chunks=tuple(self._chunks),
            tool_events=tuple(self._tool_events),
            unknown_records=tuple(self._unknown),
            terminal=self._terminal,
            exit_code=exit_code,
        )


def parse_stream(
    stream: str | bytes,
    *,
    exit_code: int,
    role: str,
    descriptor: ProtocolDescriptor = FAKE_PROTOCOL_V1,
) -> StreamingResult:
    """Parse a complete NDJSON stream without consulting terminal prose."""

    if isinstance(stream, bytes):
        try:
            text = stream.decode("utf-8")
        except UnicodeDecodeError as error:
            raise StreamingProtocolError("invalid_encoding", "stream is not UTF-8") from error
    elif isinstance(stream, str):
        text = stream
    else:
        raise TypeError("stream must be str or bytes")

    if text and not text.endswith("\n"):
        raise StreamingProtocolError("truncated_stream", "NDJSON stream lacks final newline")

    parser = StreamingParser(descriptor)
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            raise StreamingProtocolError("malformed_json", f"blank record at line {line_number}")
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise StreamingProtocolError(
                "malformed_json", f"invalid JSON at line {line_number}"
            ) from error
        parser.feed(record)
    return parser.finish(exit_code, role)


def _schema_error(value: Any, schema: Mapping[str, Any], path: str) -> str | None:
    if "enum" in schema and value not in schema["enum"]:
        return f"{path} is not one of {schema['enum']!r}"
    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(value, dict):
            return f"{path} must be an object"
        for key in schema.get("required", ()):
            if key not in value:
                return f"{path} is missing required property {key!r}"
        properties = schema.get("properties", {})
        for key, child in value.items():
            if key in properties:
                error = _schema_error(child, properties[key], f"{path}.{key}")
                if error:
                    return error
            elif not schema.get("additionalProperties", True):
                return f"{path} has unexpected property {key!r}"
    elif expected_type == "array":
        if not isinstance(value, list):
            return f"{path} must be an array"
        for index, child in enumerate(value):
            error = _schema_error(child, schema["items"], f"{path}[{index}]")
            if error:
                return error
    elif expected_type == "string":
        if not isinstance(value, str):
            return f"{path} must be a string"
        if len(value) < schema.get("minLength", 0):
            return f"{path} is too short"
    return None

