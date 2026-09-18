"""Experience direction through the copied product-intent CLI and gates; no host proof.

The user picks the product's experience direction from the model's proposals.
These tests drive that choice through the generated project's own scripts, so
both host copies (the Codex tests directory is a symlink to this one) prove the
same seams.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from ..module_isolation import load
from .test_bootstrap_scope import confirm_plan, gate, project, publish_contract
from .test_product_intent_session import CONCEPT, JOURNAL, TOPICS, decide, draft, invoke
from .test_validate_bootstrap import ATTENTION_CONTRACT_BODY

EXPERIENCE_TOPIC = "experience-direction"
BASELINE = ".allforai/product-concept/concept-baseline.json"
PROFILE = ".allforai/bootstrap/bootstrap-profile.json"
TEMPLATE = Path(__file__).resolve().parents[2] / "knowledge/orchestrator-template.md"
PROTOCOL = Path(__file__).resolve().parents[2] / "knowledge/product-intent-confirmation.md"
GATES =("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py")
DIRECTION_BLOCKER = "ui_product_without_experience_direction"
# Mirror of the proposal key set the script accepts; the wording of every value stays
# clear of interface terms so the same fixtures can reach the gates in later units.
TEXT_FIELDS = ("id", "title", "who", "circumstance", "core_loop_feel", "first_minute", "return_reason", "goal")
LIST_FIELDS = ("anti_goals", "tradeoffs", "scope", "business_rules", "acceptance")
RATIONALE = "The unhurried pass fits the tired last half hour better than a race"


def script(root):
    """The copied CLI as a module, to read the constants the generated project really ships."""
    path = root / ".allforai/bootstrap/scripts/product_intent.py"
    spec = importlib.util.spec_from_file_location("copied_product_intent", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cli(root, *args):
    """The copied CLI driven by plain arguments, the way a read-only entry is reached."""
    return subprocess.run([sys.executable, str(root / ".allforai/bootstrap/scripts/product_intent.py"),
                           str(root), *args], text=True, capture_output=True, cwd=root)


def new_product_draft():
    """`draft()` for a product without source and without a proposed experience direction."""
    request = draft()
    request.update(route="new-product", facts=[], questions=[],
                   items=[dict(item, origin="user-request", evidence=[])
                          for item in request["items"] if item["topic"] != EXPERIENCE_TOPIC])
    return request


def drafted(root, host):
    """A new-product session waiting for its experience direction."""
    project(root, host=host)
    (root / "orders.py").unlink()
    result = invoke(root, new_product_draft())
    assert result.returncode == 0, (result.stdout, result.stderr)
    return [topic for topic in TOPICS if topic != EXPERIENCE_TOPIC]


def proposal(identity, **overrides):
    """One complete experience proposal, worded without any interface term."""
    value = {"id": identity, "title": identity.replace("-", " ") + " direction",
             "who": "A shopkeeper settling the day's orders alone",
             "circumstance": "The last half hour of a shift, tired and interrupted",
             "core_loop_feel": "One unhurried pass that ends with nothing left open",
             "first_minute": "The oldest unsettled order is already waiting, nothing else asked",
             "return_reason": "Tomorrow starts from yesterday's settled state",
             "goal": "Settle the day's orders in one unhurried pass",
             "anti_goals": ["Never ask for a decision the shopkeeper cannot make yet"],
             "tradeoffs": ["Fewer choices at once in exchange for an unbroken pass"],
             "scope": ["orders"],
             "business_rules": ["Only the signed-in account's orders are settled"],
             "acceptance": ["A settled day reopens with no order left unsettled"],
             "comparable": {"product": "A paper day book",
                            "approach": "One line per order, closed with a single stroke"}}
    value.update(overrides)
    return value


def propose_request(proposals, recommended="calm-pass", rationale=RATIONALE):
    return {"operation": "propose", "proposals": proposals,
            "recommended_id": recommended, "rationale": rationale}


def propose(root, ids=("calm-pass", "quick-burst"), recommended="calm-pass", rationale=RATIONALE):
    return invoke(root, propose_request([proposal(i) for i in ids], recommended, rationale))


def direction(output):
    """The discussion entry for the experience-direction topic."""
    entries = [topic for topic in output["topics"] if topic["topic"] == EXPERIENCE_TOPIC]
    assert len(entries) == 1, output["topics"]
    return entries[0]


def set_mode(root, mode="consumer",
             reason="Shopkeepers settle their own orders; the product is theirs to live with"):
    """Record the experience priority bootstrap classified, in the profile's own shape."""
    path = root / PROFILE
    profile = json.loads(path.read_text())
    profile["experience_priority"] = {"mode": mode, "reason": reason}
    path.write_text(json.dumps(profile), encoding="utf-8")


def chosen_item(identity="calm-pass", batch="user-1", index=0, reason="Chosen direction", **extra):
    """The experience-direction intent a `select` of that proposal must produce, field for field."""
    offered = proposal(identity)
    fragment = batch + "/decisions/" + str(index)
    item = {"id": EXPERIENCE_TOPIC + "-" + identity, "topic": EXPERIENCE_TOPIC, "goal": offered["goal"],
            "scope": offered["scope"], "business_rules": offered["business_rules"],
            "acceptance": offered["acceptance"], "revision": 1, "origin": "model-proposal",
            "evidence": [], "status": "confirmed", "proposal_id": identity,
            "who": offered["who"], "circumstance": offered["circumstance"],
            "confirmation": {"source": "user", "reference": JOURNAL + "#" + fragment,
                             "decision_id": fragment, "reason": reason,
                             "user_reference": "user turn " + batch}}
    item.update(extra)
    return item


def plan_request(include, node_id="deliver-orders"):
    """One node that carries the whole frozen scope through every applicable stage.

    A product whose `experience_priority.mode` is `consumer` may not declare the
    experience stage inapplicable, so the node owns it like any other stage.
    """
    return {"operation": "plan", "nodes": [
        {"node_id": node_id, "capability": "implement", "goal": "Deliver the settled-day order service",
         "intent_ids": list(include), "source_inputs": ["orders.py"],
         "responsibilities": ["product", "experience", "technical", "implementation",
                              "documentation", "verification"],
         "exit_artifacts": [".allforai/bootstrap/order-verification.json"], "body": ATTENTION_CONTRACT_BODY}]}


def headless_plan_request(include):
    """`plan_request` for a product nobody looks at, which may leave the experience stage out."""
    request = plan_request(include)
    request["not_applicable"] = {"experience": "A headless order service; nobody ever sees a screen"}
    node = request["nodes"][0]
    node["responsibilities"] = [r for r in node["responsibilities"] if r != "experience"]
    return request


def freeze_request(include, batch="scope"):
    return {"operation": "freeze", "batch_id": batch, "user_reference": "user scope turn",
            "reason": "Release the chosen direction", "include": list(include), "exclude": {}}


def without_direction(root, host, *, headless=False):
    """A product frozen, planned and published with the direction question left open.

    The profile still classifies the product as `none` throughout, so the whole scope is
    built while the blocker cannot apply; a later classification is the only thing that
    turns it on, and nothing about the record itself changes when it does.
    """
    topics = drafted(root, host)
    confirmed = decide(root, [{"operation": "confirm", "id": topic, "reason": "Chosen direction"}
                              for topic in topics])
    assert confirmed.returncode == 0, (confirmed.stdout, confirmed.stderr)
    frozen = invoke(root, dict(freeze_request(topics),
                               exclude={"gap-" + EXPERIENCE_TOPIC: "No direction has been offered yet"}))
    assert frozen.returncode == 0, (frozen.stdout, frozen.stderr)
    planned = invoke(root, headless_plan_request(topics) if headless else plan_request(topics))
    assert planned.returncode == 0, (planned.stdout, planned.stderr)
    confirm_plan(root, stage="plan-projection", reason="Presented the projected plan")
    publish_contract(root, "deliver-orders")
    return topics


def verdicts(root):
    """What each public gate says about the project as it stands."""
    return {name: gate(root, name) for name in GATES}


def rejections():
    """Every proposal request the contract rejects, with the reason it is offered."""
    cases = [("one direction is no choice", propose_request([proposal("calm-pass")])),
             ("four directions exceed the round",
              propose_request([proposal(i) for i in ("calm-pass", "quick-burst", "third", "fourth")])),
             ("the same identity twice",
              propose_request([proposal("calm-pass"), proposal("calm-pass")], "calm-pass")),
             ("a recommendation outside the round",
              propose_request([proposal("calm-pass"), proposal("quick-burst")], "neither-of-them")),
             ("an empty rationale", propose_request([proposal("calm-pass"), proposal("quick-burst")],
                                                    rationale="   "))]
    for field in TEXT_FIELDS:
        missing = proposal("quick-burst")
        missing.pop(field)
        cases.append(("missing " + field, propose_request([proposal("calm-pass"), missing])))
        cases.append(("blank " + field,
                      propose_request([proposal("calm-pass"), proposal("quick-burst", **{field: " "})])))
    for field in LIST_FIELDS:
        missing = proposal("quick-burst")
        missing.pop(field)
        cases.append(("missing " + field, propose_request([proposal("calm-pass"), missing])))
        cases.append(("empty " + field,
                      propose_request([proposal("calm-pass"), proposal("quick-burst", **{field: []})])))
        cases.append(("blank entry in " + field,
                      propose_request([proposal("calm-pass"), proposal("quick-burst", **{field: [" "]})])))
    dropped = proposal("quick-burst")
    dropped.pop("comparable")
    cases.append(("missing comparable", propose_request([proposal("calm-pass"), dropped])))
    for sub in ("product", "approach"):
        half = {k: v for k, v in proposal("quick-burst")["comparable"].items() if k != sub}
        cases.append(("comparable without " + sub,
                      propose_request([proposal("calm-pass"), proposal("quick-burst", comparable=half)])))
    for key, value in (("origin", "user-request"), ("status", "confirmed"), ("recommended", True),
                       ("round", 1), ("confirmation", {"source": "user"})):
        cases.append(("smuggled " + key,
                      propose_request([proposal("calm-pass"), proposal("quick-burst", **{key: value})])))
    return cases


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_topic_is_listed_before_tradeoffs_and_missing_direction_is_a_gap(tmp_path, host):
    project(tmp_path, host=host)
    module = script(tmp_path)
    assert list(module.TOPICS) == TOPICS
    assert module.EXPERIENCE_TOPIC == EXPERIENCE_TOPIC
    assert TOPICS[TOPICS.index("tradeoffs") - 1] == EXPERIENCE_TOPIC
    (tmp_path / "orders.py").unlink()
    result = invoke(tmp_path, new_product_draft())
    assert result.returncode == 0, (result.stdout, result.stderr)
    output = json.loads(result.stdout)
    presented = [topic["topic"] for topic in output["topics"]]
    assert presented.index(EXPERIENCE_TOPIC) == presented.index("tradeoffs") - 1
    gaps = [question["id"] for topic in output["topics"] for question in topic["questions"]
            if question["kind"] == "gap"]
    assert "gap-" + EXPERIENCE_TOPIC in gaps


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_propose_validates_count_recommendation_and_fields(tmp_path, host):
    """Nothing is stored until the whole round is valid, and no host field carries authority."""
    drafted(tmp_path, host)
    for label, request in rejections():
        before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
        result = invoke(tmp_path, request)
        assert result.returncode == 1, (label, result.stdout, result.stderr)
        assert not result.stderr, label
        assert json.loads(result.stdout)["status"] == "blocked", label
        assert all(p.read_bytes() == content for p, content in before.items()), label
        assert "experience_proposals" not in json.loads((tmp_path / CONCEPT).read_text()), label
        assert not (tmp_path / JOURNAL).exists(), label
    accepted = propose(tmp_path)
    assert accepted.returncode == 0, (accepted.stdout, accepted.stderr)


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_propose_stores_rounds_without_journal_and_resume_presents_current_round(tmp_path, host):
    """A fresh round replaces the offer on the table without erasing what was offered before."""
    undrafted = tmp_path / "undrafted"
    project(undrafted, host=host)
    refused = propose(undrafted)
    assert refused.returncode == 1, (refused.stdout, refused.stderr)
    assert not refused.stderr
    assert json.loads(refused.stdout)["error"] == ("Experience proposals belong to a product session; "
                                                   "draft the product first")
    assert not (undrafted / CONCEPT).exists()

    drafted(tmp_path, host)
    plain = json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)
    assert "experience_proposals" not in plain
    assert all("proposals" not in topic for topic in plain["topics"])

    first = propose(tmp_path)
    assert first.returncode == 0, (first.stdout, first.stderr)
    assert not (tmp_path / JOURNAL).exists()
    opened = json.loads((tmp_path / CONCEPT).read_text())["experience_proposals"]
    assert [(p["id"], p["round"]) for p in opened] == [("calm-pass", 1), ("quick-burst", 1)]
    assert direction(json.loads(first.stdout))["proposals"] == opened

    second = "The steady ledger asks less of a tired shopkeeper than the burst ever will"
    again = propose(tmp_path, ids=("steady-ledger", "wide-sweep"), recommended="steady-ledger", rationale=second)
    assert again.returncode == 0, (again.stdout, again.stderr)
    assert not (tmp_path / JOURNAL).exists()
    stored = json.loads((tmp_path / CONCEPT).read_text())["experience_proposals"]
    assert stored[:2] == opened, "an earlier round stays readable exactly as it was offered"
    assert [(p["id"], p["round"]) for p in stored[2:]] == [("steady-ledger", 2), ("wide-sweep", 2)]

    resumed = json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)
    assert resumed == json.loads(again.stdout)
    assert resumed["experience_proposals"] == stored
    offered = direction(resumed)
    assert offered["proposals"] == stored[2:], "only the current round is on the table"
    assert offered["recommended_id"] == "steady-ledger" and offered["rationale"] == second
    assert all("proposals" not in t for t in resumed["topics"] if t["topic"] != EXPERIENCE_TOPIC)

    answered = decide(tmp_path, [{"operation": "answer", "id": "gap-" + EXPERIENCE_TOPIC,
                                  "answer": "steady ledger direction", "reason": "Still weighing the two"}])
    assert answered.returncode == 0, (answered.stdout, answered.stderr)
    settled = direction(json.loads(invoke(tmp_path, {"operation": "resume"}).stdout))
    assert not settled["items"] and not settled["questions"], "nothing is pending under the topic any more"
    assert settled["proposals"] == stored[2:], "an unanswered offer keeps its topic on the table"


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("collision", ["intent", "question", "earlier-round"])
def test_proposal_identity_is_unique_across_proposals_intents_and_questions(tmp_path, host, collision):
    """A proposal identity is separate from every intent and question identity, in every round."""
    drafted(tmp_path, host)
    taken = "tradeoffs" if collision == "intent" else "gap-" + EXPERIENCE_TOPIC
    if collision == "earlier-round":
        first = propose(tmp_path)
        assert first.returncode == 0, (first.stdout, first.stderr)
        taken = "calm-pass"
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = invoke(tmp_path, propose_request([proposal(taken), proposal("quick-burst")], taken))
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert not result.stderr
    assert json.loads(result.stdout)["error"] == ("Proposal identities must be unique and separate from "
                                                  "intent and question identities")
    assert all(p.read_bytes() == content for p, content in before.items())
    assert not (tmp_path / JOURNAL).exists()


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_proposal_cannot_be_confirmed_or_frozen(tmp_path, host):
    """Proposals live outside `requirements[]`, so no user decision can reach one."""
    topics = drafted(tmp_path, host)
    result = propose(tmp_path)
    assert result.returncode == 0, (result.stdout, result.stderr)
    stored = json.loads((tmp_path / CONCEPT).read_text())["experience_proposals"]
    assert [p["id"] for p in stored] == ["calm-pass", "quick-burst"]
    assert all(p["origin"] == "model-proposal" and p["round"] == 1 for p in stored)
    assert [p["id"] for p in stored if p["recommended"]] == ["calm-pass"]
    assert stored[0]["rationale"] == RATIONALE and "rationale" not in stored[1]
    assert stored[1]["comparable"] == proposal("quick-burst")["comparable"]
    assert not (tmp_path / JOURNAL).exists()

    confirmed = decide(tmp_path, [{"operation": "confirm", "id": "calm-pass", "reason": "I like this one"}])
    assert confirmed.returncode == 1, (confirmed.stdout, confirmed.stderr)
    assert not confirmed.stderr and not (tmp_path / JOURNAL).exists()

    assert decide(tmp_path, [{"operation": "confirm", "id": topic, "reason": "Chosen direction"}
                             for topic in topics]).returncode == 0
    freeze = {"operation": "freeze", "batch_id": "scope", "user_reference": "user scope turn",
              "reason": "Release direction", "include": topics + ["calm-pass"],
              "exclude": {"gap-" + EXPERIENCE_TOPIC: "Still choosing the direction"}}
    blocked = invoke(tmp_path, freeze)
    assert blocked.returncode == 1, (blocked.stdout, blocked.stderr)
    assert not blocked.stderr and not (tmp_path / BASELINE).exists()


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_selected_direction_freezes_and_passes_all_public_gates(tmp_path, host):
    """A picked direction is the user's own confirmed intent, and it survives every gate.

    The item is the proposal's product meaning verbatim, journal-backed like any other
    decision, so the frozen scope carries it and its acceptance reaches the node.
    """
    topics = drafted(tmp_path, host)
    set_mode(tmp_path)
    assert propose(tmp_path).returncode == 0
    reason = "The tired last half hour is the one that decides whether the day closes"
    actions = [{"operation": "select", "proposal_id": "calm-pass", "reason": reason},
               {"operation": "answer", "id": "gap-" + EXPERIENCE_TOPIC,
                "answer": "The calm pass direction", "reason": "The direction is now chosen"}]
    actions += [{"operation": "confirm", "id": topic, "reason": "Chosen direction"} for topic in topics]
    decided = decide(tmp_path, actions)
    assert decided.returncode == 0, (decided.stdout, decided.stderr)

    expected = chosen_item(reason=reason)
    identity = expected["id"]
    concept = json.loads((tmp_path / CONCEPT).read_text())
    assert [i for i in concept["requirements"] if i["id"] == identity] == [expected]
    batch = json.loads((tmp_path / JOURNAL).read_text())["batches"][-1]
    assert batch["decisions"][0] == {"question": identity, "chosen": expected["goal"], "rationale": reason,
                                     "operation": "select", "supersedes": None, "intent": expected}

    include = topics + [identity]
    frozen = invoke(tmp_path, freeze_request(include))
    assert frozen.returncode == 0, (frozen.stdout, frozen.stderr)
    baseline = json.loads((tmp_path / BASELINE).read_text())["intent_baseline"]
    assert expected in baseline["intents"]
    planned = invoke(tmp_path, plan_request(include))
    assert planned.returncode == 0, (planned.stdout, planned.stderr)
    confirm_plan(tmp_path, stage="plan-projection", reason="Presented the projected plan")
    publish_contract(tmp_path, "deliver-orders")
    node = json.loads((tmp_path / ".allforai/bootstrap/workflow.json").read_text())["nodes"][0]
    assert expected["goal"] in node["product_goals"]
    assert expected["acceptance"][0] in node["acceptance"], "the direction's acceptance is node acceptance"
    for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
        checked = gate(tmp_path, name)
        assert checked.returncode == 0, (name, checked.stdout, checked.stderr)


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_select_then_adjust_in_one_batch_keeps_revision_lineage(tmp_path, host):
    """Wording the chosen direction in the user's own words is the existing revision chain."""
    topics = drafted(tmp_path, host)
    set_mode(tmp_path)
    assert propose(tmp_path).returncode == 0
    sharper = "Settle the day's orders in one unhurried pass that never reopens tomorrow"
    actions = [{"operation": "select", "proposal_id": "calm-pass", "reason": "This is the pass I want"},
               {"operation": "adjust", "id": EXPERIENCE_TOPIC + "-calm-pass",
                "changes": {"goal": sharper}, "reason": "Said in the shopkeeper's own words"},
               {"operation": "answer", "id": "gap-" + EXPERIENCE_TOPIC,
                "answer": "The calm pass direction, reworded", "reason": "The direction is now chosen"}]
    actions += [{"operation": "confirm", "id": topic, "reason": "Chosen direction"} for topic in topics]
    decided = decide(tmp_path, actions)
    assert decided.returncode == 0, (decided.stdout, decided.stderr)

    identity = EXPERIENCE_TOPIC + "-calm-pass"
    lineage = [i for i in json.loads((tmp_path / CONCEPT).read_text())["requirements"] if i["id"] == identity]
    assert [(i["revision"], i["status"]) for i in lineage] == [(1, "superseded"), (2, "confirmed")]
    first, second = lineage
    assert first == dict(chosen_item(reason="This is the pass I want"), status="superseded")
    assert second == dict(chosen_item(reason="Said in the shopkeeper's own words", index=1),
                          goal=sharper, revision=2, supersedes={"id": identity, "revision": 1})
    assert second["origin"] == "model-proposal" and second["proposal_id"] == "calm-pass"

    frozen = invoke(tmp_path, freeze_request(topics + [identity]))
    assert frozen.returncode == 0, (frozen.stdout, frozen.stderr)
    baseline = json.loads((tmp_path / BASELINE).read_text())["intent_baseline"]
    assert [r for r in baseline["requirement_refs"] if r["id"] == identity] == [
        {"path": CONCEPT, "id": identity, "revision": 2}]


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_select_needs_a_current_round_proposal_and_a_free_direction_slot(tmp_path, host):
    """Nothing can be chosen off the table, from an old table, or on top of a standing choice."""
    drafted(tmp_path, host)
    set_mode(tmp_path)

    def refused(action, message, batch):
        before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
        result = decide(tmp_path, [action], batch=batch)
        assert result.returncode == 1, (message, result.stdout, result.stderr)
        assert not result.stderr, message
        assert json.loads(result.stdout)["error"] == message, message
        assert all(p.read_bytes() == content for p, content in before.items()), message

    refused({"operation": "select", "proposal_id": "calm-pass", "reason": "Before anything was offered"},
            "No current experience proposals; propose before select or delegate", "too-early")
    assert propose(tmp_path).returncode == 0
    assert propose(tmp_path, ids=("steady-ledger", "wide-sweep"), recommended="steady-ledger",
                   rationale="The steady ledger asks less of a tired shopkeeper").returncode == 0
    refused({"operation": "select", "proposal_id": "calm-pass", "reason": "The earlier round read better"},
            "Select one proposal of the current round", "old-round")
    refused({"operation": "select", "proposal_id": "never-offered", "reason": "Something else entirely"},
            "Select one proposal of the current round", "unoffered")

    taken = decide(tmp_path, [{"operation": "select", "proposal_id": "steady-ledger",
                               "reason": "The steady ledger it is"}], batch="chosen")
    assert taken.returncode == 0, (taken.stdout, taken.stderr)
    refused({"operation": "select", "proposal_id": "wide-sweep", "reason": "Second thoughts"},
            "An experience direction is already selected; remove it before choosing another", "second")


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_delegate_records_the_recommended_proposal_as_an_auto_decision(tmp_path, host):
    """"You decide" takes the recommendation and says on the record that it did.

    The direction is still the user's own confirmed intent, so it is the proposal's
    product meaning verbatim and it freezes like any other. What separates it from a
    pick is written down, not inferred: `auto_decided` on the item and `delegated` on
    the batch stamp, so a later reader can tell whose judgement chose this direction.
    """
    topics = drafted(tmp_path, host)
    set_mode(tmp_path)
    assert propose(tmp_path).returncode == 0
    reason = "The tired half hour is read better here than the shopkeeper can read it tonight"
    actions = [{"operation": "delegate", "reason": reason},
               {"operation": "answer", "id": "gap-" + EXPERIENCE_TOPIC,
                "answer": "The pick was handed back to the model", "reason": "The direction is now chosen"}]
    actions += [{"operation": "confirm", "id": topic, "reason": "Chosen direction"} for topic in topics]
    decided = decide(tmp_path, actions, batch="handed-over")
    assert decided.returncode == 0, (decided.stdout, decided.stderr)

    expected = chosen_item(batch="handed-over", reason=reason, auto_decided=True)
    expected["confirmation"]["delegated"] = True
    identity = expected["id"]
    assert identity == EXPERIENCE_TOPIC + "-calm-pass", "the recommended proposal, not the other one"
    concept = json.loads((tmp_path / CONCEPT).read_text())
    assert [i for i in concept["requirements"] if i.get("proposal_id")] == [expected]
    stood = [i for i in concept["requirements"] if i["id"] == identity][0]
    offered = [p for p in concept["experience_proposals"] if p["id"] == "calm-pass"][0]
    for field in ("goal", "scope", "business_rules", "acceptance", "who", "circumstance"):
        assert stood[field] == offered[field], field
    assert stood["auto_decided"] is True
    assert stood["confirmation"]["delegated"] is True
    assert stood["confirmation"]["user_reference"] == "user turn handed-over"

    batch = json.loads((tmp_path / JOURNAL).read_text())["batches"][-1]
    assert batch["user_reference"] == "user turn handed-over"
    assert batch["decisions"][0] == {"question": identity, "chosen": expected["goal"], "rationale": reason,
                                     "operation": "delegate", "supersedes": None, "intent": expected}

    frozen = invoke(tmp_path, freeze_request(topics + [identity]))
    assert frozen.returncode == 0, (frozen.stdout, frozen.stderr)
    baseline = json.loads((tmp_path / BASELINE).read_text())["intent_baseline"]
    assert expected in baseline["intents"]


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_delegate_and_select_need_a_current_proposal_round(tmp_path, host):
    """No round on the table is nothing to hand back, and a delegation names nothing.

    Handing the pick back is trust in the recommendation that was actually offered;
    without an offer there is no decision to make, and a `proposal_id` riding along
    with `delegate` would be a pick wearing a delegation's clothes.
    """
    drafted(tmp_path, host)
    set_mode(tmp_path)

    def refused(action, message, batch):
        before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
        result = decide(tmp_path, [action], batch=batch)
        assert result.returncode == 1, (message, result.stdout, result.stderr)
        assert not result.stderr, message
        assert json.loads(result.stdout)["error"] == message, message
        assert all(p.read_bytes() == content for p, content in before.items()), message
        assert not (tmp_path / JOURNAL).exists(), message

    empty = "No current experience proposals; propose before select or delegate"
    refused({"operation": "delegate", "reason": "You decide, nothing has been offered yet"},
            empty, "delegate-too-early")
    refused({"operation": "select", "proposal_id": "calm-pass", "reason": "Picking off an empty table"},
            empty, "select-too-early")

    assert propose(tmp_path).returncode == 0
    refused({"operation": "delegate", "proposal_id": "quick-burst", "reason": "You decide, but take this one"},
            "Delegate takes the recommended proposal; use select to name one", "named")
    refused({"operation": "delegate", "proposal_id": "calm-pass", "reason": "You decide, and it is the one you like"},
            "Delegate takes the recommended proposal; use select to name one", "named-recommended")


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_delegate_records_auto_decision_and_is_disclosed(tmp_path, host):
    """A handed-over pick is read back out loud, from the turn that handed it over.

    Disclosure is what `auto_decided` is written down for: `--delegations` reads the
    concept and nothing else, so a run can say at any point whose judgement chose the
    direction without moving a byte of the record. It follows the revision chain back
    to the delegation, because the user's own later rewording is their turn and must
    never be reported as the turn that handed the pick away.
    """
    topics = drafted(tmp_path, host)
    set_mode(tmp_path)
    assert propose(tmp_path).returncode == 0
    reason = "The tired half hour is read better here than the shopkeeper can read it tonight"
    actions = [{"operation": "delegate", "reason": reason},
               {"operation": "answer", "id": "gap-" + EXPERIENCE_TOPIC,
                "answer": "The pick was handed back to the model", "reason": "The direction is now chosen"}]
    actions += [{"operation": "confirm", "id": topic, "reason": "Chosen direction"} for topic in topics]
    decided = decide(tmp_path, actions, batch="handed-over")
    assert decided.returncode == 0, (decided.stdout, decided.stderr)
    identity = EXPERIENCE_TOPIC + "-calm-pass"
    stood = [i for i in json.loads((tmp_path / CONCEPT).read_text())["requirements"] if i["id"] == identity][0]
    assert stood["auto_decided"] is True and stood["confirmation"]["delegated"] is True

    handed = {"id": identity, "revision": 1, "proposal_id": "calm-pass",
              "proposal_title": proposal("calm-pass")["title"],
              "user_reference": "user turn handed-over", "reason": reason}
    before = {path: (tmp_path / path).read_bytes() for path in (CONCEPT, JOURNAL)}
    disclosed = cli(tmp_path, "--delegations")
    assert disclosed.returncode == 0, (disclosed.stdout, disclosed.stderr)
    assert not disclosed.stderr
    assert json.loads(disclosed.stdout) == {"status": "delegations", "delegations": [handed]}
    assert all((tmp_path / path).read_bytes() == content for path, content in before.items()), \
        "disclosure reads the record and never writes to it"

    sharper = "Settle the day's orders in one unhurried pass that never reopens tomorrow"
    reworded = decide(tmp_path, [{"operation": "adjust", "id": identity, "changes": {"goal": sharper},
                                  "reason": "Said in the shopkeeper's own words"}], batch="reworded")
    assert reworded.returncode == 0, (reworded.stdout, reworded.stderr)
    again = cli(tmp_path, "--delegations")
    assert again.returncode == 0, (again.stdout, again.stderr)
    assert json.loads(again.stdout)["delegations"] == [dict(handed, revision=2)], \
        "a rewording of a delegated direction is the user's turn, not the delegation's"

    picked = tmp_path / "picked"
    project(picked, host=host)
    absent = cli(picked, "--delegations")
    assert absent.returncode == 0, (absent.stdout, absent.stderr)
    assert json.loads(absent.stdout) == {"status": "delegations", "delegations": []}, \
        "a session with no concept yet has nothing to disclose"
    (picked / "orders.py").unlink()
    assert invoke(picked, new_product_draft()).returncode == 0
    assert propose(picked).returncode == 0
    chosen = decide(picked, [{"operation": "select", "proposal_id": "calm-pass",
                              "reason": "The shopkeeper read both directions and picked one"}], batch="own-pick")
    assert chosen.returncode == 0, (chosen.stdout, chosen.stderr)
    silent = cli(picked, "--delegations")
    assert silent.returncode == 0, (silent.stdout, silent.stderr)
    assert json.loads(silent.stdout)["delegations"] == [], "a direction the user picked is nobody's delegation"


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_ui_product_without_direction_is_blocked_at_every_gate(tmp_path, host):
    """A product with end users may not be built around a direction nobody ever chose.

    The scope here froze, planned and published while the product was still classified
    headless, so nothing in the record is malformed. The moment bootstrap says the
    product has end users, the same record is missing the one intent that says what
    living with it feels like, and every public gate says so before any work starts.
    """
    topics = without_direction(tmp_path, host)
    for name, result in verdicts(tmp_path).items():
        assert result.returncode == 0, (name, result.stdout, result.stderr)
        assert DIRECTION_BLOCKER not in result.stdout, name

    for mode in ("consumer", "mixed"):
        set_mode(tmp_path, mode)
        for name, result in verdicts(tmp_path).items():
            assert result.returncode == 1, (mode, name, result.stdout, result.stderr)
            assert DIRECTION_BLOCKER in result.stdout, (mode, name, result.stdout)

    set_mode(tmp_path)
    before = (tmp_path / ".allforai/bootstrap/workflow.json").read_bytes()
    replanned = invoke(tmp_path, plan_request(topics))
    assert replanned.returncode == 1, (replanned.stdout, replanned.stderr)
    assert DIRECTION_BLOCKER in replanned.stdout, replanned.stdout
    assert (tmp_path / ".allforai/bootstrap/workflow.json").read_bytes() == before, \
        "a refused plan leaves the graph exactly as it was"


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_direction_gate_stays_silent_when_it_does_not_apply(tmp_path, host):
    """Only a product people live with owes a chosen direction.

    An internal tool, a headless service, a classification bootstrap has not made yet
    and a local change are all outside the question, so none of them may be accused of
    ducking it. A missing mode is M1's own finding; answering it with this code as well
    would send the user to repair the wrong thing.
    """
    without_direction(tmp_path, host)
    for name, result in verdicts(tmp_path).items():
        assert result.returncode == 0, (name, result.stdout, result.stderr)
        assert DIRECTION_BLOCKER not in result.stdout, name
    for mode in ("none", "admin"):
        set_mode(tmp_path, mode, reason="Only the shop's own staff ever open it")
        for name, result in verdicts(tmp_path).items():
            assert DIRECTION_BLOCKER not in result.stdout, (mode, name, result.stdout)

    path = tmp_path / PROFILE
    profile = json.loads(path.read_text())
    profile.pop("experience_priority")
    path.write_text(json.dumps(profile), encoding="utf-8")
    for name, result in verdicts(tmp_path).items():
        assert DIRECTION_BLOCKER not in result.stdout, (name, result.stdout)

    local = tmp_path / "local"
    project(local, host=host)
    set_mode(local)
    for name, result in verdicts(local).items():
        assert DIRECTION_BLOCKER not in result.stdout, (name, result.stdout)

    headless = tmp_path / "headless"
    without_direction(headless, host, headless=True)
    assert json.loads((headless / PROFILE).read_text())["experience_priority"]["mode"] == "none"
    for name, result in verdicts(headless).items():
        assert result.returncode == 0, (name, result.stdout, result.stderr)


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_pre_existing_concept_and_journal_read_without_drift(tmp_path, host):
    """A session recorded before this module existed still reads back exactly as it was.

    The concept here carries neither the new topic's gap question nor a single proposal,
    which is what a record written by the earlier script looks like. Nothing may back-fill
    it: the whole session runs to a published contract through every gate, and the two
    read-only entries — `resume` and `--delegations` — have to come back empty-handed and
    leave the record byte for byte where they found it.
    """
    topics = drafted(tmp_path, host)
    path = tmp_path / CONCEPT
    concept = json.loads(path.read_text())
    concept["intent_questions"] = [question for question in concept["intent_questions"]
                                   if question["id"] != "gap-" + EXPERIENCE_TOPIC]
    path.write_text(json.dumps(concept), encoding="utf-8")
    assert "experience_proposals" not in concept

    confirmed = decide(tmp_path, [{"operation": "confirm", "id": topic, "reason": "Chosen direction"}
                                  for topic in topics])
    assert confirmed.returncode == 0, (confirmed.stdout, confirmed.stderr)
    frozen = invoke(tmp_path, freeze_request(topics))
    assert frozen.returncode == 0, (frozen.stdout, frozen.stderr)
    planned = invoke(tmp_path, plan_request(topics))
    assert planned.returncode == 0, (planned.stdout, planned.stderr)
    confirm_plan(tmp_path, stage="plan-projection", reason="Presented the projected plan")
    publish_contract(tmp_path, "deliver-orders")
    for name, result in verdicts(tmp_path).items():
        assert result.returncode == 0, (name, result.stdout, result.stderr)

    before = {name: (tmp_path / name).read_bytes() for name in (CONCEPT, JOURNAL)}
    resumed = invoke(tmp_path, {"operation": "resume"})
    assert resumed.returncode == 0, (resumed.stdout, resumed.stderr)
    presented = json.loads(resumed.stdout)
    assert "experience_proposals" not in presented, "an old record grows no proposal store by being read"
    assert all("proposals" not in entry for entry in presented["topics"])
    assert all(entry["topic"] != EXPERIENCE_TOPIC for entry in presented["topics"]), \
        "a topic nobody ever opened is not put back on the table"

    disclosed = cli(tmp_path, "--delegations")
    assert disclosed.returncode == 0, (disclosed.stdout, disclosed.stderr)
    assert not disclosed.stderr
    assert json.loads(disclosed.stdout) == {"status": "delegations", "delegations": []}, \
        "a run that predates delegation has nothing to disclose"
    assert all((tmp_path / name).read_bytes() == content for name, content in before.items()), \
        "reading an old record never rewrites it"

    stored = json.loads((tmp_path / CONCEPT).read_text())
    assert [item["id"] for item in stored["requirements"]] == topics
    for item in stored["requirements"]:
        assert "proposal_id" not in item and "auto_decided" not in item, item["id"]
        assert item["origin"] == "user-request"
    for batch in json.loads((tmp_path / JOURNAL).read_text())["batches"]:
        for decision in batch["decisions"]:
            recorded = decision.get("intent") or {}
            assert "proposal_id" not in recorded and "auto_decided" not in recorded, decision
            assert "delegated" not in (recorded.get("confirmation") or {}), decision


DELEGATION_REASON = "The tired half hour is read better here than the shopkeeper can read it tonight"


def delegated_concept(batch="handed-over"):
    """The concept record a run holds after the user handed the pick to the model.

    Written straight to disk rather than driven through a session: what the closing
    summary owes the user is readable from the record alone, so the disclosure path
    is proven without a whole bootstrap behind it, on either host's copy.
    """
    item = chosen_item(batch=batch, reason=DELEGATION_REASON, auto_decided=True)
    item["confirmation"]["delegated"] = True
    offered = dict(proposal("calm-pass"), origin="model-proposal", round=1,
                   recommended=True, rationale=RATIONALE)
    return {"requirements": [item], "experience_proposals": [offered]}


def report_section(report, heading):
    """The body lines of one `##` section of run-summary.md."""
    assert "\n## " + heading + "\n" in report, (heading, report)
    return report.split("\n## " + heading + "\n", 1)[1].split("\n## ", 1)[0].strip().splitlines()


def test_run_summary_and_completion_text_disclose_delegations(tmp_path):
    """A finished run says which directions the user never chose for themselves.

    A delegation is only a line in a file until something reads it back out, so the
    closing summary carries it into the run's auditable trace and the orchestrator
    template makes the completion text name each one. Disclosure has to survive a run
    that ended badly too: an unreadable record costs the reading, never the report.
    """
    product_intent, summarize_run_log = load("product_intent", "summarize_run_log")
    assert summarize_run_log._delegations is product_intent.delegations, \
        "the summary discloses through the CLI that records delegations, never a copy of it"

    handed = tmp_path / "handed-over"
    (handed / CONCEPT).parent.mkdir(parents=True)
    (handed / CONCEPT).write_text(json.dumps(delegated_concept()), encoding="utf-8")
    summary = summarize_run_log.summarize(handed)
    assert summary["schema_version"] == "1.0", "the summary only gained a key"
    assert "delegations_error" not in summary
    assert summary["delegations"] == [
        {"id": EXPERIENCE_TOPIC + "-calm-pass", "revision": 1, "proposal_id": "calm-pass",
         "proposal_title": proposal("calm-pass")["title"],
         "user_reference": "user turn handed-over", "reason": DELEGATION_REASON}]

    report = summarize_run_log.write_reports(handed, summary)[1].read_text(encoding="utf-8")
    assert report.index("## Delegated Decisions") > report.index("## Recent Failures"), \
        "the disclosure closes the report, after what the run itself did"
    assert report_section(report, "Delegated Decisions") == [
        "- `" + EXPERIENCE_TOPIC + "-calm-pass` proposal=`" + proposal("calm-pass")["title"]
        + "` user_turn=`user turn handed-over` reason=`" + DELEGATION_REASON + "`"]

    picked = tmp_path / "picked"
    picked.mkdir()
    quiet = summarize_run_log.summarize(picked)
    assert quiet["delegations"] == [] and "delegations_error" not in quiet
    assert report_section(summarize_run_log.write_reports(picked, quiet)[1].read_text(encoding="utf-8"),
                          "Delegated Decisions") == ["- none"], \
        "a run nobody delegated anything in still says so"

    torn = tmp_path / "torn"
    (torn / CONCEPT).parent.mkdir(parents=True)
    (torn / CONCEPT).write_text("{ the record was cut off", encoding="utf-8")
    broken = summarize_run_log.summarize(torn)
    assert broken["delegations"] == [] and broken["delegations_error"], \
        "a record that cannot be read may not be reported as nothing delegated"
    torn_lines = report_section(summarize_run_log.write_reports(torn, broken)[1].read_text(encoding="utf-8"),
                                "Delegated Decisions")
    assert torn_lines[0] == "- none"
    assert torn_lines[1] == "- unreadable: " + broken["delegations_error"]

    parts = TEMPLATE.read_text(encoding="utf-8").split("## Post-Completion", 1)
    assert len(parts) == 2, "the template still closes with one Post-Completion section"
    closing = parts[1]
    assert "product_intent.py . --delegations" in closing
    assert "Decisions you delegated to the model" in closing
    assert "No delegated decisions." in closing
    assert (closing.index("Run log summary") < closing.index("--delegations")
            < closing.index("Mark concept drift resolved")), \
        "the disclosure runs between the run log summary and the drift mark"


def test_protocol_text_names_the_new_topic_and_actions():
    """The protocol the hosts read tells them the same story the scripts enforce.

    Every seam above is reachable only if the text that instructs the host names it:
    the topic, the two new actions, where proposals come from and what disqualifies
    them, and the fact that a recommendation the user never answered is still not a
    choice. The old sentence that listed the non-actions without the new ones would
    read as permission to let a displayed default stand in for a pick, so it must be
    gone, not merely supplemented.
    """
    protocol = PROTOCOL.read_text(encoding="utf-8")
    flat = " ".join(protocol.split())  # the prose wraps; the sentences are what is pinned

    assert "omitted answers and silence are not actions." not in flat, \
        "the action sentence must be replaced, not left beside the new one"
    assert "recommendations, displayed defaults, omitted answers and silence are not actions; " \
           "`select` and `delegate` are actions." in flat
    assert "`select` and `delegate` are actions" in flat

    assert EXPERIENCE_TOPIC in protocol, "the topic the scripts accept is named in the protocol"
    topics = flat.split("Topic names:", 1)[1].split(".", 1)[0]
    assert topics.index("business-loop") < topics.index(EXPERIENCE_TOPIC) < topics.index("tradeoffs"), \
        "the topic list keeps the order the script's TOPICS ships"
    assert "gap-" + EXPERIENCE_TOPIC in protocol, "the headless exclusion names the gap question"

    assert "model-proposal" in protocol, "the origin only proposals carry is documented"
    assert "`propose`" in protocol and "recommended_id" in protocol, \
        "the operation that produces proposals has its own entry"
    assert "proposal_id" in protocol and "auto_decided" in protocol, \
        "the decide catalogue explains what select and delegate write"

    heading = "## Experience direction proposals"
    assert heading in protocol
    assert protocol.index("## Discussion responsibility") < protocol.index(heading), \
        "the proposal section follows the discussion responsibility it qualifies"
    section = " ".join(protocol.split(heading, 1)[1].split("\n## ", 1)[0].split())
    assert "consumer-maturity-patterns.md" in section, \
        "the self-check points at the anti-patterns it is a self-check against"
    for anti_pattern in ("The Compressed Admin Panel", "The Concept Demo", "Feature Checklist Design"):
        assert anti_pattern in section, anti_pattern
    assert "fragmented learning" in section, \
        "the no-literal-translation rule keeps its worked example"
    assert "--delegations" in section and "--delegations" in protocol.split("At the interactive run entry", 1)[1], \
        "delegation disclosure is named both as an obligation and as a CLI entry"

    for line in protocol.splitlines():
        if "experience_priority" in line:
            assert "experience_priority.mode" in line, line
