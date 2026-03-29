#!/usr/bin/env python3
"""Integration test: create mock bootstrap products and validate them."""

import json
import os
import shutil
import tempfile
import unittest

from check_requires import evaluate_node
from validate_bootstrap import (
    validate_node_spec,
    validate_state_machine,
    validate_graph_connectivity,
    scan_dangerous_commands,
)


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.bootstrap_dir = os.path.join(self.tmpdir, "bootstrap")
        self.specs_dir = os.path.join(self.bootstrap_dir, "node-specs")
        os.makedirs(self.specs_dir)

        # Create a mini state machine with 2 nodes
        self.sm = {
            "schema_version": "1.0",
            "nodes": [
                {
                    "id": "discovery",
                    "description": "Scan project",
                    "entry_requires": [],
                    "exit_requires": [
                        {"file_exists": os.path.join(self.tmpdir, "catalog.json")}
                    ],
                    "hints": [],
                },
                {
                    "id": "generate",
                    "description": "Generate artifacts",
                    "entry_requires": [
                        {"file_exists": os.path.join(self.tmpdir, "catalog.json")}
                    ],
                    "exit_requires": [
                        {"file_exists": os.path.join(self.tmpdir, "tasks.json")},
                        {"json_array_length_gte": [os.path.join(self.tmpdir, "tasks.json"), "$", 1]},
                    ],
                    "hints": [],
                },
            ],
            "safety": {
                "loop_detection": {"warn_threshold": 3, "stop_threshold": 5},
                "max_global_iterations": 30,
            },
            "progress": {"completed_nodes": [], "iteration_count": 0},
        }
        self.sm_path = os.path.join(self.bootstrap_dir, "state-machine.json")
        with open(self.sm_path, "w") as f:
            json.dump(self.sm, f)

        # Create matching node-specs
        for node in self.sm["nodes"]:
            nid = node["id"]
            spec_content = "---\nnode: {}\nentry_requires: {}\nexit_requires: {}\n---\n\n# Task: {}\nDo the thing.".format(
                nid,
                json.dumps(node["entry_requires"]),
                json.dumps(node["exit_requires"]),
                nid,
            )
            with open(os.path.join(self.specs_dir, f"{nid}.md"), "w") as f:
                f.write(spec_content)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_validation_passes(self):
        errors = validate_state_machine(self.sm_path)
        self.assertEqual(errors, [], f"State machine errors: {errors}")

        for fname in os.listdir(self.specs_dir):
            path = os.path.join(self.specs_dir, fname)
            errors = validate_node_spec(path)
            self.assertEqual(errors, [], f"Node-spec errors for {fname}: {errors}")

    def test_graph_connected(self):
        orphans = validate_graph_connectivity(self.sm["nodes"])
        self.assertEqual(orphans, [])

    def test_check_requires_before_artifacts(self):
        result = evaluate_node(self.sm_path, "discovery", "exit")
        self.assertFalse(result["all_passed"])

    def test_check_requires_after_artifacts(self):
        with open(os.path.join(self.tmpdir, "catalog.json"), "w") as f:
            json.dump({"files": ["a.py"]}, f)
        with open(os.path.join(self.tmpdir, "tasks.json"), "w") as f:
            json.dump([{"id": "T001", "name": "task 1"}], f)

        r1 = evaluate_node(self.sm_path, "discovery", "exit")
        self.assertTrue(r1["all_passed"])
        r2 = evaluate_node(self.sm_path, "generate", "exit")
        self.assertTrue(r2["all_passed"])

    def test_no_dangerous_commands(self):
        all_commands = []
        for node in self.sm["nodes"]:
            for req in node.get("exit_requires", []):
                if isinstance(req, dict):
                    all_commands.append(req)
        dangers = scan_dangerous_commands(all_commands)
        self.assertEqual(dangers, [])


if __name__ == "__main__":
    unittest.main()
