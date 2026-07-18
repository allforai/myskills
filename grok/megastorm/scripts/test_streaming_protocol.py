import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from streaming_protocol import (
    FAKE_PROTOCOL_V1,
    ProtocolDescriptor,
    StreamingProtocolError,
    parse_stream,
)


def event(**fields):
    return json.dumps(fields, separators=(",", ":")) + "\n"


def executor_chunks():
    envelope = json.dumps(
        {
            "kind": "executor",
            "status": "complete",
            "summary": "implemented",
            "touched_paths": ["src/a.py"],
        },
        separators=(",", ":"),
    )
    midpoint = len(envelope) // 2
    return (
        event(type="assistant.chunk", id="chunk-0", sequence=0, text=envelope[:midpoint])
        + event(type="assistant.chunk", id="chunk-1", sequence=1, text=envelope[midpoint:])
    )


def terminal(event_id="terminal-1"):
    return event(type="stream.terminal", id=event_id, status="success", text="IGNORE ME")


class DescriptorTests(unittest.TestCase):
    def test_fake_descriptor_has_provenance_and_is_explicitly_non_conformant(self):
        descriptor = FAKE_PROTOCOL_V1
        self.assertEqual(descriptor.descriptor_version, 1)
        self.assertEqual(descriptor.provenance.source, "fake")
        self.assertFalse(descriptor.real_host_conformant)
        self.assertEqual(len(descriptor.provenance.sha256), 64)

    def test_fake_provenance_cannot_claim_real_conformance(self):
        values = dict(FAKE_PROTOCOL_V1.__dict__)
        values["real_host_conformant"] = True
        with self.assertRaisesRegex(ValueError, "fake fixture"):
            ProtocolDescriptor(**values)


class SuccessfulStreamTests(unittest.TestCase):
    def test_chunks_assemble_schema_valid_envelope_not_terminal_text(self):
        result = parse_stream(executor_chunks() + terminal(), exit_code=0, role="executor")
        self.assertEqual(result.envelope["summary"], "implemented")
        self.assertEqual(len(result.chunks), 2)

    def test_tool_lifecycle_and_additive_unknown_record(self):
        stream = (
            event(type="future.telemetry", payload={"new": True})
            + event(type="tool.start", id="event-tool-1", tool_call_id="call-1", name="read")
            + event(
                type="tool.finish",
                id="event-tool-2",
                tool_call_id="call-1",
                status="success",
                additive="accepted",
            )
            + executor_chunks()
            + terminal()
        )
        result = parse_stream(stream, exit_code=0, role="executor")
        self.assertEqual(len(result.tool_events), 2)
        self.assertEqual(len(result.unknown_records), 1)

    def test_exact_duplicate_id_is_idempotently_ignored(self):
        chunk = event(type="assistant.chunk", id="chunk-0", sequence=0, text="{")
        rest = event(
            type="assistant.chunk",
            id="chunk-1",
            sequence=1,
            text='"kind":"supervisor","verdict":"confirmed","summary":"ok"}',
        )
        result = parse_stream(chunk + chunk + rest + terminal(), exit_code=0, role="supervisor")
        self.assertEqual(result.envelope["verdict"], "confirmed")


class StrictFailureTests(unittest.TestCase):
    def assert_code(self, code, stream, *, exit_code=0, role="executor"):
        with self.assertRaises(StreamingProtocolError) as raised:
            parse_stream(stream, exit_code=exit_code, role=role)
        self.assertEqual(raised.exception.code, code)

    def test_conflicting_duplicate_id_fails(self):
        self.assert_code(
            "conflicting_duplicate",
            event(type="assistant.chunk", id="same", sequence=0, text="a")
            + event(type="assistant.chunk", id="same", sequence=0, text="b")
            + terminal(),
        )

    def test_chunk_ordering_fails_closed(self):
        self.assert_code(
            "ordering",
            event(type="assistant.chunk", id="chunk-1", sequence=1, text="{}") + terminal(),
        )

    def test_tool_finish_before_start_fails(self):
        self.assert_code(
            "tool_ordering",
            event(type="tool.finish", id="finish", tool_call_id="call", status="success"),
        )

    def test_terminal_with_open_tool_fails(self):
        self.assert_code(
            "tool_ordering",
            event(type="tool.start", id="start", tool_call_id="call", name="read") + terminal(),
        )

    def test_protocol_error_fails(self):
        self.assert_code(
            "protocol_error",
            event(type="protocol.error", id="error-1", message="remote failure"),
        )

    def test_duplicate_terminal_is_post_terminal(self):
        self.assert_code("post_terminal", executor_chunks() + terminal("t1") + terminal("t1"))

    def test_semantic_record_after_terminal_fails(self):
        self.assert_code(
            "post_terminal",
            executor_chunks()
            + terminal()
            + event(type="assistant.chunk", id="late", sequence=2, text="late"),
        )

    def test_unknown_record_after_terminal_also_fails_closed(self):
        self.assert_code(
            "post_terminal",
            executor_chunks() + terminal() + event(type="future.telemetry", value=1),
        )

    def test_malformed_json_fails(self):
        self.assert_code("malformed_json", "{not json}\n")

    def test_truncated_stream_fails_even_when_last_json_is_valid(self):
        self.assert_code("truncated_stream", executor_chunks() + terminal().rstrip("\n"))

    def test_missing_terminal_on_zero_exit_fails(self):
        self.assert_code("missing_terminal", executor_chunks())

    def test_empty_result_fails(self):
        self.assert_code("empty_result", terminal())

    def test_nonzero_exit_fails_despite_success_terminal(self):
        self.assert_code("nonzero_exit", executor_chunks() + terminal(), exit_code=17)

    def test_nonzero_exit_without_terminal_is_still_nonzero_exit(self):
        self.assert_code("nonzero_exit", executor_chunks(), exit_code=2)

    def test_schema_invalid_executor_envelope_fails(self):
        invalid = json.dumps({"kind": "executor", "status": "complete", "summary": "ok"})
        self.assert_code(
            "invalid_envelope",
            event(type="assistant.chunk", id="chunk", sequence=0, text=invalid) + terminal(),
        )

    def test_unknown_supervisor_verdict_fails_schema(self):
        invalid = json.dumps(
            {"kind": "supervisor", "verdict": "probably", "summary": "uncertain"}
        )
        self.assert_code(
            "invalid_envelope",
            event(type="assistant.chunk", id="chunk", sequence=0, text=invalid) + terminal(),
            role="supervisor",
        )

    def test_terminal_failure_record_fails(self):
        self.assert_code(
            "terminal_failure",
            executor_chunks() + event(type="stream.terminal", id="terminal", status="failure"),
        )

    def test_terminal_prose_is_never_scraped_as_json(self):
        self.assert_code(
            "empty_result",
            event(
                type="stream.terminal",
                id="terminal",
                status="success",
                text='{"kind":"executor","status":"complete","summary":"bad","touched_paths":[]}',
            ),
        )


if __name__ == "__main__":
    unittest.main()
