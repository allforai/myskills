#!/usr/bin/env python3
"""Check exit_artifacts for workflow nodes. Simplified from check_requires.py.

Usage:
  python check_artifacts.py <workflow.json> [--node <node_id>] [--json]

Without --node: checks all nodes, prints summary.
With --node: checks one node's exit_artifacts.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


BLOCKING_STATUS_VALUES = {
    "accepted_with_warnings",
    "blocked",
    "degraded",
    "failed",
    "failed_validation",
    "failed_env",
    "not_generated",
    "not_ready",
    "placeholder",
    "needs_revision",
    "revision-requested",
    "spec_only",
    "spec_ready",
}

STATUS_FIELDS = (
    "status",
    "qa_status",
    "overall_status",
    "repair_status",
    "revalidation_status",
    "overall_launch_status",
    "validation_status",
)

PRODUCTION_GAP_FIELDS = (
    "asset_gaps",
    "warnings",
    "non_blocking_warnings",
    "known_gaps",
    "remaining_gaps",
    "degraded_contracts",
)

FORBIDDEN_PRODUCTION_GAP_TERMS = (
    "absent",
    "borrowed",
    "degraded",
    "fallback",
    "generic placeholder",
    "missing",
    "not delivered",
    "not_generated",
    "placeholder",
    "silent",
    "spec_ready",
    "stub",
    "tween fallback",
)

ALLOWED_PRODUCTION_GAP_FLAGS = (
    "allowed_by_production_policy",
    "explicitly_approved_for_launch",
    "prototype_mode_allowed",
)


def _resolve_path(path: str, project_root: Path | None = None) -> str:
    if os.path.isabs(path) or project_root is None:
        return path
    return str(project_root / path)


def _artifact_status_error(path: str) -> dict | None:
    if not path.endswith(".json") or not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    for field in STATUS_FIELDS:
        value = data.get(field)
        if isinstance(value, str) and value.lower() in BLOCKING_STATUS_VALUES:
            return {
                "field": field,
                "value": value,
                "reason": "artifact report status is blocking; file existence is not completion",
            }
    gap_error = _production_gap_error(data)
    if gap_error:
        return gap_error
    return None


def _allowed_gap(item) -> bool:
    if not isinstance(item, dict):
        return False
    return any(item.get(flag) is True for flag in ALLOWED_PRODUCTION_GAP_FLAGS)


def _gap_text(item) -> str:
    if isinstance(item, str):
        return item.lower()
    if isinstance(item, dict):
        parts = []
        for key, value in item.items():
            if key in ALLOWED_PRODUCTION_GAP_FLAGS:
                continue
            if isinstance(value, (str, int, float, bool)):
                parts.append(str(value))
            elif isinstance(value, list):
                parts.extend(str(v) for v in value if isinstance(v, (str, int, float, bool)))
        return " ".join(parts).lower()
    return ""


def _production_gap_error(data: dict) -> dict | None:
    policy = data.get("production_acceptance_policy")
    allow_gaps = isinstance(policy, dict) and policy.get("allow_placeholder_or_fallback_assets") is True

    for field in PRODUCTION_GAP_FIELDS:
        value = data.get(field)
        if value in (None, [], {}):
            continue
        items = value if isinstance(value, list) else [value]
        for item in items:
            if allow_gaps or _allowed_gap(item):
                continue
            text = _gap_text(item)
            matched = [term for term in FORBIDDEN_PRODUCTION_GAP_TERMS if term in text]
            if matched:
                return {
                    "field": field,
                    "value": item,
                    "matched_terms": matched,
                    "reason": (
                        "production artifact contains placeholder/stub/fallback/missing asset gap; "
                        "route to producer skill or explicitly lower scope before completion"
                    ),
                }
    return None


def check_node_artifacts(node: dict, project_root: Path | None = None) -> dict:
    """Check if a node's exit_artifacts all exist."""
    node_id = node.get("node_id")
    if not node_id:
        raise ValueError("workflow node missing required node_id")
    artifacts = node.get("exit_artifacts", [])
    results = []
    for item in artifacts:
        if isinstance(item, dict):
            path = item["path"]
            validation_commands = item.get("validation_commands", [])
        else:
            path = item
            validation_commands = []
        resolved_path = _resolve_path(path, project_root)
        entry = {"path": path, "exists": os.path.exists(resolved_path)}
        if entry["exists"]:
            status_error = _artifact_status_error(resolved_path)
            if status_error:
                entry["status_error"] = status_error
        if validation_commands and entry["exists"]:
            for cmd in validation_commands:
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    cwd=str(project_root) if project_root else None,
                )
                if proc.returncode != 0:
                    entry["validation_error"] = {
                        "command": cmd,
                        "stderr": proc.stderr.decode(errors="replace"),
                    }
                    break
        results.append(entry)
    return {
        "node_id": node_id,
        "goal": node.get("goal", ""),
        "all_exist": all(
            r["exists"] and "validation_error" not in r and "status_error" not in r
            for r in results
        ),
        "artifacts": results,
    }


def _project_root_for_workflow(workflow_path: str) -> Path:
    path = Path(workflow_path).resolve()
    if path.name == "workflow.json" and path.parent.name == "bootstrap" and path.parent.parent.name == ".allforai":
        return path.parent.parent.parent
    return Path.cwd()


def main():
    parser = argparse.ArgumentParser(description="Check workflow node exit artifacts")
    parser.add_argument("workflow_path", help="Path to workflow.json")
    parser.add_argument("--node", dest="node_id", help="Check specific node only")
    parser.add_argument("--json", dest="output_json", action="store_true")
    args = parser.parse_args()

    with open(args.workflow_path) as f:
        wf = json.load(f)

    nodes = wf.get("nodes", [])
    project_root = _project_root_for_workflow(args.workflow_path)

    if args.node_id:
        node = next((n for n in nodes if n.get("node_id") == args.node_id), None)
        if not node:
            print(f"Node '{args.node_id}' not found", file=sys.stderr)
            sys.exit(2)  # 2 = actual error (node not found), not "pending"
        result = check_node_artifacts(node, project_root)
        if args.output_json:
            print(json.dumps(result, indent=2))
            sys.exit(0)  # --json always exits 0; status is in the JSON
        else:
            status = "DONE" if result["all_exist"] else "PENDING"
            print(f"[{status}] {result['node_id']}: {result['goal']}")
            for a in result["artifacts"]:
                mark = "\u2713" if a["exists"] else "\u2717"
                print(f"  {mark} {a['path']}")
            sys.exit(0 if result["all_exist"] else 1)
    else:
        results = [check_node_artifacts(n, project_root) for n in nodes]
        done = sum(1 for r in results if r["all_exist"])
        total = len(results)
        if args.output_json:
            print(json.dumps({"done": done, "total": total, "nodes": results}, indent=2))
            sys.exit(0)  # --json always exits 0; status is in the JSON
        else:
            print(f"Progress: {done}/{total} nodes complete\n")
            for r in results:
                status = "DONE" if r["all_exist"] else "PENDING"
                print(f"  [{status}] {r['node_id']}: {r['goal']}")
            sys.exit(0 if done == total else 1)


if __name__ == "__main__":
    main()
