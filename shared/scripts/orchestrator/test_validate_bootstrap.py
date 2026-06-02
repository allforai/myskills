#!/usr/bin/env python3
"""Tests for validate_bootstrap.py — current contract only.

The module validates the NEW bootstrap products:
  - workflow.json: nodes[] non-empty, each node has id/goal/exit_artifacts (a list),
    no bare suspicious exit-artifact filenames, well-formed transition_log[].
  - node-specs/*.md: YAML frontmatter present with a 'node' field.

(The old state-machine schema, fan-out, graph-connectivity and dangerous-command
checks were removed in the validate_bootstrap simplification refactor; their tests
were removed with them.)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from validate_bootstrap import validate_workflow, validate_node_spec


def _write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f)


# ---------------------------------------------------------------------------
# validate_workflow
# ---------------------------------------------------------------------------
class TestValidateWorkflow(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self.path = os.path.join(self._dir, "workflow.json")

    def tearDown(self):
        shutil.rmtree(self._dir)

    def _node(self, **over):
        n = {"id": "n1", "goal": "do x", "exit_artifacts": ["sub/out.json"]}
        n.update(over)
        return n

    def test_valid(self):
        _write_json(self.path, {"nodes": [self._node()], "transition_log": []})
        self.assertEqual(validate_workflow(self.path), [])

    def test_cannot_parse(self):
        with open(self.path, "w") as f:
            f.write("{not json")
        self.assertTrue(any("cannot parse" in e for e in validate_workflow(self.path)))

    def test_nodes_missing(self):
        _write_json(self.path, {})
        self.assertTrue(any("nodes" in e for e in validate_workflow(self.path)))

    def test_empty_nodes(self):
        _write_json(self.path, {"nodes": []})
        self.assertTrue(any("empty" in e for e in validate_workflow(self.path)))

    def test_node_missing_id(self):
        n = self._node()
        del n["id"]
        _write_json(self.path, {"nodes": [n]})
        self.assertTrue(any("missing 'id'" in e for e in validate_workflow(self.path)))

    def test_node_missing_goal(self):
        n = self._node()
        del n["goal"]
        _write_json(self.path, {"nodes": [n]})
        self.assertTrue(any("missing 'goal'" in e for e in validate_workflow(self.path)))

    def test_node_missing_exit_artifacts(self):
        n = self._node()
        del n["exit_artifacts"]
        _write_json(self.path, {"nodes": [n]})
        self.assertTrue(any("missing 'exit_artifacts'" in e for e in validate_workflow(self.path)))

    def test_exit_artifacts_not_list(self):
        _write_json(self.path, {"nodes": [self._node(exit_artifacts="nope")]})
        self.assertTrue(any("must be a list" in e for e in validate_workflow(self.path)))

    def test_bare_suspicious_filename(self):
        _write_json(self.path, {"nodes": [self._node(exit_artifacts=["package.json"])]})
        self.assertTrue(any("bare filename" in e for e in validate_workflow(self.path)))

    def test_transition_log_must_be_list(self):
        _write_json(self.path, {"nodes": [self._node()], "transition_log": {}})
        self.assertTrue(any("transition_log must be a list" in e for e in validate_workflow(self.path)))

    def test_transition_log_entry_missing_fields(self):
        _write_json(self.path, {"nodes": [self._node()], "transition_log": [{"node": "n1"}]})
        self.assertTrue(any("missing 'status'" in e for e in validate_workflow(self.path)))

    def test_transition_log_bad_status(self):
        entry = {"node": "n1", "status": "weird", "started_at": "t",
                 "completed_at": "t", "artifacts_created": []}
        _write_json(self.path, {"nodes": [self._node()], "transition_log": [entry]})
        self.assertTrue(any("status must be one of" in e for e in validate_workflow(self.path)))

    def test_transition_log_failed_needs_error(self):
        entry = {"node": "n1", "status": "failed", "started_at": "t",
                 "completed_at": "t", "artifacts_created": []}
        _write_json(self.path, {"nodes": [self._node()], "transition_log": [entry]})
        self.assertTrue(any("failed entry missing 'error'" in e for e in validate_workflow(self.path)))


# ---------------------------------------------------------------------------
# validate_node_spec
# ---------------------------------------------------------------------------
class TestValidateNodeSpec(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self.path = os.path.join(self._dir, "spec.md")

    def tearDown(self):
        shutil.rmtree(self._dir)

    def _write(self, text):
        with open(self.path, "w") as f:
            f.write(text)

    def test_valid_spec(self):
        self._write("---\nnode: n1\n---\n\n# Task\nDo it.")
        self.assertEqual(validate_node_spec(self.path), [])

    def test_missing_node_field(self):
        self._write("---\ntitle: x\n---\n\nbody")
        self.assertTrue(any("node" in e for e in validate_node_spec(self.path)))

    def test_no_frontmatter(self):
        self._write("# Task\nno frontmatter here")
        self.assertTrue(any("frontmatter" in e for e in validate_node_spec(self.path)))

    def test_no_closing_delimiter(self):
        self._write("---\nnode: n1\nnever closed")
        self.assertTrue(any("closing" in e for e in validate_node_spec(self.path)))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
class TestCLI(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.mkdtemp()
        self._specs = os.path.join(self._dir, "node-specs")
        os.makedirs(self._specs)

    def tearDown(self):
        shutil.rmtree(self._dir)

    def _run(self):
        return subprocess.run(
            [sys.executable, "validate_bootstrap.py", self._dir],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True, text=True)

    def test_cli_valid(self):
        _write_json(os.path.join(self._dir, "workflow.json"),
                    {"nodes": [{"id": "n1", "goal": "g", "exit_artifacts": ["sub/o.json"]}],
                     "transition_log": []})
        with open(os.path.join(self._specs, "n1.md"), "w") as f:
            f.write("---\nnode: n1\n---\n\n# Task")
        r = self._run()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_cli_invalid(self):
        _write_json(os.path.join(self._dir, "workflow.json"), {"nodes": []})  # empty -> error
        r = self._run()
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
