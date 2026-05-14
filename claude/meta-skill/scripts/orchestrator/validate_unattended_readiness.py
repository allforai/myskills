#!/usr/bin/env python3
"""Validate whether a generated workflow is ready for unattended /run."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


BLOCKING_STATUS = "not_ready"
READY_STATUS = "ready"


def _load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _artifact_path(item) -> str:
    if isinstance(item, dict):
        return item.get("path", "")
    return str(item)


def _node_id(node: dict) -> str:
    return node.get("node_id") or "<missing-node-id>"


def _add(blockers: list[dict], code: str, message: str, *, node_id: str | None = None) -> None:
    item = {"code": code, "message": message}
    if node_id:
        item["node_id"] = node_id
    blockers.append(item)


def _read_approval(path: Path, node_id: str) -> dict | None:
    if not path.exists():
        return None
    try:
        data = _load_json(path)
    except Exception:
        return None
    records = data.get("records") if isinstance(data, dict) else data
    if not isinstance(records, list):
        return None
    for record in records:
        if isinstance(record, dict) and record.get("node_id") == node_id:
            return record
    return None


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def validate_unattended_readiness(project_root: Path) -> dict:
    bootstrap_root = project_root / ".allforai/bootstrap"
    workflow_path = bootstrap_root / "workflow.json"
    node_specs_dir = bootstrap_root / "node-specs"
    blockers: list[dict] = []
    warnings: list[dict] = []
    approval_gate_findings: list[dict] = []
    non_interactive_findings: list[dict] = []
    external_tool_findings: list[dict] = []
    fallback_findings: list[dict] = []
    long_task_findings: list[dict] = []

    if not workflow_path.exists():
        _add(blockers, "missing_workflow", f"{workflow_path} does not exist")
        nodes: list[dict] = []
        workflow = {}
    else:
        try:
            workflow = _load_json(workflow_path)
            nodes = workflow.get("nodes") if isinstance(workflow, dict) else []
            if not isinstance(nodes, list):
                _add(blockers, "missing_workflow", "workflow.json nodes must be a list")
                nodes = []
        except Exception as exc:
            _add(blockers, "missing_workflow", f"workflow.json cannot be parsed: {exc}")
            workflow = {}
            nodes = []

    for rel in (
        "scripts/validate_bootstrap.py",
        "scripts/check_artifacts.py",
        "scripts/validate_unattended_readiness.py",
    ):
        path = bootstrap_root / rel
        if not path.exists():
            _add(blockers, "missing_bootstrap_validator", f"{path} is missing")

    all_node_text = []
    for node in nodes:
        nid = _node_id(node)
        spec_path = node_specs_dir / f"{nid}.md"
        if not spec_path.exists():
            _add(blockers, "missing_node_spec", f"{spec_path} is missing", node_id=nid)
            continue
        text = spec_path.read_text(encoding="utf-8")
        all_node_text.append(text)

        if _contains_any(text, ("AskUserQuestion", "request user input", "ask the user", "询问用户")):
            _add(
                blockers,
                "node_spec_allows_user_prompt",
                "node-spec contains interactive user prompt language",
                node_id=nid,
            )
            non_interactive_findings.append({"node_id": nid, "state": "failed"})

        if "COMPLETED_WITH_LIMITS" in text and not node.get("allow_completed_with_limits"):
            _add(
                blockers,
                "forbidden_completed_with_limits",
                "node-spec mentions COMPLETED_WITH_LIMITS without node.allow_completed_with_limits=true",
                node_id=nid,
            )
            fallback_findings.append({"node_id": nid, "state": "failed"})

        if _contains_any(text, ("long-task", "poll", "task_id", "mcp-image-batch")):
            has_recovery = _contains_any(text, ("retry", "rerun", "resume", "repair", "timeout", "poll"))
            long_task_findings.append({"node_id": nid, "has_recovery_policy": has_recovery})
            if not has_recovery:
                _add(
                    blockers,
                    "missing_long_task_recovery",
                    "long-task node lacks retry/rerun/resume/poll policy",
                    node_id=nid,
                )

        if node.get("human_gate") is True:
            approval_path = node.get("approval_record_path")
            record = _read_approval(project_root / approval_path, nid) if approval_path else None
            gate_status = record.get("gate_status") if record else None
            finding = {"node_id": nid, "approval_record_path": approval_path, "gate_status": gate_status}
            approval_gate_findings.append(finding)
            if gate_status != "approved":
                _add(
                    blockers,
                    "pending_human_gate",
                    f"human_gate node is not approved (gate_status={gate_status!r})",
                    node_id=nid,
                )

    blob = json.dumps(workflow, ensure_ascii=False) + "\n" + "\n".join(all_node_text)
    lower_blob = blob.lower()

    if "codex" in lower_blob or "visual-acceptance" in lower_blob or "screenshot" in lower_blob:
        codex_path = shutil.which("codex")
        external_tool_findings.append({"capability": "codex_cli", "path": codex_path})
        if not codex_path:
            _add(blockers, "missing_codex_cli", "Codex CLI is required for visual review but not found in PATH")

    if "mcp-image-batch" in lower_blob or "image-batch" in lower_blob:
        settings = project_root / ".claude/settings.json"
        has_image_batch = False
        if settings.exists():
            try:
                data = _load_json(settings)
                has_image_batch = "image-batch" in (data.get("mcpServers") or {})
            except Exception:
                has_image_batch = False
        external_tool_findings.append({"capability": "mcp_image_batch", "registered": has_image_batch})
        if not has_image_batch:
            _add(blockers, "missing_mcp_image_batch", "image-batch MCP is required but not registered")

    if "google" in lower_blob or "lyria" in lower_blob or "imagen" in lower_blob:
        has_key = bool(os.environ.get("GOOGLE_API_KEY"))
        external_tool_findings.append({"capability": "google_api_key", "present": has_key})
        if not has_key:
            _add(blockers, "missing_google_key", "GOOGLE_API_KEY is required by selected workflow")

    if "fal.ai" in lower_blob or "fal_key" in lower_blob:
        has_key = bool(os.environ.get("FAL_KEY"))
        external_tool_findings.append({"capability": "fal_key", "present": has_key})
        if not has_key:
            _add(blockers, "missing_fal_key", "FAL_KEY is required by selected workflow")

    if "program-development-node-handoff.json" in lower_blob and "game-frontend" in lower_blob:
        if "runtime-gameplay-visual-acceptance" not in lower_blob:
            _add(
                blockers,
                "unexpanded_program_handoff",
                "game frontend handoff exists but runtime gameplay visual QA is not represented",
            )

    if "game_2d_production" in lower_blob or "game-2d-production" in lower_blob:
        if "game-2d-production-closure-qa" not in lower_blob and "2d-production-closure-qa" not in lower_blob:
            _add(
                blockers,
                "unexpanded_game_2d_production_handoff",
                "game 2D production handoff exists but 2D production closure QA is not represented",
            )

    status = READY_STATUS if not blockers else BLOCKING_STATUS
    return {
        "status": status,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "blockers": blockers,
        "warnings": warnings,
        "required_capabilities": external_tool_findings,
        "approval_gate_findings": approval_gate_findings,
        "non_interactive_findings": non_interactive_findings,
        "external_tool_findings": external_tool_findings,
        "fallback_findings": fallback_findings,
        "long_task_findings": long_task_findings,
        "recommended_pre_run_actions": [
            "Approve or revise pending human gates before /run.",
            "Run /setup check and configure missing external tools or keys.",
            "Re-bootstrap if program handoff or frontend QA nodes are not expanded.",
            "Remove forbidden COMPLETED_WITH_LIMITS paths or explicitly lower scope before /run.",
        ]
        if blockers
        else [],
    }


def write_markdown(path: Path, report: dict) -> None:
    lines = [
        "# Unattended Run Readiness",
        "",
        f"Status: `{report['status']}`",
        f"Checked at: `{report['checked_at']}`",
        "",
        "## Blockers",
    ]
    if report["blockers"]:
        for blocker in report["blockers"]:
            node = f" `{blocker['node_id']}`" if blocker.get("node_id") else ""
            lines.append(f"- `{blocker['code']}`{node}: {blocker['message']}")
    else:
        lines.append("- None")
    lines.extend(["", "## Required Capabilities"])
    for item in report.get("required_capabilities", []):
        lines.append(f"- `{item.get('capability')}`: {json.dumps(item, ensure_ascii=False)}")
    lines.extend(["", "## Recommended Pre-Run Actions"])
    actions = report.get("recommended_pre_run_actions") or ["Ready for unattended /run."]
    for action in actions:
        lines.append(f"- {action}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.project_root)
    report = validate_unattended_readiness(root)
    if args.write_report:
        out = root / ".allforai/bootstrap/unattended-run-readiness.json"
        _write_json(out, report)
        write_markdown(root / ".allforai/bootstrap/unattended-run-readiness.md", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
