"""compute_completeness after ADR-0008: no hollow downgrade path, two hollow refusals.

hollowness-detector left /run; its judgement ("is this feature fake") is cross-exam's.
What stays is machine-decidable: a runtime entry served through a mock layer, or answering
with a canned fixture, is refused with the reason strings cross-exam's renderer uses and
never counted as verified. A hollowness-report on disk changes nothing any more.
"""
import json
from pathlib import Path

from .. import module_isolation

# compute_completeness lives beside the orchestrator directory, not in it.
SCRIPTS = str(Path(module_isolation.ORCHESTRATOR).parent)
_cc = module_isolation._isolation.load(SCRIPTS, "compute_completeness")
compute_completeness = _cc.compute_completeness
hollow_reason = _cc.hollow_reason

MOCK_REASON = "经 mock 层（msw, json-server）的 runtime 不能判 done"


def _capture(root, rel, stdout=""):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema": "capture_evidence/v1", "command": ["true"],
                                "exit_code": 0, "stdout": stdout, "stdout_sha256": "abc"}))
    return rel


def _entry(node, evidence_path, served_by=None, **extra):
    v = {"method": "real-api", "verifier": "v-agent", "claim": "works", "evidence_path": evidence_path}
    if served_by is not None:
        v["served_by"] = served_by
    v.update(extra)
    return {"node": node, "status": "completed", "generated_by": "gen-agent", "verification": v}


def _workflow(*entries):
    return {"nodes": [{"node_id": e["node"]} for e in entries], "transition_log": list(entries)}


def _row(report, node):
    return next(r for r in report["by_node"] if r["node_id"] == node)


def test_real_backend_with_empty_mock_layers_is_verified(tmp_path):
    ev = _capture(tmp_path, "ev/orders.json", stdout='{"orders": [{"id": 17}]}')
    served = {"host": "localhost:3000", "process": "node next dev (pid 4242)", "mock_layers": []}

    r = compute_completeness(_workflow(_entry("orders", ev, served)), str(tmp_path))

    assert (r["verified"], r["unverified"]) == (1, 0), r
    assert _row(r, "orders")["reason"] == ""


def test_mock_layer_refuses_with_the_engine_reason(tmp_path):
    ev = _capture(tmp_path, "ev/orders.json", stdout='{"orders": [{"id": 17}]}')
    served = {"host": "localhost:3000", "process": "node next dev", "mock_layers": ["msw", "json-server"]}

    r = compute_completeness(_workflow(_entry("orders", ev, served)), str(tmp_path))

    assert (r["verified"], r["unverified"]) == (0, 1), r
    assert _row(r, "orders") == {"node_id": "orders", "state": "unverified", "method": "real-api",
                                 "reason": MOCK_REASON}
    assert r["refused"] == [{"node_id": "orders", "reason": MOCK_REASON}]


def test_served_by_on_the_entry_itself_is_read_too(tmp_path):
    """A gate that writes the ledger-entry shape puts served_by beside verification, not in it."""
    ev = _capture(tmp_path, "ev/orders.json", stdout="{}")
    e = _entry("orders", ev)
    e["served_by"] = {"host": "localhost:3000", "process": "node", "mock_layers": ["miragejs"]}

    r = compute_completeness(_workflow(e), str(tmp_path))

    assert _row(r, "orders")["reason"] == "经 mock 层（miragejs）的 runtime 不能判 done"


def test_response_identical_to_a_declared_fixture_is_refused(tmp_path):
    fixture = tmp_path / "mocks/orders.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text('{\n  "orders": [{"id": 1, "total": "9.99"}]\n}\n')
    ev = _capture(tmp_path, "ev/orders.json", stdout='{"orders": [{"id": 1, "total": "9.99"}]}')
    served = {"host": "localhost:3000", "process": "node", "mock_layers": [], "fixtures": ["mocks/orders.json"]}

    r = compute_completeness(_workflow(_entry("orders", ev, served)), str(tmp_path))

    assert (r["verified"], r["unverified"]) == (0, 1), r
    assert _row(r, "orders")["reason"] == "响应与 fixture 一致（mocks/orders.json）的 runtime 不能判 done"


def test_response_that_differs_from_every_fixture_is_verified(tmp_path):
    fixture = tmp_path / "mocks/orders.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text('{"orders": [{"id": 1, "total": "9.99"}]}')
    ev = _capture(tmp_path, "ev/orders.json", stdout='{"orders": [{"id": 1, "total": "12.50"}]}')
    served = {"host": "localhost:3000", "process": "node", "mock_layers": [], "fixtures": ["mocks/orders.json"]}

    r = compute_completeness(_workflow(_entry("orders", ev, served)), str(tmp_path))

    assert (r["verified"], r["unverified"]) == (1, 0), r


def test_plain_response_file_is_compared_against_fixtures_as_well(tmp_path):
    """Evidence that is not a capture record (an API transcript) is matched by its own text."""
    fixture = tmp_path / "fixtures/profile.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text('{"name": "Sample User"}')
    ev = tmp_path / "ev/profile.json"
    ev.parent.mkdir(parents=True)
    ev.write_text('{"name": "Sample User"}\n')
    e = _entry("profile", "ev/profile.json",
               {"host": "localhost", "process": "go run", "mock_layers": [], "fixtures": ["fixtures/profile.json"]})
    e["verification"]["method"] = "screenshot"   # not a capture-record method, so the file is read as-is

    r = compute_completeness(_workflow(e), str(tmp_path))

    assert _row(r, "profile")["reason"] == "响应与 fixture 一致（fixtures/profile.json）的 runtime 不能判 done"


def test_an_unreadable_fixture_is_a_reason_not_a_traceback(tmp_path):
    ev = _capture(tmp_path, "ev/orders.json", stdout="{}")
    served = {"host": "localhost", "process": "node", "mock_layers": [], "fixtures": ["mocks/gone.json"]}

    r = compute_completeness(_workflow(_entry("orders", ev, served)), str(tmp_path))

    assert _row(r, "orders")["state"] == "unverified"
    assert "mocks/gone.json" in _row(r, "orders")["reason"]


def test_hollow_refusal_only_applies_to_evidence_that_would_otherwise_count(tmp_path):
    """A node that is already unverified or failed keeps that state and its own reason."""
    served = {"host": "localhost", "process": "node", "mock_layers": ["msw"]}
    e = _entry("orders", "ev/missing.json", served)
    failed = {"node": "checkout", "status": "failed", "served_by": served}

    r = compute_completeness(_workflow(e, failed), str(tmp_path))

    assert (_row(r, "orders")["state"], _row(r, "orders")["reason"]) == ("unverified", "")
    assert (_row(r, "checkout")["state"], _row(r, "checkout")["reason"]) == ("failed", "")
    assert r["refused"] == []


def test_hollowness_report_no_longer_downgrades_anything(tmp_path):
    """The downgrade path hollowness-detector fed is gone: its report file is not read."""
    ev = _capture(tmp_path, "ev/orders.json", stdout="{}")
    report = tmp_path / ".allforai/quality/hollowness-report.json"
    report.parent.mkdir(parents=True)
    report.write_text(json.dumps({"hollow_nodes": [{"node_id": "orders", "type": "fake_success",
                                                     "downgrade_to": "unverified"}]}))

    served = {"host": "localhost:3000", "process": "node", "mock_layers": []}
    r = compute_completeness(_workflow(_entry("orders", ev, served)), str(tmp_path))

    assert (r["verified"], r["unverified"]) == (1, 0), r
    assert "hollow" not in json.dumps(r)


def test_a_runtime_claim_without_served_by_is_not_verified():
    """Nothing asked the node where its requests went, so nothing can say they went to the real thing."""
    for method in ("real-run", "real-api", "db-query", "screenshot"):
        entry = {"node_id": "n", "verification": {"method": method, "evidence_path": "e.json"}}
        reason = hollow_reason(entry)
        assert "served_by" in reason and "不计 verified" in reason, (method, reason)


def test_a_suite_run_and_a_generated_only_node_need_no_served_by():
    # real-test is a mechanical run; none never counted anyway
    for method in ("real-test", "none"):
        assert hollow_reason({"node_id": "n", "verification": {"method": method}}) == ""
