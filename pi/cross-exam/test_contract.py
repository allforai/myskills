"""Packaging checks for the Pi cross-exam adapter. Not live host proof."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[1]
CODEX = ROOT / "codex/cross-exam-skill"
SKILLS = ("cross-exam", "keep-code-simple")


class ManifestTests(unittest.TestCase):
    def test_pi_manifest_lists_completion_and_simplicity(self):
        manifest = json.loads((PACKAGE / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "myskills-cross-exam")
        self.assertIn("pi-package", manifest["keywords"])
        self.assertEqual(
            manifest["pi"]["skills"],
            [f"./skills/{name}" for name in SKILLS],
        )
        for path in manifest["pi"]["skills"]:
            self.assertTrue((PACKAGE / path / "SKILL.md").is_file(), path)
        self.assertNotIn("./skills/product-review", manifest["pi"]["skills"])

    def test_package_does_not_register_nested_protocol_files(self):
        discovered = sorted(
            p.relative_to(PACKAGE).as_posix()
            for p in PACKAGE.rglob("SKILL.md")
        )
        self.assertEqual(
            discovered,
            sorted(f"skills/{name}/SKILL.md" for name in SKILLS),
        )


class AdapterTests(unittest.TestCase):
    def test_entry_is_named_listed_and_user_invoked(self):
        text = (PACKAGE / "skills/cross-exam/SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: cross-exam\n"))
        self.assertRegex(text, r"(?m)^description:")
        self.assertNotIn("disable-model-invocation: true", text)
        header = text.split("---", 2)[1].lower()
        self.assertIn("never", header)
        self.assertIn("/skill:cross-exam", header)

    def test_hard_refuse_without_independent_probers(self):
        text = (PACKAGE / "skills/cross-exam/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("硬拒绝", text)
        self.assertIn("不会降级成自审", text)
        self.assertIn("不自动安装扩展", text)
        self.assertIn('context:"fresh"', text)
        self.assertIn("不要用 git worktree 隔离实测官", text)

    def test_binds_codex_protocol_and_renderer(self):
        text = (PACKAGE / "skills/cross-exam/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("../../codex/cross-exam-skill/", text)
        self.assertIn("SKILL.md", text)
        self.assertIn("render_report.py", text)
        self.assertIn("prompts/{prober,census,sites,sweep}.md", text)
        self.assertTrue((CODEX / "SKILL.md").is_file())
        self.assertTrue((CODEX / "scripts/render_report.py").is_file())
        self.assertTrue((CODEX / "prompts/prober.md").is_file())
        self.assertTrue((CODEX / "lenses.md").is_file())
        self.assertIn("不要读或执行 `product-review.md`", text)
        self.assertIn("Pi 没有 `AskUserQuestion`", text)


if __name__ == "__main__":
    unittest.main()
