"""A union record must never claim completeness it cannot show."""
import importlib.util
import os
import json
from pathlib import Path

HERE = Path(__file__).parent


def load():
    spec = importlib.util.spec_from_file_location("mt", HERE / "merge_transcript.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def write_window(root, name, messages, cursor="c1"):
    """One bounded window. Fewer than 50 messages means Orca was not saturated at that instant."""
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


def test_an_unsaturated_first_window_proves_the_record_starts_at_message_one(tmp_path):
    """A window below the cap held the whole history at that instant, so nothing predates it."""
    m = load()
    write_window(tmp_path, "win-0001", [msg("a", 5000), msg("b", 6000)])
    doc = m.build(tmp_path, started_at=1000)
    assert doc["coverage"]["starts_at_first_message"] is True
    assert doc["coverage"]["full_dialogue_proven"] is True
    # Launch latency is reported but must never decide completeness.
    assert doc["coverage"]["launch_to_first_message_ms"] == 4000


def test_a_saturated_first_window_can_never_prove_completeness(tmp_path):
    m = load()
    write_window(tmp_path, "win-0001", [msg(f"m{i}", 1000 + i) for i in range(50)])
    doc = m.build(tmp_path, started_at=1000)
    assert doc["coverage"]["window_reads"][0]["saturated"] is True
    assert doc["coverage"]["starts_at_first_message"] is False
    assert doc["coverage"]["full_dialogue_proven"] is False, (
        "a window at the retention cap may have dropped older history")


def test_saturated_windows_that_do_not_overlap_are_reported_as_a_broken_chain(tmp_path):
    m = load()
    write_window(tmp_path, "win-0001", [msg(f"a{i}", 1000 + i) for i in range(50)])
    write_window(tmp_path, "win-0002", [msg(f"b{i}", 90000 + i) for i in range(50)])
    doc = m.build(tmp_path, started_at=1000)
    assert doc["coverage"]["chain_breaks"] == ["win-0002"]
    assert doc["coverage"]["full_dialogue_proven"] is False


def test_an_unsaturated_later_window_never_counts_as_a_chain_break(tmp_path):
    m = load()
    write_window(tmp_path, "win-0001", [msg("a", 1000)])
    write_window(tmp_path, "win-0002", [msg("z", 90000)])
    doc = m.build(tmp_path, started_at=1000)
    assert doc["coverage"]["chain_breaks"] == []


def test_a_silence_one_window_brackets_is_reported_but_does_not_defeat_completeness(tmp_path):
    """An actor waiting on a coordinator reply goes quiet for minutes; that is not a hole.

    One window holding both bracketing messages, with nothing between, proves nothing was between.
    """
    m = load()
    write_window(tmp_path, "win-0001", [msg("a", 1000), msg("b", 500000)])
    doc = m.build(tmp_path, started_at=1000)
    gap = doc["coverage"]["internal_gaps"]
    assert gap and gap[0]["silence_ms"] == 499000, "the silence must still be reported"
    assert gap[0]["observed_within"] == ["win-0001"]
    assert gap[0]["explained"] is True
    assert doc["coverage"]["unexplained_gaps"] == []
    assert doc["coverage"]["full_dialogue_proven"] is True


def test_a_silence_no_single_window_brackets_is_unexplained_and_defeats_completeness(tmp_path):
    m = load()
    write_window(tmp_path, "win-0001", [msg("a", 1000)])
    write_window(tmp_path, "win-0002", [msg("b", 500000)])
    doc = m.build(tmp_path, started_at=1000)
    gap = doc["coverage"]["internal_gaps"]
    assert gap and gap[0]["observed_within"] == []
    assert gap[0]["explained"] is False
    assert doc["coverage"]["unexplained_gaps"] == gap
    assert doc["coverage"]["full_dialogue_proven"] is False, (
        "no window saw across this silence, so messages may be missing from it")


def test_without_a_start_time_completeness_is_never_claimed(tmp_path):
    m = load()
    write_window(tmp_path, "win-0001", [msg("a", 1000), msg("b", 2000)])
    doc = m.build(tmp_path, started_at=None)
    assert doc["coverage"]["messages"] == 2
    assert "launch_to_first_message_ms" not in doc["coverage"]


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
    write_window(tmp_path, "win-0001", [msg(f"m{i}", 1000 + i) for i in range(50)])
    out = tmp_path / "raw.json"
    assert m.main([str(tmp_path), "--out", str(out), "--started-at", "1000"]) == 1, (
        "a saturated first window is incomplete")
    write_window(tmp_path, "win-0000", [msg("m0", 999), msg("m1", 1000)])
    assert m.main([str(tmp_path), "--out", str(out), "--started-at", "999"]) == 0


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


def test_a_union_built_while_the_tailer_runs_withholds_proof(tmp_path):
    """One record named 29 windows while 33 later existed, because it merged mid-capture."""
    m = load()
    write_window(tmp_path, "win-0001", [msg("a", 1000), msg("b", 2000)])
    (tmp_path / "tail.pid").write_text(str(os.getpid()))
    doc = m.build(tmp_path, started_at=1000)
    assert doc["coverage"]["tailer_running_at_merge"] is True
    assert doc["coverage"]["full_dialogue_proven"] is False
    assert doc["coverage"]["proof_withheld_because"]


def test_a_union_built_after_the_tailer_exits_can_prove_completeness(tmp_path):
    m = load()
    write_window(tmp_path, "win-0001", [msg("a", 1000), msg("b", 2000)])
    (tmp_path / "tail.pid").write_text("999999999")  # a pid that cannot be alive
    doc = m.build(tmp_path, started_at=1000)
    assert doc["coverage"]["tailer_running_at_merge"] is False
    assert doc["coverage"]["full_dialogue_proven"] is True


def test_the_merge_records_how_many_capture_dirs_it_saw(tmp_path):
    m = load()
    write_window(tmp_path, "win-0001", [msg("a", 1000)])
    write_window(tmp_path, "win-0002", [msg("a", 1000), msg("b", 2000)])
    doc = m.build(tmp_path, started_at=1000)
    assert doc["coverage"]["capture_dirs_seen"] == 2
