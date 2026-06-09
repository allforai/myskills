import os
import unittest
from check_skill_refs import check_refs

HERE = os.path.dirname(__file__)
PLUGIN_ROOT = os.path.abspath(os.path.join(HERE, ".."))


class TestCheckRefs(unittest.TestCase):
    def test_real_plugin_refs_resolve(self):
        r = check_refs(PLUGIN_ROOT)
        self.assertTrue(r["ok"], r["missing"])

    def test_detects_missing(self):
        r = check_refs(PLUGIN_ROOT, extra_required=["knowledge/prompts/does-not-exist.md"])
        self.assertFalse(r["ok"])
        self.assertIn("knowledge/prompts/does-not-exist.md", r["missing"])


if __name__ == "__main__":
    unittest.main()
