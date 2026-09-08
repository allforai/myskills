"""Implementation, document synchronization and re-acceptance closure (#13).

A delivery completes only when product source, the confirmed baseline, the
required fact documents and the acceptance evidence agree. These drive the
copied bootstrap/resume and gate CLIs on both host adapters; they are not
real Claude/Codex host dialogue evidence.
"""
import json
import subprocess
import sys

import pytest

from .test_bootstrap_scope import ATTENTION_CONTRACT_BODY, codex_transition, project, publish_contract, write
from .test_product_intent_session import decide, invoke
from .test_evidence_freshness import invoke as freshness
from .test_freshness_admission_corrections import _artifacts, _bootstrap, _readiness, _reconcile, _set_node, HOSTS, NODE

REPORT = ".allforai/bootstrap/export-report.json"
EXISTS = [sys.executable, "-c", "import os; assert os.path.exists('" + REPORT + "')"]


@pytest.mark.parametrize("host", HOSTS)
def test_accepted_with_gaps_is_a_qualified_run_outcome_not_completion(tmp_path, host):
    project(tmp_path, confirmed=True, host=host)
    write(tmp_path, REPORT, {"status": "accepted_with_gaps", "gaps": []})
    publish_contract(tmp_path, kind="evidence", verification_command=EXISTS)
    checked = _artifacts(tmp_path)
    assert checked["freshness"]["status"] == "valid"
    assert checked["all_exist"] is False
    assert checked["artifacts"][0]["status_error"]["value"] == "accepted_with_gaps"
    node, plan = _reconcile(tmp_path)
    assert node["artifact_readiness"] == "blocked" and plan["action"] == "invalidate"


DOC = "docs/orders-export.md"
# The document's stated behavior is executed against the current code; a stale claim fails.
DOC_CHECK = [sys.executable, "-m", "doctest", DOC]
WORKFLOW = ".allforai/bootstrap/workflow.json"
ACCEPTANCE = [sys.executable, "-c", "import json; assert json.load(open('" + REPORT + "'))['status'] == 'passed'"]


def _doc(returned, header=None):
    """The fact document: what list_orders returns for one account, as a runnable example."""
    lines = ["# Orders export", "", "`list_orders(account)` returns only that account's orders:", "",
             "    >>> from orders import list_orders", "    >>> list_orders('acme')", "    " + returned]
    if header:
        lines += ["", "The CSV starts with a header row:", "", "    >>> from orders import HEADER",
                  "    >>> HEADER", "    " + header]
    return "\n".join(lines) + "\n"
WAREHOUSE_EVIDENCE = [sys.executable, "-c",
                      "import json; assert json.load(open('.allforai/bootstrap/stock.json'))['status'] == 'passed'"]
EXPORT = {"id": "export", "topic": "scenarios", "goal": "Export the current account's orders as CSV",
          "scope": ["orders"], "business_rules": ["Only the signed-in account's orders may be exported"],
          "acceptance": ["Another account's orders never appear in the CSV"]}
WAREHOUSE = {"node_id": "warehouse", "goal": "Track warehouse stock", "capability": "implement",
             "decision_inputs": [], "source_inputs": ["warehouse.py"],
             "exit_artifacts": [".allforai/bootstrap/stock.json"]}


def _transition(root, node_id, host):
    """Record a completed transition through each host's native producer."""
    if host == "codex":
        codex_transition(root, node_id, "completed")
        return
    workflow = json.loads((root / WORKFLOW).read_text())
    workflow["transition_log"].append({"node_id": node_id, "status": "completed"})
    write(root, WORKFLOW, workflow)


def _plan(root):
    """Regenerate the local workflow from the frozen scope, keeping the retained branch."""
    workflow = json.loads((root / WORKFLOW).read_text())
    request = {"operation": "plan", "transition_log": workflow.get("transition_log", []),
               "nodes": [{"node_id": NODE, "capability": "implement", "goal": "Deliver account-scoped order export",
                          "intent_ids": ["export"],
                          "responsibilities": ["implementation", "documentation", "verification"],
                          "source_inputs": ["orders.py"], "required_documents": [DOC],
                          "document_verification": {DOC: DOC_CHECK},
                          "exit_artifacts": [REPORT], "body": ATTENTION_CONTRACT_BODY},
                         dict(WAREHOUSE, body=ATTENTION_CONTRACT_BODY)]}
    result = invoke(root, request)
    assert result.returncode == 0, (result.stdout, result.stderr)
    return json.loads(result.stdout)["workflow"]


def _freeze(root, batch):
    result = invoke(root, {"operation": "freeze", "include": ["export"], "exclude": {}, "batch_id": batch,
                           "user_reference": "user scope turn " + batch, "reason": "Account export only"})
    assert result.returncode == 0, result.stdout
    return json.loads(result.stdout)["baseline"]


def closure_project(root, host):
    """One local feature owning implementation, a fact document and acceptance,
    planned from a journal-backed confirmed scope, beside an unrelated completed
    branch whose evidence must stay valid."""
    project(root, confirmed=True, host=host)
    (root / ".allforai/bootstrap/local-requirements.json").unlink()
    write(root, WORKFLOW, {"nodes": [WAREHOUSE], "transition_log": []})
    (root / ".allforai/bootstrap/node-specs/deliver-export.md").unlink()
    (root / "warehouse.py").write_text("stock = 10\n")
    write(root, ".allforai/bootstrap/stock.json", {"status": "passed"})
    _transition(root, "warehouse", host)
    result = invoke(root, {"operation": "admit", "route": "local-change", "goal": "Add account CSV export",
                           "areas": ["orders"], "items": [EXPORT]})
    assert result.returncode == 0, result.stdout
    assert decide(root, [{"operation": "confirm", "id": "export", "reason": "Account isolation"}]).returncode == 0
    assert _freeze(root, "scope-1")["version"] == 1
    _plan(root)
    publish_contract(root, "warehouse", kind="evidence", verification_command=WAREHOUSE_EVIDENCE)
    publish_contract(root)
    write(root, REPORT, {"status": "passed"})


def _publish_evidence(root, node_id=NODE, command=ACCEPTANCE):
    result, observed = freshness(root, "observe", node_id=node_id, kind="evidence")
    assert result.returncode == 0, observed
    result, published = freshness(root, "publish", observation=observed["observation"], verification_command=command)
    return result.returncode, published


def _assert_valid_unrelated(root):
    checked = _artifacts(root, "warehouse")
    assert checked["all_exist"] is True and checked["freshness"]["status"] == "valid"


@pytest.mark.parametrize("host", HOSTS)
def test_local_feature_closure_refuses_inconsistency_and_recovers(tmp_path, host):
    closure_project(tmp_path, host)

    # Documentation omitted: code and acceptance report exist, delivery is not complete.
    code, refused = _publish_evidence(tmp_path)
    assert code == 1 and refused["status"] == "inconsistent", refused
    assert refused["diff"] == {"outputs": {DOC: "missing"}}
    assert refused["repair"] == {"owner": NODE, "responsibilities": ["documentation"]}
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False
    assert checked["freshness"]["diff"]["outputs"] == {DOC: "missing"}
    assert checked["freshness"]["repair"]["owner"] == NODE
    node, plan = _reconcile(tmp_path)
    assert node["artifact_readiness"] == "blocked" and plan["action"] == "invalidate"
    assert plan["repair_owner"] == NODE and plan["diff"]["outputs"] == {DOC: "missing"}
    code, report = _readiness(tmp_path)
    assert code == 0 and report["status"] == "ready", report["blockers"]  # Contract readiness permits the work.
    _assert_valid_unrelated(tmp_path)

    # Correction: the fact document is written; acceptance and the document check both execute.
    (tmp_path / DOC).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / DOC).write_text(_doc("[]"))
    code, published = _publish_evidence(tmp_path)
    assert code == 0 and published["status"] == "valid", published
    assert published["verified_documents"] == [DOC]
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is True and checked["freshness"]["diff"] == {}
    assert _reconcile(tmp_path)[1]["action"] == "keep"
    _assert_valid_unrelated(tmp_path)

    # Decisive negative: the code changes, the required document is retained unchanged, the current
    # inputs are observed and a code-only acceptance passes. The outdated document keeps delivery blocked.
    (tmp_path / "orders.py").write_text("def list_orders(account): return [account]\n")
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False
    assert checked["freshness"]["diff"] == {"files": {"orders.py": "changed"}}
    assert checked["freshness"]["repair"] == {"owner": NODE, "responsibilities": ["implementation"]}
    node, plan = _reconcile(tmp_path)
    assert plan["action"] == "invalidate" and plan["repair_owner"] == NODE
    assert plan["repair_responsibilities"] == ["implementation"] and plan["diff"] == {"files": {"orders.py": "changed"}}
    outdated = (tmp_path / DOC).read_bytes()
    code, refused = _publish_evidence(tmp_path)
    assert code == 1 and refused["status"] == "failed_verification", refused
    assert refused["document"] == DOC and refused["command"] == DOC_CHECK
    assert refused["repair"] == {"owner": NODE, "responsibilities": ["documentation"]}
    assert (tmp_path / DOC).read_bytes() == outdated  # Verification reads the document; it never rewrites it.
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False and checked["freshness"]["status"] == "stale"
    assert _readiness(tmp_path)[0] == 1 and _reconcile(tmp_path)[1]["action"] == "invalidate"
    # Touching the document without correcting its facts is not synchronization either.
    (tmp_path / DOC).write_text(_doc("[]") + "\nRefreshed after the change.\n")
    code, refused = _publish_evidence(tmp_path)
    assert code == 1 and refused["status"] == "failed_verification" and refused["document"] == DOC
    assert _artifacts(tmp_path)["all_exist"] is False
    _assert_valid_unrelated(tmp_path)

    # Synchronization: the document states the current behavior and its check executes against the code.
    (tmp_path / DOC).write_text(_doc("['acme']"))
    code, published = _publish_evidence(tmp_path)
    assert code == 0 and published["status"] == "valid", published
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is True and checked["freshness"]["diff"] == {}
    assert _reconcile(tmp_path)[1]["action"] == "keep"
    _assert_valid_unrelated(tmp_path)

    # A fact document edited after publication to contradict the code is a documentation inconsistency.
    (tmp_path / DOC).write_text(_doc("['acme', 'other-account']"))
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False and checked["freshness"]["status"] == "stale"
    assert checked["freshness"]["diff"] == {"outputs": {DOC: "changed"}}
    assert checked["freshness"]["repair"] == {"owner": NODE, "responsibilities": ["documentation"]}
    code, report = _readiness(tmp_path)
    assert code == 1 and report["status"] == "not_ready"
    blocker = next(b for b in report["blockers"] if b["code"] == "stale_evidence" and b["node_id"] == NODE)
    assert "repair owner " + NODE + " (documentation)" in blocker["message"] and DOC in blocker["message"]
    code, refused = _publish_evidence(tmp_path)
    assert code == 1 and refused["status"] == "failed_verification" and refused["document"] == DOC
    (tmp_path / DOC).write_text(_doc("['acme']"))
    code, published = _publish_evidence(tmp_path)
    assert code == 0 and published["status"] == "valid"

    # SG01 inside synchronization: inputs observed as A, changed to B before publication.
    result, observed = freshness(tmp_path, "observe", node_id=NODE, kind="evidence")
    assert result.returncode == 0
    (tmp_path / "orders.py").write_text("def list_orders(account): return [account, 'csv']\n")
    result, rejected = freshness(tmp_path, "publish", observation=observed["observation"], verification_command=ACCEPTANCE)
    assert result.returncode == 1 and rejected["status"] == "stale"
    (tmp_path / DOC).write_text(_doc("['acme', 'csv']"))
    code, published = _publish_evidence(tmp_path)
    assert code == 0 and published["status"] == "valid"
    state = tmp_path / ".allforai/bootstrap/evidence-freshness.json"
    before = state.read_bytes()
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is True and checked["freshness"]["diff"] == {} and "repair" not in checked["freshness"]
    assert _artifacts(tmp_path) == checked and state.read_bytes() == before
    _assert_valid_unrelated(tmp_path)

    # An approved product change is recorded once; it propagates through refreeze and replan.
    adjusted = decide(tmp_path, [{"operation": "adjust", "id": "export", "reason": "Header row requested",
                                  "changes": {"acceptance": ["Another account's orders never appear in the CSV",
                                                             "The CSV starts with a header row"]}}], batch="adjust-1")
    assert adjusted.returncode == 0, adjusted.stdout
    assert json.loads(adjusted.stdout)["topics"] == []  # Nothing pending: the decision is not asked again.
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False
    assert checked["freshness"]["diff"]["requirements"] == [".allforai/bootstrap/local-requirements.json#export"]
    assert checked["freshness"]["repair"] == {"owner": "interactive-bootstrap", "responsibilities": ["replan"]}
    code, report = _readiness(tmp_path)
    assert code == 1 and NODE in [b["node_id"] for b in report["blockers"] if b["code"] == "stale_requirement"]
    _assert_valid_unrelated(tmp_path)
    assert _freeze(tmp_path, "scope-2")["version"] == 2
    resumed = invoke(tmp_path, {"operation": "resume"})
    assert resumed.returncode == 0 and json.loads(resumed.stdout)["topics"] == []
    workflow = _plan(tmp_path)
    node = next(n for n in workflow["nodes"] if n["node_id"] == NODE)
    assert node["acceptance"][-1] == "The CSV starts with a header row"
    assert "The CSV starts with a header row" in (tmp_path / ".allforai/bootstrap/node-specs" / (NODE + ".md")).read_text()
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False
    assert checked["freshness"]["repair"]["owner"] == NODE
    assert set(checked["freshness"]["repair"]["responsibilities"]) == {"requirement-sync", "contract"}
    publish_contract(tmp_path)
    code, report = _readiness(tmp_path)
    assert code == 0 and report["status"] == "ready", report["blockers"]
    (tmp_path / "orders.py").write_text("HEADER = 'id,total'\ndef list_orders(account): return [account, 'csv']\n")
    (tmp_path / DOC).write_text(_doc("['acme', 'csv']", header="'id,total'"))
    code, published = _publish_evidence(tmp_path)
    assert code == 0 and published["status"] == "valid", published
    assert _artifacts(tmp_path)["all_exist"] is True
    _assert_valid_unrelated(tmp_path)

    # A reopened product decision blocks the dependent work; unattended execution cannot resolve it.
    reopened = decide(tmp_path, [{"operation": "reopen", "id": "export", "reason": "Reconsider archived orders"}],
                      batch="reopen-1")
    assert reopened.returncode == 0, reopened.stdout
    assert [t["topic"] for t in json.loads(reopened.stdout)["topics"]] == ["scenarios"]
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False
    assert checked["freshness"]["repair"] == {"owner": "interactive-bootstrap", "responsibilities": ["product-decision"]}
    code, report = _readiness(tmp_path)
    assert code == 1 and NODE in [b["node_id"] for b in report["blockers"] if b["code"] == "pending_requirement"]
    node, plan = _reconcile(tmp_path)
    assert plan["action"] == "invalidate" and plan["repair_owner"] == "interactive-bootstrap"
    _assert_valid_unrelated(tmp_path)
    policy = invoke(tmp_path, {"operation": "run-policy", "user_reference": "user policy turn",
                               "answers": {"on_repeated_failure": "halt", "on_needs_iteration": "accept",
                                           "on_safety_warning": "continue"}})
    assert policy.returncode == 0, policy.stdout
    event = subprocess.run([sys.executable, str(tmp_path / ".allforai/bootstrap/scripts/product_intent.py"), str(tmp_path),
                            "--policy-event", "on_needs_iteration"], text=True, capture_output=True, cwd=tmp_path)
    assert json.loads(event.stdout)["action"] == "accept"
    write(tmp_path, REPORT, {"status": "accepted_with_gaps", "gaps": ["archived orders undecided"]})
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False and checked["freshness"]["repair"]["owner"] == "interactive-bootstrap"
    assert _readiness(tmp_path)[0] == 1
    assert json.loads((tmp_path / ".allforai/bootstrap/local-requirements.json").read_text())["requirements"][-1]["status"] == "pending"

    # Recovery: the user confirms at interactive bootstrap; the scope is refrozen, replanned and reverified.
    assert decide(tmp_path, [{"operation": "confirm", "id": "export", "reason": "Archived orders stay excluded"}],
                  batch="confirm-2").returncode == 0
    assert json.loads(invoke(tmp_path, {"operation": "resume"}).stdout)["topics"] == []
    assert _freeze(tmp_path, "scope-3")["version"] == 3
    _plan(tmp_path)
    publish_contract(tmp_path)
    assert _readiness(tmp_path)[1]["status"] == "ready"
    write(tmp_path, REPORT, {"status": "passed"})
    code, published = _publish_evidence(tmp_path)
    assert code == 0 and published["status"] == "valid", published
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is True and "repair" not in checked["freshness"]
    assert _reconcile(tmp_path)[1]["action"] == "keep"
    _assert_valid_unrelated(tmp_path)
    history = json.loads((tmp_path / ".allforai/bootstrap/local-requirements.json").read_text())["requirements"]
    assert [item["revision"] for item in history] == [1, 2, 3]  # Prior revisions are retained.


@pytest.mark.parametrize("host", HOSTS)
def test_required_document_without_verification_is_refused_at_every_gate(tmp_path, host):
    """Declaring a fact document is a responsibility, not proof: planning must also
    declare how that document is checked against the current source."""
    project(tmp_path, confirmed=True, host=host)
    _set_node(tmp_path, required_documents=[DOC])
    (tmp_path / DOC).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / DOC).write_text(_doc("[]"))
    write(tmp_path, REPORT, {"status": "passed"})
    code, errors = _bootstrap(tmp_path)
    assert code == 1 and any(NODE in e and "document_verification" in e for e in errors), errors
    code, report = _readiness(tmp_path)
    assert code == 1 and NODE in [b["node_id"] for b in report["blockers"] if b["code"] == "missing_document_verification"]
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False and checked["freshness"]["admission"] == "invalid"
    assert _reconcile(tmp_path)[1]["action"] == "invalidate"
    code, refused = _publish_evidence(tmp_path)
    assert code == 1 and refused["status"] == "inconsistent", refused
    assert refused["diff"] == {"documents": {DOC: "unverified"}}
    assert refused["repair"] == {"owner": NODE, "responsibilities": ["documentation", "verification"]}

    _set_node(tmp_path, required_documents=[DOC], document_verification={DOC: DOC_CHECK})
    publish_contract(tmp_path)
    assert _bootstrap(tmp_path)[0] == 0 and _readiness(tmp_path)[1]["status"] == "ready"
    code, published = _publish_evidence(tmp_path)
    assert code == 0 and published["status"] == "valid", published
    assert _artifacts(tmp_path)["all_exist"] is True


MUTATE_SOURCE = [sys.executable, "-c", "open('orders.py', 'a').write('\\n# rewritten by a document check\\n')"]


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("target", ["own-source", "upstream-source"])
def test_document_check_that_changes_inputs_cannot_publish_proof_for_the_old_state(tmp_path, host, target):
    """A document check reads; a check that rewrites source A into B while the
    observation still describes A cannot publish A's evidence as valid."""
    project(tmp_path, confirmed=True, host=host)
    write(tmp_path, REPORT, {"status": "passed"})
    publish_contract(tmp_path, kind="evidence", verification_command=ACCEPTANCE)
    (tmp_path / DOC).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / DOC).write_text(_doc("[]"))
    if target == "own-source":
        node_id, acceptance = NODE, ACCEPTANCE
        _set_node(tmp_path, required_documents=[DOC], document_verification={DOC: MUTATE_SOURCE})
    else:
        node_id = "verify-export"
        acceptance = [sys.executable, "-c", "import json; assert json.load(open('.allforai/bootstrap/verify.json'))['status'] == 'passed'"]
        workflow = json.loads((tmp_path / WORKFLOW).read_text())
        consumer = {"node_id": node_id, "goal": "Verify the export", "capability": "verify", "decision_inputs": [],
                    "source_inputs": [], "hard_blocked_by": [NODE], "required_documents": [DOC],
                    "document_verification": {DOC: MUTATE_SOURCE}, "exit_artifacts": [".allforai/bootstrap/verify.json"]}
        workflow["nodes"].append(consumer)
        write(tmp_path, WORKFLOW, workflow)
        (tmp_path / ".allforai/bootstrap/node-specs" / (node_id + ".md")).write_text(
            "---\n" + json.dumps(consumer) + "\n---\n" + ATTENTION_CONTRACT_BODY)
        write(tmp_path, ".allforai/bootstrap/verify.json", {"status": "passed"})
    state = tmp_path / ".allforai/bootstrap/evidence-freshness.json"
    recorded = state.read_bytes()
    source = (tmp_path / "orders.py").read_bytes()
    code, rejected = _publish_evidence(tmp_path, node_id, command=acceptance)
    assert code == 1 and rejected["status"] == "stale", rejected
    assert (tmp_path / "orders.py").read_bytes() != source  # The mutation is visible, never hidden.
    assert state.read_bytes() == recorded  # Nothing was published for either state.
    assert _artifacts(tmp_path, node_id)["all_exist"] is False
    if target == "upstream-source":
        assert _artifacts(tmp_path)["freshness"]["status"] == "stale"  # The producer's evidence is also stale now.


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("spelling", ["relative", "dot-relative", "absolute-in-project"])
def test_document_check_script_is_a_consumed_input(tmp_path, host, spelling):
    """A project checker script is part of the delivery's inputs whatever its argv
    spelling: an unobserved checker cannot verify, and weakening a tracked checker
    invalidates the evidence."""
    project(tmp_path, confirmed=True, host=host)
    script = "scripts/check_orders_doc.py"
    argv_path = {"relative": script, "dot-relative": "./" + script,
                 "absolute-in-project": str(tmp_path / script)}[spelling]
    (tmp_path / script).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / script).write_text("import doctest, sys\n"
                                   "sys.path.insert(0, '.')\n"
                                   "failed, _ = doctest.testfile('" + DOC + "', module_relative=False)\n"
                                   "sys.exit(1 if failed else 0)\n")
    (tmp_path / DOC).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / DOC).write_text(_doc("[]"))
    write(tmp_path, REPORT, {"status": "passed"})
    _set_node(tmp_path, required_documents=[DOC], document_verification={DOC: [sys.executable, argv_path]})
    code, refused = _publish_evidence(tmp_path)
    assert code == 1 and refused["status"] == "inconsistent", refused
    assert refused["diff"] == {"documents": {DOC: "unobserved-check:" + script}}
    assert refused["repair"]["owner"] == NODE

    _set_node(tmp_path, required_documents=[DOC], document_verification={DOC: [sys.executable, argv_path]},
              input_dependencies=[script])
    code, published = _publish_evidence(tmp_path)
    assert code == 0 and published["status"] == "valid", published
    assert _artifacts(tmp_path)["all_exist"] is True
    (tmp_path / script).write_text("import sys\nsys.exit(0)\n")  # A weakened checker is a changed input.
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False and checked["freshness"]["diff"] == {"files": {script: "changed"}}


@pytest.mark.parametrize("host", HOSTS)
def test_corrupt_read_register_blocks_all_legacy_history_without_freshness_state(tmp_path, host):
    """Dependency impact is unknown when the dynamic-read register is unreadable,
    even when every node is retained history and no evidence state was ever written."""
    project(tmp_path, confirmed=True, host=host, source_inputs=None)
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    workflow["nodes"] = [{"node_id": "warehouse", "goal": "Track warehouse stock", "capability": "implement",
                          "decision_inputs": [], "exit_artifacts": [".allforai/bootstrap/stock.json"]}]
    write(tmp_path, WORKFLOW, workflow)
    (tmp_path / ".allforai/bootstrap/node-specs/deliver-export.md").unlink()
    (tmp_path / ".allforai/bootstrap/node-specs/warehouse.md").write_text(
        "---\n" + json.dumps(workflow["nodes"][0]) + "\n---\n" + ATTENTION_CONTRACT_BODY)
    profile = json.loads((tmp_path / ".allforai/bootstrap/bootstrap-profile.json").read_text())
    profile.pop("task_scope"); profile.pop("task_route")
    write(tmp_path, ".allforai/bootstrap/bootstrap-profile.json", profile)
    write(tmp_path, ".allforai/bootstrap/stock.json", {"status": "passed"})
    _transition(tmp_path, "warehouse", host)
    assert not (tmp_path / ".allforai/bootstrap/evidence-freshness.json").exists()
    assert _artifacts(tmp_path, "warehouse")["all_exist"] is True

    register = tmp_path / ".allforai/bootstrap/observed-input-dependencies.json"
    register.write_text("{not json")
    checked = _artifacts(tmp_path, "warehouse")
    assert checked["all_exist"] is False and checked["freshness"]["status"] == "invalid", checked
    code, report = _readiness(tmp_path)
    assert code == 1 and "warehouse" in [b["node_id"] for b in report["blockers"] if b["code"] == "stale_evidence"]
    node, plan = _reconcile(tmp_path, "warehouse")
    assert node["artifact_readiness"] == "blocked" and plan["action"] == "invalidate"
    assert register.read_text() == "{not json"  # Left in place for repair, never dropped.

    register.write_text("{}")
    assert _artifacts(tmp_path, "warehouse")["all_exist"] is True
    assert _readiness(tmp_path)[0] == 0
