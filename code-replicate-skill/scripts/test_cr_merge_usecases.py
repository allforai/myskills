#!/usr/bin/env python3
"""Tests for cr_merge_usecases.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cr_merge_usecases import merge_usecases


class TestMergeUsecases(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base_path = os.path.join(self.tmpdir, "project")
        self.fragments_dir = os.path.join(self.tmpdir, "fragments")
        os.makedirs(os.path.join(self.fragments_dir, "usecases"), exist_ok=True)

    def _write_fragment(self, name, data):
        path = os.path.join(self.fragments_dir, "usecases", name)
        with open(path, "w") as f:
            json.dump(data, f)

    def _read_output(self):
        path = os.path.join(self.base_path, ".allforai", "use-case", "use-case-tree.json")
        with open(path) as f:
            return json.load(f)

    def _make_uc(self, title="Login", role="R001", feature_area="Auth", task_ref="T001",
                 uc_type="happy_path", given="user exists", when="enters creds", then="logged in",
                 priority="high"):
        return {
            "title": title, "role": role, "feature_area": feature_area,
            "task_ref": task_ref, "type": uc_type, "given": given,
            "when": when, "then": then, "priority": priority,
        }

    def test_basic_merge(self):
        self._write_fragment("mod1.json", {
            "use_cases": [self._make_uc(title="Login OK", role="R001", feature_area="Auth", task_ref="T001")]
        })
        self._write_fragment("mod2.json", {
            "use_cases": [self._make_uc(title="Register OK", role="R001", feature_area="Auth", task_ref="T002")]
        })
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertEqual(out["source"], "code-replicate")
        self.assertIn("generated_at", out)
        self.assertIsInstance(out["tree"], list)
        # Both under same role
        self.assertEqual(len(out["tree"]), 1)
        self.assertEqual(out["tree"][0]["role"], "R001")

    def test_id_assignment(self):
        self._write_fragment("mod.json", {
            "use_cases": [
                self._make_uc(title="UC A"),
                self._make_uc(title="UC B"),
                self._make_uc(title="UC C"),
            ]
        })
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()

        # Flatten use cases from tree
        ucs = []
        for role_node in out["tree"]:
            for fa in role_node["feature_areas"]:
                for task in fa["tasks"]:
                    ucs.extend(task["use_cases"])
        ids = [uc["id"] for uc in ucs]
        self.assertEqual(ids, ["UC001", "UC002", "UC003"])

    def test_tree_structure(self):
        """Verify 4-layer tree: role > feature_area > task > use_case."""
        self._write_fragment("mod.json", {
            "use_cases": [
                self._make_uc(title="Login", role="R001", feature_area="Auth", task_ref="T001"),
                self._make_uc(title="Logout", role="R001", feature_area="Auth", task_ref="T002"),
                self._make_uc(title="View Dashboard", role="R002", feature_area="Dashboard", task_ref="T003"),
            ]
        })
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertEqual(len(out["tree"]), 2)  # 2 roles
        r001 = out["tree"][0]
        self.assertEqual(r001["role"], "R001")
        self.assertEqual(len(r001["feature_areas"]), 1)  # Auth
        self.assertEqual(r001["feature_areas"][0]["name"], "Auth")
        self.assertEqual(len(r001["feature_areas"][0]["tasks"]), 2)  # T001, T002

        r002 = out["tree"][1]
        self.assertEqual(r002["role"], "R002")
        self.assertEqual(len(r002["feature_areas"]), 1)  # Dashboard

    def test_invalid_type_skipped(self):
        self._write_fragment("mod.json", {
            "use_cases": [
                self._make_uc(title="Good", uc_type="happy_path"),
                self._make_uc(title="Bad Type", uc_type="unknown_type"),
            ]
        })
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()

        ucs = []
        for r in out["tree"]:
            for fa in r["feature_areas"]:
                for t in fa["tasks"]:
                    ucs.extend(t["use_cases"])
        self.assertEqual(len(ucs), 1)
        self.assertEqual(ucs[0]["title"], "Good")

    def test_missing_required_fields_skipped(self):
        self._write_fragment("mod.json", {
            "use_cases": [
                self._make_uc(title="Complete"),
                {"title": "No given", "type": "happy_path", "when": "x", "then": "y"},  # missing given
                {"type": "happy_path", "given": "x", "when": "y", "then": "z"},  # missing title
            ]
        })
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()

        ucs = []
        for r in out["tree"]:
            for fa in r["feature_areas"]:
                for t in fa["tasks"]:
                    ucs.extend(t["use_cases"])
        self.assertEqual(len(ucs), 1)
        self.assertEqual(ucs[0]["title"], "Complete")

    def test_all_valid_types_accepted(self):
        ucs = [
            self._make_uc(title="Happy", uc_type="happy_path"),
            self._make_uc(title="Exception", uc_type="exception"),
            self._make_uc(title="Boundary", uc_type="boundary"),
            self._make_uc(title="Validation", uc_type="validation"),
        ]
        self._write_fragment("mod.json", {"use_cases": ucs})
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()

        all_ucs = []
        for r in out["tree"]:
            for fa in r["feature_areas"]:
                for t in fa["tasks"]:
                    all_ucs.extend(t["use_cases"])
        self.assertEqual(len(all_ucs), 4)

    def test_empty_fragments_dir(self):
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(out["tree"], [])

    def test_output_path_correct(self):
        self._write_fragment("mod.json", {"use_cases": [self._make_uc()]})
        result_path = merge_usecases(self.base_path, self.fragments_dir)
        expected = os.path.join(self.base_path, ".allforai", "use-case", "use-case-tree.json")
        self.assertEqual(result_path, expected)
        self.assertTrue(os.path.exists(expected))

    def test_default_priority(self):
        uc = self._make_uc(title="No Priority")
        del uc["priority"]
        self._write_fragment("mod.json", {"use_cases": [uc]})
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()

        all_ucs = []
        for r in out["tree"]:
            for fa in r["feature_areas"]:
                for t in fa["tasks"]:
                    all_ucs.extend(t["use_cases"])
        self.assertEqual(all_ucs[0]["priority"], "medium")

    def test_nonexistent_usecases_subdir(self):
        """If usecases/ subdir doesn't exist, should produce empty output."""
        import shutil
        shutil.rmtree(os.path.join(self.fragments_dir, "usecases"))
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(out["tree"], [])


if __name__ == "__main__":
    unittest.main()
