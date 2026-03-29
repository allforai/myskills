# Meta-Skill Plan 1: Core Infrastructure + Plugin Scaffold

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundational Python scripts (check_requires.py, validate_bootstrap.py) and scaffold the meta-skill plugin directory structure with empty knowledge/ placeholders.

**Architecture:** Two Python scripts handle mechanical evaluation (entry/exit_requires checking and bootstrap validation). The plugin scaffold follows the existing claude/*-skill/ convention with plugin.json, SKILL.md, commands/, skills/, and knowledge/ directories.

**Tech Stack:** Python 3 (unittest), Claude Code plugin format (.claude-plugin/), Markdown skill files

**Spec:** `docs/superpowers/specs/2026-03-29-meta-skill-architecture-design.md` Sections 7, 8, 10

---

### Task 1: check_requires.py — Four Evaluation Primitives

**Files:**
- Create: `shared/scripts/orchestrator/check_requires.py`
- Test: `shared/scripts/orchestrator/test_check_requires.py`

This script evaluates node-spec entry/exit_requires declarations mechanically (no LLM). Four primitives:
- `file_exists(path)` — `os.path.exists`
- `command_succeeds(cmd)` — `subprocess` exit code == 0
- `json_field_gte(file, json_path, value)` — read JSON, compare number
- `json_array_length_gte(file, json_path, min_length)` — read JSON, check array length

- [ ] **Step 1: Create directory and test file with file_exists tests**

```python
#!/usr/bin/env python3
"""Tests for check_requires.py — entry/exit_requires evaluation primitives."""

import json
import os
import tempfile
import unittest

# Import will fail until we create the module
from check_requires import evaluate_require


class TestFileExists(unittest.TestCase):
    def test_existing_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"hello")
            path = f.name
        try:
            result = evaluate_require({"file_exists": path})
            self.assertTrue(result["passed"])
            self.assertEqual(result["primitive"], "file_exists")
        finally:
            os.unlink(path)

    def test_missing_file(self):
        result = evaluate_require({"file_exists": "/nonexistent/path/xyz.json"})
        self.assertFalse(result["passed"])

    def test_directory_counts_as_exists(self):
        with tempfile.TemporaryDirectory() as d:
            result = evaluate_require({"file_exists": d})
            self.assertTrue(result["passed"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/aa/Documents/myskills/shared/scripts/orchestrator && python -m pytest test_check_requires.py::TestFileExists -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'check_requires'`

- [ ] **Step 3: Implement file_exists primitive**

```python
#!/usr/bin/env python3
"""Evaluate node-spec entry/exit_requires declarations mechanically.

Four primitives:
  file_exists(path)                         — os.path.exists
  command_succeeds(cmd)                     — subprocess exit code == 0
  json_field_gte(file, json_path, value)    — read JSON, compare number
  json_array_length_gte(file, json_path, n) — read JSON, check array length

Usage:
  python check_requires.py <state-machine.json> <node-id> [--type entry|exit]
  Returns JSON: { "node": "...", "type": "entry|exit", "results": [...], "all_passed": bool }
"""

import json
import os
import subprocess
import sys


def evaluate_require(req: dict) -> dict:
    """Evaluate a single require declaration. Returns { primitive, passed, detail }."""
    if "file_exists" in req:
        path = req["file_exists"]
        passed = os.path.exists(path)
        return {"primitive": "file_exists", "passed": passed, "detail": path}

    return {"primitive": "unknown", "passed": False, "detail": f"Unknown require format: {req}"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/aa/Documents/myskills/shared/scripts/orchestrator && python -m pytest test_check_requires.py::TestFileExists -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Add command_succeeds tests**

Append to `test_check_requires.py`:

```python
class TestCommandSucceeds(unittest.TestCase):
    def test_true_command(self):
        result = evaluate_require({"command_succeeds": "true"})
        self.assertTrue(result["passed"])

    def test_false_command(self):
        result = evaluate_require({"command_succeeds": "false"})
        self.assertFalse(result["passed"])

    def test_echo_pipe_grep_match(self):
        result = evaluate_require({"command_succeeds": "echo 'BUILD SUCCEEDED' | grep 'SUCCEEDED'"})
        self.assertTrue(result["passed"])

    def test_echo_pipe_grep_no_match(self):
        result = evaluate_require({"command_succeeds": "echo 'BUILD FAILED' | grep 'SUCCEEDED'"})
        self.assertFalse(result["passed"])

    def test_timeout_is_failure(self):
        result = evaluate_require({"command_succeeds": "sleep 999"}, timeout=1)
        self.assertFalse(result["passed"])
        self.assertIn("timeout", result["detail"].lower())
```

- [ ] **Step 6: Run test to verify it fails**

Run: `cd /Users/aa/Documents/myskills/shared/scripts/orchestrator && python -m pytest test_check_requires.py::TestCommandSucceeds -v`
Expected: FAIL — `TypeError` (timeout param not supported yet)

- [ ] **Step 7: Implement command_succeeds primitive**

Add to `check_requires.py` inside `evaluate_require()`, before the `return unknown`:

```python
    if "command_succeeds" in req:
        cmd = req["command_succeeds"]
        cmd_timeout = kwargs.get("timeout", 60)
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, timeout=cmd_timeout
            )
            passed = result.returncode == 0
            detail = f"exit={result.returncode}"
            if not passed and result.stderr:
                detail += f" stderr={result.stderr.decode('utf-8', errors='replace')[:200]}"
            return {"primitive": "command_succeeds", "passed": passed, "detail": detail}
        except subprocess.TimeoutExpired:
            return {"primitive": "command_succeeds", "passed": False, "detail": f"timeout after {cmd_timeout}s"}
```

Also update the function signature:

```python
def evaluate_require(req: dict, **kwargs) -> dict:
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd /Users/aa/Documents/myskills/shared/scripts/orchestrator && python -m pytest test_check_requires.py::TestCommandSucceeds -v`
Expected: PASS (5 tests)

- [ ] **Step 9: Add JSON primitive tests**

Append to `test_check_requires.py`:

```python
class TestJsonFieldGte(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.json_path = os.path.join(self.tmpdir, "data.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write(self, data):
        with open(self.json_path, "w") as f:
            json.dump(data, f)

    def test_field_gte_pass(self):
        self._write({"coverage": 75})
        result = evaluate_require(
            {"json_field_gte": [self.json_path, "$.coverage", 50]}
        )
        self.assertTrue(result["passed"])

    def test_field_gte_fail(self):
        self._write({"coverage": 30})
        result = evaluate_require(
            {"json_field_gte": [self.json_path, "$.coverage", 50]}
        )
        self.assertFalse(result["passed"])

    def test_nested_field(self):
        self._write({"stats": {"score": 85}})
        result = evaluate_require(
            {"json_field_gte": [self.json_path, "$.stats.score", 80]}
        )
        self.assertTrue(result["passed"])

    def test_missing_file(self):
        result = evaluate_require(
            {"json_field_gte": ["/nonexistent.json", "$.x", 0]}
        )
        self.assertFalse(result["passed"])


class TestJsonArrayLengthGte(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.json_path = os.path.join(self.tmpdir, "data.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write(self, data):
        with open(self.json_path, "w") as f:
            json.dump(data, f)

    def test_root_array(self):
        self._write([1, 2, 3])
        result = evaluate_require(
            {"json_array_length_gte": [self.json_path, "$", 2]}
        )
        self.assertTrue(result["passed"])

    def test_root_array_too_short(self):
        self._write([1])
        result = evaluate_require(
            {"json_array_length_gte": [self.json_path, "$", 5]}
        )
        self.assertFalse(result["passed"])

    def test_nested_array(self):
        self._write({"items": [{"id": 1}, {"id": 2}]})
        result = evaluate_require(
            {"json_array_length_gte": [self.json_path, "$.items", 1]}
        )
        self.assertTrue(result["passed"])

    def test_empty_array(self):
        self._write({"items": []})
        result = evaluate_require(
            {"json_array_length_gte": [self.json_path, "$.items", 1]}
        )
        self.assertFalse(result["passed"])
```

- [ ] **Step 10: Run tests to verify they fail**

Run: `cd /Users/aa/Documents/myskills/shared/scripts/orchestrator && python -m pytest test_check_requires.py::TestJsonFieldGte test_check_requires.py::TestJsonArrayLengthGte -v`
Expected: FAIL — unknown primitive

- [ ] **Step 11: Implement JSON primitives**

Add to `check_requires.py`:

```python
def _resolve_json_path(data, path: str):
    """Resolve a simple JSON path like '$.stats.score' or '$' (root)."""
    if path == "$":
        return data, True
    parts = path.lstrip("$.").split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None, False
    return current, True
```

Add inside `evaluate_require()`, before the `return unknown`:

```python
    if "json_field_gte" in req:
        args = req["json_field_gte"]
        file_path, json_path, threshold = args[0], args[1], args[2]
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            value, found = _resolve_json_path(data, json_path)
            if not found:
                return {"primitive": "json_field_gte", "passed": False, "detail": f"path {json_path} not found"}
            passed = value >= threshold
            return {"primitive": "json_field_gte", "passed": passed, "detail": f"{json_path}={value} (threshold={threshold})"}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return {"primitive": "json_field_gte", "passed": False, "detail": str(e)}

    if "json_array_length_gte" in req:
        args = req["json_array_length_gte"]
        file_path, json_path, min_length = args[0], args[1], args[2]
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            value, found = _resolve_json_path(data, json_path)
            if not found:
                return {"primitive": "json_array_length_gte", "passed": False, "detail": f"path {json_path} not found"}
            if not isinstance(value, list):
                return {"primitive": "json_array_length_gte", "passed": False, "detail": f"path {json_path} is not an array"}
            passed = len(value) >= min_length
            return {"primitive": "json_array_length_gte", "passed": passed, "detail": f"len={len(value)} (min={min_length})"}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return {"primitive": "json_array_length_gte", "passed": False, "detail": str(e)}
```

- [ ] **Step 12: Run all tests**

Run: `cd /Users/aa/Documents/myskills/shared/scripts/orchestrator && python -m pytest test_check_requires.py -v`
Expected: PASS (17 tests)

- [ ] **Step 13: Add evaluate_node function and CLI tests**

Append to `test_check_requires.py`:

```python
from check_requires import evaluate_node


class TestEvaluateNode(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.sm_path = os.path.join(self.tmpdir, "state-machine.json")
        # Create a dummy file that node requires
        self.artifact = os.path.join(self.tmpdir, "artifact.json")
        with open(self.artifact, "w") as f:
            json.dump([1, 2, 3], f)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_all_pass(self):
        sm = {
            "schema_version": "1.0",
            "nodes": [{
                "id": "test-node",
                "entry_requires": [{"file_exists": self.artifact}],
                "exit_requires": [
                    {"file_exists": self.artifact},
                    {"json_array_length_gte": [self.artifact, "$", 2]}
                ]
            }],
            "safety": {},
            "progress": {}
        }
        with open(self.sm_path, "w") as f:
            json.dump(sm, f)

        result = evaluate_node(self.sm_path, "test-node", "exit")
        self.assertTrue(result["all_passed"])
        self.assertEqual(len(result["results"]), 2)

    def test_partial_fail(self):
        sm = {
            "schema_version": "1.0",
            "nodes": [{
                "id": "test-node",
                "entry_requires": [],
                "exit_requires": [
                    {"file_exists": self.artifact},
                    {"file_exists": "/nonexistent"}
                ]
            }],
            "safety": {},
            "progress": {}
        }
        with open(self.sm_path, "w") as f:
            json.dump(sm, f)

        result = evaluate_node(self.sm_path, "test-node", "exit")
        self.assertFalse(result["all_passed"])

    def test_unknown_node(self):
        sm = {"schema_version": "1.0", "nodes": [], "safety": {}, "progress": {}}
        with open(self.sm_path, "w") as f:
            json.dump(sm, f)

        with self.assertRaises(ValueError):
            evaluate_node(self.sm_path, "nonexistent", "entry")
```

- [ ] **Step 14: Run test to verify it fails**

Run: `cd /Users/aa/Documents/myskills/shared/scripts/orchestrator && python -m pytest test_check_requires.py::TestEvaluateNode -v`
Expected: FAIL — `ImportError`

- [ ] **Step 15: Implement evaluate_node and CLI**

Add to `check_requires.py`:

```python
def evaluate_node(sm_path: str, node_id: str, req_type: str = "exit") -> dict:
    """Evaluate all requires for a node. Returns { node, type, results[], all_passed }."""
    with open(sm_path, "r", encoding="utf-8") as f:
        sm = json.load(f)

    node = None
    for n in sm.get("nodes", []):
        if n["id"] == node_id:
            node = n
            break
    if node is None:
        raise ValueError(f"Node '{node_id}' not found in {sm_path}")

    key = f"{req_type}_requires"
    requires = node.get(key, [])
    results = [evaluate_require(r) for r in requires]
    all_passed = all(r["passed"] for r in results)

    return {
        "node": node_id,
        "type": req_type,
        "results": results,
        "all_passed": all_passed,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <state-machine.json> <node-id> [--type entry|exit]", file=sys.stderr)
        sys.exit(1)

    sm_path = sys.argv[1]
    node_id = sys.argv[2]
    req_type = "exit"
    if "--type" in sys.argv:
        idx = sys.argv.index("--type")
        req_type = sys.argv[idx + 1]

    result = evaluate_node(sm_path, node_id, req_type)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["all_passed"] else 1)
```

- [ ] **Step 16: Run all tests**

Run: `cd /Users/aa/Documents/myskills/shared/scripts/orchestrator && python -m pytest test_check_requires.py -v`
Expected: PASS (20 tests)

- [ ] **Step 17: Commit**

```bash
git add shared/scripts/orchestrator/check_requires.py shared/scripts/orchestrator/test_check_requires.py
git commit -m "feat(meta-skill): check_requires.py — 4 evaluation primitives for entry/exit_requires"
```

---

### Task 2: validate_bootstrap.py — Bootstrap Validation Script

**Files:**
- Create: `shared/scripts/orchestrator/validate_bootstrap.py`
- Test: `shared/scripts/orchestrator/test_validate_bootstrap.py`

Validates generated bootstrap products (Step 5.5 Layer 1+2): YAML frontmatter parsing, required fields, graph connectivity, dangerous command detection.

- [ ] **Step 1: Write tests for YAML frontmatter validation**

```python
#!/usr/bin/env python3
"""Tests for validate_bootstrap.py — bootstrap product validation."""

import json
import os
import tempfile
import unittest

from validate_bootstrap import validate_node_spec, validate_state_machine, validate_graph_connectivity, scan_dangerous_commands


class TestValidateNodeSpec(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write_spec(self, content):
        path = os.path.join(self.tmpdir, "spec.md")
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_valid_spec(self):
        path = self._write_spec(
            "---\nnode: test-node\nentry_requires:\n  - file_exists: a.json\nexit_requires:\n  - file_exists: b.json\n---\n\n# Task\nDo stuff."
        )
        errors = validate_node_spec(path)
        self.assertEqual(errors, [])

    def test_missing_node_field(self):
        path = self._write_spec(
            "---\nentry_requires: []\nexit_requires: []\n---\n\n# Task"
        )
        errors = validate_node_spec(path)
        self.assertTrue(any("node" in e for e in errors))

    def test_missing_exit_requires(self):
        path = self._write_spec(
            "---\nnode: test\nentry_requires: []\n---\n\n# Task"
        )
        errors = validate_node_spec(path)
        self.assertTrue(any("exit_requires" in e for e in errors))

    def test_no_frontmatter(self):
        path = self._write_spec("# Just markdown\nNo frontmatter here.")
        errors = validate_node_spec(path)
        self.assertTrue(any("frontmatter" in e.lower() for e in errors))


class TestValidateStateMachine(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_valid(self):
        sm = {
            "schema_version": "1.0",
            "nodes": [{"id": "a", "entry_requires": [], "exit_requires": []}],
            "safety": {"loop_detection": {"warn_threshold": 3, "stop_threshold": 5}, "max_global_iterations": 30},
            "progress": {"completed_nodes": [], "iteration_count": 0}
        }
        path = os.path.join(self.tmpdir, "sm.json")
        with open(path, "w") as f:
            json.dump(sm, f)
        errors = validate_state_machine(path)
        self.assertEqual(errors, [])

    def test_empty_nodes(self):
        sm = {"schema_version": "1.0", "nodes": [], "safety": {}, "progress": {}}
        path = os.path.join(self.tmpdir, "sm.json")
        with open(path, "w") as f:
            json.dump(sm, f)
        errors = validate_state_machine(path)
        self.assertTrue(any("empty" in e.lower() for e in errors))

    def test_missing_schema_version(self):
        sm = {"nodes": [{"id": "a"}], "safety": {}, "progress": {}}
        path = os.path.join(self.tmpdir, "sm.json")
        with open(path, "w") as f:
            json.dump(sm, f)
        errors = validate_state_machine(path)
        self.assertTrue(any("schema_version" in e for e in errors))


class TestGraphConnectivity(unittest.TestCase):
    def test_connected(self):
        nodes = [
            {"id": "a", "entry_requires": [], "exit_requires": [{"file_exists": "a.json"}]},
            {"id": "b", "entry_requires": [{"file_exists": "a.json"}], "exit_requires": []},
        ]
        orphans = validate_graph_connectivity(nodes)
        self.assertEqual(orphans, [])

    def test_orphan_node(self):
        nodes = [
            {"id": "a", "entry_requires": [], "exit_requires": [{"file_exists": "a.json"}]},
            {"id": "b", "entry_requires": [{"file_exists": "b.json"}], "exit_requires": []},
            {"id": "c", "entry_requires": [{"file_exists": "c.json"}], "exit_requires": []},
        ]
        # b and c have entry_requires that don't match any exit_requires output
        # But a has no entry_requires so it's a root — b and c are orphans
        # Actually connectivity is about: can every node be reached from a root?
        # We define root = node with empty entry_requires
        # Reachability: a node is reachable if its entry_requires overlap with some reachable node's exit_requires
        orphans = validate_graph_connectivity(nodes)
        # b requires b.json which nobody produces, c requires c.json which nobody produces
        self.assertIn("b", orphans)
        self.assertIn("c", orphans)


class TestDangerousCommands(unittest.TestCase):
    def test_safe_command(self):
        specs = [{"command_succeeds": "go build ./..."}]
        dangers = scan_dangerous_commands(specs)
        self.assertEqual(dangers, [])

    def test_rm_rf(self):
        specs = [{"command_succeeds": "rm -rf /tmp/stuff"}]
        dangers = scan_dangerous_commands(specs)
        self.assertTrue(len(dangers) > 0)

    def test_sudo(self):
        specs = [{"command_succeeds": "sudo apt install foo"}]
        dangers = scan_dangerous_commands(specs)
        self.assertTrue(len(dangers) > 0)

    def test_chmod_777(self):
        specs = [{"command_succeeds": "chmod 777 /etc/passwd"}]
        dangers = scan_dangerous_commands(specs)
        self.assertTrue(len(dangers) > 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/aa/Documents/myskills/shared/scripts/orchestrator && python -m pytest test_validate_bootstrap.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement validate_bootstrap.py**

```python
#!/usr/bin/env python3
"""Validate bootstrap-generated products (Step 5.5 Layer 1+2).

Checks:
  - Node-spec YAML frontmatter: parseable, required fields present
  - state-machine.json schema: nodes non-empty, safety complete, schema_version present
  - Graph connectivity: all nodes reachable from root (empty entry_requires)
  - Dangerous commands: scan command_succeeds for rm -rf, sudo, chmod 777, etc.

Usage:
  python validate_bootstrap.py <bootstrap-dir>
  Returns JSON: { "errors": [...], "warnings": [...], "passed": bool }
"""

import json
import os
import re
import sys

import yaml


# ── Dangerous command patterns ───────────────────────────────────────────────

DANGEROUS_PATTERNS = [
    (r"\brm\s+(-\w*f|-\w*r)+", "rm with -rf flags"),
    (r"\bsudo\b", "sudo usage"),
    (r"\bchmod\s+777\b", "chmod 777"),
    (r">\s*/dev/", "write to /dev/"),
    (r"\bmkfs\b", "mkfs (format disk)"),
    (r"\bdd\s+", "dd command"),
    (r":\(\)\s*\{", "fork bomb pattern"),
]


def validate_node_spec(path: str) -> list[str]:
    """Validate a single node-spec .md file. Returns list of error strings."""
    errors = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return [f"Cannot read {path}: {e}"]

    # Extract YAML frontmatter
    if not content.startswith("---"):
        return [f"{path}: No YAML frontmatter found"]

    parts = content.split("---", 2)
    if len(parts) < 3:
        return [f"{path}: Malformed frontmatter (no closing ---)"]

    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return [f"{path}: YAML parse error: {e}"]

    if not isinstance(fm, dict):
        return [f"{path}: Frontmatter is not a dict"]

    if "node" not in fm:
        errors.append(f"{path}: Missing required field 'node'")
    if "entry_requires" not in fm:
        errors.append(f"{path}: Missing required field 'entry_requires'")
    if "exit_requires" not in fm:
        errors.append(f"{path}: Missing required field 'exit_requires'")

    return errors


def validate_state_machine(path: str) -> list[str]:
    """Validate state-machine.json schema. Returns list of error strings."""
    errors = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            sm = json.load(f)
    except Exception as e:
        return [f"Cannot read {path}: {e}"]

    if "schema_version" not in sm:
        errors.append("Missing schema_version field")
    if not sm.get("nodes"):
        errors.append("nodes array is empty or missing")
    if "safety" not in sm:
        errors.append("Missing safety field")
    if "progress" not in sm:
        errors.append("Missing progress field")

    for node in sm.get("nodes", []):
        if "id" not in node:
            errors.append(f"Node missing 'id' field: {node}")

    return errors


def validate_graph_connectivity(nodes: list[dict]) -> list[str]:
    """Check that all nodes are reachable from root nodes.

    Root = node with empty entry_requires.
    Reachable = node whose entry_requires reference files that appear in
    some reachable node's exit_requires (file_exists primitives).

    Returns list of orphan node IDs.
    """
    if not nodes:
        return []

    # Extract what each node produces (from exit_requires file_exists)
    produces = {}
    for node in nodes:
        files = set()
        for req in node.get("exit_requires", []):
            if isinstance(req, dict) and "file_exists" in req:
                files.add(req["file_exists"])
        produces[node["id"]] = files

    # Extract what each node needs (from entry_requires file_exists)
    needs = {}
    for node in nodes:
        files = set()
        for req in node.get("entry_requires", []):
            if isinstance(req, dict) and "file_exists" in req:
                files.add(req["file_exists"])
        needs[node["id"]] = files

    # BFS from roots
    roots = [n["id"] for n in nodes if not needs.get(n["id"])]
    if not roots:
        return [n["id"] for n in nodes]  # No roots = all orphans

    reachable = set(roots)
    available_files = set()
    for r in roots:
        available_files |= produces.get(r, set())

    changed = True
    while changed:
        changed = False
        for node in nodes:
            nid = node["id"]
            if nid in reachable:
                continue
            node_needs = needs.get(nid, set())
            if node_needs and node_needs.issubset(available_files):
                reachable.add(nid)
                available_files |= produces.get(nid, set())
                changed = True

    all_ids = {n["id"] for n in nodes}
    orphans = sorted(all_ids - reachable)
    return orphans


def scan_dangerous_commands(requires: list[dict]) -> list[str]:
    """Scan command_succeeds entries for dangerous patterns. Returns list of warnings."""
    warnings = []
    for req in requires:
        if not isinstance(req, dict):
            continue
        cmd = req.get("command_succeeds", "")
        if not cmd:
            continue
        for pattern, description in DANGEROUS_PATTERNS:
            if re.search(pattern, cmd):
                warnings.append(f"Dangerous command detected ({description}): {cmd}")
    return warnings


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <bootstrap-dir>", file=sys.stderr)
        sys.exit(1)

    bootstrap_dir = sys.argv[1]
    all_errors = []
    all_warnings = []

    # Validate state-machine.json
    sm_path = os.path.join(bootstrap_dir, "state-machine.json")
    if os.path.exists(sm_path):
        all_errors.extend(validate_state_machine(sm_path))

        with open(sm_path, "r") as f:
            sm = json.load(f)
        orphans = validate_graph_connectivity(sm.get("nodes", []))
        if orphans:
            all_warnings.append(f"Orphan nodes (unreachable from root): {orphans}")
    else:
        all_errors.append(f"state-machine.json not found in {bootstrap_dir}")

    # Validate node-specs
    specs_dir = os.path.join(bootstrap_dir, "node-specs")
    all_commands = []
    if os.path.isdir(specs_dir):
        for fname in sorted(os.listdir(specs_dir)):
            if fname.endswith(".md"):
                spec_path = os.path.join(specs_dir, fname)
                all_errors.extend(validate_node_spec(spec_path))
                # Collect commands for dangerous check
                with open(spec_path, "r") as f:
                    content = f.read()
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        try:
                            fm = yaml.safe_load(parts[1])
                            for req in fm.get("exit_requires", []):
                                if isinstance(req, dict):
                                    all_commands.append(req)
                        except yaml.YAMLError:
                            pass

    dangers = scan_dangerous_commands(all_commands)
    all_errors.extend(dangers)  # Dangerous commands are errors, not warnings

    result = {
        "errors": all_errors,
        "warnings": all_warnings,
        "passed": len(all_errors) == 0,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["passed"] else 1)
```

- [ ] **Step 4: Run all tests**

Run: `cd /Users/aa/Documents/myskills/shared/scripts/orchestrator && python -m pytest test_validate_bootstrap.py -v`
Expected: PASS (14 tests)

- [ ] **Step 5: Commit**

```bash
git add shared/scripts/orchestrator/validate_bootstrap.py shared/scripts/orchestrator/test_validate_bootstrap.py
git commit -m "feat(meta-skill): validate_bootstrap.py — structure, graph, and safety validation"
```

---

### Task 3: Meta-Skill Plugin Scaffold

**Files:**
- Create: `claude/meta-skill/.claude-plugin/plugin.json`
- Create: `claude/meta-skill/.claude-plugin/marketplace.json`
- Create: `claude/meta-skill/SKILL.md`
- Create: `claude/meta-skill/commands/bootstrap.md`
- Create: `claude/meta-skill/skills/bootstrap.md`
- Create: `claude/meta-skill/knowledge/nodes/` (empty directory with .gitkeep)
- Create: `claude/meta-skill/knowledge/mappings/` (empty directory with .gitkeep)
- Create: `claude/meta-skill/knowledge/domains/` (empty directory with .gitkeep)
- Create: `claude/meta-skill/knowledge/learned/` (empty directory with .gitkeep)
- Create: `claude/meta-skill/knowledge/safety.md`
- Create: `claude/meta-skill/knowledge/orchestrator-template.md`

- [ ] **Step 1: Create plugin manifest**

```json
{
  "name": "meta-skill",
  "description": "Meta-skill generator: analyzes target projects and generates project-specific skills, commands, and state machine configurations. Replaces all 6 specialized skills with a unified /bootstrap + /run workflow.",
  "version": "0.1.0",
  "author": { "name": "dv" }
}
```

- [ ] **Step 2: Create marketplace manifest**

```json
{
  "name": "meta-skill",
  "version": "0.1.0",
  "display_name": "Meta-Skill Generator",
  "description": "Unified skill generator — analyzes projects, produces specialized node-specs and orchestrator configs. Two commands: /bootstrap (analyze + generate) and /run (execute).",
  "category": "development",
  "tags": ["meta", "orchestrator", "state-machine", "code-replicate", "dev-forge", "code-tuner"]
}
```

- [ ] **Step 3: Create SKILL.md**

```markdown
---
name: meta-skill
description: >
  Meta-skill generator for the myskills ecosystem. Analyzes target projects and generates
  project-specific skills (node-specs), state machine configurations, and orchestrator
  commands. Use /bootstrap to analyze a project, then /run to execute any workflow.
version: "0.1.0"
---

# Meta-Skill v0.1.0

> Unified skill generator — replaces 6 specialized plugins with /bootstrap + /run.

## Commands

| Command | Purpose |
|---------|---------|
| `/bootstrap` | Analyze target project → generate node-specs + state-machine + /run command |
| `/run [goal]` | Execute orchestrator toward a goal (generated by /bootstrap) |

## Architecture

```
Layer 1: Generator (/bootstrap)
  Lightweight analysis → project-specific node-specs + state-machine.json

Layer 2: Orchestrator (/run)
  LLM-driven state machine → dispatch subagents → safety guardrails
```

## Knowledge Base

```
knowledge/
├── nodes/      — Node templates (distilled from existing skills)
├── mappings/   — Tech stack mapping tables
├── domains/    — Business domain knowledge
├── learned/    — Cross-project experience (auto-populated)
├── safety.md   — Safety rules template
└── orchestrator-template.md — /run command template
```
```

- [ ] **Step 4: Create bootstrap command skeleton**

Write `claude/meta-skill/commands/bootstrap.md`:

```markdown
---
name: bootstrap
description: Analyze target project and generate project-specific skills, state machine, and orchestrator command.
arguments:
  - name: path
    description: Path to target project (default: current directory)
    required: false
---

Invoke the bootstrap skill to analyze this project and generate specialized configurations.

> Read ${CLAUDE_PLUGIN_ROOT}/skills/bootstrap.md and follow its protocol.
```

- [ ] **Step 5: Create bootstrap skill skeleton**

Write `claude/meta-skill/skills/bootstrap.md`:

```markdown
---
name: bootstrap
description: >
  Internal skill for /bootstrap command. Performs lightweight project analysis,
  generates project-specific node-specs and state-machine.json, validates products,
  and writes to target project.
---

# Bootstrap Protocol v0.1.0

> TODO: Full implementation in Plan 3. This is the skeleton.

## Steps

1. Lightweight analysis → bootstrap-profile.json
2. Select relevant knowledge (node templates + mappings + domains)
3. LLM generates node-specs
4. Generate state-machine.json
5. Generate .claude/commands/run.md
5.5. Validate products (structure + graph + safety + user confirmation)
6. Write files to target project
```

- [ ] **Step 6: Create knowledge directory structure**

```bash
mkdir -p claude/meta-skill/knowledge/{nodes,mappings,domains,learned}
touch claude/meta-skill/knowledge/nodes/.gitkeep
touch claude/meta-skill/knowledge/mappings/.gitkeep
touch claude/meta-skill/knowledge/domains/.gitkeep
touch claude/meta-skill/knowledge/learned/.gitkeep
```

- [ ] **Step 7: Create safety.md template**

Write `claude/meta-skill/knowledge/safety.md`:

```markdown
# Safety Rules Template

> Used by bootstrap to generate the safety section of state-machine.json.

## Default Configuration

```yaml
safety:
  loop_detection:
    warn_threshold: 3
    stop_threshold: 5
  max_global_iterations: 30
  progress_monotonicity:
    check_interval: 5
    violation_action: "output current best + TODO list"
  max_concurrent_nodes: 3
  max_node_execution_time: 600
```

## Loop Detection

Hash input: `node_id + exit_requires evaluation results (true/false per condition)`
Sliding window: last 10 iterations.
Does not include timestamps or other volatile data.

## Progress Monotonicity

`progress = len(completed_nodes) / len(total_nodes)`
`total_nodes` fixed at bootstrap time (prevention rules don't change node count).
Checked every `check_interval` iterations.

## Dangerous Command Patterns

Blocked in generated node-specs:
- `rm` with `-rf` flags
- `sudo` usage
- `chmod 777`
- Writes to `/dev/`
- `mkfs`, `dd`, fork bombs
```

- [ ] **Step 8: Create orchestrator-template.md**

Write `claude/meta-skill/knowledge/orchestrator-template.md`:

```markdown
# Orchestrator Template

> Used by bootstrap to generate .claude/commands/run.md in target projects.

## Template

The generated run.md should contain:

1. A YAML frontmatter with name, description, arguments
2. The orchestrator loop protocol:
   - Read state-machine.json (ground truth)
   - Mechanically evaluate entry/exit_requires (call check_requires.py)
   - LLM decides next node (only when multiple choices or errors)
   - Dispatch subagent with node-spec
   - Compress result to ≤500 char summary → write to state-machine.json
   - Safety checks (loop detection, progress monotonicity)
3. Diagnosis protocol reference (dispatch diagnosis subagent on failure)
4. Termination conditions

## Context Management

Orchestrator LLM context per iteration:
- Fixed: state-machine.json (nodes + safety + progress + node_summaries)
- Sliding: last 2-3 node results + last diagnosis (if any)
- Not in context: old node results, artifact contents, node-spec files

## Subagent Response Contract

All node subagents return:
```json
{
  "status": "success | failure | needs_input",
  "summary": "≤500 chars",
  "artifacts_created": [],
  "errors": [],
  "user_prompt": null
}
```
```

- [ ] **Step 9: Commit**

```bash
git add claude/meta-skill/
git commit -m "feat(meta-skill): plugin scaffold — manifests, SKILL.md, commands, knowledge structure"
```

---

### Task 4: Integration Smoke Test

**Files:**
- Create: `shared/scripts/orchestrator/test_integration.py`

End-to-end test: create a mock bootstrap directory with state-machine.json + node-specs, run both validation scripts, verify outputs.

- [ ] **Step 1: Write integration test**

```python
#!/usr/bin/env python3
"""Integration test: create mock bootstrap products and validate them."""

import json
import os
import shutil
import tempfile
import unittest

from check_requires import evaluate_node
from validate_bootstrap import (
    validate_node_spec,
    validate_state_machine,
    validate_graph_connectivity,
    scan_dangerous_commands,
)


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.bootstrap_dir = os.path.join(self.tmpdir, "bootstrap")
        self.specs_dir = os.path.join(self.bootstrap_dir, "node-specs")
        os.makedirs(self.specs_dir)

        # Create a mini state machine with 2 nodes
        self.sm = {
            "schema_version": "1.0",
            "nodes": [
                {
                    "id": "discovery",
                    "description": "Scan project",
                    "entry_requires": [],
                    "exit_requires": [
                        {"file_exists": os.path.join(self.tmpdir, "catalog.json")}
                    ],
                    "hints": [],
                },
                {
                    "id": "generate",
                    "description": "Generate artifacts",
                    "entry_requires": [
                        {"file_exists": os.path.join(self.tmpdir, "catalog.json")}
                    ],
                    "exit_requires": [
                        {"file_exists": os.path.join(self.tmpdir, "tasks.json")},
                        {"json_array_length_gte": [os.path.join(self.tmpdir, "tasks.json"), "$", 1]},
                    ],
                    "hints": [],
                },
            ],
            "safety": {
                "loop_detection": {"warn_threshold": 3, "stop_threshold": 5},
                "max_global_iterations": 30,
            },
            "progress": {"completed_nodes": [], "iteration_count": 0},
        }
        self.sm_path = os.path.join(self.bootstrap_dir, "state-machine.json")
        with open(self.sm_path, "w") as f:
            json.dump(self.sm, f)

        # Create matching node-specs
        for node_id, reqs in [("discovery", self.sm["nodes"][0]), ("generate", self.sm["nodes"][1])]:
            spec_content = f"---\nnode: {node_id}\nentry_requires: {json.dumps(reqs['entry_requires'])}\nexit_requires: {json.dumps(reqs['exit_requires'])}\n---\n\n# Task: {node_id}\nDo the thing."
            with open(os.path.join(self.specs_dir, f"{node_id}.md"), "w") as f:
                f.write(spec_content)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_validation_passes(self):
        errors = validate_state_machine(self.sm_path)
        self.assertEqual(errors, [], f"State machine errors: {errors}")

        for fname in os.listdir(self.specs_dir):
            path = os.path.join(self.specs_dir, fname)
            errors = validate_node_spec(path)
            self.assertEqual(errors, [], f"Node-spec errors for {fname}: {errors}")

    def test_graph_connected(self):
        orphans = validate_graph_connectivity(self.sm["nodes"])
        self.assertEqual(orphans, [])

    def test_check_requires_before_artifacts(self):
        # Before creating artifacts, discovery exit should fail
        result = evaluate_node(self.sm_path, "discovery", "exit")
        self.assertFalse(result["all_passed"])

    def test_check_requires_after_artifacts(self):
        # Create the artifacts
        with open(os.path.join(self.tmpdir, "catalog.json"), "w") as f:
            json.dump({"files": ["a.py"]}, f)
        with open(os.path.join(self.tmpdir, "tasks.json"), "w") as f:
            json.dump([{"id": "T001", "name": "task 1"}], f)

        # Now both nodes should pass
        r1 = evaluate_node(self.sm_path, "discovery", "exit")
        self.assertTrue(r1["all_passed"])
        r2 = evaluate_node(self.sm_path, "generate", "exit")
        self.assertTrue(r2["all_passed"])

    def test_no_dangerous_commands(self):
        all_commands = []
        for node in self.sm["nodes"]:
            for req in node.get("exit_requires", []):
                if isinstance(req, dict):
                    all_commands.append(req)
        dangers = scan_dangerous_commands(all_commands)
        self.assertEqual(dangers, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run integration test**

Run: `cd /Users/aa/Documents/myskills/shared/scripts/orchestrator && python -m pytest test_integration.py -v`
Expected: PASS (5 tests)

- [ ] **Step 3: Run all orchestrator tests together**

Run: `cd /Users/aa/Documents/myskills/shared/scripts/orchestrator && python -m pytest -v`
Expected: PASS (39 tests total)

- [ ] **Step 4: Commit**

```bash
git add shared/scripts/orchestrator/test_integration.py
git commit -m "test(meta-skill): integration test — mock bootstrap validation end-to-end"
```

---

### Task 5: Verify Plugin Structure

**Files:** None created — verification only.

- [ ] **Step 1: Verify directory structure matches spec**

Run:
```bash
find claude/meta-skill -type f | sort
```

Expected output:
```
claude/meta-skill/.claude-plugin/marketplace.json
claude/meta-skill/.claude-plugin/plugin.json
claude/meta-skill/SKILL.md
claude/meta-skill/commands/bootstrap.md
claude/meta-skill/knowledge/domains/.gitkeep
claude/meta-skill/knowledge/learned/.gitkeep
claude/meta-skill/knowledge/mappings/.gitkeep
claude/meta-skill/knowledge/nodes/.gitkeep
claude/meta-skill/knowledge/orchestrator-template.md
claude/meta-skill/knowledge/safety.md
claude/meta-skill/skills/bootstrap.md
```

- [ ] **Step 2: Verify Python scripts directory**

Run:
```bash
find shared/scripts/orchestrator -type f | sort
```

Expected output:
```
shared/scripts/orchestrator/check_requires.py
shared/scripts/orchestrator/test_check_requires.py
shared/scripts/orchestrator/test_integration.py
shared/scripts/orchestrator/test_validate_bootstrap.py
shared/scripts/orchestrator/validate_bootstrap.py
```

- [ ] **Step 3: Final commit with version bump note**

```bash
git add -A
git commit -m "chore(meta-skill): Plan 1 complete — core infrastructure + plugin scaffold"
```
