import json
import os
import sys

import pytest

from ..module_isolation import load

_readiness = load("validate_unattended_readiness")
validate_unattended_readiness = _readiness.validate_unattended_readiness


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
        ],
        "user_steps": ["/cross-exam", "/product-review"],
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
            # Closure waits for the repair and for the QA rerun that proves it; waiting
            # for the repair alone is the shape both gates refuse.
            {"node_id": "closure-qa", "goal": "closure", "capability": "qa",
             "hard_blocked_by": ["runtime-repair", "runtime-qa"],
             "exit_artifacts": [{"path": ".allforai/quality-checks/closure.json"}]},
        ],
        "user_steps": ["/cross-exam", "/product-review"],
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


# The run boundary reads whatever `workflow.json` currently holds. Every check below the
# workflow load either indexes the graph by node identifier or names one in a blocker, so
# an identifier that cannot key a map is decided first and reported as a blocker. A gate
# that raises has decided nothing, and a caller that publishes nothing leaves its previous
# `ready` on disk as this run's answer.
def _with_nodes(tmp_path, nodes):
    _minimal_project(tmp_path)
    _write(tmp_path, ".allforai/bootstrap/workflow.json", json.dumps({"nodes": nodes}))


@pytest.mark.parametrize("node_id", [1, 0, 3.5, True, None, ["design"], {"id": "design"}, "", "  "])
def test_a_node_identifier_the_graph_cannot_address_blocks_the_run(tmp_path, node_id):
    _with_nodes(tmp_path, [{"node_id": node_id, "goal": "g", "capability": "implement",
                            "exit_artifacts": [{"path": ".allforai/game-design/design.json"}]}])

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert any(item["code"] == "malformed_workflow_node" for item in report["blockers"]), report


def test_one_malformed_identifier_beside_a_valid_node_still_blocks(tmp_path):
    """The addressable remainder is not the graph, so no per-node verdict is offered for it."""
    _with_nodes(tmp_path, [
        {"node_id": ["design"], "goal": "g", "capability": "implement", "exit_artifacts": []},
        {"node_id": "build", "goal": "g", "capability": "implement", "exit_artifacts": []},
    ])

    report = validate_unattended_readiness(tmp_path)

    codes = [item["code"] for item in report["blockers"]]
    assert "malformed_workflow_node" in codes, report
    assert "missing_node_spec" not in codes, report


def test_a_repeated_node_identifier_blocks_the_run(tmp_path):
    _with_nodes(tmp_path, [{"node_id": "design", "goal": "g", "capability": "implement",
                            "exit_artifacts": []} for _ in range(2)])

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert any(item["code"] == "malformed_workflow_node" for item in report["blockers"]), report


@pytest.mark.parametrize("nodes", [None, "bad", 42, {"design": {}}, [None], ["design"], [[]], [3]],
                         ids=["null", "string", "number", "object", "null-entry", "string-entry",
                              "array-entry", "number-entry"])
def test_a_malformed_node_collection_blocks_without_raising(tmp_path, nodes):
    _with_nodes(tmp_path, nodes)

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert report["blockers"]


@pytest.mark.parametrize("workflow", [b"{not json", b'{"nodes": [{"node_id": "\xff\xfe"}]}'],
                         ids=["unparseable", "undecodable"])
def test_a_workflow_that_cannot_be_read_blocks_without_raising(tmp_path, workflow):
    _minimal_project(tmp_path)
    (tmp_path / ".allforai/bootstrap/workflow.json").write_bytes(workflow)

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert any(item["code"] == "missing_workflow" for item in report["blockers"]), report


def test_a_node_spec_that_cannot_be_decoded_blocks_the_node(tmp_path):
    """The interactive, fallback and long-task rules are all read from this text; a brief
    that cannot be read yields no verdict, and no verdict is not an acceptance."""
    _minimal_project(tmp_path)
    (tmp_path / ".allforai/bootstrap/node-specs/design.md").write_bytes(b"work \xff\xfe here")

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert any(item["code"] == "unreadable_node_spec" and item.get("node_id") == "design"
               for item in report["blockers"]), report


@pytest.mark.parametrize("approval_path", [7, ["records.json"], {"path": "records.json"}, True])
def test_an_approval_record_path_that_names_no_file_leaves_the_gate_pending(tmp_path, approval_path):
    _minimal_project(tmp_path)
    workflow = json.loads((tmp_path / ".allforai/bootstrap/workflow.json").read_text())
    workflow["nodes"][0]["approval_record_path"] = approval_path
    _write(tmp_path, ".allforai/bootstrap/workflow.json", json.dumps(workflow))

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert any(item["code"] == "pending_human_gate" for item in report["blockers"]), report


@pytest.mark.parametrize("edges", ["runtime-repair", {"0": "runtime-repair"}, 4],
                         ids=["string", "object", "number"])
def test_a_closure_whose_edges_are_not_a_list_is_not_blocked_by_the_repair(tmp_path, edges):
    """A string edge list answers `in` by substring, which would admit an unwired closure."""
    _project_with_repair_loop(tmp_path, _repair_loop())
    workflow = json.loads((tmp_path / ".allforai/bootstrap/workflow.json").read_text())
    for node in workflow["nodes"]:
        if node["node_id"] == "closure-qa":
            node["hard_blocked_by"] = edges
    _write(tmp_path, ".allforai/bootstrap/workflow.json", json.dumps(workflow))

    report = validate_unattended_readiness(tmp_path)

    assert any(item["code"] == "closure_not_blocked_by_repair_loop" for item in report["blockers"]), report


@pytest.mark.parametrize("declared", ["runtime-qa", {"qa": 1}, 3], ids=["string", "object", "number"])
def test_a_repair_loop_whose_declared_node_list_is_not_a_list_is_refused(tmp_path, declared):
    _project_with_repair_loop(tmp_path, _repair_loop(qa_node_ids=declared))

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert any(item["code"] == "invalid_repair_loop_spec" for item in report["blockers"]), report


@pytest.mark.parametrize("qa_node_id", [1, None, ["runtime-qa"], {"id": "runtime-qa"}, "  "])
def test_a_repair_loop_naming_an_unaddressable_qa_node_is_refused(tmp_path, qa_node_id):
    _project_with_repair_loop(tmp_path, _repair_loop(qa_node_ids=[qa_node_id]))

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert any(item["code"] == "missing_repair_loop_source" for item in report["blockers"]), report


@pytest.mark.parametrize("closure_node_id", [1, None, ["closure-qa"], {"id": "closure-qa"}, "  "])
def test_a_repair_loop_naming_an_unaddressable_closure_node_is_refused(tmp_path, closure_node_id):
    _project_with_repair_loop(tmp_path, _repair_loop(closure_node_ids=[closure_node_id]))

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert any(item["code"] == "missing_repair_loop_closure" for item in report["blockers"]), report


def test_a_gate_that_cannot_reach_a_verdict_refuses_instead_of_raising(tmp_path, monkeypatch):
    """`main` is the boundary both hosts call; an undecided gate admits nothing."""
    _minimal_project(tmp_path)

    def explode(_root):
        raise RuntimeError("freshness store unreadable")

    monkeypatch.setattr(_readiness, "validate_unattended_readiness", explode)
    report_path = tmp_path / ".allforai/bootstrap/unattended-run-readiness.json"
    _write(tmp_path, ".allforai/bootstrap/unattended-run-readiness.json",
           json.dumps({"status": "ready", "blockers": []}))

    assert _readiness.main([str(tmp_path), "--write-report"]) == 1
    published = json.loads(report_path.read_text())
    assert published["status"] == "not_ready"
    assert [item["code"] for item in published["blockers"]] == ["readiness_gate_error"]
    assert "freshness store unreadable" in published["blockers"][0]["message"]


def test_a_read_only_report_file_is_still_replaced(tmp_path):
    """A stale `ready` cannot outlive the run that supersedes it just by being unwritable."""
    _minimal_project(tmp_path, gate_status="in-review")
    report_path = tmp_path / ".allforai/bootstrap/unattended-run-readiness.json"
    _write(tmp_path, ".allforai/bootstrap/unattended-run-readiness.json",
           json.dumps({"status": "ready", "blockers": []}))
    report_path.chmod(0o444)

    assert _readiness.main([str(tmp_path), "--write-report"]) == 1
    assert json.loads(report_path.read_text())["status"] == "not_ready"


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores directory permissions")
def test_a_read_only_directory_still_replaces_the_stale_report(tmp_path):
    """No new file can be created here, so the superseded verdict is overwritten in place
    rather than left standing beside a refusal only the exit code carries."""
    _minimal_project(tmp_path, gate_status="in-review")
    bootstrap = tmp_path / ".allforai/bootstrap"
    report_path = bootstrap / "unattended-run-readiness.json"
    _write(tmp_path, ".allforai/bootstrap/unattended-run-readiness.json",
           json.dumps({"status": "ready", "blockers": []}))
    _write(tmp_path, ".allforai/bootstrap/unattended-run-readiness.md", "Status: `ready`")
    bootstrap.chmod(0o555)
    try:
        assert _readiness.main([str(tmp_path), "--write-report"]) == 1
        assert json.loads(report_path.read_text())["status"] == "not_ready"
    finally:
        bootstrap.chmod(0o755)


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores filesystem permissions")
def test_an_unpublishable_verdict_is_still_a_refusal(tmp_path):
    """Nothing on disk can be written or removed, so the report is beyond this gate's
    reach. It still refuses, names the fault, and says the file on disk is not this run's
    answer — which is what both hosts' non-zero-exit check acts on."""
    _minimal_project(tmp_path, gate_status="in-review")
    bootstrap = tmp_path / ".allforai/bootstrap"
    report_path = bootstrap / "unattended-run-readiness.json"
    _write(tmp_path, ".allforai/bootstrap/unattended-run-readiness.json",
           json.dumps({"status": "ready", "blockers": []}))
    report_path.chmod(0o444)
    bootstrap.chmod(0o555)
    try:
        assert _readiness.main([str(tmp_path), "--write-report"]) == 1
    finally:
        bootstrap.chmod(0o755)
        report_path.chmod(0o644)


# A recorded safety halt is run-wide: it names work that was produced and never
# independently revalidated, and nothing about the plan, the policy or the evidence can
# qualify it. Both records are fences; neither is cleared by reading it.
MARKER = ".allforai/bootstrap/safety-quarantine.json"
LOCK = ".allforai/bootstrap/safety-quarantine.lock"


def _quarantine(tmp_path, node_ids=("design",)):
    _write(tmp_path, MARKER, json.dumps(
        {"schema_version": 1, "status": "quarantined", "node_ids": list(node_ids),
         "events": [{"recorded_at": "2026-09-09T10:00:00Z", "reason": "wave halted",
                     "nodes": [{"node_id": n, "exit_artifacts": []} for n in node_ids]}]}))


def test_a_recorded_safety_quarantine_blocks_the_run(tmp_path):
    _minimal_project(tmp_path)
    _quarantine(tmp_path)

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    blocker = next(b for b in report["blockers"] if b["code"] == "unresolved_safety_quarantine")
    assert "design" in blocker["message"], blocker
    assert (tmp_path / MARKER).exists(), "the gate must never clear a safety marker"


@pytest.mark.parametrize("marker", [
    b"{not json", b'\xff\xfe', b'{"schema_version": 2, "status": "quarantined", "node_ids": [], "events": []}',
    b'{"schema_version": 1, "status": "cleared", "node_ids": [], "events": []}',
    b'{"schema_version": 1, "status": "quarantined", "node_ids": "design", "events": []}',
    b'[]',
], ids=["unparseable", "undecodable", "wrong-schema", "cleared-status", "bad-node-ids", "array"])
def test_a_safety_marker_that_cannot_be_read_still_blocks(tmp_path, marker):
    """An unreadable halt is a stronger reason to stop than a legible one."""
    _minimal_project(tmp_path)
    (tmp_path / MARKER).write_bytes(marker)

    report = validate_unattended_readiness(tmp_path)

    codes = [b["code"] for b in report["blockers"]]
    assert "unresolved_safety_quarantine" in codes, report
    assert "invalid_safety_quarantine" in codes, report


@pytest.mark.parametrize("kind", ["directory", "broken-symlink", "symlink"])
def test_a_safety_marker_that_is_not_a_file_still_blocks(tmp_path, kind):
    _minimal_project(tmp_path)
    marker = tmp_path / MARKER
    if kind == "directory":
        marker.mkdir(parents=True)
    else:
        target = tmp_path / "elsewhere.json"
        if kind == "symlink":
            _quarantine(tmp_path)
            (tmp_path / MARKER).rename(target)
        marker.symlink_to(target)

    report = validate_unattended_readiness(tmp_path)

    assert "unresolved_safety_quarantine" in [b["code"] for b in report["blockers"]], report


def test_a_held_safety_lock_blocks_even_without_a_marker(tmp_path):
    """A quarantine that could not be published leaves this fence; the missing marker is
    exactly what cannot be trusted, so its absence is not evidence of nothing to record."""
    _minimal_project(tmp_path)
    (tmp_path / LOCK).mkdir(parents=True)

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert "unreconciled_safety_halt" in [b["code"] for b in report["blockers"]], report
    assert not (tmp_path / MARKER).exists()
    assert (tmp_path / LOCK).exists(), "the gate must never remove the fence"


def test_a_project_with_no_safety_record_is_still_admitted(tmp_path):
    """The halt must refuse a halted run, not every run."""
    _minimal_project(tmp_path)

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "ready", report


# The repair-authorization ledger fences itself the same way a safety halt does, and the
# gate reads both fences identically: refuse, never clear. What it must NOT do is treat an
# absent ledger as a fault — a run that has not recorded its origin yet has no ledger, and
# that is every new run before `initialize` proves zero from the workflow.
LEDGER_LOCK = ".allforai/bootstrap/repair-authorizations.lock"
LEDGER = ".allforai/bootstrap/repair-authorizations.json"


def test_a_held_repair_ledger_lock_blocks_the_run(tmp_path):
    _minimal_project(tmp_path)
    (tmp_path / LEDGER_LOCK).mkdir(parents=True)

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    blocker = next(b for b in report["blockers"]
                   if b["code"] == "unreconciled_repair_accounting")
    assert "reconcile" in blocker["message"].lower(), blocker
    assert (tmp_path / LEDGER_LOCK).is_dir(), "the gate must never clear the fence"


def test_a_missing_repair_ledger_does_not_block_readiness(tmp_path):
    """Normal before a verified `initialize`; blocking here would refuse every new run."""
    _minimal_project(tmp_path)
    assert not (tmp_path / LEDGER).exists()

    report = validate_unattended_readiness(tmp_path)

    codes = [b["code"] for b in report["blockers"]]
    assert "unreconciled_repair_accounting" not in codes, report
    assert report["status"] == "ready", report


# ADR-0008: `/cross-exam` and `/product-review` are user steps after the pipeline, never
# nodes. A generated workflow lists them at the top level in `user_steps`, where no engine
# reads them as work; a node that plans either is refused by name at the run boundary.
def _design_node(**overrides):
    node = {"node_id": "design", "goal": "design", "capability": "game-design",
            "human_gate": True,
            "approval_record_path": ".allforai/game-design/approval-records.json",
            "exit_artifacts": [{"path": ".allforai/game-design/design.json"}]}
    node.update(overrides)
    return node


def _with_workflow(tmp_path, workflow):
    _minimal_project(tmp_path)
    _write(tmp_path, ".allforai/bootstrap/workflow.json", json.dumps(workflow))


@pytest.mark.parametrize("field, value", [
    ("node_id", "cross-exam"), ("node_id", "product-review"),
    ("node_id", "Cross_Exam"), ("node_id", "final-product-review"),
    ("capability", "cross-exam"), ("capability", "product-review"),
])
def test_a_node_named_after_a_verdict_entry_is_refused_by_name(tmp_path, field, value):
    node = _design_node(**{field: value})
    _with_workflow(tmp_path, {"nodes": [node]})
    _write(tmp_path, f".allforai/bootstrap/node-specs/{node['node_id']}.md", "non interactive work")

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    blocker = next(b for b in report["blockers"] if b["code"] == "verdict_entry_planned_as_node")
    assert blocker["node_id"] == node["node_id"]
    assert "user step" in blocker["message"] and "user_steps" in blocker["message"], blocker


def test_user_steps_after_the_pipeline_are_admitted_and_never_scheduled(tmp_path):
    _with_workflow(tmp_path, {"nodes": [_design_node()],
                              "user_steps": ["/cross-exam", "/product-review"]})

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "ready", report
    assert report["blockers"] == []


@pytest.mark.parametrize("user_steps", ["/cross-exam", {"entry": "/cross-exam"}, [1], [""], [None]])
def test_user_steps_that_name_no_entry_are_refused_with_a_reason(tmp_path, user_steps):
    _with_workflow(tmp_path, {"nodes": [_design_node()], "user_steps": user_steps})

    report = validate_unattended_readiness(tmp_path)

    assert report["status"] == "not_ready"
    assert any(b["code"] == "invalid_user_steps" for b in report["blockers"]), report


def test_a_workflow_that_plans_verification_but_forgets_its_user_steps_is_not_ready(tmp_path):
    # a verify node means there is a product to examine afterwards; the steps the user takes then
    # are part of the workflow, and only an empty list says "nothing to examine"
    verify = {**_design_node(), "node_id": "pv", "capability": "product-verify",
              "exit_artifacts": [{"path": ".allforai/product-verify/verify-report.json"}]}
    _with_workflow(tmp_path, {"nodes": [_design_node(), verify]})
    report = validate_unattended_readiness(tmp_path)
    blocker = next(b for b in report["blockers"] if b["code"] == "missing_user_steps")
    assert "user_steps" in blocker["message"] and "[]" in blocker["message"]
    _with_workflow(tmp_path, {"nodes": [_design_node(), verify], "user_steps": []})
    assert not [b for b in validate_unattended_readiness(tmp_path)["blockers"] if b["code"] == "missing_user_steps"]
    # a design-only workflow is warned, not blocked
    _with_workflow(tmp_path, {"nodes": [_design_node()]})
    report = validate_unattended_readiness(tmp_path)
    assert not [b for b in report["blockers"] if b["code"] == "missing_user_steps"]
    assert any(w["code"] == "missing_user_steps" for w in report.get("warnings", []))


def _gate_node():
    return {"node_id": "concept-acceptance", "goal": "coverage gate", "capability": "concept-acceptance",
            "exit_artifacts": [{"path": ".allforai/concept-acceptance/acceptance-report.json"}]}


def _with_policy(tmp_path, on_needs_iteration):
    _write(tmp_path, ".allforai/bootstrap/run-policy.json", json.dumps({"on_needs_iteration": on_needs_iteration}))


def test_auto_fix_once_with_the_coverage_gate_needs_a_declared_repair_loop(tmp_path):
    _with_workflow(tmp_path, {"nodes": [_design_node(), _gate_node()],
                              "user_steps": ["/cross-exam", "/product-review"]})
    _with_policy(tmp_path, "auto_fix_once")
    report = validate_unattended_readiness(tmp_path)
    blocker = next(b for b in report["blockers"] if b["code"] == "missing_coverage_repair_loop")
    assert "required_repair_loops" in blocker["message"] and "concept-acceptance" in blocker["message"]
    assert blocker["node_id"] == "concept-acceptance"


def test_halt_with_report_needs_no_loop_for_the_coverage_gate(tmp_path):
    _with_workflow(tmp_path, {"nodes": [_design_node(), _gate_node()],
                              "user_steps": ["/cross-exam", "/product-review"]})
    _with_policy(tmp_path, "halt_with_report")
    report = validate_unattended_readiness(tmp_path)
    assert not [b for b in report["blockers"] if b["code"] == "missing_coverage_repair_loop"]


def test_a_declared_coverage_loop_satisfies_the_gate(tmp_path):
    gate, repair, rerun = _gate_node(), {
        "node_id": "concept-repair", "goal": "repair", "capability": "implement",
        "hard_blocked_by": ["concept-acceptance"],
        "exit_artifacts": [{"path": ".allforai/concept-acceptance/repair.json"}]}, {
        "node_id": "concept-acceptance-rerun", "goal": "rerun", "capability": "concept-acceptance",
        "hard_blocked_by": ["concept-repair", "concept-acceptance"],
        "exit_artifacts": [{"path": ".allforai/concept-acceptance/acceptance-report-2.json"}]}
    _with_workflow(tmp_path, {"nodes": [_design_node(), gate, repair, rerun],
                              "user_steps": ["/cross-exam", "/product-review"]})
    for n in ("concept-acceptance", "concept-repair", "concept-acceptance-rerun"):
        _write(tmp_path, f".allforai/bootstrap/node-specs/{n}.md", "non interactive work")
    _with_policy(tmp_path, "auto_fix_once")
    spec = json.loads((tmp_path / ".allforai/bootstrap/unattended-run-readiness-spec.json").read_text())
    spec["required_repair_loops"] = [_repair_loop(scope="concept-acceptance", qa_node_ids=["concept-acceptance"],
                                                  repair_node_id="concept-repair",
                                                  closure_node_ids=["concept-acceptance-rerun"])]
    _write(tmp_path, ".allforai/bootstrap/unattended-run-readiness-spec.json", json.dumps(spec))
    report = validate_unattended_readiness(tmp_path)
    assert not [b for b in report["blockers"] if b["code"] == "missing_coverage_repair_loop"], report
