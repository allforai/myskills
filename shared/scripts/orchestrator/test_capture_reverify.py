import json
import os
import sys
import tempfile
import unittest

from capture_evidence import capture, write_capture
from reverify import reverify


class TestCapture(unittest.TestCase):
    def test_capture_records_real_exit_and_output(self):
        rec = capture([sys.executable, "-c", "print('hello-evidence')"])
        self.assertEqual(rec["schema"], "capture_evidence/v1")
        self.assertEqual(rec["exit_code"], 0)
        self.assertIn("hello-evidence", rec["stdout"])
        self.assertTrue(rec["stdout_sha256"])

    def test_capture_records_failure(self):
        rec = capture([sys.executable, "-c", "import sys; sys.exit(3)"])
        self.assertEqual(rec["exit_code"], 3)

    def test_write_capture_creates_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "sub", "ev.json")
            write_capture(p, [sys.executable, "-c", "print(1)"])
            self.assertTrue(os.path.exists(p))


class TestReverify(unittest.TestCase):
    def test_reproduces_real_passing_command(self):
        rec = capture([sys.executable, "-c", "print('ok')"])
        r = reverify(rec)
        self.assertTrue(r["ok"])
        self.assertTrue(r["exit_match"])

    def test_catches_fabricated_record(self):
        # hand-forged: claims exit 0 for a command that actually FAILS
        forged = {"schema": "capture_evidence/v1",
                  "command": [sys.executable, "-c", "import sys; sys.exit(1)"],
                  "exit_code": 0, "stdout": "", "stdout_sha256": "deadbeef"}
        r = reverify(forged)
        self.assertFalse(r["ok"])          # re-run does not reproduce success
        self.assertEqual(r["actual_exit"], 1)
        self.assertFalse(r["exit_match"])

    def test_rejects_non_capture_record(self):
        self.assertFalse(reverify({"some": "freeform"})["ok"])
        self.assertFalse(reverify({"schema": "capture_evidence/v1"})["ok"])  # no command


if __name__ == "__main__":
    unittest.main()
