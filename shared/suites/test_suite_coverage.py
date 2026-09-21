"""Every tracked test file is run by a line of shared/suites/suites.txt.

ADR-0010: a check that no hook or pipeline invokes does not count as existing. This is the drift
check for that rule — add a test directory without listing it and this goes red.
"""
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUITES = ROOT / "shared/suites/suites.txt"
HOOK = ROOT / ".githooks/pre-commit"
EXEMPT_PREFIXES = ("docs/",)  # frozen campaign records, not live suites

# Runtime CLI tools with no tests yet; delete the entry when a test lands.
EXEMPT_CONTRACT_SCRIPT_STEMS = ("check_product_summary", "check_structured_node_spec")


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


def contract_script_stems():
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    listing = subprocess.run(["git", "ls-files", "shared/scripts/orchestrator"], cwd=ROOT, env=env,
                             capture_output=True, text=True, check=True).stdout
    stems = []
    for f in listing.splitlines():
        name = Path(f).name
        if name.endswith(".py") and (name.startswith("check_") or name.startswith("smoke_")):
            stems.append(Path(f).stem)
    return stems


def test_every_contract_script_is_invoked_by_the_hook_or_a_test():
    hook_text = HOOK.read_text()
    self_rel = Path(__file__).resolve().relative_to(ROOT).as_posix()
    # Exclude this file itself: naming a stem in EXEMPT_CONTRACT_SCRIPT_STEMS is bookkeeping,
    # not a test that exercises the script, so it must not count as coverage.
    test_files = [f for f in tracked_test_files() if f != self_rel]
    test_texts = [(f, (ROOT / f).read_text()) for f in test_files]

    def referenced(stem):
        if stem in hook_text:
            return True
        return any(stem in text for _, text in test_texts)

    stems = contract_script_stems()
    unreferenced = [s for s in stems if not referenced(s) and s not in EXEMPT_CONTRACT_SCRIPT_STEMS]
    assert unreferenced == [], (
        f"no line of .githooks/pre-commit and no tracked test_*.py file names these "
        f"shared/scripts/orchestrator contract scripts: {unreferenced}"
    )

    stale = [
        s for s in EXEMPT_CONTRACT_SCRIPT_STEMS
        if s not in stems or referenced(s)
    ]
    assert stale == [], f"stale entries in EXEMPT_CONTRACT_SCRIPT_STEMS (no longer exempt-worthy): {stale}"
