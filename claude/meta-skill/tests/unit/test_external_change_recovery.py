"""External source change discovered at bootstrap/resume and decided by the user (#14).

Code changed outside the delivery flow is detected at the bootstrap/resume
boundary, verified against the confirmed baseline's own recorded acceptance, and
either synchronized as a fact update or presented as a product conflict the user
accepts, rejects or defers. These drive the copied gate CLIs in temporary
projects on both host adapters; they are not real Claude/Codex host dialogue evidence.
"""
import json
import subprocess
import sys

import pytest

from .test_bootstrap_scope import write
from .test_delivery_closure import (ACCEPTANCE, DOC, DOC_CHECK, NODE, REPORT, WORKFLOW, _doc,
                                    _publish_evidence, _transition, closure_project)
from .test_evidence_freshness import invoke as freshness
from .test_freshness_admission_corrections import HOSTS, _artifacts, _readiness, _reconcile
from .test_product_intent_session import invoke

REQUIREMENT = ".allforai/bootstrap/local-requirements.json"
JOURNAL = ".allforai/product-concept/decision-journal.json"
STORE = ".allforai/bootstrap/external-changes.json"
# The confirmed acceptance executed against the code: no other account's orders may appear.
ISOLATION = [sys.executable, "-c",
             "import json; from orders import list_orders;"
             " assert json.load(open('" + REPORT + "'))['status'] == 'passed';"
             " assert all(o == 'acme' for o in list_orders('acme')), list_orders('acme')"]


def drift_project(root, host):
    """A closed delivery: implementation, its fact document and acceptance evidence
    published and completed, beside an unrelated completed branch."""
    closure_project(root, host)
    (root / "orders.py").write_text("def list_orders(account): return [account]\n")
    (root / DOC).parent.mkdir(parents=True, exist_ok=True)
    (root / DOC).write_text(_doc("['acme']"))
    code, published = _publish_evidence(root, command=ISOLATION)
    assert code == 0 and published["status"] == "valid", published
    _transition(root, NODE, host)


def external(root, **request):
    return freshness(root, "external-changes", **request)


def _unrelated_is_valid(root):
    checked = _artifacts(root, "warehouse")
    assert checked["all_exist"] is True and checked["freshness"]["status"] == "valid"


@pytest.mark.parametrize("host", HOSTS)
def test_external_implementation_change_is_reported_with_its_impact(tmp_path, host):
    drift_project(tmp_path, host)
    journal_before = (tmp_path / JOURNAL).read_bytes()

    # An edit outside the flow: the account's orders are listed twice. The confirmed
    # acceptance still holds, so this is an implementation fact, not a product change.
    (tmp_path / "orders.py").write_text("def list_orders(account): return [account, account]\n")
    result, report = external(tmp_path)
    assert result.returncode == 0, report
    assert report["status"] == "fact_update"
    assert [change["node_id"] for change in report["changes"]] == [NODE]
    change = report["changes"][0]
    assert change["files"] == {"orders.py": "changed"}
    assert change["classification"] == "fact-update"
    assert change["impact"] == {"facts": ["orders.py"], "documents": [DOC],
                                "product_decisions": [REQUIREMENT + "#export"],
                                "tasks": [NODE], "acceptance": [REPORT]}
    assert change["resolution"] is None
    assert change["verification"]["command"] == ISOLATION and change["verification"]["returncode"] == 0

    # Detection records facts only: no product decision was invented for the change.
    assert (tmp_path / JOURNAL).read_bytes() == journal_before
    assert json.loads((tmp_path / STORE).read_text())["changes"][change["change_id"]] == change
    _unrelated_is_valid(tmp_path)


CONFLICTING = "def list_orders(account): return [account, 'other-account']\n"


@pytest.mark.parametrize("host", HOSTS)
def test_external_product_behavior_change_is_a_conflict_not_a_new_requirement(tmp_path, host):
    drift_project(tmp_path, host)
    requirement_before = (tmp_path / REQUIREMENT).read_bytes()
    journal_before = (tmp_path / JOURNAL).read_bytes()

    # The code now exports another account's orders: the confirmed acceptance fails.
    (tmp_path / "orders.py").write_text(CONFLICTING)
    result, report = external(tmp_path)
    assert result.returncode == 1 and report["status"] == "conflict", report
    change = report["changes"][0]
    assert change["classification"] == "product-conflict"
    assert change["verification"]["returncode"] != 0
    assert change["resolution"] is None

    # The confirmed baseline is untouched: changed code never writes itself into intent.
    assert (tmp_path / REQUIREMENT).read_bytes() == requirement_before
    assert (tmp_path / JOURNAL).read_bytes() == journal_before

    # Affected work is withheld and returns to the interactive product decision.
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False
    assert checked["freshness"]["repair"] == {"owner": "interactive-bootstrap",
                                              "responsibilities": ["product-decision"]}
    node, plan = _reconcile(tmp_path)
    assert plan["action"] == "invalidate" and plan["repair_owner"] == "interactive-bootstrap"

    # Unattended execution reports the unresolved conflict; it never interviews or assumes acceptance.
    code, readiness = _readiness(tmp_path)
    assert code == 1 and readiness["status"] == "not_ready"
    blocker = next(b for b in readiness["blockers"] if b["code"] == "unresolved_external_change")
    assert blocker["node_id"] == NODE and change["change_id"] in blocker["message"]
    assert "interactive" in blocker["message"] and "orders.py" in blocker["message"]
    _unrelated_is_valid(tmp_path)


PARTNER_ACCEPTANCE = ["The CSV lists every order of the partner group"]
PARTNER = [sys.executable, "-c",
           "import json; from orders import list_orders;"
           " assert json.load(open('" + REPORT + "'))['status'] == 'passed';"
           " assert list_orders('acme') == ['acme', 'other-account'], list_orders('acme')"]


def _accept(root, change_id, actions, batch="external-1"):
    return invoke(root, {"operation": "external-change", "change_id": change_id, "resolution": "accept",
                         "batch_id": batch, "user_reference": "user turn: partners share one export",
                         "reason": "Partner accounts were merged into one export", "actions": actions})


@pytest.mark.parametrize("host", HOSTS)
def test_accepting_an_external_change_records_the_decision_and_recovers_execution(tmp_path, host):
    from .test_bootstrap_scope import publish_contract
    from .test_delivery_closure import _freeze, _plan

    drift_project(tmp_path, host)
    (tmp_path / "orders.py").write_text(CONFLICTING)
    change = external(tmp_path)[1]["changes"][0]

    # Acceptance without stating the new desired behavior is refused: the code change
    # cannot supply the requirement it conflicts with.
    refused = _accept(tmp_path, change["change_id"], [])
    assert refused.returncode == 1 and "desired" in json.loads(refused.stdout)["error"], refused.stdout
    assert json.loads((tmp_path / REQUIREMENT).read_text())["requirements"][-1]["acceptance"] != PARTNER_ACCEPTANCE

    accepted = _accept(tmp_path, change["change_id"],
                       [{"operation": "adjust", "id": "export", "reason": "Partner accounts were merged",
                         "changes": {"acceptance": PARTNER_ACCEPTANCE,
                                     "business_rules": ["The partner group's orders are exported together"]}}])
    assert accepted.returncode == 0, accepted.stdout

    # The decision and its reason are recorded in the journal and bound to the change.
    batch = next(b for b in json.loads((tmp_path / JOURNAL).read_text())["batches"] if b["batch_id"] == "external-1")
    assert batch["source"] == "user_session"
    assert batch["user_reference"] == "user turn: partners share one export"
    assert batch["external_change"] == {"change_id": change["change_id"], "node_id": NODE,
                                        "resolution": "accept", "files": {"orders.py": "changed"}}
    resolution = json.loads((tmp_path / STORE).read_text())["changes"][change["change_id"]]["resolution"]
    assert resolution["resolution"] == "accept" and resolution["batch_id"] == "external-1"
    assert resolution["reason"] == "Partner accounts were merged into one export"
    assert resolution["decision"] == JOURNAL + "#external-1/decisions/0"

    # The conflict is settled; the accepted change now propagates as a baseline revision.
    code, readiness = _readiness(tmp_path)
    assert code == 1 and not [b for b in readiness["blockers"] if b["code"] == "unresolved_external_change"]
    assert NODE in [b["node_id"] for b in readiness["blockers"] if b["code"] == "stale_requirement"]
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False
    assert checked["freshness"]["repair"] == {"owner": "interactive-bootstrap", "responsibilities": ["replan"]}
    _unrelated_is_valid(tmp_path)

    # Recovery through the existing synchronization loop: refreeze, replan, resynchronize, reverify.
    assert _freeze(tmp_path, "scope-2")["version"] == 2
    workflow = _plan(tmp_path)
    assert next(n for n in workflow["nodes"] if n["node_id"] == NODE)["acceptance"] == PARTNER_ACCEPTANCE
    publish_contract(tmp_path)
    assert _readiness(tmp_path)[1]["status"] == "ready"
    (tmp_path / DOC).write_text(_doc("['acme', 'other-account']"))
    code, published = _publish_evidence(tmp_path, command=PARTNER)
    assert code == 0 and published["status"] == "valid", published
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is True and "repair" not in checked["freshness"]
    assert _reconcile(tmp_path)[1]["action"] == "keep"
    assert external(tmp_path)[1] == {"status": "clear", "changes": []}
    _unrelated_is_valid(tmp_path)


def _reject(root, change_id, batch="external-2"):
    return invoke(root, {"operation": "external-change", "change_id": change_id, "resolution": "reject",
                         "batch_id": batch, "user_reference": "user turn: account isolation stands",
                         "reason": "Account isolation is a legal requirement"})


@pytest.mark.parametrize("host", HOSTS)
def test_rejecting_an_external_change_keeps_the_baseline_and_scopes_the_repair(tmp_path, host):
    drift_project(tmp_path, host)
    baseline_before = (tmp_path / REQUIREMENT).read_bytes()
    (tmp_path / "orders.py").write_text(CONFLICTING)
    change = external(tmp_path)[1]["changes"][0]

    rejected = _reject(tmp_path, change["change_id"])
    assert rejected.returncode == 0, rejected.stdout

    # The confirmed baseline stands unchanged; the decision and its reason are recorded.
    assert (tmp_path / REQUIREMENT).read_bytes() == baseline_before
    batch = next(b for b in json.loads((tmp_path / JOURNAL).read_text())["batches"] if b["batch_id"] == "external-2")
    assert batch["source"] == "user_session" and batch["external_change"]["resolution"] == "reject"
    assert batch["decisions"][0]["chosen"] == "Restore the confirmed behavior"
    assert batch["decisions"][0]["rationale"] == "Account isolation is a legal requirement"

    # The outcome is a scoped implementation repair, not a further product question.
    resolution = json.loads((tmp_path / STORE).read_text())["changes"][change["change_id"]]["resolution"]
    assert resolution["repair_task"] == {"node_id": NODE, "responsibilities": ["implementation"],
                                         "files": ["orders.py"], "restore_acceptance": ISOLATION,
                                         "product_decisions": [REQUIREMENT + "#export"]}
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False
    assert checked["freshness"]["repair"] == {"owner": NODE, "responsibilities": ["implementation"]}
    code, readiness = _readiness(tmp_path)
    assert code == 1 and not [b for b in readiness["blockers"] if b["code"] == "unresolved_external_change"]
    blocker = next(b for b in readiness["blockers"] if b["code"] == "external_change_repair_pending")
    assert blocker["node_id"] == NODE and "orders.py" in blocker["message"]
    _unrelated_is_valid(tmp_path)

    # Republishing without repairing cannot close the delivery: the confirmed acceptance still fails.
    code, refused = _publish_evidence(tmp_path, command=ISOLATION)
    assert code == 1 and refused["status"] == "failed_verification", refused

    # Repair, resynchronize and reverify through the existing loop; execution resumes.
    (tmp_path / "orders.py").write_text("def list_orders(account): return [account] if account else []\n")
    code, published = _publish_evidence(tmp_path, command=ISOLATION)
    assert code == 0 and published["status"] == "valid", published
    assert external(tmp_path)[1] == {"status": "clear", "changes": []}
    assert _readiness(tmp_path)[1]["status"] == "ready"
    assert _artifacts(tmp_path)["all_exist"] is True
    assert _reconcile(tmp_path)[1]["action"] == "keep"
    _unrelated_is_valid(tmp_path)


RUN_POLICY = {"on_repeated_failure": "continue", "on_needs_iteration": "accept", "on_safety_warning": "halt"}


@pytest.mark.parametrize("host", HOSTS)
def test_deferred_conflict_holds_only_dependent_work_and_resumes_without_rebuilding(tmp_path, host):
    from .test_bootstrap_scope import publish_contract
    from .test_delivery_closure import _freeze, _plan

    drift_project(tmp_path, host)
    warehouse_spec = (tmp_path / ".allforai/bootstrap/node-specs/warehouse.md").read_bytes()
    requirement_before = (tmp_path / REQUIREMENT).read_bytes()
    journal_before = (tmp_path / JOURNAL).read_bytes()

    (tmp_path / "orders.py").write_text(CONFLICTING)
    change = external(tmp_path)[1]["changes"][0]
    deferred = invoke(tmp_path, {"operation": "external-change", "change_id": change["change_id"],
                                 "resolution": "defer", "user_reference": "user turn: decide after the contract",
                                 "reason": "The partner contract is not signed yet"})
    assert deferred.returncode == 0, deferred.stdout

    # Deferring is not a product decision: neither the journal nor the baseline moves.
    assert (tmp_path / JOURNAL).read_bytes() == journal_before
    assert (tmp_path / REQUIREMENT).read_bytes() == requirement_before
    resolution = json.loads((tmp_path / STORE).read_text())["changes"][change["change_id"]]["resolution"]
    assert resolution == {"resolution": "defer", "reason": "The partner contract is not signed yet",
                          "user_reference": "user turn: decide after the contract",
                          "baseline_version": change["baseline_version"],
                          "requirement_binding": change["requirement_binding"]}

    # Only the dependent work is held; the unrelated completed branch keeps its evidence.
    code, readiness = _readiness(tmp_path)
    assert code == 1
    held = [b for b in readiness["blockers"] if b["code"] == "unresolved_external_change"]
    assert [b["node_id"] for b in held] == [NODE] and "deferred" in held[0]["message"]
    _unrelated_is_valid(tmp_path)

    # The next boundary check is idempotent: same identity, retained context, no invented decision.
    store_before = (tmp_path / STORE).read_bytes()
    result, again = external(tmp_path)
    assert result.returncode == 1 and again["status"] == "conflict"
    assert again["changes"][0]["change_id"] == change["change_id"]
    assert again["changes"][0]["resolution"] == resolution
    assert (tmp_path / STORE).read_bytes() == store_before
    assert (tmp_path / JOURNAL).read_bytes() == journal_before

    # A recorded Run Policy answer is a run choice; accept there never accepts a product change.
    policy = invoke(tmp_path, {"operation": "run-policy", "answers": RUN_POLICY,
                               "user_reference": "user policy turn"})
    assert policy.returncode == 0, policy.stdout
    event = subprocess.run([sys.executable, str(tmp_path / ".allforai/bootstrap/scripts/product_intent.py"),
                            str(tmp_path), "--policy-event", "on_needs_iteration"],
                           text=True, capture_output=True, cwd=tmp_path)
    assert json.loads(event.stdout)["action"] == "accept"
    assert json.loads((tmp_path / STORE).read_text())["changes"][change["change_id"]]["resolution"] == resolution
    code, readiness = _readiness(tmp_path)
    assert code == 1 and [b["node_id"] for b in readiness["blockers"]
                          if b["code"] == "unresolved_external_change"] == [NODE]

    # Returning to the interactive entry continues from the retained conflict.
    accepted = _accept(tmp_path, change["change_id"],
                       [{"operation": "adjust", "id": "export", "reason": "The partner contract was signed",
                         "changes": {"acceptance": PARTNER_ACCEPTANCE,
                                     "business_rules": ["The partner group's orders are exported together"]}}])
    assert accepted.returncode == 0, accepted.stdout
    assert _freeze(tmp_path, "scope-2")["version"] == 2
    _plan(tmp_path)
    publish_contract(tmp_path)
    (tmp_path / DOC).write_text(_doc("['acme', 'other-account']"))
    code, published = _publish_evidence(tmp_path, command=PARTNER)
    assert code == 0 and published["status"] == "valid", published
    assert _readiness(tmp_path)[1]["status"] == "ready"
    assert external(tmp_path)[1] == {"status": "clear", "changes": []}

    # The unrelated branch was never replanned or reverified to recover this one.
    assert (tmp_path / ".allforai/bootstrap/node-specs/warehouse.md").read_bytes() == warehouse_spec
    _unrelated_is_valid(tmp_path)


@pytest.mark.parametrize("host", HOSTS)
def test_unmapped_external_change_is_reported_as_uncertain_impact(tmp_path, host):
    drift_project(tmp_path, host)

    # Source appears that no node declares: the semantic impact is undetermined,
    # so it is a conflict to coordinate, not a silent no-op and not a rebuild.
    (tmp_path / "pricing.py").write_text("def discount(total): return total * 0.5\n")
    result, report = external(tmp_path)
    assert result.returncode == 1 and report["status"] == "conflict", report
    change = next(c for c in report["changes"] if c["node_id"] is None)
    assert change["classification"] == "uncertain"
    assert change["files"] == {"pricing.py": "added"}
    assert change["impact"] == {"facts": ["pricing.py"], "documents": [], "product_decisions": [],
                                "tasks": [NODE, "warehouse"], "acceptance": []}
    assert "input mapping" in change["verification"]["reason"]
    assert change["resolution"] is None

    code, readiness = _readiness(tmp_path)
    assert code == 1
    held = sorted(b["node_id"] for b in readiness["blockers"] if b["code"] == "unresolved_external_change")
    assert held == [NODE, "warehouse"]
    assert _artifacts(tmp_path)["freshness"]["status"] == "uncertain"

    # Mapping the input and reverifying resolves it without any product decision.
    journal_before = (tmp_path / JOURNAL).read_bytes()
    workflow = json.loads((tmp_path / WORKFLOW).read_text())
    node = next(n for n in workflow["nodes"] if n["node_id"] == NODE)
    node["source_inputs"] = ["orders.py", "pricing.py"]
    write(tmp_path, WORKFLOW, workflow)
    (tmp_path / ".allforai/bootstrap/node-specs" / (NODE + ".md")).write_text(
        "---\n" + json.dumps(node) + "\n---\n" + (tmp_path / ".allforai/bootstrap/node-specs" /
                                                  (NODE + ".md")).read_text().split("---\n", 2)[2])
    code, published = _publish_evidence(tmp_path, command=ISOLATION)
    assert code == 0 and published["status"] == "valid", published
    assert external(tmp_path)[1] == {"status": "clear", "changes": []}
    assert (tmp_path / JOURNAL).read_bytes() == journal_before
    assert _readiness(tmp_path)[1]["status"] == "ready"


@pytest.mark.parametrize("host", HOSTS)
def test_unreadable_freshness_state_cannot_report_or_decide_external_changes(tmp_path, host):
    drift_project(tmp_path, host)
    (tmp_path / "orders.py").write_text(CONFLICTING)
    change = external(tmp_path)[1]["changes"][0]

    # A record that cannot be read cannot establish what changed outside the flow.
    write(tmp_path, ".allforai/bootstrap/evidence-freshness.json", {"nodes": [NODE]})
    result, report = external(tmp_path)
    assert result.returncode == 1 and report["status"] == "invalid"
    assert "unreadable" in report["reason"] and not result.stderr

    # No decision can be recorded against a change the current source cannot confirm.
    refused = _reject(tmp_path, change["change_id"], batch="external-3")
    assert refused.returncode == 1 and not refused.stderr
    assert "unreadable" in json.loads(refused.stdout)["error"]
    assert not [b for b in json.loads((tmp_path / JOURNAL).read_text())["batches"]
                if b["batch_id"] == "external-3"]

    # The gates fail closed on the same state: unreadable is never read as settled.
    code, readiness = _readiness(tmp_path)
    assert code == 1 and readiness["status"] == "not_ready" and readiness["blockers"]
    assert not [b for b in readiness["blockers"] if b["code"] == "external_change_repair_pending"]


@pytest.mark.parametrize("host", HOSTS)
def test_a_corrupt_change_store_reopens_the_conflict_instead_of_claiming_a_decision(tmp_path, host):
    drift_project(tmp_path, host)
    (tmp_path / "orders.py").write_text(CONFLICTING)
    change = external(tmp_path)[1]["changes"][0]
    assert _reject(tmp_path, change["change_id"]).returncode == 0

    # The recorded store is damaged: a lost decision is asked again, never assumed.
    write(tmp_path, STORE, {"schema_version": "1.0", "changes": "corrupt"})
    result, again = external(tmp_path)
    assert result.returncode == 1 and again["status"] == "conflict", again
    assert again["changes"][0]["change_id"] == change["change_id"]
    assert again["changes"][0]["resolution"] is None
    code, readiness = _readiness(tmp_path)
    assert code == 1
    assert not [b for b in readiness["blockers"] if b["code"] == "external_change_repair_pending"]
    assert [b["node_id"] for b in readiness["blockers"]
            if b["code"] == "unresolved_external_change"] == [NODE]


@pytest.mark.parametrize("host", HOSTS)
def test_accepting_an_unmapped_change_records_consent_without_inventing_intent(tmp_path, host):
    drift_project(tmp_path, host)
    requirement_before = (tmp_path / REQUIREMENT).read_bytes()
    (tmp_path / "pricing.py").write_text("def discount(total): return total * 0.5\n")
    change = next(c for c in external(tmp_path)[1]["changes"] if c["node_id"] is None)

    accepted = invoke(tmp_path, {"operation": "external-change", "change_id": change["change_id"],
                                 "resolution": "accept", "batch_id": "external-4", "actions": [],
                                 "user_reference": "user turn: the pricing module is intended",
                                 "reason": "The pricing module was added deliberately"})
    assert accepted.returncode == 0, accepted.stdout

    # The decision is recorded; no intent was invented for source with no confirmed decision.
    batch = next(b for b in json.loads((tmp_path / JOURNAL).read_text())["batches"] if b["batch_id"] == "external-4")
    assert batch["decisions"][0]["chosen"] == "Accept the changed source"
    assert batch["external_change"] == {"change_id": change["change_id"], "node_id": None,
                                        "resolution": "accept", "files": {"pricing.py": "added"}}
    assert (tmp_path / REQUIREMENT).read_bytes() == requirement_before

    # Consent settles the decision; it does not complete the delivery. The input still
    # needs mapping and the affected evidence still needs reverification.
    code, readiness = _readiness(tmp_path)
    assert code == 1 and not [b for b in readiness["blockers"] if b["code"] == "unresolved_external_change"]
    assert NODE in [b["node_id"] for b in readiness["blockers"] if b["code"] == "stale_evidence"]
    assert _artifacts(tmp_path)["freshness"]["status"] == "uncertain"
    assert external(tmp_path)[1]["status"] == "decided"


@pytest.mark.parametrize("host", HOSTS)
def test_a_rejected_change_survives_the_next_baseline_freeze(tmp_path, host):
    """A decision is about changed source content, not about the baseline version
    that happened to be current when it was recorded."""
    from .test_delivery_closure import _freeze

    drift_project(tmp_path, host)
    (tmp_path / "orders.py").write_text(CONFLICTING)
    change = external(tmp_path)[1]["changes"][0]
    assert _reject(tmp_path, change["change_id"]).returncode == 0

    # Refreezing the same confirmed scope advances the baseline version (the
    # rejection's own journal batch is newer than the frozen scope batch).
    assert _freeze(tmp_path, "scope-9")["version"] == 2

    # The unchanged source keeps its identity, so the settled decision is still reachable.
    result, again = external(tmp_path)
    assert result.returncode == 0 and again["status"] == "decided", again
    assert [c["change_id"] for c in again["changes"]] == [change["change_id"]]
    resolution = again["changes"][0]["resolution"]
    assert resolution["resolution"] == "reject"
    assert resolution["repair_task"]["files"] == ["orders.py"]

    # The scoped repair still blocks; the user is not asked the settled question again.
    code, readiness = _readiness(tmp_path)
    assert code == 1
    assert not [b for b in readiness["blockers"] if b["code"] == "unresolved_external_change"]
    assert [b["node_id"] for b in readiness["blockers"]
            if b["code"] == "external_change_repair_pending"] == [NODE]
    assert _artifacts(tmp_path)["freshness"]["repair"] == {"owner": NODE, "responsibilities": ["implementation"]}

    # Deciding again is refused: the recorded decision was never orphaned.
    refused = _reject(tmp_path, change["change_id"], batch="external-9")
    assert refused.returncode == 1 and "already rejected" in json.loads(refused.stdout)["error"], refused.stdout

    # Repairing the implementation closes it through the existing loop.
    (tmp_path / "orders.py").write_text("def list_orders(account): return [account] if account else []\n")
    code, published = _publish_evidence(tmp_path, command=ISOLATION)
    assert code == 0 and published["status"] == "valid", published
    assert external(tmp_path)[1] == {"status": "clear", "changes": []}
    assert _readiness(tmp_path)[1]["status"] == "ready"
    _unrelated_is_valid(tmp_path)


@pytest.mark.parametrize("host", HOSTS)
def test_a_revised_confirmed_intent_supersedes_the_earlier_decision(tmp_path, host):
    """A settled decision travels with the confirmed intent it was made against.
    When the user revises that intent, the old decision is history, not consent."""
    from .test_delivery_closure import decide

    drift_project(tmp_path, host)
    (tmp_path / "orders.py").write_text(CONFLICTING)
    change = external(tmp_path)[1]["changes"][0]
    assert _reject(tmp_path, change["change_id"]).returncode == 0

    # The user later revises the very requirement the rejection preserved.
    assert decide(tmp_path, [{"operation": "adjust", "id": "export", "reason": "Partner accounts were merged",
                              "changes": {"acceptance": PARTNER_ACCEPTANCE,
                                          "business_rules": ["The partner group's orders are exported together"]}}],
                  batch="revise-1").returncode == 0

    result, again = external(tmp_path)
    assert result.returncode == 1 and again["status"] == "conflict", again
    settled = again["changes"][0]
    assert settled["change_id"] == change["change_id"]
    assert settled["resolution"] is None
    # The superseded decision and its reason are preserved, not erased.
    history = settled["superseded_resolutions"]
    assert [item["resolution"] for item in history] == ["reject"]
    assert history[0]["reason"] == "Account isolation is a legal requirement"

    # The stale rejection no longer scopes a repair; the question returns to the user.
    code, readiness = _readiness(tmp_path)
    assert code == 1
    assert not [b for b in readiness["blockers"] if b["code"] == "external_change_repair_pending"]
    reopened = [b for b in readiness["blockers"] if b["code"] == "unresolved_external_change"]
    assert [b["node_id"] for b in reopened] == [NODE]
    assert "revised" in reopened[0]["message"] and "interactive" in reopened[0]["message"]
    # The revised requirement is not yet refrozen, so the interactive entry owns it.
    assert _artifacts(tmp_path)["freshness"]["repair"]["owner"] == "interactive-bootstrap"
    _unrelated_is_valid(tmp_path)


@pytest.mark.parametrize("host", HOSTS)
def test_drift_reaches_the_product_decision_owner_without_a_prior_detection_call(tmp_path, host):
    """The bootstrap/resume gates own the boundary comparison themselves: a conflict
    is routed to the interactive product decision even when nothing ran detection."""
    drift_project(tmp_path, host)
    journal_before = (tmp_path / JOURNAL).read_bytes()
    (tmp_path / "orders.py").write_text(CONFLICTING)

    code, readiness = _readiness(tmp_path)
    assert code == 1 and readiness["status"] == "not_ready"
    blocker = next(b for b in readiness["blockers"] if b["code"] == "unresolved_external_change")
    assert blocker["node_id"] == NODE and "interactive" in blocker["message"]
    assert _artifacts(tmp_path)["freshness"]["repair"] == {"owner": "interactive-bootstrap",
                                                          "responsibilities": ["product-decision"]}
    assert _reconcile(tmp_path)[1]["repair_owner"] == "interactive-bootstrap"

    # Nothing was decided or interviewed on the way, and the repeat is stable.
    assert (tmp_path / JOURNAL).read_bytes() == journal_before
    store = (tmp_path / STORE).read_bytes()
    again = _readiness(tmp_path)
    assert (again[0], again[1]["blockers"]) == (code, readiness["blockers"])
    assert (tmp_path / STORE).read_bytes() == store
    _unrelated_is_valid(tmp_path)

    # The user resolves the conflict the gate reported, without redetecting first.
    change_id = next(iter(json.loads((tmp_path / STORE).read_text())["changes"]))
    assert _reject(tmp_path, change_id).returncode == 0
    assert [b["code"] for b in _readiness(tmp_path)[1]["blockers"]
            if b["node_id"] == NODE and b["code"].startswith("external")] == ["external_change_repair_pending"]


@pytest.mark.parametrize("host", HOSTS)
def test_implementation_only_drift_keeps_its_node_owner_at_the_same_gates(tmp_path, host):
    """Routing the boundary comparison through the gates never turns a verified
    implementation fact into a product question."""
    drift_project(tmp_path, host)
    journal_before = (tmp_path / JOURNAL).read_bytes()
    requirement_before = (tmp_path / REQUIREMENT).read_bytes()
    (tmp_path / "orders.py").write_text("def list_orders(account): return [account, account]\n")

    code, readiness = _readiness(tmp_path)
    assert code == 1
    assert not [b for b in readiness["blockers"] if b["code"].startswith("external_change")
                or b["code"] == "unresolved_external_change"]
    assert [b["node_id"] for b in readiness["blockers"] if b["code"] == "stale_evidence"] == [NODE]
    repair = _artifacts(tmp_path)["freshness"]["repair"]
    assert repair["owner"] == NODE and "implementation" in repair["responsibilities"]

    assert (tmp_path / JOURNAL).read_bytes() == journal_before
    assert (tmp_path / REQUIREMENT).read_bytes() == requirement_before

    # Synchronizing the fact document and republishing closes it: no decision was needed.
    (tmp_path / DOC).write_text(_doc("['acme', 'acme']"))
    code, published = _publish_evidence(tmp_path, command=ISOLATION)
    assert code == 0 and published["status"] == "valid", published
    assert _readiness(tmp_path)[1]["status"] == "ready"
    _unrelated_is_valid(tmp_path)
