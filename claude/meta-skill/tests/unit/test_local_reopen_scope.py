"""#11 local-change route: reopening one local intent blocks only its consumers.

Two disjoint local intents reach the copied ``product_intent`` CLI through the
actual admit, decide, freeze and plan operations on both host copies (the Codex
tests directory is a symlink to this one). These are copied-CLI seam tests in
temporary projects, not host-dialogue proof.
"""
import json

import pytest

from .test_bootstrap_scope import project as shared_project, gate, write, publish_contract
from .test_product_intent_session import invoke, decide, JOURNAL
from .test_validate_bootstrap import ATTENTION_CONTRACT_BODY

LOCAL = ".allforai/bootstrap/local-requirements.json"
PROFILE = ".allforai/bootstrap/bootstrap-profile.json"
WORKFLOW = ".allforai/bootstrap/workflow.json"
READINESS = ".allforai/bootstrap/unattended-run-readiness.json"
GATES = ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py")
RESPONSIBILITIES = ["implementation", "documentation", "verification"]
INTENTS = ["export", "archive"]
NODES = ["node-a", "node-b"]


def item(identity, goal):
    return {"id": identity, "topic": "scenarios", "goal": goal, "scope": ["orders"],
            "business_rules": ["Only the signed-in account is affected"], "acceptance": [goal + " is verified"]}


def local_project(root, host):
    """Admit two disjoint local intents, confirm both and answer the question one depends on."""
    shared_project(root, host=host, source_inputs=None)
    (root / LOCAL).unlink()
    admitted = invoke(root, {"operation": "admit", "route": "local-change", "goal": "Add export and archive",
                             "areas": ["orders"],
                             "items": [item("export", "Export account orders"), item("archive", "Archive old orders")],
                             "questions": [{"id": "retention", "topic": "scenarios", "kind": "gap",
                                            "question": "How long are archives kept?", "depends_on": ["archive"]}]})
    assert admitted.returncode == 0, admitted.stdout
    confirmed = decide(root, [{"operation": "confirm", "id": i, "reason": "Wanted"} for i in INTENTS] + [
        {"operation": "answer", "id": "retention", "answer": "One year", "reason": "Policy"}], "local-1")
    assert confirmed.returncode == 0, confirmed.stdout


def node(identity, intents):
    return {"node_id": identity, "capability": "implement", "goal": "Deliver " + identity, "intent_ids": intents,
            "responsibilities": RESPONSIBILITIES, "source_inputs": ["orders.py"],
            "exit_artifacts": [".allforai/bootstrap/" + identity + ".json"], "body": ATTENTION_CONTRACT_BODY}


def plan(root):
    return invoke(root, {"operation": "plan", "nodes": [node("node-a", ["export"]), node("node-b", ["archive"])]})


def freeze_and_plan(root, batch, publish=NODES):
    frozen = invoke(root, {"operation": "freeze", "include": INTENTS, "exclude": {}, "batch_id": batch,
                           "user_reference": "user scope " + batch, "reason": "Both changes"})
    assert frozen.returncode == 0, frozen.stdout
    planned = plan(root)
    assert planned.returncode == 0, planned.stdout
    for identity in publish:
        publish_contract(root, identity)
    return json.loads(frozen.stdout)["baseline"]


def gates_ready(root):
    for name in GATES:
        result = gate(root, name, *(("--write-report",) if name.endswith("readiness.py") else ()))
        assert result.returncode == 0, (name, result.stdout, result.stderr)


def blockers(root):
    readiness = gate(root, "validate_unattended_readiness.py", "--write-report")
    assert readiness.returncode == 1, readiness.stdout
    found = json.loads((root / READINESS).read_text())["blockers"]
    assert found, readiness.stdout
    return found


def assert_only_node_b(root, found):
    assert all(b.get("node_id") == "node-b" for b in found), found
    assert "invalid_scope" not in {b["code"] for b in found}, found
    for name in GATES[:2]:
        result = gate(root, name)
        assert result.returncode == 1, (name, result.stdout)
        assert "node-b" in result.stdout and "node-a" not in result.stdout, (name, result.stdout)
        assert "invalid_scope" not in result.stdout, (name, result.stdout)


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("reopened", ["archive", "retention"])
def test_reopened_local_intent_blocks_only_its_consumers_until_reconfirm_refreeze_replan(tmp_path, host, reopened):
    local_project(tmp_path, host)
    freeze_and_plan(tmp_path, "local-scope")
    gates_ready(tmp_path)
    spec_a = (tmp_path / ".allforai/bootstrap/node-specs/node-a.md").read_bytes()
    reopen = decide(tmp_path, [{"operation": "reopen", "id": reopened, "reason": "Reconsider"}], "reconsider")
    assert reopen.returncode == 0, reopen.stdout
    found = blockers(tmp_path)
    assert_only_node_b(tmp_path, found)
    assert "pending_requirement" in {b["code"] for b in found}, found
    if reopened == "retention":
        assert any("unresolved" in b["message"] for b in found), found
    # Neither a refreeze nor a replan can proceed while the reopened decision is pending.
    assert invoke(tmp_path, {"operation": "freeze", "include": INTENTS, "exclude": {}, "batch_id": "early",
                             "user_reference": "user", "reason": "Too early"}).returncode == 1
    assert plan(tmp_path).returncode == 1
    action = ({"operation": "answer", "id": "retention", "answer": "Two years", "reason": "Reviewed"}
              if reopened == "retention" else {"operation": "confirm", "id": "archive", "reason": "Still wanted"})
    assert decide(tmp_path, [action], "settled").returncode == 0
    # Reconfirm, refreeze, replan and actually reverify only the affected node.
    baseline = freeze_and_plan(tmp_path, "local-scope-2", publish=["node-b"])
    gates_ready(tmp_path)
    assert baseline["version"] == 2
    assert (tmp_path / ".allforai/bootstrap/node-specs/node-a.md").read_bytes() == spec_a
    profile = json.loads((tmp_path / PROFILE).read_text())
    assert profile["intent_scope"] == baseline
    revisions = {r["id"]: r["revision"] for r in profile["task_scope"]["requirement_refs"]}
    assert revisions == {"export": 1, "archive": 2 if reopened == "archive" else 1}


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("drift", ["forged-status", "silent-edit", "silent-revision"])
def test_local_journal_authority_and_revision_checks_bind_to_the_consuming_node(tmp_path, host, drift):
    local_project(tmp_path, host)
    freeze_and_plan(tmp_path, "local-scope")
    gates_ready(tmp_path)
    local = json.loads((tmp_path / LOCAL).read_text())
    archive = next(i for i in local["requirements"] if i["id"] == "archive")
    if drift == "forged-status":
        assert decide(tmp_path, [{"operation": "reopen", "id": "archive", "reason": "Reconsider"}], "reconsider").returncode == 0
        local = json.loads((tmp_path / LOCAL).read_text())
        # Flipping the reopened revision to confirmed without a journal decision is not a confirmation.
        next(i for i in local["requirements"] if i["id"] == "archive" and i["revision"] == 2)["status"] = "confirmed"
    elif drift == "silent-edit":
        archive["acceptance"] = ["Every account is archived"]
    else:
        local["requirements"].append(dict(archive, revision=2))
    write(tmp_path, LOCAL, local)
    found = blockers(tmp_path)
    assert_only_node_b(tmp_path, found)
    assert "stale_requirement" in {b["code"] for b in found}, found


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("fault", ["missing-batch", "scope-mismatch", "superseded-scope"])
def test_local_freeze_level_invalidity_stays_a_global_blocker(tmp_path, host, fault):
    local_project(tmp_path, host)
    freeze_and_plan(tmp_path, "local-scope")
    gates_ready(tmp_path)
    profile = json.loads((tmp_path / PROFILE).read_text())
    if fault == "missing-batch":
        profile["intent_scope"]["confirmation"] = JOURNAL + "#missing/decisions/0"
    elif fault == "scope-mismatch":
        profile["task_scope"]["requirement_refs"] = profile["task_scope"]["requirement_refs"][:1]
    else:
        journal = json.loads((tmp_path / JOURNAL).read_text())
        journal["batches"].append({"batch_id": "cancel", "source": "user_session", "topic": "Cancel scope",
                                   "user_reference": "user cancel", "decisions": [{
                                       "question": "Keep this scope?", "chosen": "Cancel", "rationale": "Changed mind",
                                       "supersedes": profile["intent_scope"]["confirmation"]}]})
        write(tmp_path, JOURNAL, journal)
    write(tmp_path, PROFILE, profile)
    found = blockers(tmp_path)
    assert [b["code"] for b in found] == ["invalid_scope"] and "node_id" not in found[0], found
