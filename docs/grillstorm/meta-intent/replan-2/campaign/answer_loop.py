"""Coordinator loop for one host cell (blind protocol, evaluator-private turns).

Drives a supervised Orca dispatch: waits for its deliveries, answers each `question` with the
scenario's NEXT scripted user turn (never invents one), snapshots the pending state before every
reply (the silence observation), acks what it consumed, and stops on `worker_done`. Pure decision
logic is in next_action() so it can be tested without Orca.

Usage: answer_loop.py --dispatch <id> --script turns.json --out <dir> [--orca orca] [--timeout-ms 900000]
"""
import argparse
import json
import subprocess
import time
from pathlib import Path


def next_action(delivery, script, used):
    kind = delivery.get("type")
    if kind == "worker_done":
        return {"kind": "done", "ack": delivery.get("delivery_id"), "used": used, "snapshot_before": False}
    if kind == "escalation":
        return {"kind": "escalation", "message_id": delivery.get("message_id"), "ack": None, "used": used, "snapshot_before": True}
    if kind == "question":
        turns = script.get("turns") or []
        if used < len(turns):
            return {"kind": "reply", "message_id": delivery.get("message_id"), "body": turns[used],
                    "ack": delivery.get("delivery_id"), "used": used + 1, "snapshot_before": True}
        return {"kind": "pending", "message_id": delivery.get("message_id"), "ack": None, "used": used, "snapshot_before": True}
    return {"kind": "ignore", "ack": delivery.get("delivery_id"), "used": used, "snapshot_before": False}


def orca(args, exe):
    out = subprocess.run([exe, *args, "--json"], capture_output=True, text=True, timeout=1000)
    return out.returncode, (json.loads(out.stdout) if out.stdout.strip().startswith("{") else {"raw": out.stdout, "stderr": out.stderr})


def snapshot(exe, dispatch, out_dir, k):
    """The pending state before a reply: the worker's dispatch pages as Orca reports them now."""
    code, page = orca(["orchestration", "worker-show", "--dispatch", dispatch], exe)
    (out_dir / f"snapshot-before-reply-{k:02d}.json").write_text(json.dumps({"exit": code, "at": time.time(), "page": page}, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dispatch", required=True); ap.add_argument("--script", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path); ap.add_argument("--orca", default="orca")
    ap.add_argument("--timeout-ms", type=int, default=900000); ap.add_argument("--max-empty", type=int, default=3)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    script = json.loads(a.script.read_text()); used = 0; replies = []; empty = 0; ack = None
    while True:
        args = ["orchestration", "check", "--wait", "--types", "worker_done,escalation,question", "--timeout-ms", str(a.timeout_ms)]
        if ack: args += ["--ack", ack]
        code, delivery = orca(args, a.orca); ack = None
        if not delivery.get("type"):
            empty += 1
            if empty >= a.max_empty:
                replies.append({"event": "stalled", "after_empty_waits": empty}); break
            continue
        empty = 0
        act = next_action(delivery, script, used); used = act["used"]
        if act["snapshot_before"]:
            snapshot(a.orca, a.dispatch, a.out, len(replies) + 1)
        if act["kind"] == "reply":
            orca(["orchestration", "reply", "--id", act["message_id"], "--body", act["body"]], a.orca)
            replies.append({"question": delivery.get("body"), "answer": act["body"]}); ack = act["ack"]
        elif act["kind"] == "done":
            replies.append({"event": "worker_done", "outcome": delivery.get("outcome")}); ack = act["ack"]
            orca(["orchestration", "check", "--ack", ack, "--timeout-ms", "1000"], a.orca); break
        elif act["kind"] in ("pending", "escalation"):
            replies.append({"event": act["kind"], "message": delivery}); break   # operator decides
        else:
            ack = act["ack"]
    (a.out / "replies.json").write_text(json.dumps({"used_turns": used, "replies": replies}, indent=2, ensure_ascii=False))
    print(json.dumps({"dispatch": a.dispatch, "used_turns": used, "last": replies[-1] if replies else None}))


if __name__ == "__main__":
    main()
