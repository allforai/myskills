# codex/grillstorm-skill/scripts/validate_plan_tasks.py
#!/usr/bin/env python3
"""§4.3 gate: every plan task MUST carry a non-empty touched_paths list and a
non-blank acceptance_cmd. touched_paths feeds the §4.5 concurrency DAG;
acceptance_cmd feeds the §4.6 anti-fake-completion supervisor's objective rerun.
Plans failing this are bounced back to the plan agent.

VACUOUS-PASSABLE acceptance: a test command that selects a subset BY NAME exits
0 when the name matches nothing, so a 0-test run masquerades as green.

grillstorm is LANGUAGE-AGNOSTIC. A static script cannot read run output, so this
early check is necessarily a best-effort heuristic over a NON-EXHAUSTIVE,
EXTENSIBLE registry of common runners (`_VACUOUS_RUNNERS` below — add your own).
The AUTHORITATIVE anti-vacuous gate is the supervisor (prompts/supervisor.md),
which reads the real run output for a 0-test result and is therefore runner- and
language-independent. This script just moves the cheap cases earlier (plan time)
so they don't burn an execution round."""
import json
import re
import sys


# Non-exhaustive, EXTENSIBLE registry of selective-by-name test invocations that
# EXIT 0 when the selector matches nothing (a vacuous pass). Add patterns for
# your stack. Not a definition of "the languages grillstorm supports" — just the
# common runners we can cheaply pre-screen. tier: "hard" silently green-lights
# (block); "warn" usually errors on a missing name but can still run 0 (warn).
# (pytest -k is intentionally absent: pytest exits 5 on no collection, so it is
#  NOT vacuous-passable.)
_VACUOUS_RUNNERS = [
    (r"swift\s+test\b[^|;&]*--filter\b", "hard"),       # swift
    (r"go\s+test\b[^|;&]*\s-run\b", "hard"),            # go
    (r"\b(jest|vitest)\b[^|;&]*\s-t\b", "hard"),        # js/ts
    (r"\bcargo\s+test\b[^|;&]*\s[\w:]+\s*$", "hard"),   # rust: cargo test <name>
    (r"-only-testing[:=]", "warn"),                      # xcodebuild
]
_SELECTIVE_HARD = re.compile(
    "(" + "|".join(p for p, t in _VACUOUS_RUNNERS if t == "hard") + ")", re.IGNORECASE
)
_SELECTIVE_WARN = re.compile(
    "(" + "|".join(p for p, t in _VACUOUS_RUNNERS if t == "warn") + ")", re.IGNORECASE
)

# A guard in the same command that makes it FAIL when zero tests actually ran.
_ZERO_TEST_GUARD = re.compile(
    r"(no tests to run"                          # ! grep 'no tests to run'
    r"|no matching test"                         # swift "No matching test cases were run"
    r"|executed\s+\[1-9\]"                        # grep 'Executed [1-9]'
    r"|passed\s+\[1-9\]"
    r"|with\s+\[1-9\]"
    r"|tests?\s+ran"
    r"|\bwc\s+-l\b"                               # count assertion
    r"|\bgrep\s+-[a-z]*c"                         # grep -c count
    r"|\b[1-9][0-9]*\s+tests?\b)",                # explicit positive-count assertion
    re.IGNORECASE,
)


def _selector_kind(cmd):
    """Return 'hard' | 'warn' | None for a selective-by-name test command that
    lacks a zero-test guard (i.e. is vacuous-passable). None = safe."""
    if _ZERO_TEST_GUARD.search(cmd):
        return None
    if _SELECTIVE_HARD.search(cmd):
        return "hard"
    if _SELECTIVE_WARN.search(cmd):
        return "warn"
    return None


def validate_tasks(tasks, interfaces=None):
    """Return {ok, errors, warnings}. Each task needs id, non-empty touched_paths,
    non-blank acceptance_cmd, and an acceptance_cmd that cannot pass with 0 tests.
    Optional implements/requires must be lists of strings; when `interfaces` (the
    frozen registry vocabulary) is given, every value must be in it — off-registry
    tags would silently produce wrong DAG edges downstream. Optional `resources`
    (shared-physical-resource mutex tags) must be a list of non-empty strings."""
    errors = []
    warnings = []
    for i, t in enumerate(tasks):
        tid = t.get("id")
        label = tid if tid else f"<task #{i} missing id>"
        if not tid:
            errors.append(f"{label}: missing 'id'")
        paths = t.get("touched_paths")
        if not isinstance(paths, list) or len(paths) == 0:
            errors.append(f"{label}: missing or empty 'touched_paths'")
        for field in ("implements", "requires"):
            vals = t.get(field)
            if vals is None:
                continue
            if not isinstance(vals, list) or not all(isinstance(v, str) for v in vals):
                errors.append(f"{label}: '{field}' must be a list of interface names")
                continue
            if interfaces is not None:
                for v in vals:
                    if v not in interfaces:
                        errors.append(
                            f"{label}: '{field}' has off-registry interface '{v}' "
                            f"(must come from the frozen registry vocabulary)")
        res = t.get("resources")  # optional shared-physical-resource mutex tags
        if res is not None and (
            not isinstance(res, list)
            or not all(isinstance(v, str) and v.strip() for v in res)
        ):
            errors.append(
                f"{label}: 'resources' must be a list of non-empty resource name "
                f"strings (shared physical resources needing exclusive use)")
        reality_gate = t.get("reality_gate")
        if reality_gate is not None and not isinstance(reality_gate, bool):
            errors.append(f"{label}: 'reality_gate' must be a boolean")
        runbook_ptr = t.get("runbook_ptr")
        if reality_gate is True and (not isinstance(runbook_ptr, str)
                                     or not runbook_ptr.strip()):
            errors.append(f"{label}: reality_gate task requires non-empty 'runbook_ptr'")
        if reality_gate is not True and runbook_ptr is not None:
            errors.append(f"{label}: 'runbook_ptr' requires reality_gate=true")
        cmd = t.get("acceptance_cmd")
        if not isinstance(cmd, str) or not cmd.strip():
            errors.append(f"{label}: missing or blank 'acceptance_cmd'")
            continue
        kind = _selector_kind(cmd)
        if kind == "hard":
            errors.append(
                f"{label}: VACUOUS-PASSABLE acceptance_cmd — it selects tests by name "
                f"with no zero-test guard, so a 0-match run exits 0 and passes green "
                f"without the feature working. Append an "
                f"assertion that >0 tests actually ran (fail on a 'no tests'/'0 tests' "
                f"line, or assert a positive executed-test count), or restructure so the "
                f"named test is provably created."
            )
        elif kind == "warn":
            warnings.append(
                f"{label}: acceptance_cmd uses -only-testing with no zero-test guard; "
                f"ensure the named test class exists with >=1 assertion (it can run 0 "
                f"tests if the class has no test methods)."
            )
    return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings}


def main(argv):
    path = argv[1] if len(argv) > 1 else "-"
    raw = sys.stdin.read() if path == "-" else open(path).read()
    tasks = json.loads(raw)
    if isinstance(tasks, dict):
        tasks = tasks.get("tasks", [])
    interfaces = None
    if len(argv) > 2:  # optional registry.json (the frozen interface vocabulary)
        reg = json.loads(open(argv[2]).read())
        interfaces = set(reg if isinstance(reg, list) else reg.get("interfaces", []))
    result = validate_tasks(tasks, interfaces)
    for w in result["warnings"]:
        print(f"WARN: {w}")
    if result["ok"]:
        print(f"OK: {len(tasks)} tasks carry touched_paths + non-vacuous acceptance_cmd")
        return 0
    print("BLOCKED: plan tasks failed validation (return to plan agent):")
    for e in result["errors"]:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
