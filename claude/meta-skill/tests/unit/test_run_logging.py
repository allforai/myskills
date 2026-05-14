import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts/orchestrator"))
from record_run_event import record_event
from summarize_run_log import summarize, write_reports


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
