# claude/megastorm/scripts/test_validate_plan_tasks.py
import unittest
from validate_plan_tasks import validate_tasks


def _t(tid, paths=("a.py",), cmd="pytest a.py"):
    return {"id": tid, "touched_paths": list(paths), "acceptance_cmd": cmd}


class TestValidateTasks(unittest.TestCase):
    def test_interface_tags_valid_vocab(self):
        t = dict(_t("T1"), implements=["api:login"], requires=["data:user"])
        r = validate_tasks([t], interfaces={"api:login", "data:user"})
        self.assertTrue(r["ok"], r["errors"])

    def test_interface_tags_off_registry_blocks(self):
        t = dict(_t("T1"), requires=["api:loginn"])
        r = validate_tasks([t], interfaces={"api:login"})
        self.assertFalse(r["ok"])
        self.assertTrue(any("off-registry" in e and "api:loginn" in e for e in r["errors"]))

    def test_interface_tags_ignored_without_registry(self):
        t = dict(_t("T1"), requires=["api:whatever"])
        r = validate_tasks([t])
        self.assertTrue(r["ok"], r["errors"])

    def test_interface_tags_must_be_string_list(self):
        t = dict(_t("T1"), implements="api:login")
        r = validate_tasks([t], interfaces={"api:login"})
        self.assertFalse(r["ok"])
        self.assertTrue(any("list of interface names" in e for e in r["errors"]))

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

    def test_resources_valid_list_passes(self):
        t = dict(_t("T1"), resources=["sim:default", "stack:shared-test"])
        r = validate_tasks([t])
        self.assertTrue(r["ok"], r["errors"])

    def test_resources_absent_passes(self):
        r = validate_tasks([_t("T1")])
        self.assertTrue(r["ok"], r["errors"])

    def test_resources_not_a_list_blocks(self):
        t = dict(_t("T1"), resources="sim:default")
        r = validate_tasks([t])
        self.assertFalse(r["ok"])
        self.assertTrue(any("resources" in e for e in r["errors"]))

    def test_resources_blank_entry_blocks(self):
        t = dict(_t("T1"), resources=["sim:default", "  "])
        r = validate_tasks([t])
        self.assertFalse(r["ok"])
        self.assertTrue(any("resources" in e for e in r["errors"]))


class TestVacuousAcceptance(unittest.TestCase):
    """A name-selective test cmd exits 0 on 0 match (the vacuous-pass failure mode)."""

    def test_swift_filter_without_guard_blocks(self):
        # name-selective test, no zero-test guard
        r = validate_tasks([_t("T", cmd="cd x && swift test --filter SomeFeatureTests")])
        self.assertFalse(r["ok"])
        self.assertTrue(any("VACUOUS" in e for e in r["errors"]))

    def test_go_test_run_without_guard_blocks(self):
        r = validate_tasks([_t("T", cmd="go test -run TestInvite ./...")])
        self.assertFalse(r["ok"])
        self.assertTrue(any("VACUOUS" in e for e in r["errors"]))

    def test_jest_t_without_guard_blocks(self):
        r = validate_tasks([_t("T", cmd="npx jest -t 'call flow'")])
        self.assertFalse(r["ok"])

    def test_swift_filter_with_executed_guard_passes(self):
        cmd = "swift test --filter SomeFeatureTests 2>&1 | grep -q 'Executed [1-9]'"
        r = validate_tasks([_t("T", cmd=cmd)])
        self.assertTrue(r["ok"], r["errors"])

    def test_go_run_with_no_tests_guard_passes(self):
        cmd = "go test -run TestX ./pkg/... 2>&1 | tee /tmp/o && ! grep -q 'no tests to run' /tmp/o"
        r = validate_tasks([_t("T", cmd=cmd)])
        self.assertTrue(r["ok"], r["errors"])

    def test_pytest_k_is_not_flagged(self):
        # pytest exits 5 on no collection — not vacuous-passable
        r = validate_tasks([_t("T", cmd="pytest -k call_flow tests/")])
        self.assertTrue(r["ok"], r["errors"])

    def test_full_suite_not_flagged(self):
        r = validate_tasks([_t("T", cmd="swift test && go build ./...")])
        self.assertTrue(r["ok"], r["errors"])

    def test_only_testing_warns_not_blocks(self):
        cmd = "xcodebuild test -only-testing:App/SomeTests -quiet"
        r = validate_tasks([_t("T", cmd=cmd)])
        self.assertTrue(r["ok"], r["errors"])          # warn, does not block
        self.assertTrue(any("only-testing" in w for w in r["warnings"]))

    def test_only_testing_with_count_guard_no_warn(self):
        cmd = "xcodebuild test -only-testing:App/SomeTests | grep -c 'Test Case'"
        r = validate_tasks([_t("T", cmd=cmd)])
        self.assertEqual(r["warnings"], [])

    def test_reality_gate_true_device_bound_accepted(self):
        # reality_gate task keeps a real, non-empty (possibly device-bound) acceptance_cmd
        t = dict(_t("T-rg", cmd="run-ui-on-simulator"), reality_gate=True)
        r = validate_tasks([t])
        self.assertTrue(r["ok"], r["errors"])

    def test_reality_gate_must_be_boolean(self):
        t = dict(_t("T-bad"), reality_gate="yes")
        r = validate_tasks([t])
        self.assertFalse(r["ok"])
        self.assertTrue(any("reality_gate" in e and "boolean" in e for e in r["errors"]))

    def test_reality_gate_task_still_needs_acceptance_cmd(self):
        t = dict(_t("T-e", cmd="   "), reality_gate=True)
        r = validate_tasks([t])
        self.assertFalse(r["ok"])
        self.assertTrue(any("acceptance_cmd" in e for e in r["errors"]))

    def test_reality_gate_omitted_backward_compatible(self):
        r = validate_tasks([_t("T-o")])
        self.assertTrue(r["ok"], r["errors"])


if __name__ == "__main__":
    unittest.main()
