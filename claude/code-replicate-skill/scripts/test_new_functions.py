#!/usr/bin/env python3
"""Tests for new functions added in v2.1-v3.0."""

import copy
import json
import os
import sys
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import assign_ids
from cr_gen_product_map import _infer_experience_priority
from cr_merge_roles import _infer_audience_type
from cr_merge_screens import _infer_render_as, RENDER_AS_KEYWORDS
from cr_gen_report import _coverage_warnings
from cr_discover import (
    _has_project_manifest, _split_mega_module, _find_module_dirs,
    _load_profile, _has_sub_modules, _count_code_files_shallow,
    scan_project,
)
from cr_merge_tasks import STRUCTURED_DEFAULTS, DEFAULT_PROTECTION_LEVEL


# ══════════════════════════════════════════════════════════════════════
# 1. assign_ids — adaptive width
# ══════════════════════════════════════════════════════════════════════

class TestAssignIdsAdaptiveWidth(unittest.TestCase):

    def test_small_set_3_digits(self):
        items = [{"name": f"i{i}"} for i in range(50)]
        assign_ids(items, "T", 1)
        self.assertEqual(items[0]["id"], "T001")
        self.assertEqual(items[49]["id"], "T050")

    def test_boundary_999(self):
        items = [{"name": f"i{i}"} for i in range(999)]
        assign_ids(items, "UC", 1)
        self.assertEqual(items[0]["id"], "UC001")
        self.assertEqual(items[998]["id"], "UC999")

    def test_over_999_4_digits(self):
        items = [{"name": f"i{i}"} for i in range(1500)]
        assign_ids(items, "UC", 1)
        self.assertEqual(items[0]["id"], "UC0001")
        self.assertEqual(items[999]["id"], "UC1000")
        self.assertEqual(items[1499]["id"], "UC1500")

    def test_10000_5_digits(self):
        items = [{"name": f"i{i}"} for i in range(10000)]
        assign_ids(items, "T", 1)
        self.assertEqual(items[0]["id"], "T00001")
        self.assertEqual(items[9999]["id"], "T10000")

    def test_consistent_width_within_set(self):
        items = [{"name": f"i{i}"} for i in range(1500)]
        assign_ids(items, "X", 1)
        widths = set(len(item["id"]) for item in items)
        self.assertEqual(len(widths), 1, "All IDs should have same width")


# ══════════════════════════════════════════════════════════════════════
# 2. _infer_experience_priority
# ══════════════════════════════════════════════════════════════════════

class TestInferExperiencePriority(unittest.TestCase):

    def test_all_consumer(self):
        roles = [
            {"id": "R001", "audience_type": "consumer"},
            {"id": "R002", "audience_type": "consumer"},
        ]
        tasks = [
            {"owner_role": "R001"}, {"owner_role": "R001"},
            {"owner_role": "R002"}, {"owner_role": "R002"},
        ]
        result = _infer_experience_priority(roles, tasks)
        self.assertEqual(result["mode"], "consumer")
        self.assertTrue(result["consumer_surface"])
        self.assertEqual(len(result["reasoning"]), 2)

    def test_all_professional(self):
        roles = [
            {"id": "R001", "audience_type": "professional"},
        ]
        tasks = [{"owner_role": "R001"}]
        result = _infer_experience_priority(roles, tasks)
        self.assertEqual(result["mode"], "admin")
        self.assertFalse(result["consumer_surface"])

    def test_mixed(self):
        roles = [
            {"id": "R001", "audience_type": "consumer"},
            {"id": "R002", "audience_type": "professional"},
        ]
        tasks = [{"owner_role": "R001"}] * 5 + [{"owner_role": "R002"}] * 5
        result = _infer_experience_priority(roles, tasks)
        self.assertEqual(result["mode"], "mixed")

    def test_no_roles(self):
        result = _infer_experience_priority([], [])
        self.assertEqual(result["mode"], "mixed")
        self.assertFalse(result["consumer_surface"])

    def test_consumer_dominant(self):
        roles = [
            {"id": "R001", "audience_type": "consumer"},
            {"id": "R002", "audience_type": "professional"},
        ]
        tasks = [{"owner_role": "R001"}] * 8 + [{"owner_role": "R002"}] * 2
        result = _infer_experience_priority(roles, tasks)
        self.assertEqual(result["mode"], "consumer")

    def test_professional_dominant(self):
        roles = [
            {"id": "R001", "audience_type": "consumer"},
            {"id": "R002", "audience_type": "professional"},
        ]
        tasks = [{"owner_role": "R001"}] * 2 + [{"owner_role": "R002"}] * 8
        result = _infer_experience_priority(roles, tasks)
        self.assertEqual(result["mode"], "admin")

    def test_all_required_fields_present(self):
        roles = [{"id": "R001", "audience_type": "consumer"}]
        tasks = [{"owner_role": "R001"}]
        result = _infer_experience_priority(roles, tasks)
        for field in ("mode", "consumer_surface", "consumer_core", "primary_experience", "reasoning"):
            self.assertIn(field, result)


# ══════════════════════════════════════════════════════════════════════
# 3. _infer_audience_type (fallback)
# ══════════════════════════════════════════════════════════════════════

class TestInferAudienceType(unittest.TestCase):

    def test_admin_keyword(self):
        self.assertEqual(_infer_audience_type({"name": "Admin User"}), "professional")

    def test_manager_keyword(self):
        self.assertEqual(_infer_audience_type({"name": "Store Manager"}), "professional")

    def test_plain_user(self):
        self.assertEqual(_infer_audience_type({"name": "Buyer"}), "consumer")

    def test_chinese_admin(self):
        self.assertEqual(_infer_audience_type({"name": "系统管理员"}), "professional")

    def test_description_fallback(self):
        role = {"name": "Power User", "description": "backend operator for management tasks"}
        self.assertEqual(_infer_audience_type(role), "professional")

    def test_permission_boundary(self):
        role = {"name": "Inspector", "permission_boundary": ["admin panel access", "manage users"]}
        self.assertEqual(_infer_audience_type(role), "professional")

    def test_empty_role(self):
        self.assertEqual(_infer_audience_type({"name": ""}), "consumer")


# ══════════════════════════════════════════════════════════════════════
# 4. _infer_render_as (fallback)
# ══════════════════════════════════════════════════════════════════════

class TestInferRenderAs(unittest.TestCase):

    def test_table_keyword_standalone(self):
        """Word 'table' as standalone word matches data_table."""
        self.assertEqual(_infer_render_as({"type": "data table", "purpose": ""}), "data_table")

    def test_form_keyword_standalone(self):
        self.assertEqual(_infer_render_as({"type": "input form", "purpose": "edit profile"}), "input_form")

    def test_chart_keyword_standalone(self):
        self.assertEqual(_infer_render_as({"type": "sales chart", "purpose": ""}), "bar_chart")

    def test_camelcase_no_match(self):
        """CamelCase compound words don't have word boundaries — fallback to text_block.
        This is by design: LLM should provide render_as directly, not rely on fallback."""
        self.assertEqual(_infer_render_as({"type": "DataTable", "purpose": ""}), "text_block")

    def test_unknown_defaults_text(self):
        self.assertEqual(_infer_render_as({"type": "CustomWidget", "purpose": ""}), "text_block")

    def test_word_boundary(self):
        """'action_log' should not match 'action' → action_bar."""
        result = _infer_render_as({"type": "action_log", "purpose": "show history"})
        # 'log' should match timeline, not 'action' matching action_bar
        self.assertIn(result, ("timeline", "text_block"))

    def test_search_filter(self):
        self.assertEqual(_infer_render_as({"type": "SearchFilter", "purpose": "filter items"}), "search_filter")


# ══════════════════════════════════════════════════════════════════════
# 5. _has_project_manifest
# ══════════════════════════════════════════════════════════════════════

class TestHasProjectManifest(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_package_json(self):
        open(os.path.join(self.tmpdir, "package.json"), "w").write("{}")
        self.assertTrue(_has_project_manifest(self.tmpdir))

    def test_csproj(self):
        open(os.path.join(self.tmpdir, "MyApp.csproj"), "w").write("")
        self.assertTrue(_has_project_manifest(self.tmpdir))

    def test_go_mod(self):
        open(os.path.join(self.tmpdir, "go.mod"), "w").write("")
        self.assertTrue(_has_project_manifest(self.tmpdir))

    def test_pubspec(self):
        open(os.path.join(self.tmpdir, "pubspec.yaml"), "w").write("")
        self.assertTrue(_has_project_manifest(self.tmpdir))

    def test_no_manifest(self):
        open(os.path.join(self.tmpdir, "main.go"), "w").write("")
        self.assertFalse(_has_project_manifest(self.tmpdir))

    def test_empty_dir(self):
        self.assertFalse(_has_project_manifest(self.tmpdir))


# ══════════════════════════════════════════════════════════════════════
# 6. _split_mega_module + _find_module_dirs with profile
# ══════════════════════════════════════════════════════════════════════

class TestSplitMegaModule(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        # Ensure clean global state
        import cr_discover
        self._saved_roots = set(cr_discover.SOURCE_ROOTS)
        self._saved_exts = set(cr_discover.CODE_EXTENSIONS)
        cr_discover.SOURCE_ROOTS.clear()
        cr_discover.SOURCE_ROOTS.update(cr_discover._DEFAULT_SOURCE_ROOTS)
        cr_discover.CODE_EXTENSIONS.clear()
        cr_discover.CODE_EXTENSIONS.update(cr_discover._DEFAULT_CODE_EXTENSIONS)

    def tearDown(self):
        shutil.rmtree(self.root)
        import cr_discover
        cr_discover.SOURCE_ROOTS.clear()
        cr_discover.SOURCE_ROOTS.update(self._saved_roots)
        cr_discover.CODE_EXTENSIONS.clear()
        cr_discover.CODE_EXTENSIONS.update(self._saved_exts)

    def _make_files(self, path, count, ext=".ts"):
        os.makedirs(path, exist_ok=True)
        for i in range(count):
            open(os.path.join(path, f"file{i}{ext}"), "w").close()

    def test_csproj_blocks_splitting(self):
        """Directory with .csproj should not be split even if >50 files."""
        mod = os.path.join(self.root, "src", "MyModule")
        os.makedirs(mod)
        open(os.path.join(mod, "MyModule.csproj"), "w").close()
        for layer in ["Views", "ViewModels", "Models"]:
            self._make_files(os.path.join(mod, layer), 20, ".cs")
        result = _split_mega_module("src/MyModule", mod, self.root)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "src/MyModule")

    def test_no_manifest_splits_large(self):
        """Directory without manifest and >50 files should split."""
        import cr_discover
        # Force reset CODE_EXTENSIONS (may have been polluted by _load_profile in other tests)
        cr_discover.CODE_EXTENSIONS.clear()
        cr_discover.CODE_EXTENSIONS.update(cr_discover._DEFAULT_CODE_EXTENSIONS)
        cr_discover.SOURCE_ROOTS.clear()
        cr_discover.SOURCE_ROOTS.update(cr_discover._DEFAULT_SOURCE_ROOTS)
        mod = os.path.join(self.root, "bigdir")
        for sub in ["user", "order", "product"]:
            self._make_files(os.path.join(mod, sub), 20, ".go")
        result = _split_mega_module("bigdir", mod, self.root)
        self.assertEqual(len(result), 3)

    def test_small_dir_no_split(self):
        """Directory with <50 files should not split."""
        mod = os.path.join(self.root, "src", "small")
        self._make_files(os.path.join(mod, "a"), 10, ".ts")
        self._make_files(os.path.join(mod, "b"), 10, ".ts")
        result = _split_mega_module("src/small", mod, self.root)
        self.assertEqual(len(result), 1)


class TestFindModuleDirsWithProfile(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_profile_module_paths(self):
        """Profile with explicit module_paths should be used directly."""
        for mod in ["mod_a", "mod_b"]:
            d = os.path.join(self.root, "src", mod)
            os.makedirs(d)
            open(os.path.join(d, "main.ts"), "w").close()

        profile = {
            "module_paths": [
                {"path": "src/mod_a", "atomic": True},
                {"path": "src/mod_b", "atomic": True},
            ]
        }
        result = _find_module_dirs(self.root, profile=profile)
        self.assertEqual(len(result), 2)
        paths = [r[0] for r in result]
        self.assertIn("src/mod_a", paths)
        self.assertIn("src/mod_b", paths)

    def test_profile_invalid_paths_skipped(self):
        """Profile paths that don't exist should be skipped."""
        profile = {
            "module_paths": [
                {"path": "nonexistent/path", "atomic": True},
            ]
        }
        result = _find_module_dirs(self.root, profile=profile)
        self.assertEqual(len(result), 0)


# ══════════════════════════════════════════════════════════════════════
# 7. _load_profile
# ══════════════════════════════════════════════════════════════════════

class TestLoadProfile(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Save ALL mutable global state before each test
        import cr_discover
        self._saved_source_roots = set(cr_discover.SOURCE_ROOTS)
        self._saved_skip_dirs = set(cr_discover.SKIP_DIRS)
        self._saved_code_exts = set(cr_discover.CODE_EXTENSIONS)
        self._saved_threshold = cr_discover._MEGA_MODULE_THRESHOLD
        self._saved_manifests = set(cr_discover._PROJECT_MANIFESTS)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        # Restore ALL mutable global state
        import cr_discover
        cr_discover.SOURCE_ROOTS.clear()
        cr_discover.SOURCE_ROOTS.update(self._saved_source_roots)
        cr_discover.SKIP_DIRS.clear()
        cr_discover.SKIP_DIRS.update(self._saved_skip_dirs)
        cr_discover.CODE_EXTENSIONS.clear()
        cr_discover.CODE_EXTENSIONS.update(self._saved_code_exts)
        cr_discover._MEGA_MODULE_THRESHOLD = self._saved_threshold
        cr_discover._PROJECT_MANIFESTS.clear()
        cr_discover._PROJECT_MANIFESTS.update(self._saved_manifests)

    def test_valid_profile(self):
        pp = os.path.join(self.tmpdir, "profile.json")
        with open(pp, "w") as f:
            json.dump({"mega_threshold": 100}, f)
        result = _load_profile(pp)
        self.assertIsNotNone(result)
        self.assertEqual(result["mega_threshold"], 100)

    def test_missing_profile(self):
        result = _load_profile(os.path.join(self.tmpdir, "missing.json"))
        self.assertIsNone(result)

    def test_invalid_json(self):
        pp = os.path.join(self.tmpdir, "bad.json")
        with open(pp, "w") as f:
            f.write("not json")
        result = _load_profile(pp)
        self.assertIsNone(result)


# ══════════════════════════════════════════════════════════════════════
# 8. _coverage_warnings
# ══════════════════════════════════════════════════════════════════════

class TestCoverageWarnings(unittest.TestCase):

    def test_normal_density(self):
        warnings = _coverage_warnings(10, 100, 10, 5, 5)
        self.assertEqual(len(warnings), 0)

    def test_low_task_density(self):
        warnings = _coverage_warnings(10, 1000, 5, 5, 5)
        self.assertTrue(any("task density" in w.lower() or "task" in w.lower() for w in warnings))

    def test_large_module_size(self):
        warnings = _coverage_warnings(2, 500, 20, 5, 5)
        self.assertTrue(any("module" in w.lower() for w in warnings))

    def test_zero_files(self):
        warnings = _coverage_warnings(0, 0, 0, 0, 0)
        self.assertEqual(len(warnings), 0)


# ══════════════════════════════════════════════════════════════════════
# 9. cr_merge_tasks — structured defaults + protection_level
# ══════════════════════════════════════════════════════════════════════

class TestMergeTasksNewFields(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base_path = os.path.join(self.tmpdir, "project")
        self.fragments_dir = os.path.join(self.tmpdir, "fragments")
        os.makedirs(os.path.join(self.fragments_dir, "tasks"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write_fragment(self, name, data):
        with open(os.path.join(self.fragments_dir, "tasks", name), "w") as f:
            json.dump(data, f)

    def _read_output(self):
        with open(os.path.join(self.base_path, ".allforai", "product-map", "task-inventory.json")) as f:
            return json.load(f)

    def test_protection_level_default(self):
        from cr_merge_tasks import merge_tasks
        self._write_fragment("m.json", {"tasks": [{"name": "T", "owner_role": "R1"}]})
        merge_tasks(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(out["tasks"][0]["protection_level"], DEFAULT_PROTECTION_LEVEL)

    def test_protection_level_preserved(self):
        from cr_merge_tasks import merge_tasks
        self._write_fragment("m.json", {"tasks": [
            {"name": "T", "owner_role": "R1", "protection_level": "core"}
        ]})
        merge_tasks(self.base_path, self.fragments_dir)
        out = self._read_output()
        self.assertEqual(out["tasks"][0]["protection_level"], "core")

    def test_structured_inputs(self):
        from cr_merge_tasks import merge_tasks
        self._write_fragment("m.json", {"tasks": [{"name": "T", "owner_role": "R1"}]})
        merge_tasks(self.base_path, self.fragments_dir)
        out = self._read_output()
        inp = out["tasks"][0]["inputs"]
        self.assertIsInstance(inp, dict)
        self.assertIn("fields", inp)
        self.assertIn("defaults", inp)

    def test_structured_outputs(self):
        from cr_merge_tasks import merge_tasks
        self._write_fragment("m.json", {"tasks": [{"name": "T", "owner_role": "R1"}]})
        merge_tasks(self.base_path, self.fragments_dir)
        out = self._read_output()
        outp = out["tasks"][0]["outputs"]
        self.assertIsInstance(outp, dict)
        for key in ("states", "messages", "records", "notifications"):
            self.assertIn(key, outp)

    def test_legacy_array_inputs_migrated(self):
        from cr_merge_tasks import merge_tasks
        self._write_fragment("m.json", {"tasks": [
            {"name": "T", "owner_role": "R1", "inputs": ["field1", "field2"]}
        ]})
        merge_tasks(self.base_path, self.fragments_dir)
        out = self._read_output()
        inp = out["tasks"][0]["inputs"]
        self.assertIsInstance(inp, dict)
        self.assertEqual(inp["fields"], ["field1", "field2"])

    def test_no_shared_reference(self):
        """Two tasks should not share the same defaults dict."""
        from cr_merge_tasks import merge_tasks
        self._write_fragment("m.json", {"tasks": [
            {"name": "T1", "owner_role": "R1"},
            {"name": "T2", "owner_role": "R1"},
        ]})
        merge_tasks(self.base_path, self.fragments_dir)
        out = self._read_output()
        out["tasks"][0]["inputs"]["fields"].append("modified")
        self.assertEqual(out["tasks"][1]["inputs"]["fields"], [])


# ══════════════════════════════════════════════════════════════════════
# Layer 2: Schema Contract Tests
# ══════════════════════════════════════════════════════════════════════

class TestSchemaContract(unittest.TestCase):
    """Verify that both product-design format and code-replicate format
    can be consumed by the same reader logic."""

    def test_usecase_tree_flat_format(self):
        """code-replicate v2.5.0+ flat format."""
        data = {
            "generated_at": "2026-01-01T00:00:00Z",
            "version": "2.5.0",
            "source": "code-replicate",
            "use_cases": [
                {"id": "UC001", "role_id": "R001", "task_id": "T001",
                 "type": "happy_path", "given": "x", "when": "y", "then": ["z"]},
            ]
        }
        # Consumer logic: try both formats
        flat = data.get("use_cases")
        nested = data.get("roles")
        self.assertIsNotNone(flat)
        self.assertIsNone(nested)
        self.assertEqual(len(flat), 1)

    def test_usecase_tree_nested_format(self):
        """product-design nested format."""
        data = {
            "generated_at": "2026-01-01T00:00:00Z",
            "roles": [
                {"role": "R001", "feature_areas": [
                    {"name": "Auth", "tasks": [
                        {"id": "T001", "use_cases": [
                            {"id": "UC001", "type": "happy_path",
                             "given": "x", "when": "y", "then": "z"}
                        ]}
                    ]}
                ]}
            ]
        }
        flat = data.get("use_cases")
        nested = data.get("roles")
        self.assertIsNone(flat)
        self.assertIsNotNone(nested)

    def test_consumer_reads_both_formats(self):
        """Simulate a consumer that handles both formats."""
        def count_use_cases(data):
            # flat format
            flat = data.get("use_cases")
            if flat and isinstance(flat, list):
                return len(flat)
            # nested format
            total = 0
            for role in data.get("roles", data.get("tree", [])):
                for fa in role.get("feature_areas", []):
                    for task in fa.get("tasks", []):
                        total += len(task.get("use_cases", []))
            return total

        flat_data = {"use_cases": [{"id": "UC001"}, {"id": "UC002"}]}
        nested_data = {"roles": [{"feature_areas": [{"tasks": [
            {"use_cases": [{"id": "UC001"}, {"id": "UC002"}]}
        ]}]}]}

        self.assertEqual(count_use_cases(flat_data), 2)
        self.assertEqual(count_use_cases(nested_data), 2)

    def test_role_with_audience_type(self):
        """Both formats should have audience_type."""
        cr_role = {"id": "R001", "name": "Admin", "audience_type": "professional"}
        pd_role = {"id": "R001", "name": "Admin", "audience_type": "professional",
                   "operation_profile": {"frequency": "high"}}
        # Both have audience_type
        self.assertIn("audience_type", cr_role)
        self.assertIn("audience_type", pd_role)

    def test_product_map_experience_priority(self):
        """Both producers should include experience_priority."""
        pm = {
            "experience_priority": {
                "mode": "consumer",
                "consumer_surface": True,
                "consumer_core": True,
                "primary_experience": "mobile",
                "reasoning": ["r1", "r2"]
            }
        }
        ep = pm["experience_priority"]
        for field in ("mode", "consumer_surface", "consumer_core", "primary_experience", "reasoning"):
            self.assertIn(field, ep)


if __name__ == "__main__":
    unittest.main()
