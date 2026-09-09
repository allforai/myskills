"""Retained product work through copied sessions and the three public gates."""
import json

import pytest

from .test_bootstrap_scope import confirm_plan, project, write, gate, codex_transition, publish_contract
from .test_product_intent_session import invoke, draft, decide, TOPICS
from .test_validate_bootstrap import ATTENTION_CONTRACT_BODY

WORKFLOW = ".allforai/bootstrap/workflow.json"
GATES = ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py")


def prepared_plan(root, host):
    project(root, confirmed=True, host=host)
    historical = {"node_id": "warehouse", "goal": "Retain warehouse results",
                  "capability": "implement", "requirement_refs": [], "decision_inputs": [],
                  "product_goals": ["Historical warehouse goal"],
                  "acceptance": ["Historical inventory reconciles"],
                  "exit_artifacts": [".allforai/bootstrap/stock.json"]}
    write(root, ".allforai/bootstrap/stock.json", {"status": "passed", "source_revision": "warehouse-v1"})
    spec = root / ".allforai/bootstrap/node-specs/warehouse.md"
    spec.write_text("---\n" + json.dumps(historical) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    workflow = json.loads((root / WORKFLOW).read_text())
    workflow["nodes"].append(historical)
    workflow["transition_log"] = [] if host == "codex" else [{"node_id": "warehouse", "status": "completed"}]
    write(root, WORKFLOW, workflow)
    if host == "codex":
        codex_transition(root, "warehouse", "completed")
    history = json.loads((root / WORKFLOW).read_text())["transition_log"]
    request = draft()
    request["questions"] = []
    assert invoke(root, request).returncode == 0
    assert decide(root, [{"operation": "confirm", "id": t, "reason": "Chosen direction"} for t in TOPICS]).returncode == 0
    assert invoke(root, {"operation": "freeze", "include": TOPICS, "exclude": {},
                         "batch_id": "scope", "user_reference": "user scope decision", "reason": "Release"}).returncode == 0
    return {"operation": "plan", "nodes": [historical, {
        "node_id": "deliver-orders", "capability": "implement", "goal": "Deliver confirmed orders",
        "intent_ids": list(TOPICS), "responsibilities": ["product", "technical", "implementation", "documentation", "verification"],
        "source_inputs": ["orders.py"],
        "exit_artifacts": [".allforai/bootstrap/order-verification.json"], "body": ATTENTION_CONTRACT_BODY}],
        "transition_log": history, "not_applicable": {"experience": "Headless API"}}


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("references", ["empty", "absent", "historical"])
def test_product_plan_preserves_unrelated_completed_work_and_provenance(tmp_path, host, references):
    plan = prepared_plan(tmp_path, host)
    historical = plan["nodes"][0]
    if references == "absent":
        historical.pop("requirement_refs")
    elif references == "historical":
        path = ".allforai/bootstrap/decision-warehouse.json"
        historical["requirement_refs"] = [{"path": path, "id": "stock", "revision": 1}]
        historical["decision_inputs"] = [path]
        write(tmp_path, path, {"requirements": [{"id": "stock", "revision": 1, "status": "confirmed"}]})
    (tmp_path / ".allforai/bootstrap/node-specs/warehouse.md").write_text(
        "---\n" + json.dumps(historical) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    paths = [".allforai/bootstrap/node-specs/warehouse.md", ".allforai/bootstrap/stock.json", "orders.py"]
    before = {p: (tmp_path / p).read_bytes() for p in paths}
    result = invoke(tmp_path, plan)
    confirm_plan(tmp_path, stage="plan-projection", reason="Presented the projected plan")
    assert result.returncode == 0, (result.stdout, result.stderr)
    workflow = json.loads(result.stdout)["workflow"]
    assert workflow["nodes"][0] == plan["nodes"][0]
    assert workflow["transition_log"] == plan["transition_log"]
    assert all((tmp_path / p).read_bytes() == content for p, content in before.items())
    publish_contract(tmp_path, "deliver-orders")  # Only the new scoped node observes; history keeps its contract.
    assert all((tmp_path / p).read_bytes() == content for p, content in before.items())
    for name in GATES:
        result = gate(tmp_path, name)
        assert result.returncode == 0, (name, result.stdout, result.stderr)


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("change", ["inserted", "reopened", "current-scope"])
def test_completed_history_does_not_exempt_new_reopened_or_current_scope_work(tmp_path, host, change):
    plan = prepared_plan(tmp_path, host)
    assert invoke(tmp_path, plan).returncode == 0
    confirm_plan(tmp_path, stage="plan-projection", reason="Presented the projected plan")
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    if change == "inserted":
        node = {"node_id": "unapproved", "capability": "implement", "goal": "Unapproved feature",
                "requirement_refs": [], "decision_inputs": [],
                "exit_artifacts": [".allforai/bootstrap/unapproved.json"]}
        workflow["nodes"].append(node)
        plan["nodes"].append({**node, "intent_ids": [], "body": ATTENTION_CONTRACT_BODY})
        (tmp_path / ".allforai/bootstrap/node-specs/unapproved.md").write_text(
            "---\n" + json.dumps(node) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    elif change == "reopened":
        # An event from the other adapter still supersedes native completion.
        event = {"node_id" if host == "codex" else "node": "warehouse", "status": "failed"}
        workflow["transition_log"].append(event)
        plan["transition_log"].append(event)
        plan["nodes"][0].update(intent_ids=[], body=ATTENTION_CONTRACT_BODY)
    else:
        node = workflow["nodes"][1]
        node["acceptance"] = ["Old implementation is sufficient"]
        event = {"node" if host == "codex" else "node_id": "deliver-orders", "status": "completed"}
        workflow["transition_log"].append(event)
        # Planning must reject excluded intent even on completed current work.
        plan["transition_log"].append(event)
        plan["nodes"][1]["intent_ids"].append("unconfirmed-intent")
    write(tmp_path, WORKFLOW, workflow)
    for name in GATES:
        result = gate(tmp_path, name)
        assert result.returncode == 1, (name, result.stdout, result.stderr)
        assert "Product" in result.stdout or "product" in result.stdout, result.stdout
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = invoke(tmp_path, plan)
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert all(p.read_bytes() == content for p, content in before.items())


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_supplied_completed_brief_keeps_historical_acceptance(tmp_path, host):
    plan = prepared_plan(tmp_path, host)
    node = plan["nodes"][0]
    node.update(intent_ids=[], body=ATTENTION_CONTRACT_BODY)
    spec = tmp_path / ".allforai/bootstrap/node-specs/warehouse.md"
    spec.unlink()
    result = invoke(tmp_path, plan)
    confirm_plan(tmp_path, stage="plan-projection", reason="Presented the projected plan")
    assert result.returncode == 0, (result.stdout, result.stderr)
    historical = json.loads(result.stdout)["workflow"]["nodes"][0]
    assert historical["product_goals"] == ["Historical warehouse goal"]
    assert historical["acceptance"] == ["Historical inventory reconciles"]
    assert historical["decision_inputs"] == []
    assert "Historical inventory reconciles" in spec.read_text()
    publish_contract(tmp_path, "deliver-orders")
    for name in GATES:
        result = gate(tmp_path, name)
        assert result.returncode == 0, (name, result.stdout, result.stderr)
