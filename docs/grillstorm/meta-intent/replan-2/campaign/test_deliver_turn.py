"""A scripted turn must never be overtakeable by a later turn."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).parent


def load(monkeypatch, fake):
    spec = importlib.util.spec_from_file_location("dt", HERE / "deliver_turn.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setattr(m, "orca", fake)
    return m


def test_an_open_ask_is_answered_rather_than_bypassed(monkeypatch, tmp_path):
    """The defect: a send-type-status message is invisible to a worker blocked inside ask, so the
    NEXT turn, delivered as the ask's answer, arrived 6.8 s earlier."""
    calls = []

    def fake(args, exe):
        calls.append(args[1])
        if args[1] == "inbox":
            return 0, {"messages": [{"run_id": "run_a", "type": "question", "id": "q1",
                                     "from_handle": "dispatch:ctx_a", "thread_id": "q1"}]}
        return 0, {"message": {"id": "m1"}}

    m = load(monkeypatch, fake)
    body = tmp_path / "b.txt"; body.write_text("turn two")
    assert m.main(["--run", "run_a", "--dispatch", "ctx_a", "--body-file", str(body)]) == 0
    assert "reply" in calls, "an open ask must be answered"
    assert "send" not in calls, "send must not be used while the worker is blocked on an ask"


def test_with_no_open_ask_send_waits_until_the_message_is_consumed(monkeypatch, tmp_path):
    state = {"polls": 0}

    def fake(args, exe):
        if args[1] == "inbox":
            state["polls"] += 1
            delivered = "2026-09-13T00:00:00Z" if state["polls"] > 2 else None
            return 0, {"messages": [{"id": "m1", "run_id": "run_a", "type": "status",
                                     "delivered_at": delivered}]}
        return 0, {"message": {"id": "m1"}}

    m = load(monkeypatch, fake)
    body = tmp_path / "b.txt"; body.write_text("turn two")
    assert m.main(["--run", "run_a", "--dispatch", "ctx_a", "--body-file", str(body),
                   "--wait-consumed-s", "30"]) == 0
    assert state["polls"] > 2, "it must keep polling until Orca reports the message consumed"


def test_a_send_that_is_never_consumed_fails_loudly(monkeypatch, tmp_path):
    """Returning success on an unconsumed send is what lets the caller invert the order."""
    def fake(args, exe):
        if args[1] == "inbox":
            return 0, {"messages": [{"id": "m1", "run_id": "run_a", "type": "status",
                                     "delivered_at": None}]}
        return 0, {"message": {"id": "m1"}}

    m = load(monkeypatch, fake)
    body = tmp_path / "b.txt"; body.write_text("turn two")
    assert m.main(["--run", "run_a", "--dispatch", "ctx_a", "--body-file", str(body),
                   "--wait-consumed-s", "1"]) == 1


def test_an_already_answered_question_is_not_treated_as_open(monkeypatch, tmp_path):
    calls = []

    def fake(args, exe):
        calls.append(args[1])
        if args[1] == "inbox":
            return 0, {"messages": [
                {"run_id": "run_a", "type": "question", "id": "q1",
                 "from_handle": "dispatch:ctx_a", "thread_id": "q1"},
                {"run_id": "run_a", "type": "status", "id": "r1", "thread_id": "q1",
                 "delivered_at": "2026-09-13T00:00:00Z"},
                {"id": "m1", "run_id": "run_a", "type": "status",
                 "delivered_at": "2026-09-13T00:00:01Z"}]}
        return 0, {"message": {"id": "m1"}}

    m = load(monkeypatch, fake)
    body = tmp_path / "b.txt"; body.write_text("turn three")
    assert m.main(["--run", "run_a", "--dispatch", "ctx_a", "--body-file", str(body)]) == 0
    assert "send" in calls, "with no OPEN ask, send is the only path"
