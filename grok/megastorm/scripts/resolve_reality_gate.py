#!/usr/bin/env python3
"""Import evidence for a pending reality gate and invalidate rejected downstream work."""
import argparse
import hashlib
import json
from pathlib import Path
import time

from run_layers import atomic_write_json


def downstream(task_id, effective_deps):
    reverse = {}
    for tid, deps in effective_deps.items():
        for dep in deps:
            reverse.setdefault(dep, set()).add(tid)
    found, stack = set(), [task_id]
    while stack:
        current = stack.pop()
        for child in reverse.get(current, ()):
            if child not in found:
                found.add(child); stack.append(child)
    return found


def recompute_summary(report, state):
    """Derive counts from post-resolution records and authoritative completion state."""
    completed = set(state.get("completed", []))
    statuses = {r.get("task_id"): r.get("status") for r in report.get("results", [])}
    invalidated = set(state.get("invalidated", []))
    report["completed"] = sorted(completed)
    report["summary"] = {
        "verified": sum(statuses.get(tid) == "done" for tid in completed),
        "reality_gated": sum(statuses.get(tid) == "reality_gated" for tid in completed),
        "escalated": sum(r.get("status") == "escalate"
                         and r.get("task_id") not in invalidated
                         for r in report.get("results", [])),
        "skipped": sum(tid not in invalidated for tid in report.get("skipped", {})),
    }


def resolve(report, state, orchestration, task_id, outcome, evidence):
    gates = {g["task_id"]: g for g in report.get("reality_gates", [])}
    if task_id not in gates:
        raise ValueError(f"task is not a pending reality gate: {task_id}")
    if not evidence or not Path(evidence).is_file():
        raise ValueError("human reality-gate outcome requires an evidence file")
    evidence_path = Path(evidence).resolve()
    resolution = {"task_id": task_id, "outcome": outcome,
                  "evidence": str(evidence_path),
                  "evidence_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
                  "resolved_at": time.time()}
    gate = gates[task_id]
    gate["human_resolution"] = resolution
    state.setdefault("reality_resolutions", {})[task_id] = resolution
    report["reality_gates"] = [g for g in report.get("reality_gates", [])
                               if g.get("task_id") != task_id]
    report.setdefault("resolved_reality_gates", []).append(gate)
    if outcome == "rejected":
        invalid = downstream(task_id, orchestration.get("effective_deps", {})) | {task_id}
        state["completed"] = sorted(set(state.get("completed", [])) - invalid)
        state["invalidated"] = sorted(set(state.get("invalidated", [])) | invalid)
        report["superseded"] = True
        report["superseded_reason"] = f"human rejected reality gate {task_id}"
        report["invalidated_tasks"] = sorted(invalid)
        report["invalidation_provenance"] = resolution
        for result in report.get("results", []):
            if result.get("task_id") in invalid:
                result["status"] = "invalidated"
                result["invalidated_by"] = task_id
    else:
        for result in report.get("results", []):
            if result.get("task_id") == task_id:
                result["status"] = "done"
                result["human_verified"] = resolution
    recompute_summary(report, state)
    return report, state


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report"); ap.add_argument("state"); ap.add_argument("orchestration")
    ap.add_argument("task_id"); ap.add_argument("outcome", choices=["verified", "rejected"])
    ap.add_argument("evidence")
    args = ap.parse_args(argv)
    report = json.loads(Path(args.report).read_text())
    state = json.loads(Path(args.state).read_text())
    orchestration = json.loads(Path(args.orchestration).read_text())
    report, state = resolve(report, state, orchestration, args.task_id,
                            args.outcome, args.evidence)
    atomic_write_json(args.report, report); atomic_write_json(args.state, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
