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
        # install_bundle.py splits output into a thin entry dir (discovered by Codex) and a
        # separate, unscanned bundle dir (default entry.parent.parent / 'skill-bundles/meta-skill').
        # Pin the bundle inside this run's TemporaryDirectory too, or it leaks to $TMPDIR/skill-bundles.
        bundle = Path(tmp) / "skill-bundles" / "meta-skill"
        env = os.environ.copy()
        env["MYSKILLS_CODEX_INSTALL_DIR"] = str(install)
        env["MYSKILLS_CODEX_BUNDLE_DIR"] = str(bundle)
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

        # Entry dir: only what install_bundle.py's pending/ stages (SKILL.md, agents/, .install-source).
        entry_required = [
            "SKILL.md",
            "agents/openai.yaml",
            ".install-source",
        ]
        for rel in entry_required:
            if not (install / rel).exists():
                errors.append(f"installed entry missing {rel}")

        # Bundle dir: the full payload (canonical/, knowledge/, scripts/, tests/), per
        # codex/meta-skill/test_install.py's fixture layout.
        bundle_required = [
            "canonical/skills/bootstrap/SKILL.md",
            "canonical/knowledge/engine-detection.md",
            "canonical/knowledge/suppress-rules.md",
            "canonical/knowledge/bootstrap-planning.md",
            "canonical/knowledge/bootstrap-art-pipeline.md",
            "canonical/knowledge/node-spec-template.md",
            "canonical/knowledge/bootstrap-audits.md",
            "knowledge/capabilities",
            "scripts/orchestrator/validate_bootstrap.py",
            "tests",
        ]
        for rel in bundle_required:
            if not (bundle / rel).exists():
                errors.append(f"installed bundle missing {rel}")

        for rel in ["knowledge/capabilities", "scripts", "tests", "mcp-ai-gateway"]:
            path = bundle / rel
            if path.is_symlink():
                errors.append(f"installed bundle retains source link {rel}")

        policy = install / "agents" / "openai.yaml"
        if policy.exists() and "allow_implicit_invocation: false" not in policy.read_text(encoding="utf-8"):
            errors.append("installed invocation policy allows implicit invocation")

    print(json.dumps({"passed": not errors, "errors": errors}, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
