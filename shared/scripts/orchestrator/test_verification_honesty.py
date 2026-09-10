import os
import tempfile
import unittest

from _module_isolation import load, module_dir

_check_evidence, _compute_completeness = load(module_dir(), "check_evidence", "compute_completeness")
derive_state = _check_evidence.derive_state
compute_completeness = _compute_completeness.compute_completeness


def _touch(path, content='x'):
    with open(path, 'w') as f:
        f.write(content)


def _capture(path, exit_code=0):
    """Write a valid capture_evidence/v1 record (what command-method evidence must be)."""
    import json
    with open(path, 'w') as f:
        json.dump({"schema": "capture_evidence/v1", "command": ["true"],
                   "exit_code": exit_code, "stdout": "", "stdout_sha256": "abc"}, f)


def _verif(method="real-run", evidence_path=None, verifier="v-agent", claim="works"):
    v = {"method": method, "verifier": verifier, "claim": claim}
    if evidence_path is not None:
        v["evidence_path"] = evidence_path
    return v


class TestDeriveState(unittest.TestCase):
    def test_failed(self):
        self.assertEqual(derive_state({"status": "failed"}), "failed")

    def test_method_none_is_unverified(self):
        # the lazy default: generated, no evidence -> NOT verified
        self.assertEqual(derive_state({"status": "completed", "verification": {"method": "none"}}), "unverified")

    def test_no_verification_field_is_unverified(self):
        self.assertEqual(derive_state({"status": "completed"}), "unverified")

    def test_evidence_missing_on_disk_downgrades(self):
        e = {"status": "completed", "verification": _verif(evidence_path="/no/such/file.png")}
        self.assertEqual(derive_state(e), "unverified")

    def test_verified_with_real_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            _capture(os.path.join(d, "evidence.json"))
            e = {"status": "completed", "verification": _verif(evidence_path="evidence.json")}
            self.assertEqual(derive_state(e, base_dir=d), "verified")

    def test_command_method_with_plaintext_evidence_is_unverified(self):
        # anti-fabrication L1: a command method must carry a structured capture record,
        # not agent-authored free text (which it could fabricate).
        with tempfile.TemporaryDirectory() as d:
            _touch(os.path.join(d, "fake.txt"), "I totally ran it and it passed, trust me")
            e = {"status": "completed", "verification": _verif(evidence_path="fake.txt")}
            self.assertEqual(derive_state(e, base_dir=d), "unverified")

    def test_screenshot_method_accepts_image_file(self):
        # screenshot is exempt from the capture-record requirement (it's an image)
        with tempfile.TemporaryDirectory() as d:
            _touch(os.path.join(d, "shot.png"), "PNGDATA")
            e = {"status": "completed", "verification": _verif(method="screenshot", evidence_path="shot.png")}
            self.assertEqual(derive_state(e, base_dir=d), "verified")

    def test_self_graded_downgrades(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "e.txt")
            _touch(p)
            e = {"status": "completed", "generated_by": "gen-agent",
                 "verification": _verif(evidence_path="e.txt", verifier="gen-agent")}
            self.assertEqual(derive_state(e, base_dir=d), "unverified")  # verifier == generator

    def test_missing_verifier_downgrades(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "e.txt")
            _touch(p)
            e = {"status": "completed", "verification": {"method": "real-run", "evidence_path": "e.txt"}}
            self.assertEqual(derive_state(e, base_dir=d), "unverified")


class TestComputeCompleteness(unittest.TestCase):
    def test_self_attested_pipeline_reads_low(self):
        # The TeteChat scenario: many nodes "completed" but with NO real evidence.
        # Must read as low verified_pct, NOT 94.65.
        tl = [{"node": f"n{i}", "status": "completed", "verification": {"method": "none"}} for i in range(100)]
        wf = {"nodes": [{"node_id": f"n{i}"} for i in range(100)], "transition_log": tl}
        r = compute_completeness(wf)
        self.assertEqual(r["verified"], 0)
        self.assertEqual(r["unverified"], 100)
        self.assertEqual(r["verified_pct"], 0.0)

    def test_mixed_counts_and_pct(self):
        with tempfile.TemporaryDirectory() as d:
            _capture(os.path.join(d, "ev.json"))
            tl = [
                {"node": "a", "status": "completed", "verification": _verif(evidence_path="ev.json")}, # verified
                {"node": "b", "status": "completed", "verification": {"method": "none"}},              # unverified
                {"node": "c", "status": "failed"},                                                     # failed
                {"node": "d", "status": "completed", "verification": _verif(evidence_path="gone.txt")},# unverified (missing)
            ]
            wf = {"nodes": [{"node_id": x} for x in "abcd"], "transition_log": tl}
            r = compute_completeness(wf, base_dir=d)
            self.assertEqual((r["verified"], r["unverified"], r["failed"]), (1, 2, 1))
            self.assertEqual(r["verified_pct"], 25.0)

    def test_critical_unverified_flagged(self):
        tl = [{"node": "crit", "status": "completed", "verification": {"method": "none"}}]
        wf = {"nodes": [{"node_id": "crit", "critical": True}], "transition_log": tl}
        r = compute_completeness(wf)
        self.assertEqual(r["critical_unverified"], ["crit"])

    def test_mock_layer_is_refused_in_cross_exams_words(self):
        # ADR-0008: the hollow judgement is cross-exam's; the machine-detectable part stays.
        with tempfile.TemporaryDirectory() as d:
            _capture(os.path.join(d, "ev.json"))
            v = dict(_verif(evidence_path="ev.json"),
                     served_by={"host": "localhost:3000", "process": "node", "mock_layers": ["msw"]})
            wf = {"nodes": [{"node_id": "a"}], "transition_log": [{"node": "a", "status": "completed", "verification": v}]}
            r = compute_completeness(wf, base_dir=d)
            self.assertEqual((r["verified"], r["unverified"]), (0, 1))
            self.assertEqual(r["refused"], [{"node_id": "a", "reason": "经 mock 层（msw）的 runtime 不能判 done"}])

    def test_response_identical_to_fixture_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(os.path.join(d, "orders.fixture.json"), '{"orders": []}')
            import json
            with open(os.path.join(d, "ev.json"), "w") as f:
                json.dump({"schema": "capture_evidence/v1", "command": ["curl"], "exit_code": 0,
                           "stdout": '{"orders": []}\n', "stdout_sha256": "abc"}, f)
            v = dict(_verif(method="real-api", evidence_path="ev.json"),
                     served_by={"host": "localhost", "process": "node", "mock_layers": [],
                                "fixtures": ["orders.fixture.json"]})
            wf = {"nodes": [{"node_id": "a"}], "transition_log": [{"node": "a", "status": "completed", "verification": v}]}
            r = compute_completeness(wf, base_dir=d)
            self.assertEqual(r["by_node"][0]["reason"], "响应与 fixture 一致（orders.fixture.json）的 runtime 不能判 done")
            self.assertEqual(r["verified"], 0)


if __name__ == "__main__":
    unittest.main()
