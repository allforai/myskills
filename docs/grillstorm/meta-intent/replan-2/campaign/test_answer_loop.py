"""The answer loop's decision logic, driven without Orca: which scripted turn answers which question,
that the pending state is snapshotted before every reply, and that it stops on worker_done."""
import json
from pathlib import Path

from answer_loop import next_action


def test_question_is_answered_with_the_next_unused_turn():
    script = {"turns": ["Put Export CSV above the table.", "Also add a UTF-8 BOM."]}
    delivery = {"type": "question", "message_id": "m1", "delivery_id": "d1", "body": "Where should the button go?"}
    act = next_action(delivery, script, used=0)
    assert act == {"kind": "reply", "message_id": "m1", "body": "Put Export CSV above the table.",
                   "ack": "d1", "used": 1, "snapshot_before": True}


def test_a_question_beyond_the_script_is_left_pending_not_invented():
    script = {"turns": ["only one turn"]}
    delivery = {"type": "question", "message_id": "m9", "delivery_id": "d9", "body": "Anything else?"}
    act = next_action(delivery, script, used=1)
    assert act == {"kind": "pending", "message_id": "m9", "ack": None, "used": 1, "snapshot_before": True}


def test_worker_done_stops_the_loop_and_is_acked():
    delivery = {"type": "worker_done", "message_id": "m2", "delivery_id": "d2", "outcome": "succeeded"}
    assert next_action(delivery, {"turns": []}, used=0) == {"kind": "done", "ack": "d2", "used": 0, "snapshot_before": False}


def test_escalation_is_recorded_and_left_to_the_operator():
    delivery = {"type": "escalation", "message_id": "m3", "delivery_id": "d3", "subject": "Blocked: no git"}
    assert next_action(delivery, {"turns": []}, used=0) == {"kind": "escalation", "message_id": "m3", "ack": None, "used": 0, "snapshot_before": True}


def test_a_delivery_is_a_batch_of_messages_acked_once():
    """Orca returns result.messages[] with a single result.deliveryId. Each message gets its own
    decision; the batch is acked once, after the batch is processed."""
    from answer_loop import plan_batch
    result = {"deliveryId": "d7", "messages": [
        {"type": "heartbeat", "id": "m1"},
        {"type": "question", "id": "m2", "body": "Which columns?"},
    ]}
    acts, used, done = plan_batch(result, {"turns": ["id, status, total."]}, used=0)
    assert [a["kind"] for a in acts] == ["ignore", "reply"]
    assert acts[1]["message_id"] == "m2" and acts[1]["body"] == "id, status, total."
    assert used == 1 and done is False


def test_worker_done_inside_a_batch_ends_the_loop():
    from answer_loop import plan_batch
    result = {"deliveryId": "d8", "messages": [{"type": "worker_done", "id": "m3", "outcome": "succeeded"}]}
    acts, used, done = plan_batch(result, {"turns": []}, used=0)
    assert done is True and acts[0]["kind"] == "done"


# The three real questions the T15/claude/missing-product-docs pilot asked, verbatim first lines.
PRODUCT_Q = {"type": "question", "id": "mp", "body": "Bootstrap Phase A — one decision, then the plan delta.\n\n决策 orders-csv-export-route（消费节点：implement-orders-csv-export）", "payload": "{}"}
GATE_CONFIRM = {"type": "question", "id": "mg1", "body": "Bootstrap Step 3.4 — plan confirmation.\n\n项目：retail-sphere\n确认这个节点集和依赖边正确吗？", "payload": '{"options":["confirm","change it"]}'}
GATE_DELTA = {"type": "question", "id": "mg2", "body": "Bootstrap Phase A — 计划 delta，需要你确认后才能执行。\n\n确认这个 delta 吗？", "payload": '{"options":["confirm","reject"]}'}


def test_a_plan_gate_question_takes_an_operational_answer_not_a_scripted_turn():
    """The private file authorises operational answers for gates: they approve no product topic."""
    from answer_loop import next_action
    for q in (GATE_CONFIRM, GATE_DELTA):
        act = next_action(q, {"turns": ["A PRODUCT ANSWER THAT MUST NOT BE SPENT HERE"]}, used=0)
        assert act["kind"] == "reply" and act["body"] == "confirm", q["id"]
        assert act["used"] == 0, "a gate answer must not consume a scripted product turn"
        assert act["operational"] is True


def test_a_product_question_still_consumes_the_next_scripted_turn():
    from answer_loop import next_action
    act = next_action(PRODUCT_Q, {"turns": ["Only the signed-in merchant's orders."]}, used=0)
    assert act["kind"] == "reply" and act["used"] == 1
    assert act["body"] == "Only the signed-in merchant's orders."
    assert act.get("operational") is not True


def test_a_confirm_option_without_a_plan_marker_is_not_auto_confirmed():
    """Fail toward the coordinator: an unfamiliar confirm-shaped question is a product question."""
    from answer_loop import next_action
    q = {"type": "question", "id": "mx", "body": "Should we charge merchants a subscription fee?",
         "payload": '{"options":["confirm","reject"]}'}
    act = next_action(q, {"turns": []}, used=0)
    assert act["kind"] == "pending", act


def test_replies_accumulate_across_resumptions_instead_of_overwriting(tmp_path):
    """A cell is often driven in several invocations (a gate answered by hand between them). Each run
    must append to the cell's record; overwriting destroys the question-and-answer evidence the
    evaluator needs."""
    from answer_loop import merge_replies
    out = tmp_path / "replies.json"
    merge_replies(out, {"used_turns": 1, "replies": [{"question": "Which columns?", "answer": "id, status, total",
                                                      "kind": "scripted-user-turn"}]})
    merge_replies(out, {"used_turns": 0, "replies": [{"event": "worker_done", "outcome": "succeeded"}]})
    import json
    d = json.loads(out.read_text())
    assert [r.get("question") or r.get("event") for r in d["replies"]] == ["Which columns?", "worker_done"]
    assert d["used_turns"] == 1, "turns consumed across the whole cell, not just the last invocation"
    assert len(d["invocations"]) == 2


def test_every_orca_check_is_scoped_to_this_cells_run():
    """Orca returns the RUN's oldest FIFO delivery, not a dispatch's. Two cells sharing a Run let one
    coordinator loop consume the other's question — which is how a turn once reached the wrong actor.
    Every check must therefore name its own run."""
    from answer_loop import check_argv
    argv = check_argv(run="run_abc", types="worker_done,escalation,question", timeout_ms=600000, ack=None)
    assert argv[:2] == ["orchestration", "check"]
    assert "--run" in argv and argv[argv.index("--run") + 1] == "run_abc"
    acked = check_argv(run="run_abc", types="question", timeout_ms=1000, ack="d5")
    assert acked[acked.index("--ack") + 1] == "d5"
    assert acked[acked.index("--run") + 1] == "run_abc", "an acking check stays scoped too"


def test_a_loop_without_a_run_refuses_to_start():
    """Failing closed: an unscoped loop would silently eat another cell's deliveries."""
    from answer_loop import check_argv
    try:
        check_argv(run="", types="question", timeout_ms=1000, ack=None)
    except ValueError as exc:
        assert "run" in str(exc).lower()
    else:
        raise AssertionError("an empty run must be refused, not defaulted")


def test_spent_turns_survive_a_resumption(tmp_path):
    """A cell is driven in several invocations. If `used` resets, the loop re-delivers turn 1 to a
    later, different question — which silently answers it with words meant for another."""
    from answer_loop import merge_replies, spent_turns
    out = tmp_path / "replies.json"
    assert spent_turns(out) == 0
    merge_replies(out, {"used_turns": 1, "replies": [{"question": "Which columns?", "answer": "id, status, total",
                                                      "kind": "scripted-user-turn"}]})
    assert spent_turns(out) == 1, "the next invocation must start from the turns already spent"


def test_the_cells_own_worker_terminal_is_not_a_foreign_delivery():
    """from_handle may be the cell's own terminal rather than dispatch:<id>; only another cell is foreign."""
    from answer_loop import is_foreign
    own = {"dispatch": "ctx_me", "terminals": ["term_mine"]}
    assert is_foreign({"from_handle": "dispatch:ctx_me"}, own) is False
    assert is_foreign({"from_handle": "term_mine"}, own) is False
    assert is_foreign({"from_handle": "run:run_x"}, own) is False       # coordinator-sourced
    assert is_foreign({"from_handle": "dispatch:ctx_other"}, own) is True


def test_resumed_invocations_do_not_double_count_spent_turns(tmp_path):
    """Each invocation's `used` already starts from spent_turns, so summing them compounds: a cell
    driven three times reported 4 spent turns for a single scripted answer, and the next invocation
    would then skip real turns. The cumulative count is the LAST invocation's, not the sum."""
    from answer_loop import merge_replies, spent_turns
    out = tmp_path / "replies.json"
    merge_replies(out, {"used_turns": 1, "replies": [{"question": "q1", "answer": "a1", "kind": "scripted-user-turn"}]})
    assert spent_turns(out) == 1
    merge_replies(out, {"used_turns": 1, "replies": [{"event": "pending"}]})      # a gate answered by hand; no turn spent
    assert spent_turns(out) == 1, "a resumption that spends no turn must not advance the count"
    merge_replies(out, {"used_turns": 2, "replies": [{"question": "q2", "answer": "a2", "kind": "scripted-user-turn"}]})
    assert spent_turns(out) == 2, "the count is cumulative, not additive"


def drive(monkeypatch, tmp_path, statuses, message_after=None):
    """Run the loop against a fake Orca and return what it recorded."""
    import answer_loop
    state = {"checks": 0}

    def fake_orca(args, exe):
        if args[1] == "worker-show":
            return 0, {"observation": statuses}
        state["checks"] += 1
        if message_after and state["checks"] >= message_after:
            return 0, {"messages": [{"type": "worker_done", "delivery_id": "d1"}]}
        return 0, {"messages": []}

    monkeypatch.setattr(answer_loop, "orca", fake_orca)
    out = tmp_path / "capture"; out.mkdir()
    (tmp_path / "dispatch.json").write_text(json.dumps({"result": {"effects": []}}))
    script = tmp_path / "turns.json"; script.write_text(json.dumps({"turns": ["x"]}))
    answer_loop.main(["--dispatch", "ctx_a", "--run", "run_a", "--script", str(script),
                      "--out", str(out), "--max-empty", "2"])
    return json.loads((out / "replies.json").read_text()), state


def test_a_live_worker_keeps_the_loop_waiting_instead_of_stalling(monkeypatch, tmp_path):
    """Two concurrent loops exited 28 seconds before their actors asked anything, on a count alone.

    The bigger fixture simply took longer to reach its first question, so an empty-wait count is not
    evidence of a stall.
    """
    recorded, state = drive(monkeypatch, tmp_path, {"status": "live"}, message_after=6)
    assert not any(r.get("event") == "stalled" for r in recorded["replies"]), (
        "a live worker must never be reported as stalled")
    assert state["checks"] >= 6, "the loop must keep waiting past max-empty while the worker lives"


def test_a_dead_worker_still_stalls_with_its_liveness_named(monkeypatch, tmp_path):
    recorded, _ = drive(monkeypatch, tmp_path, {"status": "exited"})
    stalled = [r for r in recorded["replies"] if r.get("event") == "stalled"]
    assert stalled and stalled[-1]["worker_liveness"] == "not live"


def test_unverifiable_liveness_is_never_treated_as_death(monkeypatch, tmp_path):
    """Absence is not proof of exit; it must be reported as unverifiable."""
    recorded, _ = drive(monkeypatch, tmp_path, {})
    stalled = [r for r in recorded["replies"] if r.get("event") == "stalled"]
    assert stalled and stalled[-1]["worker_liveness"] == "unverifiable"


def test_a_replayed_question_never_spends_a_second_scripted_turn(monkeypatch, tmp_path):
    """The real harm: a hand-answered question replayed, and the loop spent turn 2 on it.

    That is how a UTF-8 BOM decision reached an actor before it had asked for anything.
    """
    import answer_loop
    out = tmp_path / "capture"; out.mkdir()
    # turn 1 was delivered by hand, so its question id is recorded but the delivery was never acked
    (out / "replies.json").write_text(json.dumps({
        "used_turns": 1, "invocations": [{"used_turns": 1, "replies": 1}],
        "replies": [{"question_id": "mq1", "answer": "turn one", "kind": "scripted-user-turn"}]}))
    (tmp_path / "dispatch.json").write_text(json.dumps({"result": {"effects": []}}))
    script = tmp_path / "turns.json"
    script.write_text(json.dumps({"turns": ["turn one", "TURN TWO MUST NOT BE SPENT HERE"]}))
    sent = []

    def fake_orca(args, exe):
        if args[1] == "worker-show":
            return 0, {"observation": {"status": "exited"}}
        if args[1] == "reply":
            sent.append(args[args.index("--body") + 1])
            return 0, {}
        # the same question replays, carrying a delivery id so it can be acked away
        return 0, {"messages": [{"type": "question", "id": "mq1", "body": "the same question again"}],
                   "delivery_id": "d1"}

    monkeypatch.setattr(answer_loop, "orca", fake_orca)
    answer_loop.main(["--dispatch", "ctx_a", "--run", "run_a", "--script", str(script),
                      "--out", str(out), "--max-empty", "2"])
    assert "TURN TWO MUST NOT BE SPENT HERE" not in sent, (
        "a replayed question must not consume the next scripted turn")
    recorded = json.loads((out / "replies.json").read_text())
    assert recorded["used_turns"] == 1, "the turn ledger must not advance on a replay"
    assert any(r.get("event") == "replay-skipped" for r in recorded["replies"])


def test_a_replay_that_never_retires_stops_rather_than_spinning(monkeypatch, tmp_path):
    """Acking should retire a batch; if it keeps coming back, stop and say so."""
    import answer_loop
    out = tmp_path / "capture"; out.mkdir()
    (out / "replies.json").write_text(json.dumps({
        "used_turns": 1, "invocations": [], "replies": [{"question_id": "mq1", "answer": "t1"}]}))
    (tmp_path / "dispatch.json").write_text(json.dumps({"result": {"effects": []}}))
    script = tmp_path / "turns.json"; script.write_text(json.dumps({"turns": ["t1", "t2"]}))

    def fake_orca(args, exe):
        if args[1] == "worker-show":
            return 0, {"observation": {"status": "live"}}
        return 0, {"messages": [{"type": "question", "id": "mq1", "body": "again"}],
                   "delivery_id": "d1"}

    monkeypatch.setattr(answer_loop, "orca", fake_orca)
    answer_loop.main(["--dispatch", "ctx_a", "--run", "run_a", "--script", str(script),
                      "--out", str(out), "--max-empty", "2", "--max-replay-skips", "3"])
    recorded = json.loads((out / "replies.json").read_text())
    assert recorded["used_turns"] == 1
    assert sum(1 for r in recorded["replies"] if r.get("event") == "replay-skipped") <= 4


def test_a_replay_with_no_delivery_id_stops_instead_of_spinning(monkeypatch, tmp_path):
    import answer_loop
    out = tmp_path / "capture"; out.mkdir()
    (out / "replies.json").write_text(json.dumps({
        "used_turns": 1, "invocations": [], "replies": [{"question_id": "mq1", "answer": "t1"}]}))
    (tmp_path / "dispatch.json").write_text(json.dumps({"result": {"effects": []}}))
    script = tmp_path / "turns.json"; script.write_text(json.dumps({"turns": ["t1", "t2"]}))

    def fake_orca(args, exe):
        if args[1] == "worker-show":
            return 0, {"observation": {"status": "live"}}
        return 0, {"messages": [{"type": "question", "id": "mq1", "body": "again"}]}

    monkeypatch.setattr(answer_loop, "orca", fake_orca)
    answer_loop.main(["--dispatch", "ctx_a", "--run", "run_a", "--script", str(script),
                      "--out", str(out), "--max-empty", "2"])
    recorded = json.loads((out / "replies.json").read_text())
    assert any(r.get("event") == "replay-skipped" for r in recorded["replies"])
    assert recorded["used_turns"] == 1


def test_a_fresh_question_alongside_a_replay_is_still_answered(monkeypatch, tmp_path):
    import answer_loop
    out = tmp_path / "capture"; out.mkdir()
    (out / "replies.json").write_text(json.dumps({
        "used_turns": 1, "invocations": [], "replies": [{"question_id": "mq1", "answer": "t1"}]}))
    (tmp_path / "dispatch.json").write_text(json.dumps({"result": {"effects": []}}))
    script = tmp_path / "turns.json"; script.write_text(json.dumps({"turns": ["t1", "t2"]}))
    sent = []

    def fake_orca(args, exe):
        if args[1] == "worker-show":
            return 0, {"observation": {"status": "exited"}}
        if args[1] == "reply":
            sent.append(args[args.index("--body") + 1]); return 0, {}
        return 0, {"messages": [{"type": "question", "id": "mq1", "body": "replay"},
                                {"type": "question", "id": "mq2", "body": "genuinely new"}],
                   "delivery_id": "d1"}

    monkeypatch.setattr(answer_loop, "orca", fake_orca)
    answer_loop.main(["--dispatch", "ctx_a", "--run", "run_a", "--script", str(script),
                      "--out", str(out), "--max-empty", "2"])
    assert sent == ["t2"], f"only the new question should be answered, got {sent}"


def test_a_delivered_turn_is_persisted_before_the_loop_can_be_killed(monkeypatch, tmp_path):
    """Writing only at exit lost a delivered scripted turn when the loop was stopped mid-run."""
    import answer_loop
    out = tmp_path / "capture"; out.mkdir()
    (tmp_path / "dispatch.json").write_text(json.dumps({"result": {"effects": []}}))
    script = tmp_path / "turns.json"; script.write_text(json.dumps({"turns": ["turn one", "turn two"]}))
    state = {"n": 0}

    class Stop(Exception):
        pass

    def fake_orca(args, exe):
        if args[1] == "worker-show":
            return 0, {"observation": {"status": "live"}}
        if args[1] == "reply":
            return 0, {}
        state["n"] += 1
        if state["n"] == 1:
            return 0, {"messages": [{"type": "question", "id": "q1", "body": "first"}],
                       "deliveryId": "d1"}
        raise Stop  # stand in for the loop being killed right after the first reply

    monkeypatch.setattr(answer_loop, "orca", fake_orca)
    try:
        answer_loop.main(["--dispatch", "ctx_a", "--run", "run_a", "--script", str(script),
                          "--out", str(out), "--max-empty", "2"])
    except Stop:
        pass
    recorded = json.loads((out / "replies.json").read_text())
    assert recorded["used_turns"] == 1, "the delivered turn must already be in the ledger"
    assert recorded["replies"][0]["answer"] == "turn one"
    assert recorded["replies"][0]["question_id"] == "q1"
