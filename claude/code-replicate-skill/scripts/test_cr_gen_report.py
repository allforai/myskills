#!/usr/bin/env python3
"""Tests for cr_gen_report.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cr_gen_report import generate_report


class TestGenerateReport(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base_path = os.path.join(self.tmpdir, "project")
        self.cr_dir = os.path.join(self.base_path, ".allforai", "code-replicate")
        os.makedirs(self.cr_dir, exist_ok=True)

    def _write_artifact(self, rel_path, data):
        path = os.path.join(self.base_path, ".allforai", rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)

    def _read_output(self):
        path = os.path.join(self.cr_dir, "replicate-report.md")
        with open(path) as f:
            return f.read()

    def _setup_basic(self):
        self._write_artifact("code-replicate/replicate-config.json", {
            "source_path": "/src/project",
            "fidelity": "high",
            "target_stack": "Next.js + PostgreSQL",
            "source_overview": {
                "module_count": 5,
                "file_count": 120,
                "line_count": 8500,
                "detected_stacks": ["React", "Node.js", "PostgreSQL"]
            }
        })
        self._write_artifact("product-map/role-profiles.json", {
            "roles": [{"id": "R001", "name": "Admin"}, {"id": "R002", "name": "User"}]
        })
        self._write_artifact("product-map/task-inventory.json", {
            "tasks": [{"id": "T001"}, {"id": "T002"}, {"id": "T003"}]
        })
        self._write_artifact("product-map/business-flows.json", {
            "flows": [{"id": "F001"}]
        })
        self._write_artifact("use-case/use-case-tree.json", {
            "roles": [
                {"role_id": "R001", "features": [
                    {"use_cases": [{"id": "UC001"}, {"id": "UC002"}]}
                ]}
            ]
        })

    def test_basic_report(self):
        self._setup_basic()
        generate_report(self.base_path)
        md = self._read_output()

        self.assertIn("# Code Replicate Report", md)
        self.assertIn("/src/project", md)
        self.assertIn("high", md)
        self.assertIn("Next.js + PostgreSQL", md)

    def test_source_overview(self):
        self._setup_basic()
        generate_report(self.base_path)
        md = self._read_output()

        self.assertIn("| Modules | 5 |", md)
        self.assertIn("| Files | 120 |", md)
        self.assertIn("| Lines | 8500 |", md)
        self.assertIn("React, Node.js, PostgreSQL", md)

    def test_artifact_counts(self):
        self._setup_basic()
        generate_report(self.base_path)
        md = self._read_output()

        self.assertIn("| Roles | product-map/role-profiles.json | 2 |", md)
        self.assertIn("| Tasks | product-map/task-inventory.json | 3 |", md)
        self.assertIn("| Flows | product-map/business-flows.json | 1 |", md)
        self.assertIn("| Use Cases | use-case/use-case-tree.json | 2 |", md)

    def test_next_steps(self):
        self._setup_basic()
        generate_report(self.base_path)
        md = self._read_output()
        self.assertIn("/project-setup", md)
        self.assertIn("/design-to-spec", md)
        self.assertIn("/task-execute", md)

    def test_returns_path(self):
        self._setup_basic()
        path = generate_report(self.base_path)
        expected = os.path.join(self.cr_dir, "replicate-report.md")
        self.assertEqual(path, expected)
        self.assertTrue(os.path.exists(expected))

    def test_missing_optional_artifacts(self):
        """Report should still generate if some artifacts are missing."""
        self._write_artifact("code-replicate/replicate-config.json", {
            "source_path": "/src",
            "fidelity": "medium",
            "target_stack": "Django",
            "source_overview": {
                "module_count": 2,
                "file_count": 30,
                "line_count": 2000,
                "detected_stacks": ["Python"]
            }
        })
        generate_report(self.base_path)
        md = self._read_output()
        self.assertIn("# Code Replicate Report", md)
        self.assertIn("| Roles | product-map/role-profiles.json | 0 |", md)

    def test_warnings_section(self):
        self._setup_basic()
        # Add warnings to config
        self._write_artifact("code-replicate/replicate-config.json", {
            "source_path": "/src/project",
            "fidelity": "high",
            "target_stack": "Next.js",
            "source_overview": {
                "module_count": 5,
                "file_count": 120,
                "line_count": 8500,
                "detected_stacks": ["React"]
            },
            "warnings": ["Module X skipped: binary files", "Module Y: no source files"]
        })
        generate_report(self.base_path)
        md = self._read_output()
        self.assertIn("## Warnings", md)
        self.assertIn("Module X skipped: binary files", md)
        self.assertIn("Module Y: no source files", md)

    def test_no_warnings(self):
        self._setup_basic()
        generate_report(self.base_path)
        md = self._read_output()
        self.assertIn("## Warnings", md)
        self.assertIn("No warnings", md)

    def test_usecase_count_from_nested(self):
        """Use case count should sum across all roles and features."""
        self._setup_basic()
        self._write_artifact("use-case/use-case-tree.json", {
            "roles": [
                {"role_id": "R001", "features": [
                    {"use_cases": [{"id": "UC001"}, {"id": "UC002"}]},
                    {"use_cases": [{"id": "UC003"}]}
                ]},
                {"role_id": "R002", "features": [
                    {"use_cases": [{"id": "UC004"}]}
                ]}
            ]
        })
        generate_report(self.base_path)
        md = self._read_output()
        self.assertIn("| Use Cases | use-case/use-case-tree.json | 4 |", md)


if __name__ == "__main__":
    unittest.main()
