# codex/megastorm-skill/scripts/test_run_layers.py
import json
import pathlib
import subprocess
import tempfile
import threading
import unittest

from run_layers import (ANTI_VACUOUS, HEAVY_CMD_RE, build_supervisor_prompt,
                        EventLog, InfrastructureFailure, atomic_write_json, parse_verdict,
                        main, prepare_integration_workspace, run_task,
                        recover_confirmed_from_git, run_task_in_worktree, schedule,
                        undeclared_paths)

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

    def test_reality_gate_does_not_consume_business_retry(self):
        task = dict(_task("T-rg"), reality_gate=True, runbook_ptr="plan.md#verify")
        fake = FakeRunner([_v(False, reality_gated=True, evidence="device absent")])
        r = run_task(task, fake, MODELS, ".", PROMPTS, log=lambda *_: None)
        self.assertEqual(r["status"], "reality_gated")
        self.assertEqual(r["retries"], 0)
        self.assertEqual(r["runbook_ptr"], "plan.md#verify")

    def test_infrastructure_retry_separate_from_business_retry(self):
        class Flaky(FakeRunner):
            def __init__(self):
                super().__init__([_v(True)])
                self.failed = False

            def run(self, prompt, model, cwd):
                if not self.failed:
                    self.failed = True
                    raise InfrastructureFailure("network")
                return super().run(prompt, model, cwd)

        r = run_task(_task("T-infra"), Flaky(), MODELS, ".", PROMPTS,
                     log=lambda *_: None)
        self.assertEqual(r["status"], "done")
        self.assertEqual(r["retries"], 0)
        self.assertEqual(r["infra_retries"], 1)


class TestDurabilityAndScope(unittest.TestCase):
    def test_atomic_json_never_leaves_temp(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td, "state.json")
            atomic_write_json(path, {"completed": ["a"]})
            self.assertEqual(json.loads(path.read_text())["completed"], ["a"])
            self.assertEqual(list(pathlib.Path(td).glob(".megastorm-*.tmp")), [])

    def test_undeclared_path_detection(self):
        self.assertEqual(undeclared_paths(["src/a.py", "tests/x.py"], ["src"]),
                         ["tests/x.py"])
        self.assertEqual(undeclared_paths(["../escape"], ["src"]), ["../escape"])

    def test_event_log_quarantines_partial_tail(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td, "events.jsonl")
            path.write_text(json.dumps({"run_id": "r", "seq": 1}) + "\n" + '{"bad"')
            log = EventLog(path, "r", 1)
            log.append("resumed")
            lines = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual([x["seq"] for x in lines], [1, 2])
            self.assertTrue(pathlib.Path(str(path) + ".partial").exists())

    def test_integration_workspace_preserves_dirty_user_tree(self):
        with tempfile.TemporaryDirectory() as root:
            for cmd in (["git", "init", "-q"], ["git", "config", "user.email", "t@t"],
                        ["git", "config", "user.name", "t"],
                        ["git", "commit", "-q", "--allow-empty", "-m", "init"]):
                subprocess.run(cmd, cwd=root, check=True, capture_output=True)
            dirty = pathlib.Path(root, "user-draft.txt")
            dirty.write_text("mine")
            integration, ref, baseline = prepare_integration_workspace(
                pathlib.Path(root), "12345678-test", {})
            try:
                self.assertEqual(dirty.read_text(), "mine")
                self.assertFalse(pathlib.Path(integration, "user-draft.txt").exists())
                self.assertTrue(ref.startswith("refs/megastorm/runs/"))
                self.assertTrue(baseline)
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(integration)],
                               cwd=root, capture_output=True)

    def test_confirmation_marker_recovers_after_snapshot_gap(self):
        with tempfile.TemporaryDirectory() as root:
            for cmd in (["git", "init", "-q"], ["git", "config", "user.email", "t@t"],
                        ["git", "config", "user.name", "t"],
                        ["git", "commit", "-q", "--allow-empty", "-m", "init"]):
                subprocess.run(cmd, cwd=root, check=True, capture_output=True)
            baseline = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                                      capture_output=True, text=True).stdout.strip()
            subprocess.run(["git", "commit", "--allow-empty", "-m",
                            "megastorm-confirmed: T1"], cwd=root,
                           check=True, capture_output=True)
            self.assertEqual(recover_confirmed_from_git(
                pathlib.Path(root), baseline, {"T1": {}, "T2": {}}), {"T1": "done"})

    def test_main_publishes_integration_ref_without_touching_user_tree(self):
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td)
            repo = base / "repo"; repo.mkdir()
            for cmd in (["git", "init", "-q"], ["git", "config", "user.email", "t@t"],
                        ["git", "config", "user.name", "t"],
                        ["git", "commit", "-q", "--allow-empty", "-m", "init"]):
                subprocess.run(cmd, cwd=repo, check=True, capture_output=True)
            (repo / "user-draft.txt").write_text("mine")
            tasks = [{"id": "T1", "title": "write output", "touched_paths": ["out.txt"],
                      "acceptance_cmd": "test -f out.txt", "depends_on": []}]
            orch = {"effective_deps": {"T1": []}, "isolate_groups": [],
                    "resource_groups": {}}
            (base / "tasks.json").write_text(json.dumps(tasks))
            (base / "orch.json").write_text(json.dumps(orch))
            (base / "models.json").write_text(json.dumps(MODELS))
            fake = base / "fake_agent.py"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import json,pathlib,sys\n"
                "model,cwd,out,prompt=sys.argv[1:]\n"
                "if 'anti-fake-completion verifier' in prompt:\n"
                " pathlib.Path(out).write_text(json.dumps({'done':True,'rerun_exit_code':0,'evidence':'ok'}))\n"
                "else:\n"
                " pathlib.Path(cwd,'out.txt').write_text('done')\n"
                " pathlib.Path(out).write_text('implemented')\n")
            fake.chmod(0o755)
            args = ["run_layers.py", str(base / "orch.json"), str(base / "tasks.json"),
                    "--models", str(base / "models.json"), "--prompts", str(PROMPTS),
                    "--root", str(repo), "--state", str(base / "state.json"),
                    "--events", str(base / "events.jsonl"),
                    "--report", str(base / "report.json"),
                    "--codex-template", f"{fake} {{model}} {{cwd}} {{out}}"]
            self.assertEqual(main(args), 0)
            report = json.loads((base / "report.json").read_text())
            self.assertEqual(report["summary"]["verified"], 1)
            self.assertTrue(report["integration_ref"].startswith("refs/megastorm/runs/"))
            self.assertEqual((repo / "user-draft.txt").read_text(), "mine")
            self.assertFalse((repo / "out.txt").exists())

    def test_safe_mode_keeps_declared_collision_mutexes(self):
        # Scheduler-level regression: singleton isolation markers must not replace
        # the original [a,b] mutex group.
        tasks = [_task("a", ["same.py"]), _task("b", ["same.py"])]
        peak = {"now": 0, "max": 0}; lock = threading.Lock()

        def isolated(task):
            import time
            with lock:
                peak["now"] += 1; peak["max"] = max(peak["max"], peak["now"])
            time.sleep(0.02)
            with lock:
                peak["now"] -= 1
            return {"task_id": task["id"], "status": "done", "retries": 0}

        groups = [["a", "b"]] + [["a"], ["b"]]
        schedule({"a": [], "b": []}, groups, {}, {t["id"]: t for t in tasks},
                 isolated, isolated, set(), max_workers=2, log=lambda *_: None)
        self.assertEqual(peak["max"], 1)


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

    def test_reality_gated_task_satisfies_dependency(self):
        tasks = [_task("a"), _task("b")]
        eff = {"a": [], "b": ["a"]}
        order, _, esc, skip, done = self._run(
            eff, [], {}, tasks, {"a": "reality_gated"})
        self.assertEqual(order, ["a", "b"])
        self.assertEqual(esc, [])
        self.assertEqual(skip, {})
        self.assertEqual(done, {"a", "b"})

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
