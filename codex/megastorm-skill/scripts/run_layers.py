#!/usr/bin/env python3
"""megastorm §1.6 deterministic execution runner (Codex port).

Replaces Claude Code's Workflow control flow with plain Python: process DAG
layers in order; within a layer, non-colliding tasks run concurrently while
each isolate group runs sequentially, one git worktree per task, merged back
only after the supervisor confirms. Executor and supervisor are independent
`codex exec` processes — the supervisor never sees the executor's narrative,
only the task + repo, and reruns acceptance_cmd itself (anti-fake-completion).

The soft-retry budget (initial attempt + <=2 retries) is enforced by an
in-process ledger and a persistent state file — this runner exists because a
stateless prose loop drifts. NO automatic model downgrade: models.json is
resolved and frozen by the human in Phase 0; a model failure here is an
escalation, never a silent substitution.

Usage:
  python3 run_layers.py orchestration.json all-tasks.json \
      --models models.json --prompts ../prompts --root /path/to/repo \
      [--state .megastorm-state.json] [--report execution-report.json] \
      [--max-workers 4] [--isolation groups|all] [--codex-template '...'] [--dry-run]

Exit 0 = all tasks done. Exit 1 = escalation(s) — render report to the human.
"""
import argparse
import json
import re
import shlex
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor

SOFT_RETRY_BUDGET = 2  # initial attempt + at most 2 retries = 3 dispatches total

ANTI_VACUOUS = (
    "IMPORTANT: the previous acceptance run passed only because it selected tests "
    "by name and matched 0 (a vacuous pass). Create the named test with >=1 real "
    "assertion and confirm a non-zero executed-test count before declaring done."
)

DEFAULT_CODEX_TEMPLATE = (
    "codex exec --sandbox workspace-write -m {model} --cd {cwd} "
    "--output-last-message {out}"
)


# ---------- verdict parsing ----------

def parse_verdict(text):
    """Extract the supervisor's JSON verdict from a final message. Tries the
    whole text, then fenced blocks, then the last {...} span. None = unparseable."""
    if not text:
        return None
    candidates = [text.strip()]
    candidates += re.findall(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    spans = re.findall(r"\{.*\}", text, re.DOTALL)
    if spans:
        candidates.append(spans[-1])
    for c in reversed(candidates):  # prefer the most specific extraction
        try:
            obj = json.loads(c)
            if isinstance(obj, dict) and "done" in obj:
                return obj
        except (ValueError, TypeError):
            continue
    return None


# ---------- prompt assembly ----------

def build_executor_prompt(prompts_dir, task, feedback=None):
    base = (prompts_dir / "executor.md").read_text()
    parts = [base, "\n## Your task (JSON)\n", json.dumps(task, ensure_ascii=False, indent=2)]
    if feedback:
        parts += ["\n## Supervisor feedback on your previous attempt\n", feedback]
    return "".join(parts)


def build_supervisor_prompt(prompts_dir, task):
    """The supervisor gets ONLY the task definition — never the executor's
    narrative or self-report (independence is the anti-fake-completion root)."""
    base = (prompts_dir / "supervisor.md").read_text()
    return "".join([
        base,
        "\n## Task to verify (JSON)\n", json.dumps(task, ensure_ascii=False, indent=2),
        "\n\nRerun the acceptance_cmd yourself in the current repo and end your "
        "final message with EXACTLY one JSON verdict object per the schema.",
    ])


# ---------- agent invocation ----------

class CodexRunner:
    """Spawns one headless `codex exec` per call. Template is overridable so a
    codex CLI flag rename never bricks the runner (same upgrade-proof stance as
    the model tiers)."""

    def __init__(self, template=DEFAULT_CODEX_TEMPLATE):
        self.template = template

    def run(self, prompt, model, cwd):
        with tempfile.NamedTemporaryFile("r", suffix=".txt", delete=False) as f:
            out_path = f.name
        cmd = shlex.split(self.template.format(model=model, cwd=str(cwd), out=out_path))
        cmd.append(prompt)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        try:
            last = open(out_path).read().strip()
        except OSError:
            last = ""
        if not last:
            last = proc.stdout.strip()
        if proc.returncode != 0 and not last:
            raise RuntimeError(f"codex exec failed (exit {proc.returncode}): {proc.stderr[-500:]}")
        return last


# ---------- single-task execute + supervise loop ----------

def run_task(task, runner, models, cwd, prompts_dir, log=print):
    """Execute one task with adversarial supervision and the soft-retry budget.
    Returns {task_id, status: 'done'|'escalate', retries, verdict?, reason?}."""
    tid = task["id"]
    retries = 0
    feedback = None
    while True:
        log(f"[{tid}] executor attempt {retries + 1} (model={models['bulk']})")
        runner.run(build_executor_prompt(prompts_dir, task, feedback), models["bulk"], cwd)
        log(f"[{tid}] supervisor verify (model={models['verify']}, fresh context)")
        verdict = None
        for _ in range(2):  # one re-ask on unparseable output
            raw = runner.run(build_supervisor_prompt(prompts_dir, task), models["verify"], cwd)
            verdict = parse_verdict(raw)
            if verdict is not None:
                break
        if verdict is None:
            return {"task_id": tid, "status": "escalate", "retries": retries,
                    "reason": "supervisor verdict unparseable twice"}
        if verdict.get("done") is True:
            return {"task_id": tid, "status": "done", "retries": retries, "verdict": verdict}
        pieces = [verdict.get("refutation") or verdict.get("evidence") or "acceptance_cmd failed"]
        if verdict.get("vacuous"):
            pieces.append(ANTI_VACUOUS)
        feedback = "\n".join(pieces)
        if retries >= SOFT_RETRY_BUDGET:
            return {"task_id": tid, "status": "escalate", "retries": retries,
                    "reason": "soft-retry budget exhausted", "verdict": verdict}
        retries += 1


# ---------- git worktree isolation ----------

def _git(args, cwd):
    return subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True, text=True)


def run_task_in_worktree(task, runner, models, root, prompts_dir, merge_lock, log=print):
    """Isolate one file-colliding task in its own worktree; merge back only
    after the supervisor confirms done. Merge conflicts escalate to the human."""
    tid = task["id"]
    branch = f"megastorm/{tid}"
    wt = tempfile.mkdtemp(prefix=f"ms-{tid}-")
    r = _git(["worktree", "add", "-b", branch, wt, "HEAD"], root)
    if r.returncode != 0:
        return {"task_id": tid, "status": "escalate", "retries": 0,
                "reason": f"worktree add failed: {r.stderr.strip()[-300:]}"}
    try:
        result = run_task(task, runner, models, wt, prompts_dir, log)
        if result["status"] != "done":
            return result
        # safety-commit anything the executor left uncommitted, then merge
        _git(["add", "-A"], wt)
        if _git(["diff", "--cached", "--quiet"], wt).returncode != 0:
            _git(["commit", "-m", f"megastorm: {tid}"], wt)
        with merge_lock:  # git index/HEAD ops on the main tree must serialize
            m = _git(["merge", "--no-ff", "--no-edit", branch], root)
            if m.returncode != 0:
                _git(["merge", "--abort"], root)
                return {"task_id": tid, "status": "escalate", "retries": result["retries"],
                        "reason": f"merge conflict on {branch}: {m.stdout.strip()[-300:]}"}
        return result
    finally:
        _git(["worktree", "remove", "--force", wt], root)
        _git(["branch", "-D", branch], root)


# ---------- layer scheduling ----------

def schedule(layers, isolate_groups, tasks_by_id, run_free, run_isolated,
             completed, max_workers=4, log=print):
    """Process layers in DAG order. Within a layer: free tasks run concurrently;
    each isolate group runs sequentially (its own thread). Any escalation
    finishes the current layer then stops. Returns (results, escalations)."""
    grouped = {tid for g in isolate_groups for tid in g}
    results, escalations = [], []
    lock = threading.Lock()

    def record(res):
        with lock:
            results.append(res)
            if res["status"] == "done":
                completed.add(res["task_id"])
            else:
                escalations.append(res)

    for li, layer in enumerate(layers):
        pending = [tid for tid in layer if tid not in completed]
        if not pending:
            continue
        log(f"=== layer {li + 1}/{len(layers)}: {pending}")
        jobs = []
        layer_set = set(pending)
        for g in isolate_groups:
            members = [tid for tid in g if tid in layer_set]
            if members:
                def group_job(ms=members):
                    for tid in ms:  # sequential within the group, declaration order
                        res = run_isolated(tasks_by_id[tid])
                        record(res)
                        if res["status"] != "done":
                            return  # don't pile more work on a broken group
                jobs.append(group_job)
        for tid in pending:
            if tid not in grouped:
                jobs.append(lambda t=tid: record(run_free(tasks_by_id[t])))
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            for f in [ex.submit(j) for j in jobs]:
                f.result()
        if escalations:
            log(f"escalation(s) in layer {li + 1} — stopping before next layer")
            break
    return results, escalations


# ---------- entry ----------

def load_models(path):
    models = json.loads(open(path).read())
    for k in ("think", "verify", "bulk"):
        v = models.get(k, "")
        if not v or v.startswith("REPLACE"):
            sys.exit(f"models.json: '{k}' not resolved — Phase 0 must freeze real "
                     f"model names with the human (no automatic resolution).")
    return models


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("orchestration")
    ap.add_argument("tasks")
    ap.add_argument("--models", required=True)
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--root", default=".")
    ap.add_argument("--state", default=".megastorm-state.json")
    ap.add_argument("--report", default="execution-report.json")
    ap.add_argument("--max-workers", type=int, default=4)
    ap.add_argument("--isolation", choices=["groups", "all"], default="groups",
                    help="'all' worktree-isolates every task (safer when executors "
                         "git-commit concurrently in the main tree)")
    ap.add_argument("--codex-template", default=DEFAULT_CODEX_TEMPLATE)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the schedule without invoking codex")
    args = ap.parse_args(argv[1:])

    import pathlib
    orch = json.loads(open(args.orchestration).read())
    tasks = json.loads(open(args.tasks).read())
    if isinstance(tasks, dict):
        tasks = tasks.get("tasks", [])
    tasks_by_id = {t["id"]: t for t in tasks}
    models = load_models(args.models)
    prompts_dir = pathlib.Path(args.prompts)
    root = pathlib.Path(args.root).resolve()

    try:
        completed = set(json.loads(open(args.state).read()).get("completed", []))
    except (OSError, ValueError):
        completed = set()
    if completed:
        print(f"resuming: {len(completed)} task(s) already done per {args.state}")

    if args.dry_run:
        grouped = {tid for g in orch.get("isolate_groups", []) for tid in g}
        for li, layer in enumerate(orch["layers"]):
            pend = [t for t in layer if t not in completed]
            print(f"layer {li + 1}: free={[t for t in pend if t not in grouped]} "
                  f"isolated={[t for t in pend if t in grouped]}")
        return 0

    runner = CodexRunner(args.codex_template)
    merge_lock = threading.Lock()
    isolate_groups = orch.get("isolate_groups", [])
    if args.isolation == "all":
        isolate_groups = [[t["id"]] for t in tasks]

    def run_free(task):
        return run_task(task, runner, models, root, prompts_dir)

    def run_isolated(task):
        return run_task_in_worktree(task, runner, models, root, prompts_dir, merge_lock)

    results, escalations = schedule(
        orch["layers"], isolate_groups, tasks_by_id, run_free, run_isolated,
        completed, args.max_workers)

    json.dump({"completed": sorted(completed)}, open(args.state, "w"), indent=2)
    json.dump({"results": results, "escalations": escalations,
               "completed": sorted(completed),
               "total_tasks": len(tasks_by_id)}, open(args.report, "w"),
              indent=2, ensure_ascii=False)
    if escalations:
        print(f"ESCALATE: {len(escalations)} task(s) need a human decision — see {args.report}")
        for e in escalations:
            print(f"  - {e['task_id']}: {e['reason']}")
        return 1
    print(f"ALL DONE: {len(completed)}/{len(tasks_by_id)} tasks confirmed by supervisor")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
