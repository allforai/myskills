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
