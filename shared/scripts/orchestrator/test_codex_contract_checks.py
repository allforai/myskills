"""Exercise the public check commands on disposable, deliberately damaged bundles."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
PARITY = "check_codex_meta_skill_parity.py"
SMOKE = "smoke_codex_generated_run.py"


@pytest.fixture(scope="module")
def snapshot(tmp_path_factory):
    root = tmp_path_factory.mktemp("codex-check-source")
    for relative in ("claude/meta-skill", "codex/meta-skill", "shared"):
        shutil.copytree(
            ROOT / relative, root / relative, symlinks=True,
            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "node_modules", ".git"),
        )
    return root


def run_check(root, script):
    result = subprocess.run(
        [sys.executable, "-B", str(root / "shared/scripts/orchestrator" / script)],
        cwd=root, capture_output=True, text=True, timeout=30,
    )
    return result.returncode, json.loads(result.stdout)


@pytest.mark.parametrize("script", [PARITY, SMOKE])
def test_current_bundle_contract_passes(snapshot, script):
    code, report = run_check(snapshot, script)
    assert code == 0, report
    assert report["passed"] is True
    assert report["errors"] == []


@pytest.mark.parametrize("script", [PARITY, SMOKE])
@pytest.mark.parametrize("damage", ["bypass", "missing_policy", "unrestricted_policy"])
def test_execution_policy_regressions_are_rejected(snapshot, tmp_path, script, damage):
    root = tmp_path / "repo"
    shutil.copytree(snapshot, root, symlinks=True)
    path = root / "codex/meta-skill/knowledge/flow-template.py"
    text = path.read_text()
    if damage == "bypass":
        text = text.replace('"--sandbox", policy["sandbox"]',
                            '"--dangerously-bypass-approvals-and-sandbox"')
    elif damage == "missing_policy":
        text = text.replace('"--sandbox", policy["sandbox"]', '"--quiet"')
    else:
        text = text.replace('policy["sandbox"] not in {"read-only", "workspace-write"}',
                            'policy["sandbox"] not in {"read-only", "workspace-write", "danger-full-access"}')
    assert text != path.read_text(), "fixture mutation did not apply"
    path.write_text(text)
    code, report = run_check(root, script)
    assert code == 1, report
    assert report["passed"] is False
    assert any("sandbox" in error for error in report["errors"]), report


@pytest.mark.parametrize("damage,expected", [
    ("bootstrap", "versions"),
    ("canonical", "canonical knowledge"),
    ("bundle_location", "outside skill discovery"),
    ("metadata", "source metadata"),
    ("delegation", "delegate"),
])
def test_bundle_contract_regressions_are_rejected(snapshot, tmp_path, damage, expected):
    root = tmp_path / "repo"
    shutil.copytree(snapshot, root, symlinks=True)
    if damage == "bootstrap":
        (root / "claude/meta-skill/skills/bootstrap/SKILL.md").unlink()
    else:
        relative, before, after = {
            "canonical": ("install_bundle.py", "payload / 'canonical/knowledge'", "payload / 'wrong/knowledge'"),
            "bundle_location": ("install_bundle.py", "entry.parent.parent / 'skill-bundles/meta-skill'", "entry.parent / 'meta-skill-bundle'"),
            "metadata": ("install_bundle.py", ".install-source", ".untracked-origin"),
            "delegation": ("install.sh", 'exec python3 "$SCRIPT_DIR/install_bundle.py"', 'exit 0'),
        }[damage]
        path = root / "codex/meta-skill" / relative
        text = path.read_text()
        assert before in text, "fixture mutation did not apply"
        path.write_text(text.replace(before, after))
    code, report = run_check(root, PARITY)
    assert code == 1, report
    assert report["passed"] is False
    assert any(expected in error for error in report["errors"]), report
