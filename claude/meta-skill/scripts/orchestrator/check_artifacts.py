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
    "conditional_pass",
    "degraded",
    "failed",
    "failed_validation",
    "failed_env",
    "incomplete",
    "not_generated",
    "not_ready",
    "partial",
    "partial_pass",
    "placeholder",
    "existence_only",
    "not_good_enough",
    "quality_failed",
    "needs_revision",
    "passed_with_warnings",
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
    "acceptance_state",
    "quality_status",
    "effect_status",
    "experience_status",
    "visual_quality_status",
)

PRODUCTION_GAP_FIELDS = (
    "asset_gaps",
    "audio_gaps",
    "code_gaps",
    "contract_gaps",
    "gaps",
    "warnings",
    "non_blocking_warnings",
    "known_gaps",
    "remaining_gaps",
    "test_gaps",
    "unresolved_findings",
    "degraded_contracts",
    "blockers",
    "major_findings",
    "quality_gaps",
    "effect_gaps",
    "experience_gaps",
    "visual_quality_gaps",
    "perceptual_gaps",
)

FORBIDDEN_PRODUCTION_GAP_TERMS = (
    "absent",
    "borrowed",
    "conditional pass",
    "debug scene",
    "degraded",
    "fallback",
    "generic",
    "generic placeholder",
    "not good enough",
    "quality gap",
    "quality failed",
    "existence only",
    "function only",
    "structure only",
    "looks wrong",
    "does not match concept",
    "graphics",
    "missing",
    "not delivered",
    "not_generated",
    "placeholder",
    "prototype",
    "prototypeboard",
    "pure-color",
    "sample scene",
    "silent",
    "spec_ready",
    "stub",
    "tween fallback",
    "缺失",
    "未完成",
    "未生成",
    "未修复",
    "未处理",
    "待处理",
    "剩余",
    "降级",
    "占位",
    "警告",
)

ALLOWED_PRODUCTION_GAP_FLAGS = (
    "allowed_by_production_policy",
    "explicitly_approved_for_launch",
    "prototype_mode_allowed",
)

STALE_SENSITIVE_ARTIFACT_MARKERS = (
    ".allforai/game-2d/assembly/",
    ".allforai/game-2d/qa/",
    ".allforai/game-2d/repair/",
    ".allforai/game-frontend/assembly/",
    ".allforai/game-frontend/qa/",
    ".allforai/visual-qa/",
)

STALE_SOURCE_DIRS = (
    "game-client/assets/scripts",
    "game-client/assets/scenes",
    "game-client/assets/resources",
    "assets/scripts",
    "assets/scenes",
    "assets/resources",
    "src",
)


def _resolve_path(path: str, project_root: Path | None = None) -> str:
    if os.path.isabs(path) or project_root is None:
        return path
    return str(project_root / path)


def _artifact_status_error(path: str, project_root: Path | None = None) -> dict | None:
    if not path.endswith(".json") or not os.path.exists(path):
        return None
    stale_error = _stale_runtime_artifact_error(path, project_root)
    if stale_error:
        return stale_error
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    if not data:
        return {
            "field": "$",
            "value": {},
            "reason": "empty JSON artifact is not a valid completion report or contract",
        }
    for field in STATUS_FIELDS:
        value = data.get(field)
        if isinstance(value, str) and (
            value.lower() in BLOCKING_STATUS_VALUES or value.lower().startswith("blocked_by_")
        ):
            return {
                "field": field,
                "value": value,
                "reason": "artifact report status is blocking; file existence is not completion",
            }
    gap_error = _production_gap_error(data)
    if gap_error:
        return gap_error
    return None


def _stale_runtime_artifact_error(path: str, project_root: Path | None) -> dict | None:
    if project_root is None:
        return None
    try:
        rel_path = str(Path(path).resolve().relative_to(project_root.resolve()))
    except Exception:
        return None
    if not any(marker in rel_path for marker in STALE_SENSITIVE_ARTIFACT_MARKERS):
        return None
    artifact_mtime = os.path.getmtime(path)
    newest_source: tuple[str, float] | None = None
    for rel_dir in STALE_SOURCE_DIRS:
        source_dir = project_root / rel_dir
        if not source_dir.exists():
            continue
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in {"node_modules", "library", "temp", "build"}]
            for name in files:
                if not name.endswith((".ts", ".js", ".json", ".scene", ".prefab", ".png", ".jpg", ".jpeg", ".webp", ".mp3", ".wav", ".ogg")):
                    continue
                full_path = os.path.join(root, name)
                mtime = os.path.getmtime(full_path)
                if mtime > artifact_mtime and (newest_source is None or mtime > newest_source[1]):
                    newest_source = (str(Path(full_path).relative_to(project_root)), mtime)
    if newest_source is None:
        return None
    return {
        "field": "$mtime",
        "value": rel_path,
        "newer_source": newest_source[0],
        "reason": "runtime/visual QA artifact is stale because source or asset files changed after it was written",
    }


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
        if field in {
            "asset_gaps",
            "audio_gaps",
            "blockers",
            "code_gaps",
            "contract_gaps",
            "gaps",
            "major_findings",
            "remaining_gaps",
            "test_gaps",
            "unresolved_findings",
        }:
            return {
                "field": field,
                "value": value,
                "reason": (
                    "artifact contains unresolved gaps/findings; continue repair and revalidation "
                    "instead of treating file existence as completion"
                ),
            }
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
            status_error = _artifact_status_error(resolved_path, project_root)
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
