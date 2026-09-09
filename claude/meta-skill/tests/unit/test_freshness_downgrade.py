"""Freshness admission cannot be downgraded to legacy (#12 admission downgrade holes).

A completion label in the transition log is not provenance. Removing
`source_inputs` from a previously published node, or adding completed history
to newly scoped undeclared work, must not turn intent-aware work into admitted
legacy history; a legacy admission never admits evaluated stale or invalid
evidence; a corrupt or unknown freshness record fails closed. Genuinely
retained out-of-current-scope history keeps its warning-only behavior with no
invented provenance. These exercise copied CLIs in temporary projects on both
host adapters, not actual Claude/Codex host dialogue.
"""
import json
from pathlib import Path
import sys

import pytest

from .test_bootstrap_scope import (ATTENTION_CONTRACT_BODY, REF, codex_transition, confirm_plan,
                                   project, publish_contract, write)
from .test_freshness_admission_corrections import (
    _ABSENT, _artifacts, _blockers, _bootstrap, _readiness, _reconcile, _set_node, HOSTS, NODE, WORKFLOW)

STATE = ".allforai/bootstrap/evidence-freshness.json"
REPO = Path(__file__).resolve().parents[4]
OLD_REF = {"path": ".allforai/bootstrap/decision-warehouse.json", "id": "stock", "revision": 1}
PASSING_EVIDENCE = [sys.executable, "-c",
                    "import json; assert json.load(open('.allforai/bootstrap/export-report.json'))['status'] == 'passed'"]


def _complete(root, node_id, host):
    """Record a completed transition through each host's native log shape."""
    if host == "codex":
        codex_transition(root, node_id, "completed")
        return
    workflow = json.loads((root / WORKFLOW).read_text())
    workflow["transition_log"].append({"node_id": node_id, "status": "completed"})
    write(root, WORKFLOW, workflow)


def _append_node(root, node, *, confirmed=True):
    """Add a node to the plan. `confirmed=False` scripts a plan the user never saw."""
    workflow = json.loads((root / WORKFLOW).read_text())
    workflow["nodes"].append(node)
    write(root, WORKFLOW, workflow)
    if confirmed:
        confirm_plan(root, reason="Presented the retained node with the plan")
    (root / ".allforai/bootstrap/node-specs" / (node["node_id"] + ".md")).write_text(
        "---\n" + json.dumps(node) + "\n---\n" + ATTENTION_CONTRACT_BODY)


def _assert_refused_as_missing(root, node_id=NODE):
    code, errors = _bootstrap(root)
    assert code == 1 and any(node_id in e and "source_inputs" in e for e in errors), errors
    code, report = _readiness(root)
    assert code == 1 and report["status"] == "not_ready"
    assert node_id in [b["node_id"] for b in _blockers(report, "missing_source_inputs")], report["blockers"]
    checked = _artifacts(root, node_id)
    assert checked["all_exist"] is False
    assert checked["freshness"]["admission"] == "missing"
    assert checked["freshness"]["status"] != "valid"
    node, plan = _reconcile(root, node_id)
    assert node["artifact_readiness"] == "blocked" and plan["action"] == "invalidate"
    assert "missing_source_inputs" in node["artifacts"][0]["blockers"]
    assert "missing_source_inputs" in plan["reasons"]


def _assert_admitted_legacy(root, node_id, *, other_blockers=()):
    """The retained node is admitted with a warning; only the listed blockers may exist elsewhere."""
    assert _bootstrap(root)[0] == 0
    code, report = _readiness(root)
    assert code == (1 if other_blockers else 0), report["blockers"]
    assert report["status"] == ("not_ready" if other_blockers else "ready"), report["blockers"]
    assert {(b["code"], b["node_id"]) for b in report["blockers"]} == set(other_blockers), report["blockers"]
    assert node_id in [w["node_id"] for w in report["warnings"] if w["code"] == "undeclared_source_inputs"]
    checked = _artifacts(root, node_id)
    assert checked["all_exist"] is True
    assert checked["freshness"]["admission"] == "legacy" and checked["freshness"]["status"] == "undeclared"
    node, plan = _reconcile(root, node_id)
    assert node["artifact_readiness"] == "complete" and plan["action"] == "keep"


@pytest.mark.parametrize("host", HOSTS)
def test_removing_source_inputs_from_a_published_completed_node_cannot_admit_stale_evidence(tmp_path, host):
    project(tmp_path, confirmed=True, host=host)
    write(tmp_path, ".allforai/bootstrap/export-report.json", {"status": "passed"})
    publish_contract(tmp_path, kind="evidence", verification_command=PASSING_EVIDENCE)
    _complete(tmp_path, NODE, host)
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is True and checked["freshness"]["status"] == "valid"

    # The product source changes: the published evidence is stale and traced as such.
    (tmp_path / "orders.py").write_text("def list_orders(account): return [42]\n")
    assert _artifacts(tmp_path)["all_exist"] is False
    assert _artifacts(tmp_path)["freshness"]["status"] == "stale"

    # Withdrawing the declaration cannot launder the stale evidence into admitted history:
    # the node is current scoped work with recorded provenance, not retained legacy.
    _set_node(tmp_path, source_inputs=_ABSENT)
    _assert_refused_as_missing(tmp_path)

    # Restoring the declaration reactivates tracing; reverification admits it again.
    _set_node(tmp_path, source_inputs=["orders.py"])
    assert _artifacts(tmp_path)["freshness"]["status"] == "stale"
    publish_contract(tmp_path, kind="evidence", verification_command=PASSING_EVIDENCE)
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is True and checked["freshness"]["admission"] == "declared"


@pytest.mark.parametrize("host", HOSTS)
def test_removing_source_inputs_from_a_recorded_node_outside_current_scope_is_not_legacy(tmp_path, host):
    """A record proves the node once declared; losing the declaration is a missing one, whatever the scope."""
    project(tmp_path, confirmed=True, host=host)
    write(tmp_path, ".allforai/bootstrap/export-report.json", {"status": "passed"})
    publish_contract(tmp_path, kind="evidence", verification_command=PASSING_EVIDENCE)
    _complete(tmp_path, NODE, host)
    # The scope moves on to another requirement; deliver-export becomes historical work.
    profile = json.loads((tmp_path / ".allforai/bootstrap/bootstrap-profile.json").read_text())
    profile["task_scope"] = {"areas": ["warehouse"], "requirement_refs": [OLD_REF]}
    write(tmp_path, ".allforai/bootstrap/bootstrap-profile.json", profile)
    write(tmp_path, OLD_REF["path"], {"requirements": [{"id": "stock", "revision": 1, "status": "confirmed",
                                                          "scope": ["warehouse"], "goal": "Track stock",
                                                          "business_rules": ["Stock never goes negative"],
                                                          "acceptance": ["Stock counts reconcile"],
                                                          "confirmation": {"source": "user", "reference": "turn 1",
                                                                           "decision_id": "confirm-stock-1",
                                                                           "reason": "Required"}}]})
    _append_node(tmp_path, {"node_id": "warehouse", "goal": "Track warehouse stock", "capability": "implement",
                            "exit_artifacts": [".allforai/bootstrap/stock.json"], "requirement_refs": [OLD_REF],
                            "decision_inputs": [OLD_REF["path"]], "responsibilities": ["implementation"],
                            "source_inputs": []})
    write(tmp_path, ".allforai/bootstrap/stock.json", {"status": "passed"})

    (tmp_path / "orders.py").write_text("def list_orders(account): return [42]\n")
    _set_node(tmp_path, source_inputs=_ABSENT)
    checked = _artifacts(tmp_path)
    assert checked["all_exist"] is False and checked["freshness"]["admission"] == "missing"
    code, report = _readiness(tmp_path)
    assert NODE in [b["node_id"] for b in _blockers(report, "missing_source_inputs")], report["blockers"]
    node, plan = _reconcile(tmp_path)
    assert node["artifact_readiness"] == "blocked" and "missing_source_inputs" in plan["reasons"]


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("shape", ["existing-node", "new-node"])
def test_completed_history_on_scoped_undeclared_work_does_not_bypass_declaration(tmp_path, host, shape):
    project(tmp_path, confirmed=True, host=host, source_inputs=None)
    write(tmp_path, ".allforai/bootstrap/export-report.json", {"status": "passed"})
    node_id = NODE
    if shape == "new-node":
        node_id = "deliver-audit"
        _append_node(tmp_path, {"node_id": node_id, "goal": "Audit the export", "capability": "implement",
                                "exit_artifacts": [".allforai/bootstrap/audit-report.json"],
                                "requirement_refs": [REF], "decision_inputs": [".allforai/bootstrap/local-requirements.json"],
                                "responsibilities": ["verification"]})
        write(tmp_path, ".allforai/bootstrap/audit-report.json", {"status": "passed"})
    _assert_refused_as_missing(tmp_path, node_id)

    # A completion label without provenance is not retained history for current scoped work.
    _complete(tmp_path, node_id, host)
    _assert_refused_as_missing(tmp_path, node_id)
    assert _artifacts(tmp_path, node_id)["freshness"]["status"] == "undeclared"


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("historical_refs", ["absent", "empty", "out-of-scope"])
def test_retained_out_of_scope_history_stays_legacy_without_invented_provenance(tmp_path, host, historical_refs):
    project(tmp_path, confirmed=True, host=host)
    write(tmp_path, ".allforai/bootstrap/export-report.json", {"status": "passed"})
    publish_contract(tmp_path, kind="evidence", verification_command=PASSING_EVIDENCE)
    old = {"node_id": "warehouse", "goal": "Retain completed warehouse work", "capability": "implement",
           "exit_artifacts": [".allforai/bootstrap/stock.json"], "decision_inputs": [], "responsibilities": ["implementation"]}
    if historical_refs == "out-of-scope":
        old["requirement_refs"] = [OLD_REF]
        old["decision_inputs"] = [OLD_REF["path"]]
        write(tmp_path, OLD_REF["path"], {"requirements": [{"id": "stock", "revision": 1, "status": "confirmed"}]})
    elif historical_refs == "empty":
        old["requirement_refs"] = []
    _append_node(tmp_path, old)
    write(tmp_path, ".allforai/bootstrap/stock.json", {"status": "passed"})
    _complete(tmp_path, "warehouse", host)
    _assert_admitted_legacy(tmp_path, "warehouse")
    assert "warehouse" not in json.loads((tmp_path / STATE).read_text()).get("nodes", {})

    # Changing the current product source does not touch history nobody claims to trace.
    # The declared node is stale, and the impact of the out-of-flow edit is unverified
    # until the explicit verification runs; neither reaches the retained legacy node.
    (tmp_path / "orders.py").write_text("def list_orders(account): return [42]\n")
    _assert_admitted_legacy(tmp_path, "warehouse", other_blockers=[("stale_evidence", NODE),
                                                                  ("unverified_external_change", NODE)])
    assert _artifacts(tmp_path)["freshness"]["status"] == "stale"


CORRUPT_STATES = [
    ("not-json", "{nodes"),
    ("array-root", "[]"),
    ("list-bucket", '{"nodes": []}'),
    ("string-bucket", '{"contracts": "warehouse"}'),
    ("unknown-record", '{"nodes": {"warehouse": 1}}'),
    ("null-record", '{"nodes": {"deliver-export": null}}'),
]


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("label,content", CORRUPT_STATES, ids=[label for label, _ in CORRUPT_STATES])
def test_corrupt_or_unknown_freshness_record_fails_closed_for_every_node(tmp_path, host, label, content):
    project(tmp_path, confirmed=True, host=host)
    write(tmp_path, ".allforai/bootstrap/export-report.json", {"status": "passed"})
    publish_contract(tmp_path, kind="evidence", verification_command=PASSING_EVIDENCE)
    _append_node(tmp_path, {"node_id": "warehouse", "goal": "Retain completed warehouse work", "capability": "implement",
                            "exit_artifacts": [".allforai/bootstrap/stock.json"], "decision_inputs": []})
    write(tmp_path, ".allforai/bootstrap/stock.json", {"status": "passed"})
    _complete(tmp_path, "warehouse", host)
    assert _artifacts(tmp_path)["all_exist"] is True
    _assert_admitted_legacy(tmp_path, "warehouse")
    intact = (tmp_path / STATE).read_text()

    (tmp_path / STATE).write_text(content)
    for node_id in (NODE, "warehouse"):
        checked = _artifacts(tmp_path, node_id)
        assert checked["all_exist"] is False, (node_id, checked)
        assert checked["freshness"]["status"] == "invalid", (node_id, checked)
        assert "unreadable" in checked["freshness"]["reason"].lower() or "cannot be evaluated" in checked["freshness"]["reason"]
        node, plan = _reconcile(tmp_path, node_id)
        assert node["artifact_readiness"] == "blocked" and plan["action"] == "invalidate"
    code, report = _readiness(tmp_path)
    assert code == 1 and report["status"] == "not_ready"
    assert {b["node_id"] for b in _blockers(report, "stale_evidence")} >= {NODE, "warehouse"}, report["blockers"]
    assert (tmp_path / STATE).read_text() == content

    # Restoring the recorded state restores both admissions without republishing.
    (tmp_path / STATE).write_text(intact)
    assert _artifacts(tmp_path)["all_exist"] is True
    _assert_admitted_legacy(tmp_path, "warehouse")


def test_legacy_admission_never_admits_evaluated_or_unknown_status():
    sys.path.insert(0, str(REPO / "claude/meta-skill/scripts/orchestrator"))
    from check_artifacts import freshness_admits
    assert freshness_admits(None) is True
    assert freshness_admits({"status": "valid", "admission": "declared"}) is True
    assert freshness_admits({"status": "undeclared", "readiness_status": "undeclared", "admission": "legacy"}) is True
    for withheld in ({"status": "stale", "admission": "legacy"},
                     {"status": "invalid", "admission": "legacy"},
                     {"status": "uncertain", "admission": "legacy"},
                     {"status": "valid", "admission": "legacy"},
                     {"admission": "legacy"},
                     {"status": "undeclared", "admission": "missing"},
                     {"status": "unknown"},
                     {},
                     "valid",
                     ["valid"]):
        assert freshness_admits(withheld) is False, withheld


@pytest.mark.parametrize("history", [42, None, "completed", {"deliver-export": "completed"},
                                     [None], ["completed"], [{"node_id": [], "status": "completed"}],
                                     [{"node_id": {"id": "deliver-export"}, "status": "completed"}],
                                     [{"node_id": "deliver-export"}]],
                         ids=["number", "null", "string", "object", "null-entry", "string-entry",
                              "array-node-id", "object-node-id", "missing-status"])
def test_malformed_history_never_completes_scoped_undeclared_work(history):
    sys.path.insert(0, str(REPO / "claude/meta-skill/scripts/orchestrator"))
    from check_artifacts import freshness_admission
    node = {"node_id": "deliver-export", "requirement_refs": [REF], "exit_artifacts": []}
    workflow = {"nodes": [node], "transition_log": history}
    assert freshness_admission(node, workflow) == "missing"
    assert freshness_admission({**node, "source_inputs": []}, workflow) == "declared"
