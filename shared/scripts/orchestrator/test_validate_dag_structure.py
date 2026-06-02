import unittest
from validate_dag_structure import find_cycles, find_missing_deps, validate_dag_structure


def _n(nid, deps=None):
    return {"node_id": nid, "hard_blocked_by": deps or []}


class TestFindCycles(unittest.TestCase):
    def test_linear_no_cycle(self):
        nodes = [_n("a"), _n("b", ["a"]), _n("c", ["b"])]
        self.assertEqual(find_cycles(nodes), [])

    def test_diamond_no_false_cycle(self):
        nodes = [_n("a"), _n("b", ["a"]), _n("c", ["a"]), _n("d", ["b", "c"])]
        self.assertEqual(find_cycles(nodes), [])

    def test_two_node_cycle(self):
        nodes = [_n("a", ["b"]), _n("b", ["a"])]
        self.assertEqual(sorted(find_cycles(nodes)), ["a", "b"])

    def test_self_loop(self):
        nodes = [_n("a", ["a"])]
        self.assertEqual(find_cycles(nodes), ["a"])

    def test_three_node_cycle_plus_clean_node(self):
        nodes = [_n("x"), _n("a", ["c"]), _n("b", ["a"]), _n("c", ["b"])]
        self.assertEqual(sorted(find_cycles(nodes)), ["a", "b", "c"])

    def test_missing_dep_is_not_a_cycle(self):
        # depending on a non-existent node is a missing-dep error, not a cycle
        nodes = [_n("a", ["ghost"])]
        self.assertEqual(find_cycles(nodes), [])


class TestFindMissingDeps(unittest.TestCase):
    def test_all_present(self):
        nodes = [_n("a"), _n("b", ["a"])]
        self.assertEqual(find_missing_deps(nodes), [])

    def test_missing_reported(self):
        nodes = [_n("a", ["ghost"]), _n("b", ["a"])]
        self.assertEqual(find_missing_deps(nodes), [("a", "ghost")])


class TestValidateDagStructure(unittest.TestCase):
    def test_valid(self):
        wf = {"nodes": [_n("a"), _n("b", ["a"])]}
        r = validate_dag_structure(wf)
        self.assertTrue(r["ok"], r["errors"])

    def test_cycle_blocks(self):
        wf = {"nodes": [_n("a", ["b"]), _n("b", ["a"])]}
        r = validate_dag_structure(wf)
        self.assertFalse(r["ok"])
        self.assertTrue(any("cycle" in e for e in r["errors"]))

    def test_missing_dep_blocks(self):
        wf = {"nodes": [_n("a", ["ghost"])]}
        r = validate_dag_structure(wf)
        self.assertFalse(r["ok"])
        self.assertTrue(any("missing" in e for e in r["errors"]))


if __name__ == "__main__":
    unittest.main()
