"""#9 the plan that executes must be the plan the user confirmed.

Step 3.4 presents a node list and the later audits may change it, so the presented
graph is persisted with its provenance and every later change is a delta against it.
These drive the copied public gates — the bootstrap validator and the run-readiness
gate — in temporary projects; they are copied-CLI seam tests, not host dialogue proof.
"""
import json

import pytest

from .test_bootstrap_scope import (ATTENTION_CONTRACT_BODY, PLAN_CONFIRMATION, PLAN_JOURNAL,
                                   REF, REQUIREMENTS, confirm_plan, gate, project, write)

WORKFLOW = ".allforai/bootstrap/workflow.json"
GATES = ("validate_bootstrap.py", "validate_unattended_readiness.py")
NODE = "deliver-export"


def record(root):
    return json.loads((root / PLAN_CONFIRMATION).read_text())


def journal(root):
    return json.loads((root / PLAN_JOURNAL).read_text())


def add_node(root, node_id, *, hard_blocked_by=(), completed=False):
    """Grow the plan the way an audit would, without presenting it to anyone."""
    workflow = json.loads((root / WORKFLOW).read_text())
    node = {"node_id": node_id, "goal": "Added by an audit", "capability": "implement",
            "hard_blocked_by": list(hard_blocked_by), "decision_inputs": [REQUIREMENTS],
            "requirement_refs": [REF], "responsibilities": ["implementation"],
            "source_inputs": ["orders.py"],
            "exit_artifacts": [f".allforai/bootstrap/{node_id}.json"]}
    workflow["nodes"].append(node)
    if completed:
        workflow["transition_log"].append({"node_id": node_id, "status": "completed"})
    write(root, WORKFLOW, workflow)
    write(root, f".allforai/bootstrap/{node_id}.json", {"status": "passed"})
    (root / ".allforai/bootstrap/node-specs" / (node_id + ".md")).write_text(
        "---\n" + json.dumps(node) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    return node


def refused(root, code, *, node_id=None):
    """Both public boundaries must refuse, and the readiness report must carry the code."""
    for name in GATES:
        options = ("--write-report",) if name.endswith("readiness.py") else ()
        result = gate(root, name, *options)
        assert result.returncode == 1, (name, result.stdout, result.stderr)
        assert not result.stderr, (name, result.stderr)
        assert code in result.stdout, (name, result.stdout)
    blockers = json.loads((root / ".allforai/bootstrap/unattended-run-readiness.json").read_text())["blockers"]
    matched = [b for b in blockers if b["code"] == code]
    assert matched, blockers
    if node_id is not None:
        assert [b.get("node_id") for b in matched] == [node_id], matched
    return matched


PLAN_CODES = ("unconfirmed_plan", "invalid_plan_confirmation", "unconfirmed_plan_delta")


def accepted(root):
    """The bootstrap validator passes and no plan-confirmation blocker survives at run time."""
    result = gate(root, "validate_bootstrap.py")
    assert result.returncode == 0, result.stdout
    gate(root, "validate_unattended_readiness.py", "--write-report")
    blockers = json.loads((root / ".allforai/bootstrap/unattended-run-readiness.json").read_text())["blockers"]
    assert [b for b in blockers if b["code"] in PLAN_CODES] == [], blockers


def test_a_confirmed_plan_passes_both_public_boundaries(tmp_path):
    project(tmp_path, confirmed=True)
    accepted(tmp_path)
    assert record(tmp_path)["confirmations"][0]["plan"] == {NODE: []}


def test_a_generated_plan_without_its_confirmation_is_refused_at_run_time(tmp_path):
    project(tmp_path, confirmed=True)
    (tmp_path / PLAN_CONFIRMATION).unlink()
    refused(tmp_path, "unconfirmed_plan", node_id=NODE)


def test_finished_history_without_a_record_is_left_alone(tmp_path):
    """An unrecorded plan is demanded of the work that has yet to execute, not of history."""
    project(tmp_path, confirmed=True)
    (tmp_path / PLAN_CONFIRMATION).unlink()
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow["transition_log"] = [{"node_id": NODE, "status": "completed"}]
    write(tmp_path, WORKFLOW, workflow)
    result = gate(tmp_path, "validate_bootstrap.py")
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize("mutation", [
    {"schema_version": "1.0", "confirmations": [{"revision": 1, "stage": "step-3.4", "approved": True}]},
    {"schema_version": "1.0", "confirmations": []},
    {"schema_version": "1.0", "confirmations": [{"revision": 1, "stage": "step-3.4", "plan": {}}]},
    {"approved": True},
], ids=["approval-flag", "empty-record", "empty-plan", "bare-boolean"])
def test_an_approval_flag_is_not_a_confirmed_plan(tmp_path, mutation):
    project(tmp_path, confirmed=True)
    write(tmp_path, PLAN_CONFIRMATION, mutation)
    refused(tmp_path, "invalid_plan_confirmation")


@pytest.mark.parametrize("reference", [
    "the user said yes in chat",
    ".allforai/bootstrap/approved.json#batch/decisions/0",
    ".allforai/bootstrap/plan-confirmation-journal.json#no-such-batch/decisions/0",
    ".allforai/bootstrap/plan-confirmation-journal.json#plan-revision-1/decisions/7",
    "/etc/passwd#plan-revision-1/decisions/0",
], ids=["free-text", "arbitrary-file", "missing-batch", "missing-decision", "outside-project"])
def test_a_fabricated_reference_is_not_authority(tmp_path, reference):
    project(tmp_path, confirmed=True)
    stored = record(tmp_path)
    stored["confirmations"][0]["confirmation"]["reference"] = reference
    write(tmp_path, PLAN_CONFIRMATION, stored)
    refused(tmp_path, "invalid_plan_confirmation")


@pytest.mark.parametrize("mutation", [
    {"source": "model_inference"},
    {"status": "pending"},
], ids=["not-a-user-session", "unconfirmed-batch"])
def test_a_batch_that_is_not_a_confirmed_user_session_is_not_authority(tmp_path, mutation):
    project(tmp_path, confirmed=True)
    entries = journal(tmp_path)
    entries["batches"][0].update(mutation)
    write(tmp_path, PLAN_JOURNAL, entries)
    refused(tmp_path, "invalid_plan_confirmation")


def test_a_retracted_confirmation_invalidates_the_plan_it_authorized(tmp_path):
    """Revisions are append-only, so supersession means the confirmation was retracted."""
    project(tmp_path, confirmed=True)
    entries = journal(tmp_path)
    entries["batches"].append({
        "batch_id": "retraction", "source": "user_session", "topic": "Workflow plan",
        "user_reference": "user withdrew the plan",
        "decisions": [{"question": "Keep that plan?", "chosen": "No, withdraw it",
                       "rationale": "Wrong scope",
                       "supersedes": "plan-revision-1/decisions/0"}]})
    write(tmp_path, PLAN_JOURNAL, entries)
    refused(tmp_path, "invalid_plan_confirmation")


def test_a_decision_that_records_another_graph_does_not_confirm_this_one(tmp_path):
    project(tmp_path, confirmed=True)
    entries = journal(tmp_path)
    entries["batches"][0]["decisions"][0]["intent"] = {"plan": {"some-other-node": []}}
    write(tmp_path, PLAN_JOURNAL, entries)
    refused(tmp_path, "invalid_plan_confirmation")


@pytest.mark.parametrize("edges", [None, "deliver-export", [17, None], ["", "  "], ["ghost-node"],
                                   [NODE, NODE]],
                         ids=["null", "string", "mixed", "blank", "outside-plan", "repeated"])
def test_a_malformed_recorded_graph_is_refused_not_repaired(tmp_path, edges):
    """A null, a string or a mixed edge list must not be sanitized into a valid plan."""
    project(tmp_path, confirmed=True)
    stored = record(tmp_path)
    stored["confirmations"][0]["plan"] = {NODE: edges}
    write(tmp_path, PLAN_CONFIRMATION, stored)
    refused(tmp_path, "invalid_plan_confirmation")


@pytest.mark.parametrize("edges", [None, "deliver-export", [17, None], ["ghost-node"]],
                         ids=["null", "string", "mixed", "outside-plan"])
def test_a_malformed_recorded_intent_is_refused_not_repaired(tmp_path, edges):
    project(tmp_path, confirmed=True)
    entries = journal(tmp_path)
    entries["batches"][0]["decisions"][0]["intent"] = {"plan": {NODE: edges}}
    write(tmp_path, PLAN_JOURNAL, entries)
    refused(tmp_path, "invalid_plan_confirmation")


def test_a_node_added_after_the_confirmation_holds_only_that_node(tmp_path):
    project(tmp_path, confirmed=True)
    add_node(tmp_path, "cross-module-stitch")
    blockers = refused(tmp_path, "unconfirmed_plan_delta", node_id="cross-module-stitch")
    assert NODE not in [b.get("node_id") for b in blockers]


def test_completing_the_inserted_node_does_not_confirm_it(tmp_path):
    """A newly mutated completed record buys no exemption from the confirmation it skipped."""
    project(tmp_path, confirmed=True)
    add_node(tmp_path, "cross-module-stitch", completed=True)
    refused(tmp_path, "unconfirmed_plan_delta", node_id="cross-module-stitch")


def test_a_rewired_dependency_is_a_plan_change(tmp_path):
    project(tmp_path, confirmed=True)
    add_node(tmp_path, "orders-display-contract")
    confirm_plan(tmp_path, reason="Presented the added contract node")
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow["nodes"][0]["hard_blocked_by"] = ["orders-display-contract"]
    write(tmp_path, WORKFLOW, workflow)
    (tmp_path / ".allforai/bootstrap/node-specs" / (NODE + ".md")).write_text(
        "---\n" + json.dumps(workflow["nodes"][0]) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    refused(tmp_path, "unconfirmed_plan_delta", node_id=NODE)


def test_a_node_dropped_after_the_confirmation_is_a_plan_change(tmp_path):
    project(tmp_path, confirmed=True)
    add_node(tmp_path, "cross-module-stitch")
    confirm_plan(tmp_path, reason="Presented the added stitch node")
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow["nodes"] = [n for n in workflow["nodes"] if n["node_id"] != "cross-module-stitch"]
    write(tmp_path, WORKFLOW, workflow)
    (tmp_path / ".allforai/bootstrap/node-specs/cross-module-stitch.md").unlink()
    refused(tmp_path, "unconfirmed_plan_delta")


def test_the_confirmed_delta_recovers_the_plan_and_keeps_earlier_history(tmp_path):
    project(tmp_path, confirmed=True)
    first = record(tmp_path)["confirmations"][0]
    add_node(tmp_path, "cross-module-stitch")
    refused(tmp_path, "unconfirmed_plan_delta", node_id="cross-module-stitch")

    confirm_plan(tmp_path, reason="Presented the added stitch node")
    accepted(tmp_path)
    stored = record(tmp_path)["confirmations"]
    assert stored[0] == first, "an earlier revision is history, not something to rewrite"
    assert stored[1]["revision"] == 2
    assert stored[1]["delta"] == {"added": ["cross-module-stitch"], "removed": [], "rewired": []}


def test_a_revision_that_misstates_its_delta_is_refused(tmp_path):
    project(tmp_path, confirmed=True)
    add_node(tmp_path, "cross-module-stitch")
    confirm_plan(tmp_path, reason="Presented the added stitch node")
    stored = record(tmp_path)
    stored["confirmations"][1]["delta"] = {"added": [], "removed": [], "rewired": []}
    write(tmp_path, PLAN_CONFIRMATION, stored)
    refused(tmp_path, "invalid_plan_confirmation")


def test_a_re_confirmation_that_changes_nothing_is_not_a_revision(tmp_path):
    project(tmp_path, confirmed=True)
    stored = record(tmp_path)
    repeat = json.loads(json.dumps(stored["confirmations"][0]))
    repeat["revision"] = 2
    repeat["delta"] = {"added": [], "removed": [], "rewired": []}
    stored["confirmations"].append(repeat)
    write(tmp_path, PLAN_CONFIRMATION, stored)
    refused(tmp_path, "invalid_plan_confirmation")


def test_history_cannot_be_renumbered_to_hide_a_revision(tmp_path):
    project(tmp_path, confirmed=True)
    add_node(tmp_path, "cross-module-stitch")
    confirm_plan(tmp_path, reason="Presented the added stitch node")
    stored = record(tmp_path)
    stored["confirmations"] = stored["confirmations"][1:]  # drop the first revision, keep its number
    write(tmp_path, PLAN_CONFIRMATION, stored)
    refused(tmp_path, "invalid_plan_confirmation")
