# codex/megastorm-skill/scripts/test_run_layers.py
import json
import pathlib
import subprocess
import tempfile
import threading
import unittest

from run_layers import (ANTI_VACUOUS, HEAVY_CMD_RE, build_supervisor_prompt,
                        parse_verdict, run_task, run_task_in_worktree, schedule)

PROMPTS = pathlib.Path(__file__).resolve().parent.parent / "prompts"


def _task(tid, paths=("a.py",), cmd="pytest a.py"):
    return {"id": tid, "title": tid, "touched_paths": list(paths),
            "acceptance_cmd": cmd, "depends_on": []}


class FakeRunner:
    """Scripted agent: supervisor replies come from a per-task queue; executor
    calls are recorded (incl. whether feedback was attached)."""

    def __init__(self, verdicts):
        self.verdicts = list(verdicts)
        self.executor_prompts = []
        self.lock = threading.Lock()

    def run(self, prompt, model, cwd):
        with self.lock:
            if "anti-fake-completion verifier" in prompt:
                return self.verdicts.pop(0)
            self.executor_prompts.append(prompt)
            return "implemented."


def _v(done, **kw):
    return json.dumps(dict({"done": done, "rerun_exit_code": 0 if done else 1,
                            "evidence": "out"}, **kw))


MODELS = {"think": "m-think", "verify": "m-verify", "bulk": "m-bulk"}


class TestHeavyCmdHeuristic(unittest.TestCase):
    """Machine-heavy acceptance_cmd detection backing the unbounded-concurrency
    warning (warn only — the runner never auto-caps)."""

    def test_matches_heavy_commands(self):
        for cmd in ("docker build .", "make all", "cargo build --release",
                    "npm run build", "gradle assemble"):
            self.assertTrue(HEAVY_CMD_RE.search(cmd), cmd)

    def test_ignores_light_commands(self):
        for cmd in ("pytest tests/test_x.py -q", "python3 check.py",
                    "node smoke.js", ""):
            self.assertFalse(HEAVY_CMD_RE.search(cmd), cmd)


class TestParseVerdict(unittest.TestCase):
    def test_plain_json(self):
        self.assertTrue(parse_verdict(_v(True))["done"])

    def test_fenced_json(self):
        self.assertFalse(parse_verdict("notes\n```json\n" + _v(False) + "\n```")["done"])

    def test_json_with_surrounding_prose(self):
        self.assertTrue(parse_verdict("I reran it.\n" + _v(True) + "\nbye")["done"])

    def test_unparseable_returns_none(self):
        self.assertIsNone(parse_verdict("no json here"))
        self.assertIsNone(parse_verdict('{"unrelated": 1}'))


class TestRunTask(unittest.TestCase):
    def test_done_first_try(self):
        r = run_task(_task("T1"), FakeRunner([_v(True)]), MODELS, ".", PROMPTS, log=lambda *_: None)
        self.assertEqual((r["status"], r["retries"]), ("done", 0))

    def test_retry_then_done(self):
        fake = FakeRunner([_v(False, refutation="test fails"), _v(True)])
        r = run_task(_task("T1"), fake, MODELS, ".", PROMPTS, log=lambda *_: None)
        self.assertEqual((r["status"], r["retries"]), ("done", 1))
        self.assertIn("test fails", fake.executor_prompts[1])  # feedback re-injected

    def test_budget_exhausted_escalates(self):
        fake = FakeRunner([_v(False)] * 3)
        r = run_task(_task("T1"), fake, MODELS, ".", PROMPTS, log=lambda *_: None)
        self.assertEqual((r["status"], r["retries"]), ("escalate", 2))
        self.assertEqual(len(fake.executor_prompts), 3)  # initial + 2 retries

    def test_vacuous_bounce_injects_instruction(self):
        fake = FakeRunner([_v(False, vacuous=True), _v(True)])
        r = run_task(_task("T1"), fake, MODELS, ".", PROMPTS, log=lambda *_: None)
        self.assertEqual(r["status"], "done")
        self.assertIn(ANTI_VACUOUS, fake.executor_prompts[1])

    def test_unparseable_verdict_twice_escalates(self):
        fake = FakeRunner(["garbage", "still garbage"])
        r = run_task(_task("T1"), fake, MODELS, ".", PROMPTS, log=lambda *_: None)
        self.assertEqual(r["status"], "escalate")
        self.assertIn("unparseable", r["reason"])

    def test_supervisor_prompt_independent_of_executor(self):
        p = build_supervisor_prompt(PROMPTS, _task("T1"))
        self.assertIn("acceptance_cmd", p)
        self.assertNotIn("implemented.", p)  # never sees executor narrative


class TestSchedule(unittest.TestCase):
    """Ready-set scheduler: effective_deps drive readiness, mutex sets serialize
    collisions, escalations skip transitive dependents but never halt the loop."""

    def _run(self, eff_deps, isolate_groups, resource_groups, tasks, results_map,
             completed=None, max_workers=4):
        order = []
        lock = threading.Lock()

        def runner(t):
            with lock:
                order.append(t["id"])
            return {"task_id": t["id"], "status": results_map.get(t["id"], "done"),
                    "retries": 0, "reason": "x"}
        completed = completed if completed is not None else set()
        res, esc, skip = schedule(eff_deps, isolate_groups, resource_groups,
                                  {t["id"]: t for t in tasks}, runner, runner,
                                  completed, max_workers=max_workers, log=lambda *_: None)
        return order, res, esc, skip, completed

    def test_dep_order_respected(self):
        tasks = [_task(t) for t in ("a", "b", "c")]
        eff = {"a": [], "b": ["a"], "c": ["b"]}
        order, _, esc, _, done = self._run(eff, [], {}, tasks, {})
        self.assertEqual(esc, [])
        self.assertEqual(order, ["a", "b", "c"])
        self.assertEqual(done, {"a", "b", "c"})

    def test_independents_all_run(self):
        tasks = [_task(t) for t in ("a", "b", "c")]
        eff = {"a": [], "b": [], "c": []}
        order, _, esc, _, done = self._run(eff, [], {}, tasks, {})
        self.assertEqual(sorted(order), ["a", "b", "c"])
        self.assertEqual(done, {"a", "b", "c"})

    def test_escalation_skips_transitive_dependents_not_independents(self):
        # b<-a, c<-b (chain) and independent d. a escalates → b and c skipped,
        # d still runs. The loop does NOT halt.
        tasks = [_task(t) for t in ("a", "b", "c", "d")]
        eff = {"a": [], "b": ["a"], "c": ["b"], "d": []}
        order, _, esc, skip, done = self._run(eff, [], {}, tasks, {"a": "escalate"})
        self.assertEqual(len(esc), 1)
        self.assertEqual(set(skip), {"b", "c"})
        self.assertEqual(skip["b"], "a")
        self.assertIn("d", order)        # independent kept running
        self.assertNotIn("b", order)     # dependent never dispatched
        self.assertEqual(done, {"d"})

    def test_isolate_group_serializes_concurrent_members(self):
        # a,b share a file (no dep between them) → never in flight together.
        tasks = [_task("a", ["s.py"]), _task("b", ["s.py"])]
        eff = {"a": [], "b": []}
        inflight_peak = {"n": 0}
        cur = {"n": 0}
        lock = threading.Lock()

        def runner(t):
            with lock:
                cur["n"] += 1
                inflight_peak["n"] = max(inflight_peak["n"], cur["n"])
            import time
            time.sleep(0.02)
            with lock:
                cur["n"] -= 1
            return {"task_id": t["id"], "status": "done", "retries": 0}
        res, esc, skip = schedule(eff, [["a", "b"]], {}, {t["id"]: t for t in tasks},
                                  runner, runner, set(), max_workers=4, log=lambda *_: None)
        self.assertEqual(inflight_peak["n"], 1)  # mutex held: never 2 at once

    def _peak_concurrency(self, n_tasks, max_workers):
        tasks = [_task(f"t{i}", [f"f{i}.py"]) for i in range(n_tasks)]
        eff = {t["id"]: [] for t in tasks}
        peak, cur, lock = {"n": 0}, {"n": 0}, threading.Lock()

        def runner(t):
            with lock:
                cur["n"] += 1
                peak["n"] = max(peak["n"], cur["n"])
            import time
            time.sleep(0.05)
            with lock:
                cur["n"] -= 1
            return {"task_id": t["id"], "status": "done", "retries": 0}
        _, esc, _ = schedule(eff, [], {}, {t["id"]: t for t in tasks},
                             runner, runner, set(), max_workers=max_workers,
                             log=lambda *_: None)
        self.assertEqual(esc, [])
        return peak["n"]

    def test_unbounded_default_dispatches_all_ready_at_once(self):
        # max_workers=0 (the default) = no in-flight cap: all 6 independent
        # tasks must be in flight simultaneously.
        self.assertEqual(self._peak_concurrency(6, max_workers=0), 6)

    def test_explicit_cap_still_limits_in_flight(self):
        self.assertLessEqual(self._peak_concurrency(6, max_workers=2), 2)

    def test_resource_group_serializes(self):
        tasks = [_task("a"), _task("b")]
        eff = {"a": [], "b": []}
        inflight_peak = {"n": 0}
        cur = {"n": 0}
        lock = threading.Lock()

        def runner(t):
            with lock:
                cur["n"] += 1
                inflight_peak["n"] = max(inflight_peak["n"], cur["n"])
            import time
            time.sleep(0.02)
            with lock:
                cur["n"] -= 1
            return {"task_id": t["id"], "status": "done", "retries": 0}
        schedule(eff, [], {"sim:default": ["a", "b"]}, {t["id"]: t for t in tasks},
                 runner, runner, set(), max_workers=4, log=lambda *_: None)
        self.assertEqual(inflight_peak["n"], 1)

    def test_resume_skips_completed(self):
        tasks = [_task(t) for t in ("a", "b")]
        eff = {"a": [], "b": ["a"]}
        order, _, _, _, done = self._run(eff, [], {}, tasks, {}, completed={"a"})
        self.assertEqual(order, ["b"])
        self.assertEqual(done, {"a", "b"})

    def test_isolate_member_uses_run_isolated(self):
        # the isolated branch must route through run_isolated, free tasks through run_free
        tasks = [_task("a", ["s.py"]), _task("b", ["s.py"]), _task("c")]
        eff = {"a": [], "b": [], "c": []}
        seen = {"free": [], "iso": []}
        lock = threading.Lock()

        def free(t):
            with lock:
                seen["free"].append(t["id"])
            return {"task_id": t["id"], "status": "done", "retries": 0}

        def iso(t):
            with lock:
                seen["iso"].append(t["id"])
            return {"task_id": t["id"], "status": "done", "retries": 0}
        schedule(eff, [["a", "b"]], {}, {t["id"]: t for t in tasks},
                 free, iso, set(), max_workers=4, log=lambda *_: None)
        self.assertEqual(sorted(seen["iso"]), ["a", "b"])
        self.assertEqual(seen["free"], ["c"])


class CommitFakeRunner(FakeRunner):
    """Executor really writes + commits a file in its cwd (simulates a real run)."""

    def run(self, prompt, model, cwd):
        if "anti-fake-completion verifier" not in prompt:
            tid = json.loads(prompt.split("## Your task (JSON)")[1].split("##")[0])["id"]
            pathlib.Path(cwd, f"{tid}.txt").write_text("done")
            subprocess.run(["git", "add", "-A"], cwd=cwd, capture_output=True)
            subprocess.run(["git", "commit", "-m", tid], cwd=cwd, capture_output=True)
        return super().run(prompt, model, cwd)


class NoCommitFakeRunner(FakeRunner):
    """Executor writes files in cwd but NEVER commits (the live-run failure mode
    that poisoned worktree merges before the safety-commit fix)."""

    def run(self, prompt, model, cwd):
        if "anti-fake-completion verifier" not in prompt:
            tid = json.loads(prompt.split("## Your task (JSON)")[1].split("##")[0])["id"]
            pathlib.Path(cwd, "pkg").mkdir(exist_ok=True)
            pathlib.Path(cwd, "pkg", "mod.py").write_text(f"# by {tid}\n")
        return FakeRunner.run(self, prompt, model, cwd)


class TestWorktreeSmoke(unittest.TestCase):
    def test_worktree_isolated_task_merges_back(self):
        with tempfile.TemporaryDirectory() as root:
            for cmd in (["git", "init", "-q"], ["git", "config", "user.email", "t@t"],
                        ["git", "config", "user.name", "t"],
                        ["git", "commit", "-q", "--allow-empty", "-m", "init"]):
                subprocess.run(cmd, cwd=root, check=True, capture_output=True)
            fake = CommitFakeRunner([_v(True)])
            r = run_task_in_worktree(_task("T-x-01"), fake, MODELS, pathlib.Path(root),
                                     PROMPTS, threading.Lock(), log=lambda *_: None)
            self.assertEqual(r["status"], "done", r)
            self.assertTrue(pathlib.Path(root, "T-x-01.txt").exists())  # merged back
            wt_list = subprocess.run(["git", "worktree", "list"], cwd=root,
                                     capture_output=True, text=True).stdout
            self.assertEqual(len(wt_list.strip().splitlines()), 1)  # cleaned up


class TestMainTreeConsistency(unittest.TestCase):
    def _repo(self, root):
        for cmd in (["git", "init", "-q"], ["git", "config", "user.email", "t@t"],
                    ["git", "config", "user.name", "t"],
                    ["git", "commit", "-q", "--allow-empty", "-m", "init"]):
            subprocess.run(cmd, cwd=root, check=True, capture_output=True)

    def test_uncommitted_free_task_does_not_poison_worktree_merge(self):
        # Regression for the todoscan live run: a free task leaves pkg/mod.py
        # UNCOMMITTED in main; the next isolated task touches the same path in
        # its worktree. Without the pre-worktree safety-commit the merge dies
        # with "untracked working tree files would be overwritten".
        from run_layers import run_task, safety_commit
        with tempfile.TemporaryDirectory() as root:
            self._repo(root)
            rootp = pathlib.Path(root)
            free = NoCommitFakeRunner([_v(True)])
            r1 = run_task(_task("T-a-01", ["pkg/mod.py"]), free, MODELS, rootp,
                          PROMPTS, log=lambda *_: None)
            self.assertEqual(r1["status"], "done")
            # main tree now has uncommitted pkg/mod.py (executor never committed)
            iso = NoCommitFakeRunner([_v(True)])
            r2 = run_task_in_worktree(_task("T-b-01", ["pkg/mod.py"]), iso, MODELS,
                                      rootp, PROMPTS, threading.Lock(),
                                      log=lambda *_: None)
            self.assertEqual(r2["status"], "done", r2.get("reason"))
            self.assertIn("by T-b-01", (rootp / "pkg" / "mod.py").read_text())

    def test_merge_failure_reason_carries_stderr(self):
        # Force a genuine content conflict and assert the reason is non-empty.
        from run_layers import _git, safety_commit
        with tempfile.TemporaryDirectory() as root:
            self._repo(root)
            rootp = pathlib.Path(root)
            (rootp / "pkg").mkdir(); (rootp / "pkg" / "mod.py").write_text("main version\n")
            safety_commit(rootp, "seed mod.py")

            class Conflicting(FakeRunner):
                def run(self, prompt, model, cwd):
                    if "anti-fake-completion verifier" not in prompt:
                        pathlib.Path(cwd, "pkg", "mod.py").write_text("worktree version\n")
                    return FakeRunner.run(self, prompt, model, cwd)

            runner = Conflicting([_v(True)])
            lock = threading.Lock()
            # diverge main AFTER the worktree branches: patch worktree add to
            # also advance main — simpler: branch first via direct calls
            wt_res = run_task_in_worktree  # exercise real path with main advanced mid-flight
            # advance main between branch and merge by hooking the runner
            orig_run = runner.run
            def run_and_diverge(prompt, model, cwd):
                out = orig_run(prompt, model, cwd)
                if "anti-fake-completion verifier" in prompt:
                    (rootp / "pkg" / "mod.py").write_text("diverged on main\n")
                    safety_commit(rootp, "diverge main")
                return out
            runner.run = run_and_diverge
            r = wt_res(_task("T-c-01", ["pkg/mod.py"]), runner, MODELS, rootp,
                       PROMPTS, lock, log=lambda *_: None)
            self.assertEqual(r["status"], "escalate")
            self.assertTrue(len(r["reason"]) > len("merge conflict on megastorm/T-c-01: "),
                            r["reason"])


if __name__ == "__main__":
    unittest.main()
