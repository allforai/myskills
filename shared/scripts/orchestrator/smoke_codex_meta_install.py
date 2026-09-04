#!/usr/bin/env python3
"""Install the Codex meta-skill into an isolated snapshot and verify portability."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "codex" / "meta-skill"


def main() -> int:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="codex-meta-install-") as tmp:
        install = Path(tmp) / "meta-skill"
        env = os.environ.copy()
        env["MYSKILLS_CODEX_INSTALL_DIR"] = str(install)
        result = subprocess.run(
            ["bash", str(SOURCE / "install.sh")],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            errors.append(f"installer failed: {result.stderr or result.stdout}")

        required = [
            "SKILL.md",
            "agents/openai.yaml",
            "canonical/skills/bootstrap.md",
            "canonical/knowledge/engine-detection.md",
            "canonical/knowledge/suppress-rules.md",
            "canonical/knowledge/bootstrap-planning.md",
            "canonical/knowledge/bootstrap-art-pipeline.md",
            "canonical/knowledge/node-spec-template.md",
            "canonical/knowledge/bootstrap-audits.md",
            "knowledge/capabilities",
            "scripts/orchestrator/validate_bootstrap.py",
            "tests",
            ".install-source",
        ]
        for rel in required:
            if not (install / rel).exists():
                errors.append(f"installed snapshot missing {rel}")

        for rel in ["knowledge/capabilities", "scripts", "tests", "mcp-ai-gateway"]:
            path = install / rel
            if path.is_symlink():
                errors.append(f"installed snapshot retains source link {rel}")

        policy = install / "agents" / "openai.yaml"
        if policy.exists() and "allow_implicit_invocation: false" not in policy.read_text(encoding="utf-8"):
            errors.append("installed invocation policy allows implicit invocation")

    print(json.dumps({"passed": not errors, "errors": errors}, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
