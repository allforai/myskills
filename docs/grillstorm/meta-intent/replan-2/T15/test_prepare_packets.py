"""Exporter fidelity only; no actor behavior is tested here."""
from pathlib import Path
import json
import subprocess
import sys


def test_exported_user_invocation_hook_retains_executable_mode(tmp_path):
    cli = Path(__file__).with_name("prepare_packets.py")
    destination = tmp_path / "packets"
    result = subprocess.run([sys.executable, str(cli), str(destination)],
                            capture_output=True, text=True)
    assert result.returncode == 0, (result.stdout, result.stderr)
    hook = destination / "candidate/claude/meta-skill/hooks/user-only-skills.sh"
    # The pinned source Git tree records this public hook as mode 100755.
    assert hook.stat().st_mode & 0o777 == 0o755


def test_export_manifest_records_git_modes_and_symlink_targets(tmp_path):
    cli = Path(__file__).with_name("prepare_packets.py")
    destination = tmp_path / "packets"
    result = subprocess.run([sys.executable, str(cli), str(destination)],
                            capture_output=True, text=True)
    assert result.returncode == 0, (result.stdout, result.stderr)
    manifest = json.loads((destination / "candidate-manifest.json").read_text())
    assert manifest["git_modes"]["claude/meta-skill/hooks/user-only-skills.sh"] == "100755"
    assert manifest["git_modes"]["codex/meta-skill/scripts"] == "120000"
    assert manifest["symlinks"]["codex/meta-skill/scripts"] == "../../claude/meta-skill/scripts"
