#!/usr/bin/env python3
"""Tests for _common.py shared utilities."""

import json
import os
import re
import sys
import tempfile
import unittest

from _common import (
    FLOW_NODES_FIELD,
    get_flow_nodes,
    ensure_list,
    now_iso,
    ensure_dir,
    write_json,
    load_json,
    require_json,
    write_markdown,
    load_fragments,
    assign_ids,
    dedup_by,
)


class TestFlowConstants(unittest.TestCase):
    def test_flow_nodes_field(self):
        self.assertEqual(FLOW_NODES_FIELD, "nodes")

    def test_get_flow_nodes(self):
        flow = {"nodes": [{"id": "n1"}, {"id": "n2"}]}
        self.assertEqual(len(get_flow_nodes(flow)), 2)

    def test_get_flow_nodes_missing(self):
        self.assertEqual(get_flow_nodes({}), [])


class TestEnsureList(unittest.TestCase):
    def test_list_passthrough(self):
        data = [1, 2, 3]
        self.assertEqual(ensure_list(data), [1, 2, 3])

    def test_dict_key_extraction(self):
        data = {"modules": [{"id": "M001"}]}
        result = ensure_list(data, "modules")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "M001")

    def test_fallback_keys(self):
        data = {"items": ["a", "b"]}
        result = ensure_list(data, "nonexistent")
        self.assertEqual(result, ["a", "b"])

    def test_fallback_data_key(self):
        data = {"data": [1, 2]}
        self.assertEqual(ensure_list(data, "nonexistent"), [1, 2])

    def test_fallback_results_key(self):
        data = {"results": [1]}
        self.assertEqual(ensure_list(data, "nonexistent"), [1])

    def test_fallback_tasks_key(self):
        data = {"tasks": [{"id": "T1"}]}
        self.assertEqual(len(ensure_list(data, "nonexistent")), 1)

    def test_fallback_gaps_key(self):
        data = {"gaps": [1, 2, 3]}
        self.assertEqual(ensure_list(data, "nonexistent"), [1, 2, 3])

    def test_fallback_decisions_key(self):
        data = {"decisions": [1]}
        self.assertEqual(ensure_list(data, "nonexistent"), [1])

    def test_empty_fallback(self):
        data = {"unrecognized_key": "value"}
        self.assertEqual(ensure_list(data, "nonexistent"), [])

    def test_non_dict_non_list(self):
        self.assertEqual(ensure_list("string"), [])
        self.assertEqual(ensure_list(42), [])
        self.assertEqual(ensure_list(None), [])


class TestNowIso(unittest.TestCase):
    def test_format(self):
        ts = now_iso()
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
        self.assertRegex(ts, pattern)


class TestJsonRoundtrip(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_write_and_load(self):
        path = os.path.join(self.tmpdir, "test.json")
        data = {"key": "value", "number": 42}
        write_json(path, data)
        loaded = load_json(path)
        self.assertEqual(loaded, data)

    def test_chinese_characters_preserved(self):
        path = os.path.join(self.tmpdir, "chinese.json")
        data = {"name": "用户管理", "desc": "中文描述测试"}
        write_json(path, data)
        # Verify raw file contains actual Chinese, not escaped
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        self.assertIn("用户管理", raw)
        self.assertNotIn("\\u", raw)
        # Verify roundtrip
        loaded = load_json(path)
        self.assertEqual(loaded["name"], "用户管理")

    def test_auto_mkdir(self):
        path = os.path.join(self.tmpdir, "sub", "deep", "test.json")
        write_json(path, {"ok": True})
        self.assertTrue(os.path.isfile(path))
        loaded = load_json(path)
        self.assertEqual(loaded, {"ok": True})

    def test_load_missing_file(self):
        result = load_json(os.path.join(self.tmpdir, "nonexistent.json"))
        self.assertIsNone(result)

    def test_load_invalid_json(self):
        path = os.path.join(self.tmpdir, "bad.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write("{invalid json}")
        result = load_json(path)
        self.assertIsNone(result)

    def test_require_json_exits_on_missing(self):
        with self.assertRaises(SystemExit) as cm:
            require_json(os.path.join(self.tmpdir, "missing.json"), "test-label")
        self.assertEqual(cm.exception.code, 1)

    def test_require_json_success(self):
        path = os.path.join(self.tmpdir, "valid.json")
        write_json(path, {"x": 1})
        data = require_json(path, "test-label")
        self.assertEqual(data, {"x": 1})


class TestWriteMarkdown(unittest.TestCase):
    def test_write_markdown(self):
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, "sub", "test.md")
        write_markdown(path, "# Hello\n\nWorld")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "# Hello\n\nWorld")


class TestLoadFragments(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_load_and_sort(self):
        # Create fragment files in non-alphabetical order
        write_json(os.path.join(self.tmpdir, "M002.json"), {"name": "second"})
        write_json(os.path.join(self.tmpdir, "M001.json"), {"name": "first"})
        write_json(os.path.join(self.tmpdir, "M003.json"), {"name": "third"})

        result = load_fragments(self.tmpdir)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0][0], "M001")
        self.assertEqual(result[0][1]["name"], "first")
        self.assertEqual(result[1][0], "M002")
        self.assertEqual(result[2][0], "M003")

    def test_prefix_filter(self):
        write_json(os.path.join(self.tmpdir, "M001.json"), {"name": "module"})
        write_json(os.path.join(self.tmpdir, "X001.json"), {"name": "other"})

        result = load_fragments(self.tmpdir, prefix="M")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "M001")

    def test_missing_dir(self):
        result = load_fragments(os.path.join(self.tmpdir, "nonexistent"))
        self.assertEqual(result, [])

    def test_skip_non_json(self):
        write_json(os.path.join(self.tmpdir, "M001.json"), {"ok": True})
        with open(os.path.join(self.tmpdir, "readme.txt"), "w", encoding="utf-8") as f:
            f.write("not json")
        result = load_fragments(self.tmpdir)
        self.assertEqual(len(result), 1)


class TestAssignIds(unittest.TestCase):
    def test_basic(self):
        items = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        result = assign_ids(items, prefix="T", start=1)
        self.assertEqual(result[0]["id"], "T001")
        self.assertEqual(result[1]["id"], "T002")
        self.assertEqual(result[2]["id"], "T003")

    def test_custom_prefix(self):
        items = [{"name": "x"}]
        result = assign_ids(items, prefix="M", start=5)
        self.assertEqual(result[0]["id"], "M005")

    def test_in_place(self):
        items = [{"name": "a"}]
        result = assign_ids(items)
        self.assertIs(result, items)
        self.assertEqual(items[0]["id"], "T001")


class TestDedupBy(unittest.TestCase):
    def test_single_key(self):
        items = [
            {"name": "a", "val": 1},
            {"name": "b", "val": 2},
            {"name": "a", "val": 3},
        ]
        result = dedup_by(items, "name")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["val"], 1)
        self.assertEqual(result[1]["val"], 2)

    def test_composite_key(self):
        items = [
            {"mod": "M001", "type": "api", "val": 1},
            {"mod": "M001", "type": "db", "val": 2},
            {"mod": "M001", "type": "api", "val": 3},
        ]
        result = dedup_by(items, "mod", "type")
        self.assertEqual(len(result), 2)

    def test_no_duplicates(self):
        items = [{"name": "a"}, {"name": "b"}]
        result = dedup_by(items, "name")
        self.assertEqual(len(result), 2)

    def test_empty_list(self):
        self.assertEqual(dedup_by([], "name"), [])

    def test_missing_key_treated_as_empty(self):
        items = [{"name": "a"}, {"other": "b"}, {"other": "c"}]
        result = dedup_by(items, "name")
        # Second and third items both have name="" → deduped
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
