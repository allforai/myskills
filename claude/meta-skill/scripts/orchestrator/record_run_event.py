#!/usr/bin/env python3
"""Append structured workflow run events to .allforai/bootstrap/run-log.jsonl."""

from __future__ import annotations

import argparse
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path


RUN_ID_PATH = Path(".allforai/bootstrap/run-id")
RUN_LOG_PATH = Path(".allforai/bootstrap/run-log.jsonl")
WORKFLOW_PATH = Path(".allforai/bootstrap/workflow.json")
# Diagnoses one invocation of the run may record before it stops as UNRESOLVED. The count
# starts again with each `run_started`: what an earlier invocation diagnosed has been seen
# by the person who started this one (ADR 0017).
DIAGNOSIS_CAP = 5


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_run_id(project_root: Path) -> str:
    path = project_root / RUN_ID_PATH
    if path.exists():
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(run_id + "\n", encoding="utf-8")
    return run_id


def _parse_json_value(value: str | None):
    if value is None or value == "":
        return None
    try:
        return json.loads(value)
    except Exception:
        return value


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _diagnosis_history(project_root: Path) -> list:
    try:
        workflow = json.loads((project_root / WORKFLOW_PATH).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    history = workflow.get("diagnosis_history") if isinstance(workflow, dict) else None
    return history if isinstance(history, list) else []


def _is_diagnosis(entry) -> bool:
    return isinstance(entry, dict) and entry.get("kind") != "failure" and bool(entry.get("root_cause"))


def diagnosis_budget(project_root: Path) -> dict:
    """How many diagnoses this invocation has recorded, against its cap.

    The invocation's `run_started` event recorded how long `diagnosis_history` was when it
    began; everything after that position belongs to this invocation. A log with no such
    record counts the whole history, which is the bound that applied before invocations.

    Only a diagnosis counts: an entry that names a root cause. The engine also appends a
    record of each hard failure before anyone has diagnosed it, and one failure must not
    spend the allowance twice.
    """
    project_root = project_root.resolve()
    history = _diagnosis_history(project_root)
    start = 0
    try:
        lines = (project_root / RUN_LOG_PATH).read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("event") == "run_started":
            at_start = event.get("diagnosis_entries_at_start")
            start = at_start if isinstance(at_start, int) and 0 <= at_start <= len(history) else 0
    recorded = history[start:]
    current = [entry for entry in recorded if _is_diagnosis(entry)]
    return {
        "cap": DIAGNOSIS_CAP,
        "entries_total": len(history),
        "entries_this_invocation": len(current),
        "failure_records_this_invocation": len(recorded) - len(current),
        "capped": len(current) >= DIAGNOSIS_CAP,
        "this_invocation": [
            {"failed_node": entry.get("failed_node"), "root_cause": entry.get("root_cause")}
            for entry in current
        ],
    }


def record_event(project_root: Path, event: dict) -> dict:
    project_root = project_root.resolve()
    event = {key: value for key, value in event.items() if value not in (None, [], {})}
    payload = {
        "ts": _now(),
        "run_id": _read_run_id(project_root),
        **event,
    }
    log_path = project_root / RUN_LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--event")
    parser.add_argument("--diagnosis-budget", action="store_true",
                        help="print this invocation's diagnosis count against its cap; records nothing")
    parser.add_argument("--node-id")
    parser.add_argument("--capability")
    parser.add_argument("--status")
    parser.add_argument("--message")
    parser.add_argument("--command")
    parser.add_argument("--duration-ms", type=int)
    parser.add_argument("--expected-artifacts")
    parser.add_argument("--created-artifacts")
    parser.add_argument("--blocking-reason")
    parser.add_argument("--repair-route")
    parser.add_argument("--skill-refs")
    parser.add_argument("--metadata-json")
    args = parser.parse_args(argv)
    if args.diagnosis_budget:
        print(json.dumps(diagnosis_budget(Path(args.project_root)), ensure_ascii=False, indent=2))
        return 0
    if not args.event:
        parser.error("--event is required")
    at_start = None
    if args.event == "run_started":
        at_start = len(_diagnosis_history(Path(args.project_root).resolve()))

    payload = record_event(
        Path(args.project_root),
        {
            "event": args.event,
            "node_id": args.node_id,
            "capability": args.capability,
            "status": args.status,
            "message": args.message,
            "command": args.command,
            "duration_ms": args.duration_ms,
            "expected_artifacts": _split_csv(args.expected_artifacts),
            "created_artifacts": _split_csv(args.created_artifacts),
            "blocking_reason": args.blocking_reason,
            "repair_route": args.repair_route,
            "skill_refs": _split_csv(args.skill_refs),
            "metadata": _parse_json_value(args.metadata_json),
            "diagnosis_entries_at_start": at_start,
        },
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
