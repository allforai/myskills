import unittest
from validate_audit_outputs import (
    validate_granularity_audit, validate_decision_coverage, validate_decision_artifact
)

class TestGranularity(unittest.TestCase):
    def test_valid(self):
        ok, errs = validate_granularity_audit({
            "split": [{"from": "big", "into": ["a", "b"], "rationale": "two outcomes"}],
            "merged": [{"from": ["t1", "t2"], "into": "u", "rationale": "fragment"}],
            "kept": ["c"]
        })
        self.assertTrue(ok, errs)

    def test_missing_top_key(self):
        ok, errs = validate_granularity_audit({"split": [], "merged": []})  # no 'kept'
        self.assertFalse(ok)
        self.assertIn("kept", " ".join(errs))

    def test_split_requires_rationale(self):
        ok, errs = validate_granularity_audit({"split": [{"from": "x", "into": ["a"]}], "merged": [], "kept": []})
        self.assertFalse(ok)
        self.assertIn("rationale", " ".join(errs))

class TestDecisionCoverage(unittest.TestCase):
    def test_valid(self):
        ok, errs = validate_decision_coverage({
            "captured": [{"id": "art-style", "node_id": "ui"}],
            "missing": [{"id": "tone", "rationale": "implied by concept, no node", "consumer_node": "copy"}]
        })
        self.assertTrue(ok, errs)

    def test_missing_entry_requires_rationale_and_consumer(self):
        ok, errs = validate_decision_coverage({"captured": [], "missing": [{"id": "tone"}]})
        self.assertFalse(ok)
        self.assertIn("rationale", " ".join(errs))
        # fix C4: a missing decision must name the node that will consume it
        ok2, errs2 = validate_decision_coverage({"captured": [], "missing": [{"id": "tone", "rationale": "x"}]})
        self.assertFalse(ok2)
        self.assertIn("consumer_node", " ".join(errs2))

class TestDecisionArtifact(unittest.TestCase):
    def test_valid(self):
        ok, errs = validate_decision_artifact({
            "id": "art-style", "decision": "flat-2d", "rationale": "fits brand", "options_considered": ["flat-2d", "painterly"]
        })
        self.assertTrue(ok, errs)

    def test_requires_decision_field(self):
        ok, errs = validate_decision_artifact({"id": "art-style", "rationale": "x"})
        self.assertFalse(ok)
        self.assertIn("decision", " ".join(errs))

import subprocess, sys, os, json, tempfile

class TestCli(unittest.TestCase):
    def test_cli_valid_granularity(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"split": [], "merged": [], "kept": ["a"]}, f)
            p = f.name
        r = subprocess.run([sys.executable, "validate_audit_outputs.py", "granularity", p],
                           cwd=os.path.dirname(os.path.abspath(__file__)), capture_output=True, text=True)
        os.unlink(p)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK", r.stdout)

if __name__ == "__main__":
    unittest.main()
