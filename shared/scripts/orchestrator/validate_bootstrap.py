#!/usr/bin/env python3
"""Bootstrap product validation for generated node-specs and state-machine.

Four public functions:
  - validate_node_spec(path) -> list[str]
  - validate_state_machine(path) -> list[str]
  - validate_graph_connectivity(nodes) -> list[str]
  - scan_dangerous_commands(requires) -> list[str]

Plus a CLI: python validate_bootstrap.py <bootstrap-dir>
"""

import argparse
import json
import os
import re
import sys
from collections import deque
from typing import Any, Dict, List

# Try PyYAML, fallback to simple regex parser
try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


# ---------------------------------------------------------------------------
# YAML frontmatter helpers
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> tuple:
    """Parse YAML frontmatter from markdown text.

    Returns (parsed_dict | None, list[str] errors).
    """
    errors: List[str] = []

    if not text.startswith("---"):
        errors.append("File does not start with '---' (no YAML frontmatter)")
        return None, errors

    # Find closing ---
    second = text.find("---", 3)
    if second == -1:
        errors.append("No closing '---' delimiter for YAML frontmatter")
        return None, errors

    yaml_text = text[3:second].strip()

    if _HAS_YAML:
        try:
            data = yaml.safe_load(yaml_text)
            if not isinstance(data, dict):
                errors.append(f"YAML frontmatter did not parse as a dict (got {type(data).__name__})")
                return None, errors
            return data, errors
        except yaml.YAMLError as e:
            errors.append(f"YAML parse error: {e}")
            return None, errors
    else:
        # Simple regex fallback: parse top-level "key: value" lines
        data = {}
        try:
            for line in yaml_text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                m = re.match(r'^(\w+)\s*:\s*(.*)', line)
                if m:
                    key = m.group(1)
                    val = m.group(2).strip()
                    # Try to parse as JSON for lists/dicts
                    if val.startswith("[") or val.startswith("{"):
                        try:
                            data[key] = json.loads(val)
                        except json.JSONDecodeError:
                            data[key] = val
                    else:
                        data[key] = val
            return data, errors
        except Exception as e:
            errors.append(f"YAML parse error (fallback parser): {e}")
            return None, errors


# ---------------------------------------------------------------------------
# validate_node_spec
# ---------------------------------------------------------------------------

_REQUIRED_NODE_FIELDS = ("node", "entry_requires", "exit_requires")


def validate_node_spec(path: str) -> List[str]:
    """Validate a single node-spec .md file. Returns list of error strings."""
    errors: List[str] = []

    try:
        with open(path) as f:
            text = f.read()
    except Exception as e:
        return [f"Cannot read file: {e}"]

    data, parse_errors = _parse_frontmatter(text)
    errors.extend(parse_errors)

    if data is None:
        return errors

    for field in _REQUIRED_NODE_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    return errors


# ---------------------------------------------------------------------------
# validate_state_machine
# ---------------------------------------------------------------------------

def validate_state_machine(path: str) -> List[str]:
    """Validate state-machine.json. Returns list of error strings."""
    errors: List[str] = []

    try:
        with open(path) as f:
            data = json.load(f)
    except Exception as e:
        return [f"Cannot read/parse state-machine.json: {e}"]

    if "schema_version" not in data:
        errors.append("Missing required field: schema_version")

    if "safety" not in data:
        errors.append("Missing required field: safety")

    if "progress" not in data:
        errors.append("Missing required field: progress")

    nodes = data.get("nodes")
    if not isinstance(nodes, list):
        errors.append("'nodes' must be an array")
    elif len(nodes) == 0:
        errors.append("'nodes' array must be non-empty")
    else:
        for i, node in enumerate(nodes):
            if "id" not in node:
                errors.append(f"Node at index {i} missing required field: id")

    return errors


# ---------------------------------------------------------------------------
# validate_graph_connectivity
# ---------------------------------------------------------------------------

def _extract_file_exists(requires: list) -> set:
    """Extract file_exists paths from a list of require dicts."""
    paths = set()
    for req in (requires or []):
        if isinstance(req, dict) and "file_exists" in req:
            paths.add(req["file_exists"])
    return paths


def validate_graph_connectivity(nodes: List[Dict[str, Any]]) -> List[str]:
    """Check all nodes reachable from root(s) via BFS.

    Root = node with empty entry_requires.
    Returns list of orphan node IDs (unreachable nodes).
    """
    if not nodes:
        return []

    # Build node map
    node_map = {}
    for n in nodes:
        nid = n.get("id", "")
        node_map[nid] = n

    # Find roots: nodes with empty entry_requires
    roots = []
    for nid, n in node_map.items():
        entry = n.get("entry_requires", [])
        if not entry:
            roots.append(nid)

    if not roots:
        return list(node_map.keys())

    # BFS: iteratively expand reachable set
    reachable = set(roots)
    # Collect files produced by reachable nodes
    produced = set()
    for rid in roots:
        produced |= _extract_file_exists(node_map[rid].get("exit_requires", []))

    changed = True
    while changed:
        changed = False
        for nid, n in node_map.items():
            if nid in reachable:
                continue
            needed = _extract_file_exists(n.get("entry_requires", []))
            if needed and needed.issubset(produced):
                reachable.add(nid)
                produced |= _extract_file_exists(n.get("exit_requires", []))
                changed = True

    orphans = [nid for nid in node_map if nid not in reachable]
    return orphans


# ---------------------------------------------------------------------------
# scan_dangerous_commands
# ---------------------------------------------------------------------------

_DANGEROUS_PATTERNS = [
    (r'\brm\b.*-[^\s]*r[^\s]*f|rm\b.*-[^\s]*f[^\s]*r', "rm with -rf flags"),
    (r'\bsudo\b', "sudo usage"),
    (r'\bchmod\s+777\b', "chmod 777"),
    (r'/dev/', "write to /dev/"),
    (r'\bmkfs\b', "mkfs"),
    (r'\bdd\b', "dd command"),
    (r':\(\)\s*\{.*\|.*\}', "fork bomb"),
]


def scan_dangerous_commands(requires: List[Dict[str, str]]) -> List[str]:
    """Scan command_succeeds entries for dangerous patterns.

    Returns list of warning strings.
    """
    warnings: List[str] = []

    for req in requires:
        cmd = req.get("command_succeeds")
        if cmd is None:
            continue
        for pattern, label in _DANGEROUS_PATTERNS:
            if re.search(pattern, cmd):
                warnings.append(f"Dangerous command detected ({label}): {cmd}")

    return warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list = None):
    parser = argparse.ArgumentParser(
        description="Validate bootstrap products (node-specs + state-machine)")
    parser.add_argument("bootstrap_dir", help="Path to bootstrap directory")
    args = parser.parse_args(argv)

    bdir = args.bootstrap_dir
    errors: List[str] = []
    warnings: List[str] = []

    # Validate state-machine.json
    sm_path = os.path.join(bdir, "state-machine.json")
    if os.path.exists(sm_path):
        sm_errors = validate_state_machine(sm_path)
        errors.extend([f"state-machine.json: {e}" for e in sm_errors])

        # Load nodes for connectivity + dangerous command scan
        try:
            with open(sm_path) as f:
                sm_data = json.load(f)
            sm_nodes = sm_data.get("nodes", [])

            # Graph connectivity
            orphans = validate_graph_connectivity(sm_nodes)
            for o in orphans:
                errors.append(f"Graph connectivity: node '{o}' is unreachable from root")

            # Dangerous command scan across all nodes
            for node in sm_nodes:
                for req_type in ("entry_requires", "exit_requires"):
                    reqs = node.get(req_type, [])
                    node_warnings = scan_dangerous_commands(reqs)
                    for w in node_warnings:
                        warnings.append(f"Node '{node.get('id', '?')}' {req_type}: {w}")
        except Exception:
            pass
    else:
        errors.append("state-machine.json not found")

    # Validate node-spec files
    nodes_dir = os.path.join(bdir, "nodes")
    if os.path.isdir(nodes_dir):
        for fname in sorted(os.listdir(nodes_dir)):
            if fname.endswith(".md"):
                fpath = os.path.join(nodes_dir, fname)
                spec_errors = validate_node_spec(fpath)
                errors.extend([f"nodes/{fname}: {e}" for e in spec_errors])

    result = {
        "errors": errors,
        "warnings": warnings,
        "passed": len(errors) == 0,
    }

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
