"""A goal-only legacy journal choice never authorizes newly inferred projection fields.

Copied-CLI seam tests in temporary projects on both host copies; not host-dialogue proof.
"""
import json

import pytest

from .test_bootstrap_scope import confirm_plan, project, gate, publish_contract, write
from .test_product_intent_session import invoke, draft, decide, TOPICS, CONCEPT, JOURNAL
from .test_validate_bootstrap import ATTENTION_CONTRACT_BODY

GATES = ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py")
LOCAL = ".allforai/bootstrap/local-requirements.json"
LEGACY_CONFIRMATION = {"source": "user", "reference": JOURNAL + "#prior/decisions/0",
                       "decision_id": "prior/decisions/0", "reason": "Privacy"}


def export_item():
    return {"id": "export", "topic": "scenarios", "goal": "Export account orders", "scope": ["orders"],
            "business_rules": ["Account isolation"], "acceptance": ["Other accounts are excluded"],
            "status": "confirmed", "revision": 1, "confirmation": dict(LEGACY_CONFIRMATION)}


def goal_only_journal(goal, rationale="Privacy"):
    return {"schema_version": "1.0", "batches": [{"batch_id": "prior", "source": "user_session", "decisions": [
        {"question": "Export which orders?", "chosen": goal, "rationale": rationale}]}]}


def pending_items(output):
    return {i["id"]: i for t in output["topics"] for i in t["items"]}


def local_plan(root):
    planned = _local_plan(root)
    if planned.returncode == 0:
        confirm_plan(root, stage="plan-projection", reason="Presented the projected plan")
    return planned


def _local_plan(root):
    return invoke(root, {"operation": "plan", "nodes": [{"node_id": "export", "capability": "implement",
        "goal": "Deliver CSV export", "intent_ids": ["export"],
        "responsibilities": ["implementation", "documentation", "verification"], "source_inputs": ["orders.py"],
        "exit_artifacts": [".allforai/bootstrap/export-result.json"], "body": ATTENTION_CONTRACT_BODY}]})


def local_admit(root, item):
    (root / LOCAL).unlink()
    return invoke(root, {"operation": "admit", "route": "local-change", "goal": "Add account CSV export",
                         "areas": ["orders"], "items": [item]})


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_local_goal_only_history_exposes_unevidenced_projection_and_blocks_freeze_until_confirmed(tmp_path, host):
    project(tmp_path, host=host)
    prior = goal_only_journal("Export account orders")
    write(tmp_path, JOURNAL, prior)
    result = local_admit(tmp_path, export_item())
    assert result.returncode == 0, result.stdout
    output = json.loads(result.stdout)
    pending = pending_items(output)
    assert list(pending) == ["export"], output
    exposed = pending["export"]
    assert exposed["status"] == "pending"
    assert exposed["legacy_reuse"] == {"reference": LEGACY_CONFIRMATION["reference"], "evidenced": ["goal"],
                                       "unconfirmed": ["scope", "business_rules", "acceptance"]}
    assert "scope" in exposed["pending_reason"] and "acceptance" in exposed["pending_reason"]
    assert exposed["goal"] == "Export account orders"
    # The evidenced goal is kept for context; the local admission asks no whole-product questions.
    assert not [q for t in output["topics"] for q in t["questions"]]
    assert json.loads((tmp_path / JOURNAL).read_text()) == prior
    frozen = invoke(tmp_path, {"operation": "freeze", "include": ["export"], "exclude": {}, "batch_id": "local-scope",
                               "user_reference": "local scope turn", "reason": "Account export only"})
    assert frozen.returncode == 1, frozen.stdout
    assert json.loads((tmp_path / JOURNAL).read_text()) == prior
    assert gate(tmp_path, "validate_unattended_readiness.py").returncode == 1
    confirmed = decide(tmp_path, [{"operation": "confirm", "id": "export", "reason": "Isolation rules and acceptance approved"}],
                       "projection")
    assert confirmed.returncode == 0, confirmed.stdout
    assert pending_items(json.loads(confirmed.stdout)) == {}
    stored = json.loads((tmp_path / LOCAL).read_text())["requirements"][-1]
    assert stored["status"] == "confirmed" and "pending_reason" not in stored
    assert stored["prior_confirmation"] == LEGACY_CONFIRMATION
    assert stored["confirmation"]["reference"] == JOURNAL + "#projection/decisions/0"
    journal = json.loads((tmp_path / JOURNAL).read_text())
    assert journal["batches"][0] == prior["batches"][0]
    assert journal["batches"][1]["decisions"][0]["intent"] == stored
    frozen = invoke(tmp_path, {"operation": "freeze", "include": ["export"], "exclude": {}, "batch_id": "local-scope",
                               "user_reference": "local scope turn", "reason": "Account export only"})
    assert frozen.returncode == 0, frozen.stdout
    planned = local_plan(tmp_path)
    assert planned.returncode == 0, planned.stdout
    publish_contract(tmp_path, "export")
    for name in GATES:
        checked = gate(tmp_path, name)
        assert checked.returncode == 0, (name, checked.stdout)
    node = json.loads((tmp_path / ".allforai/bootstrap/workflow.json").read_text())["nodes"][0]
    assert node["acceptance"] == ["Other accounts are excluded"]


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_local_full_payload_history_is_reused_without_reconfirmation(tmp_path, host):
    project(tmp_path, host=host)
    item = export_item()
    prior = goal_only_journal("Export account orders")
    prior["batches"][0]["decisions"][0]["intent"] = dict(item)
    write(tmp_path, JOURNAL, prior)
    result = local_admit(tmp_path, export_item())
    assert result.returncode == 0, result.stdout
    output = json.loads(result.stdout)
    assert pending_items(output) == {}
    assert json.loads((tmp_path / LOCAL).read_text())["requirements"][0]["status"] == "confirmed"
    frozen = invoke(tmp_path, {"operation": "freeze", "include": ["export"], "exclude": {}, "batch_id": "local-scope",
                               "user_reference": "local scope turn", "reason": "Account export only"})
    assert frozen.returncode == 0, frozen.stdout
    assert local_plan(tmp_path).returncode == 0
    publish_contract(tmp_path, "export")
    for name in GATES:
        assert gate(tmp_path, name).returncode == 0
    assert json.loads((tmp_path / JOURNAL).read_text())["batches"][0] == prior["batches"][0]


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("route", ["product-reconstruction", "new-product"])
def test_product_goal_only_history_blocks_freeze_until_projection_confirmed(tmp_path, host, route):
    project(tmp_path, host=host)
    request = draft()
    request["questions"] = []
    item = request["items"][0]
    item.update(status="confirmed", revision=1, confirmation={"source": "user", "reference": JOURNAL + "#prior/decisions/0",
                "decision_id": "prior/decisions/0", "reason": "Existing explicit choice"})
    if route == "new-product":
        (tmp_path / "orders.py").unlink()
        request.update(route="new-product", facts=[])
        for entry in request["items"]:
            entry.update(origin="user-request", evidence=[])
    prior = goal_only_journal(item["goal"], "Existing explicit choice")
    write(tmp_path, JOURNAL, prior)
    result = invoke(tmp_path, request)
    assert result.returncode == 0, result.stdout
    output = json.loads(result.stdout)
    exposed = pending_items(output)["target-users"]
    assert exposed["legacy_reuse"]["evidenced"] == ["goal"]
    assert exposed["legacy_reuse"]["unconfirmed"] == ["scope", "business_rules", "acceptance"]
    stored = next(i for i in json.loads((tmp_path / CONCEPT).read_text())["requirements"] if i["id"] == "target-users")
    assert stored["status"] == "pending" and stored["confirmation"] == item["confirmation"]
    freeze = {"operation": "freeze", "include": ["target-users"], "exclude": {t: "Later scope" for t in TOPICS[1:]},
              "batch_id": "scope", "user_reference": "scope user turn", "reason": "Choose release scope"}
    assert invoke(tmp_path, freeze).returncode == 1
    assert json.loads((tmp_path / JOURNAL).read_text()) == prior
    assert decide(tmp_path, [{"operation": "confirm", "id": "target-users", "reason": "Projection approved"}],
                  "projection").returncode == 0
    stored = next(i for i in json.loads((tmp_path / CONCEPT).read_text())["requirements"] if i["id"] == "target-users")
    assert stored["prior_confirmation"] == item["confirmation"]
    frozen = invoke(tmp_path, freeze)
    assert frozen.returncode == 0, frozen.stdout
    assert json.loads((tmp_path / JOURNAL).read_text())["batches"][0] == prior["batches"][0]


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_confirmed_goal_only_history_in_stored_file_is_not_treated_as_frozen_authority(tmp_path, host):
    """A stored concept that was marked confirmed before this rule resumes as pending."""
    project(tmp_path, host=host)
    request = draft()
    request["questions"] = []
    assert invoke(tmp_path, request).returncode == 0
    concept = json.loads((tmp_path / CONCEPT).read_text())
    item = concept["requirements"][0]
    item.update(status="confirmed", confirmation={"source": "user", "reference": JOURNAL + "#prior/decisions/0",
                "decision_id": "prior/decisions/0", "reason": "Existing explicit choice"})
    write(tmp_path, CONCEPT, concept)
    write(tmp_path, JOURNAL, goal_only_journal(item["goal"], "Existing explicit choice"))
    before = (tmp_path / CONCEPT).read_bytes()
    output = json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)
    exposed = pending_items(output)["target-users"]
    assert exposed["status"] == "pending" and exposed["legacy_reuse"]["unconfirmed"] == ["scope", "business_rules", "acceptance"]
    assert (tmp_path / CONCEPT).read_bytes() == before
