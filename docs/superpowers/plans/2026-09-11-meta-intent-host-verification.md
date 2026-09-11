# meta-intent Host Verification (T15–T18 → #9–#18) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the four prepared thought-test batches (T15–T18) as real Claude and Codex host sessions against a fresh candidate, evaluate every cell against its private criteria, and record a `results.json` ledger that can honestly close #9–#18 — or say exactly which cells failed or could not be verified.

**Architecture:** The harness already exists under `docs/grillstorm/meta-intent/replan-2/T15..T18/` and is *suspended* on every batch because its candidate predates the ADR-0008 work and the #9–#14 audit. Each batch is: export a pinned candidate and N isolated fixture projects (`prepare_packets.py`), launch one fresh supervised host session per cell (Orca `worker-start`, `--agent claude|codex`) delivering only that cell's `actor-input.md`, answer its `ask`s with the scripted user turns from `evaluator-private.md`, capture the dispatch pages, admit the evidence by identity (`admit_evidence.py`), then a fresh-context evaluator reads the raw dialogue against the private criteria and writes the cell's status. Closes happen only in the main session on a green ledger.

**Tech Stack:** Python 3 (`prepare_packets.py`, `capture_worker.py`, `admit_evidence.py`, pytest pins), Orca CLI 1.4.199 (`orca orchestration run-create / worker-start / check / reply`, `orca terminal read`), Claude Code and Codex CLI 0.153.4 as the two hosts.

**Spec:** GitHub issues #15, #16, #17, #18 (their "执行、证据与关闭条件" sections) and the two shared v2 criteria on #9–#14. The batch-specific oracles are `docs/grillstorm/meta-intent/replan-2/T<n>/evaluator-private.md` and are never sent to a tested context.

## Global Constraints

- **Blind execution.** A tested actor receives only its cell's `actor-input.md`, its `project/` folder, the candidate skill assets, and the one user turn being delivered. Never the criteria, expected conclusions, other cells, reports, test sources, or evaluator materials. ("受测 agent 仅接收场景、原始仓库／历史资料、当前 Skill 和该步用户输入".)
- **Both hosts, really.** Every cell is executed on Claude *and* Codex as a fresh independent session. A host that cannot run a cell is recorded `unverified` with the reason; one host's result never stands in for the other.
- **No semantic pass from a script.** `admit_evidence.py` checks identity only (candidate bytes, session id, raw-dialogue hash, loaded-file hashes). A cell is `passed` only when a fresh-context evaluator, holding `evaluator-private.md`, judges the raw dialogue and artefacts. "不能用提示词含关键字、文件存在或 agent 自报代替行为验证."
- **Candidate bytes are frozen for the whole campaign.** Any product fix requires a new accepted candidate and fresh executions of every affected cell. Record the candidate commit and `candidate_tree_sha256` in every ledger and receipt.
- **Isolated fixtures only.** Actors work in the exported `project/` folders under the packet root; nothing touches a real product, no production calls, no dependency installs.
- **Silence is an observation.** While an actor is blocked in `ask`, capture the pending state *before* replying — that is the "user did not answer" evidence several scenarios need.
- **Actor launches are the operator's step.** This plan prepares, launches through Orca supervised orchestration, and evaluates; a task that starts host sessions runs only when the user has said "launch batch T<n>" for that batch. Do not launch on the plan alone.
- Results vocabulary: a cell is `passed` or `unverified`; an `unverified` cell must carry a `reason` (`test_results_pin.py` enforces this).
- Never stage `docs/feedback/inbox/`. Commit messages via `-F` file; trailer on every commit:
  ```
  Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
  ```
- Resolved Orca executable for this session is `orca` (managed terminal, `ORCA_APP_VERSION=1.4.198`; `orca --version` → 1.4.199). Prefer `--json` everywhere.

---

## File Structure

| File | Responsibility |
|---|---|
| `docs/grillstorm/meta-intent/replan-2/T<n>/prepare_packets.py` | Exports candidate + fixture projects + `actor-input.md` per cell (exists; T16–T18 reuse T15's exporter) |
| `docs/grillstorm/meta-intent/replan-2/T15/capture_worker.py` | Records a dispatch's Orca pages to disk without grading (exists) |
| `docs/grillstorm/meta-intent/replan-2/T15/admit_evidence.py` | Identity check of a cell's `receipt.json` against the manifest (exists) |
| `docs/grillstorm/meta-intent/replan-2/T<n>/evaluator-private.md` | Scripted user turns + private criteria per scenario (exists; **never** delivered to an actor) |
| `docs/grillstorm/meta-intent/replan-2/T<n>/results.json` | The batch ledger: `required_cells[]` with status/reason/packet/attempts (exists; rewritten per campaign) |
| `docs/grillstorm/meta-intent/replan-2/T<n>/launch-request.md` | Launch binding for the current candidate (exists; rewritten to lift the suspension) |
| `docs/grillstorm/meta-intent/replan-2/campaign/launch_cell.sh` | **New.** One-cell launcher: `run-create` once, `worker-start` for a cell, records dispatch id |
| `docs/grillstorm/meta-intent/replan-2/campaign/answer_loop.py` | **New.** Coordinator loop: `check --wait`, snapshot-before-reply, `reply` with the scenario's next scripted turn, until `worker_done` |
| `docs/grillstorm/meta-intent/replan-2/campaign/evaluate_cell.md` | **New.** The fresh-context evaluator prompt template (criteria injected from `evaluator-private.md`, transcript from the capture) |
| `docs/grillstorm/meta-intent/replan-2/campaign/T<n>-evaluations/<host>-<scene>.md` | **New.** One evaluator verdict per cell |

Cell counts: T15 14 (7 scenes × 2 hosts), T16 14, T17 16, T18 16 — 60 cells.

---

### Task 1: Fresh candidate — lift the suspension on all four batches

**Files:**
- Modify: `docs/grillstorm/meta-intent/replan-2/T15/launch-request.md`, `T16/…`, `T17/…`, `T18/…` (replace the "Launch suspended" header with a current binding)
- Modify: `docs/grillstorm/meta-intent/replan-2/T15/results.json`, `T16/`, `T17/`, `T18/` (reset `required_cells[].status` to `unverified`, new `packet_root`, new `candidate_tree_sha256`)
- Test (run): `docs/grillstorm/meta-intent/replan-2/T15/test_prepare_packets.py`, `T15/test_results_pin.py` and the T16–T18 twins

**Interfaces:**
- Consumes: `python3 <T>/prepare_packets.py <new-absolute-dir> --candidate <commit>` → prints `{"packets", "candidate_tree_sha256", "cells", "executed"}` and writes `<dir>/candidate/`, `<dir>/candidate-manifest.json`, `<dir>/<host>/<scene>/{project/,source-before.json,actor-input.md}`.
- Produces: `PACKETS_T<n>` (absolute packet root per batch) and `CANDIDATE` (one commit for all four) — every later task reads them from the batch's `results.json` fields `packet_root` and `candidate_tree_sha256`.

- [ ] **Step 1: Pin the candidate and verify the tree is what the audit proved**

```bash
cd /Users/aa/workspace/myskills
git fetch -q origin && test "$(git log --oneline HEAD..origin/main | wc -l)" = 0
CANDIDATE=$(git rev-parse HEAD)          # 01146b70 at plan time; the audit proved this tree
echo "$CANDIDATE"
python3 -m pytest -q claude/meta-skill/tests/unit 2>&1 | tail -1     # expect ≈1166 passed, 0 failed
```

Expected: `… passed` with no failures. A red suite means the candidate is not acceptable; stop.

- [ ] **Step 2: Export packets for each batch**

```bash
R=docs/grillstorm/meta-intent/replan-2
ROOT=$(mktemp -d /private/tmp/meta-intent-host-campaign.XXXXXX)
for T in T15 T16 T17 T18; do
  python3 $R/$T/prepare_packets.py "$ROOT/$T" --candidate "$CANDIDATE" | tee "$ROOT/$T-export.json"
done
ls "$ROOT"/T15/claude/ "$ROOT"/T18/codex/
```

Expected: four JSON lines with `"executed": 0` and `cells` 14/14/16/16; each `<host>/<scene>/` holds `project/`, `actor-input.md`, `source-before.json`. All four `candidate_tree_sha256` values are identical (same commit).

- [ ] **Step 3: Verify the exporter preserved executable bits**

The T15 evaluator notes an earlier export lost the 0755 mode on the user-invocation hook. Check the manifest's mode record:

```bash
python3 - <<EOF
import json,sys
m=json.load(open("$ROOT/T15/candidate-manifest.json"))
hook=[p for p in m.get("modes",m.get("git_modes",{})) if p.endswith("user-only-skills.sh")]
print("hook entries:", hook, {p: m.get("modes",m.get("git_modes",{}))[p] for p in hook})
EOF
```

Expected: the hook is listed with mode `100755`. If absent or `100644`, the export is invalid — stop and file it.

- [ ] **Step 4: Rewrite each `launch-request.md` and reset each `results.json`**

For each batch, replace the "## Launch suspended" section with:

```markdown
## Current launch binding — candidate <CANDIDATE>

Candidate commit: `<CANDIDATE>` (main; #9–#14 audit-proved, ADR-0008 merged, 1166 unit tests green).
Packet root: `<ROOT>/T<n>`
Candidate tree SHA-256: `<candidate_tree_sha256 from the export JSON>`
Claude entry: `candidate/claude/meta-skill/skills/bootstrap/SKILL.md`
Codex entry:  `candidate/codex/meta-skill/SKILL.md`

Every cell is `unverified` until a real host session runs it and a fresh-context evaluator
judges the raw dialogue. Deliver each cell's `actor-input.md` verbatim and nothing else.
```

Keep the batch's historical text below it under "## Historical launch binding — superseded". Then reset the ledger with this script (run once per batch):

```bash
python3 - <<EOF
import json, pathlib
T="T15"; root="$ROOT/T15"; sha=json.load(open("$ROOT/T15-export.json"))["candidate_tree_sha256"]
p=pathlib.Path("$R/T15/results.json"); d=json.load(open(p))
d["source_commit"]="$CANDIDATE"; d["packet_root"]=root; d["candidate_tree_sha256"]=sha
d.pop("candidate_acceptance_withdrawal", None); d.pop("candidate_refresh_required", None)
for c in d["required_cells"]:
    scene=c["scenario"].split("/")[-1]; host=c["host"]
    c.update(status="unverified", reason="Fresh candidate prepared; no actor execution yet.",
             packet=f"{root}/{host}/{scene}/actor-input.md", project=f"{root}/{host}/{scene}/project", attempts=[])
d["executed_cells"]=[]
p.write_text(json.dumps(d, indent=2, ensure_ascii=False)+"\n")
print(T, len(d["required_cells"]), "cells reset")
EOF
```

(Repeat with `T16`, `T17`, `T18`, substituting the batch name in the three places it appears.)

- [ ] **Step 5: Run the pins and commit**

```bash
for T in T15 T16 T17 T18; do python3 -m pytest -q $R/$T/test_prepare_packets.py $R/$T/test_results_pin.py 2>&1 | tail -1; done
cat > /tmp/host1.txt <<'EOF'
meta-intent host campaign: fresh candidate exported for T15–T18, suspensions lifted, ledgers reset to unverified

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add $R/T15 $R/T16 $R/T17 $R/T18 && git commit -q -F /tmp/host1.txt
```

Expected: four `passed` lines (the pin tests accept `unverified` cells that carry a reason).

---

### Task 2: One-cell launcher and the coordinator answer loop

**Files:**
- Create: `docs/grillstorm/meta-intent/replan-2/campaign/launch_cell.sh`
- Create: `docs/grillstorm/meta-intent/replan-2/campaign/answer_loop.py`
- Create: `docs/grillstorm/meta-intent/replan-2/campaign/test_answer_loop.py`

**Interfaces:**
- Consumes: Orca verbs from the version-matched guide — `orca orchestration run-create --objective … --json`, `orca orchestration worker-start --spec "<task>" --worktree current --agent <claude|codex> --json` (returns `dispatch_id`), `orca orchestration check --wait --types "worker_done,escalation,question" --timeout-ms N --json` (returns the oldest delivery with `message_id`, `delivery_id`), `orca orchestration reply --id <message_id> --body "<answer>" --json`, `orca orchestration check --ack <delivery_id> …`.
- Produces: `launch_cell.sh <T> <host> <scene>` → prints `{"dispatch_id": …, "run_id": …}` and appends to `<packet_root>/campaign-run.json`; `answer_loop.py --dispatch <id> --script <turns.json> --out <dir>` → drives one cell to `worker_done`, writing `<dir>/snapshot-before-reply-<k>.json` and `<dir>/replies.json`. `turns.json` is `{"turns": ["<user turn 1>", "<user turn 2>", …]}` extracted from the scenario's section of `evaluator-private.md`.

- [ ] **Step 1: Write the failing test for the answer loop's pure logic**

`campaign/test_answer_loop.py`:

```python
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
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd docs/grillstorm/meta-intent/replan-2/campaign && python3 -m pytest -q test_answer_loop.py -v`
Expected: FAIL — `ModuleNotFoundError: answer_loop`.

- [ ] **Step 3: Write `answer_loop.py`**

```python
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
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd docs/grillstorm/meta-intent/replan-2/campaign && python3 -m pytest -q test_answer_loop.py -v`
Expected: `4 passed`.

- [ ] **Step 5: Write `launch_cell.sh`**

```bash
#!/usr/bin/env bash
# Launch ONE blind host cell as a supervised Orca worker. Usage: launch_cell.sh <T15|T16|T17|T18> <claude|codex> <scene>
# Reads packet_root from the batch's results.json; creates the campaign Run once (campaign-run.json in the packet root).
set -euo pipefail
T=$1; HOST=$2; SCENE=$3; ORCA=${ORCA:-orca}
R=$(cd "$(dirname "$0")/.." && pwd)
ROOT=$(python3 -c "import json;print(json.load(open('$R/$T/results.json'))['packet_root'])")
CELL="$ROOT/$HOST/$SCENE"; test -f "$CELL/actor-input.md" || { echo "no packet at $CELL" >&2; exit 2; }
RUNF="$ROOT/campaign-run.json"
if [ ! -f "$RUNF" ]; then
  $ORCA orchestration run-create --objective "meta-intent host campaign $T on candidate $(python3 -c "import json;print(json.load(open('$R/$T/results.json'))['source_commit'])")" --json > "$RUNF"
fi
RUN_ID=$(python3 -c "import json;d=json.load(open('$RUNF'));print(d.get('run_id') or d.get('run',{}).get('id'))")
# The spec IS the packet, verbatim, plus the working folder. Nothing else is delivered.
SPEC="Work only inside $CELL/project. $(cat "$CELL/actor-input.md")"
$ORCA orchestration worker-start --spec "$SPEC" --worktree current --agent "$HOST" --json | tee "$CELL/dispatch.json"
python3 - <<EOF
import json; d=json.load(open("$CELL/dispatch.json"))
print(json.dumps({"dispatch_id": d.get("dispatch_id") or d.get("dispatch",{}).get("id"), "run_id": "$RUN_ID", "cell": "$T/$HOST/$SCENE"}))
EOF
```

`chmod +x campaign/launch_cell.sh`. This script is **not run in this task** — it starts a real host session and is invoked only in Task 4 after the user says to launch a batch.

- [ ] **Step 6: Commit**

```bash
cat > /tmp/host2.txt <<'EOF'
meta-intent host campaign: one-cell launcher and the blind coordinator answer loop

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add docs/grillstorm/meta-intent/replan-2/campaign/launch_cell.sh docs/grillstorm/meta-intent/replan-2/campaign/answer_loop.py docs/grillstorm/meta-intent/replan-2/campaign/test_answer_loop.py
git commit -q -F /tmp/host2.txt
```

---

### Task 3: Scripted-turn extraction and the evaluator prompt

**Files:**
- Create: `docs/grillstorm/meta-intent/replan-2/campaign/extract_turns.py`
- Create: `docs/grillstorm/meta-intent/replan-2/campaign/test_extract_turns.py`
- Create: `docs/grillstorm/meta-intent/replan-2/campaign/evaluate_cell.md`

**Interfaces:**
- Consumes: `T<n>/evaluator-private.md` — per scenario a `### <scene>` section whose user turns are the quoted strings introduced by `Answer only …: "…"` / `coordinator supplies this next user turn: "…"` (T15 shape; T16–T18 use the same quoting).
- Produces: `extract_turns.py <T> <scene>` → writes `<packet_root>/<scene>-turns.json` as `{"turns": [...]}` (the file `answer_loop.py --script` reads) and prints the count. `evaluate_cell.md` is the prompt template with three placeholders `{{CRITERIA}}`, `{{TRANSCRIPT_PATH}}`, `{{RECEIPT_PATH}}`.

- [ ] **Step 1: Write the failing test**

`campaign/test_extract_turns.py`:

```python
from pathlib import Path
from extract_turns import turns_for


SAMPLE = '''### large-code-local-button

Initial materials reuse the retail fixture.

Answer only unresolved UI/output questions: "Put Export CSV above the orders table. Use id, status, total."

Inspect whether the actor reused the journal.

Unwired contrast after a valid generated state: coordinator supplies this next user turn: "I also decide that this CSV includes a UTF-8 BOM."

### missing-product-docs

Answer only: "Nothing else; proceed."
'''


def test_turns_are_the_quoted_user_strings_of_one_scene_in_order():
    assert turns_for(SAMPLE, "large-code-local-button") == [
        "Put Export CSV above the orders table. Use id, status, total.",
        "I also decide that this CSV includes a UTF-8 BOM."]


def test_other_scenes_are_not_mixed_in_and_an_unknown_scene_is_empty():
    assert turns_for(SAMPLE, "missing-product-docs") == ["Nothing else; proceed."]
    assert turns_for(SAMPLE, "no-such-scene") == []
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd docs/grillstorm/meta-intent/replan-2/campaign && python3 -m pytest -q test_extract_turns.py -v`
Expected: FAIL — `ModuleNotFoundError: extract_turns`.

- [ ] **Step 3: Write `extract_turns.py`**

```python
"""Pull one scenario's scripted user turns out of evaluator-private.md, in order, and nothing else.

The private file mixes turns (quoted strings the coordinator delivers) with observations (what the
evaluator looks for). Only the quoted strings are turns; the observations never leave the evaluator.

Usage: extract_turns.py <T15|T16|T17|T18> <scene>   → writes <packet_root>/<scene>-turns.json
"""
import json
import re
import sys
from pathlib import Path

QUOTED = re.compile(r'"([^"\n]{8,})"')      # a user turn is a quoted sentence; short quoted tokens are not turns


def turns_for(private_md, scene):
    section = re.search(r'^### ' + re.escape(scene) + r'\n(.*?)(?=^### |\Z)', private_md, re.S | re.M)
    if not section:
        return []
    return [m.group(1) for m in QUOTED.finditer(section.group(1))]


def main():
    T, scene = sys.argv[1], sys.argv[2]
    R = Path(__file__).resolve().parent.parent
    private = (R / T / "evaluator-private.md").read_text()
    root = Path(json.load(open(R / T / "results.json"))["packet_root"])
    turns = turns_for(private, scene)
    (root / f"{scene}-turns.json").write_text(json.dumps({"turns": turns}, ensure_ascii=False, indent=2))
    print(json.dumps({"scene": scene, "turns": len(turns), "file": str(root / f"{scene}-turns.json")}))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd docs/grillstorm/meta-intent/replan-2/campaign && python3 -m pytest -q test_extract_turns.py -v`
Expected: `2 passed`.

- [ ] **Step 5: Write the evaluator prompt template**

`campaign/evaluate_cell.md`:

```markdown
You are the evaluator for ONE blind host cell. You did not run the actor and must not trust anything it says
about itself. Judge only from the raw dialogue and the artefacts it wrote.

Inputs:
- Raw transcript (dispatch pages, in order): {{TRANSCRIPT_PATH}}
- Receipt the actor wrote (identity only — already admitted by admit_evidence.py): {{RECEIPT_PATH}}
- Private criteria for this scenario (never shown to the actor):

{{CRITERIA}}

Rules:
- A criterion passes only on observed behaviour: what the actor asked, what it generated, what state it left.
  A keyword in a prompt, a file merely existing, or the actor's own claim of success proves nothing.
- Quote the transcript line(s) that decide each criterion. No quote, no verdict.
- "环境无法验证" is a legitimate result when the host lacked a capability the scenario needs; say which capability.
- Do not repair, re-run, or advise. Record.

Return exactly this JSON and nothing else:
{"status": "passed" | "unverified", "reason": "<one sentence; required when unverified>",
 "criteria": [{"criterion": "<quoted>", "verdict": "pass" | "fail" | "unverifiable", "evidence": "<transcript quote or artefact path>"}],
 "defects": ["<minimal reproducible step, if any criterion failed>"]}
```

- [ ] **Step 6: Commit**

```bash
cat > /tmp/host3.txt <<'EOF'
meta-intent host campaign: scripted-turn extraction and the fresh-context evaluator prompt

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add docs/grillstorm/meta-intent/replan-2/campaign/extract_turns.py docs/grillstorm/meta-intent/replan-2/campaign/test_extract_turns.py docs/grillstorm/meta-intent/replan-2/campaign/evaluate_cell.md
git commit -q -F /tmp/host3.txt
```

---

### Task 4: Execute one batch (repeat per batch, T15 first) — **operator-gated**

**Files:**
- Modify: `docs/grillstorm/meta-intent/replan-2/T<n>/results.json` (`required_cells[].status/reason/attempts`, `executed_cells`)
- Create: `docs/grillstorm/meta-intent/replan-2/campaign/T<n>-evaluations/<host>-<scene>.md` (one per cell)

**Interfaces:**
- Consumes: `launch_cell.sh`, `answer_loop.py`, `extract_turns.py` (Tasks 2–3); `T15/capture_worker.py <dispatch> <out> --orca orca`; `T15/admit_evidence.py <manifest> <candidate_root> <receipt>`.
- Produces: a green or explained ledger for the batch.

**Gate:** run this task only after the user has said "launch T<n>". Each cell starts a real host session.

- [ ] **Step 1: Prepare the turns for every scene in the batch**

```bash
R=docs/grillstorm/meta-intent/replan-2; T=T15
for scene in $(python3 -c "import json;print(' '.join(sorted({c['scenario'].split('/')[-1] for c in json.load(open('$R/$T/results.json'))['required_cells']})))"); do
  python3 $R/campaign/extract_turns.py $T $scene
done
```

Expected: one JSON line per scene with `turns ≥ 1` (a scene with 0 turns is a private-file formatting gap — fix the quoting in `evaluator-private.md`, never invent a turn).

- [ ] **Step 2: Launch the cells, host by host, and drive each to completion**

Launch **one host at a time** (Claude cells, then Codex cells) so the Orca Run's FIFO deliveries are unambiguous. For each cell:

```bash
ROOT=$(python3 -c "import json;print(json.load(open('$R/$T/results.json'))['packet_root'])")
HOST=claude; SCENE=large-code-local-button
OUT="$ROOT/$HOST/$SCENE/capture"; mkdir -p "$OUT"
D=$($R/campaign/launch_cell.sh $T $HOST $SCENE | tail -1 | python3 -c "import json,sys;print(json.load(sys.stdin)['dispatch_id'])")
python3 $R/campaign/answer_loop.py --dispatch "$D" --script "$ROOT/$SCENE-turns.json" --out "$OUT" --orca orca
python3 $R/T15/capture_worker.py "$D" "$OUT/transcript" --orca orca --pages 30 --limit 200
```

**Capture before releasing, and check completeness.** Orca's transcript archive is bounded: the
pilot captured after `worker-release` and got `contentComplete: false` with `initial-window-limited`,
losing the opening exchange. Run `capture_worker.py` while the dispatch is still held, then read
`capture.json`'s `limitations` and each page's `contentComplete`. A cell whose transcript is
incomplete cannot pass — the evaluator is required to judge from the actual dialogue — so record it
`unverified` with that reason and re-run the cell rather than evaluating a partial record. Release
only after the capture is complete:

```bash
orca orchestration worker-release --dispatch "$D" --json
```

Expected per cell: `answer_loop` prints `"last": {"event": "worker_done", …}`; `capture_worker` writes `page-0001.stdout.json …` and a `capture.json`. If `answer_loop` ends on `pending` (actor asked beyond the script) or `escalation`, the cell stays `unverified` with that reason — do not improvise an answer.

- [ ] **Step 3: Admit each cell's evidence by identity**

```bash
python3 $R/T15/admit_evidence.py "$ROOT/candidate-manifest.json" "$ROOT/candidate" "$ROOT/$HOST/$SCENE/receipt.json"
```

Expected: exit 0 and an empty `reasons` list. Any reason (`missing-session-identity`, hash mismatch, extra files) marks the cell `unverified` with that reason; the actor's raw dialogue still goes to the evaluator so a defect can be described, but the cell cannot pass.

- [ ] **Step 4: Evaluate each cell in a fresh context**

Build the prompt from the template and the scene's private section, then hand it to a fresh-context subagent (never the session that drove the actor):

```bash
python3 - <<EOF > "$OUT/evaluate-prompt.md"
import re
tpl=open("$R/campaign/evaluate_cell.md").read()
priv=open("$R/$T/evaluator-private.md").read()
sec=re.search(r'^### $SCENE\n(.*?)(?=^### |\Z)', priv, re.S|re.M).group(1)
print(tpl.replace("{{CRITERIA}}", sec).replace("{{TRANSCRIPT_PATH}}", "$OUT").replace("{{RECEIPT_PATH}}", "$ROOT/$HOST/$SCENE/receipt.json"))
EOF
```

Dispatch a fresh subagent with that file as its entire prompt; save its JSON verbatim to `$R/campaign/$T-evaluations/$HOST-$SCENE.md` (JSON body under a one-line header naming the cell, dispatch id and candidate sha). The evaluator's `status` is the cell's status.

- [ ] **Step 5: Write the ledger and pin it**

```bash
python3 - <<EOF
import json, pathlib, glob
R="$R"; T="$T"; p=pathlib.Path(f"{R}/{T}/results.json"); d=json.load(open(p))
for c in d["required_cells"]:
    scene=c["scenario"].split("/")[-1]; host=c["host"]
    ev=pathlib.Path(f"{R}/campaign/{T}-evaluations/{host}-{scene}.md")
    if not ev.exists(): continue
    body=ev.read_text().split("\n",1)[1]; v=json.loads(body)
    c["status"]=v["status"]; c["reason"]=v.get("reason","") if v["status"]=="unverified" else ""
    c.setdefault("attempts",[]).append({"evaluation": str(ev), "dispatch": open(f"{d['packet_root']}/{host}/{scene}/dispatch.json").read()[:200]})
d["executed_cells"]=[c["scenario"]+"@"+c["host"] for c in d["required_cells"] if c["status"]=="passed"]
p.write_text(json.dumps(d, indent=2, ensure_ascii=False)+"\n")
print({c["host"]+"/"+c["scenario"].split("/")[-1]: c["status"] for c in d["required_cells"]})
EOF
python3 -m pytest -q $R/$T/test_results_pin.py -v
```

Expected: the pin passes (every `unverified` cell has a reason; `passed_cells` equals the proven set).

- [ ] **Step 6: Commit the batch**

```bash
cat > /tmp/host4-$T.txt <<EOF
meta-intent host campaign: $T executed on Claude and Codex — <N> passed, <M> unverified (reasons in results.json)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add $R/$T/results.json $R/campaign/$T-evaluations
git commit -q -F /tmp/host4-$T.txt
```

Fill `<N>`/`<M>` from Step 5's printed map. Repeat Task 4 for T16, T17, T18 in that order (T16–T18 depend on the #9/#10 behaviours T15 exercises; a T15 failure that is a product defect must be fixed under a **new candidate** — Task 1 again — before later batches run).

---

### Task 5: Closure — tickets, defects, push

**Files:** none new.

- [ ] **Step 1: Confirm the four ledgers and the pins**

```bash
R=docs/grillstorm/meta-intent/replan-2
for T in T15 T16 T17 T18; do python3 -c "
import json;d=json.load(open('$R/$T/results.json'));c=d['required_cells']
print('$T', 'passed', sum(x['status']=='passed' for x in c), 'unverified', sum(x['status']!='passed' for x in c), 'of', len(c))"; done
for T in T15 T16 T17 T18; do python3 -m pytest -q $R/$T/test_results_pin.py 2>&1 | tail -1; done
```

- [ ] **Step 2: File a defect for every failed criterion (not for environment-unverifiable ones)**

For each evaluation whose `criteria[]` contains a `"verdict": "fail"`, create one issue per distinct defect (dedupe across hosts and scenes by the `defects[]` text):

```bash
gh issue create --label needs-triage --title "meta-intent <T>/<scene> (<host>): <first defect sentence>" --body "$(cat <<'EOF'
Found by the blind host campaign. Candidate <sha>, cell <T>/<host>/<scene>, evaluation: docs/grillstorm/meta-intent/replan-2/campaign/<T>-evaluations/<host>-<scene>.md

Failed criterion: <quoted>
Evidence: <transcript quote>
Minimal reproduction: <from defects[]>
EOF
)"
```

Record each new issue number in the cell's `attempts[-1].defect`.

- [ ] **Step 3: Close only what the ledgers prove**

A thought-test ticket (#15–#18) closes when **every** cell of its batch is `passed` on **both** hosts. A cell `unverified` for an environment reason keeps the ticket open by the ticket's own rule ("未解决失败或环境无法验证须保持未完成并明确原因"); say which cells and why in the comment.

```bash
# for a fully green batch, e.g. T15 ↔ #15:
gh issue close 15 --comment "All 14 cells (7 scenarios × Claude, Codex) passed on candidate <sha>; ledger docs/grillstorm/meta-intent/replan-2/T15/results.json, per-cell evaluations under campaign/T15-evaluations/. Evaluator held criteria privately; actors received only actor-input.md."
# for a batch with open cells:
gh issue comment 15 --body "Campaign on candidate <sha>: <N>/14 passed. Open cells: <host/scene — reason> … Ticket stays open per its closure rule."
```

The implementation tickets #9–#14 stay open on their two host-parity criteria until the batch that exercises them is fully green: #9/#10 ↔ T15, #11 ↔ T16, #12/#13 ↔ T17, #14 ↔ T18. When that batch closes, append to the ticket's audit record (`docs/grillstorm/meta-intent/audit/<nn>-audit.md`) the two host rows as `PASS (T<n> ledger, both hosts)` and close it with the record.

- [ ] **Step 4: Parent comment and push**

```bash
gh issue comment 8 --body "Host campaign on candidate <sha>: T15 <n>/14, T16 <n>/14, T17 <n>/16, T18 <n>/16 passed on both hosts. Closed: <list>. Open with reasons: <list>. Defects filed: <list>."
git fetch -q origin && test "$(git log --oneline HEAD..origin/main | wc -l)" = 0 && git push -q origin main
```

---

## Self-Review

**Spec coverage.** Each ticket's closure clause maps to a step: blind delivery (Task 2 `SPEC` is the packet verbatim; Task 4 Step 4 evaluator never sees the actor's session); both hosts actually executed with platform/version/session recorded (Task 4 Steps 2–3 via `receipt.json` + `admit_evidence.py`, `unverified` never borrows the other host); evaluator holds criteria privately and judges behaviour, not keywords (Task 3 template rules, Task 4 Step 4); isolated fixtures and synthetic data (Task 1 export, `project/` folders); failures get minimal repro and a defect issue, deduped (Task 5 Step 2); fixes need a new candidate and re-runs of affected cells (Task 4 closing note); nothing closes with unresolved or environment-unverifiable cells (Task 5 Step 3). The #9–#14 host-parity rows are closed only from a fully green batch (Task 5 Step 3).

**Placeholder scan.** `<N>`, `<M>`, `<sha>`, `<host/scene — reason>` in Task 4 Step 6 and Task 5 are values read off the ledger at run time, each with the command that produces them; no "TBD". Every Orca verb is copied from the version-matched guide fetched in this session (`run-create`, `worker-start --spec --worktree current --agent`, `check --wait --types --timeout-ms`, `reply --id --body`, `check --ack`, `worker-show --dispatch`). One assumption is flagged rather than hidden: the exact JSON keys `worker-start` returns for the dispatch id are read with a fallback (`dispatch_id` or `dispatch.id`) in `launch_cell.sh`; the first real launch confirms which.

**Type consistency.** `turns.json` is `{"turns": [...]}` in Task 2's tests, `answer_loop.py`, and `extract_turns.py`; `next_action` returns the same key set in every branch; cell status vocabulary is `passed`/`unverified` in the evaluator template, the ledger writer and the pin test; `packet_root`/`source_commit`/`candidate_tree_sha256` are the `results.json` keys Task 1 writes and Tasks 2–5 read.
