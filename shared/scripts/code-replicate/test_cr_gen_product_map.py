#!/usr/bin/env python3
"""Tests for cr_gen_product_map.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cr_gen_product_map import generate_product_map


class TestGenerateProductMap(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base_path = os.path.join(self.tmpdir, "project")
        self.pm_dir = os.path.join(self.base_path, ".allforai", "product-map")
        os.makedirs(self.pm_dir, exist_ok=True)

    def _write_artifact(self, rel_path, data):
        path = os.path.join(self.base_path, ".allforai", rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)

    def _read_output(self):
        path = os.path.join(self.pm_dir, "product-map.json")
        with open(path) as f:
            return json.load(f)

    def _setup_basic(self, tasks=None, roles=None, flows=None):
        if tasks is None:
            tasks = [{"id": "T001", "title": "Login", "category": "basic"}]
        if roles is None:
            roles = [{"id": "R001", "name": "Admin"}]
        if flows is None:
            flows = [{"id": "F001", "name": "Auth", "nodes": []}]
        self._write_artifact("product-map/task-inventory.json", {"tasks": tasks})
        self._write_artifact("product-map/role-profiles.json", {"roles": roles})
        self._write_artifact("product-map/business-flows.json", {"flows": flows})

    def test_basic_generation(self):
        self._setup_basic()
        generate_product_map(self.base_path)
        out = self._read_output()

        self.assertIn("generated_at", out)
        self.assertEqual(out["version"], "2.6.0")
        self.assertEqual(out["source"], "code-replicate")
        self.assertEqual(out["scope"], "full")
        self.assertEqual(out["summary"]["role_count"], 1)
        self.assertEqual(out["summary"]["task_count"], 1)
        self.assertEqual(out["summary"]["flow_count"], 1)

    def test_scale_small(self):
        tasks = [{"id": f"T{i:03d}", "title": f"Task {i}", "category": "basic"} for i in range(1, 20)]
        self._setup_basic(tasks=tasks)
        generate_product_map(self.base_path)
        out = self._read_output()
        self.assertEqual(out["scale"], "small")

    def test_scale_medium(self):
        tasks = [{"id": f"T{i:03d}", "title": f"Task {i}", "category": "basic"} for i in range(1, 50)]
        self._setup_basic(tasks=tasks)
        generate_product_map(self.base_path)
        out = self._read_output()
        self.assertEqual(out["scale"], "medium")

    def test_scale_large(self):
        tasks = [{"id": f"T{i:03d}", "title": f"Task {i}", "category": "basic"} for i in range(1, 100)]
        self._setup_basic(tasks=tasks)
        generate_product_map(self.base_path)
        out = self._read_output()
        self.assertEqual(out["scale"], "large")

    def test_category_counts(self):
        tasks = [
            {"id": "T001", "title": "A", "category": "basic"},
            {"id": "T002", "title": "B", "category": "basic"},
            {"id": "T003", "title": "C", "category": "core"},
            {"id": "T004", "title": "D", "category": "advanced"},
        ]
        self._setup_basic(tasks=tasks)
        generate_product_map(self.base_path)
        out = self._read_output()
        self.assertEqual(out["summary"]["basic_count"], 2)
        self.assertEqual(out["summary"]["core_count"], 1)

    def test_frequency_and_risk_counts(self):
        tasks = [
            {"id": "T001", "title": "A", "category": "basic", "frequency": "high", "risk_level": "low"},
            {"id": "T002", "title": "B", "category": "core", "frequency": "low", "risk_level": "high"},
            {"id": "T003", "title": "C", "category": "core", "frequency": "high-daily", "risk_level": "high-critical"},
        ]
        self._setup_basic(tasks=tasks)
        generate_product_map(self.base_path)
        out = self._read_output()
        self.assertEqual(out["summary"]["high_freq_count"], 2)
        self.assertEqual(out["summary"]["high_risk_count"], 2)

    def test_orphan_tasks(self):
        tasks = [
            {"id": "T001", "title": "A", "category": "basic"},
            {"id": "T002", "title": "B", "category": "basic"},
        ]
        flows = [{"id": "F001", "name": "Flow", "nodes": [{"task_id": "T001"}]}]
        self._setup_basic(tasks=tasks, flows=flows)
        generate_product_map(self.base_path)
        out = self._read_output()
        self.assertEqual(out["summary"]["orphan_task_count"], 1)

    def test_flow_gaps(self):
        flows = [
            {"id": "F001", "name": "Flow", "nodes": [
                {"id": "N1"}, {"id": "N2", "gap": True}, {"id": "N3", "gap": True}
            ]}
        ]
        self._setup_basic(flows=flows)
        generate_product_map(self.base_path)
        out = self._read_output()
        self.assertEqual(out["summary"]["flow_gaps"], 2)

    def test_constraints_loaded(self):
        self._setup_basic()
        self._write_artifact("product-map/constraints.json", {
            "constraints": [
                {"id": "C001", "text": "Must support HTTPS"},
                {"id": "C002", "text": "Max 2s response time"},
            ]
        })
        generate_product_map(self.base_path)
        out = self._read_output()
        self.assertEqual(out["summary"]["constraint_count"], 2)
        self.assertEqual(len(out["constraints"]), 2)

    def test_no_constraints_file(self):
        self._setup_basic()
        generate_product_map(self.base_path)
        out = self._read_output()
        self.assertEqual(out["summary"]["constraint_count"], 0)
        self.assertEqual(out["constraints"], [])

    def test_zero_fields(self):
        self._setup_basic()
        generate_product_map(self.base_path)
        out = self._read_output()
        self.assertEqual(out["summary"]["conflict_count"], 0)
        self.assertEqual(out["summary"]["validation_issues"], 0)
        self.assertEqual(out["summary"]["competitor_gaps"], 0)
        self.assertEqual(out["conflicts"], [])

    def test_roles_and_tasks_in_output(self):
        self._setup_basic()
        generate_product_map(self.base_path)
        out = self._read_output()
        self.assertEqual(len(out["roles"]), 1)
        self.assertEqual(out["roles"][0]["name"], "Admin")
        self.assertEqual(len(out["tasks"]), 1)
        self.assertEqual(out["tasks"][0]["id"], "T001")


if __name__ == "__main__":
    unittest.main()
