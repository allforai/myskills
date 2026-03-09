#!/usr/bin/env python3
"""Tests for FullContext class and load_full_context() in _common.py."""

import json
import os
import tempfile
import unittest

# Add scripts dir to path
import sys
sys.path.insert(0, os.path.dirname(__file__))

from _common import load_full_context, FullContext


class TestFullContextEmpty(unittest.TestCase):
    """test_empty_base: load from empty dir, verify all fields are None/empty."""

    def test_empty_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = load_full_context(tmp)
            self.assertIsInstance(ctx, FullContext)
            self.assertIsNone(ctx.tasks)
            self.assertIsNone(ctx.roles)
            self.assertIsNone(ctx.roles_full)
            self.assertEqual(ctx.flows, [])
            self.assertIsNone(ctx.entity_model)
            self.assertEqual(ctx.api_contracts, [])
            self.assertEqual(ctx.view_objects, [])
            self.assertIsNone(ctx.experience_map)
            self.assertEqual(ctx.screens, {})
            self.assertEqual(ctx.task_screen_map, {})
            self.assertIsNone(ctx.interaction_gate)
            self.assertIsNone(ctx.pattern_catalog)
            self.assertIsNone(ctx.behavioral_standards)
            self.assertIsNone(ctx.concept)
            self.assertEqual(ctx.xv_findings, [])
            self.assertEqual(ctx.constraints, [])


class TestLoadsArtifacts(unittest.TestCase):
    """test_loads_artifacts: create artifacts, verify all loaded and task_name normalized."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        pm = os.path.join(self.tmp, "product-map")
        os.makedirs(pm)

        # task-inventory with 'name' only (no 'task_name') to test normalization
        write(os.path.join(pm, "task-inventory.json"), {
            "tasks": [
                {"id": "T001", "name": "Login"},
                {"id": "T002", "task_name": "Register"},
            ]
        })
        write(os.path.join(pm, "role-profiles.json"), {
            "roles": [
                {"id": "R001", "name": "Admin", "description": "Administrator"},
                {"id": "R002", "name": "User", "description": "Regular user"},
            ]
        })
        write(os.path.join(pm, "entity-model.json"), {
            "entities": [{"id": "E001", "name": "User"}],
            "relationships": [{"from": "E001", "to": "E001", "type": "self"}],
        })
        write(os.path.join(pm, "api-contracts.json"), {
            "endpoints": [
                {"id": "API001", "path": "/login", "task_refs": ["T001"]},
            ]
        })
        write(os.path.join(pm, "view-objects.json"), {
            "view_objects": [
                {"id": "VO001", "name": "LoginForm", "task_refs": ["T001"]},
            ]
        })

    def test_loads_artifacts(self):
        ctx = load_full_context(self.tmp)

        # tasks loaded and normalized
        self.assertIsNotNone(ctx.tasks)
        self.assertIn("T001", ctx.tasks)
        self.assertIn("T002", ctx.tasks)
        # 'name' only → task_name should be added
        self.assertEqual(ctx.tasks["T001"]["task_name"], "Login")
        self.assertEqual(ctx.tasks["T001"]["name"], "Login")
        # 'task_name' only → name should be added
        self.assertEqual(ctx.tasks["T002"]["name"], "Register")
        self.assertEqual(ctx.tasks["T002"]["task_name"], "Register")

        # roles
        self.assertEqual(ctx.roles, {"R001": "Admin", "R002": "User"})
        self.assertIsNotNone(ctx.roles_full)
        self.assertEqual(len(ctx.roles_full), 2)

        # entity model
        self.assertIsNotNone(ctx.entity_model)
        entities, rels = ctx.entity_model
        self.assertEqual(len(entities), 1)
        self.assertEqual(len(rels), 1)

        # api contracts
        self.assertEqual(len(ctx.api_contracts), 1)
        self.assertEqual(ctx.api_contracts[0]["path"], "/login")

        # view objects
        self.assertEqual(len(ctx.view_objects), 1)
        self.assertEqual(ctx.view_objects[0]["name"], "LoginForm")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)


class TestConstraintsLoading(unittest.TestCase):
    """test_constraints_loading: verify get_constraints filters correctly."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        cdir = os.path.join(self.tmp, "constraints")
        os.makedirs(cdir)

        write(os.path.join(cdir, "wireframe.json"), {
            "constraint_id": "C001",
            "targets": ["ui-design", "experience-map"],
            "rule": "No modal dialogs on mobile",
        })
        write(os.path.join(cdir, "map.json"), {
            "constraint_id": "C002",
            "targets": ["product-map"],
            "rule": "Max 50 tasks per role",
        })

    def test_constraints_loading(self):
        ctx = load_full_context(self.tmp)
        self.assertEqual(len(ctx.constraints), 2)

        # filter for ui-design
        ui_constraints = ctx.get_constraints("ui-design")
        self.assertEqual(len(ui_constraints), 1)
        self.assertEqual(ui_constraints[0]["constraint_id"], "C001")

        # filter for product-map
        map_constraints = ctx.get_constraints("product-map")
        self.assertEqual(len(map_constraints), 1)
        self.assertEqual(map_constraints[0]["constraint_id"], "C002")

        # filter for nonexistent target
        self.assertEqual(ctx.get_constraints("nonexistent"), [])

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)


class TestXvFindingsCollection(unittest.TestCase):
    """test_xv_findings_collection: verify get_xv_findings filters by phase."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

        # ui-design XV review
        uid = os.path.join(self.tmp, "ui-design")
        os.makedirs(uid)
        write(os.path.join(uid, "ui-xv-review.json"), {
            "reviews": [
                {"task_type": "design_review", "finding": "Color contrast issue"},
                {"task_type": "visual_consistency", "finding": "Font mismatch"},
            ]
        })

        # design-audit XV review
        dad = os.path.join(self.tmp, "design-audit")
        os.makedirs(dad)
        write(os.path.join(dad, "audit-xv-review.json"), {
            "reviews": [
                {"task_type": "cross_layer_validation", "finding": "Missing entity ref"},
            ]
        })

    def test_xv_findings_collection(self):
        ctx = load_full_context(self.tmp)
        self.assertEqual(len(ctx.xv_findings), 3)

        # filter by phase
        ui_findings = ctx.get_xv_findings("ui-design")
        self.assertEqual(len(ui_findings), 2)

        audit_findings = ctx.get_xv_findings("design-audit")
        self.assertEqual(len(audit_findings), 1)
        self.assertEqual(audit_findings[0]["finding"], "Missing entity ref")

        # nonexistent phase
        self.assertEqual(ctx.get_xv_findings("nonexistent"), [])

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)


class TestVoForScreen(unittest.TestCase):
    """test_vo_for_screen: verify vo_for_screen matches via task intersection."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        pm = os.path.join(self.tmp, "product-map")
        os.makedirs(pm)
        em = os.path.join(self.tmp, "experience-map")
        os.makedirs(em)

        write(os.path.join(pm, "view-objects.json"), {
            "view_objects": [
                {"id": "VO001", "name": "LoginForm", "task_refs": ["T001", "T002"]},
                {"id": "VO002", "name": "Dashboard", "task_refs": ["T003"]},
                {"id": "VO003", "name": "Profile", "task_refs": ["T002", "T004"]},
            ]
        })

        # experience-map with screens referencing tasks
        write(os.path.join(em, "experience-map.json"), {
            "operation_lines": [
                {
                    "line_id": "L1",
                    "nodes": [
                        {
                            "id": "N1",
                            "screens": [
                                {"id": "S001", "name": "Login Screen", "tasks": ["T001"]},
                                {"id": "S002", "name": "Register Screen", "tasks": ["T002", "T004"]},
                            ]
                        }
                    ]
                }
            ]
        })

    def test_vo_for_screen(self):
        ctx = load_full_context(self.tmp)

        # S001 has tasks [T001] → VO001 has task_refs [T001, T002] → match
        vos = ctx.vo_for_screen("S001")
        vo_ids = [v["id"] for v in vos]
        self.assertIn("VO001", vo_ids)
        self.assertNotIn("VO002", vo_ids)  # T003 not in S001
        self.assertNotIn("VO003", vo_ids)  # T002,T004 not in S001.tasks=[T001]

        # S002 has tasks [T002, T004] → VO001 (T002 intersects), VO003 (T002,T004 intersect)
        vos2 = ctx.vo_for_screen("S002")
        vo_ids2 = [v["id"] for v in vos2]
        self.assertIn("VO001", vo_ids2)
        self.assertIn("VO003", vo_ids2)
        self.assertNotIn("VO002", vo_ids2)

        # Nonexistent screen
        self.assertEqual(ctx.vo_for_screen("S999"), [])

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)


class TestApiForScreen(unittest.TestCase):
    """test_api_for_screen: same pattern for API endpoints."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        pm = os.path.join(self.tmp, "product-map")
        os.makedirs(pm)
        em = os.path.join(self.tmp, "experience-map")
        os.makedirs(em)

        write(os.path.join(pm, "api-contracts.json"), {
            "endpoints": [
                {"id": "API001", "path": "/login", "task_refs": ["T001"]},
                {"id": "API002", "path": "/dashboard", "task_refs": ["T003"]},
                {"id": "API003", "path": "/profile", "task_refs": ["T002", "T004"]},
            ]
        })

        write(os.path.join(em, "experience-map.json"), {
            "operation_lines": [
                {
                    "line_id": "L1",
                    "nodes": [
                        {
                            "id": "N1",
                            "screens": [
                                {"id": "S001", "name": "Login Screen", "tasks": ["T001"]},
                                {"id": "S002", "name": "Profile Screen", "tasks": ["T002", "T004"]},
                            ]
                        }
                    ]
                }
            ]
        })

    def test_api_for_screen(self):
        ctx = load_full_context(self.tmp)

        # S001 tasks=[T001] → API001 matches
        apis = ctx.api_for_screen("S001")
        api_ids = [a["id"] for a in apis]
        self.assertIn("API001", api_ids)
        self.assertNotIn("API002", api_ids)
        self.assertNotIn("API003", api_ids)

        # S002 tasks=[T002,T004] → API003 matches
        apis2 = ctx.api_for_screen("S002")
        api_ids2 = [a["id"] for a in apis2]
        self.assertIn("API003", api_ids2)
        self.assertNotIn("API001", api_ids2)
        self.assertNotIn("API002", api_ids2)

        # Nonexistent screen
        self.assertEqual(ctx.api_for_screen("S999"), [])

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)


def write(path, data):
    """Helper to write JSON files in tests."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    unittest.main()
