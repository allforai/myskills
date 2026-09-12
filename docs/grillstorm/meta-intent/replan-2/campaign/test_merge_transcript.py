"""A union record must never claim completeness it cannot show."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).parent


def load():
    spec = importlib.util.spec_from_file_location("mt", HERE / "merge_transcript.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def write_window(root, name, messages, cursor="c1"):
    d = root / name
    d.mkdir(parents=True)
    (d / "capture.json").write_text(json.dumps({"dispatchId": "ctx_x", "cursor": cursor}))
    (d / "page-0001.stdout.json").write_text(json.dumps(
        {"result": {"transcript": {"messages": messages, "limited": True,
                                   "returnedMessageCount": len(messages)}}}))
    return d


def msg(mid, ts, text="x"):
    return {"id": mid, "role": "assistant", "timestamp": ts,
            "blocks": [{"type": "text", "text": text}]}


def test_overlapping_windows_dedupe_and_order(tmp_path):
    m = load()
    write_window(tmp_path, "win-0001", [msg("a", 1000), msg("b", 2000)])
    write_window(tmp_path, "win-0002", [msg("b", 2000), msg("c", 3000)])
    doc = m.build(tmp_path, started_at=1000)
    assert [x["id"] for x in doc["dialogue"]] == ["a", "b", "c"]
    prov = {p["id"]: p["seen_in"] for p in doc["provenance"]}
    assert prov["b"] == ["win-0001", "win-0002"], "a corroborated message records both windows"
    assert prov["a"] == ["win-0001"]


def test_full_dialogue_is_proven_only_when_the_start_is_covered(tmp_path):
    m = load()
    write_window(tmp_path, "win-0001", [msg("a", 5000), msg("b", 6000)])
    late = m.build(tmp_path, started_at=1000)
    assert late["coverage"]["covers_dispatch_start"] is False
    assert late["coverage"]["front_gap_ms"] == 4000
    assert late["coverage"]["full_dialogue_proven"] is False, "a front gap can never be a proven record"
    covered = m.build(tmp_path, started_at=5000)
    assert covered["coverage"]["covers_dispatch_start"] is True
    assert covered["coverage"]["full_dialogue_proven"] is True


def test_an_interior_silence_defeats_completeness(tmp_path):
    m = load()
    write_window(tmp_path, "win-0001", [msg("a", 1000), msg("b", 500000)])
    doc = m.build(tmp_path, started_at=1000)
    assert doc["coverage"]["internal_gaps"], "a 499s silence must be reported"
    assert doc["coverage"]["full_dialogue_proven"] is False


def test_without_a_start_time_completeness_is_never_claimed(tmp_path):
    m = load()
    write_window(tmp_path, "win-0001", [msg("a", 1000), msg("b", 2000)])
    doc = m.build(tmp_path, started_at=None)
    assert doc["coverage"]["full_dialogue_proven"] is False
    assert doc["coverage"]["messages"] == 2


def test_unreadable_and_empty_pages_are_skipped_not_fatal(tmp_path):
    m = load()
    write_window(tmp_path, "win-0001", [msg("a", 1000)])
    bad = tmp_path / "win-0002"
    bad.mkdir()
    (bad / "capture.json").write_text("{}")
    (bad / "page-0001.stdout.json").write_text("not json{{")
    doc = m.build(tmp_path, started_at=1000)
    assert [x["id"] for x in doc["dialogue"]] == ["a"]


def test_messages_without_an_id_are_dropped_rather_than_duplicated(tmp_path):
    m = load()
    write_window(tmp_path, "win-0001", [msg("a", 1000), {"role": "tool", "timestamp": 1500}])
    doc = m.build(tmp_path, started_at=1000)
    assert doc["coverage"]["messages"] == 1


def test_exit_code_is_nonzero_when_the_record_is_incomplete(tmp_path):
    m = load()
    write_window(tmp_path, "win-0001", [msg("a", 5000)])
    out = tmp_path / "raw.json"
    assert m.main([str(tmp_path), "--out", str(out), "--started-at", "1000"]) == 1
    assert m.main([str(tmp_path), "--out", str(out), "--started-at", "5000"]) == 0


def test_launcher_starts_the_tailer_before_the_actor_can_finish():
    """The regression that cost two cells: capture must begin at dispatch, not at the end."""
    launch = (HERE / "launch_cell.sh").read_text()
    assert "tail_transcript.sh" in launch, "launch must start the transcript tailer"
    assert launch.index("tail_transcript.sh") > launch.index("worker-start"), (
        "the tailer needs the dispatch id, so it starts just after worker-start")
    assert "coordinator-identity.worker-show.json" in launch, (
        "launch must record a coordinator-side identity the actor cannot author")


def test_the_tailer_takes_a_final_window_after_the_worker_stops():
    tail = (HERE / "tail_transcript.sh").read_text()
    assert "worker no longer live" in tail
    # A poll interval that exceeds the retained window stops producing overlap.
    assert "200s" in tail or "do not raise the interval" in tail.lower()


def test_launcher_writes_the_structured_identity_record_admission_reads():
    """worker-show alone is not enough: admission reads capture/coordinator-identity.json."""
    launch = (HERE / "launch_cell.sh").read_text()
    assert "write_identity.py" in launch
    assert launch.index("write_identity.py") > launch.index("worker-start")


def test_identity_record_reports_missing_fields_rather_than_writing_a_hollow_one(tmp_path):
    spec = importlib.util.spec_from_file_location("wi", HERE / "write_identity.py")
    wi = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wi)
    (tmp_path / "d.json").write_text(json.dumps({"result": {}}))
    (tmp_path / "r.json").write_text(json.dumps({"result": {}}))
    (tmp_path / "w.json").write_text(json.dumps({"result": {}}))
    rc = wi.main([str(tmp_path), str(tmp_path / "d.json"), str(tmp_path / "r.json"),
                  str(tmp_path / "w.json")])
    assert rc == 1, "an incomplete record must be reported, not silently accepted"
    written = json.loads((tmp_path / "capture" / "coordinator-identity.json").read_text())
    assert written["dispatch_id"] is None


def test_identity_record_is_complete_when_orca_supplies_both_sides(tmp_path):
    spec = importlib.util.spec_from_file_location("wi", HERE / "write_identity.py")
    wi = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wi)
    (tmp_path / "d.json").write_text(json.dumps({"result": {
        "dispatchId": "ctx_a", "runId": "run_a", "taskId": "task_a",
        "prompt": {"processIncarnation": "inc_a", "provider": "codex"},
        "launch": {"effective": {"agent": "codex"}},
        "effects": [{"kind": "terminal", "id": "term_a"}]}}))
    (tmp_path / "r.json").write_text(json.dumps({"result": {"run": {"id": "run_a"}}}))
    (tmp_path / "w.json").write_text(json.dumps({"result": {
        "terminal": {"incarnationId": "inc_a", "agentIdentity": "codex"}}}))
    rc = wi.main([str(tmp_path), str(tmp_path / "d.json"), str(tmp_path / "r.json"),
                  str(tmp_path / "w.json")])
    assert rc == 0
    written = json.loads((tmp_path / "capture" / "coordinator-identity.json").read_text())
    assert written["dispatch_id"] == "ctx_a"
    assert written["orca_side"]["dispatch_prompt_processIncarnation"] == "inc_a"
