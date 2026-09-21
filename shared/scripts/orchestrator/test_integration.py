#!/usr/bin/env python3
"""Integration test: create mock bootstrap products and validate them."""

import json
import os
import shutil
import tempfile
import unittest

from _module_isolation import load, module_dir

_validate_bootstrap = load(module_dir(), "validate_bootstrap")
validate_node_spec = _validate_bootstrap.validate_node_spec
validate_workflow = _validate_bootstrap.validate_workflow

NODE_IDS = ("discovery", "generate")


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.bootstrap_dir = os.path.join(self.tmpdir, "bootstrap")
        self.specs_dir = os.path.join(self.bootstrap_dir, "node-specs")
        os.makedirs(self.specs_dir)

        self.wf = {
            "nodes": [
                {"id": nid, "goal": "Do " + nid, "exit_artifacts": ["artifacts/" + nid + ".json"]}
                for nid in NODE_IDS
            ],
            "transition_log": [],
        }
        self.wf_path = os.path.join(self.bootstrap_dir, "workflow.json")
        with open(self.wf_path, "w") as f:
            json.dump(self.wf, f)

        for nid in NODE_IDS:
            with open(os.path.join(self.specs_dir, f"{nid}.md"), "w") as f:
                f.write("---\nnode: {}\n---\n\n# Task: {}\nDo the thing.".format(nid, nid))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_validation_passes(self):
        errors = validate_workflow(self.wf_path)
        self.assertEqual(errors, [], f"workflow.json errors: {errors}")

        for fname in os.listdir(self.specs_dir):
            path = os.path.join(self.specs_dir, fname)
            errors = validate_node_spec(path)
            self.assertEqual(errors, [], f"Node-spec errors for {fname}: {errors}")


if __name__ == "__main__":
    unittest.main()
