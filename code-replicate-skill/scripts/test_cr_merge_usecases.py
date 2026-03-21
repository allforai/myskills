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
        self.assertEqual(out["version"], "2.5.0")
        # v2.5.0+ flat format
        self.assertIsInstance(out["use_cases"], list)
        self.assertEqual(len(out["use_cases"]), 2)

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

        ids = [uc["id"] for uc in out["use_cases"]]
        self.assertEqual(ids, ["UC001", "UC002", "UC003"])

    def test_flat_structure(self):
        """Verify flat use_cases array with explicit role/area/task fields."""
        self._write_fragment("mod.json", {
            "use_cases": [
                self._make_uc(title="Login", role="R001", feature_area="Auth", task_ref="T001"),
                self._make_uc(title="Logout", role="R001", feature_area="Auth", task_ref="T002"),
                self._make_uc(title="View Dashboard", role="R002", feature_area="Dashboard", task_ref="T003"),
            ]
        })
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertEqual(len(out["use_cases"]), 3)

        uc0 = out["use_cases"][0]
        self.assertEqual(uc0["role_id"], "R001")
        self.assertEqual(uc0["functional_area_name"], "Auth")
        self.assertEqual(uc0["task_id"], "T001")
        self.assertIn("role_name", uc0)
        self.assertIn("functional_area_id", uc0)

        # Third UC should have different role
        uc2 = out["use_cases"][2]
        self.assertEqual(uc2["role_id"], "R002")
        self.assertEqual(uc2["functional_area_name"], "Dashboard")

    def test_then_is_array(self):
        """then field must be an array, even if source is string."""
        self._write_fragment("mod.json", {
            "use_cases": [self._make_uc(title="String Then", then="single assertion")]
        })
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()

        uc = out["use_cases"][0]
        self.assertIsInstance(uc["then"], list)
        self.assertEqual(uc["then"], ["single assertion"])

    def test_then_array_preserved(self):
        """then as array should be preserved as-is."""
        self._write_fragment("mod.json", {
            "use_cases": [self._make_uc(title="Array Then", then=["a1", "a2", "a3"])]
        })
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertEqual(out["use_cases"][0]["then"], ["a1", "a2", "a3"])

    def test_invalid_type_skipped(self):
        self._write_fragment("mod.json", {
            "use_cases": [
                self._make_uc(title="Good", uc_type="happy_path"),
                self._make_uc(title="Bad Type", uc_type="unknown_type"),
            ]
        })
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertEqual(len(out["use_cases"]), 1)
        self.assertEqual(out["use_cases"][0]["title"], "Good")

    def test_extended_types_accepted(self):
        """v2.5.0+ type enum includes 13 types."""
        extended_types = [
            "happy_path", "exception", "boundary", "validation",
            "journey_guidance", "result_visibility", "continuity", "entry_clarity",
            "innovation_mechanism", "innovation_boundary",
            "state_transition", "state_timeout", "state_compensation",
        ]
        ucs = [self._make_uc(title=f"UC_{t}", uc_type=t) for t in extended_types]
        self._write_fragment("mod.json", {"use_cases": ucs})
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertEqual(len(out["use_cases"]), 13)

    def test_missing_required_fields_skipped(self):
        self._write_fragment("mod.json", {
            "use_cases": [
                self._make_uc(title="Complete"),
                {"title": "No given", "type": "happy_path", "when": "x", "then": "y"},
                {"type": "happy_path", "given": "x", "when": "y", "then": "z"},
            ]
        })
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertEqual(len(out["use_cases"]), 1)
        self.assertEqual(out["use_cases"][0]["title"], "Complete")

    def test_innovation_use_case_field(self):
        uc = self._make_uc(title="Innovation")
        uc["innovation_use_case"] = True
        self._write_fragment("mod.json", {"use_cases": [uc]})
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertTrue(out["use_cases"][0]["innovation_use_case"])

    def test_innovation_default_false(self):
        self._write_fragment("mod.json", {"use_cases": [self._make_uc()]})
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertFalse(out["use_cases"][0]["innovation_use_case"])

    def test_empty_fragments_dir(self):
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(out["use_cases"], [])

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

        self.assertEqual(out["use_cases"][0]["priority"], "medium")

    def test_nonexistent_usecases_subdir(self):
        """If usecases/ subdir doesn't exist, should produce empty output."""
        import shutil
        shutil.rmtree(os.path.join(self.fragments_dir, "usecases"))
        merge_usecases(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(out["use_cases"], [])


if __name__ == "__main__":
    unittest.main()
