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


def _as_bool(value) -> bool:
    return value is True or str(value).lower() == "true"


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def _load_readiness_spec(path: Path, blockers: list[dict]) -> dict:
    if not path.exists():
        _add(
            blockers,
            "missing_unattended_readiness_spec",
            f"{path} is missing; bootstrap must specialize unattended requirements before /run",
        )
        return {}
    try:
        spec = _load_json(path)
    except Exception as exc:
        _add(blockers, "invalid_unattended_readiness_spec", f"{path} cannot be parsed: {exc}")
        return {}
    if not isinstance(spec, dict):
        _add(blockers, "invalid_unattended_readiness_spec", f"{path} must contain a JSON object")
        return {}
    return spec


def _validate_policy_spec(spec: dict, blockers: list[dict], warnings: list[dict]) -> None:
    if not spec:
        return

    if not _as_bool(spec.get("forbid_mid_run_user_prompts")):
        _add(
            blockers,
            "missing_noninteractive_policy",
            "unattended spec must set forbid_mid_run_user_prompts=true",
        )
    if not _as_bool(spec.get("forbid_hidden_fallback_completion")):
        _add(
            blockers,
            "missing_no_fallback_policy",
            "unattended spec must set forbid_hidden_fallback_completion=true",
        )

    max_repair_attempts = spec.get("max_repair_attempts")
    if max_repair_attempts is None:
        _add(blockers, "missing_repair_attempt_budget", "unattended spec missing max_repair_attempts")
    elif not isinstance(max_repair_attempts, int) or max_repair_attempts < 1 or max_repair_attempts > 5:
        _add(
            blockers,
            "invalid_repair_attempt_budget",
            "unattended spec max_repair_attempts must be an integer from 1 to 5",
        )

    long_task_policy = spec.get("long_task_policy")
    if not isinstance(long_task_policy, dict):
        _add(blockers, "missing_long_task_recovery", "unattended spec missing long_task_policy")
    else:
        for key in ("file_based_handoff", "polling", "timeout", "retry", "resume"):
            if not _as_bool(long_task_policy.get(key)):
                _add(
                    blockers,
                    "missing_long_task_recovery",
                    f"unattended spec long_task_policy.{key} must be true",
                )

    repair_loops = spec.get("required_repair_loops")
    if repair_loops is None:
        warnings.append({
            "code": "missing_required_repair_loops",
            "message": "unattended spec declares no required repair loops; this is valid only for non-QA workflows",
        })
    elif not isinstance(repair_loops, list):
        _add(blockers, "invalid_repair_loop_spec", "required_repair_loops must be a list")


def _validate_required_capabilities(
    project_root: Path,
    spec: dict,
    blockers: list[dict],
    external_tool_findings: list[dict],
) -> None:
    capabilities = spec.get("required_capabilities") if isinstance(spec, dict) else None
    if capabilities is None:
        return
    if not isinstance(capabilities, list):
        _add(blockers, "invalid_required_capabilities", "required_capabilities must be a list")
        return

    for item in capabilities:
        if not isinstance(item, dict):
            _add(blockers, "invalid_required_capabilities", "required_capabilities entries must be objects")
            continue
        if item.get("required") is False:
            continue
        capability = item.get("capability")
        if not capability:
            _add(blockers, "invalid_required_capabilities", "required capability missing capability name")
            continue

        if capability == "codex_cli":
            codex_path = shutil.which("codex")
            external_tool_findings.append({"capability": "codex_cli", "path": codex_path, "source": "spec"})
            if not codex_path:
                _add(blockers, "missing_codex_cli", "Codex CLI is required by unattended spec")
        elif capability == "mcp_image_batch":
            settings = project_root / ".claude/settings.json"
            has_image_batch = False
            if settings.exists():
                try:
                    data = _load_json(settings)
                    servers = data.get("mcpServers") or {}
                    has_image_batch = "image-batch" in servers or "mcp-image-batch" in servers
                except Exception:
                    has_image_batch = False
            external_tool_findings.append({
                "capability": "mcp_image_batch",
                "registered": has_image_batch,
                "source": "spec",
            })
            if not has_image_batch:
                _add(blockers, "missing_mcp_image_batch", "mcp-image-batch is required by unattended spec")
        elif capability == "google_api_key":
            has_key = bool(os.environ.get(item.get("env") or "GOOGLE_API_KEY"))
            external_tool_findings.append({"capability": "google_api_key", "present": has_key, "source": "spec"})
            if not has_key:
                _add(blockers, "missing_google_key", "Google API key is required by unattended spec")
        elif capability == "fal_key":
            has_key = bool(os.environ.get(item.get("env") or "FAL_KEY"))
            external_tool_findings.append({"capability": "fal_key", "present": has_key, "source": "spec"})
            if not has_key:
                _add(blockers, "missing_fal_key", "FAL key is required by unattended spec")
        elif capability == "runtime_command":
            commands = item.get("commands")
            if not isinstance(commands, list) or not commands:
                _add(blockers, "missing_runtime_command", "runtime_command capability requires commands[]")
                continue
            missing = []
            for command in commands:
                if not isinstance(command, str) or not command.strip():
                    missing.append(command)
                    continue
                binary = command.strip().split()[0]
                if binary.startswith("./"):
                    if not (project_root / binary).exists():
                        missing.append(command)
                elif not shutil.which(binary):
                    missing.append(command)
            external_tool_findings.append({
                "capability": "runtime_command",
                "commands": commands,
                "missing_commands": missing,
                "source": "spec",
            })
            if missing:
                _add(blockers, "missing_runtime_command", f"runtime command binaries/files unavailable: {missing}")
        elif capability in {"playwright", "browser_automation"}:
            has_tool = bool(shutil.which("playwright") or shutil.which("npx"))
            external_tool_findings.append({"capability": capability, "available": has_tool, "source": "spec"})
            if not has_tool:
                _add(
                    blockers,
                    "missing_playwright_or_engine_automation",
                    f"{capability} is required by unattended spec",
                )
        elif capability == "engine_automation":
            commands = item.get("commands")
            if not isinstance(commands, list) or not commands:
                _add(
                    blockers,
                    "missing_playwright_or_engine_automation",
                    "engine_automation capability requires commands[]",
                )
        else:
            external_tool_findings.append({
                "capability": capability,
                "state": "declared_unchecked",
                "source": "spec",
            })


def _validate_repair_loop_spec(spec: dict, nodes: list[dict], blockers: list[dict]) -> None:
    if not spec or not isinstance(spec.get("required_repair_loops"), list):
        return
    node_ids = {node.get("node_id") for node in nodes if node.get("node_id")}
    node_by_id = {node.get("node_id"): node for node in nodes if node.get("node_id")}

    for index, loop in enumerate(spec.get("required_repair_loops") or []):
        if not isinstance(loop, dict):
            _add(blockers, "invalid_repair_loop_spec", f"required_repair_loops[{index}] must be an object")
            continue
        repair_node_id = loop.get("repair_node_id")
        qa_nodes = loop.get("qa_node_ids") or loop.get("qa_nodes") or []
        closure_nodes = loop.get("closure_node_ids") or loop.get("closure_nodes") or []
        if not repair_node_id:
            _add(blockers, "missing_repair_loop_node", f"required_repair_loops[{index}] missing repair_node_id")
            continue
        if repair_node_id not in node_ids:
            _add(blockers, "missing_repair_loop_node", f"repair loop node '{repair_node_id}' missing from workflow")
            continue
        for qa_node_id in qa_nodes:
            if qa_node_id not in node_ids:
                _add(blockers, "missing_repair_loop_source", f"QA node '{qa_node_id}' missing from workflow")
            elif qa_node_id not in (node_by_id[repair_node_id].get("hard_blocked_by") or []):
                _add(
                    blockers,
                    "repair_loop_not_blocked_by_qa",
                    f"repair loop '{repair_node_id}' must hard_blocked_by QA node '{qa_node_id}'",
                )
        for closure_node_id in closure_nodes:
            if closure_node_id not in node_ids:
                _add(blockers, "missing_repair_loop_closure", f"closure node '{closure_node_id}' missing from workflow")
            elif repair_node_id not in (node_by_id[closure_node_id].get("hard_blocked_by") or []):
                _add(
                    blockers,
                    "closure_not_blocked_by_repair_loop",
                    f"closure node '{closure_node_id}' must hard_blocked_by repair loop '{repair_node_id}'",
                )


def validate_unattended_readiness(project_root: Path) -> dict:
    bootstrap_root = project_root / ".allforai/bootstrap"
    workflow_path = bootstrap_root / "workflow.json"
    node_specs_dir = bootstrap_root / "node-specs"
    spec_path = bootstrap_root / "unattended-run-readiness-spec.json"
    blockers: list[dict] = []
    warnings: list[dict] = []
    approval_gate_findings: list[dict] = []
    non_interactive_findings: list[dict] = []
    external_tool_findings: list[dict] = []
    fallback_findings: list[dict] = []
    long_task_findings: list[dict] = []

    readiness_spec = _load_readiness_spec(spec_path, blockers)
    _validate_policy_spec(readiness_spec, blockers, warnings)

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

    _validate_required_capabilities(project_root, readiness_spec, blockers, external_tool_findings)
    _validate_repair_loop_spec(readiness_spec, nodes, blockers)

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
