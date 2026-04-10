#!/usr/bin/env python3
"""Behavior-level smoke check for Codex generated run template.

This does not execute a real bootstrap engine. Instead, it materializes the
Codex orchestrator template into a temporary target project and validates that
the generated run entry uses the expected Codex-local contract.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = ROOT / "codex" / "meta-skill" / "knowledge" / "orchestrator-template.md"
FLOW_TEMPLATE_PATH = ROOT / "codex" / "meta-skill" / "knowledge" / "flow-template.py"


def extract_template(text: str) -> str:
    match = re.search(r"~~~markdown\n(.*?)\n~~~", text, re.DOTALL)
    if not match:
        raise ValueError("Could not extract Codex run template fenced block")
    return match.group(1)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    raw = TEMPLATE_PATH.read_text(encoding="utf-8")
    rendered = extract_template(raw)
    flow_template = FLOW_TEMPLATE_PATH.read_text(encoding="utf-8")

    tmpdir = Path(tempfile.mkdtemp(prefix="codex-run-smoke-"))
    try:
        run_path = tmpdir / ".codex" / "commands" / "run.md"
        flow_path = tmpdir / ".allforai" / "codex" / "flow.py"
        run_path.parent.mkdir(parents=True, exist_ok=True)
        flow_path.parent.mkdir(parents=True, exist_ok=True)
        run_path.write_text(rendered, encoding="utf-8")
        flow_path.write_text(flow_template, encoding="utf-8")

        text = run_path.read_text(encoding="utf-8")
        flow_text = flow_path.read_text(encoding="utf-8")

        if "workflow.json" not in text:
            errors.append("generated run does not reference workflow.json")
        if ".allforai/bootstrap/scripts/check_artifacts.py" not in text:
            errors.append("generated run does not reference project-local check_artifacts.py")
        if ".allforai/bootstrap/node-specs/" not in text:
            errors.append("generated run does not reference project-local node-specs")
        if ".allforai/codex/flow.py" not in text:
            errors.append("generated run does not expose the Codex non-stop driver")
        if ".claude/commands/run.md" in text:
            errors.append("generated run still references .claude/commands/run.md")
        if "${CLAUDE_PLUGIN_ROOT}" in text:
            errors.append("generated run still references ${CLAUDE_PLUGIN_ROOT}")
        if "--dangerously-bypass-approvals-and-sandbox" not in flow_text:
            errors.append("flow template does not use Codex highest-permission execution")
        if ".allforai/bootstrap/workflow.json" not in flow_text:
            errors.append("flow template does not reference workflow.json")
        if "MAX_CONSECUTIVE_FAILURES_PER_NODE = 3" not in flow_text:
            errors.append("flow template does not enforce repeated-failure supervision")
        if "MAX_STAGNANT_ITERATIONS = 5" not in flow_text:
            errors.append("flow template does not enforce stagnation supervision")
        if "diagnosis_history" not in flow_text:
            errors.append("flow template does not record diagnosis history")
        if ".allforai/bootstrap/protocols/diagnosis.md" not in flow_text:
            errors.append("flow template does not read the diagnosis protocol")
        if ".allforai/codex/flow.py" not in str(flow_path):
            errors.append("flow template was not materialized to the Codex-only path")
        if ".codex/commands/run.md" in text:
            warnings.append("generated run mentions its own target path; acceptable but not required")

        result = {
            "passed": not errors,
            "errors": errors,
            "warnings": warnings,
            "generated_run": str(run_path),
            "generated_flow": str(flow_path),
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if not errors else 1
    finally:
        shutil.rmtree(tmpdir)


if __name__ == "__main__":
    sys.exit(main())
