import unittest

from simulate_workflow import simulate


class WorkflowSimulationTests(unittest.TestCase):
    def test_reports_initial_ready_and_failure_blast_radius(self):
        tasks = [{"id": "A"}, {"id": "B"}, {"id": "C"}]
        orchestration = {
            "ok": True,
            "effective_deps": {"A": [], "B": ["A"], "C": []},
            "isolate_groups": [["A", "C"]],
            "resource_groups": {},
            "derived_edges": [["B", "A"]],
            "warnings": [],
        }
        result = simulate(tasks, orchestration)
        self.assertTrue(result["ok"])
        self.assertEqual(result["initial_ready"], ["A", "C"])
        self.assertEqual(result["dependency_waves_informational"], [["A", "C"], ["B"]])
        self.assertEqual(result["failure_blast_radius"]["A"], ["B"])
        self.assertEqual(result["path_merge_groups"], [["A", "C"]])

    def test_reports_resource_mutexes(self):
        result = simulate(
            [{"id": "A"}, {"id": "B"}],
            {
                "ok": True,
                "effective_deps": {"A": [], "B": []},
                "resource_groups": {"db:test": ["A", "B"]},
            },
        )
        self.assertEqual(result["resource_mutexes"], {"db:test": ["A", "B"]})

    def test_blocks_unreachable_graph(self):
        result = simulate(
            [{"id": "A"}, {"id": "B"}],
            {"ok": True, "effective_deps": {"A": ["B"], "B": ["A"]}},
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["unreachable"], ["A", "B"])

    def test_blocks_unknown_dependency(self):
        result = simulate(
            [{"id": "A"}],
            {"ok": True, "effective_deps": {"A": ["missing"]}},
        )
        self.assertFalse(result["ok"])
        self.assertIn("unknown", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
