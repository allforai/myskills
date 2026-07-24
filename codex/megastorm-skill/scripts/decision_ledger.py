#!/usr/bin/env python3
"""Run-scoped autonomous decision ledger for unattended Megastorm phases."""

import argparse
import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

TERMINAL_OUTCOMES = {"action-taken", "fallback-taken", "deferred"}
RISKS = {"low", "medium", "high"}
AUTHORITIES = {"inside-envelope", "deferred"}


def _read_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _atomic_json_retry(path, value):
    last_error = None
    for _ in range(3):
        try:
            _atomic_json(path, value)
            return
        except OSError as exc:
            last_error = exc
    raise last_error


@contextmanager
def _single_writer(run_dir):
    lock_path = Path(run_dir) / "decision-ledger.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def init_run(run_dir, envelope):
    run_dir = Path(run_dir)
    run_id = envelope.get("run_id")
    if not run_id:
        raise ValueError("decision envelope requires run_id")
    _atomic_json(run_dir / "decision-envelope.json", envelope)
    ledger = run_dir / "decision-ledger.json"
    if not ledger.exists():
        _atomic_json(ledger, {"run_id": run_id, "records": []})


def _validate_proposal(proposal, envelope):
    required = {
        "phase", "branch_id", "question", "options_considered", "chosen",
        "reason", "assumptions", "risk", "reversible", "authority",
        "authority_basis", "affected_artifacts",
    }
    missing = sorted(required - proposal.keys())
    if missing:
        raise ValueError(f"decision proposal missing: {', '.join(missing)}")
    if proposal["risk"] not in RISKS:
        raise ValueError("invalid risk")
    if proposal["authority"] not in AUTHORITIES:
        raise ValueError("invalid authority")
    if proposal["authority"] == "inside-envelope":
        basis = proposal["authority_basis"]
        field = basis.get("field") if isinstance(basis, dict) else None
        if field not in envelope or envelope[field] != basis.get("value"):
            raise ValueError("authority_basis does not cite the frozen envelope")


def record_decision(run_dir, proposal):
    run_dir = Path(run_dir)
    envelope = _read_json(run_dir / "decision-envelope.json", {})
    _validate_proposal(proposal, envelope)
    ledger_path = run_dir / "decision-ledger.json"
    with _single_writer(run_dir):
        ledger = _read_json(ledger_path, {"run_id": envelope["run_id"], "records": []})
        record = dict(proposal)
        record.update({
            "decision_id": f"D-{len(ledger['records']) + 1:04d}",
            "run_id": envelope["run_id"],
            "task_id": proposal.get("task_id"),
            "fallback": proposal.get("fallback"),
            "outcome": None,
            "result_ref": None,
            "skipped_dependents": proposal.get("skipped_dependents", []),
        })
        ledger["records"].append(record)
        try:
            _atomic_json_retry(ledger_path, ledger)
        except OSError:
            record["decision_id"] = f"E-{len(unified_records(run_dir)) + 1:04d}"
            record["authority"] = "deferred"
            record["outcome"] = "deferred"
            record["result_ref"] = f"emergency:{record['decision_id']}"
            record["durability"] = "emergency"
            emergency = run_dir / "decision-emergency.ndjson"
            with emergency.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
    return record


def finalize_decision(run_dir, decision_id, outcome, result_ref, skipped=None):
    if outcome not in TERMINAL_OUTCOMES or not result_ref:
        raise ValueError("terminal outcome and result_ref are required")
    path = Path(run_dir) / "decision-ledger.json"
    with _single_writer(run_dir):
        ledger = _read_json(path, {})
        matches = [r for r in ledger.get("records", []) if r["decision_id"] == decision_id]
        if len(matches) != 1:
            raise ValueError("decision_id not found or duplicated")
        record = matches[0]
        if record["outcome"] is not None:
            raise ValueError("decision already finalized")
        record["outcome"] = outcome
        record["result_ref"] = result_ref
        if skipped is not None:
            record["skipped_dependents"] = skipped
        _atomic_json_retry(path, ledger)
    return record


def unified_records(run_dir):
    run_dir = Path(run_dir)
    records = list(_read_json(
        run_dir / "decision-ledger.json", {"records": []}).get("records", []))
    for record in records:
        record.setdefault("durability", "ledger")
    emergency = run_dir / "decision-emergency.ndjson"
    if emergency.exists():
        for line in emergency.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                record["durability"] = "emergency"
                records.append(record)
    return records


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_init = sub.add_parser("init")
    p_init.add_argument("run_dir")
    p_init.add_argument("envelope_json")
    p_record = sub.add_parser("record")
    p_record.add_argument("run_dir")
    p_record.add_argument("proposal_json")
    p_finish = sub.add_parser("finalize")
    p_finish.add_argument("run_dir")
    p_finish.add_argument("decision_id")
    p_finish.add_argument("outcome", choices=sorted(TERMINAL_OUTCOMES))
    p_finish.add_argument("result_ref")
    args = parser.parse_args()
    if args.command == "init":
        init_run(args.run_dir, json.loads(Path(args.envelope_json).read_text()))
    elif args.command == "record":
        print(json.dumps(record_decision(
            args.run_dir, json.loads(Path(args.proposal_json).read_text())),
            ensure_ascii=False))
    else:
        print(json.dumps(finalize_decision(
            args.run_dir, args.decision_id, args.outcome, args.result_ref),
            ensure_ascii=False))


if __name__ == "__main__":
    main()
