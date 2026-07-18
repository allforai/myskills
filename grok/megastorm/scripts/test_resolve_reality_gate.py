import tempfile
import unittest
import hashlib
from pathlib import Path

from resolve_reality_gate import resolve


class ResolveRealityGateTests(unittest.TestCase):
    def test_rejection_supersedes_report_and_invalidates_downstream(self):
        with tempfile.TemporaryDirectory() as td:
            ev = Path(td, "evidence.txt"); ev.write_text("failed on device")
            report = {"reality_gates": [{"task_id": "a"}],
                      "results": [{"task_id": x, "status": "done"}
                                  for x in ("a", "b", "c", "independent")],
                      "summary": {"verified": 3, "reality_gated": 1}}
            state = {"completed": ["a", "b", "c", "independent"]}
            orch = {"effective_deps": {"a": [], "b": ["a"], "c": ["b"],
                                       "independent": []}}
            report, state = resolve(report, state, orch, "a", "rejected", str(ev))
            self.assertTrue(report["superseded"])
            self.assertEqual(state["completed"], ["independent"])
            self.assertEqual(state["invalidated"], ["a", "b", "c"])
            self.assertEqual(report["reality_gates"], [])
            self.assertEqual(report["invalidation_provenance"]["outcome"], "rejected")
            self.assertEqual(report["summary"]["reality_gated"], 0)
            self.assertEqual(report["summary"],
                             {"verified": 1, "reality_gated": 0,
                              "escalated": 0, "skipped": 0})
            self.assertTrue(all(r["status"] == "invalidated" for r in report["results"][:3]))

    def test_verification_closes_without_invalidation(self):
        with tempfile.TemporaryDirectory() as td:
            ev = Path(td, "evidence.txt"); ev.write_text("passed")
            report, state = resolve({"reality_gates": [{"task_id": "a"}],
                                     "results": [{"task_id": "a",
                                                  "status": "reality_gated"},
                                                 {"task_id": "b", "status": "done"}],
                                     "summary": {"verified": 1, "reality_gated": 1}},
                                    {"completed": ["a", "b"]},
                                    {"effective_deps": {"a": [], "b": ["a"]}},
                                    "a", "verified", str(ev))
            self.assertNotIn("superseded", report)
            self.assertEqual(state["completed"], ["a", "b"])
            self.assertEqual(report["reality_gates"], [])
            self.assertEqual(report["summary"],
                             {"verified": 2, "reality_gated": 0,
                              "escalated": 0, "skipped": 0})
            self.assertEqual(report["results"][0]["status"], "done")
            resolution = report["resolved_reality_gates"][0]["human_resolution"]
            self.assertEqual(state["reality_resolutions"]["a"]["outcome"], "verified")
            self.assertEqual(resolution["evidence_sha256"],
                             hashlib.sha256(ev.read_bytes()).hexdigest())

    def test_rejected_gate_stays_invalidated_against_old_events(self):
        with tempfile.TemporaryDirectory() as td:
            ev = Path(td, "evidence.txt"); ev.write_text("failed")
            report, state = resolve({"reality_gates": [{"task_id": "a"}]},
                                    {"completed": ["a"], "invalidated": []},
                                    {"effective_deps": {"a": []}},
                                    "a", "rejected", str(ev))
            recovered_from_old_event = {"a": "reality_gated"}
            allowed = {tid for tid in recovered_from_old_event
                       if tid not in set(state["invalidated"])}
            self.assertEqual(allowed, set())

    def test_rejection_recomputes_all_counts_after_downstream_invalidation(self):
        with tempfile.TemporaryDirectory() as td:
            ev = Path(td, "evidence.txt"); ev.write_text("rejected")
            report = {
                "reality_gates": [{"task_id": "gate"}],
                "results": [
                    {"task_id": "gate", "status": "reality_gated"},
                    {"task_id": "child", "status": "done"},
                    {"task_id": "grandchild", "status": "done"},
                    {"task_id": "independent", "status": "done"},
                    {"task_id": "other-failure", "status": "escalate"}],
                "skipped": {"child": "gate", "other-skip": "other-failure"},
                "summary": {"verified": 99, "reality_gated": 99,
                            "escalated": 99, "skipped": 99}}
            state = {"completed": ["gate", "child", "grandchild", "independent"]}
            orch = {"effective_deps": {
                "gate": [], "child": ["gate"], "grandchild": ["child"],
                "independent": [], "other-failure": [], "other-skip": ["other-failure"]}}
            report, state = resolve(report, state, orch, "gate", "rejected", str(ev))
            self.assertEqual(state["completed"], ["independent"])
            self.assertEqual(report["summary"],
                             {"verified": 1, "reality_gated": 0,
                              "escalated": 1, "skipped": 1})


if __name__ == "__main__":
    unittest.main()
