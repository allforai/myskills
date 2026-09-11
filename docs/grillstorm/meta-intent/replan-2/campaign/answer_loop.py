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


# The private file's "Run Policy and gates" section authorises operational answers that "approve no
# product topic or release scope", because "bootstrap planning is the task". A gate question is one
# that offers a confirm-shaped choice about the PLAN or the RUN POLICY — never about the product.
# Classification fails toward the coordinator: anything unrecognised is treated as a product question,
# so it spends a scripted turn or goes pending, and a human decides.
GATE_MARKERS = ("step 3.4", "plan confirmation", "plan delta", "计划 delta", "计划delta",
                "run policy", "运行策略", "unconfirmed_plan")
GATE_ANSWER = "confirm"


def is_gate_question(message):
    """True when the message is a plan/policy gate offering a confirm choice."""
    try:
        options = (json.loads(message.get("payload") or "{}") or {}).get("options") or []
    except (ValueError, TypeError):
        options = []
    if not any(str(o).strip().lower() == GATE_ANSWER for o in options):
        return False
    body = (message.get("body") or "").lower()
    return any(marker in body for marker in GATE_MARKERS)


def next_action(message, script, used):
    """Decide one message. `message` carries `type` and, for a question, `id` and `body`."""
    kind = message.get("type")
    mid = message.get("id") or message.get("message_id")
    ack = message.get("delivery_id")          # only set by the legacy one-message shape
    if kind == "worker_done":
        return {"kind": "done", "ack": ack, "used": used, "snapshot_before": False}
    if kind == "escalation":
        return {"kind": "escalation", "message_id": mid, "ack": None, "used": used, "snapshot_before": True}
    if kind == "question":
        if is_gate_question(message):
            # operational, and deliberately does NOT advance `used`: a gate spends no product turn
            return {"kind": "reply", "message_id": mid, "body": GATE_ANSWER, "ack": ack,
                    "used": used, "snapshot_before": True, "operational": True}
        turns = script.get("turns") or []
        if used < len(turns):
            return {"kind": "reply", "message_id": mid, "body": turns[used],
                    "ack": ack, "used": used + 1, "snapshot_before": True}
        return {"kind": "pending", "message_id": mid, "ack": None, "used": used, "snapshot_before": True}
    return {"kind": "ignore", "ack": ack, "used": used, "snapshot_before": False}


def plan_batch(result, script, used):
    """One Orca delivery is a batch: result.messages[] under a single result.deliveryId.
    Decide every message in order; the caller acks the deliveryId once, after acting."""
    acts = []
    done = False
    for message in result.get("messages") or []:
        act = next_action(message, script, used)
        used = act["used"]
        acts.append(act)
        if act["kind"] in ("done", "pending", "escalation"):
            done = True
            break
    return acts, used, done


def orca(args, exe):
    """Run an Orca command and return (exit, result). Orca wraps every payload in {id, ok, result}."""
    out = subprocess.run([exe, *args, "--json"], capture_output=True, text=True, timeout=1000)
    if not out.stdout.strip().startswith("{"):
        return out.returncode, {"raw": out.stdout, "stderr": out.stderr}
    body = json.loads(out.stdout)
    return out.returncode, body.get("result", body)


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
        code, result = orca(args, a.orca); ack = None
        messages = result.get("messages") or []
        if not messages:
            empty += 1
            if empty >= a.max_empty:
                replies.append({"event": "stalled", "after_empty_waits": empty}); break
            continue
        empty = 0
        acts, used, done = plan_batch(result, script, used)
        for act, message in zip(acts, messages):
            if act["snapshot_before"]:
                snapshot(a.orca, a.dispatch, a.out, len(replies) + 1)
            if act["kind"] == "reply":
                orca(["orchestration", "reply", "--id", act["message_id"], "--body", act["body"]], a.orca)
                # the evaluator must be able to tell a scripted user turn from an operational gate answer
                replies.append({"question": message.get("body"), "answer": act["body"],
                                "kind": "operational-gate" if act.get("operational") else "scripted-user-turn"})
            elif act["kind"] == "done":
                replies.append({"event": "worker_done", "outcome": message.get("outcome")})
            elif act["kind"] in ("pending", "escalation"):
                replies.append({"event": act["kind"], "message": message})
        ack = result.get("deliveryId")
        if done:
            if ack:
                orca(["orchestration", "check", "--ack", ack, "--timeout-ms", "1000"], a.orca)
            break
    (a.out / "replies.json").write_text(json.dumps({"used_turns": used, "replies": replies}, indent=2, ensure_ascii=False))
    print(json.dumps({"dispatch": a.dispatch, "used_turns": used, "last": replies[-1] if replies else None}))


if __name__ == "__main__":
    main()
