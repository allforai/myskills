"""Mechanical gates (compile, spec-compliance, security, pipeline-closure) write ledger-shaped entries
with medium build or contract — the media a later /cross-exam admits as gates (#63, ADR-0008)."""
import json
import os
import subprocess
from pathlib import Path

import pytest

from .. import module_isolation

SCRIPTS = str(Path(module_isolation.ORCHESTRATOR).parent)
_capture, _check = module_isolation._isolation.load(SCRIPTS, "capture_evidence", "check_evidence")
write_entry, entries_reason = _capture.write_entry, _check.entries_reason


def _git(repo, *args):
    # A clean env and an explicit no-op hooksPath: this suite may itself be running inside this
    # repo's own pre-commit hook, which leaves GIT_DIR/GIT_WORK_TREE/hooksPath set in the
    # environment — without stripping them, a nested `git init` here would resolve back to the
    # outer repo and re-run its hooks against these throwaway trees (matches test_evidence_entries.py).
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x")
    return subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
                           *args], check=True, capture_output=True, text=True, env=env).stdout.strip()


@pytest.fixture
def gate_project(tmp_path, monkeypatch):
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.delenv(key, raising=False)
    _git(tmp_path, "init", "-q"); (tmp_path / "app.py").write_text("print(1)\n")
    _git(tmp_path, "add", "."); _git(tmp_path, "commit", "-qm", "init")
    return tmp_path


def _gate_draft(run, node, medium, q, output="ok\n", suffix=".log"):
    d = run / "evidence" / node / "q01"
    d.mkdir(parents=True, exist_ok=True)
    (d / ("capture" + suffix)).write_text(output)
    return {"q": q, "facet": "F1", "medium": medium, "verdict": "done",
            "evidence": {"dir": "evidence/%s/q01/" % node, "key_observation": "captured"}}


def test_compile_verify_writes_a_build_entry_cross_exam_can_admit(gate_project):
    run = gate_project / ".allforai/compile-verify"
    node = "compile-verify-web"
    draft = _gate_draft(run, node, "build", "npm run build 在真实树上过吗？", "vite v5 built in 1.2s\n")
    entry, reason = write_entry(run, draft, gate_project, node, "compile-verify")
    assert reason == "", reason
    assert entry["medium"] == "build" and "served_by" not in entry
    assert entry["author"] == {"pipeline": "meta-skill/run", "node_id": node, "capability": "compile-verify"}
    assert entries_reason(run, gate_project, node) == ""


def test_a_failed_build_is_a_gap_entry_never_omitted(gate_project):
    run = gate_project / ".allforai/compile-verify"
    node = "compile-verify-web"
    draft = {**_gate_draft(run, node, "build", "构建过吗？", "error TS2304\n"), "verdict": "gap"}
    entry, reason = write_entry(run, draft, gate_project, node, "compile-verify")
    assert reason == "" and entry["verdict"] == "gap"


def test_a_build_entry_without_captured_output_is_refused(gate_project):
    run = gate_project / ".allforai/compile-verify"
    node = "compile-verify-web"
    draft = _gate_draft(run, node, "build", "构建过吗？", suffix=".png")   # a picture is not a captured output
    _, reason = write_entry(run, draft, gate_project, node, "compile-verify")
    assert "机械门证据无输出文件" in reason


def test_a_stale_build_entry_is_refused_at_gate_time(gate_project):
    run = gate_project / ".allforai/compile-verify"
    node = "compile-verify-web"
    draft = _gate_draft(run, node, "build", "构建过吗？")
    assert write_entry(run, draft, gate_project, node, "compile-verify")[1] == ""
    (gate_project / "app.py").write_text("print(2)\n")
    assert "构建标识不匹配" in entries_reason(run, gate_project, node)


@pytest.mark.parametrize("capability, run_name, output", [
    ("spec-compliance-verify", "spec-compliance", '{"endpoints": {"declared": 20, "present": 20, "drifted": []}}\n'),
    ("security-verify", "security-verify", '{"decisions_checked": 6, "missing": []}\n'),
    ("pipeline-closure-verify", "pipeline-closure", '{"pipelines": [{"id": "checkout", "status": "complete"}]}\n'),
])
def test_contract_gates_write_contract_entries(gate_project, capability, run_name, output):
    run = gate_project / ".allforai" / run_name
    node = capability + "-1"
    draft = _gate_draft(run, node, "contract", capability + " 的比对在真实树上做了吗？", output, suffix=".json")
    entry, reason = write_entry(run, draft, gate_project, node, capability)
    assert reason == "", reason
    assert entry["medium"] == "contract" and "served_by" not in entry
    assert entry["author"]["capability"] == capability
    assert entries_reason(run, gate_project, node) == ""


def test_a_contract_entry_whose_diff_was_not_captured_is_refused(gate_project):
    run = gate_project / ".allforai/spec-compliance"
    node = "spec-compliance-verify-1"
    d = run / "evidence" / node / "q01"; d.mkdir(parents=True)
    (d / "diff.png").write_bytes(b"\x89PNG")
    draft = {"q": "比对做了吗？", "facet": "F1", "medium": "contract", "verdict": "done",
             "evidence": {"dir": "evidence/%s/q01/" % node, "key_observation": "x"}}
    _, reason = write_entry(run, draft, gate_project, node, "spec-compliance-verify")
    assert "机械门证据无输出文件" in reason
