import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent / "install_official_skills.py"


def test_status_reports_host_and_required_names():
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "status"],
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["host"] in {"claude", "pi", "codex", "generic"}
    assert "grilling" in payload["install_command"][-1] or payload["install_command"][2] == "install"
    assert isinstance(payload["missing_required"], list)


def test_dry_run_install_prints_command_without_failing():
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "install", "--host", "pi", "--dry-run"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["host"] == "pi"
    assert payload["command"][:5] == ["npx", "--yes", "skills@latest", "add", "mattpocock/skills"]
    assert "-g" in payload["command"]
    assert "-y" in payload["command"]
    assert "implement" not in payload["command"][-1]


def test_claude_dry_run_uses_plugin_install():
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "install", "--host", "claude", "--dry-run"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["command"][:4] == ["claude", "plugin", "install", "mattpocock-skills"]
