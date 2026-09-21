"""Every tracked test file is run by a line of shared/suites/suites.txt.

ADR-0010: a check that no hook or pipeline invokes does not count as existing. This is the drift
check for that rule — add a test directory without listing it and this goes red.
"""
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUITES = ROOT / "shared/suites/suites.txt"
EXEMPT_PREFIXES = ("docs/",)  # frozen campaign records, not live suites


def suite_paths():
    paths = []
    for line in SUITES.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            paths.extend(line.split())
    return paths


def tracked_test_files():
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    listing = subprocess.run(["git", "ls-files"], cwd=ROOT, env=env,
                             capture_output=True, text=True, check=True).stdout
    return [f for f in listing.splitlines()
            if f.endswith(".py")
            and (Path(f).name.startswith("test_") or f.endswith("_test.py"))
            and not f.startswith(EXEMPT_PREFIXES)]


def covered(path, suites):
    return any(path == s or path.startswith(s.rstrip("/") + "/") for s in suites)


def test_every_tracked_test_file_is_in_a_suite():
    suites = suite_paths()
    orphans = [f for f in tracked_test_files() if not covered(f, suites)]
    assert orphans == [], f"no line of shared/suites/suites.txt runs these: {orphans}"


def test_every_suite_path_exists():
    missing = [s for s in suite_paths() if not (ROOT / s).exists()]
    assert missing == [], f"shared/suites/suites.txt names paths that do not exist: {missing}"


def test_an_unlisted_file_is_reported():
    assert not covered("shared/new-package/test_thing.py", suite_paths())
    assert covered("shared/keep-code-simple/test_contract.py", suite_paths())
