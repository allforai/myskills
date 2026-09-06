import tempfile
import unittest
from pathlib import Path

from resolve_reality_gate import resolve


class ResolveRealityGateTests(unittest.TestCase):
    def test_rejection_supersedes_report_and_invalidates_downstream(self):
        with tempfile.TemporaryDirectory() as td:
            ev = Path(td, "evidence.txt"); ev.write_text("failed on device")
            report = {"reality_gates": [{"task_id": "a"}]}
            state = {"completed": ["a", "b", "c", "independent"]}
            orch = {"effective_deps": {"a": [], "b": ["a"], "c": ["b"],
                                       "independent": []}}
            report, state = resolve(report, state, orch, "a", "rejected", str(ev))
            self.assertTrue(report["superseded"])
            self.assertEqual(state["completed"], ["independent"])

    def test_verification_closes_without_invalidation(self):
        with tempfile.TemporaryDirectory() as td:
            ev = Path(td, "evidence.txt"); ev.write_text("passed")
            report, state = resolve({"reality_gates": [{"task_id": "a"}]},
                                    {"completed": ["a", "b"]},
                                    {"effective_deps": {"a": [], "b": ["a"]}},
                                    "a", "verified", str(ev))
            self.assertNotIn("superseded", report)
            self.assertEqual(state["completed"], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
