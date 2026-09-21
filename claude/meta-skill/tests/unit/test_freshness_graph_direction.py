"""Invalidation travels the way the flow does.

A node's `source_inputs` are what it reads to produce its own work. When they
reach into the write scope of a node that depends on it, the graph is inverted:
delivering that work stales the node that planned it, the planner sits behind a
freeze a run may not reopen, and neither can publish again. Planning refuses the
inversion as `inverted_source_inputs`; the engine, which also meets plans written
before that refusal existed, declines to deadlock on one — a path covered by a
transitive consumer's declared `parallel_write_scopes` does not invalidate its
planner. Only that declaration exempts, and only downstream: a node cannot exempt
its own inputs, and an undeclared write scope exempts nothing.
"""
import json
import sys

from .test_bootstrap_scope import (ATTENTION_CONTRACT_BODY, REF, REQUIREMENTS, confirm_plan, project,
                                   publish_contract, write)
from .test_freshness_admission_corrections import _artifacts, _bootstrap, NODE, WORKFLOW

DOWNSTREAM = "ship-export"
# The engine meets plans the planner refuses: a workflow written before that refusal
# existed is what the exemption is for, so these publish against a plain contract check
# rather than the plan gate that now rejects the inversion outright.
LEGACY_CHECK = [sys.executable, "-c", "import json; json.load(open('.allforai/bootstrap/workflow.json'))"]


def _consumer(root, *, write_scopes):
    """Add a node that depends on NODE and declares what it writes."""
    node = {"node_id": DOWNSTREAM, "goal": "Ship the export NODE planned",
            "capability": "implement", "hard_blocked_by": [NODE],
            "exit_artifacts": [".allforai/bootstrap/shipped.json"],
            "source_inputs": ["orders.py"], "requirement_refs": [REF],
            "responsibilities": ["implementation"], "decision_inputs": [REQUIREMENTS]}
    if write_scopes is not None:
        node["parallel_write_scopes"] = write_scopes
    workflow = json.loads((root / WORKFLOW).read_text())
    workflow["nodes"] = [n for n in workflow["nodes"] if n.get("node_id") != DOWNSTREAM]
    workflow["nodes"].append(node)
    write(root, WORKFLOW, workflow)
    confirm_plan(root, reason="Presented the delivery node with the plan")
    (root / ".allforai/bootstrap/node-specs" / (DOWNSTREAM + ".md")).write_text(
        "---\n" + json.dumps(node) + "\n---\n" + ATTENTION_CONTRACT_BODY)


def _deliver(root):
    """The delivery edits the product source it is responsible for."""
    (root / "orders.py").write_text("def export(account):\n    return [account]\n", encoding="utf-8")


def test_declared_downstream_write_scope_does_not_stale_its_planner(tmp_path):
    project(tmp_path, confirmed=True)
    _consumer(tmp_path, write_scopes=["orders.py"])
    publish_contract(tmp_path, verification_command=LEGACY_CHECK)

    _deliver(tmp_path)

    # Only the contract is published here, so the node is still owed its evidence;
    # what the delivery must not do is show up as changed input on the node that planned it.
    checked = _artifacts(tmp_path, NODE)
    assert checked["freshness"]["admission"] == "declared"
    assert "files" not in checked["freshness"]["diff"], checked["freshness"]["diff"]


def test_undeclared_write_scope_exempts_nothing(tmp_path):
    project(tmp_path, confirmed=True)
    _consumer(tmp_path, write_scopes=None)
    publish_contract(tmp_path, verification_command=LEGACY_CHECK)

    _deliver(tmp_path)

    checked = _artifacts(tmp_path, NODE)
    assert checked["freshness"]["status"] == "stale", checked["freshness"]
    assert "orders.py" in checked["freshness"]["diff"]["files"], checked["freshness"]["diff"]


def test_a_node_cannot_exempt_its_own_inputs(tmp_path):
    """The exemption follows the graph, never a node's claim about itself."""
    project(tmp_path, confirmed=True)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    node = next(n for n in workflow["nodes"] if n["node_id"] == NODE)
    node["parallel_write_scopes"] = ["orders.py"]
    write(tmp_path, WORKFLOW, workflow)
    (tmp_path / ".allforai/bootstrap/node-specs" / (NODE + ".md")).write_text(
        "---\n" + json.dumps(node) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    publish_contract(tmp_path, verification_command=LEGACY_CHECK)

    _deliver(tmp_path)

    checked = _artifacts(tmp_path, NODE)
    assert checked["freshness"]["diff"]["files"] == {"orders.py": "changed"}, checked["freshness"]["diff"]


def test_planning_refuses_the_inversion(tmp_path):
    project(tmp_path, confirmed=True)
    _consumer(tmp_path, write_scopes=["orders.py"])

    code, errors = _bootstrap(tmp_path)

    assert code == 1
    inverted = [e for e in errors if e.startswith("inverted_source_inputs:")]
    assert inverted, errors
    assert NODE in inverted[0] and DOWNSTREAM in inverted[0] and "orders.py" in inverted[0]


def test_a_plan_that_reads_what_nobody_writes_downstream_is_accepted(tmp_path):
    project(tmp_path, confirmed=True)
    _consumer(tmp_path, write_scopes=["shipping/**"])

    code, errors = _bootstrap(tmp_path)

    assert not [e for e in errors if e.startswith("inverted_source_inputs:")], errors
    assert code in (0, 1)  # unrelated fixture errors stay this test's business only if they name us
