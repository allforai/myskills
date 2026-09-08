"""A hand-projected legacy local profile (no intent session marker) cannot borrow authority
from a goal-only journal choice; resume recovers it without deleting the old file.

Copied-CLI seam tests in temporary projects on both host copies; not host-dialogue proof.
The fixture is the documented hand route: `task_route: local-change`, `task_scope.requirement_refs`
into `local-requirements.json`, no `intent_session_path`.
"""
import copy
import json
import sys

import pytest

from .test_bootstrap_scope import REQUIREMENTS, project, gate, publish_contract, write
from .test_product_intent_session import invoke, decide, JOURNAL
from .test_validate_bootstrap import ATTENTION_CONTRACT_BODY

GATES = ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py")
PROFILE = ".allforai/bootstrap/bootstrap-profile.json"
READINESS = ".allforai/bootstrap/unattended-run-readiness.json"
REFERENCE = JOURNAL + "#prior/decisions/0"


def prior_journal(chosen, rationale="Account isolation is required", intent=None):
    decision = {"question": "Export which orders?", "chosen": chosen, "rationale": rationale}
    if intent is not None:
        decision["intent"] = intent
    return {"schema_version": "1.0", "batches": [{"batch_id": "prior", "source": "user_session",
                                                   "user_reference": "old turn", "decisions": [decision]}]}


SHAPE_ONLY = [sys.executable, "-c", "import json; json.load(open('.allforai/bootstrap/workflow.json'))['nodes']"]


def hand_projection(root, requirement, journal, *, acceptance=None, scope=None, ready=False):
    """Point the documented hand projection at a journal decision and re-observe the contract.

    A projection the gates must block cannot pass the bootstrap validator as its
    verifier, so its contract is published with the shape-only check the scope fixture uses.
    """
    requirement["confirmation"] = {"source": "user", "reference": REFERENCE,
                                   "decision_id": "prior/decisions/0", "reason": "Account isolation is required"}
    if acceptance is not None:
        requirement["acceptance"] = acceptance
    if scope is not None:
        requirement["scope"] = scope
    write(root, JOURNAL, journal)
    write(root, REQUIREMENTS, {"requirements": [requirement]})
    publish_contract(root, verification_command=None if ready else SHAPE_ONLY)
    return requirement


def run_gates(root):
    results = {name: gate(root, name, *(("--write-report",) if name == GATES[2] else ())) for name in GATES}
    for result in results.values():
        assert not result.stderr, result.stderr
    return results


def pending_items(output):
    return {i["id"]: i for t in output["topics"] for i in t["items"]}


def snapshot(root):
    return {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_goal_only_journal_cannot_authorize_hand_projected_scope_and_acceptance(tmp_path, host):
    requirement = project(tmp_path, confirmed=True, host=host)
    hand_projection(tmp_path, requirement, prior_journal("Export the current account's orders as CSV"),
                    acceptance=["MODEL-INVENTED acceptance"], scope=["orders", "MODEL-ADDED-area"])
    before = snapshot(tmp_path)
    results = run_gates(tmp_path)
    for name, result in results.items():
        assert result.returncode == 1, (name, result.stdout)
        assert "pending_requirement" in result.stdout, (name, result.stdout)
        assert "invalid_scope" not in result.stdout, (name, result.stdout)
    report = json.loads((tmp_path / READINESS).read_text())
    assert report["status"] == "not_ready"
    assert any(b.get("code") == "pending_requirement" and b.get("node_id") == "deliver-export"
               for b in report["blockers"]), report["blockers"]
    before.pop(tmp_path / READINESS, None)
    assert all(p.read_bytes() == content for p, content in before.items())
    # Interactive recovery: resume reads the legacy local file, keeps the evidenced goal and
    # asks only for the missing projection authority, not a whole-product interview.
    resumed = invoke(tmp_path, {"operation": "resume"})
    assert resumed.returncode == 0, resumed.stdout
    output = json.loads(resumed.stdout)
    pending = pending_items(output)
    assert list(pending) == ["export"], output
    exposed = pending["export"]
    assert exposed["status"] == "pending"
    assert exposed["legacy_reuse"] == {"reference": REFERENCE, "evidenced": ["goal"],
                                       "unconfirmed": ["scope", "business_rules", "acceptance"]}
    assert exposed["goal"] == "Export the current account's orders as CSV"
    assert exposed["confirmation"] == requirement["confirmation"]
    assert not [q for t in output["topics"] for q in t["questions"]]
    assert [(i["id"], i["revision"], i["goal"]) for i in output["history"]] == [("export", 1, requirement["goal"])]
    assert (tmp_path / REQUIREMENTS).read_bytes() == before[tmp_path / REQUIREMENTS]
    assert (tmp_path / PROFILE).read_bytes() == before[tmp_path / PROFILE]


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_mismatched_goal_only_journal_is_rejected_without_legacy_reuse(tmp_path, host):
    requirement = project(tmp_path, confirmed=True, host=host)
    prior = prior_journal("Something else entirely", "Privacy")
    hand_projection(tmp_path, requirement, prior)
    results = run_gates(tmp_path)
    for name, result in results.items():
        assert result.returncode == 1, (name, result.stdout)
        assert "pending_requirement" in result.stdout, (name, result.stdout)
    assert json.loads((tmp_path / READINESS).read_text())["status"] == "not_ready"
    output = json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)
    exposed = pending_items(output)["export"]
    assert exposed["status"] == "pending" and "legacy_reuse" not in exposed, exposed
    assert exposed["pending_reason"]
    assert json.loads((tmp_path / JOURNAL).read_text()) == prior


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_user_confirmation_recovers_legacy_profile_without_deleting_old_local_file(tmp_path, host):
    requirement = project(tmp_path, confirmed=True, host=host)
    prior = prior_journal("Export the current account's orders as CSV")
    hand_projection(tmp_path, requirement, prior)
    profile_before = (tmp_path / PROFILE).read_bytes()
    assert run_gates(tmp_path)[GATES[2]].returncode == 1
    confirmed = decide(tmp_path, [{"operation": "confirm", "id": "export",
                                   "reason": "Isolation rule and acceptance approved"}], "projection")
    assert confirmed.returncode == 0, confirmed.stdout
    assert pending_items(json.loads(confirmed.stdout)) == {}
    stored = json.loads((tmp_path / REQUIREMENTS).read_text())["requirements"]
    assert [i["id"] for i in stored] == ["export"] and stored[0]["revision"] == 1
    assert stored[0]["status"] == "confirmed" and "pending_reason" not in stored[0] and "legacy_reuse" not in stored[0]
    assert stored[0]["prior_confirmation"] == requirement["confirmation"]
    assert stored[0]["confirmation"]["reference"] == JOURNAL + "#projection/decisions/0"
    assert stored[0]["acceptance"] == requirement["acceptance"]
    journal = json.loads((tmp_path / JOURNAL).read_text())
    assert journal["batches"][0] == prior["batches"][0]
    assert journal["batches"][1]["decisions"][0]["intent"] == stored[0]
    # The legacy profile is recovered in place: no session marker, same scope, no plan rewrite.
    assert (tmp_path / PROFILE).read_bytes() == profile_before
    publish_contract(tmp_path)  # The consumed requirement changed; the contract observes it again.
    for name, result in run_gates(tmp_path).items():
        assert result.returncode == 0, (name, result.stdout)
    assert json.loads((tmp_path / READINESS).read_text())["status"] == "ready"
    assert pending_items(json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)) == {}
    # Moving on to the session lifecycle is explicit: a local freeze records the marker.
    frozen = invoke(tmp_path, {"operation": "freeze", "include": ["export"], "exclude": {}, "batch_id": "local-scope",
                               "user_reference": "local scope turn", "reason": "Account export only"})
    assert frozen.returncode == 0, frozen.stdout
    profile = json.loads((tmp_path / PROFILE).read_text())
    assert profile["intent_session_path"] == REQUIREMENTS and profile["intent_scope"]["version"] == 1
    assert json.loads((tmp_path / JOURNAL).read_text())["batches"][0] == prior["batches"][0]
    planned = invoke(tmp_path, {"operation": "plan", "nodes": [{"node_id": "export", "capability": "implement",
        "goal": "Deliver CSV export", "intent_ids": ["export"],
        "responsibilities": ["implementation", "documentation", "verification"], "source_inputs": ["orders.py"],
        "exit_artifacts": [".allforai/bootstrap/export-result.json"], "body": ATTENTION_CONTRACT_BODY}]})
    assert planned.returncode == 0, planned.stdout
    publish_contract(tmp_path, "export")
    for name, result in run_gates(tmp_path).items():
        assert result.returncode == 0, (name, result.stdout)


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_full_payload_journal_projection_stays_accepted(tmp_path, host):
    requirement = project(tmp_path, confirmed=True, host=host)
    requirement["confirmation"] = {"source": "user", "reference": REFERENCE,
                                   "decision_id": "prior/decisions/0", "reason": "Account isolation is required"}
    prior = prior_journal(requirement["goal"], intent=copy.deepcopy(requirement))
    hand_projection(tmp_path, requirement, prior, ready=True)
    for name, result in run_gates(tmp_path).items():
        assert result.returncode == 0, (name, result.stdout)
    assert pending_items(json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)) == {}
    # A projection drifting from the recorded payload loses that authority.
    drifted = json.loads((tmp_path / REQUIREMENTS).read_text())
    drifted["requirements"][0]["acceptance"] = ["Export every account"]
    write(tmp_path, REQUIREMENTS, drifted)
    publish_contract(tmp_path, verification_command=SHAPE_ONLY)
    for name, result in run_gates(tmp_path).items():
        assert result.returncode == 1, (name, result.stdout)
        assert "pending_requirement" in result.stdout
    assert json.loads((tmp_path / JOURNAL).read_text()) == prior


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_actual_user_turn_projection_stays_accepted_on_resume(tmp_path, host):
    requirement = project(tmp_path, confirmed=True, host=host)
    for name, result in run_gates(tmp_path).items():
        assert result.returncode == 0, (name, result.stdout)
    resumed = invoke(tmp_path, {"operation": "resume"})
    assert resumed.returncode == 0, resumed.stdout
    output = json.loads(resumed.stdout)
    assert pending_items(output) == {}
    assert output["history"] == [requirement]


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_admit_still_refuses_to_overwrite_legacy_local_file(tmp_path, host):
    project(tmp_path, confirmed=True, host=host)
    before = snapshot(tmp_path)
    result = invoke(tmp_path, {"operation": "admit", "route": "local-change", "goal": "Add order CSV export",
                               "areas": ["orders"], "items": [{"id": "export", "topic": "scenarios", "goal": "x",
                                                                "scope": ["orders"], "business_rules": ["r"],
                                                                "acceptance": ["a"]}]})
    assert result.returncode == 1
    assert "resume" in json.loads(result.stdout)["error"]
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_mixed_legacy_history_enters_the_session_lifecycle_without_an_interview(tmp_path, host):
    """User-turn confirmed item + goal-only pending item + user-turn removed item: confirm
    only the pending one; a local freeze then needs the user-turn item recorded once (no
    question asked), keeps removed history removed after the marker, and plans."""
    requirement = project(tmp_path, confirmed=True, host=host)
    user_turn = dict(requirement["confirmation"])
    sync = {"id": "sync", "revision": 1, "scope": ["orders"], "goal": "Sync orders to the warehouse",
            "business_rules": ["Nightly only"], "acceptance": ["No sync runs by day"], "status": "confirmed",
            "confirmation": {"source": "user", "reference": REFERENCE, "decision_id": "prior/decisions/0",
                             "reason": "Warehouse needs the orders"}}
    old = {"id": "old", "revision": 1, "scope": ["orders"], "goal": "Fax orders", "business_rules": ["Never"],
           "acceptance": ["No fax"], "status": "removed",
           "confirmation": {"source": "user", "reference": "bootstrap user turn 3", "decision_id": "remove-fax-1",
                            "reason": "Fax is gone"}}
    prior = prior_journal(sync["goal"], "Warehouse needs the orders")
    write(tmp_path, JOURNAL, prior)
    write(tmp_path, REQUIREMENTS, {"requirements": [requirement, sync, old]})
    publish_contract(tmp_path)
    output = json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)
    assert list(pending_items(output)) == ["sync"] and "legacy_reuse" in pending_items(output)["sync"]
    assert decide(tmp_path, [{"operation": "confirm", "id": "sync", "reason": "Sync rules approved"}],
                  "projection").returncode == 0
    assert pending_items(json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)) == {}
    # The recorded sync decision is not consumed by the hand-written plan yet: the
    # decision-input gate names the journal as unwired until the scope is planned.
    unwired = run_gates(tmp_path)["check_decision_inputs.py"]
    assert unwired.returncode == 1 and "orphan (unwired): " + JOURNAL in unwired.stdout, unwired.stdout
    freeze = {"operation": "freeze", "include": ["export", "sync"], "exclude": {"old": "Fax is gone"},
              "batch_id": "local-scope", "user_reference": "local scope turn", "reason": "Export and sync"}
    blocked = invoke(tmp_path, freeze)
    assert blocked.returncode == 1, blocked.stdout
    error = json.loads(blocked.stdout)["error"]
    assert "export" in error and "confirm" in error, error
    assert "intent_session_path" not in json.loads((tmp_path / PROFILE).read_text())
    # One recording decision under the original user turn: it records the already
    # evidenced payload unchanged; it is not a fresh approval and asks no question.
    recorded = invoke(tmp_path, {"operation": "decide", "batch_id": "record", "topic": "Record legacy confirmation",
                                 "user_reference": user_turn["reference"],
                                 "actions": [{"operation": "confirm", "id": "export", "reason": user_turn["reason"]}]})
    assert recorded.returncode == 0, recorded.stdout
    stored = {i["id"]: i for i in json.loads((tmp_path / REQUIREMENTS).read_text())["requirements"]}
    assert stored["export"]["prior_confirmation"] == user_turn and stored["export"]["revision"] == 1
    assert stored["export"]["confirmation"]["user_reference"] == user_turn["reference"]
    assert {k: stored["export"][k] for k in ("goal", "scope", "business_rules", "acceptance")} == {
        k: requirement[k] for k in ("goal", "scope", "business_rules", "acceptance")}
    record_batch = json.loads((tmp_path / JOURNAL).read_text())["batches"][-1]
    assert record_batch["user_reference"] == user_turn["reference"]
    assert record_batch["decisions"][0]["intent"] == stored["export"]
    assert stored["old"]["status"] == "removed" and "prior_confirmation" not in stored["old"]
    frozen = invoke(tmp_path, freeze)
    assert frozen.returncode == 0, frozen.stdout
    profile = json.loads((tmp_path / PROFILE).read_text())
    assert profile["intent_session_path"] == REQUIREMENTS and profile["intent_scope"]["excluded"] == {"old": "Fax is gone"}
    output = json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)
    assert pending_items(output) == {}, output
    history = {i["id"]: i for i in output["history"]}
    assert history["old"]["status"] == "removed" and "pending_reason" not in history["old"]
    assert history["export"]["status"] == "confirmed" and history["sync"]["status"] == "confirmed"
    assert output["excluded"] == {"old": "Fax is gone"}
    # Freezing must not weaken the original removal into a confirmable projection.
    before_restore = snapshot(tmp_path)
    refused = decide(tmp_path, [{"operation": "confirm", "id": "old", "reason": "Record existing history"}],
                     "not-a-restore")
    assert refused.returncode == 1 and "restore" in json.loads(refused.stdout)["error"], refused.stdout
    assert snapshot(tmp_path) == before_restore
    planned = invoke(tmp_path, {"operation": "plan", "nodes": [{"node_id": "deliver", "capability": "implement",
        "goal": "Deliver export and sync", "intent_ids": ["export", "sync"],
        "responsibilities": ["implementation", "documentation", "verification"], "source_inputs": ["orders.py"],
        "exit_artifacts": [".allforai/bootstrap/deliver-result.json"], "body": ATTENTION_CONTRACT_BODY}]})
    assert planned.returncode == 0, planned.stdout
    publish_contract(tmp_path, "deliver")
    for name, result in run_gates(tmp_path).items():
        assert result.returncode == 0, (name, result.stdout)
    journal = json.loads((tmp_path / JOURNAL).read_text())
    assert journal["batches"][0] == prior["batches"][0]
    assert [b["batch_id"] for b in journal["batches"]] == ["prior", "projection", "record", "local-scope"]


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("provenance", ["full-payload", "user-turn", "invalid"])
def test_legacy_removed_history_resumes_as_removed_not_as_new_work(tmp_path, host, provenance):
    """A removed legacy item with real provenance stays removed history; an invalid
    tombstone is pending, never approval; only an explicit restore revives it."""
    requirement = project(tmp_path, confirmed=True, host=host)
    removed = {"id": "sync", "revision": 1, "scope": ["orders"], "goal": "Sync orders to the warehouse",
               "business_rules": ["Nightly only"], "acceptance": ["No sync runs by day"], "status": "removed",
               "confirmation": {"source": "user", "reference": "bootstrap user turn 3",
                                "decision_id": "remove-sync-1", "reason": "Warehouse sync is out of scope"}}
    prior = None
    if provenance == "full-payload":
        # Both items cite the same journal, so it is consumed through the scoped export.
        removed["confirmation"].update(reference=REFERENCE, decision_id="prior/decisions/0")
        requirement["confirmation"].update(reference=JOURNAL + "#prior/decisions/1", decision_id="prior/decisions/1")
        prior = prior_journal(removed["goal"], "Warehouse sync is out of scope", intent=copy.deepcopy(removed))
        prior["batches"][0]["decisions"].append({"question": "Export which orders?", "chosen": requirement["goal"],
                                                 "rationale": requirement["confirmation"]["reason"],
                                                 "intent": copy.deepcopy(requirement)})
        write(tmp_path, JOURNAL, prior)
    elif provenance == "invalid":
        removed["confirmation"]["source"] = "code"
    write(tmp_path, REQUIREMENTS, {"requirements": [requirement, removed]})
    publish_contract(tmp_path)
    before = snapshot(tmp_path)
    for name, result in run_gates(tmp_path).items():  # The removed item is outside the task scope.
        assert result.returncode == 0, (name, result.stdout)
    output = json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)
    pending = pending_items(output)
    history = {i["id"]: i for i in output["history"]}
    if provenance == "invalid":
        assert list(pending) == ["sync"] and "legacy_reuse" not in pending["sync"], output
        assert pending["sync"]["pending_reason"]
    else:
        assert pending == {}, output
        assert history["sync"]["status"] == "removed" and "pending_reason" not in history["sync"]
        # A removed intention is not restored by confirm; only an explicit restore revives it.
        refused = decide(tmp_path, [{"operation": "confirm", "id": "sync", "reason": "Bring it back"}], "revive")
        assert refused.returncode == 1 and "restore" in json.loads(refused.stdout)["error"]
        assert not (tmp_path / JOURNAL).exists() or json.loads((tmp_path / JOURNAL).read_text()) == prior
        restored = decide(tmp_path, [{"operation": "restore", "id": "sync", "reason": "Warehouse sync wanted again"}],
                          "revive")
        assert restored.returncode == 0, restored.stdout
        stored = json.loads((tmp_path / REQUIREMENTS).read_text())["requirements"]
        assert [(i["id"], i["revision"], i["status"]) for i in stored] == [
            ("export", 1, "confirmed"), ("sync", 1, "removed"), ("sync", 2, "confirmed")]
        if prior:
            assert json.loads((tmp_path / JOURNAL).read_text())["batches"][0] == prior["batches"][0]
    before.pop(tmp_path / ".allforai/bootstrap/unattended-run-readiness.json", None)
    if provenance == "invalid":
        assert all(p.read_bytes() == content for p, content in before.items())
