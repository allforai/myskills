import json, os, tempfile, unittest
from check_decision_inputs import check_decision_inputs

class TestCheckDecisionInputs(unittest.TestCase):
    def _wf(self, nodes):
        return {"nodes": nodes}

    def test_all_present_returns_ok(self):
        with tempfile.TemporaryDirectory() as d:
            art = os.path.join(d, "decision-a.json")
            open(art, "w").write("{}")
            wf = self._wf([{"node_id": "a", "decision_inputs": [art]}])
            missing = check_decision_inputs(wf, base_dir=d)
            self.assertEqual(missing, [])

    def test_missing_artifact_reported(self):
        with tempfile.TemporaryDirectory() as d:
            wf = self._wf([{"node_id": "a", "decision_inputs": [os.path.join(d, "nope.json")]}])
            missing = check_decision_inputs(wf, base_dir=d)
            self.assertEqual(len(missing), 1)
            self.assertEqual(missing[0]["node_id"], "a")

    def test_nodes_without_decision_inputs_ignored(self):
        wf = self._wf([{"node_id": "a"}, {"node_id": "b", "decision_inputs": []}])
        self.assertEqual(check_decision_inputs(wf, base_dir="/tmp"), [])

    def test_orphan_decision_detected(self):
        from check_decision_inputs import find_orphan_decisions
        wf = self._wf([{"node_id": "a", "decision_inputs": ["d/decision-x.json"]}])
        # decision-y.json was gathered but no node references it -> orphan (fix C4)
        orphans = find_orphan_decisions(wf, ["d/decision-x.json", "d/decision-y.json"])
        self.assertEqual(orphans, ["d/decision-y.json"])

if __name__ == "__main__":
    unittest.main()
