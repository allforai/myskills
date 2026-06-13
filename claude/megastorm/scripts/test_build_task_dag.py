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

    def test_interface_edge_orders_cross_module(self):
        a = dict(_t("T-auth-01", ["auth/api.py"]), implements=["api:login"])
        b = dict(_t("T-ui-01", ["ui/login.py"]), requires=["api:login"])
        r = build_dag([b, a])  # declaration order does not matter
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["layers"], [["T-auth-01"], ["T-ui-01"]])
        self.assertEqual(r["derived_edges"], [["T-ui-01", "T-auth-01"]])

    def test_required_interface_without_implementer_errors(self):
        b = dict(_t("T-ui-01", ["ui/login.py"]), requires=["api:login"])
        r = build_dag([b])
        self.assertFalse(r["ok"])
        self.assertTrue(any("api:login" in e and "no task implements" in e for e in r["errors"]))

    def test_self_implements_and_requires_no_self_edge(self):
        a = dict(_t("T-a-01", ["a.py"]), implements=["api:x"], requires=["api:x"])
        r = build_dag([a])
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["derived_edges"], [])

    def test_multiple_implementers_all_become_deps(self):
        a1 = dict(_t("T-a-01", ["a1.py"]), implements=["api:x"])
        a2 = dict(_t("T-a-02", ["a2.py"]), implements=["api:x"])
        b = dict(_t("T-b-01", ["b.py"]), requires=["api:x"])
        r = build_dag([a1, a2, b])
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["layers"], [["T-a-01", "T-a-02"], ["T-b-01"]])
        self.assertEqual(sorted(r["derived_edges"]),
                         [["T-b-01", "T-a-01"], ["T-b-01", "T-a-02"]])

    def test_derived_edge_cycle_errors(self):
        a = dict(_t("T-a-01", ["a.py"]), implements=["api:x"], requires=["api:y"])
        b = dict(_t("T-b-01", ["b.py"]), implements=["api:y"], requires=["api:x"])
        r = build_dag([a, b])
        self.assertFalse(r["ok"])
        self.assertTrue(any("cycle" in e for e in r["errors"]))

    def test_derived_edge_combines_with_explicit(self):
        a = dict(_t("T-a-01", ["a.py"]), implements=["api:x"])
        b = dict(_t("T-b-01", ["b.py"]), requires=["api:x"])
        c = _t("T-c-01", ["c.py"], ["T-b-01"])
        r = build_dag([a, b, c])
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["layers"], [["T-a-01"], ["T-b-01"], ["T-c-01"]])

    def test_isolate_groups_two_separate_groups(self):
        tasks = [_t("a", ["p.py"]), _t("b", ["p.py"]), _t("c", ["q.py"]), _t("d", ["q.py"])]
        r = build_dag(tasks)
        self.assertEqual(r["isolate_groups"], [["a", "b"], ["c", "d"]])

    def test_effective_deps_emitted(self):
        a = dict(_t("a", ["a.py"]), implements=["api:x"])
        b = dict(_t("b", ["b.py"], ["a"]), requires=["api:x"])
        r = build_dag([a, b])
        self.assertTrue(r["ok"], r["errors"])
        # explicit depends_on + derived interface edge, deduped
        self.assertEqual(r["effective_deps"], {"a": [], "b": ["a"]})

    def test_effective_deps_includes_derived_edge(self):
        a = dict(_t("a", ["a.py"]), implements=["api:x"])
        b = dict(_t("b", ["b.py"]), requires=["api:x"])
        r = build_dag([a, b])
        self.assertEqual(r["effective_deps"]["b"], ["a"])

    def test_cross_layer_concurrent_path_collision_isolated(self):
        # b (layer 1) and c (layer 0) have no dep path but share a file:
        # under ready-set scheduling they CAN overlap -> must be isolated.
        tasks = [_t("a", ["x.py"]), _t("b", ["shared.py"], ["a"]), _t("c", ["shared.py"])]
        r = build_dag(tasks)
        self.assertTrue(r["ok"], r["errors"])
        self.assertIn(["b", "c"], [sorted(p) for p in r["isolate"]])

    def test_transitive_dep_path_collision_not_isolated(self):
        # a -> b -> c; a and c share a path but can never run concurrently
        tasks = [_t("a", ["s.py"]), _t("b", ["y.py"], ["a"]), _t("c", ["s.py"], ["b"])]
        r = build_dag(tasks)
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["isolate"], [])


class TestResources(unittest.TestCase):
    def test_no_resources_backward_compatible(self):
        r = build_dag([_t("a", ["x.py"]), _t("b", ["y.py"])])
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["resource_groups"], {})
        self.assertEqual(r["isolate"], [])

    def test_shared_resource_concurrent_tasks_isolated(self):
        # disjoint files, same physical resource -> mutex group + isolate
        a = dict(_t("a", ["x.py"]), resources=["sim:default"])
        b = dict(_t("b", ["y.py"]), resources=["sim:default"])
        r = build_dag([a, b])
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["resource_groups"], {"sim:default": ["a", "b"]})
        self.assertEqual([sorted(p) for p in r["isolate"]], [["a", "b"]])
        self.assertEqual(r["isolate_groups"], [["a", "b"]])
        # resource-only collision: no shared-path WARN
        self.assertEqual(r["warnings"], [])

    def test_shared_resource_dep_ordered_not_isolated(self):
        # dep-ordered tasks never overlap; resource_groups still records the set
        a = dict(_t("a", ["x.py"]), resources=["ssh:prod"])
        b = dict(_t("b", ["y.py"], ["a"]), resources=["ssh:prod"])
        r = build_dag([a, b])
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["isolate"], [])
        self.assertEqual(r["resource_groups"], {"ssh:prod": ["a", "b"]})

    def test_single_user_resource_no_group(self):
        a = dict(_t("a", ["x.py"]), resources=["sim:default"])
        r = build_dag([a, _t("b", ["y.py"])])
        self.assertEqual(r["resource_groups"], {})

    def test_resource_bridges_isolate_group_with_path_collision(self):
        # a-b share a resource, b-c share a path -> one transitive group of three
        a = dict(_t("a", ["x.py"]), resources=["stack:shared-test"])
        b = dict(_t("b", ["s.py"]), resources=["stack:shared-test"])
        c = _t("c", ["s.py"])
        r = build_dag([a, b, c])
        self.assertEqual(r["isolate_groups"], [["a", "b", "c"]])


if __name__ == "__main__":
    unittest.main()
