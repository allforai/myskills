"""#13 planning-time audit obligations that a gate can actually enforce.

`bootstrap-node-expansion-qa` names three blocker codes. The part of each that is a
structured contract — a declared repair route the orchestrators can dispatch, a deferred
effect proof with a named downstream owner, a promised document with its verification
argv — is enforced here at the copied public bootstrap gate. Whether a graph shape is a
QA loop at all, or whether a node's prose promises a document, stays a semantic judgment
for the node-spec audit; these are copied-CLI seam tests, not host dialogue proof.
"""
import json
import sys

import pytest

from .test_bootstrap_scope import (ATTENTION_CONTRACT_BODY, REF, REQUIREMENTS, confirm_plan,
                                   gate, project, publish_contract, write)

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
    # Each added node observes and publishes its own contract, as bootstrap does; an
    # unpublished one is stale evidence and would mask the structural blocker under test.
    for node in nodes:
        publish_contract(root, node_id=node["node_id"])


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


def qa_loop_project(root, *, closure_blocked_by=("repair-export", "verify-export"), host="claude"):
    project(root, confirmed=True, host=host)
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


# The runtime entry decides the same structural rules. `/run` on Claude runs the readiness
# gate alone, Codex additionally runs the bootstrap gate; both must refuse a graph bootstrap
# refuses, from the one implementation, or an unattended run executes an unroutable loop.
def readiness(root):
    result = gate(root, "validate_unattended_readiness.py", "--write-report")
    assert not result.stderr, result.stderr
    return result


def run_refused(root, code):
    result = readiness(root)
    assert result.returncode == 1, result.stdout
    report = json.loads(result.stdout)
    assert report["status"] == "not_ready", result.stdout
    codes = [blocker["code"] for blocker in report["blockers"]]
    assert code in codes, codes
    return report


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_run_refuses_a_repair_loop_with_no_closure_holder(tmp_path, host):
    """Nothing waits for the QA rerun, so the run would close on the repair alone."""
    qa_loop_project(tmp_path, host=host)
    loop(tmp_path, closure_node_ids=[])
    report = run_refused(tmp_path, "undeclared_repair_loop_routing")
    assert [blocker["code"] for blocker in report["blockers"]] == ["undeclared_repair_loop_routing"], report
    assert report["blockers"][0]["node_id"] == "repair-export", report


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_run_refuses_an_effect_deferred_to_a_node_that_cannot_prove_it(tmp_path, host):
    """The unowned deferral is the only defect: every other axis is current, so the run
    is held by this rule alone rather than by evidence that happens to be stale."""
    project(tmp_path, confirmed=True, host=host)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow["nodes"][0]["downstream_effect_owner"] = "no-such-node"
    write(tmp_path, WORKFLOW, workflow)
    write_spec(tmp_path, workflow["nodes"][0])
    write(tmp_path, workflow["nodes"][0]["exit_artifacts"][0], {"status": "passed"})
    # The bootstrap gate now refuses this graph, so the node republishes under its own
    # passing acceptance argv; this isolates ownership from freshness, it does not weaken it.
    for kind in ("contract", "evidence"):
        publish_contract(tmp_path, kind=kind,
                         verification_command=[sys.executable, "-c", "print('checked')"])
    report = run_refused(tmp_path, "unowned_effect_stage")
    assert [blocker["code"] for blocker in report["blockers"]] == ["unowned_effect_stage"], report
    assert any("no-such-node" in blocker["message"] for blocker in report["blockers"]), report


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_run_accepts_the_canonical_declared_loop(tmp_path, host):
    """The gate that refuses an unroutable loop still admits the routable one."""
    qa_loop_project(tmp_path, host=host)
    accepted(tmp_path)
    result = readiness(tmp_path)
    assert result.returncode == 0, result.stdout
    assert json.loads(result.stdout)["status"] == "ready", result.stdout


# A run-time entry reads whatever `workflow.json` currently holds. When a node identifier
# cannot key the graph, the gate must publish a current refusal at the same public seam
# both hosts already use: an exception publishes nothing and leaves the previous `ready`
# report standing as this run's answer.
REPORT = ".allforai/bootstrap/unattended-run-readiness.json"
UNADDRESSABLE = [1, 0, 3.5, True, None, ["verify-export"], {"id": "verify-export"}, "", "  "]


def published(root):
    return json.loads((root / REPORT).read_text())


def stray_node(node_id):
    """A node that is complete on every axis except the one under test."""
    return {"node_id": node_id, "goal": "Deliver the stray node", "capability": "implement",
            "decision_inputs": [REQUIREMENTS], "requirement_refs": [REF],
            "responsibilities": ["implementation"], "source_inputs": ["orders.py"],
            "exit_artifacts": [".allforai/bootstrap/stray.json"]}


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("node_id", UNADDRESSABLE, ids=[repr(v) for v in UNADDRESSABLE])
def test_run_refuses_a_node_the_graph_cannot_address(tmp_path, host, node_id):
    qa_loop_project(tmp_path, host=host)
    assert readiness(tmp_path).returncode == 0
    assert published(tmp_path)["status"] == "ready"

    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow["nodes"].append(stray_node(node_id))
    write(tmp_path, WORKFLOW, workflow)

    report = run_refused(tmp_path, "malformed_workflow_node")
    # No rule below the shape gate offers a verdict on the addressable remainder — that
    # subset is not the graph the user has. `invalid_scope` is the scope gate refusing the
    # same malformed record on its own authority, not a graph rule reading past the fault.
    assert set(blocker["code"] for blocker in report["blockers"]) <= {
        "malformed_workflow_node", "invalid_scope"}, report
    # The superseded `ready` does not survive as this run's verdict on either host.
    assert published(tmp_path) == report
@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("node_id", [1, 3.5, True, None, "", "  "],
                         ids=["int", "float", "bool", "null", "empty", "blank"])
def test_the_bootstrap_gate_refuses_the_same_unaddressable_node(tmp_path, host, node_id):
    """One rule, two entries: a graph `/run` refuses is a graph bootstrap refuses."""
    qa_loop_project(tmp_path, host=host)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow["nodes"].append(stray_node(node_id))
    write(tmp_path, WORKFLOW, workflow)

    result = gate(tmp_path, "validate_bootstrap.py")

    assert result.returncode == 1, result.stdout
    assert not result.stderr, result.stderr
    assert any("node_id" in error for error in json.loads(result.stdout)["errors"]), result.stdout


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_run_refuses_a_repeated_node_identifier(tmp_path, host):
    qa_loop_project(tmp_path, host=host)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow["nodes"].append(dict(workflow["nodes"][0]))
    write(tmp_path, WORKFLOW, workflow)

    report = run_refused(tmp_path, "malformed_workflow_node")
    assert report["blockers"][0]["node_id"] == workflow["nodes"][0]["node_id"], report


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("workflow", [b"{not json", b'{"nodes": [{"node_id": "\xff\xfe"}]}'],
                         ids=["unparseable", "undecodable"])
def test_run_refuses_a_workflow_it_cannot_read_and_supersedes_the_ready_report(
        tmp_path, host, workflow):
    qa_loop_project(tmp_path, host=host)
    assert readiness(tmp_path).returncode == 0
    assert published(tmp_path)["status"] == "ready"

    (tmp_path / WORKFLOW).write_bytes(workflow)

    report = run_refused(tmp_path, "missing_workflow")
    assert published(tmp_path) == report


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_run_refuses_a_node_brief_it_cannot_decode(tmp_path, host):
    """The non-interactive, fallback and long-task rules are read from this text; an
    unreadable brief yields no verdict, and no verdict is not an acceptance."""
    qa_loop_project(tmp_path, host=host)
    (tmp_path / SPECS / "verify-export.md").write_bytes(b"---\nnode_id: verify-export\n---\n\xff\xfe")

    report = run_refused(tmp_path, "unreadable_node_spec")
    assert any(blocker.get("node_id") == "verify-export" for blocker in report["blockers"]), report


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_the_canonical_loop_is_still_admitted_after_the_shape_gate(tmp_path, host):
    """The shape gate must not become a blanket refusal of a graph both hosts can run."""
    qa_loop_project(tmp_path, host=host)
    accepted(tmp_path)
    result = readiness(tmp_path)
    assert result.returncode == 0, result.stdout
    assert json.loads(result.stdout)["status"] == "ready", result.stdout
    assert published(tmp_path)["blockers"] == []


# A safety halt refuses the run at the same public seam both hosts already call, and is
# never cleared by the gate that reads it.
SAFETY_MARKER = ".allforai/bootstrap/safety-quarantine.json"
SAFETY_LOCK = ".allforai/bootstrap/safety-quarantine.lock"


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_run_refuses_a_recorded_safety_quarantine(tmp_path, host):
    qa_loop_project(tmp_path, host=host)
    assert readiness(tmp_path).returncode == 0
    write(tmp_path, SAFETY_MARKER, {
        "schema_version": 1, "status": "quarantined", "node_ids": ["verify-export"],
        "events": [{"recorded_at": "2026-09-09T10:00:00Z", "reason": "wave halted",
                    "nodes": [{"node_id": "verify-export", "exit_artifacts": []}]}]})

    report = run_refused(tmp_path, "unresolved_safety_quarantine")
    assert published(tmp_path) == report
    assert (tmp_path / SAFETY_MARKER).exists(), "the gate must never clear a safety marker"


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_run_refuses_a_held_safety_lock_with_no_marker(tmp_path, host):
    """The publication that would have written the marker failed or was interrupted."""
    qa_loop_project(tmp_path, host=host)
    assert readiness(tmp_path).returncode == 0
    (tmp_path / SAFETY_LOCK).mkdir(parents=True)

    report = run_refused(tmp_path, "unreconciled_safety_halt")
    assert not (tmp_path / SAFETY_MARKER).exists(), report
    assert (tmp_path / SAFETY_LOCK).exists(), "the gate must never remove the fence"
    assert published(tmp_path) == report
