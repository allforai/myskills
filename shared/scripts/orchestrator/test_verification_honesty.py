import os
import tempfile
import unittest

from check_evidence import derive_state
from compute_completeness import compute_completeness


def _touch(path, content='x'):
    with open(path, 'w') as f:
        f.write(content)


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
            p = os.path.join(d, "evidence.txt")
            _touch(p, "real run output")
            e = {"status": "completed", "verification": _verif(evidence_path="evidence.txt")}
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
            _touch(os.path.join(d, "ev.txt"), "proof")
            tl = [
                {"node": "a", "status": "completed", "verification": _verif(evidence_path="ev.txt")},  # verified
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


if __name__ == "__main__":
    unittest.main()
