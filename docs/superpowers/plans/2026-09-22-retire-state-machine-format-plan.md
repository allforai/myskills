# Retire the state-machine.json Format Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A bootstrap directory that holds only the retired `state-machine.json` format is refused with a named error instead of passing validation, and the code and documents that exist only for that format are gone.

**Architecture:** Both `validate_bootstrap.py` files (the shared one and the Claude one — they differ on purpose and are tested separately) replace their silent "old format, skip validation" branch with an error. Then the three files nothing invokes any more are deleted with their tests, and the five documents that still describe the old format are corrected.

**Tech Stack:** Python 3 (stdlib + pytest), Markdown.

**Spec:** `docs/adr/0010-seams-are-guarded-from-the-receiving-side.md` — criterion 3: "Unchecked is its own outcome. A receiver that could not complete its check … returns that, distinctly. It is not a pass." The user decided on 2026-09-22 to drop legacy support rather than keep it.

## Global Constraints

- Work directly on `main`, one commit per task. No worktree, no `git stash` / `checkout` / `reset` / `restore` / `clean`.
- Commit with an explicit pathspec (`git commit -F - -- <paths>`): another session may stage into the same index while the hook runs. Never `--no-verify`.
- End every commit message with exactly `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` — do not substitute another model name.
- No CI. Do not create anything under `.github/`. Do not push.
- `codex/meta-skill/scripts` and `pi/meta-skill/scripts` are symlinks to `claude/meta-skill/scripts`; editing or deleting the Claude file is the whole change for all three hosts.
- The error string is exactly: `retired_bootstrap_format: state-machine.json is no longer supported; rerun /bootstrap to generate workflow.json`

## Facts established on 2026-09-22

- Nothing in the repository writes `state-machine.json`. No skill, command, or orchestrator template calls `check_requires.py`; only tests import it. `check_artifacts.py` describes itself as "Simplified from check_requires.py".
- Reproduced: a directory containing only `state-machine.json` (content `{}`) makes both `shared/scripts/orchestrator/validate_bootstrap.py` and `claude/meta-skill/scripts/orchestrator/validate_bootstrap.py` print `{"errors": [], "passed": true}` and exit 0. No test covers that branch in either tree.
- `shared/scripts/orchestrator/visualize.py` reads only `state-machine.json` and is referenced by nothing.
- `shared/scripts/orchestrator/check_requires.py` and `claude/meta-skill/scripts/orchestrator/check_requires.py` differ from each other; both go.
- No installer, package manifest, or contract test names `check_requires` or `visualize`, and no test pins the documents' "backward compatibility" sentences.
- `claude/meta-skill/skills/bootstrap/SKILL.md` no longer mentions `state-machine.json` at all.

---

### Task 1: Both validators refuse the retired format

**Files:**
- Modify: `shared/scripts/orchestrator/validate_bootstrap.py` (the `else:` branch in `main()` holding `pass  # backward compat: old format, skip validation`)
- Modify: `claude/meta-skill/scripts/orchestrator/validate_bootstrap.py` (the identical branch near the end of `main()`)
- Test: `shared/scripts/orchestrator/test_validate_bootstrap.py`
- Test: `claude/meta-skill/tests/unit/test_validate_bootstrap.py`

**Interfaces:**
- Consumes: in the Claude test file, the existing module-level `HOSTS = ["claude", "codex"]` and the existing helper `_main_report(host, bdir)` which returns `(returncode, report_dict)`.
- Produces: both scripts exit 1 and list the exact error string from Global Constraints when `workflow.json` is absent and `state-machine.json` is present. A directory with neither file keeps today's error `workflow.json not found`.

- [ ] **Step 1: Write the failing test for the shared validator**

Append to `shared/scripts/orchestrator/test_validate_bootstrap.py`, directly above the final `if __name__ == "__main__":` line:

```python
RETIRED_FORMAT_ERROR = ("retired_bootstrap_format: state-machine.json is no longer supported; "
                        "rerun /bootstrap to generate workflow.json")


class TestRetiredFormat(unittest.TestCase):
    """A directory that holds only the retired format is refused, never waved through."""

    def setUp(self):
        self._dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._dir)

    def _run(self):
        script = os.path.join(module_dir(), "validate_bootstrap.py")
        result = subprocess.run([sys.executable, "-B", script, self._dir],
                                capture_output=True, text=True)
        return result.returncode, json.loads(result.stdout)

    def test_state_machine_only_is_refused_by_name(self):
        _write_json(os.path.join(self._dir, "state-machine.json"), {})
        code, report = self._run()
        self.assertEqual(code, 1, report)
        self.assertFalse(report["passed"])
        self.assertEqual(report["errors"], [RETIRED_FORMAT_ERROR])

    def test_empty_directory_still_reports_the_missing_workflow(self):
        code, report = self._run()
        self.assertEqual(code, 1, report)
        self.assertEqual(report["errors"], ["workflow.json not found"])
```

- [ ] **Step 2: Write the failing test for the Claude validator**

Append to the end of `claude/meta-skill/tests/unit/test_validate_bootstrap.py`:

```python
RETIRED_FORMAT_ERROR = ("retired_bootstrap_format: state-machine.json is no longer supported; "
                        "rerun /bootstrap to generate workflow.json")


@pytest.mark.parametrize("host", HOSTS)
def test_main_refuses_a_directory_that_holds_only_the_retired_format(tmp_path, host):
    """"Could not check" is not "passed": the old format used to skip validation and exit 0."""
    bdir = tmp_path / "bootstrap"
    bdir.mkdir()
    (bdir / "state-machine.json").write_text("{}")

    returncode, report = _main_report(host, bdir)

    assert returncode == 1, report
    assert report["passed"] is False, report
    assert RETIRED_FORMAT_ERROR in report["errors"], report
```

- [ ] **Step 3: Run both and confirm they fail for the right reason**

Run: `python3 -B -m pytest -q -p no:cacheprovider shared/scripts/orchestrator/test_validate_bootstrap.py -k RetiredFormat`
Expected: `test_state_machine_only_is_refused_by_name` FAILS with `0 != 1` (the script exits 0 today); `test_empty_directory_still_reports_the_missing_workflow` PASSES.

Run: `python3 -B -m pytest -q -p no:cacheprovider claude/meta-skill/tests/unit/test_validate_bootstrap.py -k retired_format`
Expected: 2 FAILED (one per host) with `assert 0 == 1`.

- [ ] **Step 4: Replace the branch in both validators**

In **both** `shared/scripts/orchestrator/validate_bootstrap.py` and `claude/meta-skill/scripts/orchestrator/validate_bootstrap.py`, replace:

```python
        sm_path = os.path.join(bdir, "state-machine.json")
        if os.path.exists(sm_path):
            pass  # backward compat: old format, skip validation
        else:
            errors.append("workflow.json not found")
```

with:

```python
        if os.path.exists(os.path.join(bdir, "state-machine.json")):
            # The retired format used to skip validation and pass. Nothing generates or executes it
            # any more, and "could not check" is not "passed" (ADR-0010).
            errors.append("retired_bootstrap_format: state-machine.json is no longer supported; "
                          "rerun /bootstrap to generate workflow.json")
        else:
            errors.append("workflow.json not found")
```

- [ ] **Step 5: Run the tests again**

Run: `python3 -B -m pytest -q -p no:cacheprovider shared/scripts/orchestrator/test_validate_bootstrap.py claude/meta-skill/tests/unit/test_validate_bootstrap.py`
Expected: 0 failed.

- [ ] **Step 6: Commit**

```bash
git commit -F - -- shared/scripts/orchestrator/validate_bootstrap.py shared/scripts/orchestrator/test_validate_bootstrap.py claude/meta-skill/scripts/orchestrator/validate_bootstrap.py claude/meta-skill/tests/unit/test_validate_bootstrap.py <<'EOF'
fix(meta-skill): 只有旧格式 state-machine.json 的目录不再被校验器悄悄放行

两份 validate_bootstrap 遇到没有 workflow.json、只有 state-machine.json 的目录时
跳过校验并报 passed: true——把「没法检查」报成了「没问题」（ADR-0010 第三条）。
已经没有任何东西生成或执行这个格式，改为点名报错 retired_bootstrap_format 并提示重跑 /bootstrap。

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```

---

### Task 2: Delete what only the retired format used

**Files:**
- Delete: `shared/scripts/orchestrator/check_requires.py`
- Delete: `claude/meta-skill/scripts/orchestrator/check_requires.py`
- Delete: `shared/scripts/orchestrator/test_check_requires.py`
- Delete: `shared/scripts/orchestrator/visualize.py`
- Modify: `shared/scripts/orchestrator/test_integration.py` (whole file replaced)
- Modify: `shared/scripts/orchestrator/test_module_isolation.py` (docstring line naming the modules; the `CONTAMINABLE` tuple)
- Modify: `shared/scripts/orchestrator/_module_isolation.py` (docstring line naming the modules)
- Modify: `claude/meta-skill/tests/module_isolation.py` (docstring line naming the modules)
- Modify: `shared/scripts/orchestrator/check_artifacts.py:2` and `claude/meta-skill/scripts/orchestrator/check_artifacts.py:2` (docstring's first line)

**Interfaces:**
- Consumes: Task 1's validators (unchanged by this task).
- Produces: no file named `check_requires.py` or `visualize.py` remains tracked; `shared/scripts/orchestrator/test_integration.py` keeps one test, `test_validation_passes`, built on `workflow.json` only.

- [ ] **Step 1: Confirm nothing else references the files about to go**

Run:
```bash
git grep -n "check_requires\|visualize\.py" -- ':!docs/' ':!**/node_modules/**' | grep -v "^shared/scripts/orchestrator/check_requires.py\|^claude/meta-skill/scripts/orchestrator/check_requires.py\|^shared/scripts/orchestrator/test_check_requires.py\|^shared/scripts/orchestrator/visualize.py"
```
Expected: only lines in these files — `shared/scripts/orchestrator/test_integration.py`, `shared/scripts/orchestrator/test_module_isolation.py`, `shared/scripts/orchestrator/_module_isolation.py`, `claude/meta-skill/tests/module_isolation.py`, and the two `check_artifacts.py` docstrings. If any other file appears, stop and report it instead of continuing.

- [ ] **Step 2: Replace the integration test**

Overwrite `shared/scripts/orchestrator/test_integration.py` with:

```python
#!/usr/bin/env python3
"""Integration test: create mock bootstrap products and validate them."""

import json
import os
import shutil
import tempfile
import unittest

from _module_isolation import load, module_dir

_validate_bootstrap = load(module_dir(), "validate_bootstrap")
validate_node_spec = _validate_bootstrap.validate_node_spec
validate_workflow = _validate_bootstrap.validate_workflow

NODE_IDS = ("discovery", "generate")


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.bootstrap_dir = os.path.join(self.tmpdir, "bootstrap")
        self.specs_dir = os.path.join(self.bootstrap_dir, "node-specs")
        os.makedirs(self.specs_dir)

        self.wf = {
            "nodes": [
                {"id": nid, "goal": "Do " + nid, "exit_artifacts": ["artifacts/" + nid + ".json"]}
                for nid in NODE_IDS
            ],
            "transition_log": [],
        }
        self.wf_path = os.path.join(self.bootstrap_dir, "workflow.json")
        with open(self.wf_path, "w") as f:
            json.dump(self.wf, f)

        for nid in NODE_IDS:
            with open(os.path.join(self.specs_dir, f"{nid}.md"), "w") as f:
                f.write("---\nnode: {}\n---\n\n# Task: {}\nDo the thing.".format(nid, nid))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_validation_passes(self):
        errors = validate_workflow(self.wf_path)
        self.assertEqual(errors, [], f"workflow.json errors: {errors}")

        for fname in os.listdir(self.specs_dir):
            path = os.path.join(self.specs_dir, fname)
            errors = validate_node_spec(path)
            self.assertEqual(errors, [], f"Node-spec errors for {fname}: {errors}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Delete the four files**

```bash
git rm -q shared/scripts/orchestrator/check_requires.py claude/meta-skill/scripts/orchestrator/check_requires.py shared/scripts/orchestrator/test_check_requires.py shared/scripts/orchestrator/visualize.py
```

- [ ] **Step 4: Remove the name from the module-isolation lists and the two docstrings**

In `shared/scripts/orchestrator/test_module_isolation.py`:
- replace `` `validate_bootstrap` (and `check_artifacts`, `check_requires`, `loop_detection`) whose `` with `` `validate_bootstrap` (and `check_artifacts`, `loop_detection`) whose ``
- replace `CONTAMINABLE = ("validate_bootstrap", "check_artifacts", "check_requires", "loop_detection")` with `CONTAMINABLE = ("validate_bootstrap", "check_artifacts", "loop_detection")`

In `shared/scripts/orchestrator/_module_isolation.py`, replace `` `check_artifacts`, `check_requires`, `loop_detection`, `` with `` `check_artifacts`, `loop_detection`, ``.

In `claude/meta-skill/tests/module_isolation.py`, replace `` `validate_bootstrap`, `check_artifacts`, `check_requires` and `loop_detection` with `` with `` `validate_bootstrap`, `check_artifacts` and `loop_detection` with ``.

In **both** `shared/scripts/orchestrator/check_artifacts.py` and `claude/meta-skill/scripts/orchestrator/check_artifacts.py`, replace the first docstring line `"""Check exit_artifacts for workflow nodes. Simplified from check_requires.py.` with `"""Check exit_artifacts for workflow nodes.`

- [ ] **Step 5: Run the suites these files belong to**

Run: `python3 -B -m pytest -q -p no:cacheprovider shared/scripts/orchestrator shared/suites`
Expected: 0 failed. (The count drops by the deleted `test_check_requires.py` tests and the two removed integration tests.)

Run: `python3 -B -m pytest -q -p no:cacheprovider claude/meta-skill/tests/unit/test_check_artifacts.py claude/meta-skill/tests/unit/test_validate_bootstrap.py`
Expected: 0 failed.

Run the Step 1 `git grep` again.
Expected: no output.

- [ ] **Step 6: Commit**

```bash
git add shared/scripts/orchestrator/test_integration.py shared/scripts/orchestrator/test_module_isolation.py shared/scripts/orchestrator/_module_isolation.py claude/meta-skill/tests/module_isolation.py shared/scripts/orchestrator/check_artifacts.py claude/meta-skill/scripts/orchestrator/check_artifacts.py
git commit -F - -- shared/scripts/orchestrator/check_requires.py claude/meta-skill/scripts/orchestrator/check_requires.py shared/scripts/orchestrator/test_check_requires.py shared/scripts/orchestrator/visualize.py shared/scripts/orchestrator/test_integration.py shared/scripts/orchestrator/test_module_isolation.py shared/scripts/orchestrator/_module_isolation.py claude/meta-skill/tests/module_isolation.py shared/scripts/orchestrator/check_artifacts.py claude/meta-skill/scripts/orchestrator/check_artifacts.py <<'EOF'
chore(meta-skill): 删掉只为旧格式 state-machine.json 存在的代码

check_requires.py（两份，内容还不一样）只有测试在调用，check_artifacts 早已接替它；
visualize.py 只读旧格式且没有任何东西引用。连同 test_check_requires.py 一起删除，
test_integration.py 留下只基于 workflow.json 的那条，模块隔离清单去掉 check_requires。

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```

---

### Task 3: The documents stop describing the retired format

**Files:**
- Modify: `CLAUDE.md` (the "User workflow:" line under "Claude Meta-Skill Structure")
- Modify: `codex/meta-skill/AGENTS.md` (the `state-machine.json` bullet)
- Modify: `codex/meta-skill/execution-playbook.md` (the `state-machine.json` paragraph)
- Modify: `codex/meta-skill/skills/bootstrap.md` (section "3. Canonical Bootstrap Graph")
- Modify: `pi/meta-skill/skills/bootstrap/SKILL.md` (the sentence after 写 `.allforai/bootstrap/workflow.json`)

**Interfaces:**
- Consumes: the error name `retired_bootstrap_format` from Task 1.
- Produces: no tracked document outside `docs/` says `state-machine.json` is generated, or is read for compatibility.

- [ ] **Step 1: Make the five replacements**

`CLAUDE.md` — replace
`generates `.allforai/bootstrap/` (state-machine.json + node-specs)`
with
`generates `.allforai/bootstrap/` (workflow.json + node-specs)`

`codex/meta-skill/AGENTS.md` — replace
`- `state-machine.json` may only be read for backward compatibility during migration.`
with
`- `state-machine.json` is a retired format: the validator refuses a directory that holds only it (`retired_bootstrap_format`); rerun bootstrap.`

`codex/meta-skill/execution-playbook.md` — replace
`` `state-machine.json` is not the primary contract. It may only be read for backward compatibility while older bootstrap outputs still exist. ``
with
`` `state-machine.json` is a retired format. Nothing reads it; a bootstrap directory that holds only it fails validation with `retired_bootstrap_format` and must be regenerated. ``

`codex/meta-skill/skills/bootstrap.md` — replace these lines

```
When the canonical protocol mentions `state-machine.json`, treat that as legacy wording.

For Codex generation:

- write `.allforai/bootstrap/workflow.json`
- validate against `workflow.json`
- only read `state-machine.json` for backward compatibility if older outputs exist
```

with

```
For Codex generation:

- write `.allforai/bootstrap/workflow.json`
- validate against `workflow.json`
- `state-machine.json` is a retired format; if a target project still has one and no `workflow.json`, regenerate — the validator refuses it (`retired_bootstrap_format`)
```

`pi/meta-skill/skills/bootstrap/SKILL.md` — replace
`` `state-machine.json` 只在旧产物存在时为兼容而读。``
with
`` `state-machine.json` 是已退役的格式：只剩它而没有 `workflow.json` 的目录会被校验器以 `retired_bootstrap_format` 拒绝，重跑 bootstrap 即可。``

- [ ] **Step 2: Check nothing still describes it as live, and the contract checks still pass**

Run: `git grep -n "state-machine.json" -- ':!docs/' ':!**/node_modules/**' ':!*.py'`
Expected: exactly four lines — `codex/meta-skill/AGENTS.md`, `codex/meta-skill/execution-playbook.md`, `codex/meta-skill/skills/bootstrap.md`, `pi/meta-skill/skills/bootstrap/SKILL.md` — each now saying "retired" / 已退役. `CLAUDE.md` no longer mentions the file at all.

Run: `python3 -B shared/scripts/orchestrator/check_codex_meta_skill_parity.py >/dev/null; echo $?` and `python3 -B -m pytest -q -p no:cacheprovider pi/meta-skill/test_contract.py codex/meta-skill/test_install.py`
Expected: `0`, and 0 failed.

- [ ] **Step 3: Commit**

```bash
git commit -F - -- CLAUDE.md codex/meta-skill/AGENTS.md codex/meta-skill/execution-playbook.md codex/meta-skill/skills/bootstrap.md pi/meta-skill/skills/bootstrap/SKILL.md <<'EOF'
docs(meta-skill): state-machine.json 写明是已退役格式，不再说「生成」或「为兼容而读」

CLAUDE.md 还把它写成 bootstrap 的产物；codex 与 pi 的文档说它「为兼容而读」，
而实际上已经没有任何东西读它。统一改为：已退役，校验器以 retired_bootstrap_format 拒绝。

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```
