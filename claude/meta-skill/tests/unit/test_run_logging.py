import json
import os
import sys

from ..module_isolation import load

_record_run_event, _summarize_run_log = load("record_run_event", "summarize_run_log")
record_event = _record_run_event.record_event
summarize, write_reports = _summarize_run_log.summarize, _summarize_run_log.write_reports


def test_record_run_event_appends_jsonl(tmp_path):
    payload = record_event(
        tmp_path,
        {
            "event": "node_started",
            "node_id": "build",
            "capability": "compile-verify",
            "expected_artifacts": [".allforai/build.json"],
        },
    )

    path = tmp_path / ".allforai/bootstrap/run-log.jsonl"
    lines = path.read_text().splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["event"] == "node_started"
    assert event["run_id"] == payload["run_id"]
    assert (tmp_path / ".allforai/bootstrap/run-id").exists()


def test_summarize_run_log_writes_reports(tmp_path):
    record_event(tmp_path, {"event": "run_started", "status": "started"})
    record_event(tmp_path, {"event": "node_failed", "node_id": "qa", "blocking_reason": "missing_screenshot"})

    summary = summarize(tmp_path)
    json_path, md_path = write_reports(tmp_path, summary)

    assert summary["event_count"] == 2
    assert summary["failure_count"] == 1
    assert json_path.exists()
    assert md_path.exists()
    assert "missing_screenshot" in md_path.read_text()


def test_summarize_run_log_accepts_legacy_node_key(tmp_path):
    log_path = tmp_path / ".allforai/bootstrap/run-log.jsonl"
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        json.dumps({
            "event": "node_completed",
            "node": "legacy-node",
            "status": "completed",
            "run_id": "r1",
            "ts": "2026-01-01T00:00:00+00:00",
        })
        + "\n"
    )

    summary = summarize(tmp_path)

    assert summary["completed_nodes"] == ["legacy-node"]
    assert summary["nodes"]["legacy-node"]["node_completed"] == 1
