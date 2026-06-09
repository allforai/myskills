# claude/megastorm/scripts/test_validate_plan_tasks.py
import unittest
from validate_plan_tasks import validate_tasks


def _t(tid, paths=("a.py",), cmd="pytest a.py"):
    return {"id": tid, "touched_paths": list(paths), "acceptance_cmd": cmd}


class TestValidateTasks(unittest.TestCase):
    def test_all_valid(self):
        r = validate_tasks([_t("T1"), _t("T2", ("b.py",), "npm run build")])
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["errors"], [])

    def test_missing_touched_paths(self):
        r = validate_tasks([{"id": "T1", "acceptance_cmd": "pytest"}])
        self.assertFalse(r["ok"])
        self.assertTrue(any("touched_paths" in e for e in r["errors"]))

    def test_empty_touched_paths(self):
        r = validate_tasks([{"id": "T1", "touched_paths": [], "acceptance_cmd": "x"}])
        self.assertFalse(r["ok"])
        self.assertTrue(any("touched_paths" in e for e in r["errors"]))

    def test_missing_acceptance_cmd(self):
        r = validate_tasks([{"id": "T1", "touched_paths": ["a.py"]}])
        self.assertFalse(r["ok"])
        self.assertTrue(any("acceptance_cmd" in e for e in r["errors"]))

    def test_blank_acceptance_cmd(self):
        r = validate_tasks([{"id": "T1", "touched_paths": ["a.py"], "acceptance_cmd": "  "}])
        self.assertFalse(r["ok"])
        self.assertTrue(any("acceptance_cmd" in e for e in r["errors"]))

    def test_missing_id(self):
        r = validate_tasks([{"touched_paths": ["a.py"], "acceptance_cmd": "x"}])
        self.assertFalse(r["ok"])
        self.assertTrue(any("id" in e for e in r["errors"]))

    def test_error_names_task(self):
        r = validate_tasks([_t("T1"), {"id": "T2"}])
        self.assertFalse(r["ok"])
        self.assertTrue(any("T2" in e for e in r["errors"]))


if __name__ == "__main__":
    unittest.main()
