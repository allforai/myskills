"""Inherited product acceptance versus this node's stage evidence, through the copied CLI.

T15 recorded the ambiguity: the plan copies the complete user-confirmed acceptance onto
every consuming node, so a documentation node inherits "only one volunteer holds the
claim" and cannot tell whether it must implement concurrency or describe it. These are
generated-project seam tests — a real `plan` run, then the copied public gates on what it
wrote. They prove the generated brief allocates the obligation and that the two losses
stay refused (deleted acceptance, a deferral whose owner does not carry the requirement).
Actual host behaviour, i.e. whether an executor follows the distinction, is not proven here.
"""
import json

import pytest

from .test_bootstrap_scope import confirm_plan, gate, project, publish_contract, write
from .test_product_intent_session import CONCEPT, TOPICS, decide, invoke
from .test_product_intent_session import draft as base_draft
from .test_validate_bootstrap import ATTENTION_CONTRACT_BODY

WORKFLOW = ".allforai/bootstrap/workflow.json"
SPECS = ".allforai/bootstrap/node-specs"
GUIDE = ".allforai/bootstrap/artifacts/claim-guide.md"
CONCURRENCY = "For simultaneous claim attempts, only one volunteer holds the claim."
EFFECT = "\n\n## Effect Verification\nA real concurrent claim run proves the winner is unique.\n"
DOC_EFFECT = ("\n\n## Effect Verification\nThe guide is diffed against claim.py; the concurrent "
              "claim effect itself is proved by release-verification.\n")


def frozen_new_product(root, host):
    """Confirm and freeze a new-product scope whose acceptance includes a claim race."""
    project(root, host=host)
    (root / "claim.py").write_text("def claim(volunteer): return True\n")
    request = base_draft()
    request.update(route="new-product", facts=[], goal="Deliver volunteer request matching")
    for item in request["items"]:
        item.update(origin="user-request", evidence=[])
    request["items"][0]["acceptance"] = [CONCURRENCY]
    assert invoke(root, request).returncode == 0
    actions = [{"operation": "confirm", "id": topic, "reason": "Chosen direction"} for topic in TOPICS]
    actions.append({"operation": "answer", "id": "conflict", "answer": "Exclude archived orders",
                    "reason": "Release scope"})
    assert decide(root, actions).returncode == 0
    freeze = {"operation": "freeze", "batch_id": "scope", "user_reference": "user scope decision",
              "reason": "Release direction", "include": list(TOPICS), "exclude": {}}
    frozen = invoke(root, freeze)
    assert frozen.returncode == 0, (frozen.stdout, frozen.stderr)


def plan_request(*, owner="release-verification", acceptance_node_ids=TOPICS):
    """Three real stages over one confirmed scope: build, document, verify."""
    def node(node_id, capability, goal, responsibilities, body, **extra):
        return {"node_id": node_id, "capability": capability, "goal": goal,
                "intent_ids": list(TOPICS), "responsibilities": responsibilities,
                "source_inputs": ["claim.py"],
                "exit_artifacts": [".allforai/bootstrap/%s.json" % node_id],
                "body": ATTENTION_CONTRACT_BODY + body, **extra}

    return {"operation": "plan", "not_applicable": {
        "experience": "Operator CLI in this scope has no user interface"}, "nodes": [
        node("build-claim-flow", "implement", "Build the durable atomic claim",
             ["product", "technical", "implementation"], EFFECT),
        node("operator-documentation", "generate-artifacts", "Document the claim rule as built",
             ["documentation"], DOC_EFFECT, hard_blocked_by=["build-claim-flow"],
             required_documents=[GUIDE], downstream_effect_owner=owner,
             document_verification={GUIDE: ["python3", "-c", "print('checked')"]}),
        node("release-verification", "product-verify", "Prove the claim race on a real run",
             ["verification"], EFFECT, hard_blocked_by=["operator-documentation"]),
    ]}


def planned(root, host, **overrides):
    frozen_new_product(root, host)
    result = invoke(root, plan_request(**overrides))
    return result


def accepted_plan(root, host, **overrides):
    result = planned(root, host, **overrides)
    assert result.returncode == 0, (result.stdout, result.stderr)
    confirm_plan(root, stage="plan-projection", reason="Presented the projected plan")
    for node_id in ("build-claim-flow", "operator-documentation", "release-verification"):
        publish_contract(root, node_id)
    return json.loads((root / WORKFLOW).read_text())


def spec(root, node_id):
    return (root / SPECS / (node_id + ".md")).read_text()


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_documentation_node_owes_its_stage_evidence_for_the_inherited_acceptance(tmp_path, host):
    """The docs node keeps the whole confirmed acceptance and is told what it owes for it."""
    workflow = accepted_plan(tmp_path, host)
    nodes = {node["node_id"]: node for node in workflow["nodes"]}
    inherited = nodes["operator-documentation"]["acceptance"]
    assert CONCURRENCY in inherited
    # Scope is not reallocated: every consuming node still carries the identical full list.
    assert all(node["acceptance"] == inherited for node in workflow["nodes"])

    documentation = spec(tmp_path, "operator-documentation")
    assert CONCURRENCY in documentation
    assert "Confirmed acceptance (inherited requirement scope, complete and unmodifiable):" in documentation
    assert "declared responsibilities (documentation)" in documentation
    assert "document_verification" in documentation and "downstream_effect_owner" in documentation
    assert "stale_requirement" in documentation and "unowned_effect_stage" in documentation
    # The distinction is per node, not one universal paragraph: each stage names its own duty.
    assert "declared responsibilities (product, technical, implementation)" in spec(tmp_path, "build-claim-flow")
    assert "declared responsibilities (verification)" in spec(tmp_path, "release-verification")

    for name in ("validate_bootstrap.py", "check_decision_inputs.py"):
        checked = gate(tmp_path, name)
        assert checked.returncode == 0, (name, checked.stdout, checked.stderr)


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_a_stage_may_not_delete_the_inherited_acceptance_it_cannot_prove(tmp_path, host):
    """Dropping the race criterion from the documentation stage is scope loss, not scoping."""
    workflow = accepted_plan(tmp_path, host)
    node = next(n for n in workflow["nodes"] if n["node_id"] == "operator-documentation")
    body = spec(tmp_path, "operator-documentation")
    node["acceptance"] = [a for a in node["acceptance"] if a != CONCURRENCY]
    write(tmp_path, WORKFLOW, workflow)
    (tmp_path / SPECS / "operator-documentation.md").write_text(
        "---\n" + json.dumps(node) + "\n---\n" + body.split("\n---\n", 1)[1].replace(CONCURRENCY, ""))
    refused = gate(tmp_path, "validate_bootstrap.py")
    assert refused.returncode == 1 and "stale_requirement" in refused.stdout, refused.stdout
    assert "operator-documentation" in refused.stdout


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_a_node_spec_may_not_quietly_narrow_the_confirmed_acceptance(tmp_path, host):
    """A spec that rewords the inherited criterion no longer mirrors the confirmed one."""
    accepted_plan(tmp_path, host)
    path = tmp_path / SPECS / "operator-documentation.md"
    path.write_text(path.read_text().replace(CONCURRENCY, "The guide mentions concurrent claims."))
    refused = gate(tmp_path, "validate_bootstrap.py")
    assert refused.returncode == 1 and "acceptance" in refused.stdout, refused.stdout


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_a_deferred_full_effect_needs_an_owner_that_carries_the_requirement(tmp_path, host):
    """Deferring is allowed; deferring to a node that does not consume the requirement is not."""
    frozen_new_product(tmp_path, host)
    request = plan_request(owner="release-acceptance")
    request["nodes"].append({
        "node_id": "release-acceptance", "capability": "concept-acceptance",
        "goal": "Accept the matching direction", "intent_ids": [TOPICS[1]],
        "responsibilities": ["verification"], "source_inputs": ["claim.py"],
        "hard_blocked_by": ["release-verification"],
        "exit_artifacts": [".allforai/bootstrap/release-acceptance.json"],
        "body": ATTENTION_CONTRACT_BODY + EFFECT})
    blocked = invoke(tmp_path, request)
    assert blocked.returncode == 1, blocked.stdout
    error = json.loads(blocked.stdout)["error"]
    assert "unowned_effect_stage" in error and "release-acceptance" in error, error
    assert not (tmp_path / SPECS / "operator-documentation.md").exists()


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_a_deferral_to_a_node_outside_the_plan_is_refused(tmp_path, host):
    """A named owner that no node answers for leaves the full effect unheld."""
    workflow = accepted_plan(tmp_path, host)
    node = next(n for n in workflow["nodes"] if n["node_id"] == "operator-documentation")
    body = spec(tmp_path, "operator-documentation").split("\n---\n", 1)[1]
    node["downstream_effect_owner"] = "later-release"
    write(tmp_path, WORKFLOW, workflow)
    (tmp_path / SPECS / "operator-documentation.md").write_text(
        "---\n" + json.dumps(node) + "\n---\n" + body)
    refused = gate(tmp_path, "validate_bootstrap.py")
    assert refused.returncode == 1 and "unowned_effect_stage" in refused.stdout, refused.stdout
