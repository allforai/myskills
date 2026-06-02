import unittest
from compute_reset_closure import reset_closure

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

if __name__ == "__main__":
    unittest.main()
