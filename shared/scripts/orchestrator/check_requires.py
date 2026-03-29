#!/usr/bin/env python3
"""Mechanical evaluation of node entry/exit requires declarations.

Four primitives (no LLM, no network):
  - file_exists(path)
  - command_succeeds(cmd, timeout=30)
  - json_field_gte(file, json_path, value)
  - json_array_length_gte(file, json_path, min_length)

Plus evaluate_node(sm_path, node_id, req_type) and a CLI.
"""

import argparse
import json
import os
import subprocess
import sys
from typing import Any


# ---------------------------------------------------------------------------
# JSON dot-path navigation
# ---------------------------------------------------------------------------

def _resolve_json_path(data: Any, path: str) -> Any:
    """Navigate a simple dot-path like '$.field.sub' into *data*.

    '$' alone returns *data* as-is.  Raises KeyError / TypeError on miss.
    """
    if path == "$":
        return data
    if not path.startswith("$."):
        raise ValueError(f"Invalid json_path (must start with $ or $.): {path}")
    keys = path[2:].split(".")
    cur = data
    for k in keys:
        if isinstance(cur, dict):
            cur = cur[k]
        else:
            raise TypeError(f"Cannot index into {type(cur).__name__} with key '{k}'")
    return cur


# ---------------------------------------------------------------------------
# Four primitives
# ---------------------------------------------------------------------------

def file_exists(path: str) -> bool:
    """Return True if *path* exists (file or directory)."""
    if not path:
        return False
    return os.path.exists(path)


def command_succeeds(cmd: str, timeout: int = 30) -> bool:
    """Run *cmd* via shell; return True if exit code == 0."""
    try:
        result = subprocess.run(
            cmd, shell=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def json_field_gte(file: str, json_path: str, value: float) -> bool:
    """Read JSON *file*, navigate *json_path*, check number >= *value*."""
    try:
        with open(file) as f:
            data = json.load(f)
        resolved = _resolve_json_path(data, json_path)
        return float(resolved) >= float(value)
    except Exception:
        return False


def json_array_length_gte(file: str, json_path: str, min_length: int) -> bool:
    """Read JSON *file*, navigate *json_path*, check array length >= *min_length*."""
    try:
        with open(file) as f:
            data = json.load(f)
        resolved = _resolve_json_path(data, json_path)
        if not isinstance(resolved, list):
            return False
        return len(resolved) >= int(min_length)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Primitive dispatch
# ---------------------------------------------------------------------------

_PRIMITIVES = {
    "file_exists": lambda args: file_exists(args),
    "command_succeeds": lambda args: command_succeeds(args),
    "json_field_gte": lambda args: json_field_gte(args[0], args[1], args[2]),
    "json_array_length_gte": lambda args: json_array_length_gte(args[0], args[1], args[2]),
}


def _eval_single(req: dict) -> dict:
    """Evaluate one require declaration; return {primitive, detail, passed}.

    *req* must be a single-key dict, e.g. {"file_exists": "/some/path"}.
    """
    for prim_name, args in req.items():
        fn = _PRIMITIVES.get(prim_name)
        if fn is None:
            return {"primitive": prim_name, "detail": args, "passed": False,
                    "error": f"unknown primitive: {prim_name}"}
        passed = fn(args)
        return {"primitive": prim_name, "detail": args, "passed": passed}
    return {"primitive": "?", "detail": None, "passed": False, "error": "empty require"}


# ---------------------------------------------------------------------------
# evaluate_node
# ---------------------------------------------------------------------------

def evaluate_node(sm_path: str, node_id: str, req_type: str = "entry") -> dict:
    """Load state-machine.json, find *node_id*, evaluate its requires.

    *req_type* is 'entry' or 'exit'.
    Returns {"node": node_id, "type": req_type, "results": [...], "all_passed": bool}.
    Raises ValueError if *node_id* not found.
    """
    with open(sm_path) as f:
        sm = json.load(f)

    node = None
    for n in sm.get("nodes", []):
        if n.get("id") == node_id:
            node = n
            break

    if node is None:
        raise ValueError(f"Node '{node_id}' not found in {sm_path}")

    key = f"{req_type}_requires"
    requires = node.get(key, [])
    results = [_eval_single(r) for r in requires]
    return {
        "node": node_id,
        "type": req_type,
        "results": results,
        "all_passed": all(r["passed"] for r in results),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list = None):
    parser = argparse.ArgumentParser(
        description="Evaluate node entry/exit requires from state-machine.json")
    parser.add_argument("sm_path", help="Path to state-machine.json")
    parser.add_argument("node_id", help="Node ID to evaluate")
    parser.add_argument("--type", dest="req_type", default="entry",
                        choices=["entry", "exit"],
                        help="Require type (default: entry)")
    parser.add_argument("--json", dest="output_json", action="store_true",
                        help="Output results as JSON")
    args = parser.parse_args(argv)

    outcome = evaluate_node(args.sm_path, args.node_id, args.req_type)
    results = outcome["results"]
    all_passed = outcome["all_passed"]

    if args.output_json:
        print(json.dumps(outcome, indent=2))
    else:
        for r in results:
            status = "PASS" if r["passed"] else "FAIL"
            print(f"  [{status}] {r['primitive']}: {r['detail']}")
        if results:
            print(f"\n{'ALL PASSED' if all_passed else 'SOME FAILED'}")
        else:
            print("  (no requires)")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
