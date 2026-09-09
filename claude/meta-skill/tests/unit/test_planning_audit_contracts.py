"""#13 planning-time audit obligations that a gate can actually enforce.

`bootstrap-node-expansion-qa` names three blocker codes. The part of each that is a
structured contract — a declared repair route the orchestrators can dispatch, a deferred
effect proof with a named downstream owner, a promised document with its verification
argv — is enforced here at the copied public bootstrap gate. Whether a graph shape is a
QA loop at all, or whether a node's prose promises a document, stays a semantic judgment
for the node-spec audit; these are copied-CLI seam tests, not host dialogue proof.
"""
import json

import pytest

from .test_bootstrap_scope import (ATTENTION_CONTRACT_BODY, REF, REQUIREMENTS, confirm_plan,
                                   gate, project, write)

WORKFLOW = ".allforai/bootstrap/workflow.json"
READINESS_SPEC = ".allforai/bootstrap/unattended-run-readiness-spec.json"
SPECS = ".allforai/bootstrap/node-specs"
EFFECT_SECTION = "\n\n## Effect Verification\nA real request proves the export.\n"


def add_nodes(root, *nodes):
    """Add nodes to the plan and record the confirmation the presented list received."""
    workflow = json.loads((root / WORKFLOW).read_text())
    for node in nodes:
        node.setdefault("goal", "Deliver " + node["node_id"])
        node.setdefault("capability", "implement")
        node.setdefault("decision_inputs", [REQUIREMENTS])
        node.setdefault("requirement_refs", [REF])
        node.setdefault("responsibilities", ["implementation"])
        node.setdefault("source_inputs", ["orders.py"])
        node.setdefault("exit_artifacts", [".allforai/bootstrap/%s.json" % node["node_id"]])
        workflow["nodes"].append(node)
        write(root, node["exit_artifacts"][0], {"status": "passed"})
        write_spec(root, node)
    write(root, WORKFLOW, workflow)
    confirm_plan(root, reason="Presented the loop nodes with the plan")


def write_spec(root, node, *, body=ATTENTION_CONTRACT_BODY + EFFECT_SECTION, **overrides):
    frontmatter = dict(node, **overrides)
    (root / SPECS / (node["node_id"] + ".md")).write_text(
        "---\n" + json.dumps(frontmatter) + "\n---\n" + body)


def loop(root, **overrides):
    spec = json.loads((root / READINESS_SPEC).read_text())
    declared = {"scope": "orders-export", "qa_node_ids": ["verify-export"],
                "repair_node_id": "repair-export", "closure_node_ids": ["accept-export"],
                "max_attempts": 2}
    declared.update(overrides)
    spec["required_repair_loops"] = [declared]
    write(root, READINESS_SPEC, spec)


def qa_loop_project(root, *, closure_blocked_by=("repair-export", "verify-export")):
    project(root, confirmed=True)
    add_nodes(root,
              {"node_id": "verify-export", "capability": "product-verify"},
              {"node_id": "repair-export", "hard_blocked_by": ["verify-export"]},
              {"node_id": "accept-export", "hard_blocked_by": list(closure_blocked_by)})
    loop(root)


def refused(root, code):
    result = gate(root, "validate_bootstrap.py")
    assert result.returncode == 1, result.stdout
    assert not result.stderr, result.stderr
    assert code in result.stdout, result.stdout
    return json.loads(result.stdout)["errors"]


def accepted(root):
    result = gate(root, "validate_bootstrap.py")
    assert result.returncode == 0, result.stdout


def test_a_fully_declared_repair_loop_is_accepted(tmp_path):
    qa_loop_project(tmp_path)
    accepted(tmp_path)


@pytest.mark.parametrize("overrides", [
    {"qa_node_ids": []},
    {"closure_node_ids": []},
    {"qa_node_ids": ["repair-export"]},
    {"closure_node_ids": ["repair-export"]},
], ids=["no-qa-source", "no-closure-holder", "repair-is-its-own-qa", "repair-is-its-own-closure"])
def test_a_loop_that_routes_nothing_is_refused(tmp_path, overrides):
    """A wired edge is not a route: the orchestrators dispatch the repair from this
    declaration, so a loop with no source or no holder never runs."""
    qa_loop_project(tmp_path)
    loop(tmp_path, **overrides)
    refused(tmp_path, "undeclared_repair_loop_routing")


def test_closure_that_never_waits_for_the_qa_rerun_is_refused(tmp_path):
    qa_loop_project(tmp_path, closure_blocked_by=("repair-export",))
    errors = refused(tmp_path, "undeclared_repair_loop_routing")
    assert any("accept-export" in error and "verify-export" in error for error in errors), errors


def test_a_deferred_effect_needs_a_downstream_owner_that_proves_it(tmp_path):
    project(tmp_path, confirmed=True)
    add_nodes(tmp_path, {"node_id": "cross-module-stitch", "hard_blocked_by": ["deliver-export"]})
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow["nodes"][0]["downstream_effect_owner"] = "cross-module-stitch"
    write(tmp_path, WORKFLOW, workflow)
    write_spec(tmp_path, workflow["nodes"][0])
    accepted(tmp_path)


@pytest.mark.parametrize("owner", ["", "no-such-node", "deliver-export"],
                         ids=["empty", "missing", "itself"])
def test_an_unresolvable_effect_owner_is_refused(tmp_path, owner):
    project(tmp_path, confirmed=True)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow["nodes"][0]["downstream_effect_owner"] = owner
    write(tmp_path, WORKFLOW, workflow)
    write_spec(tmp_path, workflow["nodes"][0])
    refused(tmp_path, "unowned_effect_stage")


def test_an_effect_owner_that_does_not_run_after_this_node_is_refused(tmp_path):
    """A sibling that may be dispatched in parallel cannot prove this node's full effect."""
    project(tmp_path, confirmed=True)
    add_nodes(tmp_path, {"node_id": "sibling"})
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow["nodes"][0]["downstream_effect_owner"] = "sibling"
    write(tmp_path, WORKFLOW, workflow)
    write_spec(tmp_path, workflow["nodes"][0])
    refused(tmp_path, "unowned_effect_stage")


def test_an_owner_without_effect_verification_cannot_accept_the_deferral(tmp_path):
    project(tmp_path, confirmed=True)
    add_nodes(tmp_path, {"node_id": "cross-module-stitch", "hard_blocked_by": ["deliver-export"]})
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    owner = next(n for n in workflow["nodes"] if n["node_id"] == "cross-module-stitch")
    write_spec(tmp_path, owner, body=ATTENTION_CONTRACT_BODY)
    workflow["nodes"][0]["downstream_effect_owner"] = "cross-module-stitch"
    write(tmp_path, WORKFLOW, workflow)
    write_spec(tmp_path, workflow["nodes"][0])
    refused(tmp_path, "unowned_effect_stage")


def test_an_effect_owner_declared_in_the_spec_alone_is_refused(tmp_path):
    project(tmp_path, confirmed=True)
    add_nodes(tmp_path, {"node_id": "cross-module-stitch", "hard_blocked_by": ["deliver-export"]})
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    write_spec(tmp_path, workflow["nodes"][0], downstream_effect_owner="cross-module-stitch")
    refused(tmp_path, "unowned_effect_stage")


def test_a_promised_document_needs_its_verification_argv(tmp_path):
    """A document declared without a project-specific check against current source has no gate."""
    project(tmp_path, confirmed=True)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    node = workflow["nodes"][0]
    node["responsibilities"] = ["implementation", "documentation", "verification"]
    node["required_documents"] = [".allforai/bootstrap/artifacts/orders-export-guide.md"]
    node["document_verification"] = {}
    write(tmp_path, WORKFLOW, workflow)
    write_spec(tmp_path, node)
    refused(tmp_path, "document_verification")

    node["document_verification"] = {
        ".allforai/bootstrap/artifacts/orders-export-guide.md": ["python3", "-c", "print('checked')"]}
    write(tmp_path, WORKFLOW, workflow)
    write_spec(tmp_path, node)
    accepted(tmp_path)


def test_a_document_promised_in_the_node_spec_alone_has_no_contract(tmp_path):
    project(tmp_path, confirmed=True)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    node = workflow["nodes"][0]
    write_spec(tmp_path, node,
               required_documents=[".allforai/bootstrap/artifacts/orders-export-guide.md"],
               document_verification={".allforai/bootstrap/artifacts/orders-export-guide.md":
                                      ["python3", "-c", "print('checked')"]})
    errors = refused(tmp_path, "missing_document_contract")
    assert any("required_documents" in error for error in errors), errors
