"""Interrupted dialogue through copied public CLIs; these are not host transcripts."""
import json

import pytest

from .test_bootstrap_scope import project, gate
from .test_product_intent_session import invoke, draft, decide, TOPICS, CONCEPT, JOURNAL
from .test_validate_bootstrap import ATTENTION_CONTRACT_BODY
from .test_bootstrap_scope import write


def freeze_and_plan(root, batch="scope"):
    frozen = invoke(root, {"operation": "freeze", "include": TOPICS, "exclude": {},
        "batch_id": batch, "user_reference": "user scope", "reason": "Release"})
    if frozen.returncode:
        return frozen
    return invoke(root, {"operation": "plan", "nodes": [{"node_id": "deliver", "capability": "implement",
        "goal": "Deliver orders", "intent_ids": TOPICS,
        "responsibilities": ["product", "technical", "implementation", "documentation", "verification"],
        "exit_artifacts": [".allforai/bootstrap/verified.json"], "body": ATTENTION_CONTRACT_BODY}],
        "not_applicable": {"experience": "Headless API"}})


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_resume_restores_reasons_history_and_explicit_exclusions_without_reasking(tmp_path, host):
    project(tmp_path, host=host)
    assert invoke(tmp_path, draft()).returncode == 0
    assert decide(tmp_path, [
        {"operation": "confirm", "id": "target-users", "reason": "Our customers"},
        {"operation": "adjust", "id": "scenarios", "changes": {"goal": "Offline ordering"}, "reason": "Poor connectivity"},
        {"operation": "remove", "id": "business-loop", "reason": "Drop ads"},
    ]).returncode == 0
    excluded = {i: "Later release" for i in [*TOPICS[2:], "conflict"]}
    assert invoke(tmp_path, {"operation": "freeze", "include": TOPICS[:2], "exclude": excluded,
        "batch_id": "scope", "user_reference": "user scope", "reason": "Release one"}).returncode == 0
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    output = json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)
    assert output["topics"] == []
    assert output["excluded"] == excluded
    assert [i["status"] for i in output["history"] if i["id"] == "scenarios"] == ["superseded", "confirmed"]
    assert output["history"][0]["confirmation"]["reason"] == "Our customers"
    assert next(i for i in output["history"] if i["id"] == "business-loop")["status"] == "removed"
    assert all(p.read_bytes() == b for p, b in before.items())


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_resume_does_not_hide_unanswered_topics_using_revoked_scope(tmp_path, host):
    project(tmp_path, host=host)
    assert invoke(tmp_path, draft()).returncode == 0
    assert decide(tmp_path, [{"operation": "confirm", "id": "target-users", "reason": "Customers"}]).returncode == 0
    assert invoke(tmp_path, {"operation": "freeze", "include": ["target-users"],
        "exclude": {i: "Later" for i in [*TOPICS[1:], "conflict"]}, "batch_id": "scope",
        "user_reference": "scope turn", "reason": "Release"}).returncode == 0
    journal = json.loads((tmp_path / JOURNAL).read_text())
    journal["batches"][-1]["decisions"][0]["status"] = "pending"
    write(tmp_path, JOURNAL, journal)
    result = invoke(tmp_path, {"operation": "resume"})
    assert result.returncode == 1, result.stdout


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_explicit_reconsideration_reopens_previously_excluded_topic_only(tmp_path, host):
    project(tmp_path, host=host)
    assert invoke(tmp_path, draft()).returncode == 0
    assert decide(tmp_path, [{"operation": "confirm", "id": "target-users", "reason": "Customers"}]).returncode == 0
    assert invoke(tmp_path, {"operation": "freeze", "include": ["target-users"],
        "exclude": {i: "Later" for i in [*TOPICS[1:], "conflict"]}, "batch_id": "scope",
        "user_reference": "scope turn", "reason": "Release"}).returncode == 0
    result = decide(tmp_path, [{"operation": "reopen", "id": "tradeoffs", "reason": "Discuss this now"}], "reconsider")
    assert result.returncode == 0, result.stdout
    output = json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)
    assert [i["id"] for t in output["topics"] for i in t["items"]] == ["tradeoffs"]
    assert "tradeoffs" not in output["excluded"]
    assert "scenarios" in output["excluded"]


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_legacy_removed_label_without_user_provenance_remains_pending(tmp_path, host):
    project(tmp_path, host=host)
    assert invoke(tmp_path, draft()).returncode == 0
    concept = json.loads((tmp_path / CONCEPT).read_text())
    concept["requirements"][0]["status"] = "removed"
    write(tmp_path, CONCEPT, concept)
    result = json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)
    assert result["topics"][0]["items"][0]["id"] == "target-users"
    assert result["topics"][0]["items"][0]["status"] == "pending"
    confirmed = decide(tmp_path, [{"operation": "confirm", "id": "target-users", "reason": "We still serve them"}], "verify-legacy")
    assert confirmed.returncode == 0, confirmed.stdout


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_reopened_question_blocks_dependents_until_explicit_answer_and_replan(tmp_path, host):
    project(tmp_path, host=host)
    assert invoke(tmp_path, draft()).returncode == 0
    assert decide(tmp_path, [{"operation": "confirm", "id": t, "reason": "Chosen"} for t in TOPICS] + [
        {"operation": "answer", "id": "conflict", "answer": "Exclude archived orders", "reason": "Privacy"}]).returncode == 0
    assert freeze_and_plan(tmp_path).returncode == 0
    assert gate(tmp_path, "validate_unattended_readiness.py").returncode == 0
    result = decide(tmp_path, [{"operation": "reopen", "id": "conflict", "reason": "Privacy needs reconsideration"}], "reconsider")
    assert result.returncode == 0, result.stdout
    output = json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)
    assert [q["id"] for t in output["topics"] for q in t["questions"]] == ["conflict"]
    assert not [i for t in output["topics"] for i in t["items"]]
    for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
        blocked = gate(tmp_path, name)
        assert blocked.returncode == 1 and "unresolved" in blocked.stdout, blocked.stdout
    assert freeze_and_plan(tmp_path, "blocked-scope").returncode == 1
    assert decide(tmp_path, [{"operation": "answer", "id": "conflict", "answer": "Exclude archived orders", "reason": "Reviewed privacy"}], "answer-2").returncode == 0
    assert freeze_and_plan(tmp_path, "scope-2").returncode == 0
    for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
        result = gate(tmp_path, name)
        assert result.returncode == 0, result.stdout
    journal = json.loads((tmp_path / JOURNAL).read_text())
    assert journal["batches"][0]["decisions"][-1]["intent"]["answer"] == "Exclude archived orders"


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_explicit_restore_and_reconsider_preserve_all_prior_revisions(tmp_path, host):
    project(tmp_path, host=host)
    assert invoke(tmp_path, draft()).returncode == 0
    assert decide(tmp_path, [{"operation": "confirm", "id": "target-users", "reason": "Initial choice"}]).returncode == 0
    assert decide(tmp_path, [{"operation": "remove", "id": "target-users", "reason": "Stop serving this group"}], "remove").returncode == 0
    restored = decide(tmp_path, [{"operation": "restore", "id": "target-users", "reason": "Serve them again"}], "restore")
    assert restored.returncode == 0, restored.stdout
    result = decide(tmp_path, [{"operation": "reopen", "id": "target-users", "reason": "Need to verify audience"}], "reopen")
    assert result.returncode == 0, result.stdout
    resumed = json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)
    history = [i for i in resumed["history"] if i["id"] == "target-users"]
    assert [i["revision"] for i in history] == [1, 2, 3, 4]
    assert [i["confirmation"]["reason"] for i in history] == ["Initial choice", "Stop serving this group", "Serve them again", "Need to verify audience"]
    assert history[1]["status"] == "removed"
    assert history[-1]["status"] == "pending"
    assert decide(tmp_path, [{"operation": "confirm", "id": "target-users", "reason": "Audience verified"}], "verified").returncode == 0
    resumed = json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)
    assert "target-users" not in [i["id"] for t in resumed["topics"] for i in t["items"]]


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("trusted", [True, False])
def test_local_legacy_admission_reuses_only_supported_choice_and_preserves_old_documents(tmp_path, host, trusted):
    project(tmp_path, host=host)
    (tmp_path / ".allforai/bootstrap/local-requirements.json").unlink()
    write(tmp_path, CONCEPT, {"mission": "Account-isolated retail operations", "unrelated": "warehouse"})
    write(tmp_path, ".allforai/product-concept/concept-baseline.json", {
        "_meta": {"generated_from": "product-concept phase", "generated_at": "2026-08-01T10:00:00Z",
                  "source_files": ["product-concept.json", "role-value-map.json", "product-mechanisms.json"]},
        "mission": "Account-isolated retail operations", "target_market": "Small retailers",
        "roles": [{"id": "R1", "name": "Account owner", "app": "website", "client_type": "web",
                   "screen_granularity": "single_task_focus", "high_frequency_tasks": ["Export account orders"],
                   "design_principle": "Keep accounts isolated"}],
        "governance_styles": [], "errc_highlights": {"must_have": ["Account isolation"], "eliminate": ["Cross-account exports"]}})
    item = {"id": "export", "topic": "scenarios", "goal": "Export account orders", "scope": ["orders"],
            "business_rules": ["Account isolation"], "acceptance": ["Other accounts are excluded"],
            "status": "confirmed", "revision": 1, "confirmation": {"source": "user" if trusted else "code",
            "reference": JOURNAL + "#prior/decisions/0", "decision_id": "prior/decisions/0", "reason": "Privacy"}}
    prior = {"schema_version": "1.0", "batches": [{"batch_id": "prior", "source": "user_session", "decisions": [
        {"question": "Export which orders?", "chosen": "Export account orders", "rationale": "Privacy"}]}]}
    write(tmp_path, JOURNAL, prior)
    preserved = {p: p.read_bytes() for p in [tmp_path / CONCEPT, tmp_path / ".allforai/product-concept/concept-baseline.json", tmp_path / "orders.py"]}
    result = invoke(tmp_path, {"operation": "admit", "route": "local-change", "goal": "Add account CSV export",
        "areas": ["orders"], "items": [item]})
    assert result.returncode == 0, result.stdout
    output = json.loads(result.stdout)
    assert [i["id"] for t in output["topics"] for i in t["items"]] == ([] if trusted else ["export"])
    assert not [q for t in output["topics"] for q in t["questions"]]
    assert json.loads((tmp_path / JOURNAL).read_text()) == prior
    assert gate(tmp_path, "validate_unattended_readiness.py").returncode == 1
    if not trusted:
        assert decide(tmp_path, [{"operation": "confirm", "id": "export", "reason": "Privacy approved"}], "missing-choice").returncode == 0
    frozen = invoke(tmp_path, {"operation": "freeze", "include": ["export"], "exclude": {}, "batch_id": "local-scope",
        "user_reference": "local scope turn", "reason": "Account export only"})
    assert frozen.returncode == 0, frozen.stdout
    planned = invoke(tmp_path, {"operation": "plan", "nodes": [{"node_id": "export", "capability": "implement",
        "goal": "Deliver CSV export", "intent_ids": ["export"], "responsibilities": ["implementation", "documentation", "verification"],
        "exit_artifacts": [".allforai/bootstrap/export-result.json"], "body": ATTENTION_CONTRACT_BODY}]})
    assert planned.returncode == 0, planned.stdout
    for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
        result = gate(tmp_path, name)
        assert result.returncode == 0, result.stdout
    assert all(p.read_bytes() == b for p, b in preserved.items())
    assert json.loads((tmp_path / ".allforai/bootstrap/bootstrap-profile.json").read_text())["task_route"] == "local-change"
    local_path = ".allforai/bootstrap/local-requirements.json"
    local = json.loads((tmp_path / local_path).read_text())
    local["requirements"][-1]["acceptance"] = ["Export every account"]
    write(tmp_path, local_path, local)
    for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
        result = gate(tmp_path, name)
        assert result.returncode == 1, (name, result.stdout)
