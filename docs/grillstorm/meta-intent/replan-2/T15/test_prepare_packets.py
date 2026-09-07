"""Exporter fidelity only; no actor behavior is tested here."""
from pathlib import Path
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
