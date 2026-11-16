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



class TestRouteDefects(unittest.TestCase):
    """A defect a node reported in another node's output goes back to that node, once."""

    def project(self, warnings):
        root = Path(tempfile.mkdtemp())
        workflow = {"nodes": [dict(n) for n in NODES], "transition_log": [
            {"node_id": n["node_id"], "status": "completed"} for n in NODES]}
        (root / "workflow.json").write_text(json.dumps(workflow))
        (root / "run-warnings.json").write_text(json.dumps({"warnings": warnings}))
        return root

    def route(self, root):
        result = subprocess.run([sys.executable, str(SCRIPT), str(root / "workflow.json"), "--route-defects"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def statuses(self, root):
        log = json.loads((root / "workflow.json").read_text())["transition_log"]
        return {e["node_id"]: e["status"] for e in log}

    def test_a_reported_defect_reopens_its_owner_and_what_was_built_on_it(self):
        root = self.project(["defect in n2: docs/api.md — the label is misspelled",
                             "building block chosen by n1: sqlite (already used)"])
        out = self.route(root)
        self.assertEqual(out["routed"], [{"owner": "n2", "defect": "docs/api.md — the label is misspelled"}])
        self.assertEqual(out["reset"], ["n2", "n3"])
        self.assertEqual(self.statuses(root), {"n1": "completed", "n2": "superseded",
                                               "n3": "superseded", "x": "completed"})
        correction = json.loads((root / "diagnosis-corrections/n2.json").read_text())
        self.assertEqual(correction["node_id"], "n2")
        self.assertIn("the label is misspelled", correction["corrections"][0]["action"])

    def test_a_defect_is_routed_once(self):
        root = self.project(["defect in x: data.json — two periods"])
        self.assertEqual(len(self.route(root)["routed"]), 1)
        before = (root / "workflow.json").read_bytes()
        self.assertEqual(self.route(root), {"routed": [], "kept": [], "reset": [], "diagnosis": None})
        self.assertEqual((root / "workflow.json").read_bytes(), before)

    def test_nothing_reported_changes_nothing(self):
        root = self.project(["review required"])
        before = (root / "workflow.json").read_bytes()
        self.assertEqual(self.route(root)["routed"], [])
        self.assertEqual((root / "workflow.json").read_bytes(), before)
        self.assertFalse((root / "diagnosis-corrections").exists())
        self.assertFalse((root / "routed-defects.json").exists())

    def test_a_defect_naming_no_node_of_the_plan_stays_a_warning(self):
        root = self.project(["defect in vendor-lib: README — typo"])
        out = self.route(root)
        self.assertEqual(out["routed"], [])
        self.assertIn("no node of the plan", out["kept"][0]["reason"])

    def test_an_owner_is_sent_back_a_bounded_number_of_times(self):
        root = self.project([])
        for round_number in range(_mod.ROUTE_LIMIT):
            (root / "run-warnings.json").write_text(json.dumps(
                {"warnings": [f"defect in x: data.json — wording {round_number}", f"defect in x: other {round_number}"]}))
            self.assertEqual(len(self.route(root)["routed"]), 2, "one round carries every defect of the owner")
        (root / "run-warnings.json").write_text(json.dumps({"warnings": ["defect in x: data.json — reworded again"]}))
        out = self.route(root)
        self.assertEqual(out["routed"], [])
        self.assertIn("already sent back", out["kept"][0]["reason"])

    def test_corrections_already_pending_for_the_owner_are_kept(self):
        root = self.project(["defect in x: data.json — two periods"])
        (root / "diagnosis-corrections").mkdir()
        (root / "diagnosis-corrections/x.json").write_text(json.dumps(
            {"node_id": "x", "diagnosis": "d1", "corrections": [{"action": "use the tenant key"}]}))
        self.route(root)
        actions = [c["action"] for c in json.loads((root / "diagnosis-corrections/x.json").read_text())["corrections"]]
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0], "use the tenant key")

if __name__ == "__main__":
    unittest.main()
