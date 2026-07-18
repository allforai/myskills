import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_manifest_and_two_skills(self):
        manifest = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(manifest["name"], "megastorm")
        self.assertTrue(manifest["version"])
        self.assertTrue(manifest["description"])
        for name in ("megastorm", "cross-exam"):
            skill = ROOT / "skills" / name / "SKILL.md"
            self.assertTrue(skill.is_file(), skill)
            text = skill.read_text()
            self.assertTrue(text.startswith("---\n"))
            self.assertIn(f"name: {name}", text)

    def test_install_uses_grok_home_and_owns_only_plugin_dir(self):
        with tempfile.TemporaryDirectory() as td:
            env = dict(os.environ, GROK_HOME=str(Path(td) / "home"))
            result = subprocess.run(
                [str(ROOT / "install.sh")], env=env, text=True,
                capture_output=True, check=True,
            )
            installed = Path(td) / "home/plugins/megastorm"
            self.assertTrue((installed / ".claude-plugin/plugin.json").is_file())
            self.assertTrue((installed / "skills/megastorm/SKILL.md").is_file())
            self.assertTrue((installed / "skills/cross-exam/SKILL.md").is_file())
            self.assertEqual(list((Path(td) / "home").iterdir()), [Path(td) / "home/plugins"])
            self.assertIn("grok plugin validate", result.stdout)

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "plugin"
            result = subprocess.run(
                [str(ROOT / "install.sh"), "--dry-run", "--dest", str(dest)],
                text=True, capture_output=True, check=True,
            )
            self.assertFalse(dest.exists())
            self.assertIn("Would install", result.stdout)


if __name__ == "__main__":
    unittest.main()
