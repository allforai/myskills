"""Exporter fidelity only; no actor behavior is tested here."""
from pathlib import Path
import json
import subprocess
import sys

PIN = "ed430dfcebed485b913b54d7785f02cc86998303"


def test_export_requires_an_explicit_candidate_and_records_its_exact_content(tmp_path):
    cli = Path(__file__).with_name("prepare_packets.py")
    destination = tmp_path / "packets"
    missing = subprocess.run([sys.executable, str(cli), str(destination)],
                             capture_output=True, text=True)
    assert missing.returncode == 2
    assert not destination.exists(), "never export the obsolete implicit candidate"
    exported = subprocess.run([sys.executable, str(cli), str(destination), "--candidate", PIN],
                              capture_output=True, text=True)
    assert exported.returncode == 0, (exported.stdout, exported.stderr)
    manifest = json.loads((destination / "candidate-manifest.json").read_text())
    assert manifest["source_commit"] == PIN
    assert manifest["production_commit"] == PIN
    relative = "claude/meta-skill/scripts/orchestrator/product_intent.py"
    expected = subprocess.check_output(["git", "show", f"{PIN}:{relative}"], cwd=cli.resolve().parents[5])
    assert (destination / "candidate" / relative).read_bytes() == expected
    assert json.loads(exported.stdout)["executed"] == 0


def test_exported_user_invocation_hook_retains_executable_mode(tmp_path):
    cli = Path(__file__).with_name("prepare_packets.py")
    destination = tmp_path / "packets"
    result = subprocess.run([sys.executable, str(cli), str(destination), "--candidate", PIN],
                            capture_output=True, text=True)
    assert result.returncode == 0, (result.stdout, result.stderr)
    hook = destination / "candidate/claude/meta-skill/hooks/user-only-skills.sh"
    # The pinned source Git tree records this public hook as mode 100755.
    assert hook.stat().st_mode & 0o777 == 0o755


def test_export_manifest_records_git_modes_and_symlink_targets(tmp_path):
    cli = Path(__file__).with_name("prepare_packets.py")
    destination = tmp_path / "packets"
    result = subprocess.run([sys.executable, str(cli), str(destination), "--candidate", PIN],
                            capture_output=True, text=True)
    assert result.returncode == 0, (result.stdout, result.stderr)
    manifest = json.loads((destination / "candidate-manifest.json").read_text())
    assert manifest["git_modes"]["claude/meta-skill/hooks/user-only-skills.sh"] == "100755"
    assert manifest["git_modes"]["codex/meta-skill/scripts"] == "120000"
    assert manifest["symlinks"]["codex/meta-skill/scripts"] == "../../claude/meta-skill/scripts"
