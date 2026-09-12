"""Serve many concurrent cells from ONE coordinator terminal, by rotating the Run binding.

Orca fences both `check` and `reply` on the coordinator terminal's bound Run: a terminal can consume
for exactly one Run at a time. Starting one driving loop per cell therefore does NOT work — eight of
nine were refused with consumer_fenced while their actors sat waiting. Actors run concurrently; their
DRIVER cannot. This rotates instead: bind a cell, drain what is waiting, answer from that cell's own
script, unbind by binding the next.

Each cell keeps its own replies.json ledger, so a scripted turn is never taken from the wrong
scenario's script and a turn already delivered is never delivered twice.

Usage: rotate_driver.py --cells cells.json [--rounds N] [--orca orca] [--per-cell-timeout-ms 4000]
  cells.json: [{"key": "codex/reshape-business-model", "dispatch": "...", "run": "...",
                "script": "/abs/turns.json", "out": "/abs/capture"}, ...]
"""
import argparse
import json
import subprocess
import time
from pathlib import Path

import answer_loop as al


def orca(args, exe):
    out = subprocess.run([exe, *args, "--json"], capture_output=True, text=True, timeout=300)
    if not out.stdout.strip().startswith("{"):
        return out.returncode, {"raw": out.stdout[:400], "stderr": out.stderr[:400]}
    try:
        payload = json.loads(out.stdout)
    except ValueError:
        return out.returncode, {"raw": out.stdout[:400]}
    return (0 if payload.get("ok") else 1), (payload.get("result") or payload.get("error") or {})


def bind(run, exe):
    code, result = orca(["orchestration", "run-use", "--id", run], exe)
    return code == 0, result


def serve(cell, exe, timeout_ms):
    """One visit to one cell: bind, drain its waiting batch, answer what this cell's script covers."""
    ok, detail = bind(cell["run"], exe)
    if not ok:
        return {"key": cell["key"], "event": "bind-failed", "detail": str(detail)[:200]}
    script = json.loads(Path(cell["script"]).read_text())
    out = Path(cell["out"])
    used = al.spent_turns(out / "replies.json")
    already = al.answered_question_ids(out / "replies.json")
    code, result = orca(["orchestration", "check", "--run", cell["run"], "--wait", "--types",
                         "worker_done,escalation,question", "--timeout-ms", str(timeout_ms)], exe)
    if code != 0:
        return {"key": cell["key"], "event": "check-failed", "detail": str(result)[:200]}
    messages = [m for m in (result.get("messages") or [])
                if (m.get("id") or m.get("message_id")) not in already]
    if not messages:
        return {"key": cell["key"], "event": "idle"}
    acts, used_after, done = al.plan_batch(dict(result, messages=messages), script, used)
    recorded, served = [], []
    for act, message in zip(acts, messages):
        if act["kind"] == "reply":
            orca(["orchestration", "reply", "--id", act["message_id"], "--body", act["body"]], exe)
            recorded.append({"question": message.get("body"),
                             "question_id": message.get("id") or message.get("message_id"),
                             "answer": act["body"],
                             "kind": "operational-gate" if act.get("operational") else "scripted-user-turn"})
            served.append("reply")
        elif act["kind"] == "done":
            recorded.append({"event": "worker_done", "outcome": message.get("outcome")})
            served.append("worker_done")
        else:
            recorded.append({"event": act["kind"], "message": message})
            served.append(act["kind"])
    if recorded:
        al.merge_replies(out / "replies.json", {"used_turns": used_after, "replies": recorded})
    ack = result.get("deliveryId") or result.get("delivery_id")
    if ack:
        orca(["orchestration", "check", "--run", cell["run"], "--ack", ack, "--timeout-ms", "1000"], exe)
    return {"key": cell["key"], "event": "served", "actions": served, "used_turns": used_after,
            "settled": bool(done)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", required=True)
    ap.add_argument("--rounds", type=int, default=200)
    ap.add_argument("--orca", default="orca")
    ap.add_argument("--per-cell-timeout-ms", type=int, default=4000)
    a = ap.parse_args(argv)
    cells = json.loads(Path(a.cells).read_text())
    settled = set()
    for round_index in range(a.rounds):
        for cell in cells:
            if cell["key"] in settled:
                continue
            report = serve(cell, a.orca, a.per_cell_timeout_ms)
            if report["event"] != "idle":
                print(json.dumps({"round": round_index, **report}), flush=True)
            if report.get("settled"):
                settled.add(cell["key"])
        if len(settled) == len(cells):
            print(json.dumps({"event": "all-settled", "rounds": round_index + 1}), flush=True)
            return 0
    print(json.dumps({"event": "rounds-exhausted", "settled": sorted(settled)}), flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
