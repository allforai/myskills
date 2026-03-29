#!/usr/bin/env python3
"""Tests for validate_bootstrap.py — bootstrap product validation."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from validate_bootstrap import (
    validate_node_spec,
    validate_state_machine,
    validate_graph_connectivity,
    scan_dangerous_commands,
)


# ---------------------------------------------------------------------------
# validate_node_spec
# ---------------------------------------------------------------------------
class TestValidateNodeSpec(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._dir)

    def _write(self, name, content):
        path = os.path.join(self._dir, name)
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_valid_spec(self):
        path = self._write("node.md", (
            "---\n"
            "node: build\n"
            "entry_requires:\n"
            "  - file_exists: src/\n"
            "exit_requires:\n"
            "  - file_exists: dist/\n"
            "---\n"
            "# Build node\n"
        ))
        errors = validate_node_spec(path)
        self.assertEqual(errors, [])

    def test_missing_node_field(self):
        path = self._write("node.md", (
            "---\n"
            "entry_requires:\n"
            "  - file_exists: src/\n"
            "exit_requires:\n"
            "  - file_exists: dist/\n"
            "---\n"
        ))
        errors = validate_node_spec(path)
        self.assertTrue(any("node" in e for e in errors))

    def test_missing_exit_requires(self):
        path = self._write("node.md", (
            "---\n"
            "node: build\n"
            "entry_requires:\n"
            "  - file_exists: src/\n"
            "---\n"
        ))
        errors = validate_node_spec(path)
        self.assertTrue(any("exit_requires" in e for e in errors))

    def test_no_frontmatter(self):
        path = self._write("node.md", "# Just markdown\nNo frontmatter here.\n")
        errors = validate_node_spec(path)
        self.assertTrue(any("frontmatter" in e.lower() or "---" in e for e in errors))

    def test_malformed_yaml(self):
        path = self._write("node.md", (
            "---\n"
            "  bad indent\n"
            "    : missing key\n"
            "---\n"
        ))
        errors = validate_node_spec(path)
        # Should report missing required fields at minimum (malformed content)
        self.assertTrue(len(errors) > 0)

    def test_missing_closing_delimiter(self):
        path = self._write("node.md", (
            "---\n"
            "node: build\n"
            "entry_requires: []\n"
            "exit_requires: []\n"
        ))
        errors = validate_node_spec(path)
        self.assertTrue(any("closing" in e.lower() or "---" in e for e in errors))


# ---------------------------------------------------------------------------
# validate_state_machine
# ---------------------------------------------------------------------------
class TestValidateStateMachine(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._dir)

    def _write(self, data):
        path = os.path.join(self._dir, "state-machine.json")
        with open(path, "w") as f:
            json.dump(data, f)
        return path

    def test_valid(self):
        path = self._write({
            "schema_version": "1.0",
            "nodes": [{"id": "build"}, {"id": "test"}],
            "safety": {"max_retries": 3},
            "progress": {"total": 2},
        })
        errors = validate_state_machine(path)
        self.assertEqual(errors, [])

    def test_empty_nodes(self):
        path = self._write({
            "schema_version": "1.0",
            "nodes": [],
            "safety": {},
            "progress": {},
        })
        errors = validate_state_machine(path)
        self.assertTrue(any("empty" in e.lower() or "non-empty" in e.lower() for e in errors))

    def test_missing_schema_version(self):
        path = self._write({
            "nodes": [{"id": "build"}],
            "safety": {},
            "progress": {},
        })
        errors = validate_state_machine(path)
        self.assertTrue(any("schema_version" in e for e in errors))

    def test_missing_safety(self):
        path = self._write({
            "schema_version": "1.0",
            "nodes": [{"id": "build"}],
            "progress": {},
        })
        errors = validate_state_machine(path)
        self.assertTrue(any("safety" in e for e in errors))

    def test_node_missing_id(self):
        path = self._write({
            "schema_version": "1.0",
            "nodes": [{"id": "build"}, {"name": "test"}],
            "safety": {},
            "progress": {},
        })
        errors = validate_state_machine(path)
        self.assertTrue(any("id" in e for e in errors))


# ---------------------------------------------------------------------------
# validate_graph_connectivity
# ---------------------------------------------------------------------------
class TestValidateGraphConnectivity(unittest.TestCase):
    def test_connected_graph(self):
        nodes = [
            {"id": "root", "entry_requires": [], "exit_requires": [{"file_exists": "a.txt"}]},
            {"id": "mid", "entry_requires": [{"file_exists": "a.txt"}], "exit_requires": [{"file_exists": "b.txt"}]},
            {"id": "leaf", "entry_requires": [{"file_exists": "b.txt"}], "exit_requires": []},
        ]
        orphans = validate_graph_connectivity(nodes)
        self.assertEqual(orphans, [])

    def test_orphan_nodes(self):
        nodes = [
            {"id": "root", "entry_requires": [], "exit_requires": [{"file_exists": "a.txt"}]},
            {"id": "orphan", "entry_requires": [{"file_exists": "z.txt"}], "exit_requires": []},
        ]
        orphans = validate_graph_connectivity(nodes)
        self.assertIn("orphan", orphans)

    def test_no_roots(self):
        nodes = [
            {"id": "a", "entry_requires": [{"file_exists": "x.txt"}], "exit_requires": []},
            {"id": "b", "entry_requires": [{"file_exists": "y.txt"}], "exit_requires": []},
        ]
        orphans = validate_graph_connectivity(nodes)
        # All nodes are orphans if no root exists
        self.assertIn("a", orphans)
        self.assertIn("b", orphans)


# ---------------------------------------------------------------------------
# scan_dangerous_commands
# ---------------------------------------------------------------------------
class TestScanDangerousCommands(unittest.TestCase):
    def test_safe_command(self):
        requires = [{"command_succeeds": "npm test"}]
        warnings = scan_dangerous_commands(requires)
        self.assertEqual(warnings, [])

    def test_rm_rf(self):
        requires = [{"command_succeeds": "rm -rf /"}]
        warnings = scan_dangerous_commands(requires)
        self.assertTrue(len(warnings) > 0)
        self.assertTrue(any("rm" in w.lower() for w in warnings))

    def test_sudo(self):
        requires = [{"command_succeeds": "sudo apt install foo"}]
        warnings = scan_dangerous_commands(requires)
        self.assertTrue(len(warnings) > 0)
        self.assertTrue(any("sudo" in w.lower() for w in warnings))

    def test_chmod_777(self):
        requires = [{"command_succeeds": "chmod 777 /var/www"}]
        warnings = scan_dangerous_commands(requires)
        self.assertTrue(len(warnings) > 0)

    def test_dd_command(self):
        requires = [{"command_succeeds": "dd if=/dev/zero of=/dev/sda"}]
        warnings = scan_dangerous_commands(requires)
        self.assertTrue(len(warnings) > 0)

    def test_non_command_entries_ignored(self):
        requires = [{"file_exists": "/tmp/safe"}]
        warnings = scan_dangerous_commands(requires)
        self.assertEqual(warnings, [])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
class TestCLI(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self._nodes_dir = os.path.join(self._dir, "nodes")
        os.makedirs(self._nodes_dir)

    def tearDown(self):
        shutil.rmtree(self._dir)

    def _write_node(self, name, content):
        path = os.path.join(self._nodes_dir, name)
        with open(path, "w") as f:
            f.write(content)
        return path

    def _write_sm(self, data):
        path = os.path.join(self._dir, "state-machine.json")
        with open(path, "w") as f:
            json.dump(data, f)
        return path

    def test_cli_valid_bootstrap(self):
        self._write_node("build.md", (
            "---\n"
            "node: build\n"
            "entry_requires: []\n"
            "exit_requires:\n"
            "  - file_exists: dist/\n"
            "---\n"
            "# Build\n"
        ))
        self._write_sm({
            "schema_version": "1.0",
            "nodes": [{"id": "build", "entry_requires": [], "exit_requires": [{"file_exists": "dist/"}]}],
            "safety": {"max_retries": 3},
            "progress": {"total": 1},
        })
        result = subprocess.run(
            [sys.executable, "-m", "validate_bootstrap", self._dir],
            capture_output=True, text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertTrue(output["passed"])

    def test_cli_invalid_bootstrap(self):
        self._write_node("bad.md", "# No frontmatter\n")
        self._write_sm({
            "nodes": [{"id": "bad"}],
            "safety": {},
            "progress": {},
        })
        result = subprocess.run(
            [sys.executable, "-m", "validate_bootstrap", self._dir],
            capture_output=True, text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        self.assertEqual(result.returncode, 1)
        output = json.loads(result.stdout)
        self.assertFalse(output["passed"])
        self.assertTrue(len(output["errors"]) > 0)


if __name__ == "__main__":
    unittest.main()
