"""Scripted bootstrap artifacts exercised through the generated-project CLI gates.

The agent chooses the route and graph; these tests supply its explicit artifacts,
not a substitute semantic planner. Actual host dialogue proof belongs to T15.
"""
import importlib.util
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


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("malformed", [42, None, {}, "decision.json", [42], [""], ["  "]])
def test_retained_input_shape_rejects_stale_ready_and_recovers(tmp_path, host, malformed):
    project(tmp_path, confirmed=True, host=host)
    workflow_path = ".allforai/bootstrap/workflow.json"
    workflow = json.loads((tmp_path / workflow_path).read_text())
    retained = {"node_id": "warehouse", "goal": "Keep warehouse history",
                "capability": "implement", "decision_inputs": [],
                "exit_artifacts": [".allforai/bootstrap/stock.json"]}
    workflow["nodes"].append(retained)
    workflow["transition_log"] = [{"node" if host == "codex" else "node_id": "warehouse",
                                   "status": "completed"}]
    write(tmp_path, ".allforai/bootstrap/stock.json", {"status": "passed"})
    for inputs, expected in [([], 0), (malformed, 1), ([], 0)]:
        retained["decision_inputs"] = inputs
        write(tmp_path, workflow_path, workflow)
        (tmp_path / ".allforai/bootstrap/node-specs/warehouse.md").write_text(
            "---\n" + json.dumps(retained) + "\n---\n" + ATTENTION_CONTRACT_BODY)
        for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
            options = ("--write-report",) if name == "validate_unattended_readiness.py" else ()
            result = gate(tmp_path, name, *options)
            assert result.returncode == expected, (name, result.stdout, result.stderr)
            assert not result.stderr
        report = json.loads((tmp_path / ".allforai/bootstrap/unattended-run-readiness.json").read_text())
        assert report["status"] == ("not_ready" if expected else "ready")


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


def codex_transition(root, node_id, status):
    """Use the native generated runtime's completion producer."""
    flow_path = root / ".allforai/codex/flow.py"
    flow_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__).resolve().parents[4] /
                 "codex/meta-skill/knowledge/flow-template.py", flow_path)
    spec = importlib.util.spec_from_file_location("generated_flow", flow_path)
    flow = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(flow)
    workflow_path = root / ".allforai/bootstrap/workflow.json"
    before_count = len(json.loads(workflow_path.read_text())["transition_log"])
    flow.append_transition_if_missing(workflow_path, before_count, node_id, status,
                                      "2026-09-07T10:00:00Z", [])


def gate(root, name, *options):
    arg = root / ".allforai/bootstrap" if name == "validate_bootstrap.py" else root
    return subprocess.run([sys.executable, str(root / ".allforai/bootstrap/scripts" / name), str(arg), *options],
                          text=True, capture_output=True, cwd=root)


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_journal_backed_local_requirement_is_consumed_at_all_public_gates(tmp_path, host):
    requirement = project(tmp_path, confirmed=True, documents=True, host=host)
    journal = ".allforai/product-concept/decision-journal.json"
    write(tmp_path, journal, {"schema_version": "1.0", "batches": [{
        "batch_id": "export-choice", "source": "user_session", "topic": "Order export",
        "decisions": [{"question": "Which orders may be exported?",
                       "chosen": "Only the signed-in account's orders",
                       "rationale": "Account isolation is required", "supersedes": None}]
    }]})
    requirement["confirmation"]["reference"] = journal + "#export-choice/decisions/0"
    write(tmp_path, REQUIREMENTS, {"requirements": [requirement]})
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    for name in ("validate_bootstrap.py", "validate_unattended_readiness.py", "check_decision_inputs.py"):
        result = gate(tmp_path, name)
        assert result.returncode == 0, (name, result.stdout, result.stderr)
    assert all(p.read_bytes() == content for p, content in before.items())
    # Reusing history must not hide a newly collected, applicable decision.
    unwired = ".allforai/bootstrap/decision-export-format.json"
    write(tmp_path, unwired, {"scope": ["orders"], "status": "confirmed",
                             "chosen": "Include a header row"})
    rejected = gate(tmp_path, "check_decision_inputs.py")
    assert rejected.returncode == 1, (rejected.stdout, rejected.stderr)
    assert "orphan (unwired): " + unwired in rejected.stdout
    assert "orphan (unwired): " + journal not in rejected.stdout
    (tmp_path / unwired).unlink()
    assert gate(tmp_path, "check_decision_inputs.py").returncode == 0


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("fault", ["missing", "schema", "source", "pending", "empty-choice",
                                  "duplicate-batch", "missing-fragment", "outside-project",
                                  "removed", "superseded"])
def test_forged_journal_reference_cannot_authorize_local_requirement(tmp_path, host, fault):
    requirement = project(tmp_path, confirmed=True, host=host)
    journal = ".allforai/product-concept/decision-journal.json"
    batch = {"batch_id": "export-choice", "source": "user_session", "topic": "Order export",
             "decisions": [{"question": "Which orders?", "chosen": "Account orders",
                            "rationale": "Account isolation", "supersedes": None}]}
    data = {"schema_version": "1.0", "batches": [batch]}
    reference = journal + "#export-choice/decisions/0"
    if fault == "schema":
        data["schema_version"] = "invented"
    elif fault == "source":
        batch["source"] = "code_inference"
    elif fault == "pending":
        batch["decisions"][0]["status"] = "pending"
    elif fault == "removed":
        batch["decisions"][0]["status"] = "removed"
    elif fault == "superseded":
        data["batches"].append({"batch_id": "revised-export", "source": "user_session",
                                "topic": "Cancel export", "decisions": [{
                                    "question": "Keep export?", "chosen": "Remove export",
                                    "rationale": "No longer wanted", "supersedes": reference}]})
    elif fault == "empty-choice":
        batch["decisions"][0]["chosen"] = ""
    elif fault == "duplicate-batch":
        data["batches"].append(batch)
    elif fault == "missing-fragment":
        reference = journal
    elif fault == "outside-project":
        external = tmp_path.parent / "decision-journal.json"
        external.write_text(json.dumps(data))
        reference = str(external) + "#export-choice/decisions/0"
    if fault != "missing":
        write(tmp_path, journal, data)
    requirement["confirmation"]["reference"] = reference
    write(tmp_path, REQUIREMENTS, {"requirements": [requirement]})
    for name in ("validate_bootstrap.py", "validate_unattended_readiness.py", "check_decision_inputs.py"):
        result = gate(tmp_path, name)
        assert result.returncode == 1, (name, result.stdout, result.stderr)
        assert "invalid_scope" in result.stdout
        assert not result.stderr


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
@pytest.mark.parametrize("historical_refs", ["present", "absent", "empty"])
def test_confirmed_local_change_reuses_decision_and_preserves_unrelated_work(tmp_path, documents, host, historical_refs):
    project(tmp_path, confirmed=True, documents=documents, host=host)
    workflow_path = tmp_path / ".allforai/bootstrap/workflow.json"
    workflow = json.loads(workflow_path.read_text())
    old_ref = {"path": ".allforai/bootstrap/decision-warehouse.json", "id": "stock", "revision": 1}
    old = {"node_id": "warehouse", "goal": "Retain completed warehouse work", "capability": "implement",
           "exit_artifacts": [".allforai/bootstrap/stock.json"], "requirement_refs": [old_ref],
           "decision_inputs": [old_ref["path"]], "responsibilities": ["implementation"]}
    write(tmp_path, old_ref["path"], {"requirements": [{"id": "stock", "revision": 1, "status": "confirmed"}]})
    write(tmp_path, ".allforai/bootstrap/stock.json", {"status": "passed", "count": 3})
    if historical_refs == "absent":
        old.pop("requirement_refs")
    elif historical_refs == "empty":
        old["requirement_refs"] = []
    workflow["nodes"].append(old)
    workflow["transition_log"] = ([] if host == "codex" else
                                  [{"node_id": "warehouse", "status": "completed"}])
    write(tmp_path, ".allforai/bootstrap/workflow.json", workflow)
    if host == "codex":
        codex_transition(tmp_path, "warehouse", "completed")
    (tmp_path / ".allforai/bootstrap/node-specs/warehouse.md").write_text(
        "---\n" + json.dumps(old) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
        result = gate(tmp_path, name)
        assert result.returncode == 0, (name, result.stdout, result.stderr)
    assert all(p.read_bytes() == content for p, content in before.items())
    assert not (tmp_path / ".allforai/product-concept/concept-baseline.json").exists()


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("malformed", [
    {"nodes": None}, {"nodes": [None]}, {"nodes": ["bad"]},
    {"nodes": {}}, {"nodes": "bad"}, {"nodes": False},
    None, [], "bad", 42,
    {"nodes": [{}, None]}, {"nodes": [[]]}, {"nodes": [False]},
    {"nodes": [{"node_id": []}]}, {"nodes": [{}], "transition_log": [None]},
], ids=["null-nodes", "null-node", "string-node", "object-nodes", "string-nodes",
        "boolean-nodes", "null-root", "array-root", "string-root", "number-root",
        "mixed-nodes", "array-node", "boolean-node", "array-node-id", "null-transition"])
def test_malformed_workflow_replaces_ready_report_and_allows_corrected_reentry(tmp_path, host, malformed):
    project(tmp_path, confirmed=True, documents=True, host=host)
    workflow_path = tmp_path / ".allforai/bootstrap/workflow.json"
    report_path = tmp_path / ".allforai/bootstrap/unattended-run-readiness.json"
    workflow = json.loads(workflow_path.read_text())
    retained = {"node_id": "warehouse", "goal": "Retain completed warehouse work",
                "capability": "implement", "exit_artifacts": [".allforai/bootstrap/stock.json"]}
    workflow["nodes"].append(retained)
    workflow["transition_log"] = [{"node_id": "warehouse", "status": "completed"}]
    write(tmp_path, ".allforai/bootstrap/workflow.json", workflow)
    write(tmp_path, ".allforai/bootstrap/stock.json", {"status": "passed", "count": 3})
    (tmp_path / ".allforai/bootstrap/node-specs/warehouse.md").write_text(
        "---\n" + json.dumps(retained) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    original = workflow_path.read_bytes()
    preserved = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file() and p != workflow_path}
    ready = gate(tmp_path, "validate_unattended_readiness.py", "--write-report")
    assert ready.returncode == 0, (ready.stdout, ready.stderr)
    assert json.loads(report_path.read_text())["status"] == "ready"

    write(tmp_path, ".allforai/bootstrap/workflow.json", malformed)
    for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
        options = ("--write-report",) if name == "validate_unattended_readiness.py" else ()
        rejected = gate(tmp_path, name, *options)
        assert rejected.returncode == 1, (name, rejected.stdout, rejected.stderr)
        assert not rejected.stderr, (name, rejected.stderr)
        if name == "validate_bootstrap.py":
            result = json.loads(rejected.stdout)
            assert result["passed"] is False
            assert any(error.startswith("invalid_scope:") for error in result["errors"])
        elif name == "check_decision_inputs.py":
            assert rejected.stdout.startswith("BLOCKED:")
            assert "invalid_scope:" in rejected.stdout
        else:
            report = json.loads(rejected.stdout)
            assert report["status"] == "not_ready"
            assert any(b["code"] == "invalid_scope" for b in report["blockers"])
            assert json.loads(report_path.read_text()) == report
    assert json.loads(workflow_path.read_text()) == malformed
    assert all(p.read_bytes() == content for p, content in preserved.items())

    workflow_path.write_bytes(original)
    for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
        options = ("--write-report",) if name == "validate_unattended_readiness.py" else ()
        corrected = gate(tmp_path, name, *options)
        assert corrected.returncode == 0, (name, corrected.stdout, corrected.stderr)
    assert json.loads(report_path.read_text())["status"] == "ready"
    assert all(p.read_bytes() == content for p, content in preserved.items())


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("refs", [None, []], ids=["absent", "empty"])
@pytest.mark.parametrize("name", ["validate_bootstrap.py", "validate_unattended_readiness.py", "check_decision_inputs.py"])
def test_new_unscoped_work_is_rejected_but_scoped_prerequisite_can_reenter(tmp_path, host, refs, name):
    project(tmp_path, confirmed=True, host=host)
    workflow_path = tmp_path / ".allforai/bootstrap/workflow.json"
    workflow = json.loads(workflow_path.read_text())
    node = {"node_id": "prepare-export", "goal": "Prepare export prerequisite",
            "capability": "implement", "exit_artifacts": [".allforai/bootstrap/preparation.json"]}
    if refs is not None:
        node["requirement_refs"] = refs
    workflow["nodes"].append(node)
    workflow["nodes"][0]["hard_blocked_by"] = [node["node_id"]]
    spec_dir = tmp_path / ".allforai/bootstrap/node-specs"

    def publish():
        write(tmp_path, ".allforai/bootstrap/workflow.json", workflow)
        for item in workflow["nodes"]:
            (spec_dir / (item["node_id"] + ".md")).write_text(
                "---\n" + json.dumps(item) + "\n---\n" + ATTENTION_CONTRACT_BODY)

    publish()
    before = {p: p.read_bytes() for p in (tmp_path / REQUIREMENTS, tmp_path / "orders.py")}
    rejected = gate(tmp_path, name)
    assert rejected.returncode == 1, (rejected.stdout, rejected.stderr)
    assert "scope_requirement_unwired" in rejected.stdout
    assert "prepare-export" in rejected.stdout
    assert not rejected.stderr, rejected.stderr

    node["requirement_refs"] = [REF]
    node["decision_inputs"] = [REQUIREMENTS]
    publish()
    corrected = gate(tmp_path, name)
    assert corrected.returncode == 0, (corrected.stdout, corrected.stderr)
    assert all(p.read_bytes() == content for p, content in before.items())


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("first_writer", ["node_id", "node"])
def test_mixed_native_history_uses_latest_state_without_changing_authority(tmp_path, host, first_writer):
    project(tmp_path, confirmed=True, documents=True, host=host)
    workflow_path = tmp_path / ".allforai/bootstrap/workflow.json"
    workflow = json.loads(workflow_path.read_text())
    retained = {"node_id": "warehouse", "goal": "Retain completed warehouse work",
                "capability": "implement", "exit_artifacts": [".allforai/bootstrap/stock.json"]}
    workflow["nodes"].append(retained)
    write(tmp_path, ".allforai/bootstrap/workflow.json", workflow)
    write(tmp_path, ".allforai/bootstrap/stock.json", {"status": "passed", "count": 3})
    (tmp_path / ".allforai/bootstrap/node-specs/warehouse.md").write_text(
        "---\n" + json.dumps(retained) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    preserved = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file() and p != workflow_path}
    writers = [first_writer, "node" if first_writer == "node_id" else "node_id", first_writer]
    for writer, status in zip(writers, ["completed", "failed", "completed"]):
        if writer == "node":
            codex_transition(tmp_path, "warehouse", status)
        else:
            workflow = json.loads(workflow_path.read_text())
            workflow["transition_log"].append({"node_id": "warehouse", "status": status})
            write(tmp_path, ".allforai/bootstrap/workflow.json", workflow)
        # A different node's event must not replace warehouse's latest state.
        codex_transition(tmp_path, "deliver-export", "failed")
        history = workflow_path.read_bytes()
        for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
            options = ("--write-report",) if name == "validate_unattended_readiness.py" else ()
            result = gate(tmp_path, name, *options)
            assert result.returncode == (1 if status == "failed" else 0), (name, result.stdout, result.stderr)
            if status == "failed":
                assert "scope_requirement_unwired" in result.stdout
                assert "warehouse" in result.stdout
            assert not result.stderr
        report = json.loads((tmp_path / ".allforai/bootstrap/unattended-run-readiness.json").read_text())
        assert report["status"] == ("not_ready" if status == "failed" else "ready")
        # Zero iterations exercises real run preflight without invoking a host.
        if host == "codex":
            result = subprocess.run([sys.executable, str(tmp_path / ".allforai/codex/flow.py"),
                                     "Add order CSV export", "0"], cwd=tmp_path, text=True, capture_output=True)
            assert result.returncode == (6 if status == "failed" else 2), (result.stdout, result.stderr)
            assert json.loads(result.stderr)["error"] == (
                "unattended readiness preflight blocked execution" if status == "failed"
                else "max iterations reached: 0")
        assert workflow_path.read_bytes() == history
        assert all(p.read_bytes() == content for p, content in preserved.items())


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("malformed_history", [
    {}, None, "", False, 42, [None], ["bad"], [[]], [False], [{}],
    [{"node_id": "deliver-export"}],
    [{"node_id": [], "status": "completed"}],
    [{"node": " ", "status": "completed"}],
    [{"node": "deliver-export", "status": None}],
    [{"node_id": "deliver-export", "status": " "}],
    [{"node_id": "deliver-export", "node": "warehouse", "status": "completed"}],
], ids=["object-history", "null-history", "string-history", "boolean-history", "number-history",
        "null-entry", "string-entry", "array-entry", "boolean-entry", "empty-entry",
        "missing-status", "array-node-id", "empty-node", "null-status", "empty-status",
        "conflicting-native-ids"])
def test_invalid_history_replaces_ready_report_and_corrected_history_reenters(tmp_path, host, malformed_history):
    project(tmp_path, confirmed=True, documents=True, host=host)
    workflow_path = tmp_path / ".allforai/bootstrap/workflow.json"
    report_path = tmp_path / ".allforai/bootstrap/unattended-run-readiness.json"
    workflow = json.loads(workflow_path.read_text())
    preserved = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file() and p != workflow_path}
    for history, expected in (([], 0), (malformed_history, 1), ([], 0)):
        workflow["transition_log"] = history
        write(tmp_path, ".allforai/bootstrap/workflow.json", workflow)
        before = workflow_path.read_bytes()
        for name in ("validate_bootstrap.py", "check_decision_inputs.py", "validate_unattended_readiness.py"):
            options = ("--write-report",) if name == "validate_unattended_readiness.py" else ()
            result = gate(tmp_path, name, *options)
            assert result.returncode == expected, (name, history, result.stdout, result.stderr)
            assert not result.stderr
            if expected:
                assert "invalid_scope" in result.stdout
        report = json.loads(report_path.read_text())
        assert report["status"] == ("not_ready" if expected else "ready")
        if expected:
            assert any(b["code"] == "invalid_scope" for b in report["blockers"])
        assert workflow_path.read_bytes() == before
        assert all(p.read_bytes() == content for p, content in preserved.items())
