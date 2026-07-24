import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from portable_checkpoint import (
    CheckpointError,
    create_checkpoint,
    validate_checkpoint,
)


class PortableCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"],
                       cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"],
                       cwd=self.repo, check=True)
        (self.repo / "base").write_text("base")
        subprocess.run(["git", "add", "base"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=self.repo, check=True)
        self.baseline = self.git("rev-parse", "HEAD")
        subprocess.run(
            ["git", "commit", "--allow-empty", "-qm", "grillstorm-confirmed: T-a"],
            cwd=self.repo,
            check=True,
        )
        self.integration = self.git("rev-parse", "HEAD")
        self.ref = "refs/grillstorm/runs/run-1/integration"
        subprocess.run(["git", "update-ref", self.ref, self.integration],
                       cwd=self.repo, check=True)
        self.tasks = [{"id": "T-a"}, {"id": "T-b"}]
        self.orchestration = {"effective_deps": {"T-a": [], "T-b": ["T-a"]}}
        self.run_state = {
            "spec_revision": 1,
            "task_revision": 1,
            "workflow_revision": 1,
            "launch_revision": 1,
        }

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, capture_output=True,
                              text=True, check=True).stdout.strip()

    def workflow_state(self):
        return {
            "run_id": "run-1",
            "baseline_commit": self.baseline,
            "integration_ref": self.ref,
            "completed": ["T-a"],
        }

    def test_round_trip_produces_new_controller_seed(self):
        checkpoint = create_checkpoint(
            self.workflow_state(), self.run_state, self.tasks,
            self.orchestration, self.repo, "claude",
        )
        seed = validate_checkpoint(
            json.loads(json.dumps(checkpoint)), self.tasks, self.orchestration, self.repo,
        )
        self.assertEqual(seed["completed"], ["T-a"])
        self.assertEqual(seed["portable_integration_commit"], self.integration)

    def test_rejects_state_without_supervised_marker(self):
        state = self.workflow_state()
        state["completed"].append("T-b")
        with self.assertRaisesRegex(CheckpointError, "markers"):
            create_checkpoint(
                state, self.run_state, self.tasks, self.orchestration, self.repo, "claude",
            )

    def test_rejects_changed_workflow(self):
        checkpoint = create_checkpoint(
            self.workflow_state(), self.run_state, self.tasks,
            self.orchestration, self.repo, "claude",
        )
        with self.assertRaisesRegex(CheckpointError, "workflow inputs"):
            validate_checkpoint(
                checkpoint, self.tasks + [{"id": "T-c"}], self.orchestration, self.repo,
            )

    def test_rejects_tampering(self):
        checkpoint = create_checkpoint(
            self.workflow_state(), self.run_state, self.tasks,
            self.orchestration, self.repo, "codex",
        )
        checkpoint["completed"] = []
        with self.assertRaisesRegex(CheckpointError, "fingerprint"):
            validate_checkpoint(checkpoint, self.tasks, self.orchestration, self.repo)


if __name__ == "__main__":
    unittest.main()
