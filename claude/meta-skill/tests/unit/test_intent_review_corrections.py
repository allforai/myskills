"""T11 spec-review corrections at the copied product-intent CLI and gates; no host proof.

Covers review findings 2 (product-route legacy reuse), 4 (reopened intent
blocks only its consumers) and 6 (invalid Run Policy repair). The Codex tests
directory is a symlink to this one, so both host copies run the same seams.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from .test_bootstrap_scope import project as shared_project, gate, write, SCRIPTS
from .test_product_intent_session import invoke, draft, decide, CONCEPT, JOURNAL
from .test_product_intent_session import TOPICS as SHARED_TOPICS
from .test_validate_bootstrap import ATTENTION_CONTRACT_BODY

TOPICS = list(SHARED_TOPICS)
GATES = ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py")
STAGES = ["product", "technical", "implementation", "documentation", "verification"]
POLICY = {"on_repeated_failure": "continue", "on_needs_iteration": "accept", "on_safety_warning": "halt"}
RUN_POLICY = ".allforai/bootstrap/run-policy.json"
REPAIRS = ".allforai/bootstrap/run-policy-repairs.json"
READINESS = ".allforai/bootstrap/unattended-run-readiness.json"


def project(root, **options):
    """Scoped fixture without the local node's contract publication; plans below declare their own inputs."""
    requirement = shared_project(root, source_inputs=None, **options)
    shutil.copy2(SCRIPTS / "orchestrator/evidence_freshness.py", root / ".allforai/bootstrap/scripts/evidence_freshness.py")
    return requirement


def publish(root, node_id):
    """Publish one node's contract through the copied freshness CLI, verified by the copied validator."""
    def freshness(request):
        return subprocess.run([sys.executable, str(root / ".allforai/bootstrap/scripts/evidence_freshness.py"), str(root)],
                              input=json.dumps(request), text=True, capture_output=True, cwd=root)
    observed = freshness({"operation": "observe", "node_id": node_id, "kind": "contract"})
    assert observed.returncode == 0, (observed.stdout, observed.stderr)
    published = freshness({"operation": "publish", "observation": json.loads(observed.stdout)["observation"],
                           "verification_command": [sys.executable, ".allforai/bootstrap/scripts/validate_bootstrap.py",
                                                    ".allforai/bootstrap"]})
    assert published.returncode == 0, (published.stdout, published.stderr)


def cli(root, *args):
    return subprocess.run([sys.executable, str(root / ".allforai/bootstrap/scripts/product_intent.py"),
                           str(root), *args], text=True, capture_output=True, cwd=root)


def node(identity, intents):
    return {"node_id": identity, "capability": "implement", "goal": "Deliver " + identity,
            "intent_ids": intents, "responsibilities": STAGES, "source_inputs": ["orders.py"],
            "exit_artifacts": [".allforai/bootstrap/" + identity + ".json"], "body": ATTENTION_CONTRACT_BODY}


def two_node_plan(root, batch="scope"):
    frozen = invoke(root, {"operation": "freeze", "include": TOPICS, "exclude": {}, "batch_id": batch,
                           "user_reference": "user scope " + batch, "reason": "Release"})
    assert frozen.returncode == 0, frozen.stdout
    planned = invoke(root, {"operation": "plan", "not_applicable": {"experience": "Headless API"},
                            "nodes": [node("node-a", TOPICS[:3]), node("node-b", TOPICS[3:])]})
    assert planned.returncode == 0, planned.stdout
    for identity in ("node-a", "node-b"):
        publish(root, identity)
    return planned


def confirmed_product(root, host):
    project(root, host=host)
    assert invoke(root, draft()).returncode == 0
    assert decide(root, [{"operation": "confirm", "id": t, "reason": "Chosen"} for t in TOPICS] + [
        {"operation": "answer", "id": "conflict", "answer": "Exclude archived orders", "reason": "Privacy"}]).returncode == 0


def blockers(root):
    return json.loads((root / READINESS).read_text())["blockers"]


# ---- Finding 4: reopening one intent blocks its consumers only ----------------------------------

@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("reopened", ["value-proposition", "conflict"])
def test_reopened_intent_blocks_only_consuming_nodes_until_refreeze_and_replan(tmp_path, host, reopened):
    confirmed_product(tmp_path, host)
    two_node_plan(tmp_path)
    for name in GATES:
        result = gate(tmp_path, name, *(("--write-report",) if name.endswith("readiness.py") else ()))
        assert result.returncode == 0, (name, result.stdout)
    spec_a = (tmp_path / ".allforai/bootstrap/node-specs/node-a.md").read_bytes()
    reopen = decide(tmp_path, [{"operation": "reopen", "id": reopened, "reason": "Reconsider"}], "reconsider")
    assert reopen.returncode == 0, reopen.stdout
    readiness = gate(tmp_path, "validate_unattended_readiness.py", "--write-report")
    assert readiness.returncode == 1
    found = blockers(tmp_path)
    assert found, readiness.stdout
    assert all(b.get("node_id") == "node-b" for b in found), found
    assert "pending_requirement" in {b["code"] for b in found}
    assert "invalid_scope" not in {b["code"] for b in found}
    if reopened == "conflict":
        assert any("unresolved" in b["message"] for b in found), found
    for name in GATES[:2]:
        result = gate(tmp_path, name)
        assert result.returncode == 1, (name, result.stdout)
        assert "node-b" in result.stdout and "node-a" not in result.stdout, (name, result.stdout)
        assert "invalid_scope" not in result.stdout, (name, result.stdout)
    # A pending intent cannot be refrozen; the user answers first, then refreezes and replans.
    assert invoke(tmp_path, {"operation": "freeze", "include": TOPICS, "exclude": {}, "batch_id": "early",
                             "user_reference": "user", "reason": "Too early"}).returncode == 1
    action = ({"operation": "answer", "id": "conflict", "answer": "Exclude archived orders", "reason": "Reviewed"}
              if reopened == "conflict" else {"operation": "confirm", "id": reopened, "reason": "Still wanted"})
    assert decide(tmp_path, [action], "settled").returncode == 0
    two_node_plan(tmp_path, "scope-2")
    for name in GATES:
        result = gate(tmp_path, name, *(("--write-report",) if name.endswith("readiness.py") else ()))
        assert result.returncode == 0, (name, result.stdout)
    assert (tmp_path / ".allforai/bootstrap/node-specs/node-a.md").read_bytes() == spec_a
    workflow = json.loads((tmp_path / ".allforai/bootstrap/workflow.json").read_text())
    assert workflow["product_baseline"]["version"] == 2


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_freeze_level_drift_stays_a_global_blocker(tmp_path, host):
    confirmed_product(tmp_path, host)
    two_node_plan(tmp_path)
    baseline_path = ".allforai/product-concept/concept-baseline.json"
    baseline = json.loads((tmp_path / baseline_path).read_text())
    baseline["intent_baseline"]["confirmation"] = JOURNAL + "#missing/decisions/0"
    write(tmp_path, baseline_path, baseline)
    readiness = gate(tmp_path, "validate_unattended_readiness.py", "--write-report")
    assert readiness.returncode == 1
    found = blockers(tmp_path)
    assert [b["code"] for b in found] == ["invalid_scope"] and "node_id" not in found[0], found


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_node_projection_drift_blocks_that_node_only(tmp_path, host):
    confirmed_product(tmp_path, host)
    two_node_plan(tmp_path)
    path = ".allforai/bootstrap/workflow.json"
    workflow = json.loads((tmp_path / path).read_text())
    target = next(n for n in workflow["nodes"] if n["node_id"] == "node-b")
    target["acceptance"][0] = "Old code is sufficient"
    write(tmp_path, path, workflow)
    spec = tmp_path / ".allforai/bootstrap/node-specs/node-b.md"
    spec.write_text("---\n" + json.dumps(target) + "\n---\n" + spec.read_text().split("---", 2)[2])
    readiness = gate(tmp_path, "validate_unattended_readiness.py", "--write-report")
    assert readiness.returncode == 1
    found = blockers(tmp_path)
    assert found and all(b.get("node_id") == "node-b" for b in found), found
    scope = [b for b in found if b["code"] != "stale_evidence"]
    assert scope and all("product" in b["message"].lower() for b in scope), found


# ---- Finding 2: product-route legacy reuse needs canonical journal provenance -------------------

def prior_journal(goal):
    return {"schema_version": "1.0", "batches": [{"batch_id": "prior", "source": "user_session", "topic": "Users",
            "decisions": [{"question": "Who are our customers?", "chosen": goal, "rationale": "Existing explicit choice"}]}]}


def legacy_item(variant):
    item = draft()["items"][0]
    item.update(status="confirmed", confirmation={"source": "user", "reference": JOURNAL + "#prior/decisions/0",
                "decision_id": "prior/decisions/0", "reason": "Existing explicit choice"})
    if variant == "non-canonical-reference":
        item["confirmation"]["reference"] = "bootstrap user turn 2"
    elif variant == "code-source":
        item["confirmation"]["source"] = "code"
    elif variant == "different-choice":
        item["confirmation"]["reason"] = "Reason the journal never recorded"
    return item


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("variant", ["trusted", "trusted-new-product", "non-canonical-reference", "code-source",
                                     "different-choice", "superseded", "missing-journal"])
def test_product_draft_reuses_legacy_choice_only_with_canonical_journal_provenance(tmp_path, host, variant):
    project(tmp_path, host=host)
    item = legacy_item(variant)
    journal = prior_journal(item["goal"])
    if variant == "superseded":
        journal["batches"].append({"batch_id": "later", "source": "user_session", "topic": "Users", "decisions": [
            {"question": "Who are our customers?", "chosen": "Enterprise buyers", "rationale": "Pivot",
             "supersedes": "prior/decisions/0"}]})
    if variant != "missing-journal":
        write(tmp_path, JOURNAL, journal)
    request = draft()
    request["questions"] = []
    request["items"][0] = item
    if variant == "trusted-new-product":
        (tmp_path / "orders.py").unlink()
        request.update(route="new-product", facts=[])
        for entry in request["items"]:
            entry.update(origin="user-request", evidence=[])
    result = invoke(tmp_path, request)
    assert result.returncode == 0, result.stdout
    output = json.loads(result.stdout)
    pending = [i for t in output["topics"] for i in t["items"]]
    trusted = variant.startswith("trusted")
    # The goal-only journal choice evidences the goal, not the drafted scope, rules and
    # acceptance: every variant is presented, and only trusted provenance keeps the goal.
    assert "target-users" in [i["id"] for i in pending], output
    stored = next(i for i in json.loads((tmp_path / CONCEPT).read_text())["requirements"] if i["id"] == "target-users")
    assert stored["status"] == "pending"
    assert stored["pending_reason"]
    assert next(i for i in pending if i["id"] == "target-users")["pending_reason"]
    assert ("legacy_reuse" in stored) is trusted, stored
    if variant != "missing-journal":
        assert json.loads((tmp_path / JOURNAL).read_text()) == journal
    freeze = {"operation": "freeze", "include": ["target-users"], "exclude": {t: "Later scope" for t in TOPICS[1:]},
              "batch_id": "scope", "user_reference": "scope user turn", "reason": "Choose release scope"}
    frozen = invoke(tmp_path, freeze)
    assert frozen.returncode == 1, frozen.stdout
    if trusted:
        assert decide(tmp_path, [{"operation": "confirm", "id": "target-users", "reason": "Projection approved"}],
                      "projection").returncode == 0
        stored = next(i for i in json.loads((tmp_path / CONCEPT).read_text())["requirements"] if i["id"] == "target-users")
        assert stored["prior_confirmation"] == item["confirmation"]
        frozen = invoke(tmp_path, freeze)
        assert frozen.returncode == 0, frozen.stdout
        batches = json.loads((tmp_path / JOURNAL).read_text())["batches"]
        assert batches[0] == journal["batches"][0] and [b["batch_id"] for b in batches] == ["prior", "projection", "scope"]
    else:
        assert decide(tmp_path, [{"operation": "confirm", "id": "target-users", "reason": "Verified"}]).returncode == 0
        assert invoke(tmp_path, freeze).returncode == 0


# ---- Finding 6: invalid Run Policy repair needs explicit user answers, keeps an audit -----------

INVALID = {"wrong-value": {"on_repeated_failure": "retry", "on_needs_iteration": "accept", "on_safety_warning": "halt"},
           "missing-key": {"on_repeated_failure": "continue"}, "not-an-object": ["continue"]}


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("kind", ["wrong-value", "missing-key", "not-an-object", "not-json"])
def test_invalid_run_policy_is_repaired_only_by_explicit_user_answers_with_audit(tmp_path, host, kind):
    project(tmp_path, confirmed=True, host=host)
    target = tmp_path / RUN_POLICY
    target.parent.mkdir(parents=True, exist_ok=True)
    if kind == "not-json":
        target.write_text("{not json")
    else:
        write(tmp_path, RUN_POLICY, INVALID[kind])
    broken = target.read_bytes()
    asked = cli(tmp_path, "--run-policy")
    assert asked.returncode == 1 and not asked.stderr, (asked.stdout, asked.stderr)
    output = json.loads(asked.stdout)
    assert output["status"] == "needs_run_policy" and output["questions"] == {
        "on_repeated_failure": ["continue", "halt"], "on_needs_iteration": ["halt_with_report", "auto_fix_once", "accept"],
        "on_safety_warning": ["continue", "halt"]}
    assert "invalid" in json.dumps(output).lower()
    event = cli(tmp_path, "--policy-event", "on_needs_iteration")
    assert event.returncode == 1 and json.loads(event.stdout)["status"] == "blocked"
    for request in ({"operation": "run-policy", "answers": POLICY},
                    {"operation": "run-policy", "answers": dict(POLICY, on_safety_warning="ignore"), "user_reference": "run entry"},
                    {"operation": "run-event", "event": "on_needs_iteration", "answers": POLICY, "user_reference": "run entry"}):
        rejected = invoke(tmp_path, request)
        assert rejected.returncode == 1 and json.loads(rejected.stdout)["status"] == "blocked", (request, rejected.stdout)
        assert target.read_bytes() == broken
        assert not (tmp_path / REPAIRS).exists()
    repaired = invoke(tmp_path, {"operation": "run-policy", "answers": POLICY, "user_reference": "run entry user turn"})
    assert repaired.returncode == 0, repaired.stdout
    assert json.loads(repaired.stdout) == {"status": "run_policy_ready", "policy": POLICY, "questions": []}
    assert json.loads(target.read_text()) == POLICY
    audit = json.loads((tmp_path / REPAIRS).read_text())
    assert len(audit) == 1 and audit[0]["answers"] == POLICY and audit[0]["user_reference"] == "run entry user turn"
    assert audit[0]["previous"] == (broken.decode() if kind == "not-json" else INVALID[kind])
    assert audit[0]["reason"]
    assert json.loads(cli(tmp_path, "--run-policy").stdout)["policy"] == POLICY
    assert json.loads(cli(tmp_path, "--policy-event", "on_repeated_failure").stdout)["action"] == "continue"
    # A valid recorded policy is never silently replaced by later answers.
    again = invoke(tmp_path, {"operation": "run-policy", "answers": dict(POLICY, on_repeated_failure="halt"),
                              "user_reference": "second attempt"})
    assert again.returncode == 0 and json.loads(again.stdout)["policy"] == POLICY
    assert json.loads(target.read_text()) == POLICY and len(json.loads((tmp_path / REPAIRS).read_text())) == 1
    assert not (tmp_path / JOURNAL).exists()
