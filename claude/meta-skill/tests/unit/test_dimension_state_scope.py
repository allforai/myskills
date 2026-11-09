"""Dimension × state scope questions are asked before freeze (ADR-0011 C).

When a product offers several instances of something a user moves between, each thing it
keeps about that user is either shared across those instances or kept per instance. That
is a user-visible rule. The draft declares both lists; every pair it does not already
settle becomes an ordinary pending question, so the existing freeze rule refuses to
freeze it unanswered. Words here are deliberately abstract: the rule is generic.
"""
import json

from .test_bootstrap_scope import project
from .test_product_intent_session import TOPICS, decide, draft, invoke

DIMENSIONS = [{"id": "area", "name": "content areas"}, {"id": "mode", "name": "play modes"}]
STATEFUL = [{"id": "balance", "name": "the user's balance"}, {"id": "streak", "name": "the user's streak"}]


def _drafted(tmp_path, **declared):
    project(tmp_path, host="claude")
    request = draft()
    request.update(declared)
    return invoke(tmp_path, request)


def _scope_questions(root):
    concept = json.loads((root / ".allforai/product-concept/product-concept.json").read_text())
    return {q["id"]: q for q in concept["intent_questions"] if q.get("kind") == "scope"}


def test_a_draft_must_declare_both_lists(tmp_path):
    project(tmp_path, host="claude")
    request = draft()
    request.pop("dimensions")
    result = invoke(tmp_path, request)
    assert result.returncode == 1
    assert "dimensions" in result.stdout


def test_every_unsettled_pair_becomes_a_pending_scope_question(tmp_path):
    result = _drafted(tmp_path, dimensions=DIMENSIONS, stateful=STATEFUL)
    assert result.returncode == 0, result.stdout
    scope = _scope_questions(tmp_path)
    assert set(scope) == {"scope-area-balance", "scope-area-streak",
                          "scope-mode-balance", "scope-mode-streak"}
    q = scope["scope-area-balance"]
    assert q["status"] == "pending" and q["options"] == ["shared", "per-instance", "mixed"]
    assert "the user's balance" in q["question"] and "content areas" in q["question"]


def test_a_pair_an_intent_already_settles_is_not_asked(tmp_path):
    result = _drafted(tmp_path, dimensions=DIMENSIONS, stateful=STATEFUL,
                      settled_scopes=[{"dimension": "area", "stateful": "balance",
                                       "intent_id": "business-loop"}])
    assert result.returncode == 0, result.stdout
    ids = set(_scope_questions(tmp_path))
    assert "scope-area-balance" not in ids and "scope-area-streak" in ids


def test_a_settlement_must_name_a_drafted_intent(tmp_path):
    result = _drafted(tmp_path, dimensions=DIMENSIONS, stateful=STATEFUL,
                      settled_scopes=[{"dimension": "area", "stateful": "balance",
                                       "intent_id": "no-such-intent"}])
    assert result.returncode == 1
    assert "settled_scopes" in result.stdout


def test_unknown_pair_members_are_refused(tmp_path):
    result = _drafted(tmp_path, dimensions=DIMENSIONS, stateful=STATEFUL,
                      settled_scopes=[{"dimension": "area", "stateful": "ghost",
                                       "intent_id": "business-loop"}])
    assert result.returncode == 1


def test_freeze_refuses_an_unanswered_scope_question_and_accepts_an_answer(tmp_path):
    assert _drafted(tmp_path, dimensions=DIMENSIONS[:1], stateful=STATEFUL[:1]).returncode == 0
    actions = [{"operation": "confirm", "id": t, "reason": "Chosen direction"} for t in TOPICS]
    actions.append({"operation": "answer", "id": "conflict", "answer": "Exclude archived", "reason": "Scope"})
    assert decide(tmp_path, actions).returncode == 0
    freeze = {"operation": "freeze", "batch_id": "freeze-1", "user_reference": "user turn freeze",
              "reason": "Freeze confirmed scope", "include": list(TOPICS), "exclude": {}}
    refused = invoke(tmp_path, freeze)
    assert refused.returncode == 1 and "unresolved question" in refused.stdout
    answered = decide(tmp_path, [{"operation": "answer", "id": "scope-area-balance",
                                  "answer": "per-instance", "reason": "Each area stands alone"}],
                      batch="user-2")
    assert answered.returncode == 0, answered.stdout
    frozen = invoke(tmp_path, dict(freeze, batch_id="freeze-2"))
    assert frozen.returncode == 0, frozen.stdout


def test_a_product_with_no_dimension_asks_nothing_extra(tmp_path):
    assert _drafted(tmp_path, dimensions=[], stateful=STATEFUL).returncode == 0
    assert _scope_questions(tmp_path) == {}
