#!/usr/bin/env python3
"""Tests for check_requires.py — four evaluation primitives."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

from check_requires import (
    file_exists,
    command_succeeds,
    json_field_gte,
    json_array_length_gte,
    evaluate_node,
)


# ---------------------------------------------------------------------------
# file_exists
# ---------------------------------------------------------------------------
class TestFileExists(unittest.TestCase):
    def test_existing_file(self):
        with tempfile.NamedTemporaryFile() as f:
            self.assertTrue(file_exists(f.name))

    def test_missing_file(self):
        self.assertFalse(file_exists("/tmp/__nonexistent_file_xyz__"))

    def test_directory(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(file_exists(d))

    def test_empty_path(self):
        self.assertFalse(file_exists(""))


# ---------------------------------------------------------------------------
# command_succeeds
# ---------------------------------------------------------------------------
class TestCommandSucceeds(unittest.TestCase):
    def test_true(self):
        self.assertTrue(command_succeeds("true"))

    def test_false(self):
        self.assertFalse(command_succeeds("false"))

    def test_pipe_match(self):
        self.assertTrue(command_succeeds("echo hello | grep hello"))

    def test_pipe_no_match(self):
        self.assertFalse(command_succeeds("echo hello | grep goodbye"))

    def test_timeout(self):
        # sleep 10 should be killed by 1-second timeout
        self.assertFalse(command_succeeds("sleep 10", timeout=1))


# ---------------------------------------------------------------------------
# json_field_gte
# ---------------------------------------------------------------------------
class TestJsonFieldGte(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self._file = os.path.join(self._dir, "data.json")

    def _write(self, data):
        with open(self._file, "w") as f:
            json.dump(data, f)

    def test_pass(self):
        self._write({"coverage": 80})
        self.assertTrue(json_field_gte(self._file, "$.coverage", 50))

    def test_equal(self):
        self._write({"coverage": 50})
        self.assertTrue(json_field_gte(self._file, "$.coverage", 50))

    def test_fail(self):
        self._write({"coverage": 30})
        self.assertFalse(json_field_gte(self._file, "$.coverage", 50))

    def test_nested_field(self):
        self._write({"stats": {"pass_rate": 95}})
        self.assertTrue(json_field_gte(self._file, "$.stats.pass_rate", 90))

    def test_missing_file(self):
        self.assertFalse(json_field_gte("/tmp/__no_file__", "$.x", 0))

    def test_missing_field(self):
        self._write({"a": 1})
        self.assertFalse(json_field_gte(self._file, "$.b", 0))

    def test_root_value(self):
        """$ alone means root — root is a number."""
        self._write(42)
        self.assertTrue(json_field_gte(self._file, "$", 40))


# ---------------------------------------------------------------------------
# json_array_length_gte
# ---------------------------------------------------------------------------
class TestJsonArrayLengthGte(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self._file = os.path.join(self._dir, "data.json")

    def _write(self, data):
        with open(self._file, "w") as f:
            json.dump(data, f)

    def test_root_array(self):
        self._write([1, 2, 3])
        self.assertTrue(json_array_length_gte(self._file, "$", 2))

    def test_root_array_exact(self):
        self._write([1, 2])
        self.assertTrue(json_array_length_gte(self._file, "$", 2))

    def test_nested_array(self):
        self._write({"items": [1, 2, 3, 4]})
        self.assertTrue(json_array_length_gte(self._file, "$.items", 3))

    def test_too_short(self):
        self._write({"items": [1]})
        self.assertFalse(json_array_length_gte(self._file, "$.items", 5))

    def test_empty_array(self):
        self._write([])
        self.assertFalse(json_array_length_gte(self._file, "$", 1))

    def test_empty_array_zero_min(self):
        self._write([])
        self.assertTrue(json_array_length_gte(self._file, "$", 0))

    def test_missing_file(self):
        self.assertFalse(json_array_length_gte("/tmp/__no__", "$.x", 0))

    def test_not_an_array(self):
        self._write({"items": "not_array"})
        self.assertFalse(json_array_length_gte(self._file, "$.items", 1))


# ---------------------------------------------------------------------------
# evaluate_node
# ---------------------------------------------------------------------------
class TestEvaluateNode(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self._sm_path = os.path.join(self._dir, "state-machine.json")
        self._data_file = os.path.join(self._dir, "results.json")
        with open(self._data_file, "w") as f:
            json.dump({"score": 80, "items": [1, 2, 3]}, f)

    def _write_sm(self, nodes):
        with open(self._sm_path, "w") as f:
            json.dump({"nodes": nodes}, f)

    def test_all_pass(self):
        self._write_sm([{
            "id": "build",
            "exit_requires": [
                {"file_exists": self._data_file},
                {"json_field_gte": [self._data_file, "$.score", 50]},
            ],
        }])
        results = evaluate_node(self._sm_path, "build", "exit")
        self.assertTrue(all(r["passed"] for r in results))

    def test_partial_fail(self):
        self._write_sm([{
            "id": "build",
            "exit_requires": [
                {"file_exists": self._data_file},
                {"json_field_gte": [self._data_file, "$.score", 99]},
            ],
        }])
        results = evaluate_node(self._sm_path, "build", "exit")
        self.assertTrue(results[0]["passed"])
        self.assertFalse(results[1]["passed"])

    def test_entry_requires(self):
        self._write_sm([{
            "id": "verify",
            "entry_requires": [
                {"file_exists": self._data_file},
            ],
        }])
        results = evaluate_node(self._sm_path, "verify", "entry")
        self.assertTrue(results[0]["passed"])

    def test_unknown_node(self):
        self._write_sm([{"id": "build"}])
        with self.assertRaises(ValueError):
            evaluate_node(self._sm_path, "nonexistent", "exit")

    def test_no_requires(self):
        """Node exists but has no requires of the requested type."""
        self._write_sm([{"id": "build"}])
        results = evaluate_node(self._sm_path, "build", "exit")
        self.assertEqual(results, [])

    def test_command_succeeds_in_evaluate(self):
        self._write_sm([{
            "id": "lint",
            "entry_requires": [
                {"command_succeeds": "true"},
            ],
        }])
        results = evaluate_node(self._sm_path, "lint", "entry")
        self.assertTrue(results[0]["passed"])

    def test_array_length_in_evaluate(self):
        self._write_sm([{
            "id": "check",
            "exit_requires": [
                {"json_array_length_gte": [self._data_file, "$.items", 2]},
            ],
        }])
        results = evaluate_node(self._sm_path, "check", "exit")
        self.assertTrue(results[0]["passed"])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
class TestCLI(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self._sm_path = os.path.join(self._dir, "state-machine.json")
        data_file = os.path.join(self._dir, "r.json")
        with open(data_file, "w") as f:
            json.dump({"score": 80}, f)
        sm = {"nodes": [{
            "id": "build",
            "exit_requires": [
                {"file_exists": data_file},
                {"json_field_gte": [data_file, "$.score", 50]},
            ],
        }]}
        with open(self._sm_path, "w") as f:
            json.dump(sm, f)

    def test_cli_exit_pass(self):
        result = subprocess.run(
            [sys.executable, "-m", "check_requires",
             self._sm_path, "build", "--type", "exit"],
            capture_output=True, text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        self.assertEqual(result.returncode, 0)

    def test_cli_exit_fail(self):
        # Overwrite SM with impossible requirement
        sm = {"nodes": [{
            "id": "build",
            "exit_requires": [{"file_exists": "/tmp/__nope__"}],
        }]}
        with open(self._sm_path, "w") as f:
            json.dump(sm, f)
        result = subprocess.run(
            [sys.executable, "-m", "check_requires",
             self._sm_path, "build", "--type", "exit"],
            capture_output=True, text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        self.assertEqual(result.returncode, 1)

    def test_cli_default_type_is_entry(self):
        sm = {"nodes": [{
            "id": "build",
            "entry_requires": [{"command_succeeds": "true"}],
        }]}
        with open(self._sm_path, "w") as f:
            json.dump(sm, f)
        result = subprocess.run(
            [sys.executable, "-m", "check_requires",
             self._sm_path, "build"],
            capture_output=True, text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
