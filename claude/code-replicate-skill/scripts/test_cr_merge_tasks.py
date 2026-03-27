#!/usr/bin/env python3
"""Tests for cr_merge_tasks.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cr_merge_tasks import merge_tasks, REQUIRED_FIELDS, RECOMMENDED_STRING_FIELDS, RECOMMENDED_ARRAY_FIELDS


class TestMergeTasks(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base_path = os.path.join(self.tmpdir, "project")
        self.fragments_dir = os.path.join(self.tmpdir, "fragments")
        os.makedirs(os.path.join(self.fragments_dir, "tasks"), exist_ok=True)

    def _write_fragment(self, name, data):
        path = os.path.join(self.fragments_dir, "tasks", name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def _read_output(self):
        path = os.path.join(self.base_path, ".allforai", "product-map", "task-inventory.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_basic_merge(self):
        self._write_fragment("mod1.json", {
            "tasks": [{"name": "Create User", "owner_role": "R001",
                        "frequency": "daily", "risk_level": "low",
                        "main_flow": "F001", "status": "active", "category": "user-mgmt"}]
        })
        self._write_fragment("mod2.json", {
            "tasks": [{"name": "Delete User", "owner_role": "R001",
                        "frequency": "rare", "risk_level": "high",
                        "main_flow": "F001", "status": "active", "category": "user-mgmt"}]
        })
        merge_tasks(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertEqual(out["source"], "code-replicate")
        self.assertEqual(len(out["tasks"]), 2)
        self.assertEqual(out["tasks"][0]["id"], "T001")
        self.assertEqual(out["tasks"][1]["id"], "T002")
        # Must be array
        self.assertIsInstance(out["tasks"], list)

    def test_dedup_by_name_and_owner(self):
        self._write_fragment("a.json", {
            "tasks": [{"name": "Create User", "owner_role": "R001"}]
        })
        self._write_fragment("b.json", {
            "tasks": [
                {"name": "Create User", "owner_role": "R001"},  # dup
                {"name": "Create User", "owner_role": "R002"},  # different owner, keep
            ]
        })
        merge_tasks(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["tasks"]), 2)

    def test_dedup_case_insensitive_name(self):
        self._write_fragment("a.json", {
            "tasks": [{"name": "Create User", "owner_role": "R001"}]
        })
        self._write_fragment("b.json", {
            "tasks": [{"name": "create user", "owner_role": "R001"}]
        })
        merge_tasks(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["tasks"]), 1)

    def test_required_fields_filled(self):
        """Tasks missing required fields get '[INFERRED]' placeholder."""
        self._write_fragment("mod.json", {
            "tasks": [{"name": "Minimal Task", "owner_role": "R001"}]
        })
        merge_tasks(self.base_path, self.fragments_dir)
        out = self._read_output()
        task = out["tasks"][0]
        for field in REQUIRED_FIELDS:
            self.assertIn(field, task, f"Missing required field: {field}")

    def test_recommended_fields_filled(self):
        """Missing recommended fields auto-filled."""
        self._write_fragment("mod.json", {
            "tasks": [{"name": "Task", "owner_role": "R001"}]
        })
        merge_tasks(self.base_path, self.fragments_dir)
        task = self._read_output()["tasks"][0]

        for field in RECOMMENDED_STRING_FIELDS:
            self.assertEqual(task[field], "[INFERRED]")
        for field in RECOMMENDED_ARRAY_FIELDS:
            self.assertIsInstance(task[field], list)

    def test_empty_fragments_dir(self):
        merge_tasks(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["tasks"]), 0)

    def test_single_fragment(self):
        self._write_fragment("only.json", {
            "tasks": [
                {"name": "A", "owner_role": "R001"},
                {"name": "B", "owner_role": "R002"},
            ]
        })
        merge_tasks(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["tasks"]), 2)

    def test_overlapping_data(self):
        self._write_fragment("a.json", {
            "tasks": [{"name": "A", "owner_role": "R001"}, {"name": "B", "owner_role": "R001"}]
        })
        self._write_fragment("b.json", {
            "tasks": [{"name": "B", "owner_role": "R001"}, {"name": "C", "owner_role": "R001"}]
        })
        merge_tasks(self.base_path, self.fragments_dir)
        out = self._read_output()
        names = [t["name"] for t in out["tasks"]]
        self.assertEqual(names, ["A", "B", "C"])

    def test_output_path_correct(self):
        self._write_fragment("mod.json", {"tasks": [{"name": "X", "owner_role": "R001"}]})
        result_path = merge_tasks(self.base_path, self.fragments_dir)
        expected = os.path.join(self.base_path, ".allforai", "product-map", "task-inventory.json")
        self.assertEqual(result_path, expected)

    def test_tasks_without_name_skipped(self):
        self._write_fragment("mod.json", {
            "tasks": [{"name": "", "owner_role": "R001"}, {"owner_role": "R001"}, {"name": "Valid", "owner_role": "R001"}]
        })
        merge_tasks(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["tasks"]), 1)


if __name__ == "__main__":
    unittest.main()
