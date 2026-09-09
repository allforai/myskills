"""Public product-session identity admission, without implicit approval."""
import json

import pytest

from .test_bootstrap_scope import confirm_plan, project, write, gate, publish_contract
from .test_product_intent_session import CONCEPT, JOURNAL, TOPICS, draft, invoke, decide
from .test_validate_bootstrap import ATTENTION_CONTRACT_BODY


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("collision", ["intent", "question", "generated-gap"])
def test_question_identity_cannot_alias_an_intent_before_persistence(tmp_path, host, collision):
    project(tmp_path, host=host)
    request = draft()
    if collision == "intent":
        request["questions"][0].update(id="tradeoffs", depends_on=[])
    elif collision == "question":
        request["questions"].append(dict(request["questions"][0]))
    else:
        request["items"] = [i for i in request["items"] if i["topic"] != "value-proposition"]
        request["items"][0]["id"] = "gap-value-proposition"
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = invoke(tmp_path, request)
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert not result.stderr
    assert all(p.read_bytes() == content for p, content in before.items())
    assert not (tmp_path / CONCEPT).exists()


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("operation", ["resume", "freeze"])
def test_persisted_collision_cannot_be_resumed_or_frozen_as_valid(tmp_path, host, operation):
    project(tmp_path, host=host)
    assert invoke(tmp_path, draft()).returncode == 0
    assert decide(tmp_path, [{"operation": "confirm", "id": identity, "reason": "User choice"}
                             for identity in TOPICS]).returncode == 0
    concept = json.loads((tmp_path / CONCEPT).read_text())
    concept["intent_questions"][0].update(id="tradeoffs", depends_on=[])
    write(tmp_path, CONCEPT, concept)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = invoke(tmp_path, {"operation": operation, "batch_id": "scope", "user_reference": "scope turn",
                               "reason": "Release scope", "include": TOPICS, "exclude": {}})
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert not result.stderr
    assert all(p.read_bytes() == content for p, content in before.items())


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_added_intent_cannot_reuse_a_pending_question_identity(tmp_path, host):
    project(tmp_path, host=host)
    assert invoke(tmp_path, draft()).returncode == 0
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = decide(tmp_path, [{"operation": "add", "reason": "User requested exports",
        "item": {"id": "conflict", "topic": "scenarios", "goal": "Export orders",
                 "scope": ["orders"], "business_rules": ["Only own orders"],
                 "acceptance": ["Other accounts remain isolated"]}}])
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert not result.stderr
    assert all(p.read_bytes() == content for p, content in before.items())
    assert not (tmp_path / JOURNAL).exists()


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_public_gates_reject_persisted_question_alias_and_restore_readiness(tmp_path, host):
    project(tmp_path, host=host)
    request = draft()
    request["questions"] = []
    assert invoke(tmp_path, request).returncode == 0
    assert decide(tmp_path, [{"operation": "confirm", "id": identity, "reason": "User choice"}
                             for identity in TOPICS]).returncode == 0
    assert invoke(tmp_path, {"operation": "freeze", "batch_id": "scope", "user_reference": "scope turn",
                            "reason": "Release scope", "include": TOPICS, "exclude": {}}).returncode == 0
    assert invoke(tmp_path, {"operation": "plan", "nodes": [{
        "node_id": "deliver", "capability": "implement", "goal": "Deliver confirmed product",
        "intent_ids": TOPICS, "responsibilities": ["product", "experience", "technical",
            "implementation", "documentation", "verification"], "source_inputs": ["orders.py"],
        "exit_artifacts": [".allforai/bootstrap/delivery.json"], "body": ATTENTION_CONTRACT_BODY}]}).returncode == 0
    confirm_plan(tmp_path, stage="plan-projection", reason="Presented the projected plan")
    concept = json.loads((tmp_path / CONCEPT).read_text())
    alias = {"id": "tradeoffs", "topic": "tradeoffs", "question": "An unresolved choice",
             "depends_on": [], "status": "pending"}
    for questions, expected in [([], 0), ([alias], 1), ([], 0)]:
        concept["intent_questions"] = questions
        write(tmp_path, CONCEPT, concept)
        if expected == 0:
            publish_contract(tmp_path, "deliver")  # The consumed concept changed; re-observe before readiness.
        before = (tmp_path / CONCEPT).read_bytes()
        for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
            options = ("--write-report",) if name == "validate_unattended_readiness.py" else ()
            result = gate(tmp_path, name, *options)
            assert result.returncode == expected, (name, result.stdout, result.stderr)
            assert not result.stderr
        report = json.loads((tmp_path / ".allforai/bootstrap/unattended-run-readiness.json").read_text())
        assert report["status"] == ("not_ready" if expected else "ready")
        assert (tmp_path / CONCEPT).read_bytes() == before
