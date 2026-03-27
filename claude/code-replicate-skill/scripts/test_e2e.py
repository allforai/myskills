#!/usr/bin/env python3
"""Layer 4: End-to-end integration tests.

Tests the complete pipeline: cr_discover → merge scripts → gen scripts → validate.
Uses test_integration/ fixtures as LLM-generated fragments (simulating Phase 3 output).
Uses a synthetic source project for cr_discover (simulating Phase 2a).
"""

import json
import os
import sys
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_integration")


def _ensure_default_globals():
    """Reset cr_discover globals to defaults (may be polluted by other tests)."""
    import cr_discover
    cr_discover.SOURCE_ROOTS.clear()
    cr_discover.SOURCE_ROOTS.update(cr_discover._DEFAULT_SOURCE_ROOTS)
    cr_discover.CODE_EXTENSIONS.clear()
    cr_discover.CODE_EXTENSIONS.update(cr_discover._DEFAULT_CODE_EXTENSIONS)
    cr_discover.SKIP_DIRS.clear()
    cr_discover.SKIP_DIRS.update(cr_discover._DEFAULT_SKIP_DIRS)
    cr_discover._MEGA_MODULE_THRESHOLD = 50


class TestE2EDiscoverToValidate(unittest.TestCase):
    """Full pipeline: discover source → merge fragments → gen reports → validate."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base_path = os.path.join(self.tmpdir, "project")
        _ensure_default_globals()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _create_source_project(self):
        """Create a small synthetic Go project for cr_discover."""
        src = os.path.join(self.tmpdir, "source")
        os.makedirs(src)
        open(os.path.join(src, "go.mod"), "w").write("module github.com/test/mock-api")

        # internal/auth/
        auth = os.path.join(src, "internal", "auth")
        os.makedirs(auth)
        open(os.path.join(auth, "handler.go"), "w").write("package auth\nfunc Login() {}")
        open(os.path.join(auth, "service.go"), "w").write("package auth\nfunc Validate() {}")
        open(os.path.join(auth, "middleware.go"), "w").write("package auth\nfunc JWTMiddleware() {}")

        # internal/user/
        user = os.path.join(src, "internal", "user")
        os.makedirs(user)
        open(os.path.join(user, "handler.go"), "w").write("package user\nfunc GetUser() {}")
        open(os.path.join(user, "service.go"), "w").write("package user\nfunc FindByID() {}")
        open(os.path.join(user, "repo.go"), "w").write("package user\nfunc Save() {}")

        # cmd/api/
        cmd = os.path.join(src, "cmd", "api")
        os.makedirs(cmd)
        open(os.path.join(cmd, "main.go"), "w").write("package main\nfunc main() {}")

        return src

    def _copy_fragments(self):
        """Copy test_integration fragments to tmpdir."""
        frag_src = os.path.join(FIXTURES_DIR, "fragments")
        frag_dst = os.path.join(self.tmpdir, "fragments")
        shutil.copytree(frag_src, frag_dst)
        return frag_dst

    def _setup_allforai(self):
        """Copy source-summary.json to .allforai."""
        allforai = os.path.join(self.base_path, ".allforai", "code-replicate")
        os.makedirs(allforai, exist_ok=True)
        shutil.copy(
            os.path.join(FIXTURES_DIR, ".allforai", "code-replicate", "source-summary.json"),
            os.path.join(allforai, "source-summary.json")
        )

    # ── Phase 2a: cr_discover ───────────────────────────────────────

    def test_discover_finds_modules(self):
        """cr_discover should find modules in a real project structure."""
        from cr_discover import scan_project
        src = self._create_source_project()
        result = scan_project(src)

        self.assertIn("go", result["project"]["detected_stacks"])
        self.assertGreater(len(result["modules"]), 0)

        # Should find auth and user modules
        paths = [m["path"] for m in result["modules"]]
        self.assertTrue(
            any("auth" in p for p in paths),
            f"Should find auth module, got {paths}"
        )
        self.assertTrue(
            any("user" in p for p in paths),
            f"Should find user module, got {paths}"
        )

    def test_discover_counts_files(self):
        from cr_discover import scan_project
        src = self._create_source_project()
        result = scan_project(src)

        self.assertGreater(result["project"]["total_files"], 0)
        for mod in result["modules"]:
            self.assertGreater(mod["file_count"], 0)

    def test_discover_assigns_ids(self):
        from cr_discover import scan_project
        src = self._create_source_project()
        result = scan_project(src)

        ids = [m["id"] for m in result["modules"]]
        self.assertTrue(all(id.startswith("M") for id in ids))
        self.assertEqual(len(ids), len(set(ids)), "IDs should be unique")

    # ── Phase 3: merge scripts ──────────────────────────────────────

    def test_merge_roles_from_fixtures(self):
        from cr_merge_roles import merge_roles
        frag = self._copy_fragments()
        merge_roles(self.base_path, frag)

        path = os.path.join(self.base_path, ".allforai", "product-map", "role-profiles.json")
        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            data = json.load(f)
        self.assertGreater(len(data["roles"]), 0)
        # All roles should have audience_type
        for role in data["roles"]:
            self.assertIn("audience_type", role)

    def test_merge_tasks_from_fixtures(self):
        from cr_merge_tasks import merge_tasks
        frag = self._copy_fragments()
        merge_tasks(self.base_path, frag)

        path = os.path.join(self.base_path, ".allforai", "product-map", "task-inventory.json")
        with open(path) as f:
            data = json.load(f)
        self.assertGreater(len(data["tasks"]), 0)
        for task in data["tasks"]:
            self.assertIn("protection_level", task)
            self.assertIsInstance(task["inputs"], dict)
            self.assertIsInstance(task["outputs"], dict)

    def test_merge_flows_from_fixtures(self):
        from cr_merge_tasks import merge_tasks
        from cr_merge_flows import merge_flows
        frag = self._copy_fragments()
        # tasks first (flows cross-reference)
        merge_tasks(self.base_path, frag)
        merge_flows(self.base_path, frag)

        path = os.path.join(self.base_path, ".allforai", "product-map", "business-flows.json")
        with open(path) as f:
            data = json.load(f)
        self.assertGreater(len(data["flows"]), 0)
        self.assertIn("systems", data)
        self.assertIn("summary", data)
        for flow in data["flows"]:
            self.assertIn("description", flow)
            self.assertIn("confirmed", flow)
            self.assertIn("gap_count", flow)

    def test_merge_usecases_from_fixtures(self):
        from cr_merge_usecases import merge_usecases
        frag = self._copy_fragments()
        merge_usecases(self.base_path, frag)

        path = os.path.join(self.base_path, ".allforai", "use-case", "use-case-tree.json")
        with open(path) as f:
            data = json.load(f)
        # v2.5.0+ flat format
        self.assertIn("use_cases", data)
        self.assertGreater(len(data["use_cases"]), 0)
        for uc in data["use_cases"]:
            self.assertIn("title", uc)
            self.assertIn("role_id", uc)
            self.assertIn("task_id", uc)
            self.assertIsInstance(uc["then"], list)

    # ── Phase 3.6: gen scripts ──────────────────────────────────────

    def test_gen_product_map(self):
        from cr_merge_roles import merge_roles
        from cr_merge_tasks import merge_tasks
        from cr_merge_flows import merge_flows
        from cr_gen_product_map import generate_product_map
        frag = self._copy_fragments()

        merge_roles(self.base_path, frag)
        merge_tasks(self.base_path, frag)
        merge_flows(self.base_path, frag)
        generate_product_map(self.base_path)

        path = os.path.join(self.base_path, ".allforai", "product-map", "product-map.json")
        with open(path) as f:
            data = json.load(f)

        # Must have experience_priority
        self.assertIn("experience_priority", data)
        ep = data["experience_priority"]
        for field in ("mode", "consumer_surface", "consumer_core", "primary_experience", "reasoning"):
            self.assertIn(field, ep)
        self.assertIsInstance(ep["reasoning"], list)
        self.assertGreaterEqual(len(ep["reasoning"]), 2)

        # Must have summary
        self.assertIn("summary", data)
        self.assertGreater(data["summary"]["task_count"], 0)
        self.assertGreater(data["summary"]["role_count"], 0)

    def test_gen_usecase_report(self):
        from cr_merge_usecases import merge_usecases
        from cr_gen_usecase_report import generate_usecase_report
        frag = self._copy_fragments()
        merge_usecases(self.base_path, frag)
        generate_usecase_report(self.base_path)

        path = os.path.join(self.base_path, ".allforai", "use-case", "use-case-report.md")
        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            content = f.read()
        self.assertIn("Use Case Report", content)
        self.assertIn("Login", content)

    # ── Phase 4a: validate ──────────────────────────────────────────

    def test_validate_passes(self):
        """Full pipeline should produce valid artifacts."""
        from cr_merge_roles import merge_roles
        from cr_merge_tasks import merge_tasks
        from cr_merge_flows import merge_flows
        from cr_merge_usecases import merge_usecases
        from cr_gen_product_map import generate_product_map
        from cr_gen_indexes import generate_indexes
        from cr_validate import validate

        frag = self._copy_fragments()
        merge_roles(self.base_path, frag)
        merge_tasks(self.base_path, frag)
        merge_flows(self.base_path, frag)
        merge_usecases(self.base_path, frag)
        generate_indexes(self.base_path)
        generate_product_map(self.base_path)

        result = validate(self.base_path)
        self.assertTrue(result["valid"], f"Validation failed: {result['errors']}")
        self.assertEqual(result["errors"], [])
        self.assertGreater(result["stats"]["tasks"], 0)
        self.assertGreater(result["stats"]["roles"], 0)

    def test_validate_task_ref_coverage(self):
        """Flows should reference tasks, giving >0 coverage."""
        from cr_merge_roles import merge_roles
        from cr_merge_tasks import merge_tasks
        from cr_merge_flows import merge_flows
        from cr_gen_product_map import generate_product_map
        from cr_validate import validate

        frag = self._copy_fragments()
        merge_roles(self.base_path, frag)
        merge_tasks(self.base_path, frag)
        merge_flows(self.base_path, frag)
        generate_product_map(self.base_path)

        result = validate(self.base_path)
        self.assertGreater(result["stats"]["task_ref_coverage"], 0)

    # ── Ground Truth Assertions ─────────────────────────────────────

    def test_ground_truth_role_count(self):
        """Fixture has 2 modules with roles: Admin, User (M001) + Editor (M002).
        After dedup, should have 3 unique roles."""
        from cr_merge_roles import merge_roles
        frag = self._copy_fragments()
        merge_roles(self.base_path, frag)

        path = os.path.join(self.base_path, ".allforai", "product-map", "role-profiles.json")
        with open(path) as f:
            data = json.load(f)

        names = {r["name"] for r in data["roles"]}
        self.assertIn("Admin", names)
        self.assertIn("User", names)

    def test_ground_truth_task_count(self):
        """M001 has 2 tasks + M002 has tasks. Should have >=2 after merge."""
        from cr_merge_tasks import merge_tasks
        frag = self._copy_fragments()
        merge_tasks(self.base_path, frag)

        path = os.path.join(self.base_path, ".allforai", "product-map", "task-inventory.json")
        with open(path) as f:
            data = json.load(f)
        self.assertGreaterEqual(len(data["tasks"]), 2)

    def test_ground_truth_usecase_types(self):
        """Fixture has happy_path, exception, and boundary use cases."""
        from cr_merge_usecases import merge_usecases
        frag = self._copy_fragments()
        merge_usecases(self.base_path, frag)

        path = os.path.join(self.base_path, ".allforai", "use-case", "use-case-tree.json")
        with open(path) as f:
            data = json.load(f)

        types = {uc["type"] for uc in data["use_cases"]}
        self.assertIn("happy_path", types)
        self.assertIn("exception", types)
        self.assertIn("boundary", types)


if __name__ == "__main__":
    unittest.main()
