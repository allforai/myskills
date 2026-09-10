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
