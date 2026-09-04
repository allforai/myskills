#!/usr/bin/env python3
"""Static parity checks for codex/meta-skill.

This script verifies the Codex adapter surface exists and that its primary
contracts are aligned with the repository's current meta-skill conventions.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CODEX_META = ROOT / "codex" / "meta-skill"
CLAUDE_META = ROOT / "claude" / "meta-skill"
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
        (CODEX_META / "agents" / "openai.yaml", "agents/openai.yaml"),
        (CODEX_META / ".mcp.json", ".mcp.json"),
        (CODEX_META / "install.sh", "install.sh"),
        (CODEX_META / "commands" / "bootstrap.md", "commands/bootstrap.md"),
        (CODEX_META / "commands" / "setup.md", "commands/setup.md"),
        (CODEX_META / "commands" / "journal.md", "commands/journal.md"),
        (CODEX_META / "commands" / "journal-merge.md", "commands/journal-merge.md"),
        (CODEX_META / "skills" / "bootstrap.md", "skills/bootstrap.md"),
        (CODEX_META / "knowledge" / "high-risk-specialization.md", "knowledge/high-risk-specialization.md"),
        (CODEX_META / "knowledge" / "im-specialization.md", "knowledge/im-specialization.md"),
        (CODEX_META / "knowledge" / "replication-specialization.md", "knowledge/replication-specialization.md"),
        (CODEX_META / "knowledge" / "product-inference.md", "knowledge/product-inference.md"),
        (CODEX_META / "knowledge" / "flow-template.py", "knowledge/flow-template.py"),
        (CODEX_META / "knowledge" / "orchestrator-template.md", "knowledge/orchestrator-template.md"),
        (CODEX_META / "knowledge", "knowledge"),
        (CODEX_META / "scripts", "scripts"),
        (CODEX_META / "tests", "tests"),
        (CODEX_META / "mcp-ai-gateway", "mcp-ai-gateway"),
        (ORCH / "check_product_summary.py", "shared/scripts/orchestrator/check_product_summary.py"),
        (ORCH / "check_structured_node_spec.py", "shared/scripts/orchestrator/check_structured_node_spec.py"),
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
    invocation_policy_text = read_text(CODEX_META / "agents" / "openai.yaml") if (CODEX_META / "agents" / "openai.yaml").exists() else ""
    agents_text = read_text(CODEX_META / "AGENTS.md") if (CODEX_META / "AGENTS.md").exists() else ""
    playbook_text = read_text(CODEX_META / "execution-playbook.md") if (CODEX_META / "execution-playbook.md").exists() else ""
    bootstrap_text = read_text(CODEX_META / "skills" / "bootstrap.md") if (CODEX_META / "skills" / "bootstrap.md").exists() else ""
    run_template_text = read_text(CODEX_META / "knowledge" / "orchestrator-template.md") if (CODEX_META / "knowledge" / "orchestrator-template.md").exists() else ""
    high_risk_text = read_text(CODEX_META / "knowledge" / "high-risk-specialization.md") if (CODEX_META / "knowledge" / "high-risk-specialization.md").exists() else ""
    im_text = read_text(CODEX_META / "knowledge" / "im-specialization.md") if (CODEX_META / "knowledge" / "im-specialization.md").exists() else ""
    replication_text = read_text(CODEX_META / "knowledge" / "replication-specialization.md") if (CODEX_META / "knowledge" / "replication-specialization.md").exists() else ""
    product_inference_text = read_text(CODEX_META / "knowledge" / "product-inference.md") if (CODEX_META / "knowledge" / "product-inference.md").exists() else ""
    flow_template_text = read_text(CODEX_META / "knowledge" / "flow-template.py") if (CODEX_META / "knowledge" / "flow-template.py").exists() else ""

    # Release and invocation parity.
    claude_bootstrap = CLAUDE_META / "skills" / "bootstrap.md"
    claude_bootstrap_text = read_text(claude_bootstrap) if claude_bootstrap.exists() else ""
    claude_version = re.search(r'^\s*version:\s*["\']?([^"\'\n]+)', claude_bootstrap_text, re.MULTILINE)
    codex_version = re.search(r'^\s*version:\s*["\']?([^"\'\n]+)', skill_text, re.MULTILINE)
    if not claude_version or not codex_version:
        errors.append("could not determine Claude/Codex meta-skill versions")
    elif not codex_version.group(1).startswith(f"{claude_version.group(1)}-codex."):
        errors.append(
            f"Codex meta-skill version {codex_version.group(1)!r} does not track "
            f"Claude meta-skill version {claude_version.group(1)!r}"
        )

    if "allow_implicit_invocation: false" not in invocation_policy_text:
        errors.append("agents/openai.yaml does not disable implicit invocation")
    if "User-invoked only" not in skill_text:
        errors.append("SKILL.md does not state the explicit invocation boundary")

    disclosed_protocols = [
        "engine-detection.md",
        "suppress-rules.md",
        "bootstrap-planning.md",
        "bootstrap-art-pipeline.md",
        "node-spec-template.md",
        "bootstrap-audits.md",
    ]
    for name in disclosed_protocols:
        check_exists(CLAUDE_META / "knowledge" / name, f"canonical knowledge/{name}", errors)

    if "./canonical/" not in bootstrap_text or "../../claude/meta-skill/" not in bootstrap_text:
        errors.append("Codex bootstrap adapter does not define source and installed canonical roots")

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

    if "replication-specialization.md" not in skill_text + agents_text + playbook_text + bootstrap_text + high_risk_text:
        errors.append("replication specialization guidance is not wired into Codex specialization flow")

    if "research" not in high_risk_text.lower():
        errors.append("high-risk specialization guidance does not encode research-first behavior")

    if "mandatory responsibility" not in im_text.lower():
        errors.append("IM specialization guidance does not define a mandatory responsibility floor")
    if "implementation-oriented" not in replication_text.lower():
        errors.append("replication specialization guidance does not steer bootstrap toward implementation-oriented parity nodes")
    if "planning / audit" not in replication_text.lower():
        errors.append("replication specialization guidance does not guard against planning-only workflows")

    if "product-summary.json" not in skill_text + agents_text + playbook_text + bootstrap_text + product_inference_text:
        errors.append("product inference contract is not fully documented")

    if "evidence" not in product_inference_text.lower():
        errors.append("product inference guidance does not require evidence-backed output")

    if ".allforai/codex/flow.py" not in skill_text + agents_text + playbook_text + bootstrap_text + flow_template_text:
        errors.append("Codex non-stop flow driver contract is not fully documented")

    if "--dangerously-bypass-approvals-and-sandbox" not in flow_template_text:
        errors.append("flow template does not use Codex highest-permission execution")
    if "MAX_CONSECUTIVE_FAILURES_PER_NODE = 3" not in flow_template_text:
        errors.append("flow template does not enforce a repeated-failure threshold")
    if "MAX_STAGNANT_ITERATIONS = 5" not in flow_template_text:
        errors.append("flow template does not enforce a stagnation threshold")
    if "diagnosis_history" not in flow_template_text:
        errors.append("flow template does not record diagnosis_history")
    if "diagnosis.md" not in flow_template_text:
        errors.append("flow template does not use the diagnosis protocol after repeated failures")
    if "validate_unattended_readiness.py" not in run_template_text + flow_template_text:
        errors.append("Codex run contract does not wire unattended readiness preflight")
    if "check_artifacts.py" not in run_template_text + flow_template_text:
        errors.append("Codex run contract does not wire check_artifacts.py")

    install_text = read_text(CODEX_META / "install.sh") if (CODEX_META / "install.sh").exists() else ""
    if 'copy_dir "$CANONICAL_SOURCE/skills" "$INSTALL_DIR/canonical/skills"' not in install_text:
        errors.append("install.sh does not bundle canonical skills")
    if 'copy_dir "$CANONICAL_SOURCE/knowledge" "$INSTALL_DIR/canonical/knowledge"' not in install_text:
        errors.append("install.sh does not bundle canonical knowledge")
    if (
        "~/.codex/skills/meta-skill" not in install_text
        and ".codex/skills/meta-skill" not in install_text
        and "$HOME/.codex/skills/meta-skill" not in install_text
        and '${CODEX_HOME:-$HOME/.codex}/skills/meta-skill' not in install_text
    ):
        errors.append("install.sh does not install into the local Codex skills directory")
    if ".install-source" not in install_text:
        errors.append("install.sh does not record installation source metadata")
    if ".allforai/codex/flow.py" not in install_text:
        errors.append("install.sh usage text does not mention the Codex non-stop driver")

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
