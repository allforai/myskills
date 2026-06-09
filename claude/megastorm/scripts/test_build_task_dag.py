# claude/megastorm/scripts/test_build_task_dag.py
import unittest
from build_task_dag import build_dag


def _t(tid, paths, deps=None):
    return {"id": tid, "touched_paths": list(paths), "depends_on": list(deps or [])}


class TestBuildDag(unittest.TestCase):
    def test_linear_layers(self):
        tasks = [_t("a", ["x.py"]), _t("b", ["y.py"], ["a"]), _t("c", ["z.py"], ["b"])]
        r = build_dag(tasks)
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["layers"], [["a"], ["b"], ["c"]])
        self.assertEqual(r["isolate"], [])

    def test_independent_same_layer_disjoint_files(self):
        tasks = [_t("a", ["x.py"]), _t("b", ["y.py"])]
        r = build_dag(tasks)
        self.assertEqual(sorted(r["layers"][0]), ["a", "b"])
        self.assertEqual(r["isolate"], [])

    def test_same_layer_file_collision_isolates(self):
        tasks = [_t("a", ["shared.py"]), _t("b", ["shared.py", "y.py"])]
        r = build_dag(tasks)
        self.assertEqual(sorted(r["layers"][0]), ["a", "b"])
        self.assertEqual([sorted(p) for p in r["isolate"]], [["a", "b"]])

    def test_collision_across_layers_not_isolated(self):
        # b depends on a, so they never run concurrently -> no isolation needed
        tasks = [_t("a", ["shared.py"]), _t("b", ["shared.py"], ["a"])]
        r = build_dag(tasks)
        self.assertEqual(r["isolate"], [])

    def test_mutual_write_no_dep_warns(self):
        tasks = [_t("a", ["shared.py"]), _t("b", ["shared.py"])]
        r = build_dag(tasks)
        self.assertTrue(any("shared.py" in w for w in r["warnings"]))

    def test_cycle_errors(self):
        tasks = [_t("a", ["x.py"], ["b"]), _t("b", ["y.py"], ["a"])]
        r = build_dag(tasks)
        self.assertFalse(r["ok"])
        self.assertTrue(any("cycle" in e for e in r["errors"]))

    def test_missing_dep_errors(self):
        tasks = [_t("a", ["x.py"], ["ghost"])]
        r = build_dag(tasks)
        self.assertFalse(r["ok"])
        self.assertTrue(any("ghost" in e for e in r["errors"]))

    def test_isolate_groups_transitive(self):
        # a-b share s1, b-c share s2 -> all three serialize as one group (b is the bridge)
        tasks = [_t("a", ["s1.py"]), _t("b", ["s1.py", "s2.py"]), _t("c", ["s2.py"])]
        r = build_dag(tasks)
        self.assertEqual(r["isolate_groups"], [["a", "b", "c"]])

    def test_isolate_groups_disjoint(self):
        tasks = [_t("a", ["x.py"]), _t("b", ["y.py"])]
        r = build_dag(tasks)
        self.assertEqual(r["isolate_groups"], [])

    def test_isolate_groups_two_separate_groups(self):
        tasks = [_t("a", ["p.py"]), _t("b", ["p.py"]), _t("c", ["q.py"]), _t("d", ["q.py"])]
        r = build_dag(tasks)
        self.assertEqual(r["isolate_groups"], [["a", "b"], ["c", "d"]])


if __name__ == "__main__":
    unittest.main()
