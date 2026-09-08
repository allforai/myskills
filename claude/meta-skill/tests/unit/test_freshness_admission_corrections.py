"""Freshness admission at the copied public gates (#12 review blockers 1 and 5).

Intent-aware nodes cannot omit `source_inputs` and silently bypass freshness;
malformed declarations produce structured fail-closed results instead of a
crash or a false pass; retained legacy work keeps its gate behavior without
invented provenance. These exercise copied CLIs in temporary projects on both
host adapters, not actual Claude/Codex host dialogue.
"""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from .test_bootstrap_scope import ATTENTION_CONTRACT_BODY, gate, project, publish_contract, write
from .test_evidence_freshness import invoke as freshness_invoke

WORKFLOW = ".allforai/bootstrap/workflow.json"
NODE = "deliver-export"
HOSTS = ["claude", "codex"]
REPO = Path(__file__).resolve().parents[4]


def _no_crash(result):
    assert "Traceback" not in result.stderr, result.stderr
    assert not result.stderr, result.stderr


def _bootstrap(root):
    result = gate(root, "validate_bootstrap.py")
    _no_crash(result)
    return result.returncode, json.loads(result.stdout)["errors"]


def _readiness(root):
    result = gate(root, "validate_unattended_readiness.py", "--write-report")
    _no_crash(result)
    report = json.loads((root / ".allforai/bootstrap/unattended-run-readiness.json").read_text())
    return result.returncode, report


def _artifacts(root, node_id=NODE):
    result = subprocess.run([sys.executable, str(root / ".allforai/bootstrap/scripts/check_artifacts.py"),
                             str(root / WORKFLOW), "--node", node_id, "--json"], text=True, capture_output=True, cwd=root)
    _no_crash(result)
    assert result.returncode == 0, result.stdout
    return json.loads(result.stdout)


def _reconcile(root, node_id=NODE):
    result = subprocess.run([sys.executable, str(root / ".allforai/bootstrap/scripts/reconcile_bootstrap_workflow.py"),
                             str(root), "--write"], text=True, capture_output=True, cwd=root)
    _no_crash(result)
    assert result.returncode == 0, result.stdout
    output = json.loads(result.stdout)
    node = next(n for n in output["state_index"]["nodes"] if n["node_id"] == node_id)
    plan = next(i for i in output["reconciliation_plan"]["items"] if i["node_id"] == node_id)
    return node, plan


def _blockers(report, code):
    return [b for b in report["blockers"] if b["code"] == code]


def _set_node(root, **fields):
    workflow = json.loads((root / WORKFLOW).read_text())
    node = next(n for n in workflow["nodes"] if n["node_id"] == NODE)
    for key, value in fields.items():
        if value is _ABSENT:
            node.pop(key, None)
        else:
            node[key] = value
    write(root, WORKFLOW, workflow)
    (root / ".allforai/bootstrap/node-specs" / (NODE + ".md")).write_text(
        "---\n" + json.dumps(node) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    return node


_ABSENT = object()


@pytest.mark.parametrize("host", HOSTS)
def test_intent_aware_node_without_source_inputs_fails_closed_until_declared_and_published(tmp_path, host):
    project(tmp_path, confirmed=True, host=host, source_inputs=None)
    write(tmp_path, ".allforai/bootstrap/export-report.json", {"status": "passed"})

    code, errors = _bootstrap(tmp_path)
    assert code == 1 and any(NODE in e and "source_inputs" in e for e in errors), errors
    code, report = _readiness(tmp_path)
    assert code == 1 and report["status"] == "not_ready"
    assert [b["node_id"] for b in _blockers(report, "missing_source_inputs")] == [NODE]
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False
    assert checked["freshness"]["status"] == "undeclared" and checked["freshness"]["admission"] == "missing"
    node, plan = _reconcile(tmp_path)
    assert node["artifact_readiness"] == "blocked" and plan["action"] == "invalidate"
    assert "missing_source_inputs" in node["artifacts"][0]["blockers"]
    assert "missing_source_inputs" in plan["reasons"]

    # Editing the product source cannot be observed yet, and nothing claims it was.
    (tmp_path / "orders.py").write_text("def list_orders(account): return [account]\n")
    assert _artifacts(tmp_path)["all_exist"] is False

    # Declaring the source and publishing verified evidence admits the node.
    _set_node(tmp_path, source_inputs=["orders.py"])
    publish_contract(tmp_path, kind="evidence", verification_command=[
        sys.executable, "-c", "import json; assert json.load(open('.allforai/bootstrap/export-report.json'))['status'] == 'passed'"])
    assert _bootstrap(tmp_path)[0] == 0
    code, report = _readiness(tmp_path)
    assert code == 0 and report["status"] == "ready", report["blockers"]
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is True and checked["freshness"]["admission"] == "declared"
    node, plan = _reconcile(tmp_path)
    assert node["artifact_readiness"] == "complete" and plan["action"] == "keep"

    # Traceability is now active: a further source edit invalidates the evidence.
    (tmp_path / "orders.py").write_text("def list_orders(account): return [42]\n")
    assert _artifacts(tmp_path)["freshness"]["status"] == "stale"
    code, report = _readiness(tmp_path)
    assert code == 1 and [b["node_id"] for b in _blockers(report, "stale_evidence")] == [NODE]
    node, plan = _reconcile(tmp_path)
    assert node["artifact_readiness"] == "blocked" and "input_freshness" in plan["reasons"]


MALFORMED = [
    ("source_inputs", "orders.py"),
    ("source_inputs", None),
    ("source_inputs", {"path": "orders.py"}),
    ("source_inputs", [42]),
    ("source_inputs", [""]),
    ("source_inputs", ["/etc/orders.py"]),
    ("source_inputs", ["../orders.py"]),
    ("input_dependencies", "policy.txt"),
    ("required_documents", [{"path": "docs/export.md"}]),
]


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("field,value", MALFORMED, ids=[f"{f}={v!r}" for f, v in MALFORMED])
def test_malformed_declaration_is_a_structured_fail_closed_result_at_every_gate(tmp_path, host, field, value):
    project(tmp_path, confirmed=True, host=host)
    write(tmp_path, ".allforai/bootstrap/export-report.json", {"status": "passed"})
    _set_node(tmp_path, **{field: value})

    code, errors = _bootstrap(tmp_path)
    assert code == 1 and any(NODE in e and field in e for e in errors), errors
    code, report = _readiness(tmp_path)
    assert code == 1 and report["status"] == "not_ready"
    blockers = _blockers(report, "invalid_source_inputs")
    assert [b["node_id"] for b in blockers] == [NODE] and field in blockers[0]["message"]
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False
    assert checked["freshness"]["status"] == "invalid" and checked["freshness"]["admission"] == "invalid"
    assert field in checked["freshness"]["reason"]
    node, plan = _reconcile(tmp_path)
    assert node["artifact_readiness"] == "blocked" and plan["action"] == "invalidate"
    assert "invalid_source_inputs" in node["artifacts"][0]["blockers"]
    assert "invalid_source_inputs" in plan["reasons"]
    # The diagnostic CLI itself keeps refusing rather than crashing.
    result, checked = freshness_invoke(tmp_path, "check")
    assert result.returncode == 1 and checked["status"] == "invalid" and not result.stderr


@pytest.mark.parametrize("host", HOSTS)
def test_malformed_sibling_declaration_withdraws_verification_from_valid_nodes(tmp_path, host):
    project(tmp_path, confirmed=True, host=host)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow["nodes"].append({
        "node_id": "warehouse", "goal": "Keep warehouse history", "capability": "implement",
        "decision_inputs": [], "source_inputs": ["warehouse.py"],
        "exit_artifacts": [".allforai/bootstrap/stock.json"]})
    workflow["transition_log"] = [{"node" if host == "codex" else "node_id": "warehouse", "status": "completed"}]
    write(tmp_path, WORKFLOW, workflow)
    (tmp_path / ".allforai/bootstrap/node-specs/warehouse.md").write_text(
        "---\n" + json.dumps(workflow["nodes"][1]) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    (tmp_path / "warehouse.py").write_text("stock = 10\n")
    write(tmp_path, ".allforai/bootstrap/stock.json", {"status": "passed"})
    publish_contract(tmp_path, "warehouse", kind="evidence", verification_command=[
        sys.executable, "-c", "import json; assert json.load(open('.allforai/bootstrap/stock.json'))['status'] == 'passed'"])
    assert _artifacts(tmp_path, "warehouse")["all_exist"] is True

    _set_node(tmp_path, source_inputs="orders.py")
    checked = _artifacts(tmp_path, "warehouse")
    assert checked["all_exist"] is False and checked["freshness"]["status"] == "invalid"
    assert NODE in checked["freshness"]["reason"]
    code, report = _readiness(tmp_path)
    assert code == 1 and [b["node_id"] for b in _blockers(report, "invalid_source_inputs")] == [NODE]
    node, _ = _reconcile(tmp_path, "warehouse")
    assert node["artifact_readiness"] == "blocked" and node["freshness"]["status"] == "invalid"


@pytest.mark.parametrize("host", HOSTS)
def test_retained_legacy_node_keeps_gate_behavior_without_invented_provenance(tmp_path, host):
    project(tmp_path, confirmed=True, host=host)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    legacy = {"node_id": "warehouse", "goal": "Keep warehouse history", "capability": "implement",
              "decision_inputs": [], "exit_artifacts": [".allforai/bootstrap/stock.json"]}
    workflow["nodes"].append(legacy)
    workflow["transition_log"] = [{"node" if host == "codex" else "node_id": "warehouse", "status": "completed"}]
    write(tmp_path, WORKFLOW, workflow)
    (tmp_path / ".allforai/bootstrap/node-specs/warehouse.md").write_text(
        "---\n" + json.dumps(legacy) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    write(tmp_path, ".allforai/bootstrap/stock.json", {"status": "passed"})

    assert _bootstrap(tmp_path)[0] == 0
    code, report = _readiness(tmp_path)
    assert code == 0 and report["status"] == "ready", report["blockers"]
    assert [w["node_id"] for w in report["warnings"] if w["code"] == "undeclared_source_inputs"] == ["warehouse"]
    checked = _artifacts(tmp_path, "warehouse")
    assert checked["all_exist"] is True
    assert checked["freshness"] == {"status": "undeclared", "readiness_status": "undeclared", "admission": "legacy",
                                    "reason": checked["freshness"]["reason"]}
    node, plan = _reconcile(tmp_path, "warehouse")
    assert node["artifact_readiness"] == "complete" and plan["action"] == "keep"
    assert node["freshness"]["status"] == "undeclared" and node["artifacts"][0]["blockers"] == []

    # Reopening the retained node makes it intent-aware work again: it must declare.
    workflow["transition_log"].append({"node" if host == "codex" else "node_id": "warehouse", "status": "reopened"})
    legacy["requirement_refs"] = workflow["nodes"][0]["requirement_refs"]
    legacy["decision_inputs"] = workflow["nodes"][0]["decision_inputs"]
    legacy["responsibilities"] = ["implementation"]
    write(tmp_path, WORKFLOW, workflow)
    (tmp_path / ".allforai/bootstrap/node-specs/warehouse.md").write_text(
        "---\n" + json.dumps(legacy) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    code, errors = _bootstrap(tmp_path)
    assert code == 1 and any("warehouse" in e and "source_inputs" in e for e in errors), errors
    code, report = _readiness(tmp_path)
    assert [b["node_id"] for b in _blockers(report, "missing_source_inputs")] == ["warehouse"]
    assert _artifacts(tmp_path, "warehouse")["all_exist"] is False


def test_legacy_workflow_without_any_declaration_keeps_freshness_out_of_the_gate(tmp_path):
    from .test_validate_unattended_readiness import _minimal_project
    sys.path.insert(0, str(REPO / "claude/meta-skill/scripts/orchestrator"))
    from check_artifacts import check_node_artifacts
    _minimal_project(tmp_path)
    write(tmp_path, ".allforai/game-design/design.json", {"status": "passed"})
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    checked = check_node_artifacts(workflow["nodes"][0], tmp_path)
    assert checked["freshness"] is None and checked["all_exist"] is True


TEMPLATES = [
    "claude/meta-skill/skills/bootstrap/SKILL.md",
    "claude/meta-skill/knowledge/node-spec-template.md",
    "claude/meta-skill/knowledge/bootstrap-planning.md",
    "claude/meta-skill/knowledge/orchestrator-template.md",
    "claude/meta-skill/knowledge/input-freshness.md",
    "codex/meta-skill/knowledge/orchestrator-template.md",
    "codex/meta-skill/skills/bootstrap.md",
]


@pytest.mark.parametrize("template", TEMPLATES)
def test_planning_templates_declare_source_inputs_with_explicit_empty_rule(template):
    text = (REPO / template).read_text(encoding="utf-8")
    assert "source_inputs" in text, template
    assert "explicit `[]`" in text or "explicit []" in text, template
