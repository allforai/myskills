#!/usr/bin/env python3
"""megastorm §1.6 deterministic execution runner (Codex port).

Replaces Claude Code's Workflow control flow with plain Python. Scheduling is a
DEPENDENCY-READY loop, NOT layer barriers: a task runs as soon as every id in its
`effective_deps` is supervisor-confirmed. Every ready task dispatches immediately —
tasks are LLM (`codex exec`) calls, not machine-bound work, so the default in-flight
cap is UNBOUNDED; pass --max-workers only when tasks run machine-heavy local work
(a single slow task never stalls its siblings — in a real 277-task run, layer
barriers idled most of the fleet). Mutex discipline
preserves serial semantics: at most ONE in-flight task per `isolate_groups` entry
and per `resource_groups` entry (file- or shared-physical-resource collisions),
members preferred in declaration order. Isolate-group members run one git worktree
per task, merged back only after the supervisor confirms. Executor and supervisor
are independent `codex exec` processes — the supervisor never sees the executor's
narrative, only the task + repo, and reruns acceptance_cmd itself.

Escalation in the execution phase does NOT halt the line (unlike Phase 1.1–1.5):
the failure is recorded, its transitive dependents are skipped, and the ready-set
loop keeps running everything else. The full ledger surfaces at close.

The soft-retry budget (initial attempt + <=2 retries) is enforced by an
in-process ledger and a persistent state file — this runner exists because a
stateless prose loop drifts. NO automatic model downgrade: models.json is
resolved and frozen by the human in Phase 0; a model failure here is an
escalation, never a silent substitution.

Usage:
  python3 run_layers.py orchestration.json all-tasks.json \
      --models models.json --prompts ../prompts --root /path/to/repo \
      [--state .megastorm-state.json] [--report execution-report.json] \
      [--max-workers N] [--isolation groups|all] [--codex-template '...'] [--dry-run]

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

# Heuristic for machine-heavy acceptance commands: with the default unbounded
# concurrency these can thrash the local machine, so we warn (never auto-cap).
HEAVY_CMD_RE = re.compile(
    r"\b(docker|make|cmake|bazel|mvn|gradle|webpack|tsc"
    r"|cargo\s+build|go\s+build|npm\s+run\s+build|yarn\s+build|pnpm\s+build)\b",
    re.IGNORECASE)

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
        # stdin MUST be closed: codex exec blocks on "Reading additional input
        # from stdin..." forever when handed an open pipe with no data.
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL)
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


def safety_commit(repo, message):
    """Commit anything pending in `repo`. The runner NEVER relies on executors
    committing their own work — an uncommitted main tree poisons every later
    worktree branch/merge (untracked files 'would be overwritten by merge')."""
    _git(["add", "-A"], repo)
    if _git(["diff", "--cached", "--quiet"], repo).returncode != 0:
        _git(["commit", "-m", message], repo)


def run_task_in_worktree(task, runner, models, root, prompts_dir, merge_lock, log=print):
    """Isolate one file-colliding task in its own worktree; merge back only
    after the supervisor confirms done. Merge conflicts escalate to the human."""
    tid = task["id"]
    branch = f"megastorm/{tid}"
    wt = tempfile.mkdtemp(prefix=f"ms-{tid}-")
    with merge_lock:
        # main tree must be committed BEFORE branching: concurrent free tasks
        # leave uncommitted files, and a worktree branched without them will
        # re-create the same paths and collide on merge.
        safety_commit(root, f"megastorm: pre-worktree snapshot before {tid}")
        r = _git(["worktree", "add", "-b", branch, wt, "HEAD"], root)
    if r.returncode != 0:
        return {"task_id": tid, "status": "escalate", "retries": 0,
                "reason": f"worktree add failed: {r.stderr.strip()[-300:]}"}
    try:
        result = run_task(task, runner, models, wt, prompts_dir, log)
        if result["status"] != "done":
            return result
        safety_commit(wt, f"megastorm: {tid}")
        with merge_lock:  # git index/HEAD ops on the main tree must serialize
            safety_commit(root, f"megastorm: main-tree snapshot before merging {tid}")
            m = _git(["merge", "--no-ff", "--no-edit", branch], root)
            if m.returncode != 0:
                _git(["merge", "--abort"], root)
                detail = (m.stderr.strip() + " " + m.stdout.strip()).strip()
                return {"task_id": tid, "status": "escalate", "retries": result["retries"],
                        "reason": f"merge conflict on {branch}: {detail[-300:]}"}
        return result
    finally:
        _git(["worktree", "remove", "--force", wt], root)
        _git(["branch", "-D", branch], root)


# ---------- ready-set scheduling ----------

def schedule(effective_deps, isolate_groups, resource_groups, tasks_by_id,
             run_free, run_isolated, completed, max_workers=0, log=print,
             on_progress=None):
    """Dependency-ready scheduler. A task is READY when every id in its
    `effective_deps` is in `completed`. Ready tasks dispatch up to `max_workers`
    in flight (0 = unbounded: every ready task dispatches at once); when one
    confirms, the ready set is recomputed and slots refill. No layer barriers.

    Mutex: at most one in-flight task per isolate_groups / resource_groups entry,
    members preferred in declaration (task) order. Isolate-group members run via
    `run_isolated` (worktree); everyone else via `run_free`.

    Escalation semantics: a task that escalates is recorded, its transitive
    dependents (forward over effective_deps) are marked skipped and never
    dispatched, and the loop keeps running the rest. Returns
    (results, escalations, skipped) where skipped maps task_id -> blocking id.
    on_progress(completed) fires after every terminal task."""
    all_ids = list(tasks_by_id)  # declaration order
    mutex_sets = [set(g) for g in isolate_groups] + \
                 [set(v) for v in resource_groups.values()]
    isolate_members = {tid for g in isolate_groups for tid in g}

    dependents = {tid: [] for tid in all_ids}
    for tid in all_ids:
        for d in effective_deps.get(tid, []):
            dependents.setdefault(d, []).append(tid)

    results, escalations = [], []
    skipped = {}            # tid -> the escalated/skipped dep that blocked it
    escalated = set()       # tids that escalated outright
    in_flight = set()
    cond = threading.Condition()

    def _propagate_skip(failed):
        stack = list(dependents.get(failed, []))
        while stack:
            d = stack.pop()
            if d in completed or d in escalated or d in skipped or d in in_flight:
                continue
            skipped[d] = failed
            stack.extend(dependents.get(d, []))

    def _deps_ok(tid):
        return all(d in completed for d in effective_deps.get(tid, []))

    def _mutex_free(tid):
        return all(tid not in s or not (s & in_flight) for s in mutex_sets)

    def _pick(cap):
        """Under cond: reserve and return ready, mutex-free tids up to the cap.
        Declaration-order scan → within a mutex set the earliest ready member is
        reserved first, which blocks its siblings for this wave."""
        picked = []
        for tid in all_ids:
            if len(in_flight) >= cap:
                break
            if (tid in completed or tid in escalated or tid in skipped
                    or tid in in_flight):
                continue
            if not _deps_ok(tid) or not _mutex_free(tid):
                continue
            in_flight.add(tid)
            picked.append(tid)
        return picked

    def _work(tid):
        fn = run_isolated if tid in isolate_members else run_free
        res = fn(tasks_by_id[tid])
        with cond:
            in_flight.discard(tid)
            results.append(res)
            if res["status"] == "done":
                completed.add(tid)
            else:
                escalated.add(tid)
                escalations.append(res)
                _propagate_skip(tid)
            if on_progress:
                on_progress(set(completed))
            cond.notify_all()

    def _terminal_count():
        return len(completed) + len(escalated) + len(skipped)

    cap = max_workers or max(len(all_ids), 1)
    with ThreadPoolExecutor(max_workers=cap) as ex:
        with cond:
            while _terminal_count() < len(all_ids):
                picked = _pick(cap)
                for tid in picked:
                    g = "" if tid not in isolate_members else " [isolated]"
                    log(f"dispatch {tid}{g} "
                        f"({_terminal_count()}/{len(all_ids)} terminal, "
                        f"{len(in_flight)} in flight)")
                    ex.submit(_work, tid)
                if not picked:
                    if not in_flight:
                        break  # nothing runnable and nothing running — done/stuck
                    cond.wait()
    if skipped:
        log(f"skipped {len(skipped)} task(s) blocked by escalations: "
            f"{sorted(skipped)}")
    return results, escalations, skipped


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
    ap.add_argument("--max-workers", type=int, default=0,
                    help="in-flight cap; 0 (default) = unbounded — dispatch every "
                         "ready task at once (tasks are LLM calls, not machine-"
                         "bound). Set a number when tasks run machine-heavy local "
                         "work (builds, whole test suites, docker).")
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
    if not args.max_workers:
        heavy = [t["id"] for t in tasks
                 if HEAVY_CMD_RE.search(t.get("acceptance_cmd") or "")]
        if heavy:
            shown = ", ".join(heavy[:5]) + ("…" if len(heavy) > 5 else "")
            print(f"WARNING: concurrency is unbounded (default) but {len(heavy)} "
                  f"task(s) look machine-heavy ({shown}) — pass --max-workers N "
                  f"to cap local load.")
    models = load_models(args.models)
    prompts_dir = pathlib.Path(args.prompts)
    root = pathlib.Path(args.root).resolve()

    try:
        completed = set(json.loads(open(args.state).read()).get("completed", []))
    except (OSError, ValueError):
        completed = set()
    if completed:
        print(f"resuming: {len(completed)} task(s) already done per {args.state}")

    effective_deps = orch.get("effective_deps")
    if effective_deps is None:  # tolerate an old DAG file by deriving from depends_on
        effective_deps = {t["id"]: list(t.get("depends_on") or []) for t in tasks}
    isolate_groups = orch.get("isolate_groups", [])
    resource_groups = orch.get("resource_groups", {})
    if args.isolation == "all":
        isolate_groups = [[t["id"]] for t in tasks]

    if args.dry_run:
        done = set(completed)
        wave = 0
        while len(done) < len(tasks_by_id):
            ready = [t for t in tasks_by_id if t not in done
                     and all(d in done for d in effective_deps.get(t, []))]
            if not ready:
                print(f"(unreachable: {sorted(set(tasks_by_id) - done)})")
                break
            print(f"wave {wave}: {ready}")
            done |= set(ready)
            wave += 1
        print(f"isolate_groups={isolate_groups} resource_groups={resource_groups}")
        return 0

    runner = CodexRunner(args.codex_template)
    merge_lock = threading.Lock()

    def run_free(task):
        res = run_task(task, runner, models, root, prompts_dir)
        if res["status"] == "done":
            with merge_lock:  # concurrent free tasks must not race git index ops
                safety_commit(root, f"megastorm: {task['id']}")
        return res

    def run_isolated(task):
        return run_task_in_worktree(task, runner, models, root, prompts_dir, merge_lock)

    def persist_state(done_set):
        json.dump({"completed": sorted(done_set)}, open(args.state, "w"), indent=2)

    results, escalations, skipped = schedule(
        effective_deps, isolate_groups, resource_groups, tasks_by_id,
        run_free, run_isolated, completed, args.max_workers,
        on_progress=persist_state)

    persist_state(completed)
    json.dump({"results": results, "escalations": escalations,
               "skipped": skipped, "completed": sorted(completed),
               "total_tasks": len(tasks_by_id)}, open(args.report, "w"),
              indent=2, ensure_ascii=False)
    if escalations:
        print(f"ESCALATE: {len(escalations)} task(s) need a human decision; "
              f"{len(skipped)} dependent(s) skipped — see {args.report}")
        for e in escalations:
            print(f"  - {e['task_id']}: {e['reason']}")
        return 1
    print(f"ALL DONE: {len(completed)}/{len(tasks_by_id)} tasks confirmed by supervisor")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
