"""Re-freezing the same confirmed selection converges; a changed selection or decision invalidates.

Copied-CLI seam tests in temporary projects on both host copies; not host-dialogue proof.
"""
import json

import pytest

from .test_bootstrap_scope import project, gate, publish_contract, write
from .test_product_intent_resume import freeze_and_plan
from .test_product_intent_session import invoke, draft, decide, TOPICS, JOURNAL
from .test_validate_bootstrap import ATTENTION_CONTRACT_BODY

GATES = ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py")
LOCAL = ".allforai/bootstrap/local-requirements.json"
PROFILE = ".allforai/bootstrap/bootstrap-profile.json"
BASELINE = ".allforai/product-concept/concept-baseline.json"


def snapshot(root):
    return {p: p.read_bytes() for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts}


def confirmed_product(root, host):
    project(root, host=host)
    assert invoke(root, draft()).returncode == 0
    assert decide(root, [{"operation": "confirm", "id": t, "reason": "Chosen"} for t in TOPICS] + [
        {"operation": "answer", "id": "conflict", "answer": "Exclude archived orders", "reason": "Privacy"}]).returncode == 0
    assert freeze_and_plan(root).returncode == 0
    for name in GATES:
        assert gate(root, name).returncode == 0


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("batch", ["scope", "scope-again"])
def test_identical_product_refreeze_converges_without_new_journal_version_or_replan(tmp_path, host, batch):
    confirmed_product(tmp_path, host)
    before = snapshot(tmp_path)
    again = invoke(tmp_path, {"operation": "freeze", "include": TOPICS, "exclude": {},
                              "batch_id": batch, "user_reference": "user scope repeat", "reason": "Release"})
    assert again.returncode == 0, again.stdout
    output = json.loads(again.stdout)
    assert output["status"] == "frozen" and output["baseline"]["version"] == 1
    assert output["unchanged"] is True
    assert snapshot(tmp_path) == before
    assert len(json.loads((tmp_path / JOURNAL).read_text())["batches"]) == 2
    for name in GATES:
        checked = gate(tmp_path, name)
        assert checked.returncode == 0, (name, checked.stdout)


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_changed_product_selection_freezes_a_new_version_and_invalidates_the_plan(tmp_path, host):
    confirmed_product(tmp_path, host)
    changed = invoke(tmp_path, {"operation": "freeze", "include": TOPICS[:-1], "exclude": {"tradeoffs": "Defer"},
                                "batch_id": "scope-2", "user_reference": "user scope change", "reason": "Narrow release"})
    assert changed.returncode == 0, changed.stdout
    assert json.loads(changed.stdout)["baseline"]["version"] == 2
    assert len(json.loads((tmp_path / JOURNAL).read_text())["batches"]) == 3
    for name in GATES:
        checked = gate(tmp_path, name)
        assert checked.returncode == 1 and "baseline" in checked.stdout, (name, checked.stdout)


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_new_decision_makes_the_same_selection_a_new_version(tmp_path, host):
    confirmed_product(tmp_path, host)
    assert decide(tmp_path, [{"operation": "adjust", "id": "scenarios", "changes": {"goal": "Offline ordering"},
                              "reason": "Poor connectivity"}], "adjust").returncode == 0
    same_selection = invoke(tmp_path, {"operation": "freeze", "include": TOPICS, "exclude": {},
                                       "batch_id": "scope-3", "user_reference": "user scope after adjust", "reason": "Release"})
    assert same_selection.returncode == 0, same_selection.stdout
    baseline = json.loads(same_selection.stdout)["baseline"]
    assert baseline["version"] == 2
    assert next(r for r in baseline["requirement_refs"] if r["id"] == "scenarios")["revision"] == 2
    assert gate(tmp_path, "validate_unattended_readiness.py").returncode == 1
    assert freeze_and_plan(tmp_path, "scope-4").returncode == 0  # replan on the new version
    assert json.loads((tmp_path / BASELINE).read_text())["intent_baseline"]["version"] == 2
    for name in GATES:
        assert gate(tmp_path, name).returncode == 0


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_reanswered_question_after_the_freeze_is_a_new_decision_and_a_new_version(tmp_path, host):
    confirmed_product(tmp_path, host)
    assert decide(tmp_path, [{"operation": "reopen", "id": "conflict", "reason": "Reconsider"}], "reconsider").returncode == 0
    assert decide(tmp_path, [{"operation": "answer", "id": "conflict", "answer": "Include archived orders",
                              "reason": "Reviewed"}], "settled").returncode == 0
    again = invoke(tmp_path, {"operation": "freeze", "include": TOPICS, "exclude": {},
                              "batch_id": "scope-2", "user_reference": "user scope after answer", "reason": "Release"})
    assert again.returncode == 0, again.stdout
    assert json.loads(again.stdout)["baseline"]["version"] == 2
    assert "unchanged" not in json.loads(again.stdout)


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_tampered_previous_scope_is_not_reused_as_the_identical_freeze(tmp_path, host):
    confirmed_product(tmp_path, host)
    journal = json.loads((tmp_path / JOURNAL).read_text())
    journal["batches"][-1]["decisions"][0]["status"] = "pending"
    write(tmp_path, JOURNAL, journal)
    again = invoke(tmp_path, {"operation": "freeze", "include": TOPICS, "exclude": {},
                              "batch_id": "scope-repair", "user_reference": "user scope repeat", "reason": "Release"})
    assert again.returncode == 0, again.stdout
    assert json.loads(again.stdout)["baseline"]["version"] == 2
    assert "unchanged" not in json.loads(again.stdout)


def local_freeze(root, batch, include, exclude):
    return invoke(root, {"operation": "freeze", "include": include, "exclude": exclude, "batch_id": batch,
                         "user_reference": "local scope turn", "reason": "Local release"})


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_identical_local_refreeze_converges_and_narrowed_selection_invalidates(tmp_path, host):
    project(tmp_path, host=host)
    (tmp_path / LOCAL).unlink()
    items = [{"id": name, "topic": "scenarios", "goal": "Deliver " + name, "scope": ["orders"],
              "business_rules": ["Account isolation"], "acceptance": [name + " covers one account"]}
             for name in ("export", "archive")]
    assert invoke(tmp_path, {"operation": "admit", "route": "local-change", "goal": "Order tools",
                             "areas": ["orders"], "items": items}).returncode == 0
    assert decide(tmp_path, [{"operation": "confirm", "id": i["id"], "reason": "Approved"} for i in items]).returncode == 0
    assert local_freeze(tmp_path, "local-scope", ["export", "archive"], {}).returncode == 0
    planned = invoke(tmp_path, {"operation": "plan", "nodes": [{"node_id": "orders", "capability": "implement",
        "goal": "Deliver order tools", "intent_ids": ["export", "archive"],
        "responsibilities": ["implementation", "documentation", "verification"], "source_inputs": ["orders.py"],
        "exit_artifacts": [".allforai/bootstrap/orders-result.json"], "body": ATTENTION_CONTRACT_BODY}]})
    assert planned.returncode == 0, planned.stdout
    publish_contract(tmp_path, "orders")
    for name in GATES:
        assert gate(tmp_path, name).returncode == 0
    before = snapshot(tmp_path)
    again = local_freeze(tmp_path, "local-scope-again", ["archive", "export"], {})
    assert again.returncode == 0, again.stdout
    assert json.loads(again.stdout)["baseline"]["version"] == 1
    assert snapshot(tmp_path) == before
    for name in GATES:
        assert gate(tmp_path, name).returncode == 0
    narrowed = local_freeze(tmp_path, "local-scope-2", ["export"], {"archive": "Later"})
    assert narrowed.returncode == 0, narrowed.stdout
    assert json.loads(narrowed.stdout)["baseline"]["version"] == 2
    assert json.loads((tmp_path / PROFILE).read_text())["intent_scope"]["version"] == 2
    for name in GATES:
        checked = gate(tmp_path, name)
        assert checked.returncode == 1, (name, checked.stdout)
