#!/usr/bin/env python3
"""Strict, file-only result channel for headless Codex attempts."""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile


class OutputChannelError(RuntimeError):
    pass


_IDENTITY = {
    "schema_version": {"type": "integer", "const": 1},
    "role": {"type": "string"},
    "run_id": {"type": "string", "minLength": 1},
    "task_id": {"type": "string", "minLength": 1},
    "attempt_id": {"type": "string", "minLength": 1},
}

_SCHEMAS = {
    "executor": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object", "additionalProperties": False,
        "required": ["schema_version", "role", "run_id", "task_id", "attempt_id",
                     "outcome", "summary", "touched_paths"],
        "properties": {
            **_IDENTITY, "role": {"type": "string", "const": "executor"},
            "outcome": {"type": "string", "enum": [
                "complete", "business_reject", "infrastructure_failure",
                "needs_replan", "reality_gated"]},
            "summary": {"type": "string", "minLength": 1},
            "touched_paths": {"type": "array", "uniqueItems": True,
                              "items": {"type": "string", "minLength": 1}},
        },
    },
    "supervisor": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object", "additionalProperties": False,
        "required": ["schema_version", "role", "run_id", "task_id", "attempt_id",
                     "verdict", "summary", "acceptance_executed", "rerun_exit_code",
                     "evidence", "acceptance_kind", "executed_test_count", "vacuous",
                     "reality_gated"],
        "properties": {
            **_IDENTITY, "role": {"type": "string", "const": "supervisor"},
            "verdict": {"type": "string", "enum": ["confirmed", "rejected"]},
            "summary": {"type": "string", "minLength": 1},
            "acceptance_executed": {"type": "boolean"},
            "rerun_exit_code": {"type": "integer"},
            "evidence": {"type": "string", "minLength": 1},
            "acceptance_kind": {"type": "string",
                                "enum": ["test", "non_test", "reality"]},
            "executed_test_count": {"type": ["integer", "null"], "minimum": 0},
            "vacuous": {"type": "boolean"},
            "reality_gated": {"type": "boolean"},
        },
    },
}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


ROLE_SCHEMA_SHA256 = {
    role: hashlib.sha256(_canonical(schema)).hexdigest()
    for role, schema in _SCHEMAS.items()
}


@dataclass(frozen=True)
class ResultChannel:
    directory: Path
    schema_path: Path
    result_path: Path
    role: str
    run_id: str
    task_id: str
    attempt_id: str
    codex_version: str
    schema_sha256: str
    directory_identity: tuple


def _require_identity(value, label):
    if not isinstance(value, str) or not value:
        raise OutputChannelError(f"{label} must be a non-empty string")


def _exclusive_write(path, payload):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(str(path), flags, 0o600)
    try:
        os.write(fd, payload)
        os.fsync(fd)
    finally:
        os.close(fd)


def prepare_result_channel(base_dir, *, run_id, task_id, attempt_id, role,
                           codex_version):
    """Create an attempt-owned directory and frozen schema; leave result absent."""
    if role not in _SCHEMAS:
        raise OutputChannelError(f"unsupported result role: {role}")
    for value, label in ((run_id, "run_id"), (task_id, "task_id"),
                         (attempt_id, "attempt_id"), (codex_version, "codex_version")):
        _require_identity(value, label)
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    if base.is_symlink() or not base.is_dir():
        raise OutputChannelError("result channel base must be a real directory")
    directory = Path(tempfile.mkdtemp(prefix=f"{role}-", dir=str(base.resolve())))
    os.chmod(directory, 0o700)
    info = directory.stat()
    schema_path = directory / "schema.json"
    result_path = directory / "result.json"
    payload = _canonical(_SCHEMAS[role])
    _exclusive_write(schema_path, payload)
    return ResultChannel(
        directory, schema_path, result_path, role, run_id, task_id, attempt_id,
        codex_version, hashlib.sha256(payload).hexdigest(),
        (info.st_dev, info.st_ino, info.st_uid),
    )


def _check_directory(channel):
    try:
        info = channel.directory.lstat()
    except OSError as exc:
        raise OutputChannelError("attempt result directory is missing") from exc
    if (not stat.S_ISDIR(info.st_mode) or channel.directory.is_symlink() or
            (info.st_dev, info.st_ino, info.st_uid) != channel.directory_identity):
        raise OutputChannelError("attempt result directory identity changed")


def _check_schema(channel):
    _check_directory(channel)
    try:
        info = channel.schema_path.lstat()
        raw = channel.schema_path.read_bytes()
    except OSError as exc:
        raise OutputChannelError("frozen output schema is missing") from exc
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid():
        raise OutputChannelError("frozen output schema is not an owned regular file")
    if hashlib.sha256(raw).hexdigest() != channel.schema_sha256:
        raise OutputChannelError("frozen output schema changed after preparation")


def build_output_flags(channel):
    """Return runner-owned Codex flags, refusing any pre-existing result path."""
    _check_schema(channel)
    if os.path.lexists(channel.result_path):
        raise OutputChannelError("attempt result path must not exist before dispatch")
    return ["--output-schema", str(channel.schema_path),
            "--output-last-message", str(channel.result_path)]


def _read_owned_result(channel, maximum_bytes=1024 * 1024):
    _check_schema(channel)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(str(channel.result_path), flags)
    except FileNotFoundError as exc:
        raise OutputChannelError("attempt result file is missing") from exc
    except OSError as exc:
        raise OutputChannelError("attempt result must be a non-symlink regular file") from exc
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or
                info.st_nlink != 1):
            raise OutputChannelError("attempt result must be an owned regular file")
        raw = os.read(fd, maximum_bytes + 1)
        if len(raw) > maximum_bytes:
            raise OutputChannelError("attempt result exceeds size limit")
    finally:
        os.close(fd)
    try:
        return raw, raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OutputChannelError("attempt result is not valid UTF-8") from exc


def _is_type(value, expected):
    if expected == "object": return isinstance(value, dict)
    if expected == "array": return isinstance(value, list)
    if expected == "string": return isinstance(value, str)
    if expected == "integer": return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean": return isinstance(value, bool)
    if expected == "null": return value is None
    return False


def _validate(value, schema, path="$"):
    kinds = schema.get("type")
    if kinds is not None:
        kinds = [kinds] if isinstance(kinds, str) else kinds
        if not any(_is_type(value, kind) for kind in kinds):
            raise OutputChannelError(f"schema type mismatch at {path}")
    if "const" in schema and value != schema["const"]:
        raise OutputChannelError(f"schema constant mismatch at {path}")
    if "enum" in schema and value not in schema["enum"]:
        raise OutputChannelError(f"schema enum mismatch at {path}")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        raise OutputChannelError(f"schema string is empty at {path}")
    if isinstance(value, int) and not isinstance(value, bool) and "minimum" in schema:
        if value < schema["minimum"]:
            raise OutputChannelError(f"schema number below minimum at {path}")
    if isinstance(value, dict):
        required = set(schema.get("required", ()))
        missing = required - set(value)
        if missing:
            raise OutputChannelError(f"schema required fields missing at {path}: {sorted(missing)}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            if extra:
                raise OutputChannelError(f"schema forbids fields at {path}: {sorted(extra)}")
        for key, child in value.items():
            if key in properties:
                _validate(child, properties[key], f"{path}.{key}")
    if isinstance(value, list):
        if schema.get("uniqueItems") and len({_canonical(item) for item in value}) != len(value):
            raise OutputChannelError(f"schema requires unique items at {path}")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                _validate(item, item_schema, f"{path}[{index}]")


def _decode_one(text):
    start = len(text) - len(text.lstrip())
    try:
        value, end = json.JSONDecoder().raw_decode(text, start)
    except (ValueError, TypeError) as exc:
        raise OutputChannelError("attempt result is not one complete JSON value") from exc
    if text[end:].strip():
        raise OutputChannelError("attempt result must contain exactly one JSON value")
    return value


def parse_result(channel, *, actual_diff=None, stdout=None, stderr=None):
    """Parse the file only; stdout/stderr are intentionally ignored diagnostics."""
    del stdout, stderr
    raw, text = _read_owned_result(channel)
    value = _decode_one(text)
    _validate(value, _SCHEMAS[channel.role])
    expected = {"role": channel.role, "run_id": channel.run_id,
                "task_id": channel.task_id, "attempt_id": channel.attempt_id}
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise OutputChannelError(f"result identity mismatch: {key}")
    if channel.role == "executor":
        if actual_diff is None:
            raise OutputChannelError("executor result requires the actual diff")
        reported = set(value["touched_paths"])
        observed = set(actual_diff)
        if reported != observed:
            raise OutputChannelError("executor touched_paths are inconsistent with actual diff")
    else:
        if not value["acceptance_executed"]:
            raise OutputChannelError("supervisor did not execute acceptance")
        if not value["evidence"].strip():
            raise OutputChannelError("supervisor evidence is empty")
        if value["verdict"] == "confirmed":
            if value["rerun_exit_code"] != 0 or value["vacuous"] or value["reality_gated"]:
                raise OutputChannelError("supervisor confirmation lacks passing non-vacuous evidence")
            if (value["acceptance_kind"] == "test" and
                    (value["executed_test_count"] is None or value["executed_test_count"] < 1)):
                raise OutputChannelError("supervisor confirmation has no executed tests")
    return value


def provenance(channel):
    """Return redaction-safe channel provenance and current result hash, if any."""
    _check_schema(channel)
    result_hash = None
    if os.path.lexists(channel.result_path):
        raw, _ = _read_owned_result(channel)
        result_hash = hashlib.sha256(raw).hexdigest()
    return {
        "role": channel.role, "run_id": channel.run_id, "task_id": channel.task_id,
        "attempt_id": channel.attempt_id, "codex_version": channel.codex_version,
        "schema_path": str(channel.schema_path), "schema_sha256": channel.schema_sha256,
        "result_path": str(channel.result_path), "result_sha256": result_hash,
    }


def cleanup(channel):
    """Remove only this verified attempt's two owned files and directory."""
    _check_directory(channel)
    for path in (channel.result_path, channel.schema_path):
        if os.path.lexists(path):
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid():
                raise OutputChannelError("refusing to clean an unowned or non-regular channel file")
            path.unlink()
    try:
        channel.directory.rmdir()
    except OSError as exc:
        raise OutputChannelError("attempt directory contains unexpected files") from exc
