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
