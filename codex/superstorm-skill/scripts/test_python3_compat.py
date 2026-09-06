import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
OWNED_DOCS = [ROOT / "SKILL.md", ROOT / "AGENTS.md", ROOT / "execution-playbook.md"]
BARE_COMMAND = re.compile(r"(?m)(?:^|[`\s])python(?:\s|$)")
BARE_SUBPROCESS = re.compile(r"[\[(][\"']python[\"']")


class Python3CompatibilityTests(unittest.TestCase):
    def test_owned_scripts_use_python3_shebang_and_no_bare_subprocess(self):
        for path in (ROOT / "scripts").glob("*.py"):
            if path.name.startswith("test_"):
                continue
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertFalse(text.startswith("#!/usr/bin/env python\n"))
                if text.startswith("#!"):
                    self.assertTrue(text.startswith("#!/usr/bin/env python3\n"))
                self.assertIsNone(BARE_SUBPROCESS.search(text))

    def test_owned_documentation_has_no_bare_python_commands(self):
        for path in OWNED_DOCS:
            with self.subTest(path=path.name):
                self.assertIsNone(BARE_COMMAND.search(path.read_text(encoding="utf-8")))

    def test_direct_script_runs_when_path_has_python3_but_no_python(self):
        with tempfile.TemporaryDirectory() as td:
            bindir = Path(td)
            (bindir / "python3").symlink_to(Path(sys.executable).resolve())
            env = dict(os.environ, PATH=str(bindir))
            result = subprocess.run(
                ["python3", str(ROOT / "scripts/check_closure.py")], env=env,
                stdin=subprocess.DEVNULL, capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 127)
            self.assertFalse((bindir / "python").exists())


if __name__ == "__main__":
    unittest.main()
