#!/usr/bin/env python3
"""Tests for cr_gen_usecase_report.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cr_gen_usecase_report import generate_usecase_report


class TestGenerateUsecaseReport(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base_path = os.path.join(self.tmpdir, "project")
        self.uc_dir = os.path.join(self.base_path, ".allforai", "use-case")
        os.makedirs(self.uc_dir, exist_ok=True)

    def _write_artifact(self, rel_path, data):
        path = os.path.join(self.base_path, ".allforai", rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)

    def _read_output(self):
        path = os.path.join(self.uc_dir, "use-case-report.md")
        with open(path) as f:
            return f.read()

    def test_basic_report(self):
        self._write_artifact("use-case/use-case-tree.json", {
            "roles": [
                {
                    "role_id": "R001",
                    "role_name": "Admin",
                    "features": [
                        {
                            "area": "Authentication",
                            "use_cases": [
                                {"id": "UC001", "title": "Login with valid credentials", "type": "happy_path", "priority": "high"},
                                {"id": "UC002", "title": "Login with wrong password", "type": "exception", "priority": "high"},
                            ]
                        }
                    ]
                }
            ]
        })
        generate_usecase_report(self.base_path)
        md = self._read_output()

        self.assertIn("# Use Case Report", md)
        self.assertIn("code-replicate", md)
        self.assertIn("## Admin", md)
        self.assertIn("### Authentication", md)
        self.assertIn("UC001", md)
        self.assertIn("Login with valid credentials", md)
        self.assertIn("happy_path", md)
        self.assertIn("UC002", md)
        self.assertIn("2 use cases across 1 roles, 1 feature areas", md)

    def test_multiple_roles(self):
        self._write_artifact("use-case/use-case-tree.json", {
            "roles": [
                {
                    "role_id": "R001",
                    "role_name": "Admin",
                    "features": [
                        {"area": "Users", "use_cases": [
                            {"id": "UC001", "title": "Manage users", "type": "happy_path", "priority": "high"}
                        ]}
                    ]
                },
                {
                    "role_id": "R002",
                    "role_name": "Viewer",
                    "features": [
                        {"area": "Dashboard", "use_cases": [
                            {"id": "UC002", "title": "View stats", "type": "happy_path", "priority": "medium"}
                        ]}
                    ]
                }
            ]
        })
        generate_usecase_report(self.base_path)
        md = self._read_output()

        self.assertIn("## Admin", md)
        self.assertIn("## Viewer", md)
        self.assertIn("2 use cases across 2 roles, 2 feature areas", md)

    def test_empty_use_cases(self):
        self._write_artifact("use-case/use-case-tree.json", {"roles": []})
        generate_usecase_report(self.base_path)
        md = self._read_output()
        self.assertIn("# Use Case Report", md)
        self.assertIn("0 use cases across 0 roles, 0 feature areas", md)

    def test_table_format(self):
        self._write_artifact("use-case/use-case-tree.json", {
            "roles": [
                {
                    "role_id": "R001",
                    "role_name": "User",
                    "features": [
                        {"area": "Auth", "use_cases": [
                            {"id": "UC001", "title": "Login", "type": "happy_path", "priority": "high"}
                        ]}
                    ]
                }
            ]
        })
        generate_usecase_report(self.base_path)
        md = self._read_output()
        self.assertIn("| ID | Title | Type | Priority |", md)
        self.assertIn("|----|-------|------|----------|", md)
        self.assertIn("| UC001 | Login | happy_path | high |", md)

    def test_returns_path(self):
        self._write_artifact("use-case/use-case-tree.json", {"roles": []})
        path = generate_usecase_report(self.base_path)
        expected = os.path.join(self.uc_dir, "use-case-report.md")
        self.assertEqual(path, expected)
        self.assertTrue(os.path.exists(expected))

    def test_missing_fields_default(self):
        """Use cases with missing fields should use empty strings."""
        self._write_artifact("use-case/use-case-tree.json", {
            "roles": [
                {
                    "role_id": "R001",
                    "role_name": "User",
                    "features": [
                        {"area": "Auth", "use_cases": [
                            {"id": "UC001", "title": "Login"}
                        ]}
                    ]
                }
            ]
        })
        generate_usecase_report(self.base_path)
        md = self._read_output()
        self.assertIn("UC001", md)
        self.assertIn("Login", md)


if __name__ == "__main__":
    unittest.main()
