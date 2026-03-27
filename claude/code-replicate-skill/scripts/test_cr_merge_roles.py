#!/usr/bin/env python3
"""Tests for cr_merge_roles.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cr_merge_roles import merge_roles


class TestMergeRoles(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base_path = os.path.join(self.tmpdir, "project")
        self.fragments_dir = os.path.join(self.tmpdir, "fragments")
        os.makedirs(os.path.join(self.fragments_dir, "roles"), exist_ok=True)

    def _write_fragment(self, name, data):
        path = os.path.join(self.fragments_dir, "roles", name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def _read_output(self):
        path = os.path.join(self.base_path, ".allforai", "product-map", "role-profiles.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_basic_merge(self):
        self._write_fragment("mod1.json", {
            "roles": [{"name": "Admin", "responsibilities": ["manage users"]}]
        })
        self._write_fragment("mod2.json", {
            "roles": [{"name": "Editor", "responsibilities": ["edit content"]}]
        })
        merge_roles(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertEqual(out["source"], "code-replicate")
        self.assertIn("generated_at", out)
        self.assertEqual(len(out["roles"]), 2)
        self.assertEqual(out["roles"][0]["id"], "R001")
        self.assertEqual(out["roles"][0]["name"], "Admin")
        self.assertEqual(out["roles"][1]["id"], "R002")
        self.assertEqual(out["roles"][1]["name"], "Editor")

    def test_dedup_case_insensitive(self):
        self._write_fragment("mod1.json", {
            "roles": [{"name": "Admin", "responsibilities": ["a"]}]
        })
        self._write_fragment("mod2.json", {
            "roles": [{"name": "admin", "responsibilities": ["b"]},
                       {"name": "ADMIN", "responsibilities": ["c"]}]
        })
        merge_roles(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertEqual(len(out["roles"]), 1)
        # First occurrence kept
        self.assertEqual(out["roles"][0]["name"], "Admin")

    def test_empty_fragments_dir(self):
        merge_roles(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["roles"]), 0)

    def test_single_fragment(self):
        self._write_fragment("only.json", {
            "roles": [
                {"name": "Viewer"},
                {"name": "Admin"},
            ]
        })
        merge_roles(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["roles"]), 2)
        self.assertEqual(out["roles"][0]["id"], "R001")
        self.assertEqual(out["roles"][1]["id"], "R002")

    def test_overlapping_data_across_fragments(self):
        self._write_fragment("a.json", {
            "roles": [{"name": "Admin"}, {"name": "Editor"}]
        })
        self._write_fragment("b.json", {
            "roles": [{"name": "Editor"}, {"name": "Viewer"}]
        })
        merge_roles(self.base_path, self.fragments_dir)
        out = self._read_output()

        names = [r["name"] for r in out["roles"]]
        self.assertEqual(names, ["Admin", "Editor", "Viewer"])

    def test_output_path_correct(self):
        self._write_fragment("mod.json", {"roles": [{"name": "X"}]})
        result_path = merge_roles(self.base_path, self.fragments_dir)
        expected = os.path.join(self.base_path, ".allforai", "product-map", "role-profiles.json")
        self.assertEqual(result_path, expected)
        self.assertTrue(os.path.exists(expected))

    def test_roles_without_name_skipped(self):
        self._write_fragment("mod.json", {
            "roles": [{"name": ""}, {"responsibilities": ["x"]}, {"name": "Valid"}]
        })
        merge_roles(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["roles"]), 1)
        self.assertEqual(out["roles"][0]["name"], "Valid")

    def test_nonexistent_roles_subdir(self):
        """If roles/ subdir doesn't exist, should produce empty output."""
        import shutil
        shutil.rmtree(os.path.join(self.fragments_dir, "roles"))
        merge_roles(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["roles"]), 0)


if __name__ == "__main__":
    unittest.main()
