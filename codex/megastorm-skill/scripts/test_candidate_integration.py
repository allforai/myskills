import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from candidate_integration import (
    CASConflict, Check, PostMergeCheckFailure, admit_candidate, recover_intent,
    subprocess_runner,
)


class EventStore:
    def __init__(self, crash_after=None):
        self.events = []
        self.crash_after = crash_after

    def write(self, kind, payload):
        self.events.append((kind, dict(payload)))
        if self.crash_after == kind:
            raise RuntimeError(f"crash after durable {kind}")

    def exists(self, kind, key):
        return any(event_kind == kind and
                   (payload["task_id"], payload["transaction_id"],
                    payload["candidate_commit"]) == key
                   for event_kind, payload in self.events)

    def payload(self, kind):
        return next(payload for event_kind, payload in self.events if event_kind == kind)


class RepoFixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        for argv in (("git", "init", "-q"),
                     ("git", "config", "user.email", "test@example.com"),
                     ("git", "config", "user.name", "Test")):
            subprocess.run(argv, cwd=self.repo, check=True, capture_output=True)
        (self.repo / "base.txt").write_text("base\n")
        self.git("add", "base.txt"); self.git("commit", "-q", "-m", "base")
        self.base = self.rev("HEAD")
        self.git("branch", "task", self.base)
        self.git("checkout", "-q", "task")
        (self.repo / "task.txt").write_text("task\n")
        self.git("add", "task.txt"); self.git("commit", "-q", "-m", "task")
        self.task = self.rev("HEAD")
        self.git("checkout", "-q", "--detach", self.base)
        self.integration_ref = "refs/megastorm/test/integration"
        self.git("update-ref", self.integration_ref, self.base)

    def git(self, *args):
        return subprocess.run(("git", *args), cwd=self.repo, check=True,
                              capture_output=True, text=True)

    def rev(self, value):
        return self.git("rev-parse", value).stdout.strip()

    def close(self):
        subprocess.run(("git", "worktree", "prune"), cwd=self.repo, capture_output=True)
        self.temp.cleanup()


class CandidateIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fx = RepoFixture()

    def tearDown(self):
        self.fx.close()

    def kwargs(self, store, checks=()):
        return dict(repo=self.fx.repo, integration_ref=self.fx.integration_ref,
                    expected_integration_commit=self.fx.base, task_commit=self.fx.task,
                    task_id="T1", transaction_id="attempt-1", contract_hash="c" * 64,
                    post_merge_checks=checks, event_writer=store.write)

    def test_happy_path_checks_intent_cas_complete_then_releases_dependents(self):
        store = EventStore()
        result = admit_candidate(**self.kwargs(
            store, [Check("task visible", ("git", "cat-file", "-e", "HEAD:task.txt"))]))
        self.assertTrue(result.dependents_ready)
        self.assertEqual([kind for kind, _ in store.events],
                         ["merge-intent", "merge-complete"])
        self.assertEqual(self.fx.rev(self.fx.integration_ref), result.candidate_commit)
        self.assertTrue(all(item["exit_code"] == 0 for item in result.evidence["checks"]))

    def test_candidate_runs_artifact_validator_before_publication(self):
        store = EventStore()
        seen = []
        result = admit_candidate(**self.kwargs(store),
                                 post_merge_validator=lambda root, base:
                                 seen.append((root, base)) or {"admission_sha256": "a" * 64})
        self.assertEqual(len(seen), 1)
        self.assertEqual(result.evidence["artifact_admission"]["admission_sha256"],
                         "a" * 64)

    def test_concurrent_task_from_older_baseline_merges_into_new_integration(self):
        self.fx.git("checkout", "-q", "--detach", self.fx.base)
        (self.fx.repo / "sibling.txt").write_text("sibling\n")
        self.fx.git("add", "sibling.txt"); self.fx.git("commit", "-q", "-m", "sibling")
        newer = self.fx.rev("HEAD")
        self.fx.git("update-ref", self.fx.integration_ref, newer, self.fx.base)
        store = EventStore()
        kwargs = self.kwargs(store)
        kwargs["expected_integration_commit"] = newer
        kwargs["task_base_commit"] = self.fx.base
        result = admit_candidate(**kwargs)
        self.assertTrue(result.dependents_ready)
        self.assertEqual(
            self.fx.git("show", f"{result.integration_commit}:task.txt").stdout, "task\n")
        self.assertEqual(
            self.fx.git("show", f"{result.integration_commit}:sibling.txt").stdout,
            "sibling\n")

    def test_failed_post_merge_check_never_publishes_and_quarantines_evidence(self):
        store = EventStore()
        with self.assertRaises(PostMergeCheckFailure) as raised:
            admit_candidate(**self.kwargs(
                store, [Check("must fail", ("git", "cat-file", "-e", "HEAD:nope"))]))
        self.assertEqual(self.fx.rev(self.fx.integration_ref), self.fx.base)
        self.assertTrue(raised.exception.evidence["quarantined"])
        self.assertTrue(Path(raised.exception.evidence["worktree"]).exists())
        self.assertEqual(store.events[0][0], "candidate-quarantined")

    def test_crash_after_durable_intent_recovers_cas_and_completion(self):
        store = EventStore(crash_after="merge-intent")
        with self.assertRaisesRegex(RuntimeError, "merge-intent"):
            admit_candidate(**self.kwargs(store))
        self.assertEqual(self.fx.rev(self.fx.integration_ref), self.fx.base)
        intent = store.payload("merge-intent")
        store.crash_after = None
        result = recover_intent(repo=self.fx.repo, integration_ref=self.fx.integration_ref,
                                intent=intent, event_writer=store.write,
                                event_exists=store.exists)
        self.assertTrue(result.dependents_ready)
        self.assertEqual(self.fx.rev(self.fx.integration_ref), intent["candidate_commit"])

    def test_crash_after_cas_before_complete_recovers_completion_only(self):
        store = EventStore()
        crashed = {"value": False}

        def runner(argv, cwd):
            result = subprocess_runner(argv, cwd)
            if (not crashed["value"] and tuple(argv[:3]) ==
                    ("git", "update-ref", self.fx.integration_ref)
                    and len(argv) == 5 and result.returncode == 0):
                crashed["value"] = True
                raise RuntimeError("crash immediately after CAS")
            return result

        with self.assertRaisesRegex(RuntimeError, "after CAS"):
            admit_candidate(**self.kwargs(store), command_runner=runner)
        intent = store.payload("merge-intent")
        self.assertEqual(self.fx.rev(self.fx.integration_ref), intent["candidate_commit"])
        self.assertFalse(store.exists("merge-complete",
                                      ("T1", "attempt-1", intent["candidate_commit"])))
        result = recover_intent(repo=self.fx.repo, integration_ref=self.fx.integration_ref,
                                intent=intent, event_writer=store.write,
                                event_exists=store.exists)
        self.assertTrue(result.dependents_ready)
        self.assertTrue(store.exists("merge-complete",
                                     ("T1", "attempt-1", intent["candidate_commit"])))

    def test_crash_after_durable_complete_is_idempotent(self):
        store = EventStore(crash_after="merge-complete")
        with self.assertRaisesRegex(RuntimeError, "merge-complete"):
            admit_candidate(**self.kwargs(store))
        intent = store.payload("merge-intent")
        self.assertEqual(self.fx.rev(self.fx.integration_ref), intent["candidate_commit"])
        store.crash_after = None
        before = len(store.events)
        result = recover_intent(repo=self.fx.repo, integration_ref=self.fx.integration_ref,
                                intent=intent, event_writer=store.write,
                                event_exists=store.exists)
        self.assertTrue(result.dependents_ready)
        self.assertEqual(len(store.events), before)  # durable complete was already present

    def test_recovery_is_idempotent_after_complete(self):
        store = EventStore()
        admitted = admit_candidate(**self.kwargs(store))
        intent = store.payload("merge-intent")
        before = list(store.events)
        recovered = recover_intent(repo=self.fx.repo,
                                   integration_ref=self.fx.integration_ref,
                                   intent=intent, event_writer=store.write,
                                   event_exists=store.exists)
        self.assertEqual(store.events, before)
        self.assertEqual(recovered.integration_commit, admitted.integration_commit)

    def test_cas_conflict_leaves_other_integration_value_and_requires_recheck(self):
        store = EventStore(crash_after="merge-intent")
        with self.assertRaises(RuntimeError):
            admit_candidate(**self.kwargs(store))
        intent = store.payload("merge-intent")
        self.fx.git("update-ref", self.fx.integration_ref, self.fx.task, self.fx.base)
        store.crash_after = None
        with self.assertRaises(CASConflict) as raised:
            recover_intent(repo=self.fx.repo, integration_ref=self.fx.integration_ref,
                           intent=intent, event_writer=store.write,
                           event_exists=store.exists)
        self.assertEqual(self.fx.rev(self.fx.integration_ref), self.fx.task)
        self.assertTrue(raised.exception.evidence["requires_recheck"])

    def test_publish_cas_race_never_overwrites_competing_ref(self):
        store = EventStore()
        raced = {"value": False}

        def runner(argv, cwd):
            if (not raced["value"] and tuple(argv[:3]) ==
                    ("git", "update-ref", self.fx.integration_ref) and len(argv) == 5):
                raced["value"] = True
                self.fx.git("update-ref", self.fx.integration_ref,
                            self.fx.task, self.fx.base)
            return subprocess_runner(argv, cwd)

        with self.assertRaises(CASConflict) as raised:
            admit_candidate(**self.kwargs(store), command_runner=runner)
        self.assertEqual(self.fx.rev(self.fx.integration_ref), self.fx.task)
        self.assertTrue(raised.exception.evidence["requires_recheck"])
        self.assertIn("candidate-quarantined", [kind for kind, _ in store.events])


if __name__ == "__main__":
    unittest.main()
