#!/usr/bin/env python3
"""Validate cross-file meta-skill contracts that are easy to break manually."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path("claude/meta-skill")
# bootstrap.md plus the protocol files it delegates to (ADR-0001). Missing files are skipped.
BOOTSTRAP_CORPUS = (
    "skills/bootstrap.md",
    "knowledge/bootstrap-planning.md",
    "knowledge/bootstrap-art-pipeline.md",
    "knowledge/bootstrap-audits.md",
    "knowledge/node-spec-template.md",
    "knowledge/engine-detection.md",
    "knowledge/suppress-rules.md",
)
DASHBOARD = ROOT / "scripts/orchestrator/render_approval_dashboard.py"
CAPABILITIES = ROOT / "knowledge/capabilities"


def _bootstrap_files() -> list[Path]:
    return [ROOT / rel for rel in BOOTSTRAP_CORPUS if (ROOT / rel).exists()]


def _bootstrap_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in _bootstrap_files())


def validate_capability_files(errors: list[str]) -> None:
    text = _bootstrap_text()
    capabilities = sorted(set(re.findall(r'capability:\s*"([^"]+)"', text)))
    for capability in capabilities:
        path = CAPABILITIES / f"{capability}.md"
        if not path.exists():
            errors.append(
                f"bootstrap.md: capability '{capability}' has no {path.as_posix()}"
            )


def validate_node_id_templates(errors: list[str]) -> None:
    for path in _bootstrap_files():
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"(?m)^node:\s+", text):
            line_no = text[: match.start()].count("\n") + 1
            errors.append(
                f"{path.name}:{line_no}: node-spec template uses forbidden legacy 'node:'; use 'node_id:'"
            )


def validate_dashboard_virtual_gates(errors: list[str]) -> None:
    bootstrap_text = _bootstrap_text()
    dashboard_text = DASHBOARD.read_text(encoding="utf-8")
    required = []
    for node_id in ("art-concept", "architecture-concept-validation"):
        if node_id in bootstrap_text:
            required.append(node_id)
    for node_id in required:
        if node_id not in dashboard_text:
            errors.append(
                f"render_approval_dashboard.py: missing virtual gate support for {node_id}"
            )
    for required_snippet in (
        "GATE_JSON_PATHS",
        "statusFromGateState",
        "blocked_validation_items",
    ):
        if required_snippet not in dashboard_text:
            errors.append(
                f"render_approval_dashboard.py: missing gate-state handling snippet {required_snippet}"
            )


def validate_approval_scripts_copied(errors: list[str]) -> None:
    text = _bootstrap_text()
    for script in (
        "render_approval_dashboard.py",
        "serve_approval.py",
        "apply_approval_action.py",
        "expand_game_2d_production.py",
        "reconcile_bootstrap_workflow.py",
        "record_meta_skill_feedback.py",
        "record_run_event.py",
        "summarize_run_log.py",
        "validate_unattended_readiness.py",
    ):
        if f"scripts/orchestrator/{script}" not in text:
            errors.append(f"bootstrap.md: does not copy approval script {script}")


def validate_unattended_run_contract(errors: list[str]) -> None:
    bootstrap_text = _bootstrap_text()
    template = ROOT / "knowledge/orchestrator-template.md"
    template_text = template.read_text(encoding="utf-8")
    template_flat = " ".join(template_text.split())
    parent = ROOT / "skills/meta-orchestration/PACK.md"
    parent_text = parent.read_text(encoding="utf-8")
    skill = ROOT / "skills/meta-orchestration/40-qa/unattended-run-readiness-qa/SKILL.md"
    if not skill.exists():
        errors.append("meta-orchestration: missing unattended-run-readiness-qa skill")
    for term in (
        ".allforai/bootstrap/unattended-run-readiness-spec.json",
        ".allforai/bootstrap/unattended-run-readiness.json",
        ".allforai/bootstrap/unattended-run-readiness.md",
        "validate_unattended_readiness.py",
    ):
        if term not in bootstrap_text:
            errors.append(f"bootstrap.md: missing unattended readiness term {term}")
    for term in (
        "Preflight Gate",
        "validate_unattended_readiness.py",
        "expand_game_2d_production.py",
        "record_meta_skill_feedback.py",
        "record_run_event.py",
        "summarize_run_log.py",
        "run-log.jsonl",
        "run-summary.md",
        "status != \"ready\"",
        "do not ask the user mid-run",
    ):
        if term not in template_text and term not in template_flat:
            errors.append(f"orchestrator-template.md: missing unattended preflight term {term}")
    if "unattended-run-readiness-qa" not in parent_text:
        errors.append("meta-orchestration/PACK.md: missing unattended readiness child")
    if "execution-repair-loop" not in parent_text:
        errors.append("meta-orchestration/PACK.md: missing execution repair loop child")


def validate_execution_repair_loop_contract(errors: list[str]) -> None:
    bootstrap_text = _bootstrap_text()
    template = ROOT / "knowledge/orchestrator-template.md"
    template_text = template.read_text(encoding="utf-8")
    skill = ROOT / "skills/meta-orchestration/40-qa/execution-repair-loop/SKILL.md"
    if not skill.exists():
        errors.append("meta-orchestration: missing execution-repair-loop skill")
        return
    skill_text = skill.read_text(encoding="utf-8")
    for term in (
        "QA repair loop",
        "code_gaps",
        "test_gaps",
        "rerun affected QA evidence",
        "3 attempts",
        "execution-repair-loop",
    ):
        if term not in bootstrap_text:
            errors.append(f"bootstrap.md: missing generic repair loop term {term}")
    for term in (
        "code_gaps",
        "test_gaps",
        "repair loop",
        "Rerun affected QA evidence",
    ):
        if term not in template_text:
            errors.append(f"orchestrator-template.md: missing repair loop runtime term {term}")
    for term in (
        "code_gaps",
        "test_gaps",
        "environment_blockers",
        "blocked_by_environment",
        "3 attempts",
        "Downstream closure nodes",
    ):
        if term not in skill_text:
            errors.append(f"execution-repair-loop/SKILL.md: missing repair contract term {term}")


def validate_implement_goal_contract(errors: list[str]) -> None:
    bootstrap_text = _bootstrap_text()
    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for term in (
        "l) 继续实施开发",
        '"implement", "demo", "product-verify", "visual-verify", "quality-checks", "concept-acceptance"',
        "Do not treat `implement` as `rebuild`",
        "translate / rebuild / create / implement",
        "translate/rebuild/create/implement",
        "goals include translate/rebuild/create/implement",
        "silently convert `implement` into `rebuild`",
    ):
        if term not in bootstrap_text:
            errors.append(f"bootstrap.md: missing implement goal term {term}")
    if "| implement | Continue implementation" not in skill_text:
        errors.append("SKILL.md: missing implement capability row")


def validate_feedback_contract(errors: list[str]) -> None:
    feedback = ROOT / "knowledge/feedback-protocol.md"
    feedback_text = feedback.read_text(encoding="utf-8")
    script = ROOT / "scripts/orchestrator/record_meta_skill_feedback.py"
    script_text = script.read_text(encoding="utf-8") if script.exists() else ""
    for term in (
        "Local myskills repo first",
        "Anonymous GitHub fallback",
        "META_SKILL_LOCAL_REPO",
        "META_SKILL_FEEDBACK_MODE=auto",
        "pending-feedback.json",
        "privacy scan",
    ):
        if term not in feedback_text:
            errors.append(f"feedback-protocol.md: missing feedback target term {term}")
    for term in (
        "find_local_myskills",
        "docs/feedback/inbox",
        "pending-feedback.json",
        "gh issue create",
        "privacy_scan_failed",
    ):
        if term not in script_text:
            errors.append(f"record_meta_skill_feedback.py: missing implementation term {term}")


def validate_canvas2d_contract(errors: list[str]) -> None:
    bootstrap_text = _bootstrap_text()
    canvas2d = ROOT / "knowledge/engines/canvas2d.md"
    if not canvas2d.exists():
        errors.append("knowledge/engines/canvas2d.md: missing Canvas2D specialization knowledge")
        return
    canvas2d_text = canvas2d.read_text(encoding="utf-8")
    for term in (
        "Canvas2D game-client profile",
        "interface-cards",
        "qa-repair-loop",
        "concept-acceptance",
        "deviceScaleFactor",
        "I/O Runtime-Effect QA",
        "shape holes",
        "Module Wiring Gate",
    ):
        if term not in canvas2d_text:
            errors.append(f"canvas2d.md: missing specialization term {term}")
    # ADR-0001: bootstrap no longer enumerates runtime node families; it must still
    # read the runtime knowledge file and record a project-local runtime profile.
    for term in (
        "knowledge/engines/<runtime>.md",
        "project-local runtime profile",
    ):
        if term not in bootstrap_text:
            errors.append(f"bootstrap.md: missing runtime-specialized bootstrap term {term}")


def validate_bootstrap_node_expansion_contract(errors: list[str]) -> None:
    bootstrap_text = _bootstrap_text()
    skill = ROOT / "skills/meta-orchestration/40-qa/bootstrap-node-expansion-qa/SKILL.md"
    parent = ROOT / "skills/meta-orchestration/PACK.md"
    if not skill.exists():
        errors.append("meta-orchestration bootstrap-node-expansion-qa skill missing")
        return
    skill_text = skill.read_text(encoding="utf-8")
    parent_text = parent.read_text(encoding="utf-8")
    for term in (
        "bootstrap-audits.md",
        "Acceptance-driven execution",
        "Quality-driven acceptance",
        "Attention management",
        "Bootstrap context compression",
        "Closure wiring",
        "named means",
        "effect verification",
        "code-only or existence-only completion",
        "existence-only completion",
        "quality_gaps",
        "missing_attention_contract",
        "unbounded_context_pull",
        "missing_stop_conditions",
        "repair_loop_not_blocked_by_qa",
        "acceptance_not_blocked_by_repair_loop",
        "qa_report_without_revalidation",
    ):
        if term not in skill_text:
            errors.append(f"bootstrap-node-expansion-qa: missing contract term {term}")
    # ADR-0001: the four-lens node-expansion gate became the bootstrap-audits lenses
    # (Coverage Self-Check, G0, A0, Phase A, three-lens DAG with reverse critic).
    for term in (
        "bootstrap-node-expansion-qa",
        "Coverage Self-Check",
        "reverse critic",
        "three-lens",
        "named means",
        "## Effect Verification",
        "quality-driven acceptance",
        "## Quality Acceptance",
        "quality_gaps",
        "## Attention Contract",
        "Primary outcome",
        "Non-goals",
        "Must-read inputs",
        "Stop conditions",
        "Repair targets",
        "Bootstrap should spend context once",
        "execute in pull mode",
    ):
        if term not in bootstrap_text:
            errors.append(f"bootstrap.md: missing bootstrap node expansion term {term}")
    if "bootstrap-node-expansion-qa" not in parent_text:
        errors.append("meta-orchestration/PACK.md: missing bootstrap-node-expansion-qa child")


def validate_rebootstrap_reconciliation_contract(errors: list[str]) -> None:
    bootstrap_text = _bootstrap_text()
    script = ROOT / "scripts/orchestrator/reconcile_bootstrap_workflow.py"
    if not script.exists():
        errors.append("scripts/orchestrator/reconcile_bootstrap_workflow.py: missing")
        return
    script_text = script.read_text(encoding="utf-8")
    for term in (
        "workflow-state-index.json",
        "workflow-reconciliation-plan.json",
        "workflow-reconciliation-plan.md",
        "keep/update/add/remove/supersede/invalidate",
        "reconciliation_applied",
        "--candidate-workflow",
        "must not silently overwrite",
    ):
        if term not in bootstrap_text:
            errors.append(f"bootstrap.md: missing re-bootstrap reconciliation term {term}")
    for term in (
        "build_state_index",
        "build_reconciliation_plan",
        "orphan_specs",
        "artifact_readiness",
        "supersede",
        "invalidate",
        "quality_gaps",
    ):
        if term not in script_text:
            errors.append(f"reconcile_bootstrap_workflow.py: missing implementation term {term}")


def validate_public_entrypoint_surface(errors: list[str]) -> None:
    commands_dir = ROOT / "commands"
    allowed_commands = {"setup.md", "bootstrap.md"}
    actual_commands = {path.name for path in commands_dir.glob("*.md")}
    extra_commands = sorted(actual_commands - allowed_commands)
    missing_commands = sorted(allowed_commands - actual_commands)
    for name in missing_commands:
        errors.append(f"commands/{name}: required public command missing")
    for name in extra_commands:
        errors.append(
            f"commands/{name}: unexpected public command; only setup/bootstrap are installed, and run is generated per project"
        )

    public_pack_skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    for path in public_pack_skills:
        errors.append(
            f"{path.relative_to(ROOT)}: unexpected public pack skill; use PACK.md so internal packs do not appear in the skill picker"
        )


def main() -> int:
    errors: list[str] = []
    validate_capability_files(errors)
    validate_node_id_templates(errors)
    validate_dashboard_virtual_gates(errors)
    validate_approval_scripts_copied(errors)
    validate_unattended_run_contract(errors)
    validate_execution_repair_loop_contract(errors)
    validate_implement_goal_contract(errors)
    validate_feedback_contract(errors)
    validate_canvas2d_contract(errors)
    validate_bootstrap_node_expansion_contract(errors)
    validate_rebootstrap_reconciliation_contract(errors)
    validate_public_entrypoint_surface(errors)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
