"""Decision-gate discrimination and the unresolved-choice blocker (C1, C2).

`decision-*.json` is a name three contract families share: the A0 coverage audit
output (`bootstrap-audits.md:264`), a recorded CLI request envelope, a requirement
source, and the Phase A decision artifact itself (`:287`). Only the last records a
product choice, and only its `decision` field says whether the user has made one.
Presence is not resolution, and a partial or placeholder artifact is not a
non-decision. These exercise the copied public CLI gates in temporary projects on
both host adapters; actual host dialogue proof belongs to T15.
"""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from .test_bootstrap_scope import (ATTENTION_CONTRACT_BODY, REF, REQUIREMENTS, SCRIPTS,
                                   gate, project, publish_contract, write)
from .test_evidence_freshness import invoke as freshness_invoke
from .test_freshness_admission_corrections import HOSTS, NODE, WORKFLOW, _bootstrap, _readiness

DECISION = ".allforai/tech-spec/decision-platform-stack.json"
COVERAGE = ".allforai/bootstrap/decision-coverage.json"
CLI_REQUEST = ".allforai/bootstrap/decision-request-1.json"
JOURNAL = ".allforai/product-concept/decision-journal.json"
SECOND = "warehouse"
SECOND_DECISION = ".allforai/tech-spec/decision-stock-source.json"
GATES = ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py")
# The contract gate publishes against the node's own acceptance; the bootstrap gate is
# the artifact under test here, so the contract is verified by loading the plan it binds.
CONTRACT_CHECK = [sys.executable, "-c",
                  "import json; json.load(open('.allforai/bootstrap/workflow.json'))['nodes']"]
RESOLVED = {"id": "platform-stack", "decision": "Node + Postgres",
            "rationale": "The user chose the stack at interactive bootstrap", "status": "confirmed"}
UNRESOLVED = {
    "null-choice": {"id": "platform-stack", "decision": None, "status": "pending",
                    "rationale": "The user has not chosen a platform stack"},
    "empty-choice": {"id": "platform-stack", "decision": "   ", "rationale": "Not chosen yet"},
    "status-pending": dict(RESOLVED, status="pending"),
    "no-decision-key": {"id": "platform-stack", "status": "pending", "rationale": "Queued for Phase A"},
    "placeholder": {},
    "absent": None,
    # A pending choice that also carries a sibling family's keys. Recognising a family by
    # one key would hand either of these a free pass; the shape must be the whole contract.
    "envelope-keys": {"id": "platform-stack", "status": "pending", "operation": "choose"},
    "journal-keys": {"id": "platform-stack", "status": "pending", "decision": None,
                     "rationale": "", "schema_version": 1, "batches": []},
    "requirement-keys": {"id": "platform-stack", "status": "pending", "requirements": []},
    # A sibling that does not hold its own shape is not a sibling.
    "malformed-audit": {"id": "platform-stack", "status": "pending",
                        "captured": "all", "missing": None},
}


def _coverage_audit():
    """The A0 output `bootstrap-audits.md:264` requires before Phase A."""
    return {"status": "complete", "captured": [{"id": "platform-stack", "node_id": NODE}],
            "missing": [{"id": "retention", "rationale": "Retention window is unowned",
                         "consumer_node": NODE}]}


def _cli_request():
    """A recorded product_intent request envelope, not a product choice."""
    return {"operation": "decide", "batch_id": "platform", "topic": "Platform stack",
            "user_reference": "bootstrap user turn 4", "actions": []}


def _spec(root, node):
    (root / ".allforai/bootstrap/node-specs" / (node["node_id"] + ".md")).write_text(
        "---\n" + json.dumps(node) + "\n---\n" + ATTENTION_CONTRACT_BODY)


def _wire(root, *paths, node_id=NODE):
    """Add decision_inputs the way `bootstrap-audits.md:272` prescribes, spec included."""
    workflow = json.loads((root / WORKFLOW).read_text())
    node = next(n for n in workflow["nodes"] if n["node_id"] == node_id)
    node["decision_inputs"] = [*node.get("decision_inputs", []), *paths]
    write(root, WORKFLOW, workflow)
    _spec(root, node)


def _second_node(root, *decision_paths):
    """A second scoped delivery whose choices are its own."""
    node = {"node_id": SECOND, "goal": "Deliver warehouse stock counts", "capability": "implement",
            "exit_artifacts": [".allforai/bootstrap/stock.json"], "requirement_refs": [REF],
            "responsibilities": ["implementation"], "source_inputs": [],
            "decision_inputs": [REQUIREMENTS, *decision_paths]}
    write(root, ".allforai/bootstrap/stock.json", {"status": "passed"})
    workflow = json.loads((root / WORKFLOW).read_text())
    workflow["nodes"].append(node)
    write(root, WORKFLOW, workflow)
    _spec(root, node)


def _audit(host, kind, path):
    """The contract's own shape validator, run from the host plugin root."""
    scripts = SCRIPTS if host == "claude" else Path(__file__).resolve().parents[4] / "codex/meta-skill/scripts"
    return subprocess.run([sys.executable, str(scripts / "validate_audit_outputs.py"), kind, str(path)],
                          text=True, capture_output=True)


def _gates(root):
    results = {name: gate(root, name) for name in GATES}
    for name, result in results.items():
        assert "Traceback" not in result.stderr and not result.stderr, (name, result.stderr)
    return results


def _repair(root, node_id=NODE):
    result, report = freshness_invoke(root, "check")
    assert result.returncode == 0, (result.stdout, result.stderr)
    return report["nodes"][node_id].get("repair")


@pytest.mark.parametrize("host", HOSTS)
def test_required_audit_output_and_cli_request_are_not_orphan_decisions(tmp_path, host):
    """The A0 artifact the contract requires must not block the gate it precedes."""
    project(tmp_path, confirmed=True, host=host)
    write(tmp_path, COVERAGE, _coverage_audit())
    write(tmp_path, CLI_REQUEST, _cli_request())
    assert _audit(host, "decision-coverage", tmp_path / COVERAGE).returncode == 0
    publish_contract(tmp_path, verification_command=CONTRACT_CHECK)
    for name, result in _gates(tmp_path).items():
        assert result.returncode == 0, (name, result.stdout)
    assert _readiness(tmp_path)[1]["status"] == "ready"


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("shape", ["complete", "partial", "placeholder", "malformed", "non-object",
                                  "envelope-keys", "journal-keys", "malformed-audit"])
def test_an_unwired_decision_artifact_still_blocks_whatever_its_shape(tmp_path, host, shape):
    """A shape test discriminates families; it never dismisses a decision it cannot read."""
    project(tmp_path, confirmed=True, host=host)
    write(tmp_path, COVERAGE, _coverage_audit())
    target = tmp_path / DECISION
    target.parent.mkdir(parents=True, exist_ok=True)
    if shape == "malformed":
        target.write_text("{not json")
    elif shape == "non-object":
        target.write_text("[]")
    else:
        write(tmp_path, DECISION, {"complete": RESOLVED, "partial": UNRESOLVED["no-decision-key"],
                                   "placeholder": {}}.get(shape) or UNRESOLVED[shape])
    result = gate(tmp_path, "check_decision_inputs.py")
    assert result.returncode == 1, result.stdout
    assert "orphan (unwired): " + DECISION in result.stdout, result.stdout
    assert "orphan (unwired): " + COVERAGE not in result.stdout, result.stdout


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("shape", sorted(UNRESOLVED))
def test_an_unresolved_wired_choice_blocks_every_public_driver_and_routes_to_bootstrap(tmp_path, host, shape):
    """An unmade choice wired the protocol's way is not authorization to run."""
    project(tmp_path, confirmed=True, host=host)
    if UNRESOLVED[shape] is not None:
        write(tmp_path, DECISION, UNRESOLVED[shape])
    _wire(tmp_path, DECISION)
    publish_contract(tmp_path, verification_command=CONTRACT_CHECK)

    lens = _gates(tmp_path)["check_decision_inputs.py"]
    assert lens.returncode == 1, lens.stdout
    assert "pending_decision" in lens.stdout and DECISION in lens.stdout, lens.stdout

    code, errors = _bootstrap(tmp_path)
    assert code == 1 and any("pending_decision" in error and DECISION in error for error in errors), errors

    code, report = _readiness(tmp_path)
    assert code == 1 and report["status"] == "not_ready", report
    pending = [b for b in report["blockers"] if b["code"] == "pending_decision"]
    assert [b.get("node_id") for b in pending] == [NODE], report["blockers"]

    assert _repair(tmp_path) == {"owner": "interactive-bootstrap", "responsibilities": ["product-decision"]}


@pytest.mark.parametrize("host", HOSTS)
def test_a_resolved_choice_restores_readiness_only_with_fresh_evidence(tmp_path, host):
    """Answering the question clears the decision blocker; the contract it changed is stale."""
    project(tmp_path, confirmed=True, host=host)
    write(tmp_path, DECISION, UNRESOLVED["null-choice"])
    _wire(tmp_path, DECISION)
    publish_contract(tmp_path, verification_command=CONTRACT_CHECK)
    assert _readiness(tmp_path)[1]["status"] == "not_ready"

    write(tmp_path, DECISION, RESOLVED)
    lens = gate(tmp_path, "check_decision_inputs.py")
    assert lens.returncode == 0, lens.stdout
    code, report = _readiness(tmp_path)
    assert code == 1 and report["status"] == "not_ready", report
    assert not [b for b in report["blockers"] if b["code"] == "pending_decision"], report["blockers"]
    assert [b for b in report["blockers"] if b.get("node_id") == NODE], report["blockers"]

    publish_contract(tmp_path, verification_command=CONTRACT_CHECK)
    for name, result in _gates(tmp_path).items():
        assert result.returncode == 0, (name, result.stdout)
    assert _readiness(tmp_path)[1]["status"] == "ready"


@pytest.mark.parametrize("host", HOSTS)
def test_settled_and_non_decision_inputs_leave_unrelated_work_executable(tmp_path, host):
    """Only the node whose own choice is unmade is held; wired audit inputs judge nothing."""
    project(tmp_path, confirmed=True, host=host)
    write(tmp_path, COVERAGE, _coverage_audit())
    write(tmp_path, DECISION, RESOLVED)
    write(tmp_path, JOURNAL, {"schema_version": "1.0", "batches": [{
        "batch_id": "platform", "source": "user_session", "user_reference": "bootstrap turn 4",
        "decisions": [{"question": "Which stack?", "chosen": "Node + Postgres",
                       "rationale": "The user chose it", "supersedes": None}]}]})
    # A settled choice, the A0 audit output and the journal, all wired as inputs.
    _wire(tmp_path, DECISION, COVERAGE, JOURNAL)
    publish_contract(tmp_path, verification_command=CONTRACT_CHECK)
    for name, result in _gates(tmp_path).items():
        assert result.returncode == 0, (name, result.stdout)

    write(tmp_path, SECOND_DECISION, {"id": "stock-source", "decision": None,
                                      "rationale": "The user has not chosen a stock source"})
    _second_node(tmp_path, SECOND_DECISION)
    code, report = _readiness(tmp_path)
    assert code == 1 and report["status"] == "not_ready", report
    pending = [b for b in report["blockers"] if b["code"] == "pending_decision"]
    assert [b.get("node_id") for b in pending] == [SECOND], report["blockers"]
    assert _repair(tmp_path, SECOND) == {"owner": "interactive-bootstrap",
                                         "responsibilities": ["product-decision"]}
    assert _repair(tmp_path) != {"owner": "interactive-bootstrap", "responsibilities": ["product-decision"]}
