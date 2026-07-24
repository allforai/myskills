import json
import os
from pathlib import Path
import tempfile
import unittest

from output_channel import (
    OutputChannelError,
    build_output_flags,
    cleanup,
    parse_result,
    prepare_result_channel,
    provenance,
)


class OutputChannelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def channel(self, role="executor"):
        return prepare_result_channel(
            self.base, run_id="run-1", task_id="task-1", attempt_id="attempt-1",
            role=role, codex_version="codex-cli 1.2.3")

    def write(self, channel, value):
        channel.result_path.write_text(
            value if isinstance(value, str) else json.dumps(value), encoding="utf-8")

    def executor(self, **changes):
        value = {
            "schema_version": 1, "role": "executor", "run_id": "run-1",
            "task_id": "task-1", "attempt_id": "attempt-1",
            "outcome": "complete", "summary": "implemented",
            "touched_paths": ["src/a.py"],
        }
        value.update(changes)
        return value

    def supervisor(self, **changes):
        value = {
            "schema_version": 1, "role": "supervisor", "run_id": "run-1",
            "task_id": "task-1", "attempt_id": "attempt-1",
            "verdict": "confirmed", "summary": "verified",
            "acceptance_executed": True, "rerun_exit_code": 0,
            "evidence": "1 test passed", "acceptance_kind": "test",
            "executed_test_count": 1, "vacuous": False,
            "reality_gated": False,
        }
        value.update(changes)
        return value

    def test_prepares_frozen_schema_and_nonexistent_result(self):
        channel = self.channel()
        self.assertTrue(channel.schema_path.is_file())
        self.assertFalse(channel.result_path.exists())
        self.assertEqual(build_output_flags(channel), [
            "--output-schema", str(channel.schema_path),
            "--output-last-message", str(channel.result_path)])
        before = provenance(channel)
        channel.schema_path.write_text("{}")
        with self.assertRaisesRegex(OutputChannelError, "schema.*changed"):
            parse_result(channel, actual_diff=[])
        self.assertEqual(before["schema_sha256"], channel.schema_sha256)

    def test_rejects_existing_result_and_symlink(self):
        channel = self.channel()
        channel.result_path.write_text("{}")
        with self.assertRaisesRegex(OutputChannelError, "must not exist"):
            build_output_flags(channel)
        other = self.base / "other"; other.write_text("{}")
        channel.result_path.unlink(); channel.result_path.symlink_to(other)
        with self.assertRaisesRegex(OutputChannelError, "regular file|symlink"):
            parse_result(channel, actual_diff=[])

    def test_exactly_one_utf8_json_value_only(self):
        for raw in ("prose " + json.dumps(self.executor()),
                    json.dumps(self.executor()) + " trailing",
                    json.dumps(self.executor()) + " {}", "{\"partial\":"):
            with self.subTest(raw=raw):
                channel = self.channel(); self.write(channel, raw)
                with self.assertRaisesRegex(OutputChannelError, "exactly one|JSON"):
                    parse_result(channel, actual_diff=["src/a.py"])
                cleanup(channel)
        channel = self.channel()
        channel.result_path.write_bytes(b"\xff")
        with self.assertRaisesRegex(OutputChannelError, "UTF-8"):
            parse_result(channel, actual_diff=[])

    def test_executor_identity_schema_outcomes_and_diff_are_strict(self):
        for change in (
            {"run_id": "other"}, {"role": "supervisor"}, {"extra": True},
            {"outcome": "done"}, {"touched_paths": "src/a.py"},
        ):
            with self.subTest(change=change):
                channel = self.channel(); self.write(channel, self.executor(**change))
                with self.assertRaises(OutputChannelError):
                    parse_result(channel, actual_diff=["src/a.py"])
                cleanup(channel)
        channel = self.channel(); self.write(channel, self.executor())
        with self.assertRaisesRegex(OutputChannelError, "actual diff"):
            parse_result(channel, actual_diff=["src/b.py"])
        cleanup(channel)
        for outcome in ("complete", "business_reject", "infrastructure_failure",
                        "needs_replan", "reality_gated"):
            channel = self.channel(); self.write(channel, self.executor(outcome=outcome))
            self.assertEqual(parse_result(channel, actual_diff=["src/a.py"])["outcome"], outcome)
            cleanup(channel)

    def test_supervisor_confirmation_requires_real_nonvacuous_evidence(self):
        bad = (
            {"verdict": "maybe"}, {"evidence": ""},
            {"acceptance_executed": False}, {"rerun_exit_code": 1},
            {"vacuous": True}, {"executed_test_count": 0},
            {"executed_test_count": None},
        )
        for change in bad:
            with self.subTest(change=change):
                channel = self.channel("supervisor"); self.write(channel, self.supervisor(**change))
                with self.assertRaises(OutputChannelError):
                    parse_result(channel)
                cleanup(channel)
        channel = self.channel("supervisor"); self.write(channel, self.supervisor())
        self.assertEqual(parse_result(channel)["verdict"], "confirmed")

    def test_diagnostics_cannot_supply_result_and_cleanup_provenance(self):
        channel = self.channel()
        with self.assertRaisesRegex(OutputChannelError, "missing"):
            parse_result(channel, actual_diff=[], stdout=json.dumps(self.executor()), stderr="")
        self.write(channel, self.executor())
        parsed = parse_result(channel, actual_diff=["src/a.py"], stdout="noise", stderr="noise")
        proof = provenance(channel)
        self.assertEqual(parsed["outcome"], "complete")
        self.assertEqual(proof["role"], "executor")
        self.assertEqual(len(proof["result_sha256"]), 64)
        cleanup(channel)
        self.assertFalse(channel.directory.exists())


if __name__ == "__main__":
    unittest.main()
