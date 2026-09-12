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




def answered_question_ids(path):
    """Question ids this cell has already answered, in any prior invocation or by hand.

    The FIFO replays an unacknowledged delivery, and a coordinator answering out of band cannot ack
    it, so without this the loop answers the same question twice and burns a scripted turn on the
    second pass.
    """
    try:
        recorded = json.loads(Path(path).read_text()).get("replies") or []
    except (OSError, ValueError):
        return set()
    out = set()
    for entry in recorded:
        qid = entry.get("question_id")
        if qid:
            out.add(qid)
        pending = entry.get("message")
        if isinstance(pending, dict) and pending.get("id"):
            out.add(pending["id"])
    return out


def worker_is_live(dispatch, exe):
    """True when Orca still observes this dispatch's agent as live.

    Absence is not death. `worker-show`'s observation is PTY liveness, so a True here means keep
    waiting; False means the process is gone and the loop may stop; None means Orca could not tell,
    which is also not proof of exit, so it is reported rather than treated as either.
    """
    code, result = orca(["orchestration", "worker-show", "--dispatch", dispatch], exe)
    observation = (result or {}).get("observation") or {}
    status = observation.get("status")
    if status == "live":
        return True
    if status in ("exited", "dead", "stopped"):
        return False
    return None


def check_argv(run, types, timeout_ms, ack):
    """Build one `check` invocation, always scoped to this cell's Run.

    Orca hands back the RUN's oldest FIFO delivery, so two cells sharing a Run let one coordinator
    loop consume the other's question. Each cell therefore gets its own Run and every check names it.
    """
    if not run:
        raise ValueError("check needs an explicit run: an unscoped loop can consume another cell's deliveries")
    argv = ["orchestration", "check", "--run", run, "--wait", "--types", types, "--timeout-ms", str(timeout_ms)]
    if ack:
        argv += ["--ack", ack]
    return argv


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


def spent_turns(path):
    """Scripted turns already delivered for this cell, across every prior invocation. Without this a
    resumed loop restarts at turn 1 and answers a later question with words meant for an earlier one."""
    try:
        return int(json.loads(Path(path).read_text()).get("used_turns") or 0)
    except (OSError, ValueError, TypeError):
        return 0


def is_foreign(message, own):
    """True only when a delivery belongs to ANOTHER cell. The sender may be this cell's dispatch, one
    of its own terminals, or the Run itself (a coordinator reply echoing back)."""
    handle = message.get("from_handle") or ""
    if not handle or handle.startswith("run:"):
        return False
    if handle == "dispatch:" + (own.get("dispatch") or ""):
        return False
    return handle not in (own.get("terminals") or [])


def merge_replies(path, record):
    """Append this invocation's record to the cell's reply log. A cell is usually driven in several
    invocations — a gate answered by hand between them — and overwriting would destroy the
    question-and-answer evidence the evaluator is required to judge from."""
    prior = {}
    if path.exists():
        try:
            prior = json.loads(path.read_text())
        except ValueError:
            prior = {"unreadable_prior": path.read_text()[:2000]}
    replies = (prior.get("replies") or []) + (record.get("replies") or [])
    invocations = (prior.get("invocations") or []) + [{"used_turns": record.get("used_turns", 0),
                                                       "replies": len(record.get("replies") or [])}]
    # Each invocation's `used` already starts from spent_turns, so it is cumulative, not a delta:
    # summing them compounds and the next invocation would skip real turns. Take the high-water mark
    # rather than the last value, so an invocation that never read the prior count (a crash, a fresh
    # output directory) cannot rewind the ledger and re-deliver a turn already spent.
    merged = {"used_turns": max([i["used_turns"] for i in invocations] + [prior.get("used_turns") or 0]),
              "invocations": invocations, "replies": replies}
    path.write_text(json.dumps(merged, indent=2, ensure_ascii=False))
    return merged


def cell_terminals(dispatch_json):
    """Terminal handles this cell owns, from its own worker-start receipt."""
    try:
        result = json.loads(Path(dispatch_json).read_text()).get("result", {})
    except (OSError, ValueError):
        return []
    return [e.get("id") for e in result.get("effects") or [] if e.get("kind") == "terminal" and e.get("id")]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dispatch", required=True); ap.add_argument("--script", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path); ap.add_argument("--orca", default="orca")
    ap.add_argument("--run", required=True, help="this cell's own Orca Run; never share one between cells")
    ap.add_argument("--timeout-ms", type=int, default=900000); ap.add_argument("--max-empty", type=int, default=3)
    ap.add_argument("--max-replay-skips", type=int, default=5)
    a = ap.parse_args(argv); a.out.mkdir(parents=True, exist_ok=True)
    script = json.loads(a.script.read_text())
    used = spent_turns(a.out / "replies.json")          # resume where the last invocation stopped
    own = {"dispatch": a.dispatch, "terminals": cell_terminals(a.out.parent / "dispatch.json")}
    replies = []; empty = 0; ack = None; skipped = 0; answered_here = set()
    while True:
        args = check_argv(a.run, "worker_done,escalation,question", a.timeout_ms, ack)
        code, result = orca(args, a.orca); ack = None
        messages = result.get("messages") or []
        if not messages:
            empty += 1
            if empty >= a.max_empty:
                # An empty wait is a checkpoint, not a failure. Exiting on a count alone killed two
                # concurrent loops 28 seconds before their actors asked anything: a bigger fixture
                # simply takes longer to reach its first question. Enumerate instead, exactly as the
                # orchestration guide directs, and only stop on positive proof the worker is gone.
                alive = worker_is_live(a.dispatch, a.orca)
                if alive:
                    empty = 0
                    continue
                replies.append({"event": "stalled", "after_empty_waits": empty,
                                "worker_liveness": "not live" if alive is False else "unverifiable"})
                break
            continue
        empty = 0
        foreign = [m for m in messages if is_foreign(m, own)]
        if foreign:
            # never answer another cell's actor; stop and let the coordinator sort the Run out
            replies.append({"event": "foreign-delivery", "from": [m.get("from_handle") for m in foreign]})
            merge_replies(a.out / "replies.json", {"used_turns": used, "replies": replies})
            print(json.dumps({"dispatch": a.dispatch, "used_turns": used,
                              "last": {"event": "foreign-delivery", "from": [m.get("from_handle") for m in foreign]}}))
            return
        # A delivery replays until acknowledged. When a coordinator answers a question by hand it
        # cannot ack the batch, so the same question comes back and the loop spent the NEXT scripted
        # turn on it: that is how a UTF-8 BOM decision reached one actor before it had asked anything.
        # Answer each question id exactly once, whatever the FIFO replays.
        already = answered_question_ids(a.out / "replies.json") | answered_here
        stale = [m for m in messages if (m.get("id") or m.get("message_id")) in already]
        if stale and len(stale) == len(messages):
            replies.append({"event": "replay-skipped",
                            "question_ids": [m.get("id") or m.get("message_id") for m in stale]})
            ack = result.get("delivery_id") or result.get("deliveryId")
            skipped += 1
            # Acking should retire the batch. If the same replay keeps coming back the FIFO is not
            # advancing, and spinning on it forever is worse than stopping and saying so.
            if not ack or skipped > a.max_replay_skips:
                merge_replies(a.out / "replies.json", {"used_turns": used, "replies": replies})
                print(json.dumps({"dispatch": a.dispatch, "used_turns": used,
                                  "last": {"event": "replay-unackable" if not ack else "replay-not-retiring",
                                           "skipped": skipped}}))
                return
            continue
        if stale:
            messages = [m for m in messages if m not in stale]
            result = dict(result, messages=messages)
        acts, used, done = plan_batch(result, script, used)
        for act, message in zip(acts, messages):
            if act["snapshot_before"]:
                snapshot(a.orca, a.dispatch, a.out, len(replies) + 1)
            if act["kind"] == "reply":
                orca(["orchestration", "reply", "--id", act["message_id"], "--body", act["body"]], a.orca)
                # the evaluator must be able to tell a scripted user turn from an operational gate answer
                answered_here.add(message.get("id") or message.get("message_id"))
                replies.append({"question": message.get("body"),
                                "question_id": message.get("id") or message.get("message_id"),
                                "answer": act["body"],
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
    merge_replies(a.out / "replies.json", {"used_turns": used, "replies": replies})
    print(json.dumps({"dispatch": a.dispatch, "used_turns": used, "last": replies[-1] if replies else None}))


if __name__ == "__main__":
    main()
