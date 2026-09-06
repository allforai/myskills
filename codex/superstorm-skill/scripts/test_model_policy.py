import json
from pathlib import Path
import tempfile
import unittest

from host_command import normalize_host_argv
from model_policy import (ModelPolicyError, ModelSource, create_policy_artifact,
                          recommend_policy, validate_policy_artifact)


class ModelPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        target = Path(self.tmp.name, "codex-real")
        target.write_text("codex"); target.chmod(0o755)
        self.codex = Path(self.tmp.name, "codex"); self.codex.symlink_to(target)
        self.key = b"run-integrity-key"

    def tearDown(self):
        self.tmp.cleanup()

    def spec(self, *args):
        return normalize_host_argv([str(self.codex), *args], "fixture")

    def test_locked_and_unknown_only_allow_inherited(self):
        self.assertEqual(recommend_policy([
            ModelSource("argv", "locked", "-m present")])[0], "inherited")
        self.assertEqual(recommend_policy([
            ModelSource("profile", "unknown", "probe unavailable")])[0], "inherited")
        with self.assertRaisesRegex(ModelPolicyError, "cannot override"):
            create_policy_artifact(
                self.spec("-m", "fixed"), [ModelSource("argv", "locked", "-m present")],
                "tiered", "user", "now", self.key,
                {"THINK": "a", "VERIFY": "b", "BULK": "c"})

    def test_all_unlocked_allows_tiered_and_requires_real_mappings(self):
        sources = [ModelSource(name, "unlocked", "effective probe")
                   for name in ("wrapper", "argv", "profile", "config", "user_project", "default")]
        self.assertEqual(recommend_policy(sources)[0], "tiered")
        with self.assertRaisesRegex(ModelPolicyError, "three real"):
            create_policy_artifact(self.spec(), sources, "tiered", "user", "now",
                                   self.key, {"THINK": "placeholder"})

    def test_confirmed_artifact_preview_and_validation_are_deterministic(self):
        config = Path(self.tmp.name, "config.toml"); config.write_text("model='free'\n")
        sources = [ModelSource(name, "unlocked", "effective probe",
                               (str(config),) if name == "config" else ())
                   for name in ("wrapper", "argv", "profile", "config", "user_project", "default")]
        mappings = {"THINK": "think-v1", "VERIFY": "verify-v1", "BULK": "bulk-v1"}
        spec = self.spec("--profile", "team")
        artifact = create_policy_artifact(spec, sources, "tiered", "alice", "2026-07-20",
                                          self.key, mappings, codex_version="codex 1")
        self.assertTrue(artifact["confirmed"])
        self.assertIn("bulk-v1", artifact["child_preview"])
        one = validate_policy_artifact(artifact, spec, sources, self.key,
                                       codex_version="codex 1")
        two = validate_policy_artifact(json.loads(json.dumps(artifact)), spec, sources,
                                       self.key, codex_version="codex 1")
        self.assertEqual(one["fingerprint"], two["fingerprint"])

    def test_resume_detects_argv_config_executable_and_version_drift(self):
        config = Path(self.tmp.name, "config.toml"); config.write_text("safe\n")
        sources = [ModelSource(name, "unlocked", "probe",
                               (str(config),) if name == "config" else ())
                   for name in ("wrapper", "argv", "profile", "config", "user_project", "default")]
        mappings = {"THINK": "t", "VERIFY": "v", "BULK": "b"}
        spec = self.spec()
        artifact = create_policy_artifact(spec, sources, "tiered", "u", "now",
                                          self.key, mappings, codex_version="v1")
        with self.assertRaisesRegex(ModelPolicyError, "version drift"):
            validate_policy_artifact(artifact, spec, sources, self.key, codex_version="v2")
        config.write_text("changed\n")
        with self.assertRaisesRegex(ModelPolicyError, "source/config drift"):
            validate_policy_artifact(artifact, spec, sources, self.key, codex_version="v1")
        Path(spec.executable).write_text("changed executable")
        with self.assertRaises(Exception):
            validate_policy_artifact(artifact, spec, sources, self.key, codex_version="v1")

    def test_inherited_artifact_keeps_argv_model_exactly_once(self):
        spec = self.spec("-m", "host-model")
        sources = [ModelSource("argv", "locked", "explicit model flag")]
        artifact = create_policy_artifact(spec, sources, "inherited", "u", "now", self.key)
        self.assertEqual(artifact["child_preview"].count("-m"), 1)
        self.assertIn("host-model", artifact["child_preview"])


if __name__ == "__main__":
    unittest.main()
