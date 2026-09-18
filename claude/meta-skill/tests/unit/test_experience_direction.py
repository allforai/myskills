"""Experience direction through the copied product-intent CLI and gates; no host proof.

The user picks the product's experience direction from the model's proposals.
These tests drive that choice through the generated project's own scripts, so
both host copies (the Codex tests directory is a symlink to this one) prove the
same seams.
"""
import importlib.util
import json

import pytest

from .test_bootstrap_scope import project
from .test_product_intent_session import CONCEPT, JOURNAL, TOPICS, decide, draft, invoke

EXPERIENCE_TOPIC = "experience-direction"
BASELINE = ".allforai/product-concept/concept-baseline.json"
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
