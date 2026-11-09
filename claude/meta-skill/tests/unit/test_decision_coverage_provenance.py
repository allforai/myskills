"""A0 decision coverage must prove it was produced against the plan it covers (ADR-0011).

A shape-valid `decision-coverage.json` with `missing: []` used to pass every gate, so an
audit nobody ran and a thorough one looked the same. Coverage now carries the passes that
produced it, and the receiving gates recompute the digests of what those passes read.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from ..module_isolation import load

_validate_bootstrap = load("validate_bootstrap")
decision_coverage_findings = _validate_bootstrap.decision_coverage_findings
decision_coverage_shape_errors = _validate_bootstrap.decision_coverage_shape_errors
structural_gate_blockers = _validate_bootstrap.structural_gate_blockers

AUDIT_CLI = Path(__file__).resolve().parents[2] / "scripts/validate_audit_outputs.py"
BASELINE = ".allforai/product-concept/concept-baseline.json"
NODES = ("design-rules", "build-client")


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _sha(root, rel):
    return hashlib.sha256((root / rel).read_bytes()).hexdigest()


def _spec(node_id):
    return f".allforai/bootstrap/node-specs/{node_id}.md"


def _pass(root, angle, paths, **overrides):
    value = {"angle": angle, "independent": True, "reader": f"{angle} sub-agent",
             "produced_at": "2026-11-09T08:00:00Z",
             "inputs": [{"path": p, "sha256": _sha(root, p)} for p in paths]}
    value.update(overrides)
    return value


def _coverage(root, *, missing=(), passes=None):
    if passes is None:
        passes = [_pass(root, "concept", [BASELINE]),
                  _pass(root, "node-rehearsal", [_spec(n) for n in NODES])]
    return {"captured": [], "missing": list(missing), "provenance": {"passes": passes}}


def _project(root, route="new-product", coverage=None):
    bdir = root / ".allforai/bootstrap"
    _write(root, ".allforai/bootstrap/bootstrap-profile.json", json.dumps({"task_route": route}))
    _write(root, ".allforai/bootstrap/workflow.json",
           json.dumps({"nodes": [{"node_id": n} for n in NODES], "transition_log": []}))
    for n in NODES:
        _write(root, _spec(n), f"---\nnode_id: {n}\n---\n# {n}\n")
    _write(root, BASELINE, json.dumps({"intent_baseline": {"version": 3}}))
    if coverage is not None:
        _write(root, ".allforai/bootstrap/decision-coverage.json", json.dumps(coverage(root)))
    return str(bdir)


def _codes(findings):
    return [f["code"] for f in findings]


def test_complete_provenance_passes_even_with_nothing_missing(tmp_path):
    bdir = _project(tmp_path, coverage=_coverage)
    assert decision_coverage_findings(bdir) == []


def test_absent_coverage_blocks_a_product_route(tmp_path):
    bdir = _project(tmp_path)
    assert _codes(decision_coverage_findings(bdir)) == ["missing_decision_coverage"]


def test_hand_written_empty_audit_is_unproven(tmp_path):
    # The incident: shape-valid, `missing: []`, no trace of any pass having run.
    bdir = _project(tmp_path, coverage=lambda root: {"captured": [], "missing": []})
    assert _codes(decision_coverage_findings(bdir)) == ["decision_coverage_unproven"]


def test_one_angle_is_not_coverage(tmp_path):
    bdir = _project(tmp_path, coverage=lambda root: _coverage(
        root, passes=[_pass(root, "concept", [BASELINE])]))
    findings = decision_coverage_findings(bdir)
    assert _codes(findings) == ["decision_coverage_unproven"]
    assert "node-rehearsal" in findings[0]["message"]


def test_a_node_spec_edited_after_rehearsal_makes_coverage_stale(tmp_path):
    bdir = _project(tmp_path, coverage=_coverage)
    _write(tmp_path, _spec("design-rules"), "---\nnode_id: design-rules\n---\n# now writes rules\n")
    findings = decision_coverage_findings(bdir)
    assert _codes(findings) == ["stale_decision_coverage"]
    assert findings[0].get("node_id") == "design-rules"


def test_a_node_added_after_rehearsal_is_not_covered(tmp_path):
    bdir = _project(tmp_path, coverage=_coverage)
    wf = tmp_path / ".allforai/bootstrap/workflow.json"
    wf.write_text(json.dumps({"nodes": [{"node_id": n} for n in NODES + ("late-node",)],
                              "transition_log": []}))
    _write(tmp_path, _spec("late-node"), "---\nnode_id: late-node\n---\n")
    findings = decision_coverage_findings(bdir)
    assert _codes(findings) == ["stale_decision_coverage"]
    assert findings[0].get("node_id") == "late-node"


def test_re_rehearsing_only_the_changed_node_restores_coverage(tmp_path):
    bdir = _project(tmp_path, coverage=_coverage)
    _write(tmp_path, _spec("design-rules"), "---\nnode_id: design-rules\n---\n# revised\n")
    path = tmp_path / ".allforai/bootstrap/decision-coverage.json"
    coverage = json.loads(path.read_text())
    coverage["provenance"]["passes"].append(_pass(tmp_path, "node-rehearsal", [_spec("design-rules")]))
    path.write_text(json.dumps(coverage))
    assert decision_coverage_findings(bdir) == []


def test_a_refrozen_baseline_makes_the_concept_angle_stale(tmp_path):
    bdir = _project(tmp_path, coverage=_coverage)
    _write(tmp_path, BASELINE, json.dumps({"intent_baseline": {"version": 4}}))
    assert _codes(decision_coverage_findings(bdir)) == ["stale_decision_coverage"]


def test_a_pass_that_was_not_independent_must_say_so(tmp_path):
    _project(tmp_path)
    coverage = _coverage(tmp_path, passes=[
        _pass(tmp_path, "concept", [BASELINE]),
        _pass(tmp_path, "node-rehearsal", [_spec(n) for n in NODES], independent=False)])
    errors = decision_coverage_shape_errors(coverage)
    assert any("disclosure" in e for e in errors)


def test_a_disclosed_serial_pass_is_accepted_and_reported(tmp_path):
    def serial(root):
        return _coverage(root, passes=[
            _pass(root, "concept", [BASELINE]),
            _pass(root, "node-rehearsal", [_spec(n) for n in NODES], independent=False,
                  disclosure="No sub-agent extension; rehearsed serially in the planner's context")])
    bdir = _project(tmp_path, coverage=serial)
    assert decision_coverage_findings(bdir) == []
    assert _validate_bootstrap.decision_coverage_disclosures(bdir) == [
        "node-rehearsal: No sub-agent extension; rehearsed serially in the planner's context"]


def test_local_change_routes_are_not_held_to_this_gate(tmp_path):
    bdir = _project(tmp_path, route="local-change")
    assert decision_coverage_findings(bdir) == []


def test_the_run_entry_reads_the_same_rule(tmp_path):
    _project(tmp_path, coverage=lambda root: {"captured": [], "missing": []})
    assert "decision_coverage_unproven" in _codes(structural_gate_blockers(tmp_path))


@pytest.mark.parametrize("coverage,expected", [
    (lambda root: {"captured": [], "missing": []}, 1),
    (_coverage, 0),
])
def test_audit_cli_rejects_coverage_without_provenance(tmp_path, coverage, expected):
    _project(tmp_path)
    path = _write(tmp_path, "coverage.json", json.dumps(coverage(tmp_path)))
    result = subprocess.run([sys.executable, str(AUDIT_CLI), "decision-coverage", str(path)],
                            text=True, capture_output=True)
    assert result.returncode == expected, (result.stdout, result.stderr)


_readiness = load("validate_unattended_readiness")


@pytest.mark.parametrize("record", [
    json.dumps({"node_id": "design-rules", "decisions": [
        {"decision_id": "d1", "needed_decision": "Shared or per instance?",
         "options": ["shared", "per-instance"], "blocking_intent_ids": []}]}),
    "{not json",
])
def test_a_recorded_product_decision_gap_blocks_the_next_run(tmp_path, record):
    _project(tmp_path, coverage=_coverage)
    _write(tmp_path, ".allforai/bootstrap/product-decision-gaps/design-rules.json", record)
    report = _readiness.validate_unattended_readiness(tmp_path)
    gaps = [b for b in report["blockers"] if b["code"] == "pending_product_decision"]
    assert [b.get("node_id") for b in gaps] == ["design-rules"]


def test_no_gap_record_no_gap_blocker(tmp_path):
    _project(tmp_path, coverage=_coverage)
    report = _readiness.validate_unattended_readiness(tmp_path)
    assert not [b for b in report["blockers"] if b["code"] == "pending_product_decision"]
