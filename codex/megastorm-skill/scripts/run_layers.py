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
members preferred in declaration order. Every task runs in a task worktree and merges
into a run-owned integration worktree/ref; the user's checkout is never staged or
modified. Executor and supervisor
are independent `codex exec` processes — the supervisor never sees the executor's
narrative, only the task + repo, and reruns acceptance_cmd itself.

Escalation in the execution phase does NOT halt the line (unlike Phase 1.1–1.5):
the failure is recorded, its transitive dependents are skipped, and the ready-set
loop keeps running everything else. The full ledger surfaces at close.

Business soft retries (initial + <=2) and infrastructure retries are separate.
Reality-gated environmental proof becomes pending without blocking merged dependents.
Atomic state plus a fsynced JSONL event trail exists because a
stateless prose loop drifts. NO automatic model downgrade: models.json is
resolved and frozen by the human in Phase 0; a model failure never causes silent substitution.

Usage:
  python3 run_layers.py orchestration.json all-tasks.json \
      --models models.json --prompts ../prompts --root /path/to/repo \
      [--state .megastorm-state.json] [--report execution-report.json] \
      [--max-workers N] [--codex-template '...'] [--agent-timeout SEC] [--dry-run]

Exit 0 = all tasks done. Exit 1 = escalation(s) — render report to the human.
"""
import argparse
import hashlib
import json
import os
import pathlib
import re
import signal
import shlex
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

SOFT_RETRY_BUDGET = 2  # initial attempt + at most 2 retries = 3 dispatches total
INFRA_RETRY_BUDGET = 2  # initial attempt + two infrastructure redispatches
DEFAULT_AGENT_TIMEOUT = 1800

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
    "codex exec --ephemeral --sandbox workspace-write -m {model} --cd {cwd} "
    "--output-last-message {out}"
)
BASE_ENV_KEYS = {"PATH", "HOME", "CODEX_HOME", "TMPDIR", "LANG", "LC_ALL", "TERM",
                 "SHELL", "SSL_CERT_FILE", "SSL_CERT_DIR", "HTTP_PROXY", "HTTPS_PROXY",
                 "NO_PROXY"}


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

class InfrastructureFailure(RuntimeError):
    """Agent transport/process failure, distinct from a task business failure."""


class CodexRunner:
    """Spawns one headless `codex exec` per call. Template is overridable so a
    codex CLI flag rename never bricks the runner (same upgrade-proof stance as
    the model tiers)."""

    def __init__(self, template=DEFAULT_CODEX_TEMPLATE, timeout=DEFAULT_AGENT_TIMEOUT,
                 allow_env=()):
        self.template = template
        self.timeout = timeout
        keys = BASE_ENV_KEYS | set(allow_env)
        self.env = {key: value for key, value in os.environ.items() if key in keys}

    def run(self, prompt, model, cwd):
        with tempfile.NamedTemporaryFile("r", suffix=".txt", delete=False) as f:
            out_path = f.name
        cmd = shlex.split(self.template.format(model=model, cwd=str(cwd), out=out_path))
        cmd.append(prompt)
        # stdin MUST be closed: codex exec blocks on "Reading additional input
        # from stdin..." forever when handed an open pipe with no data.
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, stdin=subprocess.DEVNULL,
                                start_new_session=True, env=self.env)
        try:
            stdout, stderr = proc.communicate(timeout=self.timeout)
        except subprocess.TimeoutExpired as exc:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                stdout, stderr = proc.communicate()
            raise InfrastructureFailure(f"codex exec timed out after {self.timeout}s") from exc
        try:
            last = open(out_path).read().strip()
        except OSError:
            last = ""
        if not last:
            last = stdout.strip()
        if proc.returncode != 0 and not last:
            raise InfrastructureFailure(
                f"codex exec failed (exit {proc.returncode}): {stderr[-500:]}")
        return last


# ---------- single-task execute + supervise loop ----------

def run_task(task, runner, models, cwd, prompts_dir, log=print):
    """Execute one task with adversarial supervision and the soft-retry budget.
    Returns {task_id, status: 'done'|'escalate', retries, verdict?, reason?}."""
    tid = task["id"]
    retries = 0
    infra_retries = 0
    feedback = None
    while True:
        log(f"[{tid}] executor attempt {retries + 1} (model={models['bulk']})")
        try:
            runner.run(build_executor_prompt(prompts_dir, task, feedback), models["bulk"], cwd)
        except (InfrastructureFailure, OSError, subprocess.SubprocessError) as exc:
            if infra_retries >= INFRA_RETRY_BUDGET:
                return {"task_id": tid, "status": "escalate", "retries": retries,
                        "infra_retries": infra_retries, "failure_kind": "infrastructure",
                        "reason": str(exc)}
            infra_retries += 1
            log(f"[{tid}] infrastructure retry {infra_retries}: {exc}")
            continue
        log(f"[{tid}] supervisor verify (model={models['verify']}, fresh context)")
        verdict = None
        for _ in range(2):  # one re-ask on unparseable output
            try:
                raw = runner.run(build_supervisor_prompt(prompts_dir, task), models["verify"], cwd)
            except (InfrastructureFailure, OSError, subprocess.SubprocessError) as exc:
                if infra_retries >= INFRA_RETRY_BUDGET:
                    return {"task_id": tid, "status": "escalate", "retries": retries,
                            "infra_retries": infra_retries,
                            "failure_kind": "infrastructure", "reason": str(exc)}
                infra_retries += 1
                log(f"[{tid}] infrastructure retry {infra_retries}: {exc}")
                verdict = "retry-infrastructure"
                break
            verdict = parse_verdict(raw)
            if verdict is not None:
                break
        if verdict == "retry-infrastructure":
            continue
        if verdict is None:
            return {"task_id": tid, "status": "escalate", "retries": retries,
                    "infra_retries": infra_retries,
                    "reason": "supervisor verdict unparseable twice"}
        if verdict.get("done") is True:
            return {"task_id": tid, "status": "done", "retries": retries,
                    "infra_retries": infra_retries, "verdict": verdict}
        if task.get("reality_gate") is True and verdict.get("reality_gated") is True:
            return {"task_id": tid, "status": "reality_gated", "retries": retries,
                    "infra_retries": infra_retries, "verdict": verdict,
                    "reason": verdict.get("evidence", "environmental proof unavailable"),
                    "runbook_ptr": task.get("runbook_ptr")}
        pieces = [verdict.get("refutation") or verdict.get("evidence") or "acceptance_cmd failed"]
        if verdict.get("vacuous"):
            pieces.append(ANTI_VACUOUS)
        feedback = "\n".join(pieces)
        if retries >= SOFT_RETRY_BUDGET:
            return {"task_id": tid, "status": "escalate", "retries": retries,
                    "infra_retries": infra_retries,
                    "failure_kind": "business",
                    "reason": "soft-retry budget exhausted", "verdict": verdict}
        retries += 1


# ---------- git worktree isolation ----------

def _git(args, cwd):
    return subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True, text=True)


def safety_commit(repo, message):
    """Commit pending content inside a runner-owned task/integration worktree.
    Main execution never calls this on the user's checked-out worktree."""
    _git(["add", "-A"], repo)
    if _git(["diff", "--cached", "--quiet"], repo).returncode != 0:
        _git(["commit", "-m", message], repo)


def changed_paths(repo, base_commit):
    committed = _git(["diff", "--name-only", f"{base_commit}..HEAD"], repo)
    working = _git(["status", "--porcelain", "--untracked-files=all"], repo)
    paths = set(committed.stdout.splitlines())
    for line in working.stdout.splitlines():
        raw = line[3:] if len(line) > 3 else ""
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        if raw:
            paths.add(raw.strip('"'))
    return sorted(p for p in paths if p)


def undeclared_paths(actual, declared):
    """Return repository-relative changes outside exact declared files/dirs."""
    normalized = [p.strip().rstrip("/") for p in declared if isinstance(p, str)]
    bad = []
    for path in actual:
        if path.startswith("/") or ".." in pathlib.PurePosixPath(path).parts:
            bad.append(path)
            continue
        if not any(path == d or path.startswith(d + "/") for d in normalized):
            bad.append(path)
    return bad


def run_task_in_worktree(task, runner, models, root, prompts_dir, merge_lock, log=print,
                         branch_prefix="megastorm", enforce_paths=False):
    """Isolate one file-colliding task in its own worktree; merge back only
    after the supervisor confirms done. Merge conflicts escalate to the human."""
    tid = task["id"]
    safe_tid = re.sub(r"[^A-Za-z0-9._-]", "-", tid)
    branch = f"{branch_prefix}/{safe_tid}"
    wt = tempfile.mkdtemp(prefix=f"ms-{tid}-")
    with merge_lock:
        # The runner-owned integration worktree must be clean before branching.
        safety_commit(root, f"megastorm: pre-worktree snapshot before {tid}")
        r = _git(["worktree", "add", "-b", branch, wt, "HEAD"], root)
    if r.returncode != 0:
        return {"task_id": tid, "status": "escalate", "retries": 0,
                "reason": f"worktree add failed: {r.stderr.strip()[-300:]}"}
    try:
        base = _git(["rev-parse", "HEAD"], wt).stdout.strip()
        result = run_task(task, runner, models, wt, prompts_dir, log)
        if result["status"] not in ("done", "reality_gated"):
            return result
        actual = changed_paths(wt, base)
        outside = undeclared_paths(actual, task.get("touched_paths", []))
        result["actual_touched_paths"] = actual
        if enforce_paths and outside:
            return {"task_id": tid, "status": "escalate",
                    "retries": result.get("retries", 0),
                    "failure_kind": "scope",
                    "reason": f"task modified undeclared paths: {outside}",
                    "actual_touched_paths": actual}
        safety_commit(wt, f"megastorm: {tid}")
        marker = ("megastorm-reality-gated" if result["status"] == "reality_gated"
                  else "megastorm-confirmed")
        marked = _git(["commit", "--allow-empty", "-m", f"{marker}: {tid}"], wt)
        if marked.returncode != 0:
            return {"task_id": tid, "status": "escalate",
                    "retries": result.get("retries", 0), "failure_kind": "git",
                    "reason": f"cannot write confirmation marker: {marked.stderr.strip()}"}
        with merge_lock:  # integration-worktree index/HEAD ops must serialize
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
             on_progress=None, on_event=None):
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
            if res["status"] in ("done", "reality_gated"):
                completed.add(tid)
                if on_event:
                    on_event("task_terminal", task_id=tid, status=res["status"], result=res)
            else:
                escalated.add(tid)
                escalations.append(res)
                _propagate_skip(tid)
                if on_event:
                    on_event("task_terminal", task_id=tid, status="escalated", result=res)
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
                    if on_event:
                        on_event("task_dispatched", task_id=tid,
                                 isolated=tid in isolate_members)
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


def atomic_write_json(path, value):
    """Publish a JSON snapshot atomically; never expose a partially written state."""
    path = os.path.abspath(path)
    parent = os.path.dirname(path) or "."
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".megastorm-", suffix=".tmp", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def input_fingerprint(tasks, orchestration, models, prompts_dir):
    payload = {
        "tasks": tasks,
        "orchestration": orchestration,
        "models": models,
        "prompts": {p.name: p.read_text() for p in sorted(prompts_dir.glob("*.md"))},
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class EventLog:
    """Serialized, fsynced JSONL audit events with stable sequence numbers."""

    def __init__(self, path, run_id, start_seq=0):
        self.path = os.path.abspath(path)
        self.run_id = run_id
        self.seq = start_seq
        self.lock = threading.Lock()
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        if os.path.exists(self.path):
            raw = pathlib.Path(self.path).read_bytes()
            valid = []
            for line in raw.splitlines(keepends=True):
                if not line.endswith(b"\n"):
                    pathlib.Path(self.path + ".partial").write_bytes(line)
                    break
                try:
                    event = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    pathlib.Path(self.path + ".partial").write_bytes(line)
                    break
                if event.get("run_id") != run_id:
                    raise ValueError("event log run_id does not match state")
                valid.append(line)
            if b"".join(valid) != raw:
                pathlib.Path(self.path).write_bytes(b"".join(valid))

    def append(self, kind, **payload):
        with self.lock:
            self.seq += 1
            event = {"run_id": self.run_id, "seq": self.seq,
                     "event_id": f"{self.run_id}:{self.seq}",
                     "ts": time.time(), "type": kind, "payload": payload}
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            return event


def prepare_integration_workspace(repo, run_id, prior_state):
    """Create/resume a run-owned detached integration worktree without touching
    the user's checked-out branch, index, or dirty files."""
    ref = f"refs/megastorm/runs/{run_id}/integration"
    baseline_ref = f"refs/megastorm/runs/{run_id}/baseline"
    baseline = prior_state.get("baseline_commit")
    if baseline is None:
        head = _git(["rev-parse", "HEAD"], repo)
        if head.returncode != 0:
            raise RuntimeError(f"cannot resolve repository HEAD: {head.stderr.strip()}")
        baseline = head.stdout.strip()
        for name in (baseline_ref, ref):
            created = _git(["update-ref", name, baseline, ""], repo)
            if created.returncode != 0:
                raise RuntimeError(f"cannot create run ref {name}: {created.stderr.strip()}")
    else:
        actual = _git(["rev-parse", ref], repo)
        if actual.returncode != 0:
            raise RuntimeError(f"missing integration ref for resumed run: {ref}")

    recorded = prior_state.get("integration_path")
    if recorded and pathlib.Path(recorded, ".git").exists():
        return pathlib.Path(recorded), ref, baseline

    run_root = pathlib.Path(tempfile.mkdtemp(prefix=f"megastorm-{run_id[:8]}-"))
    integration = run_root / "integration"
    added = _git(["worktree", "add", "--detach", str(integration), ref], repo)
    if added.returncode != 0:
        raise RuntimeError(f"cannot create integration worktree: {added.stderr.strip()}")
    return integration, ref, baseline


def recover_confirmed_from_git(integration, baseline, task_ids):
    """Recover confirmations committed before a crash but not yet snapshotted."""
    history = _git(["log", "--format=%s", f"{baseline}..HEAD"], integration)
    recovered = {}
    if history.returncode != 0:
        return recovered
    valid = set(task_ids)
    for subject in history.stdout.splitlines():
        for prefix, status in (("megastorm-confirmed: ", "done"),
                               ("megastorm-reality-gated: ", "reality_gated")):
            if subject.startswith(prefix):
                tid = subject[len(prefix):]
                if tid in valid:
                    recovered[tid] = status
    return recovered


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("orchestration")
    ap.add_argument("tasks")
    ap.add_argument("--models", required=True)
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--root", default=".")
    ap.add_argument("--state", default=".megastorm-state.json")
    ap.add_argument("--report", default="execution-report.json")
    ap.add_argument("--events", default=".megastorm-events.jsonl")
    ap.add_argument("--agent-timeout", type=int, default=DEFAULT_AGENT_TIMEOUT)
    ap.add_argument("--allow-env", action="append", default=[], metavar="NAME",
                    help="explicitly expose one additional environment variable to agents; "
                         "repeat as needed (ambient secrets are excluded by default)")
    ap.add_argument("--completeness", choices=["census", "audit", "unknown"],
                    default="unknown")
    ap.add_argument("--census-artifact")
    ap.add_argument("--max-workers", type=int, default=0,
                    help="in-flight cap; 0 (default) = unbounded — dispatch every "
                         "ready task at once (tasks are LLM calls, not machine-"
                         "bound). Set a number when tasks run machine-heavy local "
                         "work (builds, whole test suites, docker).")
    ap.add_argument("--isolation", choices=["groups", "all"], default="all",
                    help="deprecated compatibility option; safe v0.14 execution always "
                         "isolates every writer and never writes the user's main tree")
    ap.add_argument("--codex-template", default=DEFAULT_CODEX_TEMPLATE)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the schedule without invoking codex")
    args = ap.parse_args(argv[1:])
    if args.completeness == "census" and not args.census_artifact:
        ap.error("--completeness census requires --census-artifact")

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
    user_root = pathlib.Path(args.root).resolve()
    user_status = _git(["status", "--porcelain=v1", "--untracked-files=all"], user_root)
    if user_status.returncode != 0:
        sys.exit(f"target is not a readable git repository: {user_status.stderr.strip()}")
    user_dirty_fingerprint = hashlib.sha256(user_status.stdout.encode()).hexdigest()

    try:
        prior_state = json.loads(open(args.state).read())
    except (OSError, ValueError):
        prior_state = {}
    completed = set(prior_state.get("completed", []))
    run_id = prior_state.get("run_id") or str(uuid.uuid4())
    fingerprint = input_fingerprint(tasks, orch, models, prompts_dir)
    old_fingerprint = prior_state.get("input_fingerprint")
    if completed and old_fingerprint != fingerprint:
        sys.exit("state input fingerprint differs — refusing to reuse stale confirmations; "
                 "start a new run with a new --state/--events path")
    events = EventLog(args.events, run_id, prior_state.get("last_event_seq", 0))
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

    # Safe default: every writer gets a task worktree, and all merges target a
    # run-owned integration worktree rather than the user's checked-out tree.
    integration_root, integration_ref, baseline_commit = prepare_integration_workspace(
        user_root, run_id, prior_state)
    recovered = recover_confirmed_from_git(integration_root, baseline_commit, tasks_by_id)
    completed.update(recovered)
    # Preserve original multi-task mutex groups while adding singleton groups so
    # every writer routes through task isolation. Replacing the original groups
    # would accidentally let same-file writers execute concurrently.
    isolate_groups = list(isolate_groups) + [[t["id"]] for t in tasks]

    runner = CodexRunner(args.codex_template, timeout=args.agent_timeout,
                         allow_env=args.allow_env)
    merge_lock = threading.Lock()

    def run_free(task):
        # Kept as a scheduler interface; safe mode routes every task to isolated.
        return run_isolated(task)

    def run_isolated(task):
        result = run_task_in_worktree(
            task, runner, models, integration_root, prompts_dir, merge_lock,
            branch_prefix=f"megastorm-{run_id[:8]}", enforce_paths=True)
        if result["status"] in ("done", "reality_gated"):
            with merge_lock:
                head = _git(["rev-parse", "HEAD"], integration_root)
                if head.returncode != 0:
                    return {"task_id": task["id"], "status": "escalate",
                            "retries": result.get("retries", 0),
                            "failure_kind": "git",
                            "reason": f"cannot resolve integration HEAD: {head.stderr.strip()}"}
                old_ref = _git(["rev-parse", integration_ref], user_root)
                if old_ref.returncode != 0:
                    return {"task_id": task["id"], "status": "escalate",
                            "retries": result.get("retries", 0),
                            "failure_kind": "git",
                            "reason": f"integration ref disappeared: {old_ref.stderr.strip()}"}
                moved = _git(["update-ref", integration_ref, head.stdout.strip(),
                              old_ref.stdout.strip()], user_root)
                if moved.returncode != 0:
                    return {"task_id": task["id"], "status": "escalate",
                            "retries": result.get("retries", 0),
                            "failure_kind": "git",
                            "reason": f"cannot publish integration ref: {moved.stderr.strip()}"}
                result["integration_commit"] = head.stdout.strip()
        return result

    def persist_state(done_set):
        atomic_write_json(args.state, {"schema_version": 2, "run_id": run_id,
                          "completed": sorted(done_set),
                          "input_fingerprint": fingerprint,
                          "last_event_seq": events.seq,
                          "baseline_commit": baseline_commit,
                          "user_dirty_fingerprint": user_dirty_fingerprint,
                          "integration_ref": integration_ref,
                          "integration_path": str(integration_root)})

    results, escalations, skipped = schedule(
        effective_deps, isolate_groups, resource_groups, tasks_by_id,
        run_free, run_isolated, completed, args.max_workers,
        on_progress=persist_state, on_event=events.append)

    persist_state(completed)
    current_ids = {r.get("task_id") for r in results}
    results = ([{"task_id": tid, "status": status, "retries": 0,
                 "recovered_from_git": True}
                for tid, status in recovered.items() if tid not in current_ids] + results)
    reality_gated = [r for r in results if r.get("status") == "reality_gated"]
    events.append("run_drained", completed=sorted(completed),
                  escalations=len(escalations), reality_gated=len(reality_gated),
                  skipped=len(skipped))
    persist_state(completed)
    atomic_write_json(args.report, {"schema_version": 2, "run_id": run_id,
                      "results": results, "escalations": escalations,
                      "reality_gates": reality_gated, "skipped": skipped,
                      "completed": sorted(completed), "total_tasks": len(tasks_by_id),
                      "baseline_commit": baseline_commit,
                      "user_dirty_fingerprint": user_dirty_fingerprint,
                      "integration_ref": integration_ref,
                      "integration_commit": _git(["rev-parse", "HEAD"], integration_root).stdout.strip(),
                      "completeness": {"method": args.completeness,
                                       "artifact": args.census_artifact,
                                       "claim": ("census-backed" if args.completeness == "census"
                                                 else "Completeness unverified")},
                      "summary": {"verified": len(completed) - len(reality_gated),
                                  "reality_gated": len(reality_gated),
                                  "escalated": len(escalations),
                                  "skipped": len(skipped)}})
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
