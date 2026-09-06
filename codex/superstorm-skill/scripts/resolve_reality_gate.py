#!/usr/bin/env python3
"""Import evidence for a pending reality gate and invalidate rejected downstream work."""
import argparse
import json
from pathlib import Path

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


def resolve(report, state, orchestration, task_id, outcome, evidence):
    gates = {g["task_id"]: g for g in report.get("reality_gates", [])}
    if task_id not in gates:
        raise ValueError(f"task is not a pending reality gate: {task_id}")
    if not evidence or not Path(evidence).is_file():
        raise ValueError("human reality-gate outcome requires an evidence file")
    resolution = {"outcome": outcome, "evidence": str(Path(evidence).resolve())}
    gates[task_id]["human_resolution"] = resolution
    if outcome == "rejected":
        invalid = downstream(task_id, orchestration.get("effective_deps", {})) | {task_id}
        state["completed"] = sorted(set(state.get("completed", [])) - invalid)
        report["superseded"] = True
        report["superseded_reason"] = f"human rejected reality gate {task_id}"
        report["invalidated_tasks"] = sorted(invalid)
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
