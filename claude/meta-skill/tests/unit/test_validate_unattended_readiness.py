import json
import os
import sys

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
