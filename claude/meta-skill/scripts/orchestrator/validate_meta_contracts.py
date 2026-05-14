#!/usr/bin/env python3
"""Validate cross-file meta-skill contracts that are easy to break manually."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path("claude/meta-skill")
BOOTSTRAP = ROOT / "skills/bootstrap.md"
DASHBOARD = ROOT / "scripts/orchestrator/render_approval_dashboard.py"
CAPABILITIES = ROOT / "knowledge/capabilities"


def validate_capability_files(errors: list[str]) -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    capabilities = sorted(set(re.findall(r'capability:\s*"([^"]+)"', text)))
    for capability in capabilities:
        path = CAPABILITIES / f"{capability}.md"
        if not path.exists():
            errors.append(
                f"bootstrap.md: capability '{capability}' has no {path.as_posix()}"
            )


def validate_node_id_templates(errors: list[str]) -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    for match in re.finditer(r"(?m)^node:\s+", text):
        line_no = text[: match.start()].count("\n") + 1
        errors.append(
            f"bootstrap.md:{line_no}: node-spec template uses 'node:'; use 'node_id:'"
        )


def validate_dashboard_virtual_gates(errors: list[str]) -> None:
    bootstrap_text = BOOTSTRAP.read_text(encoding="utf-8")
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
    text = BOOTSTRAP.read_text(encoding="utf-8")
    for script in (
        "render_approval_dashboard.py",
        "serve_approval.py",
        "apply_approval_action.py",
        "expand_game_2d_production.py",
        "validate_unattended_readiness.py",
    ):
        if f"scripts/orchestrator/{script}" not in text:
            errors.append(f"bootstrap.md: does not copy approval script {script}")


def validate_unattended_run_contract(errors: list[str]) -> None:
    bootstrap_text = BOOTSTRAP.read_text(encoding="utf-8")
    template = ROOT / "knowledge/orchestrator-template.md"
    template_text = template.read_text(encoding="utf-8")
    template_flat = " ".join(template_text.split())
    parent = ROOT / "skills/meta-orchestration/SKILL.md"
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
        "status != \"ready\"",
        "do not ask the user mid-run",
    ):
        if term not in template_text and term not in template_flat:
            errors.append(f"orchestrator-template.md: missing unattended preflight term {term}")
    if "unattended-run-readiness-qa" not in parent_text:
        errors.append("meta-orchestration/SKILL.md: missing unattended readiness child")


def validate_implement_goal_contract(errors: list[str]) -> None:
    bootstrap_text = BOOTSTRAP.read_text(encoding="utf-8")
    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for term in (
        "l) 继续实施开发",
        '"implement", "demo", "product-verify", "visual-verify", "quality-checks", "concept-acceptance"',
        "Do not treat `implement` as `rebuild`",
        "translate / rebuild / create / implement",
        "translate/rebuild/create/implement",
        "goals include translate/rebuild/create/implement",
        "do not silently convert `implement` into `rebuild`",
    ):
        if term not in bootstrap_text:
            errors.append(f"bootstrap.md: missing implement goal term {term}")
    if "| implement | Continue implementation" not in skill_text:
        errors.append("SKILL.md: missing implement capability row")


def main() -> int:
    errors: list[str] = []
    validate_capability_files(errors)
    validate_node_id_templates(errors)
    validate_dashboard_virtual_gates(errors)
    validate_approval_scripts_copied(errors)
    validate_unattended_run_contract(errors)
    validate_implement_goal_contract(errors)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
