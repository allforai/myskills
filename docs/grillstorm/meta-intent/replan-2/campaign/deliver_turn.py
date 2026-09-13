"""Deliver one scripted user turn so the actor cannot receive a LATER turn first.

A supervised worker blocked inside `orca orchestration ask` does not see a `send --type status`
message: it lands with delivered_at null and stays invisible until the worker polls `check`. Sending
turn 2 that way while the driver answered the worker's open ask with turn 3 delivered turn 3 SIX
POINT EIGHT SECONDS BEFORE turn 2, so "record this choice, then pause" arrived after "update the
plan" and the scenario's unwired-decision contrast could not exist. The cell was judged unverified for
exactly that.

Worse, the `--type status` choice was made to fix a cosmetic problem: sending a user turn as
`--type question` made it look like a pending actor question in the coordinator's inbox. A bookkeeping
annoyance was traded for a real ordering defect.

So a turn is delivered by ANSWERING the ask the worker is blocked on, and only falls back to `send`
when no ask is open — and then it refuses to return until Orca reports the message consumed, so the
caller cannot race ahead with the next turn.

Usage: deliver_turn.py --run <run> --dispatch <ctx> --body-file <f> [--orca orca] [--wait-consumed-s 120]
"""
import argparse
import json
import subprocess
import time
from pathlib import Path


def orca(args, exe):
    out = subprocess.run([exe, *args, "--json"], capture_output=True, text=True, timeout=300)
    if not out.stdout.strip().startswith("{"):
        return 1, {"raw": out.stdout[:300]}
    payload = json.loads(out.stdout)
    return (0 if payload.get("ok") else 1), (payload.get("result") or payload.get("error") or {})


def open_ask(run, dispatch, exe):
    """The id of a question this dispatch is currently blocked on, if any."""
    code, result = orca(["orchestration", "inbox", "--limit", "60"], exe)
    if code:
        return None
    messages = result.get("messages") or result.get("rows") or []
    mine = [m for m in messages if m.get("run_id") == run and m.get("type") == "question"
            and (m.get("from_handle") or "").endswith(dispatch)]
    answered = {m.get("thread_id") for m in messages
                if m.get("run_id") == run and m.get("type") == "status"}
    pending = [m for m in mine if m.get("thread_id") not in answered]
    return pending[-1]["id"] if pending else None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True); ap.add_argument("--dispatch", required=True)
    ap.add_argument("--body-file", required=True); ap.add_argument("--orca", default="orca")
    ap.add_argument("--wait-consumed-s", type=int, default=120)
    a = ap.parse_args(argv)
    body = Path(a.body_file).read_text()
    orca(["orchestration", "run-use", "--id", a.run], a.orca)
    ask = open_ask(a.run, a.dispatch, a.orca)
    if ask:
        code, result = orca(["orchestration", "reply", "--id", ask, "--body", body], a.orca)
        print(json.dumps({"delivered_via": "reply-to-open-ask", "question_id": ask,
                          "ok": code == 0, "detail": str(result)[:200]}))
        return code
    # No ask is open, so the only path is `send`. Do not return until the worker has consumed it,
    # otherwise the caller can deliver the next turn first and invert the order.
    code, result = orca(["orchestration", "send", "--run", a.run, "--to", f"dispatch:{a.dispatch}",
                         "--subject", "User decision", "--type", "status", "--body", body], a.orca)
    if code:
        print(json.dumps({"delivered_via": "send", "ok": False, "detail": str(result)[:200]}))
        return code
    sent = (result.get("message") or {}).get("id")
    deadline = time.time() + a.wait_consumed_s
    while time.time() < deadline:
        got, inbox = orca(["orchestration", "inbox", "--limit", "60"], a.orca)
        if not got:
            for m in (inbox.get("messages") or inbox.get("rows") or []):
                if m.get("id") == sent and m.get("delivered_at"):
                    print(json.dumps({"delivered_via": "send", "message_id": sent, "ok": True,
                                      "consumed_at": m["delivered_at"]}))
                    return 0
        time.sleep(5)
    print(json.dumps({"delivered_via": "send", "message_id": sent, "ok": False,
                      "detail": "sent but never reported consumed; do NOT deliver the next turn"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
