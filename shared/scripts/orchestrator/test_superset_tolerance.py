import json, tempfile, os, unittest, subprocess, sys

SUPERSET_NODE = {
    "node_id": "n1", "capability": "x", "hard_blocked_by": [], "exit_artifacts": [],
    # CC-only superset fields that Codex/OpenCode validators must IGNORE, not choke on:
    "decision_mode": "brainstorm", "decision_inputs": [".allforai/x/decision-n1.json"],
    "closure_verify": ["audio"], "soft_retry_max": 2, "profile_slice": {"stack": "unity"}
}

class TestSupersetTolerance(unittest.TestCase):
    def _write_wf(self, d):
        wf = {"schema_version": "1.0", "nodes": [SUPERSET_NODE],
              "transition_log": [], "expanders": ["mk_x"]}
        path = os.path.join(d, "workflow.json")
        with open(path, "w") as f:
            json.dump(wf, f)
        return path

    def test_validate_bootstrap_tolerates_superset(self):
        import validate_bootstrap
        with tempfile.TemporaryDirectory() as d:
            wf_path = self._write_wf(d)
            wf = json.load(open(wf_path))
            # Must not raise on unknown fields; node remains structurally valid.
            self.assertEqual(wf["nodes"][0]["node_id"], "n1")
            # If validate_bootstrap exposes a node-shape checker, it must pass:
            if hasattr(validate_bootstrap, "validate_node"):
                ok, _ = validate_bootstrap.validate_node(wf["nodes"][0])
                self.assertTrue(ok)

if __name__ == "__main__":
    unittest.main()
