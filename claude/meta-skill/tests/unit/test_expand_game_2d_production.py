import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from expand_game_2d_production import expand_game_2d_production
from validate_bootstrap import (
    GAME_2D_PRODUCTION_REQUIRED_NODES,
    validate_game_2d_production_flow,
    validate_node_spec,
    validate_node_spec_contracts,
    validate_node_spec_coverage,
    validate_workflow,
)


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _minimal_project(tmp_path):
    workflow = {
        "nodes": [
            {
                "node_id": "game-frontend-playable-client-assembly",
                "goal": "assemble frontend",
                "capability": "game-frontend",
                "human_gate": False,
                "hard_blocked_by": [],
                "alignment_refs": [],
                "exit_artifacts": [
                    ".allforai/game-frontend/assembly/playable-client-assembly-report.json"
                ],
            }
        ],
        "transition_log": [],
    }
    _write(tmp_path, ".allforai/bootstrap/workflow.json", json.dumps(workflow))
    _write(
        tmp_path,
        ".allforai/bootstrap/node-specs/game-frontend-playable-client-assembly.md",
        """---
node_id: game-frontend-playable-client-assembly
goal: assemble frontend
capability: game-frontend
human_gate: false
hard_blocked_by: []
alignment_refs: []
exit_artifacts:
  - ".allforai/game-frontend/assembly/playable-client-assembly-report.json"
---
""",
    )
    _write(
        tmp_path,
        ".allforai/game-design/design/program-development-node-handoff.json",
        json.dumps({"game_2d_production": {"required": True}}),
    )
    _write(
        tmp_path,
        ".allforai/bootstrap/unattended-run-readiness-spec.json",
        json.dumps(
            {
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
        ),
    )


def test_expand_game_2d_production_generates_valid_nodes(tmp_path):
    _minimal_project(tmp_path)

    result = expand_game_2d_production(tmp_path)

    assert result["status"] == "expanded"
    assert result["generated_nodes"] == GAME_2D_PRODUCTION_REQUIRED_NODES
    assert result["readiness_spec_updated"] is True
    assert validate_workflow(str(tmp_path / ".allforai/bootstrap/workflow.json")) == []
    assert validate_node_spec_coverage(str(tmp_path / ".allforai/bootstrap")) == []
    assert validate_node_spec_contracts(str(tmp_path / ".allforai/bootstrap")) == []
    assert validate_game_2d_production_flow(str(tmp_path / ".allforai/bootstrap")) == []
    for node_id in GAME_2D_PRODUCTION_REQUIRED_NODES:
        spec_path = tmp_path / f".allforai/bootstrap/node-specs/{node_id}.md"
        assert validate_node_spec(str(spec_path)) == []
        spec_text = spec_path.read_text()
        assert f"node_id: {node_id}" in spec_text
        assert f"node: {node_id}" not in spec_text
    readiness_spec = json.loads(
        (tmp_path / ".allforai/bootstrap/unattended-run-readiness-spec.json").read_text()
    )
    assert readiness_spec["required_repair_loops"] == [
        {
            "scope": "game-2d-production",
            "qa_node_ids": [
                "game-2d-core-loop-playability-qa",
                "game-2d-asset-binding-visual-qa",
                "game-2d-session-completion-qa",
            ],
            "repair_node_id": "game-2d-code-repair-loop",
            "closure_node_ids": ["game-2d-production-closure-qa"],
            "max_attempts": 3,
        }
    ]


def test_expand_game_2d_production_skips_when_not_required(tmp_path):
    _write(tmp_path, ".allforai/bootstrap/workflow.json", json.dumps({"nodes": []}))

    result = expand_game_2d_production(tmp_path)

    assert result["status"] == "skipped"


def test_expand_game_2d_production_skips_when_required_artifacts_exist(tmp_path):
    _minimal_project(tmp_path)
    for artifact in [
        ".allforai/game-2d/assembly/playable-slice-assembly-report.json",
        ".allforai/game-2d/qa/core-loop-playability-qa-report.json",
        ".allforai/game-2d/qa/asset-binding-visual-qa-report.json",
        ".allforai/game-2d/qa/session-completion-qa-report.json",
        ".allforai/game-2d/repair/code-repair-loop-report.json",
        ".allforai/game-2d/qa/revalidation-report.json",
        ".allforai/game-2d/qa/2d-production-closure-report.json",
        ".allforai/game-2d/qa/2d-production-closure.html",
    ]:
        _write(tmp_path, artifact, "{}")
    _write(
        tmp_path,
        ".allforai/bootstrap/node-specs/game-2d-production-closure-qa.md",
        "---\nnode_id: game-2d-production-closure-qa\ncapability: game-2d-production\n---\n",
    )

    result = expand_game_2d_production(tmp_path)

    assert result["status"] == "skipped"
    assert result["reason"] == "game_2d_production_artifacts_already_exist"
    assert result["removed_orphan_specs"] == ["game-2d-production-closure-qa"]
    workflow = json.loads((tmp_path / ".allforai/bootstrap/workflow.json").read_text())
    node_ids = [node["node_id"] for node in workflow["nodes"]]
    assert "game-2d-production-closure-qa" not in node_ids
