#!/usr/bin/env python3
"""Tests for cr_gen_indexes.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cr_gen_indexes import generate_indexes


class TestGenerateIndexes(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base_path = os.path.join(self.tmpdir, "project")
        self.pm_dir = os.path.join(self.base_path, ".allforai", "product-map")
        os.makedirs(self.pm_dir, exist_ok=True)

    def _write_artifact(self, name, data):
        path = os.path.join(self.pm_dir, name)
        with open(path, "w") as f:
            json.dump(data, f)

    def _read_output(self, name):
        path = os.path.join(self.pm_dir, name)
        with open(path) as f:
            return json.load(f)

    def test_task_index_groups_by_category(self):
        self._write_artifact("task-inventory.json", {
            "tasks": [
                {"id": "T001", "title": "Login", "category": "Authentication"},
                {"id": "T002", "title": "Logout", "category": "Authentication"},
                {"id": "T003", "title": "Dashboard", "category": "Dashboard"},
            ]
        })
        self._write_artifact("business-flows.json", {"flows": []})
        generate_indexes(self.base_path)
        out = self._read_output("task-index.json")

        self.assertIn("generated_at", out)
        cats = {c["name"]: c for c in out["categories"]}
        self.assertIn("Authentication", cats)
        self.assertEqual(cats["Authentication"]["task_count"], 2)
        self.assertEqual(cats["Authentication"]["task_ids"], ["T001", "T002"])
        self.assertIn("Dashboard", cats)
        self.assertEqual(cats["Dashboard"]["task_count"], 1)

    def test_task_index_groups_by_module(self):
        self._write_artifact("task-inventory.json", {
            "tasks": [
                {"id": "T001", "title": "Login", "category": "Auth", "module": "auth"},
                {"id": "T002", "title": "Register", "category": "Auth", "module": "auth"},
                {"id": "T003", "title": "View", "category": "UI", "module": "ui"},
            ]
        })
        self._write_artifact("business-flows.json", {"flows": []})
        generate_indexes(self.base_path)
        out = self._read_output("task-index.json")

        mods = {m["name"]: m for m in out["modules"]}
        self.assertIn("auth", mods)
        self.assertEqual(mods["auth"]["task_count"], 2)
        self.assertEqual(mods["auth"]["task_ids"], ["T001", "T002"])
        self.assertIn("ui", mods)

    def test_task_index_no_module_field(self):
        self._write_artifact("task-inventory.json", {
            "tasks": [
                {"id": "T001", "title": "Login", "category": "Auth"},
            ]
        })
        self._write_artifact("business-flows.json", {"flows": []})
        generate_indexes(self.base_path)
        out = self._read_output("task-index.json")
        self.assertEqual(out["modules"], [])

    def test_flow_index_basic(self):
        self._write_artifact("task-inventory.json", {"tasks": []})
        self._write_artifact("business-flows.json", {
            "flows": [
                {
                    "id": "F001",
                    "name": "User Registration",
                    "nodes": [
                        {"id": "N1", "role": "R001"},
                        {"id": "N2", "role": "R001"},
                        {"id": "N3", "role": "R002", "gap": True},
                    ]
                }
            ]
        })
        generate_indexes(self.base_path)
        out = self._read_output("flow-index.json")

        self.assertIn("generated_at", out)
        self.assertEqual(len(out["flows"]), 1)
        f = out["flows"][0]
        self.assertEqual(f["id"], "F001")
        self.assertEqual(f["name"], "User Registration")
        self.assertEqual(f["node_count"], 3)
        self.assertEqual(f["gap_count"], 1)
        self.assertIn("R001", f["roles"])
        self.assertIn("R002", f["roles"])

    def test_flow_index_no_gaps(self):
        self._write_artifact("task-inventory.json", {"tasks": []})
        self._write_artifact("business-flows.json", {
            "flows": [
                {
                    "id": "F001",
                    "name": "Simple",
                    "nodes": [{"id": "N1", "role": "R001"}]
                }
            ]
        })
        generate_indexes(self.base_path)
        out = self._read_output("flow-index.json")
        self.assertEqual(out["flows"][0]["gap_count"], 0)

    def test_empty_inputs(self):
        self._write_artifact("task-inventory.json", {"tasks": []})
        self._write_artifact("business-flows.json", {"flows": []})
        generate_indexes(self.base_path)

        ti = self._read_output("task-index.json")
        fi = self._read_output("flow-index.json")
        self.assertEqual(ti["categories"], [])
        self.assertEqual(ti["modules"], [])
        self.assertEqual(fi["flows"], [])

    def test_returns_paths(self):
        self._write_artifact("task-inventory.json", {"tasks": []})
        self._write_artifact("business-flows.json", {"flows": []})
        paths = generate_indexes(self.base_path)
        self.assertEqual(len(paths), 2)
        self.assertTrue(all(os.path.exists(p) for p in paths))

    def test_flow_nodes_without_role(self):
        """Nodes without role field should not crash."""
        self._write_artifact("task-inventory.json", {"tasks": []})
        self._write_artifact("business-flows.json", {
            "flows": [
                {
                    "id": "F001",
                    "name": "Test",
                    "nodes": [{"id": "N1"}, {"id": "N2", "role": "R001"}]
                }
            ]
        })
        generate_indexes(self.base_path)
        out = self._read_output("flow-index.json")
        self.assertEqual(out["flows"][0]["node_count"], 2)
        self.assertEqual(out["flows"][0]["roles"], ["R001"])


if __name__ == "__main__":
    unittest.main()
