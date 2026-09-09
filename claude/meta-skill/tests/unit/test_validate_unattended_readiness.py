import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from validate_unattended_readiness import validate_unattended_readiness


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _minimal_project(tmp_path, *, gate_status="approved", node_spec="non interactive work"):
    workflow = {
        "nodes": [
            {
                "node_id": "design",
                "goal": "design",
                "capability": "game-design",
                "human_gate": True,
                "approval_record_path": ".allforai/game-design/approval-records.json",
                "exit_artifacts": [{"path": ".allforai/game-design/design.json"}],
            }
        ]
    }
    _write(tmp_path, ".allforai/bootstrap/workflow.json", json.dumps(workflow))
    _write(tmp_path, ".allforai/bootstrap/node-specs/design.md", node_spec)
    _write(tmp_path, ".allforai/bootstrap/scripts/validate_bootstrap.py", "")
    _write(tmp_path, ".allforai/bootstrap/scripts/check_artifacts.py", "")
    _write(tmp_path, ".allforai/bootstrap/scripts/validate_unattended_readiness.py", "")
    readiness_spec = {
        "version": 1,
        "run_mode": "unattended",
        "forbid_mid_run_user_prompts": True,
        "forbid_hidden_fallback_completion": True,
        "max_repair_attempts": 3,
        "required_capabilities": [],
        "required_repair_loops": [],
        "long_task_policy": {
            "file_based_handoff": True,
            "polling": True,
            "timeout": True,
            "retry": True,
            "resume": True,
        },
    }
    _write(
        tmp_path,
        ".allforai/bootstrap/unattended-run-readiness-spec.json",
        json.dumps(readiness_spec),
    )
    approval = {"records": [{"node_id": "design", "gate_status": gate_status}]}
    _write(tmp_path, ".allforai/game-design/approval-records.json", json.dumps(approval))


def test_unattended_readiness_passes_approved_noninteractive_project(tmp_path):
    _minimal_project(tmp_path)

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "ready"
    assert report["blockers"] == []


def test_unattended_readiness_blocks_pending_human_gate(tmp_path):
    _minimal_project(tmp_path, gate_status="in-review")

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert any(item["code"] == "pending_human_gate" for item in report["blockers"])


def test_unattended_readiness_blocks_interactive_node_spec(tmp_path):
    _minimal_project(tmp_path, node_spec="Use AskUserQuestion before continuing")

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert any(item["code"] == "node_spec_allows_user_prompt" for item in report["blockers"])


def test_unattended_readiness_blocks_unexpanded_game_2d_handoff(tmp_path):
    _minimal_project(tmp_path, node_spec="game_2d_production handoff exists")

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert any(
        item["code"] == "unexpanded_game_2d_production_handoff"
        for item in report["blockers"]
    )


def test_unattended_readiness_blocks_missing_spec(tmp_path):
    _minimal_project(tmp_path)
    (tmp_path / ".allforai/bootstrap/unattended-run-readiness-spec.json").unlink()

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert any(item["code"] == "missing_unattended_readiness_spec" for item in report["blockers"])


def test_unattended_readiness_blocks_broken_repair_loop_contract(tmp_path):
    _minimal_project(tmp_path)
    spec = {
        "version": 1,
        "run_mode": "unattended",
        "forbid_mid_run_user_prompts": True,
        "forbid_hidden_fallback_completion": True,
        "max_repair_attempts": 3,
        "required_capabilities": [],
        "required_repair_loops": [
            {
                "scope": "runtime-qa",
                "qa_node_ids": ["runtime-qa"],
                "repair_node_id": "runtime-repair",
                "closure_node_ids": ["closure-qa"],
                "max_attempts": 3,
            }
        ],
        "long_task_policy": {
            "file_based_handoff": True,
            "polling": True,
            "timeout": True,
            "retry": True,
            "resume": True,
        },
    }
    _write(tmp_path, ".allforai/bootstrap/unattended-run-readiness-spec.json", json.dumps(spec))

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert any(item["code"] == "missing_repair_loop_node" for item in report["blockers"])


def _project_with_repair_loop(tmp_path, loop):
    """Minimal project whose one node is both the QA node and its own repair target."""
    workflow = {
        "nodes": [
            {"node_id": "runtime-qa", "goal": "qa", "capability": "qa",
             "exit_artifacts": [{"path": ".allforai/quality-checks/qa.json"}]},
            {"node_id": "runtime-repair", "goal": "repair", "capability": "qa",
             "hard_blocked_by": ["runtime-qa"],
             "exit_artifacts": [{"path": ".allforai/quality-checks/repair.json"}]},
            {"node_id": "closure-qa", "goal": "closure", "capability": "qa",
             "hard_blocked_by": ["runtime-repair"],
             "exit_artifacts": [{"path": ".allforai/quality-checks/closure.json"}]},
        ]
    }
    _minimal_project(tmp_path)
    _write(tmp_path, ".allforai/bootstrap/workflow.json", json.dumps(workflow))
    for node_id in ("runtime-qa", "runtime-repair", "closure-qa"):
        _write(tmp_path, f".allforai/bootstrap/node-specs/{node_id}.md", "non interactive work")
    spec = json.loads((tmp_path / ".allforai/bootstrap/unattended-run-readiness-spec.json").read_text())
    spec["required_repair_loops"] = [loop]
    _write(tmp_path, ".allforai/bootstrap/unattended-run-readiness-spec.json", json.dumps(spec))


def _repair_loop(**overrides):
    loop = {
        "scope": "runtime-qa",
        "qa_node_ids": ["runtime-qa"],
        "repair_node_id": "runtime-repair",
        "closure_node_ids": ["closure-qa"],
        "max_attempts": 3,
    }
    loop.update(overrides)
    return loop


def test_unattended_readiness_accepts_a_bounded_repair_loop(tmp_path):
    _project_with_repair_loop(tmp_path, _repair_loop())

    report = validate_unattended_readiness(tmp_path)

    assert report["blockers"] == []


@pytest.mark.parametrize("max_attempts", [0, -1, "3", None, True, 3.0])
def test_unattended_readiness_blocks_an_unbounded_repair_budget(tmp_path, max_attempts):
    # The orchestrators refuse to route a loop whose declared budget is unusable;
    # readiness must surface that before /run rather than after the first QA failure.
    _project_with_repair_loop(tmp_path, _repair_loop(max_attempts=max_attempts))

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert any(item["code"] == "invalid_repair_loop_budget" for item in report["blockers"])


def test_unattended_readiness_warns_when_a_repair_budget_is_omitted(tmp_path):
    loop = _repair_loop()
    del loop["max_attempts"]
    _project_with_repair_loop(tmp_path, loop)

    report = validate_unattended_readiness(tmp_path)

    assert report["blockers"] == []
    assert any(w["code"] == "repair_loop_budget_defaulted" for w in report["warnings"])


def test_missing_codex_cli_is_a_warning_not_a_blocker(tmp_path, monkeypatch):
    # ADR-0003: the cross-platform CLI is reviewer two's preferred backend; when absent, reviewer two
    # runs as a second fresh-context sub-agent. Readiness records the warning and stays ready.
    import validate_unattended_readiness as m
    monkeypatch.setattr(m.shutil, "which", lambda name: None)
    _minimal_project(tmp_path, node_spec="capture screenshot then run visual-acceptance batches")
    report = validate_unattended_readiness(tmp_path)
    codes = {b["code"] for b in report["blockers"]}
    assert "missing_codex_cli" not in codes
    assert report["status"] == "ready"
    assert any(w.get("code") == "missing_cross_platform_cli" for w in report["warnings"])
    assert any(f.get("reviewer_two_backend") == "session-subagent" for f in report["external_tool_findings"])
