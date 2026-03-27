#!/usr/bin/env python3
"""Tests for cr_merge_flows.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import FLOW_NODES_FIELD
from cr_merge_flows import merge_flows


class TestMergeFlows(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base_path = os.path.join(self.tmpdir, "project")
        self.fragments_dir = os.path.join(self.tmpdir, "fragments")
        os.makedirs(os.path.join(self.fragments_dir, "flows"), exist_ok=True)

    def _write_fragment(self, name, data):
        path = os.path.join(self.fragments_dir, "flows", name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def _write_task_inventory(self, tasks):
        """Write a task-inventory.json so cross-referencing works."""
        path = os.path.join(self.base_path, ".allforai", "product-map", "task-inventory.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"tasks": tasks}, f, ensure_ascii=False)

    def _read_output(self):
        path = os.path.join(self.base_path, ".allforai", "product-map", "business-flows.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_basic_merge(self):
        self._write_fragment("mod1.json", {
            "flows": [{
                "name": "User Registration",
                FLOW_NODES_FIELD: [
                    {"task_ref": "T001", "role": "R001", "seq": 1},
                    {"task_ref": "T002", "role": "R001", "seq": 2},
                ]
            }]
        })
        self._write_fragment("mod2.json", {
            "flows": [{
                "name": "Order Processing",
                FLOW_NODES_FIELD: [
                    {"task_ref": "T003", "role": "R002", "seq": 1},
                ]
            }]
        })
        merge_flows(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertEqual(out["source"], "code-replicate")
        self.assertEqual(len(out["flows"]), 2)
        self.assertEqual(out["flows"][0]["id"], "F001")
        self.assertEqual(out["flows"][1]["id"], "F002")
        self.assertEqual(out["summary"]["flow_count"], 2)

    def test_dedup_by_name(self):
        self._write_fragment("a.json", {
            "flows": [{"name": "User Registration", FLOW_NODES_FIELD: []}]
        })
        self._write_fragment("b.json", {
            "flows": [{"name": "user registration", FLOW_NODES_FIELD: []}]
        })
        merge_flows(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["flows"]), 1)

    def test_node_validation_fills_missing_fields(self):
        self._write_fragment("mod.json", {
            "flows": [{
                "name": "Incomplete Flow",
                FLOW_NODES_FIELD: [{"task_ref": "T001"}]  # missing role, seq
            }]
        })
        merge_flows(self.base_path, self.fragments_dir)
        out = self._read_output()
        node = out["flows"][0][FLOW_NODES_FIELD][0]
        self.assertEqual(node["role"], "[INFERRED]")
        self.assertEqual(node["seq"], "[INFERRED]")

    def test_missing_nodes_field(self):
        self._write_fragment("mod.json", {
            "flows": [{"name": "No Nodes Flow"}]
        })
        merge_flows(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(out["flows"][0][FLOW_NODES_FIELD], [])

    def test_cross_reference_warns_missing_task_ref(self):
        """If task_ref not in inventory, warn but don't fail."""
        self._write_task_inventory([{"id": "T001", "name": "Exists"}])
        self._write_fragment("mod.json", {
            "flows": [{
                "name": "Flow",
                FLOW_NODES_FIELD: [
                    {"task_ref": "T001", "role": "R001", "seq": 1},
                    {"task_ref": "T999", "role": "R001", "seq": 2},  # doesn't exist
                ]
            }]
        })
        # Should not raise
        merge_flows(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["flows"]), 1)

    def test_orphan_tasks(self):
        self._write_task_inventory([
            {"id": "T001", "name": "Used"},
            {"id": "T002", "name": "Orphan"},
            {"id": "T003", "name": "Also Orphan"},
        ])
        self._write_fragment("mod.json", {
            "flows": [{
                "name": "Flow",
                FLOW_NODES_FIELD: [{"task_ref": "T001", "role": "R001", "seq": 1}]
            }]
        })
        merge_flows(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(sorted(out["orphan_tasks"]), ["T002", "T003"])
        self.assertEqual(out["summary"]["orphan_count"], 2)

    def test_empty_fragments_dir(self):
        merge_flows(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["flows"]), 0)
        self.assertEqual(out["summary"]["flow_count"], 0)

    def test_single_fragment(self):
        self._write_fragment("only.json", {
            "flows": [
                {"name": "A", FLOW_NODES_FIELD: []},
                {"name": "B", FLOW_NODES_FIELD: []},
            ]
        })
        merge_flows(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["flows"]), 2)

    def test_overlapping_data(self):
        self._write_fragment("a.json", {
            "flows": [
                {"name": "A", FLOW_NODES_FIELD: []},
                {"name": "B", FLOW_NODES_FIELD: []},
            ]
        })
        self._write_fragment("b.json", {
            "flows": [
                {"name": "B", FLOW_NODES_FIELD: []},
                {"name": "C", FLOW_NODES_FIELD: []},
            ]
        })
        merge_flows(self.base_path, self.fragments_dir)
        out = self._read_output()
        names = [f["name"] for f in out["flows"]]
        self.assertEqual(names, ["A", "B", "C"])

    def test_output_path_correct(self):
        self._write_fragment("mod.json", {"flows": [{"name": "X", FLOW_NODES_FIELD: []}]})
        result_path = merge_flows(self.base_path, self.fragments_dir)
        expected = os.path.join(self.base_path, ".allforai", "product-map", "business-flows.json")
        self.assertEqual(result_path, expected)

    def test_no_task_inventory_still_works(self):
        """Orphan calculation degrades gracefully without task-inventory."""
        self._write_fragment("mod.json", {
            "flows": [{
                "name": "Flow",
                FLOW_NODES_FIELD: [{"task_ref": "T001", "role": "R001", "seq": 1}]
            }]
        })
        merge_flows(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(out["orphan_tasks"], [])


if __name__ == "__main__":
    unittest.main()
