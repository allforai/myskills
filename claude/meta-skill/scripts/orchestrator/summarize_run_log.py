#!/usr/bin/env python3
"""Summarize .allforai/bootstrap/run-log.jsonl into JSON and Markdown reports."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


RUN_LOG_PATH = Path(".allforai/bootstrap/run-log.jsonl")
SUMMARY_JSON = Path(".allforai/bootstrap/run-summary.json")
SUMMARY_MD = Path(".allforai/bootstrap/run-summary.md")


def _load_events(project_root: Path) -> list[dict]:
    path = project_root / RUN_LOG_PATH
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except Exception:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def summarize(project_root: Path) -> dict:
    project_root = project_root.resolve()
    events = _load_events(project_root)
    by_event = Counter(event.get("event", "unknown") for event in events)
    by_status = Counter(event.get("status", "unknown") for event in events if event.get("status"))
    by_node = defaultdict(lambda: Counter())
    blockers = []
    failures = []
    for event in events:
        node_id = event.get("node_id")
        if node_id:
            by_node[node_id][event.get("event", "unknown")] += 1
        if event.get("blocking_reason"):
            blockers.append(event)
        if event.get("event") in {"node_failed", "validation_failed", "preflight_blocked", "run_halted"}:
            failures.append(event)

    return {
        "schema_version": "1.0",
        "event_count": len(events),
        "run_ids": sorted({event.get("run_id") for event in events if event.get("run_id")}),
        "first_ts": events[0].get("ts") if events else None,
        "last_ts": events[-1].get("ts") if events else None,
        "events_by_type": dict(sorted(by_event.items())),
        "events_by_status": dict(sorted(by_status.items())),
        "nodes": {
            node_id: dict(counter)
            for node_id, counter in sorted(by_node.items())
        },
        "blocker_count": len(blockers),
        "failure_count": len(failures),
        "blockers": blockers[-20:],
        "failures": failures[-20:],
    }


def write_reports(project_root: Path, summary: dict) -> tuple[Path, Path]:
    project_root = project_root.resolve()
    json_path = project_root / SUMMARY_JSON
    md_path = project_root / SUMMARY_MD
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Run Summary",
        "",
        f"- events: `{summary['event_count']}`",
        f"- run_ids: `{', '.join(summary['run_ids']) or 'none'}`",
        f"- first_ts: `{summary.get('first_ts')}`",
        f"- last_ts: `{summary.get('last_ts')}`",
        f"- blockers: `{summary['blocker_count']}`",
        f"- failures: `{summary['failure_count']}`",
        "",
        "## Events By Type",
    ]
    for key, value in summary["events_by_type"].items():
        lines.append(f"- `{key}`: {value}")
    if not summary["events_by_type"]:
        lines.append("- none")
    lines.extend(["", "## Recent Failures"])
    for item in summary["failures"]:
        lines.append(f"- `{item.get('event')}` node=`{item.get('node_id')}` reason=`{item.get('blocking_reason') or item.get('message')}`")
    if not summary["failures"]:
        lines.append("- none")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.project_root)
    summary = summarize(root)
    if args.write_report:
        write_reports(root, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
