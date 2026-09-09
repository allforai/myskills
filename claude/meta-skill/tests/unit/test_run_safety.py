import importlib.util
import json
from pathlib import Path
import subprocess
import sys

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/orchestrator/run_safety.py"
SPEC = importlib.util.spec_from_file_location("tested_run_safety", SCRIPT)
safety = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(safety)


def project(tmp_path):
    base = tmp_path / ".allforai/bootstrap"
    base.mkdir(parents=True)
    (base / "workflow.json").write_text(json.dumps({"nodes": [
        {"node_id": "a", "exit_artifacts": ["a.json"]},
        {"node_id": "b", "exit_artifacts": ["b.json"]}]}))
    return base


def test_quarantine_accumulates_without_accepting_or_deleting(tmp_path):
    base = project(tmp_path)
    artifact = tmp_path / "a.json"
    artifact.write_text('{"status":"passed"}')
    before = (base / "workflow.json").read_bytes()
    assert safety.quarantine(tmp_path, ["a"], "unsafe write")["status"] == "quarantined"
    result = safety.quarantine(tmp_path, ["b"], "second finding")
    assert result["node_ids"] == ["a", "b"]
    assert (base / "workflow.json").read_bytes() == before
    assert artifact.read_text() == '{"status":"passed"}'
    assert len(json.loads((tmp_path / safety.MARKER).read_text())["events"]) == 2


def test_unknown_node_is_not_silently_ignored(tmp_path):
    project(tmp_path)
    assert safety.quarantine(tmp_path, ["unknown"], "unsafe")["status"] == "blocked"
    assert not (tmp_path / safety.MARKER).exists()


def test_unreadable_existing_marker_is_preserved(tmp_path):
    project(tmp_path)
    marker = tmp_path / safety.MARKER
    marker.write_bytes(b"\xff")
    assert safety.quarantine(tmp_path, ["a"], "unsafe")["status"] == "blocked"
    assert marker.read_bytes() == b"\xff"


def test_held_lock_blocks_instead_of_losing_another_writer(tmp_path):
    base = project(tmp_path)
    lock = base / "safety-quarantine.lock"
    lock.mkdir()
    assert safety.quarantine(tmp_path, ["a"], "unsafe")["status"] == "blocked"
    assert lock.is_dir()


def test_public_cli_reports_durable_quarantine(tmp_path):
    project(tmp_path)
    result = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path),
                             "--nodes-json", '["a"]', "--reason", "unsafe"],
                            text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "quarantined"
    assert json.loads((tmp_path / safety.MARKER).read_text())["node_ids"] == ["a"]


def test_failed_publication_leaves_a_persistent_admission_fence(tmp_path, monkeypatch):
    base = project(tmp_path)
    def unavailable(*args):
        raise OSError("publication interrupted")
    monkeypatch.setattr(safety.os, "replace", unavailable)
    assert safety.quarantine(tmp_path, ["a"], "unsafe")["status"] == "blocked"
    assert (base / "safety-quarantine.lock").is_dir()
    assert not (tmp_path / safety.MARKER).exists()
