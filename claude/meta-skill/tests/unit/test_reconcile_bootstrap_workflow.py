import json
import os
import sys

from ..module_isolation import load

_reconcile = load("reconcile_bootstrap_workflow")
build_reconciliation_plan = _reconcile.build_reconciliation_plan
build_state_index = _reconcile.build_state_index


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_state_index_detects_orphan_specs_and_blocking_artifacts(tmp_path):
    workflow = {
        "goals": ["implement"],
        "nodes": [
            {
                "node_id": "qa",
                "goal": "verify quality",
                "capability": "test-verify",
                "hard_blocked_by": [],
                "alignment_refs": [],
                "exit_artifacts": [".allforai/qa/report.json"],
            }
        ],
        "transition_log": [{"node_id": "qa", "status": "completed"}],
    }
    _write(tmp_path, ".allforai/bootstrap/workflow.json", json.dumps(workflow))
    _write(tmp_path, ".allforai/bootstrap/node-specs/qa.md", "---\nnode_id: qa\n---\n")
    _write(tmp_path, ".allforai/bootstrap/node-specs/orphan.md", "---\nnode_id: orphan\n---\n")
    _write(
        tmp_path,
        ".allforai/qa/report.json",
        json.dumps({"status": "passed", "quality_gaps": [{"id": "bad_visual"}]}),
    )

    state = build_state_index(tmp_path)

    assert state["node_count"] == 1
    assert state["nodes"][0]["artifact_readiness"] == "blocked"
    assert state["nodes"][0]["artifacts"][0]["blockers"] == ["quality_gaps non-empty"]
    assert state["orphan_specs"][0]["node_id"] == "orphan"


def test_reconciliation_plan_marks_add_update_supersede_and_orphans(tmp_path):
    current = {
        "nodes": [
            {
                "node_id": "keep",
                "goal": "same",
                "capability": "impl",
                "exit_artifacts": [".allforai/keep.json"],
            },
            {
                "node_id": "change",
                "goal": "old",
                "capability": "impl",
                "exit_artifacts": [".allforai/change.json"],
            },
            {
                "node_id": "done-old",
                "goal": "remove me",
                "capability": "impl",
                "exit_artifacts": [".allforai/done-old.json"],
            },
        ]
    }
    candidate = {
        "nodes": [
            {
                "node_id": "keep",
                "goal": "same",
                "capability": "impl",
                "exit_artifacts": [".allforai/keep.json"],
            },
            {
                "node_id": "change",
                "goal": "new",
                "capability": "impl",
                "exit_artifacts": [".allforai/change.json"],
            },
            {
                "node_id": "new",
                "goal": "new node",
                "capability": "impl",
                "exit_artifacts": [".allforai/new.json"],
            },
        ]
    }
    _write(tmp_path, ".allforai/bootstrap/workflow.json", json.dumps(current))
    for node_id in ("keep", "change", "done-old", "orphan"):
        _write(tmp_path, f".allforai/bootstrap/node-specs/{node_id}.md", f"---\nnode_id: {node_id}\n---\n")
    _write(tmp_path, ".allforai/keep.json", "{}")
    _write(tmp_path, ".allforai/change.json", "{}")
    _write(tmp_path, ".allforai/done-old.json", "{}")
    candidate_path = _write(tmp_path, ".allforai/bootstrap/candidate-workflow.json", json.dumps(candidate))

    state = build_state_index(tmp_path)
    plan = build_reconciliation_plan(tmp_path, state, candidate_path)
    actions = {item["node_id"]: item["action"] for item in plan["items"]}

    assert actions["keep"] == "keep"
    assert actions["change"] == "update"
    assert actions["new"] == "add"
    assert actions["done-old"] == "supersede"
    assert actions["orphan"] == "remove"


def test_a_candidate_written_from_the_template_keeps_the_run_history(tmp_path, monkeypatch):
    # Re-bootstrap writes a candidate with the template's empty lists. Accepting it must not
    # wipe what the run recorded: --write carries the history into it, verbatim and first.
    history = {
        "transition_log": [{"node_id": "a", "status": "completed"},
                           {"node_id": "b", "status": "superseded"}],
        "diagnosis_history": [{"failed_node": "b", "repair_plan": []}],
        "corrections_applied": [{"node": "b", "fix_applied": "x"}],
    }
    nodes = [{"node_id": "a", "goal": "g", "capability": "impl", "exit_artifacts": []}]
    _write(tmp_path, ".allforai/bootstrap/workflow.json", json.dumps({"nodes": nodes, **history}))
    candidate_path = _write(tmp_path, ".allforai/bootstrap/candidate-workflow.json", json.dumps(
        {"nodes": nodes, "transition_log": [], "diagnosis_history": [],
         "corrections_applied": [{"node": "c", "fix_applied": "new"}]}))
    monkeypatch.chdir(tmp_path)
    assert _reconcile.main([str(tmp_path), "--candidate-workflow", str(candidate_path), "--write"]) == 0
    written = json.loads(candidate_path.read_text())
    assert written["transition_log"] == history["transition_log"]
    assert written["diagnosis_history"] == history["diagnosis_history"]
    assert written["corrections_applied"] == history["corrections_applied"] + [{"node": "c", "fix_applied": "new"}]
    plan = json.loads((tmp_path / ".allforai/bootstrap/workflow-reconciliation-plan.json").read_text())
    assert plan["carried_run_history"] == {"transition_log": 2, "diagnosis_history": 1, "corrections_applied": 1}


def test_without_write_the_candidate_is_untouched(tmp_path, monkeypatch):
    nodes = [{"node_id": "a", "goal": "g", "capability": "impl", "exit_artifacts": []}]
    _write(tmp_path, ".allforai/bootstrap/workflow.json", json.dumps(
        {"nodes": nodes, "transition_log": [{"node_id": "a", "status": "completed"}]}))
    text = json.dumps({"nodes": nodes, "transition_log": []})
    candidate_path = _write(tmp_path, ".allforai/bootstrap/candidate-workflow.json", text)
    monkeypatch.chdir(tmp_path)
    assert _reconcile.main([str(tmp_path), "--candidate-workflow", str(candidate_path)]) == 0
    assert candidate_path.read_text() == text
