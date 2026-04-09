#!/usr/bin/env python3
"""Static parity checks for codex/meta-skill.

This script verifies the Codex adapter surface exists and that its primary
contracts are aligned with the repository's current meta-skill conventions.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CODEX_META = ROOT / "codex" / "meta-skill"
ORCH = ROOT / "shared" / "scripts" / "orchestrator"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_exists(path: Path, label: str, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"missing: {label} ({path})")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    required_paths = [
        (CODEX_META / "SKILL.md", "SKILL.md"),
        (CODEX_META / ".mcp.json", ".mcp.json"),
        (CODEX_META / "install.sh", "install.sh"),
        (CODEX_META / "commands" / "bootstrap.md", "commands/bootstrap.md"),
        (CODEX_META / "commands" / "setup.md", "commands/setup.md"),
        (CODEX_META / "commands" / "journal.md", "commands/journal.md"),
        (CODEX_META / "commands" / "journal-merge.md", "commands/journal-merge.md"),
        (CODEX_META / "skills" / "bootstrap.md", "skills/bootstrap.md"),
        (CODEX_META / "knowledge" / "high-risk-specialization.md", "knowledge/high-risk-specialization.md"),
        (CODEX_META / "knowledge" / "im-specialization.md", "knowledge/im-specialization.md"),
        (CODEX_META / "knowledge" / "product-inference.md", "knowledge/product-inference.md"),
        (CODEX_META / "knowledge" / "orchestrator-template.md", "knowledge/orchestrator-template.md"),
        (CODEX_META / "knowledge", "knowledge"),
        (CODEX_META / "scripts", "scripts"),
        (CODEX_META / "tests", "tests"),
        (CODEX_META / "mcp-ai-gateway", "mcp-ai-gateway"),
        (ORCH / "check_product_summary.py", "shared/scripts/orchestrator/check_product_summary.py"),
    ]
    for path, label in required_paths:
        check_exists(path, label, errors)

    # Non-empty shared asset trees.
    for rel in ["knowledge", "scripts", "tests"]:
        target = CODEX_META / rel
        if target.exists():
            file_count = sum(1 for p in target.rglob("*") if p.is_file())
            if file_count == 0:
                errors.append(f"empty tree: {rel}")

    # Canonical contract checks.
    skill_text = read_text(CODEX_META / "SKILL.md") if (CODEX_META / "SKILL.md").exists() else ""
    agents_text = read_text(CODEX_META / "AGENTS.md") if (CODEX_META / "AGENTS.md").exists() else ""
    playbook_text = read_text(CODEX_META / "execution-playbook.md") if (CODEX_META / "execution-playbook.md").exists() else ""
    bootstrap_text = read_text(CODEX_META / "skills" / "bootstrap.md") if (CODEX_META / "skills" / "bootstrap.md").exists() else ""
    run_template_text = read_text(CODEX_META / "knowledge" / "orchestrator-template.md") if (CODEX_META / "knowledge" / "orchestrator-template.md").exists() else ""
    high_risk_text = read_text(CODEX_META / "knowledge" / "high-risk-specialization.md") if (CODEX_META / "knowledge" / "high-risk-specialization.md").exists() else ""
    im_text = read_text(CODEX_META / "knowledge" / "im-specialization.md") if (CODEX_META / "knowledge" / "im-specialization.md").exists() else ""
    product_inference_text = read_text(CODEX_META / "knowledge" / "product-inference.md") if (CODEX_META / "knowledge" / "product-inference.md").exists() else ""

    for name, text in {
        "SKILL.md": skill_text,
        "AGENTS.md": agents_text,
        "execution-playbook.md": playbook_text,
        "skills/bootstrap.md": bootstrap_text,
        "knowledge/orchestrator-template.md": run_template_text,
    }.items():
        if "workflow.json" not in text:
            errors.append(f"{name} does not mention workflow.json")

    if ".codex/commands/run.md" not in skill_text + agents_text + playbook_text + bootstrap_text + run_template_text:
        errors.append("generated Codex run path .codex/commands/run.md is not fully documented")

    if "${CLAUDE_PLUGIN_ROOT}" in skill_text + agents_text + playbook_text + bootstrap_text + run_template_text:
        errors.append("Codex-local files still reference ${CLAUDE_PLUGIN_ROOT}")

    if ".claude/commands/run.md" in run_template_text:
        errors.append("Codex orchestrator template still references .claude/commands/run.md")

    # High-risk specialization hook checks.
    if "high-risk-specialization.md" not in skill_text + playbook_text + bootstrap_text:
        errors.append("high-risk specialization hook is not wired into Codex bootstrap documents")

    if "im-specialization.md" not in skill_text + playbook_text + bootstrap_text + high_risk_text:
        errors.append("IM specialization guidance is not wired into Codex specialization flow")

    if "research" not in high_risk_text.lower():
        errors.append("high-risk specialization guidance does not encode research-first behavior")

    if "mandatory responsibility" not in im_text.lower():
        errors.append("IM specialization guidance does not define a mandatory responsibility floor")

    if "product-summary.json" not in skill_text + agents_text + playbook_text + bootstrap_text + product_inference_text:
        errors.append("product inference contract is not fully documented")

    if "evidence" not in product_inference_text.lower():
        errors.append("product inference guidance does not require evidence-backed output")

    # Validate .mcp.json shape.
    mcp_path = CODEX_META / ".mcp.json"
    if mcp_path.exists():
        try:
            mcp = json.loads(read_text(mcp_path))
            servers = mcp.get("mcpServers", {})
            gateway = servers.get("ai-gateway")
            if not gateway:
                errors.append(".mcp.json missing mcpServers.ai-gateway")
            else:
                if gateway.get("command") != "node":
                    errors.append(".mcp.json ai-gateway command must be 'node'")
                if "./mcp-ai-gateway/dist/index.js" not in gateway.get("args", []):
                    errors.append(".mcp.json ai-gateway args missing ./mcp-ai-gateway/dist/index.js")
        except Exception as exc:
            errors.append(f".mcp.json parse failure: {exc}")

    # Backward compatibility note is acceptable, but primary contract drift is not.
    if "state-machine.json" in skill_text:
        warnings.append("SKILL.md still mentions state-machine.json")

    result = {"passed": not errors, "errors": errors, "warnings": warnings}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
