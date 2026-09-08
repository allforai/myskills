"""Scripted interactive inputs through the copied bootstrap CLI, not host proof."""
import json
import subprocess
import sys

import pytest

from .test_bootstrap_scope import project, write, gate, publish_contract
from .test_validate_bootstrap import ATTENTION_CONTRACT_BODY

CONCEPT = ".allforai/product-concept/product-concept.json"
JOURNAL = ".allforai/product-concept/decision-journal.json"
TOPICS = ["target-users", "scenarios", "core-problem", "value-proposition", "business-loop", "tradeoffs"]


def invoke(root, request):
    return subprocess.run([sys.executable, str(root / ".allforai/bootstrap/scripts/product_intent.py"),
                           str(root)], input=json.dumps(request), text=True, capture_output=True, cwd=root)


def draft():
    return {"operation": "draft", "route": "product-reconstruction", "goal": "Reshape order service",
            "items": [{"id": topic, "topic": topic, "scope": ["orders"], "goal": topic + " proposed intent",
                       "business_rules": ["Isolate accounts"], "acceptance": ["Only account orders visible"],
                       "origin": "inference", "evidence": [{"path": "orders.py", "quote": "def list_orders"}],
                       "uncertainty": "Implementation cannot establish desired direction"} for topic in TOPICS],
            "facts": [{"path": "orders.py", "quote": "def list_orders"}],
            "questions": [{"id": "conflict", "topic": "tradeoffs", "question": "Should exports include archived orders?",
                           "kind": "contradiction", "depends_on": ["tradeoffs"]}]}


def decide(root, actions, batch="user-1"):
    return invoke(root, {"operation": "decide", "batch_id": batch, "topic": "Product direction",
                         "user_reference": "user turn " + batch, "actions": actions})


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("new", [False, True])
def test_revised_baseline_generates_full_applicable_plan_and_gates_reject_drift(tmp_path, host, new):
    project(tmp_path, host=host)
    request = draft()
    if new:
        (tmp_path / "orders.py").unlink()
        request.update(route="new-product", facts=[])
        for item in request["items"]:
            item.update(origin="user-request", evidence=[])
    assert invoke(tmp_path, request).returncode == 0
    actions = [{"operation": "confirm", "id": t, "reason": "Chosen direction"} for t in TOPICS[:-2]]
    actions += [{"operation": "remove", "id": "business-loop", "reason": "Unwanted legacy loop"},
                {"operation": "adjust", "id": "tradeoffs", "changes": {"goal": "Privacy before reach"}, "reason": "Customer privacy"},
                {"operation": "answer", "id": "conflict", "answer": "Exclude archived orders", "reason": "Release scope"},
                {"operation": "add", "item": {"id": "offline", "topic": "scenarios", "scope": ["orders"],
                 "goal": "Queue offline orders", "business_rules": ["Send on reconnection"],
                 "acceptance": ["Reconnect sends exactly one order"]}, "reason": "Unmet customer need"}]
    assert decide(tmp_path, actions).returncode == 0
    freeze = {"operation": "freeze", "batch_id": "scope", "user_reference": "user scope decision",
              "reason": "Release direction", "include": TOPICS[:-2] + ["tradeoffs", "offline"],
              "exclude": {"business-loop": "Remove legacy loop"}}
    assert invoke(tmp_path, freeze).returncode == 0
    plan = {"operation": "plan", "nodes": [{"node_id": "deliver-orders", "capability": "implement",
             "goal": "Deliver revised order service", "intent_ids": freeze["include"],
             "responsibilities": ["product", "technical", "implementation", "documentation", "verification"],
             "source_inputs": ["orders.py"],
             "exit_artifacts": [".allforai/bootstrap/order-verification.json"], "body": ATTENTION_CONTRACT_BODY}],
            "not_applicable": {"experience": "Headless API; no user interface in this scope"}}
    result = invoke(tmp_path, plan)
    assert result.returncode == 0, (result.stdout, result.stderr)
    publish_contract(tmp_path, "deliver-orders")  # Planned work observes its declared source before readiness.
    workflow = json.loads((tmp_path / ".allforai/bootstrap/workflow.json").read_text())
    node = workflow["nodes"][0]
    assert node["acceptance"][-1] == "Reconnect sends exactly one order"
    assert "Privacy before reach" in node["product_goals"]
    assert "business-loop" not in [r["id"] for r in node["requirement_refs"]]
    spec = (tmp_path / ".allforai/bootstrap/node-specs/deliver-orders.md").read_text()
    assert "Reconnect sends exactly one order" in spec and "Privacy before reach" in spec
    for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
        checked = gate(tmp_path, name)
        assert checked.returncode == 0, (name, checked.stdout, checked.stderr)
    spec_path = tmp_path / ".allforai/bootstrap/node-specs/deliver-orders.md"
    spec_path.write_text(spec.replace("Reconnect sends exactly one order", "Old code is sufficient"))
    rejected = gate(tmp_path, "validate_bootstrap.py")
    assert rejected.returncode == 1 and "acceptance" in rejected.stdout
    spec_path.write_text(spec)
    concept = json.loads((tmp_path / CONCEPT).read_text())
    concept["requirements"][-1]["goal"] = "Silently adopted code behavior"
    write(tmp_path, CONCEPT, concept)
    for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
        checked = gate(tmp_path, name)
        assert checked.returncode == 1 and "product" in checked.stdout.lower(), (name, checked.stdout)


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("new", [False, True])
def test_freeze_needs_explicit_scope_and_pending_exclusions(tmp_path, host, new):
    project(tmp_path, host=host)
    request = draft()
    if new:
        (tmp_path / "orders.py").unlink()
        request.update(route="new-product", facts=[])
        for item in request["items"]:
            item.update(origin="user-request", evidence=[])
    assert invoke(tmp_path, request).returncode == 0
    assert decide(tmp_path, [{"operation": "confirm", "id": t, "reason": "Chosen direction"}
                             for t in TOPICS[:-1]]).returncode == 0
    freeze = {"operation": "freeze", "batch_id": "scope-1", "user_reference": "user turn scope",
              "reason": "Release scope", "include": TOPICS[:-1], "exclude": {}}
    blocked = invoke(tmp_path, freeze)
    assert blocked.returncode == 1 and "explicit" in blocked.stdout
    assert not (tmp_path / ".allforai/product-concept/concept-baseline.json").exists()
    freeze["exclude"] = {"tradeoffs": "Decide in later release", "conflict": "Archived export is deferred"}
    result = invoke(tmp_path, freeze)
    assert result.returncode == 0, (result.stdout, result.stderr)
    baseline = json.loads((tmp_path / ".allforai/product-concept/concept-baseline.json").read_text())
    assert baseline["intent_baseline"]["version"] == 1
    assert [r["id"] for r in baseline["intent_baseline"]["requirement_refs"]] == TOPICS[:-1]
    assert baseline["intent_baseline"]["excluded"] == freeze["exclude"]
    assert "tradeoffs" in (tmp_path / CONCEPT).read_text()


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_four_explicit_operations_preserve_history_and_user_additions(tmp_path, host):
    project(tmp_path, host=host)
    assert invoke(tmp_path, draft()).returncode == 0
    source = (tmp_path / "orders.py").read_bytes()
    addition = {"id": "offline", "topic": "scenarios", "goal": "Queue orders offline",
                "scope": ["orders"], "business_rules": ["Retry once connected"],
                "acceptance": ["Queued order is sent when connectivity returns"]}
    result = decide(tmp_path, [
        {"operation": "confirm", "id": "target-users", "reason": "These are our customers"},
        {"operation": "add", "item": addition, "reason": "Customers have intermittent connectivity"},
        {"operation": "adjust", "id": "value-proposition", "changes": {"goal": "Reliable offline ordering"},
         "reason": "Reliability matters more than speed"},
        {"operation": "remove", "id": "business-loop", "reason": "Drop the old loop"},
    ])
    assert result.returncode == 0, (result.stdout, result.stderr)
    concept = json.loads((tmp_path / CONCEPT).read_text())
    items = concept["requirements"]
    assert [i["status"] for i in items if i["id"] == "value-proposition"] == ["superseded", "confirmed"]
    offline = next(i for i in items if i["id"] == "offline")
    assert offline["origin"] == "user-request" and not offline.get("evidence")
    assert offline["confirmation"]["reference"] == JOURNAL + "#user-1/decisions/1"
    assert next(i for i in items if i["id"] == "business-loop")["status"] == "removed"
    assert (tmp_path / "orders.py").read_bytes() == source
    resumed = json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)
    assert [t["topic"] for t in resumed["topics"]] == ["scenarios", "core-problem", "tradeoffs"]
    before = (tmp_path / JOURNAL).read_bytes()
    assert decide(tmp_path, [], batch="silent").returncode == 0
    assert (tmp_path / JOURNAL).read_bytes() == before


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_draft_is_provisional_and_resume_only_presents_pending_topics(tmp_path, host):
    project(tmp_path, host=host)
    source = (tmp_path / "orders.py").read_bytes()
    result = invoke(tmp_path, draft())
    assert result.returncode == 0, (result.stdout, result.stderr)
    output = json.loads(result.stdout)
    assert output["status"] == "discussion"
    assert [t["topic"] for t in output["topics"]] == TOPICS
    concept = json.loads((tmp_path / CONCEPT).read_text())
    assert all(i["status"] == "pending" for i in concept["requirements"])
    assert not (tmp_path / ".allforai/product-concept/concept-baseline.json").exists()
    assert (tmp_path / "orders.py").read_bytes() == source
    resumed = invoke(tmp_path, {"operation": "resume"})
    assert json.loads(resumed.stdout) == output
    assert gate(tmp_path, "validate_unattended_readiness.py").returncode == 1


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_pending_dependency_cannot_be_excluded_to_authorize_dependent_intent(tmp_path, host):
    project(tmp_path, host=host)
    assert invoke(tmp_path, draft()).returncode == 0
    assert decide(tmp_path, [{"operation": "confirm", "id": t, "reason": "Chosen direction"} for t in TOPICS]).returncode == 0
    result = invoke(tmp_path, {"operation": "freeze", "include": TOPICS,
                              "exclude": {"conflict": "Ignore question"}, "batch_id": "scope",
                              "user_reference": "user turn", "reason": "Release"})
    assert result.returncode == 1 and "depends" in result.stdout


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_invalid_batch_leaves_prior_authority_unchanged(tmp_path, host):
    project(tmp_path, host=host)
    assert invoke(tmp_path, draft()).returncode == 0
    before = (tmp_path / CONCEPT).read_bytes()
    result = decide(tmp_path, [{"operation": "confirm", "id": "target-users", "reason": "Chosen"},
                              {"operation": "adjust", "id": "tradeoffs", "changes": {"goal": ""}, "reason": "Invalid"}])
    assert result.returncode == 1
    assert (tmp_path / CONCEPT).read_bytes() == before
    assert not (tmp_path / JOURNAL).exists()


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_missing_dimensions_are_pending_gaps_and_bad_evidence_is_rejected(tmp_path, host):
    project(tmp_path, host=host)
    request = draft()
    request["items"] = request["items"][:1]
    request["items"][0]["evidence"][0]["quote"] = "invented evidence"
    rejected = invoke(tmp_path, request)
    assert rejected.returncode == 1 and "Evidence" in rejected.stdout
    assert not (tmp_path / CONCEPT).exists()
    request["items"][0]["evidence"][0]["quote"] = "def list_orders"
    result = invoke(tmp_path, request)
    assert result.returncode == 0
    output = json.loads(result.stdout)
    gaps = [q["id"] for t in output["topics"] for q in t["questions"] if q["kind"] == "gap"]
    assert gaps == ["gap-" + t for t in TOPICS[1:]]


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_existing_canonical_user_choice_is_reused_without_new_intent_decision(tmp_path, host):
    project(tmp_path, host=host)
    request = draft()
    request["questions"] = []
    assert invoke(tmp_path, request).returncode == 0
    concept = json.loads((tmp_path / CONCEPT).read_text())
    item = concept["requirements"][0]
    item.update(status="confirmed", confirmation={"source": "user", "reference": JOURNAL + "#prior/decisions/0",
                "decision_id": "prior/decisions/0", "reason": "Existing explicit choice"})
    write(tmp_path, CONCEPT, concept)
    # Reuse without a new decision needs the complete recorded payload; a goal-only
    # choice is exposed for projection confirmation (test_legacy_projection_authority).
    prior = {"batch_id": "prior", "source": "user_session", "topic": "Users", "decisions": [
        {"question": "Who are our customers?", "chosen": item["goal"], "rationale": "Existing explicit choice",
         "intent": dict(item)}]}
    write(tmp_path, JOURNAL, {"schema_version": "1.0", "batches": [prior]})
    result = invoke(tmp_path, {"operation": "freeze", "include": ["target-users"],
        "exclude": {t: "Later scope" for t in TOPICS[1:]}, "batch_id": "scope",
        "user_reference": "scope user turn", "reason": "Choose release scope"})
    assert result.returncode == 0, (result.stdout, result.stderr)
    journal = json.loads((tmp_path / JOURNAL).read_text())
    assert journal["batches"][0] == prior
    assert len(journal["batches"]) == 2


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_resume_raises_legacy_inference_as_missing_confirmation(tmp_path, host):
    project(tmp_path, host=host)
    assert invoke(tmp_path, draft()).returncode == 0
    concept = json.loads((tmp_path / CONCEPT).read_text())
    concept["requirements"][0].update(status="confirmed", confirmation={"source": "code", "confidence": "high"})
    write(tmp_path, CONCEPT, concept)
    before = (tmp_path / CONCEPT).read_bytes()
    result = invoke(tmp_path, {"operation": "resume"})
    output = json.loads(result.stdout)
    assert output["topics"][0]["topic"] == "target-users"
    assert output["topics"][0]["items"][0]["status"] == "pending"
    assert (tmp_path / CONCEPT).read_bytes() == before
