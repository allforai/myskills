"""Packaging checks for the Pi meta-skill adapter. Not live host proof."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent
CANONICAL = ROOT / "claude/meta-skill"
SKILLS = (
    "meta-skill",
    "bootstrap",
    "setup",
    "journal",
    "journal-merge",
)


class ManifestTests(unittest.TestCase):
    def test_pi_manifest_lists_only_adapter_skills(self):
        manifest = json.loads((PACKAGE / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "myskills-meta-skill")
        self.assertIn("pi-package", manifest["keywords"])
        listed = manifest["pi"]["skills"]
        self.assertEqual(
            listed,
            [f"./skills/{name}" for name in SKILLS],
        )
        for path in listed:
            self.assertTrue((PACKAGE / path / "SKILL.md").is_file(), path)

    def test_package_does_not_register_canonical_capability_skills(self):
        discovered = sorted(
            p.relative_to(PACKAGE).as_posix()
            for p in PACKAGE.rglob("SKILL.md")
        )
        self.assertEqual(
            discovered,
            sorted(f"skills/{name}/SKILL.md" for name in SKILLS),
        )
        capability_tree = CANONICAL / "skills"
        self.assertTrue(any(capability_tree.rglob("SKILL.md")))
        self.assertFalse((PACKAGE / "canonical").exists())


class EntryTests(unittest.TestCase):
    def test_entries_are_named_listed_and_user_invoked(self):
        for name in SKILLS:
            text = (PACKAGE / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=name):
                self.assertTrue(text.startswith(f"---\nname: {name}\n"))
                self.assertRegex(text, r"(?m)^description:")
                self.assertNotIn("disable-model-invocation: true", text)
                header = text.split("---", 2)[1].lower()
                self.assertIn("never", header)
                self.assertIn("/skill:", header)

    def test_bootstrap_binds_canonical_and_pi_run_path(self):
        text = (PACKAGE / "skills/bootstrap/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("../../claude/meta-skill/", text)
        self.assertIn("skills/bootstrap/SKILL.md", text)
        self.assertIn(".pi/skills/run/SKILL.md", text)
        self.assertIn("/skill:run", text)
        self.assertIn("${CLAUDE_PLUGIN_ROOT}", text)
        self.assertIn("不要写 `.claude/commands/run.md`、`.codex/commands/run.md` 或 `.allforai/codex/flow.py`", text)
        self.assertIn("Pi 没有 `AskUserQuestion`", text)
        self.assertTrue((CANONICAL / "skills/bootstrap/SKILL.md").is_file())

    def test_router_does_not_pretend_run_lives_in_the_package(self):
        text = (PACKAGE / "skills/meta-skill/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("../bootstrap/SKILL.md", text)
        self.assertIn("`run`", text)
        self.assertIn(".pi/skills/run/SKILL.md", text)
        self.assertIn("不要在这里伪造编排器", text)


class TemplateTests(unittest.TestCase):
    def test_orchestrator_template_is_pi_native(self):
        text = (PACKAGE / "knowledge/orchestrator-template.md").read_text(encoding="utf-8")
        self.assertIn(".pi/skills/run/SKILL.md", text)
        self.assertIn("name: run", text)
        self.assertIn("/skill:run", text)
        self.assertIn("Pi Dispatch", text)
        self.assertIn("validate_unattended_readiness.py", text)
        self.assertIn("check_artifacts.py", text)
        self.assertNotIn(".claude/commands/run.md", text)
        self.assertNotIn(".codex/commands/run.md", text)
        self.assertNotIn("python .allforai/codex/flow.py", text)
        self.assertIn("There is no `.allforai/codex/flow.py`", text)

    def test_runtime_symlinks_resolve_into_canonical_tree(self):
        for relative in ("scripts", "mcp-ai-gateway"):
            path = (PACKAGE / relative).resolve()
            with self.subTest(link=relative):
                self.assertTrue(path.is_dir(), relative)
                self.assertTrue(path.is_relative_to(CANONICAL.resolve()), relative)
        self.assertTrue((PACKAGE / "scripts/orchestrator/validate_bootstrap.py").is_file())
        self.assertTrue((PACKAGE / "scripts/orchestrator/product_intent.py").is_file())


if __name__ == "__main__":
    unittest.main()
