import unittest
from pathlib import Path
import tempfile

from host_command import InvocationSpec
from model_policy import ModelSource, PRECEDENCE
from prepare_codex_policy import (
    build_sources,
    ensure_outside_repository,
    select_policy,
)


class PreparePolicyTests(unittest.TestCase):
    def test_defaults_to_inherited_unknown_sources(self):
        invocation = InvocationSpec(
            executable="/bin/echo",
            root_args=(),
            exec_args=(),
            source="fixture",
            discovered_argv=("/bin/echo",),
        )
        sources = build_sources(invocation)
        self.assertEqual(len(sources), 6)
        self.assertTrue(all(item.status == "unknown" for item in sources))

    def test_explicit_argv_model_is_locked(self):
        invocation = InvocationSpec(
            executable="/bin/echo",
            root_args=(),
            exec_args=(),
            source="fixture",
            discovered_argv=("/bin/echo", "-m", "fixed"),
            argv_model="fixed",
        )
        sources = {item.name: item for item in build_sources(invocation)}
        self.assertEqual(sources["argv"].status, "locked")

    def test_rejects_policy_directory_inside_repository(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            import subprocess
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            with self.assertRaisesRegex(ValueError, "outside"):
                ensure_outside_repository(root / "docs" / "private", cwd=root)

    def test_inherited_policy_needs_no_model_names(self):
        choice, mappings, models = select_policy(None, None, None, [])
        self.assertEqual(choice, "inherited")
        self.assertEqual(mappings, {})
        self.assertEqual(models["bulk"], "<host-owned>")

    def test_tiered_policy_requires_all_sources_unlocked(self):
        sources = [ModelSource(name, "unlocked", "effective probe") for name in PRECEDENCE]
        choice, mappings, models = select_policy("think", "verify", "build", sources)
        self.assertEqual(choice, "tiered")
        self.assertEqual(mappings["BULK"], "build")
        self.assertEqual(models["verify"], "verify")

    def test_tiered_policy_rejects_unknown_source(self):
        with self.assertRaisesRegex(ValueError, "not allowed"):
            select_policy(
                "think",
                "verify",
                "build",
                [ModelSource("default", "unknown", "not inspectable")],
            )


if __name__ == "__main__":
    unittest.main()
