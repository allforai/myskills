"""Synthetic admission checks, never real-host scenario evidence."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


CLI = Path(__file__).with_name("admit_evidence.py")


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def test_receipt_without_host_session_or_raw_dialogue_is_unverified(tmp_path):
    root = tmp_path / "candidate"
    root.mkdir()
    manifest = tmp_path / "manifest.json"
    receipt = tmp_path / "receipt.json"
    write(manifest, {"sha256": {}, "symlinks": {}})
    write(receipt, {"host": "codex", "source_root": str(root)})
    result = subprocess.run([sys.executable, str(CLI), str(manifest), str(root), str(receipt)],
                            capture_output=True, text=True)
    assert result.returncode == 1, (result.stdout, result.stderr)
    report = json.loads(result.stdout)
    assert report["status"] == "unverified"
    assert "missing-session-identity" in report["reasons"]
    assert "missing-raw-dialogue" in report["reasons"]
    assert report["semantic_verdict"] == "not-evaluated"


def test_changed_loaded_candidate_invalidates_old_receipt(tmp_path):
    root, manifest, receipt, record = synthetic_receipt(tmp_path)
    Path(record["loaded_files"][0]["path"]).write_text("A new producer candidate, never run.\n")
    rejected = subprocess.run([sys.executable, str(CLI), str(manifest), str(root), str(receipt)],
                              capture_output=True, text=True)
    assert rejected.returncode == 1, rejected.stdout
    assert "changed-candidate" in json.loads(rejected.stdout)["reasons"]


def test_changed_raw_dialogue_cannot_be_admitted(tmp_path):
    root, manifest, receipt, record = synthetic_receipt(tmp_path)
    Path(record["raw_dialogue"]["path"]).write_text("Replaced transcript.\n")
    rejected = subprocess.run([sys.executable, str(CLI), str(manifest), str(root), str(receipt)],
                              capture_output=True, text=True)
    assert rejected.returncode == 1, rejected.stdout
    assert "raw-dialogue-mismatch" in json.loads(rejected.stdout)["reasons"]


def test_partial_receipt_is_unverified_with_machine_readable_reason(tmp_path):
    root, manifest, receipt, record = synthetic_receipt(tmp_path)
    record["raw_dialogue"] = {"sha256": "no captured path"}
    write(receipt, record)
    rejected = subprocess.run([sys.executable, str(CLI), str(manifest), str(root), str(receipt)],
                              capture_output=True, text=True)
    assert rejected.returncode == 1
    assert not rejected.stderr
    assert json.loads(rejected.stdout)["status"] == "unverified"


def synthetic_receipt(tmp_path):
    root = tmp_path / "candidate"
    entry = "codex/meta-skill/SKILL.md"
    path = root / entry
    path.parent.mkdir(parents=True)
    path.write_text("Synthetic admission fixture; no host ran.\n")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    raw = tmp_path / "synthetic-dialogue.txt"
    raw.write_text("Synthetic unit-test text, NOT actual host evidence.\n")
    manifest = tmp_path / "manifest.json"
    receipt = tmp_path / "receipt.json"
    write(manifest, {"sha256": {entry: digest}, "symlinks": {}})
    record = {"host": "codex", "session_id": "synthetic-unit-session",
              "source_root": str(root), "loaded_files": [{"path": str(path), "sha256": digest}],
              "raw_dialogue": {"path": str(raw), "sha256": hashlib.sha256(raw.read_bytes()).hexdigest()}}
    write(receipt, record)
    return root, manifest, receipt, record


@pytest.mark.parametrize("fault", ["installed-root", "loaded-hash"])
def test_rejects_candidate_mismatch_then_admits_only_for_semantic_review(tmp_path, fault):
    root, manifest, receipt, record = synthetic_receipt(tmp_path)
    valid = json.loads(json.dumps(record))
    if fault == "installed-root":
        record["source_root"] = str(tmp_path / "old-installed-skill")
    else:
        record["loaded_files"][0]["sha256"] = "0" * 64
    write(receipt, record)
    command = [sys.executable, str(CLI), str(manifest), str(root), str(receipt)]
    rejected = subprocess.run(command, capture_output=True, text=True)
    assert rejected.returncode == 1, rejected.stdout
    assert "candidate-mismatch" in json.loads(rejected.stdout)["reasons"]
    write(receipt, valid)
    admitted = subprocess.run(command, capture_output=True, text=True)
    assert admitted.returncode == 0, admitted.stdout
    report = json.loads(admitted.stdout)
    assert report["status"] == "admissible-for-evaluation"
    assert report["semantic_verdict"] == "not-evaluated"
