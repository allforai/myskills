#!/usr/bin/env python3
"""Tests for cr_validate.py."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import FLOW_NODES_FIELD
from cr_validate import validate


def _make_task(tid, **overrides):
    """Create a valid task dict with sensible defaults."""
    base = {
        "id": tid,
        "name": f"Task {tid}",
        "owner_role": "R001",
        "frequency": "daily",
        "risk_level": "low",
        "main_flow": "F001",
        "status": "active",
        "category": "core",
    }
    base.update(overrides)
    return base


def _make_role(rid, **overrides):
    base = {"id": rid, "name": f"Role {rid}"}
    base.update(overrides)
    return base


def _make_flow(name, nodes):
    return {"id": "F001", "name": name, FLOW_NODES_FIELD: nodes}


class TestValidateAllValid(unittest.TestCase):
    """Scenario: all files valid → exit 0, valid=true."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base = self.tmpdir
        self.pm = os.path.join(self.base, ".allforai", "product-map")
        os.makedirs(self.pm, exist_ok=True)

    def _write(self, name, data):
        with open(os.path.join(self.pm, name), "w") as f:
            json.dump(data, f)

    def _setup_valid(self):
        self._write("task-inventory.json", {
            "tasks": [_make_task("T001"), _make_task("T002")]
        })
        self._write("role-profiles.json", {
            "roles": [_make_role("R001"), _make_role("R002")]
        })
        self._write("business-flows.json", {
            "flows": [_make_flow("Registration", [
                {"task_ref": "T001", "role": "R001", "seq": 1},
                {"task_ref": "T002", "role": "R002", "seq": 2},
            ])]
        })

    def test_all_valid(self):
        self._setup_valid()
        result = validate(self.base, fullstack=False)
        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["stats"]["tasks"], 2)
        self.assertEqual(result["stats"]["roles"], 2)
        self.assertEqual(result["stats"]["flows"], 1)
        self.assertAlmostEqual(result["stats"]["task_ref_coverage"], 1.0)

    def test_minimal_valid_no_optional(self):
        """Only required files present → valid with warnings."""
        self._write("task-inventory.json", {"tasks": [_make_task("T001")]})
        self._write("role-profiles.json", {"roles": [_make_role("R001")]})
        result = validate(self.base, fullstack=False)
        self.assertTrue(result["valid"])
        self.assertEqual(result["stats"]["flows"], 0)
        self.assertEqual(result["stats"]["task_ref_coverage"], 0.0)


class TestTaskInventoryValidation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base = self.tmpdir
        self.pm = os.path.join(self.base, ".allforai", "product-map")
        os.makedirs(self.pm, exist_ok=True)

    def _write(self, name, data):
        with open(os.path.join(self.pm, name), "w") as f:
            json.dump(data, f)

    def _write_roles(self):
        self._write("role-profiles.json", {"roles": [_make_role("R001")]})

    def test_missing_task_inventory(self):
        self._write_roles()
        result = validate(self.base)
        self.assertFalse(result["valid"])
        self.assertTrue(any("task-inventory.json" in e["file"] for e in result["errors"]))

    def test_tasks_not_array(self):
        self._write("task-inventory.json", {"tasks": {"T001": {"name": "bad"}}})
        self._write_roles()
        result = validate(self.base)
        self.assertFalse(result["valid"])
        self.assertTrue(any("not an array" in e["issue"] for e in result["errors"]))

    def test_missing_required_field(self):
        task = _make_task("T001")
        del task["main_flow"]
        self._write("task-inventory.json", {"tasks": [task]})
        self._write_roles()
        result = validate(self.base)
        self.assertFalse(result["valid"])
        self.assertTrue(any("main_flow" in e["issue"] for e in result["errors"]))

    def test_duplicate_task_ids(self):
        self._write("task-inventory.json", {
            "tasks": [_make_task("T001"), _make_task("T001", name="Dup")]
        })
        self._write_roles()
        result = validate(self.base)
        self.assertFalse(result["valid"])
        self.assertTrue(any("duplicate" in e["issue"].lower() for e in result["errors"]))


class TestRoleProfilesValidation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base = self.tmpdir
        self.pm = os.path.join(self.base, ".allforai", "product-map")
        os.makedirs(self.pm, exist_ok=True)

    def _write(self, name, data):
        with open(os.path.join(self.pm, name), "w") as f:
            json.dump(data, f)

    def test_missing_role_profiles(self):
        self._write("task-inventory.json", {"tasks": [_make_task("T001")]})
        result = validate(self.base)
        self.assertFalse(result["valid"])
        self.assertTrue(any("role-profiles.json" in e["file"] for e in result["errors"]))

    def test_duplicate_role_ids(self):
        self._write("task-inventory.json", {"tasks": [_make_task("T001")]})
        self._write("role-profiles.json", {
            "roles": [_make_role("R001"), _make_role("R001", name="Dup")]
        })
        result = validate(self.base)
        self.assertFalse(result["valid"])
        self.assertTrue(any("duplicate" in e["issue"].lower() for e in result["errors"]))


class TestBusinessFlowsValidation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base = self.tmpdir
        self.pm = os.path.join(self.base, ".allforai", "product-map")
        os.makedirs(self.pm, exist_ok=True)

    def _write(self, name, data):
        with open(os.path.join(self.pm, name), "w") as f:
            json.dump(data, f)

    def _setup_base(self):
        self._write("task-inventory.json", {
            "tasks": [_make_task("T001"), _make_task("T002")]
        })
        self._write("role-profiles.json", {
            "roles": [_make_role("R001")]
        })

    def test_broken_task_ref(self):
        self._setup_base()
        self._write("business-flows.json", {
            "flows": [_make_flow("F", [
                {"task_ref": "T999", "role": "R001", "seq": 1}
            ])]
        })
        result = validate(self.base)
        self.assertFalse(result["valid"])
        self.assertTrue(any("T999" in e["issue"] for e in result["errors"]))

    def test_broken_role_ref(self):
        self._setup_base()
        self._write("business-flows.json", {
            "flows": [_make_flow("F", [
                {"task_ref": "T001", "role": "R999", "seq": 1}
            ])]
        })
        result = validate(self.base)
        self.assertFalse(result["valid"])
        self.assertTrue(any("R999" in e["issue"] for e in result["errors"]))

    def test_missing_nodes_field(self):
        self._setup_base()
        self._write("business-flows.json", {
            "flows": [{"id": "F001", "name": "Bad Flow"}]
        })
        result = validate(self.base)
        self.assertFalse(result["valid"])
        self.assertTrue(any("nodes" in e["issue"].lower() for e in result["errors"]))

    def test_node_missing_required_fields(self):
        self._setup_base()
        self._write("business-flows.json", {
            "flows": [_make_flow("F", [{"task_ref": "T001"}])]
        })
        result = validate(self.base)
        self.assertFalse(result["valid"])
        errors = [e["issue"] for e in result["errors"]]
        self.assertTrue(any("role" in e for e in errors))
        self.assertTrue(any("seq" in e for e in errors))


class TestUseCaseTreeValidation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base = self.tmpdir
        self.pm = os.path.join(self.base, ".allforai", "product-map")
        self.uc = os.path.join(self.base, ".allforai", "use-case")
        os.makedirs(self.pm, exist_ok=True)
        os.makedirs(self.uc, exist_ok=True)

    def _write(self, dir_path, name, data):
        with open(os.path.join(dir_path, name), "w") as f:
            json.dump(data, f)

    def _setup_base(self):
        self._write(self.pm, "task-inventory.json", {"tasks": [_make_task("T001")]})
        self._write(self.pm, "role-profiles.json", {"roles": [_make_role("R001")]})

    def test_valid_use_case_tree(self):
        self._setup_base()
        self._write(self.uc, "use-case-tree.json", {
            "tree": [{
                "role": "R001",
                "feature_areas": [{
                    "name": "Auth",
                    "tasks": [{
                        "task_id": "T001",
                        "use_cases": [{
                            "id": "UC001",
                            "title": "Login",
                            "type": "happy",
                            "given": "user exists",
                            "when": "enters creds",
                            "then": "logged in"
                        }]
                    }]
                }]
            }]
        })
        result = validate(self.base)
        self.assertTrue(result["valid"])
        self.assertEqual(result["stats"]["use_cases"], 1)

    def test_use_case_missing_required_field(self):
        self._setup_base()
        self._write(self.uc, "use-case-tree.json", {
            "tree": [{
                "role": "R001",
                "feature_areas": [{
                    "name": "Auth",
                    "tasks": [{
                        "task_id": "T001",
                        "use_cases": [{
                            "id": "UC001",
                            "title": "Login",
                            # missing type, given, when, then
                        }]
                    }]
                }]
            }]
        })
        result = validate(self.base)
        self.assertFalse(result["valid"])
        self.assertTrue(any("type" in e["issue"] for e in result["errors"]))


class TestConstraintsValidation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base = self.tmpdir
        self.pm = os.path.join(self.base, ".allforai", "product-map")
        os.makedirs(self.pm, exist_ok=True)

    def _write(self, name, data):
        with open(os.path.join(self.pm, name), "w") as f:
            json.dump(data, f)

    def _setup_base(self):
        self._write("task-inventory.json", {"tasks": [_make_task("T001")]})
        self._write("role-profiles.json", {"roles": [_make_role("R001")]})

    def test_missing_constraints_is_warning(self):
        self._setup_base()
        result = validate(self.base)
        self.assertTrue(result["valid"])
        self.assertTrue(any("constraints.json" in w.get("file", "") or "constraints.json" in w.get("issue", "") for w in result["warnings"]))

    def test_invalid_constraint_missing_fields(self):
        self._setup_base()
        self._write("constraints.json", {
            "constraints": [{"id": "C001"}]  # missing description, enforcement
        })
        result = validate(self.base)
        self.assertFalse(result["valid"])


class TestExperienceMapValidation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base = self.tmpdir
        self.pm = os.path.join(self.base, ".allforai", "product-map")
        self.em = os.path.join(self.base, ".allforai", "experience-map")
        os.makedirs(self.pm, exist_ok=True)
        os.makedirs(self.em, exist_ok=True)

    def _write(self, dir_path, name, data):
        with open(os.path.join(dir_path, name), "w") as f:
            json.dump(data, f)

    def _setup_base(self):
        self._write(self.pm, "task-inventory.json", {"tasks": [_make_task("T001")]})
        self._write(self.pm, "role-profiles.json", {"roles": [_make_role("R001")]})

    def test_missing_experience_map_is_warning(self):
        self._setup_base()
        result = validate(self.base)
        self.assertTrue(result["valid"])
        self.assertTrue(any("experience-map.json" in w.get("file", "") or "experience-map.json" in w.get("issue", "") for w in result["warnings"]))

    def test_valid_experience_map(self):
        self._setup_base()
        self._write(self.em, "experience-map.json", {
            "operation_lines": [{"id": "OL001", "name": "Main"}]
        })
        result = validate(self.base)
        self.assertTrue(result["valid"])


class TestCrossRefCoverage(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base = self.tmpdir
        self.pm = os.path.join(self.base, ".allforai", "product-map")
        os.makedirs(self.pm, exist_ok=True)

    def _write(self, name, data):
        with open(os.path.join(self.pm, name), "w") as f:
            json.dump(data, f)

    def test_partial_coverage(self):
        self._write("task-inventory.json", {
            "tasks": [_make_task("T001"), _make_task("T002"), _make_task("T003"), _make_task("T004")]
        })
        self._write("role-profiles.json", {"roles": [_make_role("R001")]})
        self._write("business-flows.json", {
            "flows": [_make_flow("F", [
                {"task_ref": "T001", "role": "R001", "seq": 1},
                {"task_ref": "T002", "role": "R001", "seq": 2},
            ])]
        })
        result = validate(self.base)
        self.assertTrue(result["valid"])
        self.assertAlmostEqual(result["stats"]["task_ref_coverage"], 0.5)


class TestFullstackMode(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base = self.tmpdir
        self.pm = os.path.join(self.base, ".allforai", "product-map")
        self.cr = os.path.join(self.base, ".allforai", "code-replicate")
        os.makedirs(self.pm, exist_ok=True)
        os.makedirs(self.cr, exist_ok=True)

    def _write(self, dir_path, name, data):
        with open(os.path.join(dir_path, name), "w") as f:
            json.dump(data, f)

    def _setup_base(self):
        self._write(self.pm, "task-inventory.json", {
            "tasks": [_make_task("T001"), _make_task("T002")]
        })
        self._write(self.pm, "role-profiles.json", {"roles": [_make_role("R001")]})

    def test_fullstack_api_call_map_valid(self):
        self._setup_base()
        self._write(self.cr, "source-summary.json", {
            "api_call_map": [
                {"frontend_call": "POST /api/users", "backend_task_ref": "T001"},
                {"frontend_call": "GET /api/users", "backend_task_ref": "T002"},
            ]
        })
        result = validate(self.base, fullstack=True)
        self.assertTrue(result["valid"])

    def test_fullstack_unmatched_api_call(self):
        self._setup_base()
        self._write(self.cr, "source-summary.json", {
            "api_call_map": [
                {"frontend_call": "POST /api/users", "backend_task_ref": "T001"},
                {"frontend_call": "DELETE /api/users", "backend_task_ref": "T999"},
            ]
        })
        result = validate(self.base, fullstack=True)
        # Unmatched calls are warnings, not errors
        self.assertTrue(result["valid"])
        self.assertTrue(any("T999" in w["issue"] for w in result["warnings"]))

    def test_fullstack_no_source_summary(self):
        self._setup_base()
        result = validate(self.base, fullstack=True)
        self.assertTrue(result["valid"])
        self.assertTrue(any("source-summary.json" in w.get("file", "") or "source-summary.json" in w.get("issue", "") for w in result["warnings"]))


class TestCLI(unittest.TestCase):
    """Test command-line invocation."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base = self.tmpdir
        self.pm = os.path.join(self.base, ".allforai", "product-map")
        os.makedirs(self.pm, exist_ok=True)
        self.script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cr_validate.py")

    def _write(self, name, data):
        with open(os.path.join(self.pm, name), "w") as f:
            json.dump(data, f)

    def test_cli_exit_0_on_valid(self):
        self._write("task-inventory.json", {"tasks": [_make_task("T001")]})
        self._write("role-profiles.json", {"roles": [_make_role("R001")]})
        proc = subprocess.run(
            [sys.executable, self.script, self.base],
            capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 0)
        out = json.loads(proc.stdout)
        self.assertTrue(out["valid"])

    def test_cli_exit_1_on_invalid(self):
        # No files at all
        proc = subprocess.run(
            [sys.executable, self.script, self.base],
            capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 1)
        out = json.loads(proc.stdout)
        self.assertFalse(out["valid"])

    def test_cli_fullstack_flag(self):
        self._write("task-inventory.json", {"tasks": [_make_task("T001")]})
        self._write("role-profiles.json", {"roles": [_make_role("R001")]})
        proc = subprocess.run(
            [sys.executable, self.script, self.base, "--fullstack"],
            capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 0)
        out = json.loads(proc.stdout)
        self.assertTrue(out["valid"])


if __name__ == "__main__":
    unittest.main()
