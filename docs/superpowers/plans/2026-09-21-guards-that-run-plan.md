# Guards That Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every test suite and contract check tracked in this repository is run by something — the pre-commit hook or one local command — and a test goes red when a new suite is added that nothing runs.

**Architecture:** One file, `shared/suites/suites.txt`, lists every pytest invocation in the repo, one per line. `shared/suites/run_suites.sh` runs each line; `shared/suites/test_suite_coverage.py` fails when a tracked `test_*.py` is under no listed path. The sub-second guards join the pre-commit hook; the slow ones stay behind the one command. No CI: the user ruled it out. Before any of that, the one guard that is red today is brought back in line with the decision it lags behind.

**Tech Stack:** Python 3 (stdlib + pytest), bash.

**Spec:** `docs/adr/0010-seams-are-guarded-from-the-receiving-side.md` — criterion 4: "A check that no hook or pipeline invokes does not count as existing." Here the invoker is the hook, plus `shared/suites/run_suites.sh` run by hand before a release.

## Global Constraints

- Work directly on `main`, one commit per task. No worktree, no `git stash` / `checkout` / `reset`.
- Commit with an explicit pathspec (`git commit -- <paths>`): another session may stage into the same index while the hook runs.
- End every commit message with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- The pre-commit hook must keep finishing in seconds. Anything slower than about one second stays out of it and runs through `shared/suites/run_suites.sh`.
- No CI. Do not create anything under `.github/workflows/`.
- Do not push. Every task ends at a local commit.
- Do not touch `codex/meta-skill/knowledge/flow-template.py`. Its inherit policy (commit `3923ffd8`) is the decision; the guards follow it.

## Facts established on 2026-09-21 (so nobody re-derives them)

- Green today: `claude/meta-skill/tests/unit` (1370 passed, ~7 min) and every other tracked test directory.
- Red today: `shared/scripts/orchestrator/check_codex_meta_skill_parity.py` and `smoke_codex_generated_run.py` both exit 1, and 4 tests in `shared/scripts/orchestrator/test_codex_contract_checks.py` fail. Cause: `3923ffd8` changed the Codex node sandbox policy to `inherit` on purpose; both scripts still pin the old two-value policy. No hook runs them, so nothing noticed.
- `pytest pi/meta-skill` and `pytest codex/meta-skill` fail at collection because `scripts/` and `tests/` there are symlinks into the Claude tree and basenames collide. The correct invocations are `pi/meta-skill/test_contract.py` and `codex/meta-skill/test_flow.py codex/meta-skill/test_install.py`.
- `shared/scripts/orchestrator/` and `claude/meta-skill/scripts/orchestrator/` ship same-named modules whose contracts differ **on purpose** (`shared/scripts/orchestrator/test_module_isolation.py`). That is not drift and is out of scope.
- Test files under `docs/` are frozen campaign records, not live suites.

---

### Task 1: Codex execution-policy guards follow the inherit policy

**Files:**
- Modify: `shared/scripts/orchestrator/test_codex_contract_checks.py:43-63`
- Modify: `shared/scripts/orchestrator/check_codex_meta_skill_parity.py:182-187`
- Modify: `shared/scripts/orchestrator/smoke_codex_generated_run.py:65-70`

**Interfaces:**
- Consumes: the text of `codex/meta-skill/knowledge/flow-template.py`, which contains these exact lines:
  - `    if policy["sandbox"] not in {"inherit", "read-only", "workspace-write", "danger-full-access"}:`
  - `HOST_PERMISSION_FLAGS = {"--dangerously-bypass-approvals-and-sandbox"}`
  - `HOST_SANDBOX_SELECTORS = {"-s", "--sandbox", "--dangerously-bypass-approvals-and-sandbox"}`
  - `    permission = (host_permission_args() if policy["sandbox"] == "inherit"`
  - `                  else ["--sandbox", policy["sandbox"]])`
- Produces: both check scripts exit 0 on the current tree and exit 1 with an error containing the word `sandbox` for each of four damages: `bypass`, `missing_policy`, `unrestricted_policy`, `inherit_dropped`.

What the guard now means: the driver may *recognise* the bypass flag on the host's command line and pass it through, but may never add it itself; an explicit policy is still passed as `--sandbox`; the accepted policy values are exactly the four above; `inherit` really reads the host.

- [ ] **Step 1: Update the damage cases in the test**

In `shared/scripts/orchestrator/test_codex_contract_checks.py`, replace the `test_execution_policy_regressions_are_rejected` function and its two decorators with:

```python
ACCEPTED_POLICIES = 'policy["sandbox"] not in {"inherit", "read-only", "workspace-write", "danger-full-access"}'


@pytest.mark.parametrize("script", [PARITY, SMOKE])
@pytest.mark.parametrize("damage", ["bypass", "missing_policy", "unrestricted_policy", "inherit_dropped"])
def test_execution_policy_regressions_are_rejected(snapshot, tmp_path, script, damage):
    root = tmp_path / "repo"
    shutil.copytree(snapshot, root, symlinks=True)
    path = root / "codex/meta-skill/knowledge/flow-template.py"
    text = path.read_text()
    if damage == "bypass":
        # The driver adds the bypass itself instead of only recognising it on the host command line.
        text = text.replace('"--sandbox", policy["sandbox"]',
                            '"--dangerously-bypass-approvals-and-sandbox"')
    elif damage == "missing_policy":
        text = text.replace('"--sandbox", policy["sandbox"]', '"--quiet"')
    elif damage == "unrestricted_policy":
        text = text.replace(ACCEPTED_POLICIES, ACCEPTED_POLICIES[:-1] + ', "unrestricted"}')
    else:
        text = text.replace('host_permission_args() if policy["sandbox"] == "inherit"',
                            '[] if policy["sandbox"] == "inherit"')
    assert text != path.read_text(), "fixture mutation did not apply"
    path.write_text(text)
    code, report = run_check(root, script)
    assert code == 1, report
    assert report["passed"] is False
    assert any("sandbox" in error for error in report["errors"]), report
```

- [ ] **Step 2: Run the tests and confirm they fail for the right reason**

Run: `python3 -B -m pytest -q -p no:cacheprovider shared/scripts/orchestrator/test_codex_contract_checks.py`
Expected: FAIL. `test_current_bundle_contract_passes[...]` fails for both scripts with the two errors `flow template must not automatically bypass approvals and sandbox` and `flow template does not reject unsupported sandbox escalation`. (Damage cases may pass by accident, because the stale checks already report a `sandbox` error on every tree.)

- [ ] **Step 3: Update the parity script**

In `shared/scripts/orchestrator/check_codex_meta_skill_parity.py`, replace these six lines:

```python
    if "--dangerously-bypass-approvals-and-sandbox" in flow_template_text:
        errors.append("flow template must not automatically bypass approvals and sandbox")
    if '"--sandbox", policy["sandbox"]' not in flow_template_text:
        errors.append("flow template does not pass its explicit sandbox policy to Codex")
    if 'policy["sandbox"] not in {"read-only", "workspace-write"}' not in flow_template_text:
        errors.append("flow template does not reject unsupported sandbox escalation")
```

with:

```python
    # Nodes inherit the host session's permissions (3923ffd8). The driver may recognise the bypass flag
    # on the host command line and pass it on; it may never add the flag itself.
    bypass_lines = [line.strip() for line in flow_template_text.splitlines()
                    if "--dangerously-bypass-approvals-and-sandbox" in line]
    if any(not line.startswith(("HOST_PERMISSION_FLAGS =", "HOST_SANDBOX_SELECTORS ="))
           for line in bypass_lines):
        errors.append("flow template must not add the approvals-and-sandbox bypass itself")
    if '"--sandbox", policy["sandbox"]' not in flow_template_text:
        errors.append("flow template does not pass its explicit sandbox policy to Codex")
    if ('policy["sandbox"] not in {"inherit", "read-only", "workspace-write", "danger-full-access"}'
            not in flow_template_text):
        errors.append("flow template does not reject unsupported sandbox escalation")
    if 'host_permission_args() if policy["sandbox"] == "inherit"' not in flow_template_text:
        errors.append("flow template does not read the host session for the inherit sandbox policy")
```

- [ ] **Step 4: Update the smoke script**

In `shared/scripts/orchestrator/smoke_codex_generated_run.py`, replace these six lines (they are indented eight spaces; keep that indentation):

```python
        if "--dangerously-bypass-approvals-and-sandbox" in flow_text:
            errors.append("flow template must not automatically bypass approvals and sandbox")
        if '"--sandbox", policy["sandbox"]' not in flow_text:
            errors.append("flow template does not use its explicit sandbox policy")
        if 'policy["sandbox"] not in {"read-only", "workspace-write"}' not in flow_text:
            errors.append("flow template does not reject unsupported sandbox escalation")
```

with:

```python
        # Nodes inherit the host session's permissions (3923ffd8): recognise the bypass flag, never add it.
        bypass_lines = [line.strip() for line in flow_text.splitlines()
                        if "--dangerously-bypass-approvals-and-sandbox" in line]
        if any(not line.startswith(("HOST_PERMISSION_FLAGS =", "HOST_SANDBOX_SELECTORS ="))
               for line in bypass_lines):
            errors.append("flow template must not add the approvals-and-sandbox bypass itself")
        if '"--sandbox", policy["sandbox"]' not in flow_text:
            errors.append("flow template does not use its explicit sandbox policy")
        if ('policy["sandbox"] not in {"inherit", "read-only", "workspace-write", "danger-full-access"}'
                not in flow_text):
            errors.append("flow template does not reject unsupported sandbox escalation")
        if 'host_permission_args() if policy["sandbox"] == "inherit"' not in flow_text:
            errors.append("flow template does not read the host session for the inherit sandbox policy")
```

- [ ] **Step 5: Run the tests and both scripts**

Run: `python3 -B -m pytest -q -p no:cacheprovider shared/scripts/orchestrator`
Expected: `157 passed` — the 151 that passed before, the 4 that were red, and the 2 new `inherit_dropped` cases.

Run: `python3 -B shared/scripts/orchestrator/check_codex_meta_skill_parity.py; echo $?` and `python3 -B shared/scripts/orchestrator/smoke_codex_generated_run.py; echo $?`
Expected: both print `"passed": true` and `0`.

- [ ] **Step 6: Commit**

```bash
git commit -F - -- shared/scripts/orchestrator/test_codex_contract_checks.py shared/scripts/orchestrator/check_codex_meta_skill_parity.py shared/scripts/orchestrator/smoke_codex_generated_run.py <<'EOF'
fix(codex): 执行策略守卫跟上「继承宿主权限」，parity 与 smoke 不再悄悄红着

3923ffd8 有意把节点沙箱策略改成 inherit，两份检查脚本和 4 条测试还钉着旧的两值策略；
没有任何钩子跑它们，于是没人发现。守卫的含义改为：驱动可以识别并透传宿主命令行上的
bypass，但不得自己加；显式策略仍以 --sandbox 传入；可接受的取值正好四个；inherit 真的读宿主。
新增 inherit_dropped 破坏用例。

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```

---

### Task 2: One list of suites, and a test that notices an unlisted suite

**Files:**
- Create: `shared/suites/test_suite_coverage.py`
- Create: `shared/suites/suites.txt`
- Create: `shared/suites/run_suites.sh`

**Interfaces:**
- Consumes: nothing from Task 1 except a green tree.
- Produces: `shared/suites/suites.txt` — one pytest invocation per line (space-separated paths relative to the repo root; blank lines and lines starting with `#` ignored). `shared/suites/run_suites.sh` — runs every line, exits non-zero if any line failed. Task 3 calls both by these exact paths.

- [ ] **Step 1: Write the failing test**

Create `shared/suites/test_suite_coverage.py`:

```python
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
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `python3 -B -m pytest -q -p no:cacheprovider shared/suites`
Expected: FAIL — `FileNotFoundError: ... shared/suites/suites.txt`.

- [ ] **Step 3: Write the suite list**

Create `shared/suites/suites.txt`:

```text
# One pytest invocation per line; paths are relative to the repo root.
# Same-named test files live in several directories (test_mirrors.py, test_render_report.py),
# so each directory is its own run. test_suite_coverage.py beside this file fails when a tracked test file
# is under none of these paths.
claude/meta-skill/tests/unit
claude/meta-skill/scripts/engine
claude/meta-skill/scripts/visual
claude/superstorm/scripts
claude/superstorm/knowledge/cross-exam/engine
claude/superstorm/knowledge/cross-exam/visual
claude/grillstorm/skills/grillstorm/scripts
# codex/meta-skill and pi/meta-skill hold symlinks into the Claude tree: name the files, not the dir.
codex/meta-skill/test_flow.py codex/meta-skill/test_install.py
codex/cross-exam-skill/scripts
codex/cross-exam-skill/engine
codex/cross-exam-skill/visual
codex/grillstorm/scripts
codex/superstorm-skill/scripts
pi/meta-skill/test_contract.py
pi/cross-exam
shared/evidence-engine
shared/visual-acceptance
shared/keep-code-simple
shared/scripts/orchestrator
shared/scripts/code-replicate
shared/scripts/product-design
shared/suites
```

- [ ] **Step 4: Write the runner**

Create `shared/suites/run_suites.sh`:

```bash
#!/usr/bin/env bash
# Runs every line of shared/suites/suites.txt as its own pytest invocation. Keeps going after a failure so one
# red suite does not hide another, and exits non-zero if any line failed.
set -uo pipefail
cd "$(dirname "$0")/../.."

status=0
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in ''|'#'*) continue ;; esac
  echo "[suites] $line"
  # Word splitting is intended: a line may name several test files.
  # shellcheck disable=SC2086
  env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_PREFIX \
    python3 -B -m pytest -q -p no:cacheprovider $line || { echo "[suites] FAILED: $line" >&2; status=1; }
done < shared/suites/suites.txt
exit "$status"
```

Then: `chmod +x shared/suites/run_suites.sh`

- [ ] **Step 5: Run the coverage test, then the whole list**

Run: `python3 -B -m pytest -q -p no:cacheprovider shared/suites`
Expected: `3 passed`.

Run: `shared/suites/run_suites.sh` (about 9 minutes; `claude/meta-skill/tests/unit` alone is ~7)
Expected: exit 0, no `[suites] FAILED` line.

- [ ] **Step 6: Prove the coverage test catches an orphan**

```bash
mkdir -p shared/zz-orphan && printf 'def test_x():\n    assert True\n' > shared/zz-orphan/test_orphan.py
git add shared/zz-orphan/test_orphan.py
python3 -B -m pytest -q -p no:cacheprovider shared/suites
```
Expected: FAIL naming `shared/zz-orphan/test_orphan.py`.

Then undo exactly what was added: `git rm -q --cached shared/zz-orphan/test_orphan.py && rm -r shared/zz-orphan`, and rerun `python3 -B -m pytest -q -p no:cacheprovider shared/suites` → `3 passed`. Confirm `git status --short` shows only the three new `shared/suites/` files.

- [ ] **Step 7: Commit**

```bash
git add shared/suites/test_suite_coverage.py shared/suites/suites.txt shared/suites/run_suites.sh
git commit -F - -- shared/suites/test_suite_coverage.py shared/suites/suites.txt shared/suites/run_suites.sh <<'EOF'
test(suites): 仓库里每个测试目录列进 shared/suites/suites.txt，没列进去的测试文件会让覆盖测试变红

ADR-0010 第四条：没有钩子或流水线调用的检查不算存在。suites.txt 一行一次 pytest 调用
（同名测试文件分目录跑），run_suites.sh 逐行执行且不因前一个失败而跳过后面的，
test_suite_coverage.py 用 git ls-files 对照清单。docs/ 下的是封存的战役记录，不算活的套件。

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```

---

### Task 3: The sub-second guards join the pre-commit hook

**Files:**
- Modify: `.githooks/pre-commit` (the `run_pytest shared/visual-acceptance` line, and the block of `python3 .../validate_*.py` lines)
- Modify: `CLAUDE.md` (new `## Tests` section, inserted directly before `## Skill Development Conventions`)

**Interfaces:**
- Consumes: `shared/suites/` from Task 2; green parity and smoke scripts from Task 1.
- Produces: a hook that also runs `shared/keep-code-simple`, `pi/meta-skill/test_contract.py`, `pi/cross-exam`, `shared/suites`, and both Codex contract scripts. Measured cost of all six together: under one second.

- [ ] **Step 1: Add the four fast suites**

In `.githooks/pre-commit`, directly after the line `run_pytest shared/visual-acceptance`, add:

```bash
run_pytest shared/keep-code-simple             # mirror contract of the shared protocol
run_pytest pi/meta-skill/test_contract.py      # name the file: scripts/ there is a symlink and basenames collide
run_pytest pi/cross-exam
run_pytest shared/suites                             # every tracked test file is listed in shared/suites/suites.txt
```

- [ ] **Step 2: Add the two Codex contract scripts**

Directly after the line `python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py`, add:

```bash

# These two kept pinning the Codex sandbox policy that 3923ffd8 replaced, and sat red with nothing
# running them. They take ~30 ms each.
echo "[pre-commit] codex bundle contract"
python3 -B shared/scripts/orchestrator/check_codex_meta_skill_parity.py >/dev/null \
  || { python3 -B shared/scripts/orchestrator/check_codex_meta_skill_parity.py; exit 1; }
python3 -B shared/scripts/orchestrator/smoke_codex_generated_run.py >/dev/null \
  || { python3 -B shared/scripts/orchestrator/smoke_codex_generated_run.py; exit 1; }
```

(The scripts print a JSON report on success too; the first call silences it, the second shows it only on failure.)

- [ ] **Step 3: Update the hook's closing comment about where the rest runs**

Replace the final `echo` line of the hook with:

```bash
echo "[pre-commit] ok — 快速子集已跑；全部套件（含 ~7 分钟的 meta-skill 全量单测）发版前手动跑: shared/suites/run_suites.sh"
```

- [ ] **Step 4: Run the hook by hand**

Run: `bash .githooks/pre-commit`
Expected: exit 0; output includes `[pre-commit] codex bundle contract` and the new closing line; wall time still a few seconds more than before, not minutes.

- [ ] **Step 5: Prove the new guard bites**

```bash
BAK="${TMPDIR:-/tmp}/parity.bak"; cp shared/scripts/orchestrator/check_codex_meta_skill_parity.py "$BAK"
python3 - <<'EOF'
p = "shared/scripts/orchestrator/check_codex_meta_skill_parity.py"
s = open(p).read()
open(p, "w").write(s.replace('"danger-full-access"}', '"danger-full-access", "x"}', 1))
EOF
bash .githooks/pre-commit; echo "exit=$?"
cp "$BAK" shared/scripts/orchestrator/check_codex_meta_skill_parity.py
```
Expected: `exit=1` with the JSON report showing `flow template does not reject unsupported sandbox escalation`. After the restore, `git status --short` shows only `.githooks/pre-commit` modified.

- [ ] **Step 6: Document where tests run**

In `CLAUDE.md`, directly before the line `## Skill Development Conventions`, insert:

```markdown
## Tests

`.githooks/pre-commit` runs the fast guards on every commit (seconds). `shared/suites/run_suites.sh` runs every suite in the repo from `shared/suites/suites.txt` (~9 minutes, most of it `claude/meta-skill/tests/unit`); run it by hand before a release or after a `claude/meta-skill` change. There is no CI and none is to be added — a guard that must run automatically goes in the hook. A new test directory must be added to `shared/suites/suites.txt`; `shared/suites/test_suite_coverage.py` fails until it is (ADR-0010: a check nothing invokes does not exist).

```

- [ ] **Step 7: Commit**

```bash
git commit -F - -- .githooks/pre-commit CLAUDE.md <<'EOF'
chore(hooks): 亚秒级的守卫进 pre-commit——keep-code-simple、pi 契约、套件覆盖、codex 包契约

这六项合计不到一秒。parity 与 smoke 两个脚本在 3923ffd8 之后红着没人知道，
正是因为没有任何钩子跑它们。慢的套件不进钩子，发版前用 shared/suites/run_suites.sh 手动跑。

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```

---

## Out of scope — each needs its own design first

These came out of the same seam survey. They are independent of this plan and of each other.

1. **product-review's freshness check on prior records.** `docs/experience-review/runtime.md` carries `被评提交` (a git sha), so staleness is checkable with `git log <sha>..HEAD`. `docs/cross-exam/*/completion-report.md` does not state which build it judged in its header (`claude/superstorm/scripts/render_report.py:625`), although each ledger entry carries `build`. Making that seam checkable means changing the renderer in both mirrors, then product-review's text.
2. **No mechanical check when a consumer node starts.** `validation_commands` run when the producer finishes. Whether the orchestrator should re-run an upstream artifact's commands before dispatching its consumer is a design question about `check_artifacts.py` and freshness, not a text edit.
3. **`check_requires.py` reads `state-machine.json`.** The Codex and Pi adapters document that file as legacy, read only for old outputs; `CLAUDE.md:75` still names it as what bootstrap generates. Decide whether legacy support stays, then either delete the script with its tests or correct the docs.
