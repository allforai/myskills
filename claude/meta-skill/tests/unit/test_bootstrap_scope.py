"""Scripted bootstrap artifacts exercised through the generated-project CLI gates.

The agent chooses the route and graph; these tests supply its explicit artifacts,
not a substitute semantic planner. Actual host dialogue proof belongs to T15.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from .test_validate_bootstrap import ATTENTION_CONTRACT_BODY
from .test_validate_unattended_readiness import _minimal_project

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
REQUIREMENTS = ".allforai/bootstrap/local-requirements.json"
REF = {"path": REQUIREMENTS, "id": "export", "revision": 1}


def write(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value), encoding="utf-8")


def project(root, *, confirmed=False, documents=False, host="claude"):
    _minimal_project(root)
    scripts = root / ".allforai/bootstrap/scripts"
    source_scripts = (SCRIPTS if host == "claude" else
                      Path(__file__).resolve().parents[4] / "codex/meta-skill/scripts")
    for name in ("check_artifacts.py", "validate_bootstrap.py", "validate_unattended_readiness.py", "product_intent.py"):
        shutil.copy2(source_scripts / "orchestrator" / name, scripts / name)
    shutil.copy2(source_scripts / "check_decision_inputs.py", scripts / "check_decision_inputs.py")
    write(root, ".allforai/bootstrap/bootstrap-profile.json", {
        "task_goal": "Add order CSV export", "task_route": "local-change",
        "task_scope": {"areas": ["orders"], "requirement_refs": [REF]},
    })
    requirement = {
        "id": "export", "revision": 1, "scope": ["orders"],
        "goal": "Export the current account's orders as CSV",
        "business_rules": ["Only the signed-in account's orders may be exported"],
        "acceptance": ["Another account's orders never appear in the CSV"],
        "status": "confirmed" if confirmed else "pending",
    }
    if confirmed:
        requirement["confirmation"] = {
            "source": "user", "reference": "bootstrap user turn 2",
            "decision_id": "confirm-export-1", "reason": "Account isolation is required",
        }
    write(root, REQUIREMENTS, {"requirements": [requirement]})
    (root / "orders.py").write_text("def list_orders(account): return []\n")
    if documents:
        write(root, ".allforai/product-concept/product-concept.json", {
            "vision": "Keep existing retail direction", "unrelated": ["warehouse"]})
    node = {
        "node_id": "deliver-export", "goal": "Deliver account-scoped order export",
        "capability": "implement", "exit_artifacts": [".allforai/bootstrap/export-report.json"],
        "requirement_refs": [REF],
        "responsibilities": ["implementation", "documentation", "verification"],
        "decision_inputs": [REQUIREMENTS],
    }
    write(root, ".allforai/bootstrap/workflow.json", {"nodes": [node], "transition_log": []})
    (root / ".allforai/bootstrap/node-specs/design.md").unlink()
    spec = "---\n" + json.dumps(node) + "\n---\n" + ATTENTION_CONTRACT_BODY
    (root / ".allforai/bootstrap/node-specs/deliver-export.md").write_text(spec)
    return requirement


def gate(root, name):
    arg = root / ".allforai/bootstrap" if name == "validate_bootstrap.py" else root
    return subprocess.run([sys.executable, str(root / ".allforai/bootstrap/scripts" / name), str(arg)],
                          text=True, capture_output=True, cwd=root)


def test_unanswered_local_requirement_blocks_generated_bootstrap(tmp_path):
    project(tmp_path)
    result = gate(tmp_path, "validate_bootstrap.py")
    assert result.returncode == 1, result.stdout
    assert "pending_requirement" in result.stdout


def test_unanswered_local_requirement_blocks_both_run_preflight_gates(tmp_path):
    project(tmp_path)
    for name in ("validate_unattended_readiness.py", "check_decision_inputs.py"):
        result = gate(tmp_path, name)
        assert result.returncode == 1, (name, result.stdout, result.stderr)
        assert "pending_requirement" in result.stdout


def test_code_derived_confirmed_label_is_not_user_approval(tmp_path):
    requirement = project(tmp_path, confirmed=True)
    requirement["confirmation"]["source"] = "code"
    write(tmp_path, REQUIREMENTS, {"requirements": [requirement]})
    result = gate(tmp_path, "validate_bootstrap.py")
    assert result.returncode == 1, result.stdout
    assert "pending_requirement" in result.stdout


def test_ambiguous_route_cannot_fall_back_from_existing_code(tmp_path):
    project(tmp_path, confirmed=True)
    path = tmp_path / ".allforai/bootstrap/bootstrap-profile.json"
    profile = json.loads(path.read_text())
    profile["task_route"] = ""
    write(tmp_path, ".allforai/bootstrap/bootstrap-profile.json", profile)
    result = gate(tmp_path, "validate_bootstrap.py")
    assert result.returncode == 1, result.stdout
    assert "pending_task_route" in result.stdout


def test_local_request_cannot_gain_whole_product_reverse_node(tmp_path):
    project(tmp_path, confirmed=True)
    path = tmp_path / ".allforai/bootstrap/workflow.json"
    workflow = json.loads(path.read_text())
    workflow["nodes"][0]["capability"] = "reverse-concept"
    write(tmp_path, ".allforai/bootstrap/workflow.json", workflow)
    result = gate(tmp_path, "validate_unattended_readiness.py")
    assert result.returncode == 1, result.stdout
    assert "scope_route_conflict" in result.stdout


def test_new_and_reconstruction_routes_leave_product_confirmation_pending(tmp_path):
    for route in ("new-product", "product-reconstruction"):
        root = tmp_path / route
        project(root, confirmed=True)
        if route == "new-product":
            (root / "orders.py").unlink()
        else:
            workflow_path = root / ".allforai/bootstrap/workflow.json"
            workflow = json.loads(workflow_path.read_text())
            workflow["nodes"][0]["capability"] = "reverse-concept"
            write(root, ".allforai/bootstrap/workflow.json", workflow)
        write(root, ".allforai/bootstrap/bootstrap-profile.json", {
            "task_goal": "Establish the desired product", "task_route": route,
            "task_scope": {"areas": ["product"], "requirement_refs": []},
        })
        result = gate(root, "validate_bootstrap.py")
        assert result.returncode == 1, (route, result.stdout)
        assert "pending_product_confirmation" in result.stdout
        assert "scope_route_conflict" not in result.stdout


def test_empty_acceptance_cannot_authorize_execution(tmp_path):
    requirement = project(tmp_path, confirmed=True)
    requirement["acceptance"] = []
    write(tmp_path, REQUIREMENTS, {"requirements": [requirement]})
    result = gate(tmp_path, "validate_bootstrap.py")
    assert result.returncode == 1, result.stdout
    assert "invalid_requirement" in result.stdout


def test_changed_requirement_requires_new_scoped_confirmation(tmp_path):
    requirement = project(tmp_path, confirmed=True)
    changed = dict(requirement, revision=2, status="pending", goal="Export every account")
    write(tmp_path, REQUIREMENTS, {"requirements": [requirement, changed]})
    before = (tmp_path / REQUIREMENTS).read_bytes()
    result = gate(tmp_path, "validate_bootstrap.py")
    assert result.returncode == 1, result.stdout
    assert "stale_requirement" in result.stdout
    assert (tmp_path / REQUIREMENTS).read_bytes() == before


def test_unrelated_confirmed_requirement_cannot_authorize_local_change(tmp_path):
    requirement = project(tmp_path, confirmed=True)
    requirement["scope"] = ["warehouse"]
    write(tmp_path, REQUIREMENTS, {"requirements": [requirement]})
    result = gate(tmp_path, "validate_bootstrap.py")
    assert result.returncode == 1, result.stdout
    assert "requirement_scope_conflict" in result.stdout


def test_scoped_workflow_needs_documentation_as_well_as_code_and_verification(tmp_path):
    project(tmp_path, confirmed=True)
    path = tmp_path / ".allforai/bootstrap/workflow.json"
    workflow = json.loads(path.read_text())
    workflow["nodes"][0]["responsibilities"] = ["implementation", "verification"]
    write(tmp_path, ".allforai/bootstrap/workflow.json", workflow)
    result = gate(tmp_path, "validate_unattended_readiness.py")
    assert result.returncode == 1, result.stdout
    assert "missing_scope_responsibility" in result.stdout
    assert "documentation" in result.stdout


def test_empty_goal_is_invalid_even_with_confirmed_requirement(tmp_path):
    project(tmp_path, confirmed=True)
    path = tmp_path / ".allforai/bootstrap/bootstrap-profile.json"
    profile = json.loads(path.read_text())
    profile["task_goal"] = " "
    write(tmp_path, ".allforai/bootstrap/bootstrap-profile.json", profile)
    result = gate(tmp_path, "validate_bootstrap.py")
    assert result.returncode == 1, result.stdout
    assert "invalid_scope" in result.stdout


@pytest.mark.parametrize("change", [
    {"areas": "orders"},
    {"requirement_refs": [{"path": REQUIREMENTS, "id": "export", "revision": True}]},
])
def test_malformed_scope_is_rejected_without_touching_authority(tmp_path, change):
    project(tmp_path, confirmed=True)
    path = tmp_path / ".allforai/bootstrap/bootstrap-profile.json"
    profile = json.loads(path.read_text())
    profile["task_scope"].update(change)
    write(tmp_path, ".allforai/bootstrap/bootstrap-profile.json", profile)
    before = (tmp_path / REQUIREMENTS).read_bytes()
    result = gate(tmp_path, "validate_bootstrap.py")
    assert result.returncode == 1, result.stdout
    assert "invalid_scope" in result.stdout
    assert (tmp_path / REQUIREMENTS).read_bytes() == before


def test_requirement_is_an_actual_node_input_not_only_a_coverage_label(tmp_path):
    project(tmp_path, confirmed=True)
    path = tmp_path / ".allforai/bootstrap/workflow.json"
    workflow = json.loads(path.read_text())
    workflow["nodes"][0]["decision_inputs"] = []
    write(tmp_path, ".allforai/bootstrap/workflow.json", workflow)
    result = gate(tmp_path, "check_decision_inputs.py")
    assert result.returncode == 1, result.stdout
    assert "scope_requirement_unwired" in result.stdout


def test_node_spec_cannot_silently_lose_requirement_contract(tmp_path):
    project(tmp_path, confirmed=True)
    spec = tmp_path / ".allforai/bootstrap/node-specs/deliver-export.md"
    data = json.loads(spec.read_text().split("---")[1])
    data.pop("requirement_refs")
    spec.write_text("---\n" + json.dumps(data) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    result = gate(tmp_path, "validate_bootstrap.py")
    assert result.returncode == 1, result.stdout
    assert "requirement_refs" in result.stdout


def test_missing_profile_cannot_disable_scope_checks_for_generated_nodes(tmp_path):
    project(tmp_path, confirmed=True)
    (tmp_path / ".allforai/bootstrap/bootstrap-profile.json").unlink()
    result = gate(tmp_path, "validate_unattended_readiness.py")
    assert result.returncode == 1, result.stdout
    assert "invalid_scope" in result.stdout


@pytest.mark.parametrize("documents", [False, True])
@pytest.mark.parametrize("host", ["claude", "codex"])
def test_confirmed_local_change_reuses_decision_and_preserves_unrelated_work(tmp_path, documents, host):
    project(tmp_path, confirmed=True, documents=documents, host=host)
    workflow_path = tmp_path / ".allforai/bootstrap/workflow.json"
    workflow = json.loads(workflow_path.read_text())
    old_ref = {"path": ".allforai/bootstrap/warehouse-requirements.json", "id": "stock", "revision": 1}
    old = {"node_id": "warehouse", "goal": "Retain completed warehouse work", "capability": "implement",
           "exit_artifacts": [".allforai/bootstrap/stock.json"], "requirement_refs": [old_ref],
           "decision_inputs": [old_ref["path"]], "responsibilities": ["implementation"]}
    write(tmp_path, old_ref["path"], {"requirements": [{"id": "stock", "revision": 1, "status": "confirmed"}]})
    write(tmp_path, ".allforai/bootstrap/stock.json", {"status": "passed", "count": 3})
    workflow["nodes"].append(old)
    workflow["transition_log"] = [{"node_id": "warehouse", "status": "completed"}]
    write(tmp_path, ".allforai/bootstrap/workflow.json", workflow)
    (tmp_path / ".allforai/bootstrap/node-specs/warehouse.md").write_text(
        "---\n" + json.dumps(old) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
        result = gate(tmp_path, name)
        assert result.returncode == 0, (name, result.stdout, result.stderr)
    assert all(p.read_bytes() == content for p, content in before.items())
    assert not (tmp_path / ".allforai/product-concept/concept-baseline.json").exists()
