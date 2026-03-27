#!/usr/bin/env python3
"""Tests for cr_merge_constraints.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cr_merge_constraints import merge_constraints


class TestMergeConstraints(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base_path = os.path.join(self.tmpdir, "project")
        self.fragments_dir = os.path.join(self.tmpdir, "fragments")
        os.makedirs(os.path.join(self.fragments_dir, "constraints"), exist_ok=True)

    def _write_fragment(self, name, data):
        path = os.path.join(self.fragments_dir, "constraints", name)
        with open(path, "w") as f:
            json.dump(data, f)

    def _read_output(self):
        path = os.path.join(self.base_path, ".allforai", "product-map", "constraints.json")
        with open(path) as f:
            return json.load(f)

    def _make_constraint(self, desc="Password >= 8 chars", enforcement="hard",
                         source_ref="auth.go:42", category="validation"):
        return {
            "description": desc, "enforcement": enforcement,
            "source_ref": source_ref, "category": category,
        }

    def test_basic_merge(self):
        self._write_fragment("mod1.json", {
            "constraints": [self._make_constraint("Rule A")]
        })
        self._write_fragment("mod2.json", {
            "constraints": [self._make_constraint("Rule B")]
        })
        merge_constraints(self.base_path, self.fragments_dir)
        out = self._read_output()

        self.assertEqual(out["source"], "code-replicate")
        self.assertIn("generated_at", out)
        self.assertEqual(len(out["constraints"]), 2)

    def test_id_assignment(self):
        self._write_fragment("mod.json", {
            "constraints": [
                self._make_constraint("A"),
                self._make_constraint("B"),
                self._make_constraint("C"),
            ]
        })
        merge_constraints(self.base_path, self.fragments_dir)
        out = self._read_output()

        ids = [c["id"] for c in out["constraints"]]
        self.assertEqual(ids, ["C001", "C002", "C003"])

    def test_dedup_exact(self):
        self._write_fragment("mod1.json", {
            "constraints": [self._make_constraint("Password >= 8 chars")]
        })
        self._write_fragment("mod2.json", {
            "constraints": [self._make_constraint("Password >= 8 chars")]
        })
        merge_constraints(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["constraints"]), 1)

    def test_dedup_fuzzy_case_whitespace(self):
        """Dedup should normalize case and whitespace."""
        self._write_fragment("mod1.json", {
            "constraints": [self._make_constraint("Password  must  be >= 8 chars")]
        })
        self._write_fragment("mod2.json", {
            "constraints": [self._make_constraint("password must be >= 8 chars")]
        })
        merge_constraints(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["constraints"]), 1)
        # First occurrence kept
        self.assertIn("Password", out["constraints"][0]["description"])

    def test_dedup_leading_trailing_whitespace(self):
        self._write_fragment("mod.json", {
            "constraints": [
                self._make_constraint("  Some rule  "),
                self._make_constraint("some rule"),
            ]
        })
        merge_constraints(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["constraints"]), 1)

    def test_missing_description_skipped(self):
        self._write_fragment("mod.json", {
            "constraints": [
                self._make_constraint("Valid"),
                {"enforcement": "hard"},  # missing description
            ]
        })
        merge_constraints(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["constraints"]), 1)
        self.assertEqual(out["constraints"][0]["description"], "Valid")

    def test_missing_enforcement_skipped(self):
        self._write_fragment("mod.json", {
            "constraints": [
                self._make_constraint("Valid"),
                {"description": "No enforcement"},
            ]
        })
        merge_constraints(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["constraints"]), 1)

    def test_invalid_enforcement_skipped(self):
        self._write_fragment("mod.json", {
            "constraints": [
                self._make_constraint("Valid", enforcement="hard"),
                self._make_constraint("Bad", enforcement="maybe"),
            ]
        })
        merge_constraints(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["constraints"]), 1)
        self.assertEqual(out["constraints"][0]["description"], "Valid")

    def test_soft_enforcement_accepted(self):
        self._write_fragment("mod.json", {
            "constraints": [self._make_constraint("Soft rule", enforcement="soft")]
        })
        merge_constraints(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["constraints"]), 1)
        self.assertEqual(out["constraints"][0]["enforcement"], "soft")

    def test_empty_fragments_dir(self):
        merge_constraints(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["constraints"]), 0)

    def test_output_path_correct(self):
        self._write_fragment("mod.json", {"constraints": [self._make_constraint()]})
        result_path = merge_constraints(self.base_path, self.fragments_dir)
        expected = os.path.join(self.base_path, ".allforai", "product-map", "constraints.json")
        self.assertEqual(result_path, expected)
        self.assertTrue(os.path.exists(expected))

    def test_preserves_extra_fields(self):
        self._write_fragment("mod.json", {
            "constraints": [self._make_constraint()]
        })
        merge_constraints(self.base_path, self.fragments_dir)
        out = self._read_output()
        c = out["constraints"][0]
        self.assertEqual(c["source_ref"], "auth.go:42")
        self.assertEqual(c["category"], "validation")

    def test_nonexistent_constraints_subdir(self):
        import shutil
        shutil.rmtree(os.path.join(self.fragments_dir, "constraints"))
        merge_constraints(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(len(out["constraints"]), 0)


if __name__ == "__main__":
    unittest.main()
