import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _module_isolation import load, module_dir

_mod = load(module_dir(), "compute_reset_closure")
reset_closure = _mod.reset_closure
apply_reset = _mod.apply_reset
SCRIPT = Path(__file__).resolve().parent / "compute_reset_closure.py"

NODES = [
    {"node_id": "n1", "hard_blocked_by": []},
    {"node_id": "n2", "hard_blocked_by": ["n1"]},
    {"node_id": "n3", "hard_blocked_by": ["n2"]},
    {"node_id": "x",  "hard_blocked_by": []},
]

class TestResetClosure(unittest.TestCase):
    def test_transitive_downstream(self):
        self.assertEqual(sorted(reset_closure(NODES, ["n1"])), ["n1", "n2", "n3"])

    def test_unrelated_untouched(self):
        self.assertEqual(sorted(reset_closure(NODES, ["x"])), ["x"])

    def test_diamond(self):
        nodes = [
            {"node_id": "a", "hard_blocked_by": []},
            {"node_id": "b", "hard_blocked_by": ["a"]},
            {"node_id": "c", "hard_blocked_by": ["a"]},
            {"node_id": "d", "hard_blocked_by": ["b", "c"]},
        ]
        self.assertEqual(sorted(reset_closure(nodes, ["a"])), ["a", "b", "c", "d"])


def _workflow():
    return {"nodes": [dict(n) for n in NODES], "transition_log": [
        {"node_id": "n1", "status": "completed"},
        {"node": "n2", "status": "completed"},
        {"node_id": "n2", "status": "failed"},
        {"node_id": "x", "status": "completed"},
    ]}


class TestApplyReset(unittest.TestCase):
    """The official reset: completions in the closure stop counting, history stays."""

    def test_closure_completions_are_superseded_and_named(self):
        wf = _workflow()
        closure, count = apply_reset(wf, ["n1"], "diagnosis-3", now="T")
        self.assertEqual(sorted(closure), ["n1", "n2", "n3"])
        self.assertEqual(count, 2)
        log = wf["transition_log"]
        self.assertEqual([e["status"] for e in log], ["superseded", "superseded", "failed", "completed"])
        self.assertEqual(log[0]["superseded_by"], {"diagnosis": "diagnosis-3", "at": "T"})
        self.assertEqual(len(log), 4, "nothing is deleted")

    def test_unknown_root_is_refused(self):
        with self.assertRaises(ValueError):
            apply_reset(_workflow(), ["ghost"], "d")

    def test_cli_requires_a_diagnosis_ref_and_writes_in_place(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "workflow.json"
            path.write_text(json.dumps(_workflow()))
            refused = subprocess.run([sys.executable, str(SCRIPT), str(path), "--apply", "n1"],
                                     capture_output=True, text=True)
            self.assertEqual(refused.returncode, 2)
            self.assertEqual(json.loads(path.read_text()), _workflow(), "a refused reset changes nothing")
            done = subprocess.run([sys.executable, str(SCRIPT), str(path), "--apply",
                                   "--diagnosis", "d-1", "n2"], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(json.loads(done.stdout)["reset"], ["n2", "n3"])
            statuses = [e["status"] for e in json.loads(path.read_text())["transition_log"]]
            self.assertEqual(statuses, ["completed", "superseded", "failed", "completed"])

    def test_listing_without_apply_is_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "workflow.json"
            path.write_text(json.dumps(_workflow()))
            out = subprocess.run([sys.executable, str(SCRIPT), str(path), "n1"],
                                 capture_output=True, text=True)
            self.assertEqual(sorted(json.loads(out.stdout)), ["n1", "n2", "n3"])
            self.assertEqual(json.loads(path.read_text()), _workflow())


if __name__ == "__main__":
    unittest.main()
