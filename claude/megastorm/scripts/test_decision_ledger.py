import json

import pytest

import decision_ledger as dl
from decision_ledger import (
    finalize_decision, init_run, record_decision, unified_records,
)


def _envelope():
    return {"run_id": "run-1", "scope": ["repo"], "network": False}


def _proposal():
    return {
        "phase": "1.3", "branch_id": "payments", "task_id": "pay-1",
        "question": "Which transaction boundary?", "options_considered": ["db", "queue"],
        "chosen": "db", "reason": "existing convention", "assumptions": [],
        "risk": "low", "reversible": True, "authority": "inside-envelope",
        "authority_basis": {"field": "scope", "value": ["repo"]},
        "affected_artifacts": ["src/payments.py"],
    }


def test_record_then_finalize_is_one_to_one(tmp_path):
    init_run(tmp_path, _envelope())
    record = record_decision(tmp_path, _proposal())
    assert record["decision_id"] == "D-0001"
    assert record["outcome"] is None
    final = finalize_decision(
        tmp_path, "D-0001", "action-taken", "event:42")
    assert final["outcome"] == "action-taken"
    assert len(unified_records(tmp_path)) == 1


def test_authority_basis_must_match_envelope(tmp_path):
    init_run(tmp_path, _envelope())
    proposal = _proposal()
    proposal["authority_basis"]["value"] = ["elsewhere"]
    with pytest.raises(ValueError, match="frozen envelope"):
        record_decision(tmp_path, proposal)


def test_cannot_finalize_twice(tmp_path):
    init_run(tmp_path, _envelope())
    record_decision(tmp_path, _proposal())
    finalize_decision(tmp_path, "D-0001", "deferred", "skip:pay-1")
    with pytest.raises(ValueError, match="already finalized"):
        finalize_decision(tmp_path, "D-0001", "deferred", "skip:pay-1")


def test_unified_records_reads_emergency_journal(tmp_path):
    init_run(tmp_path, _envelope())
    emergency = {"decision_id": "E-1", "outcome": "deferred"}
    (tmp_path / "decision-emergency.ndjson").write_text(
        json.dumps(emergency) + "\n", encoding="utf-8")
    records = unified_records(tmp_path)
    assert records[0]["durability"] == "emergency"


def test_ledger_write_failure_defers_to_emergency_journal(tmp_path, monkeypatch):
    init_run(tmp_path, _envelope())
    attempts = []
    def fail(*_):
        attempts.append(1)
        raise OSError("disk failure")
    monkeypatch.setattr(dl, "_atomic_json", fail)
    record = record_decision(tmp_path, _proposal())
    assert len(attempts) == 3
    assert record["outcome"] == "deferred"
    assert record["durability"] == "emergency"
    assert unified_records(tmp_path)[0]["decision_id"].startswith("E-")
    assert (tmp_path / "decision-ledger.lock").exists()
