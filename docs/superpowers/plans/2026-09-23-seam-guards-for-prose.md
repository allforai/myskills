# Seam Guards for the Prose Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a shared run-contract rule changes in its authoritative file, every copy goes red until someone revisits it; and every shell snippet a run template hands its driver is either executed by a test against the real helpers or explicitly declared illustrative.

**Architecture:** Two guards. (1) Every ```` ```bash ```` block in the three orchestrator templates is preceded by `<!-- snippet:<name> -->` (a test extracts and runs it against a bootstrapped fixture) or `<!-- illustrative: <reason> -->`; an unclassified block, or a snippet name no test executes, is red. (2) `shared/seam-contracts/clauses.json` registers each shared rule: the authority file holds the rule between `clause-begin:<id>` / `clause-end:<id>` markers, and every copy carries a stamp `clause:<id>@<hash>` of that section plus the phrases it must keep. Editing the authority section changes the hash, so every copy is red until its stamp is renewed — the author is forced to visit each copy. The pre-commit hook runs both.

**Tech Stack:** Python 3 stdlib, pytest, bash; no new dependencies.

**Spec:** `docs/adr/0010-seams-are-guarded-from-the-receiving-side.md` (criterion 1 "the receiver verifies", 2 "what crosses is checkable", 4 "every copy has a drift check that runs"), plus the 2026-09-23 seam review and its closed-loop self-review (§ Self-review record at the end). Incidents this plan must catch on replay: `85776b36` changed the `user_steps` rule and left six copies stale; `ed8d5d5f` and `98aa98e9` each changed the Claude template's repair-ledger section and neither reached the Codex template; `053ccbd5` added a Pi publish step that runs after the gate that needs it and verifies with a command that always exits 0; `cffc1115` changed the Pi parallel-dispatch predicate and left Core Loop step 4 stating the old one.

## Global Constraints

- Work directly on `main`, one commit per task; never stash, checkout or reset in this checkout.
- Commit with an explicit pathspec (`git commit -- <paths>`): another session may stage into the same index while the hook runs.
- No CI. Automatic guards go in `.githooks/pre-commit`; every new test directory goes in `shared/suites/suites.txt` (`shared/suites/test_suite_coverage.py` fails otherwise).
- Python 3 standard library only; tests use pytest.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.
- Registry `require` phrases are acceptance anchors (the words that state the rule), not incidental wording; authority sections stay small — the rule, not the surrounding chapter — because every edit inside one re-stamps every copy.

## Review Focus

1. The rule changes in its authority and a copy keeps all its old phrases (the `85776b36` / `98aa98e9` shape) — the copy must go red through its stale stamp, not pass on phrases (Task 2, `test_an_authority_edit_reddens_every_copy_until_restamped`).
2. A new bash block is added to a template without a marker, or a new `snippet:` name without a test — must be red, never silently unguarded (Task 1, `test_every_bash_block_in_the_run_templates_is_classified`).
3. A snippet's failure `exit` runs in the driver's persistent shell — the snippet must fail inside a subshell and leave the caller running (Task 1, `test_pi_freshness_publish_snippet_fails_without_killing_the_callers_shell`).
4. A registered phrase is re-wrapped across a line break — must still pass (Task 2, `test_a_token_rewrapped_across_lines_still_holds`); a registered file moved — must report "unchecked, not passed" (Task 2, `test_a_missing_copy_is_unchecked_not_passed`).
5. Codex/Pi trees hold symlinks into the Claude tree, and the registry quotes retired phrases — each forbidden phrase reported once per real file, never from the registry's own directory (Task 2, `test_forbidden_phrases_skip_symlinks_and_the_excluded_dir`).

---

### Task 1: Pi Core Loop publishes before its gate with the worker's acceptance command; every template bash block is classified and executed snippets run

**Files:**
- Modify: `pi/meta-skill/knowledge/orchestrator-template.md` (Pi Dispatch intro ≈ lines 84–89; Core Loop steps 4 and 6–10 ≈ lines 139–176; bash blocks at ≈ lines 49, 60, 162, 393)
- Modify: `claude/meta-skill/knowledge/orchestrator-template.md` (bash blocks at ≈ lines 52, 68)
- Modify: `codex/meta-skill/knowledge/orchestrator-template.md` (bash blocks at ≈ lines 68, 380)
- Create: `claude/meta-skill/tests/unit/test_template_snippets.py`
- Modify: `.githooks/pre-commit` (named fast subset)

**Interfaces:**
- Consumes: `setup(root, host)` and `invoke(root, operation, **request)` from `claude/meta-skill/tests/unit/test_evidence_freshness.py`; `SCRIPTS` (= `claude/meta-skill/scripts`) from `claude/meta-skill/tests/unit/test_bootstrap_scope.py`. Fixture node id: `deliver-export`; before any publish its gate says `all_exist: false`, after contract+evidence publish `true` (verified 2026-09-23).
- Produces: snippet names `preflight-readiness` (all three templates), `repair-ledger-initialize` (Claude, Pi), `freshness-publish` (Pi); Pi placeholders exactly `<node_id>` and `<acceptance_argv_json>`; the Pi worker return field `acceptance_argv`. Task 3 registers the phrases `acceptance_argv` and `always exits 0`.

- [ ] **Step 1: Write the failing tests**

Create `claude/meta-skill/tests/unit/test_template_snippets.py`:

```python
"""The shell a run template hands its driver runs against the helpers it names.

ADR-0010: a template snippet crosses a seam — the driver copies it verbatim, and the helper it
calls changes on its own schedule. Every bash block in a run template is classified: a
`snippet:` block is extracted and run here against a bootstrapped fixture, an `illustrative:`
block says why it is not. Drift on either side goes red here, not in a live run.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from .test_bootstrap_scope import SCRIPTS
from .test_evidence_freshness import invoke, setup

REPO = Path(__file__).resolve().parents[4]
TEMPLATES = {
    'claude': REPO / 'claude/meta-skill/knowledge/orchestrator-template.md',
    'codex': REPO / 'codex/meta-skill/knowledge/orchestrator-template.md',
    'pi': REPO / 'pi/meta-skill/knowledge/orchestrator-template.md',
}
# Every snippet name a template may use; each is executed by a test below.
EXECUTED = {'preflight-readiness', 'repair-ledger-initialize', 'freshness-publish'}
NODE = 'deliver-export'
PASSING = json.dumps([sys.executable, '-c', 'pass'])
FAILING = json.dumps([sys.executable, '-c', 'raise SystemExit(3)'])
MARKER = re.compile(r'<!-- (snippet:([a-z0-9-]+)|illustrative:(.*?)) -->')


def snippet(template, name):
    """The fenced bash block right after `<!-- snippet:<name> -->`, list indentation removed."""
    text = template.read_text(encoding='utf-8')
    match = re.search(r'<!-- snippet:' + re.escape(name) + r' -->[ \t]*\n([ \t]*)```bash\n(.*?)\n[ \t]*```',
                      text, re.S)
    assert match, f'{template.name} has no snippet:{name} marker followed by a bash block'
    indent = match.group(1)
    return '\n'.join(line[len(indent):] if line.startswith(indent) else line
                     for line in match.group(2).splitlines())


def publish_script(acceptance):
    script = snippet(TEMPLATES['pi'], 'freshness-publish')
    script = script.replace('<node_id>', NODE).replace('<acceptance_argv_json>', acceptance)
    assert not re.search(r'<[a-z_]+>', script), f'unfilled placeholder left in:\n{script}'
    return script


def run(root, script):
    return subprocess.run(['bash', '-c', script], cwd=root, text=True, capture_output=True)


def gate(root):
    result = subprocess.run([sys.executable, str(root / '.allforai/bootstrap/scripts/check_artifacts.py'),
                             str(root / '.allforai/bootstrap/workflow.json'), '--node', NODE, '--json'],
                            text=True, capture_output=True)
    return json.loads(result.stdout)['all_exist']


def test_snippet_extraction_names_a_missing_marker(tmp_path):
    template = tmp_path / 'template.md'
    template.write_text('8. On success:\n\n   ```bash\n   echo hi\n   ```\n', encoding='utf-8')
    with pytest.raises(AssertionError, match='snippet:freshness-publish'):
        snippet(template, 'freshness-publish')


@pytest.mark.parametrize('host', sorted(TEMPLATES))
def test_every_bash_block_in_the_run_templates_is_classified(host):
    lines = TEMPLATES[host].read_text(encoding='utf-8').splitlines()
    problems = []
    for number, line in enumerate(lines):
        if line.strip() != '```bash':
            continue
        previous = next((l.strip() for l in reversed(lines[:number]) if l.strip()), '')
        marker = MARKER.fullmatch(previous)
        if not marker:
            problems.append(f'line {number + 1}: bash block with no snippet:/illustrative: marker')
        elif marker.group(2) and marker.group(2) not in EXECUTED:
            problems.append(f'line {number + 1}: snippet:{marker.group(2)} is executed by no test')
        elif marker.group(3) is not None and not marker.group(3).strip():
            problems.append(f'line {number + 1}: illustrative block with no reason')
    assert problems == [], f'{TEMPLATES[host]}:\n' + '\n'.join(problems)


@pytest.mark.parametrize('host', sorted(TEMPLATES))
def test_preflight_readiness_snippet_writes_the_readiness_report(tmp_path, host):
    setup(tmp_path, 'claude')
    shutil.copy2(SCRIPTS / 'orchestrator' / 'record_run_event.py',
                 tmp_path / '.allforai/bootstrap/scripts/record_run_event.py')
    result = run(tmp_path, snippet(TEMPLATES[host], 'preflight-readiness'))
    report = tmp_path / '.allforai/bootstrap/unattended-run-readiness.json'
    assert report.is_file(), result.stdout + result.stderr
    assert json.loads(report.read_text())['status'] in ('ready', 'not_ready')


@pytest.mark.parametrize('host', ['claude', 'pi'])
def test_repair_ledger_initialize_snippet_records_a_new_run(tmp_path, host):
    setup(tmp_path, 'claude')
    shutil.copy2(SCRIPTS / 'orchestrator' / 'repair_authorization.py',
                 tmp_path / '.allforai/bootstrap/scripts/repair_authorization.py')
    (tmp_path / '.allforai/bootstrap/run-id').write_text('run-1\n', encoding='utf-8')
    script = snippet(TEMPLATES[host], 'repair-ledger-initialize')
    first = run(tmp_path, script)
    assert first.returncode == 0, first.stdout + first.stderr
    answer = json.loads(first.stdout)
    assert answer['status'] == 'ok' and answer['origin'] == 'new_run', answer
    again = json.loads(run(tmp_path, script).stdout)
    assert again['replayed'] is True, again


def test_pi_publish_then_gate_completes_an_accepted_node(tmp_path):
    # The gate reads published freshness: before publication it refuses completion, so the
    # Core Loop must publish first and gate second.
    setup(tmp_path, 'claude')
    assert gate(tmp_path) is False
    result = run(tmp_path, publish_script(PASSING))
    assert result.returncode == 0, result.stdout + result.stderr
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes'][NODE]['status'] == 'valid', checked
    assert gate(tmp_path) is True


def test_pi_core_loop_publishes_before_the_gate():
    loop = TEMPLATES['pi'].read_text(encoding='utf-8').split('## Core Loop', 1)[1].split('\n## ', 1)[0]
    publish = loop.index('<!-- snippet:freshness-publish -->')
    gate_step = loop.index('--node <node_id> --json')
    assert publish < gate_step, 'Pi Core Loop runs the artifact gate before publishing the freshness it reads'


def test_pi_freshness_publish_snippet_refuses_when_acceptance_fails(tmp_path):
    # check_artifacts.py --json exits 0 whatever it finds; the snippet's verification must be a
    # command that can fail, or a rejected delivery publishes as verified.
    setup(tmp_path, 'claude')
    result = run(tmp_path, publish_script(FAILING))
    assert result.returncode != 0, result.stdout
    assert 'failed_verification' in result.stdout, result.stdout
    _, checked = invoke(tmp_path, 'check')
    assert checked['nodes'].get(NODE, {}).get('status') != 'valid', checked
    assert gate(tmp_path) is False


def test_pi_freshness_publish_snippet_fails_without_killing_the_callers_shell(tmp_path):
    setup(tmp_path, 'claude')
    result = run(tmp_path, publish_script(FAILING) + '\necho "caller survived: $?"')
    assert 'caller survived: 1' in result.stdout, result.stdout + result.stderr
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd claude/meta-skill && python3 -m pytest -q tests/unit/test_template_snippets.py`
Expected: `test_snippet_extraction_names_a_missing_marker` passes; the classification test fails for all three templates ("bash block with no snippet:/illustrative: marker"); every snippet test fails with "has no snippet:… marker"; `test_pi_core_loop_publishes_before_the_gate` fails with `ValueError: substring not found`.

- [ ] **Step 3: Classify the existing bash blocks**

Insert one marker line directly above each fence (same indentation as the fence), leaving the blocks unchanged except the Pi publish block (Step 4):

| Template | Block (first line) | Marker |
|---|---|---|
| claude ≈52, codex ≈68, pi ≈49 | `python3 .allforai/bootstrap/scripts/record_run_event.py . --event run_started …` | `<!-- snippet:preflight-readiness -->` |
| claude ≈68, pi ≈60 | `printf '{"operation":"initialize",…` | `<!-- snippet:repair-ledger-initialize -->` |
| codex ≈380, pi ≈393 | `echo '{"operation":"observe","node_id":"<qa-node>",…` | `<!-- illustrative: request shape only; the argv is the QA node's own acceptance command (input-freshness.md) -->` |

- [ ] **Step 4: Rewrite the Pi Core Loop (publish before gate) and fix step 4**

In `pi/meta-skill/knowledge/orchestrator-template.md`:

(a) Core Loop step 4, replace the bullet `   - parallelize only when exit artifacts do not overlap` with:

```markdown
   - parallelize only when write sets are disjoint (the predicate in Pi Dispatch)
```

(b) Replace steps 7 through the end of the list (from `7. After the node reports success, independently run:` through `10. Repeat`) with:

````markdown
7. When the node reports success, publish its freshness — contract, then evidence —
   with the `acceptance_argv` the worker returned (Pi Dispatch). The helper runs that
   command itself, so publication is the orchestrator re-verifying the worker, not
   taking its word. A worker that returned no `acceptance_argv` has not finished:
   record a failed transition. `check_artifacts.py --json` cannot serve as the argv:
   it always exits 0 and carries its verdict in the JSON.

   <!-- snippet:freshness-publish -->
   ```bash
   (
     set -o pipefail
     acceptance='<acceptance_argv_json>'
     for kind in contract evidence; do
       token=$(printf '{"operation":"observe","node_id":"%s","kind":"%s"}' '<node_id>' "$kind" \
         | python3 .allforai/bootstrap/scripts/evidence_freshness.py . \
         | python3 -c 'import json,sys; print(json.load(sys.stdin)["observation"])') || exit 1
       printf '{"operation":"publish","observation":"%s","verification_command":%s}' "$token" "$acceptance" \
         | python3 .allforai/bootstrap/scripts/evidence_freshness.py . \
         | python3 -c 'import json,sys; r=json.load(sys.stdin); print(json.dumps(r)); sys.exit(r.get("status") != "valid")' \
         || exit 1
     done
   )
   ```

   A non-zero exit — any `status` other than `valid` — is a failed transition, not
   something to record around.
8. Then independently run the artifact gate, which reads the freshness just published:
   `python3 .allforai/bootstrap/scripts/check_artifacts.py .allforai/bootstrap/workflow.json --node <node_id> --json`
   Non-empty production gaps, blocking status values, or `all_exist != true` cannot be recorded as complete.
   Missing checker, nonzero exit, empty/invalid JSON, mismatched node identity or non-boolean success are failures, never implicit passes. Final bootstrap validation must also succeed before reporting the workflow complete.
9. On success: append a completed transition entry to `workflow.json`
10. On failure: append a failed transition entry, then read `.allforai/bootstrap/protocols/diagnosis.md`
11. Repeat
````

(c) Pi Dispatch intro: replace the sentence `Node workers return observations and the files they were asked to produce; they do not record completion or edit the ledger.` with:

```markdown
Node workers return observations, the files they were asked to produce, and
`acceptance_argv` — the JSON argv of the command that accepts their work and exits
non-zero when it is not accepted (the node's acceptance check, or its exit artifacts'
`validation_commands`; a no-op is not acceptance). They do not record completion,
publish freshness or edit the ledger.
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd claude/meta-skill && python3 -m pytest -q tests/unit/test_template_snippets.py tests/unit/test_evidence_freshness.py`
Expected: all pass. Then from the repo root: `python3 -m pytest -q pi/meta-skill/test_contract.py codex/meta-skill/test_flow.py` — pass (they assert template phrases this task keeps).

- [ ] **Step 6: Add the snippet test to the hook's named fast subset**

In `.githooks/pre-commit`, in the `run_pytest \` block that starts with `claude/meta-skill/tests/unit/test_validate_unattended_readiness.py \`, add after `claude/meta-skill/tests/unit/test_check_artifacts.py \`:

```bash
  claude/meta-skill/tests/unit/test_template_snippets.py \
```

and append to the comment above that block:

```bash
# test_template_snippets runs the shell the run templates hand their drivers against the real helpers.
```

- [ ] **Step 7: Commit**

```bash
git commit -F - -- pi/meta-skill/knowledge/orchestrator-template.md \
  claude/meta-skill/knowledge/orchestrator-template.md \
  codex/meta-skill/knowledge/orchestrator-template.md \
  claude/meta-skill/tests/unit/test_template_snippets.py .githooks/pre-commit <<'EOF'
run templates: Pi publishes before its gate; every bash block is executed or declared

053ccbd5 put the Pi freshness publish after the artifact gate that reads it,
so a scoped node could never complete as written, and verified with
check_artifacts.py --json, which always exits 0. The worker now returns
acceptance_argv, the orchestrator publishes with it (the helper reruns it:
the receiver verifies) and then gates; the snippet fails closed in a
subshell. Core Loop step 4 now points at cffc1115's write-set predicate.
Every bash block in the three run templates is marked snippet: (run here
against the real helpers) or illustrative: with a reason.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

---

### Task 2: Clause registry checker with authority-hash stamps, wired into the hook

**Files:**
- Create: `shared/seam-contracts/check_clauses.py`
- Create: `shared/seam-contracts/clauses.json`
- Create: `shared/seam-contracts/test_check_clauses.py`
- Modify: `shared/suites/suites.txt` (add a line)
- Modify: `.githooks/pre-commit` (add a `run_pytest` line)

**Interfaces:**
- Produces: `check_clauses.violations(root: Path, registry: dict, exclude: tuple = ()) -> list[str]`; `check_clauses.stamp(root: Path, clause: dict) -> str | None` (`'clause:<id>@<8 hex>'`, `None` when the authority is unmarked or missing); `check_clauses.load_registry(path=REGISTRY) -> dict`; `check_clauses.main(argv=None) -> int` (`--hashes` prints each clause's current stamp); constants `ROOT`, `REGISTRY`. Registry shape:

```json
{
  "scan_roots": ["claude", "codex", "pi", "shared"],
  "clauses": [
    {
      "id": "kebab-id",
      "rule": "one sentence: what every copy must keep saying",
      "authority": {"path": "repo/relative.md", "require": ["phrase inside the marked section"]},
      "copies": [
        {"path": "repo/relative.md", "require": ["phrase"]},
        {"path": "repo/relative.md", "exempt": "why this copy does not say it"}
      ],
      "forbid": ["retired phrase"]
    }
  ]
}
```

The authority file marks the rule with `clause-begin:<id>` … `clause-end:<id>` (in any comment syntax: `<!-- clause-begin:x -->`, `# clause-begin:x`). Every copy, exempt ones included, contains `clause:<id>@<hash>`.

- [ ] **Step 1: Write the failing tests**

Create `shared/seam-contracts/test_check_clauses.py`:

```python
"""The clause registry reddens on drift, and only on drift (ADR-0010 criterion 4)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_clauses  # noqa: E402

AUTHORITY = 'intro\n<!-- clause-begin:demo -->\nthe rule says X\n<!-- clause-end:demo -->\noutro\n'


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


def registry(copies=(), forbid=(), require=('the rule says X',)):
    return {'scan_roots': ['src'], 'clauses': [{
        'id': 'demo', 'rule': 'every copy says X',
        'authority': {'path': 'src/authority.md', 'require': list(require)},
        'copies': list(copies), 'forbid': list(forbid)}]}


def stamped(root, reg, body):
    return f"{check_clauses.stamp(root, reg['clauses'][0])}\n{body}"


def test_matching_copies_hold(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    reg = registry(copies=[{'path': 'src/copy.md', 'require': ['the rule says X']}])
    write(tmp_path, 'src/copy.md', stamped(tmp_path, reg, 'the rule says X'))
    assert check_clauses.violations(tmp_path, reg) == []


def test_a_token_rewrapped_across_lines_still_holds(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY.replace('the rule says X', 'the rule\n   says X'))
    assert check_clauses.violations(tmp_path, registry()) == []


def test_an_authority_edit_reddens_every_copy_until_restamped(tmp_path):
    # Replay of 85776b36 / 98aa98e9: the rule moves at its authority, the copies keep every
    # phrase they had. Phrases alone would pass; the stale stamp is what goes red.
    write(tmp_path, 'src/authority.md', AUTHORITY)
    reg = registry(copies=[{'path': 'src/a.md', 'require': ['the rule says X']},
                           {'path': 'src/b.md', 'exempt': 'host does it natively'}])
    old = check_clauses.stamp(tmp_path, reg['clauses'][0])
    write(tmp_path, 'src/a.md', f'{old}\nthe rule says X')
    write(tmp_path, 'src/b.md', old)
    write(tmp_path, 'src/authority.md', AUTHORITY.replace('says X', 'says X, and also Y'))
    new = check_clauses.stamp(tmp_path, reg['clauses'][0])
    assert new != old
    found = check_clauses.violations(tmp_path, reg)
    assert found == [
        f'demo: src/a.md was stamped {old.split("@")[1]} but the authority is now {new.split("@")[1]}: '
        'reread src/authority.md clause-begin:demo, bring this copy in line, then restamp it',
        f'demo: src/b.md was stamped {old.split("@")[1]} but the authority is now {new.split("@")[1]}: '
        'reread src/authority.md clause-begin:demo, bring this copy in line, then restamp it']
    write(tmp_path, 'src/a.md', f'{new}\nthe rule says X, and also Y')
    write(tmp_path, 'src/b.md', new)
    assert check_clauses.violations(tmp_path, reg) == []


def test_a_copy_without_a_stamp_is_named(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    write(tmp_path, 'src/copy.md', 'the rule says X')
    reg = registry(copies=[{'path': 'src/copy.md', 'require': ['the rule says X']}])
    assert check_clauses.violations(tmp_path, reg) == [
        f"demo: src/copy.md has no {check_clauses.stamp(tmp_path, reg['clauses'][0])} stamp"]


def test_an_unmarked_authority_is_named(tmp_path):
    write(tmp_path, 'src/authority.md', 'the rule says X')
    assert check_clauses.violations(tmp_path, registry()) == [
        'demo: src/authority.md has no clause-begin:demo … clause-end:demo section']


def test_an_authority_phrase_must_sit_inside_its_section(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY + 'stray phrase\n')
    assert check_clauses.violations(tmp_path, registry(require=['stray phrase'])) == [
        "demo: src/authority.md no longer says 'stray phrase'"]


def test_a_copy_that_stopped_saying_it_is_named(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    reg = registry(copies=[{'path': 'src/copy.md', 'require': ['the rule says X']}])
    write(tmp_path, 'src/copy.md', stamped(tmp_path, reg, 'the rule says Y'))
    assert check_clauses.violations(tmp_path, reg) == [
        "demo: src/copy.md no longer says 'the rule says X'"]


def test_a_missing_copy_is_unchecked_not_passed(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    reg = registry(copies=[{'path': 'src/moved.md', 'require': ['the rule says X']}])
    assert check_clauses.violations(tmp_path, reg) == [
        'demo: src/moved.md does not exist — unchecked, not passed']


def test_an_exemption_needs_a_reason(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    reg = registry(copies=[{'path': 'src/a.md', 'exempt': 'host does it natively'},
                           {'path': 'src/b.md', 'exempt': '  '}])
    write(tmp_path, 'src/a.md', stamped(tmp_path, reg, ''))
    write(tmp_path, 'src/b.md', stamped(tmp_path, reg, ''))
    assert check_clauses.violations(tmp_path, reg) == [
        'demo: src/b.md is exempt with no reason']


def test_a_copy_with_neither_require_nor_exempt_is_malformed(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    reg = registry(copies=[{'path': 'src/copy.md'}])
    write(tmp_path, 'src/copy.md', stamped(tmp_path, reg, 'anything'))
    assert check_clauses.violations(tmp_path, reg) == [
        'demo: src/copy.md has neither a non-empty require list nor an exempt reason']


def test_a_retired_phrase_is_reported_where_it_survives(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    write(tmp_path, 'src/deep/old.md', 'as before, the old\nwording stays')
    assert check_clauses.violations(tmp_path, registry(forbid=['the old wording'])) == [
        "demo: src/deep/old.md still says retired 'the old wording'"]


def test_forbidden_phrases_skip_symlinks_and_the_excluded_dir(tmp_path):
    write(tmp_path, 'src/authority.md', AUTHORITY)
    real = write(tmp_path, 'src/real/old.md', 'the old wording')
    os.symlink(real, tmp_path / 'src/link.md')
    os.symlink(tmp_path / 'src/real', tmp_path / 'src/linked-dir')
    write(tmp_path, 'src/registry/clauses.json', '"the old wording"')
    write(tmp_path, 'src/node_modules/pkg/readme.md', 'the old wording')
    found = check_clauses.violations(tmp_path, registry(forbid=['the old wording']),
                                     exclude=(tmp_path / 'src/registry',))
    assert found == ["demo: src/real/old.md still says retired 'the old wording'"]


def test_hashes_prints_each_clause_stamp(capsys):
    assert check_clauses.main(['--hashes']) == 0
    printed = capsys.readouterr().out.split()
    assert printed == [check_clauses.stamp(check_clauses.ROOT, c) or f"{c['id']}: unmarked"
                       for c in check_clauses.load_registry()['clauses']]


def test_the_repository_registry_holds():
    found = check_clauses.violations(check_clauses.ROOT, check_clauses.load_registry(),
                                     exclude=(check_clauses.REGISTRY.parent,))
    assert found == [], '\n'.join(found)
    assert check_clauses.main([]) == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest -q shared/seam-contracts`
Expected: collection error `ModuleNotFoundError: No module named 'check_clauses'`.

- [ ] **Step 3: Write the checker**

Create `shared/seam-contracts/check_clauses.py`:

```python
#!/usr/bin/env python3
"""Every registered copy of a shared rule is revisited when the rule changes.

ADR-0010: where the same content lives in several places, one is named authoritative and a
check goes red when they differ. The authority holds the rule between `clause-begin:<id>` and
`clause-end:<id>`; each copy carries `clause:<id>@<hash>` of that section. Any edit to the
section changes the hash, so every copy is red until someone rereads the rule, brings the copy
in line and restamps it — required phrases alone would let a copy that never heard of the
change keep passing. A copy that cannot be read is unchecked, never passed.

    python3 shared/seam-contracts/check_clauses.py            # check; exit 1 on any violation
    python3 shared/seam-contracts/check_clauses.py --hashes   # print each clause's current stamp
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = Path(__file__).resolve().with_name('clauses.json')
TEXT_SUFFIXES = {'.md', '.py', '.json', '.js', '.mjs', '.sh', '.txt'}
SKIP_DIRS = {'node_modules', '__pycache__', '.git'}


def normalize(text):
    return re.sub(r'\s+', ' ', text).strip()


def load_registry(path=REGISTRY):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def authority_section(root, clause):
    """The marked rule text in the authority file, or None when missing or unmarked."""
    path = Path(root) / clause['authority']['path']
    if not path.is_file():
        return None
    text = path.read_text(encoding='utf-8')
    cid = re.escape(clause['id'])
    match = re.search(rf'clause-begin:{cid}\b.*?\n(.*?)\n[^\n]*clause-end:{cid}\b', text, re.S)
    return match.group(1) if match else None


def stamp(root, clause):
    section = authority_section(root, clause)
    if section is None:
        return None
    digest = hashlib.sha256(normalize(section).encode('utf-8')).hexdigest()[:8]
    return f"clause:{clause['id']}@{digest}"


def scanned_files(root, scan_roots, exclude):
    """Real text files under the scan roots: symlinks, vendored and excluded dirs are skipped."""
    excluded = {Path(p).resolve() for p in exclude}
    for base in scan_roots:
        for dirpath, dirnames, filenames in os.walk(Path(root) / base):
            here = Path(dirpath)
            dirnames[:] = sorted(d for d in dirnames
                                 if d not in SKIP_DIRS and not (here / d).is_symlink()
                                 and (here / d).resolve() not in excluded)
            for name in sorted(filenames):
                path = here / name
                if path.suffix in TEXT_SUFFIXES and not path.is_symlink():
                    yield path


def _check_authority(root, clause, found):
    cid, rel = clause['id'], clause['authority']['path']
    if not (Path(root) / rel).is_file():
        found.append(f'{cid}: {rel} does not exist — unchecked, not passed')
        return None
    section = authority_section(root, clause)
    if section is None:
        found.append(f'{cid}: {rel} has no clause-begin:{cid} … clause-end:{cid} section')
        return None
    text = normalize(section)
    for token in clause['authority'].get('require', []):
        if normalize(token) not in text:
            found.append(f'{cid}: {rel} no longer says {token!r}')
    return stamp(root, clause)


def _check_copy(root, clause, copy, current, found):
    cid, rel = clause['id'], copy['path']
    exempt = 'exempt' in copy
    if exempt and not str(copy['exempt']).strip():
        found.append(f'{cid}: {rel} is exempt with no reason')
        return
    if not exempt and not copy.get('require'):
        found.append(f'{cid}: {rel} has neither a non-empty require list nor an exempt reason')
        return
    path = Path(root) / rel
    if not path.is_file():
        found.append(f'{cid}: {rel} does not exist — unchecked, not passed')
        return
    raw = path.read_text(encoding='utf-8')
    if current is not None and current not in raw:
        stale = re.search(rf'clause:{re.escape(cid)}@([0-9a-f]{{8}})', raw)
        if stale:
            found.append(f"{cid}: {rel} was stamped {stale.group(1)} but the authority is now "
                         f"{current.split('@')[1]}: reread {clause['authority']['path']} "
                         f"clause-begin:{cid}, bring this copy in line, then restamp it")
        else:
            found.append(f'{cid}: {rel} has no {current} stamp')
    if not exempt:
        text = normalize(raw)
        for token in copy['require']:
            if normalize(token) not in text:
                found.append(f'{cid}: {rel} no longer says {token!r}')


def violations(root, registry, exclude=()):
    root = Path(root)
    found = []
    texts = None
    for clause in registry['clauses']:
        current = _check_authority(root, clause, found)
        for copy in clause.get('copies', []):
            _check_copy(root, clause, copy, current, found)
        if clause.get('forbid'):
            if texts is None:
                texts = {path: normalize(path.read_text(encoding='utf-8', errors='ignore'))
                         for path in scanned_files(root, registry['scan_roots'], exclude)}
            for phrase in clause['forbid']:
                for path, text in texts.items():
                    if normalize(phrase) in text:
                        found.append(f"{clause['id']}: {path.relative_to(root).as_posix()} "
                                     f'still says retired {phrase!r}')
    return found


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    registry = load_registry()
    if argv == ['--hashes']:
        for clause in registry['clauses']:
            print(stamp(ROOT, clause) or f"{clause['id']}: unmarked")
        return 0
    found = violations(ROOT, registry, exclude=(REGISTRY.parent,))
    for line in found:
        print(line)
    if found:
        print(f'{len(found)} clause violation(s): fix the copy, or change the rule at its authority '
              f'and revisit every copy {REGISTRY.relative_to(ROOT)} lists', file=sys.stderr)
        return 1
    print(f"ok — {len(registry['clauses'])} clause(s), every copy agrees")
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 4: Create the empty registry**

Create `shared/seam-contracts/clauses.json` (Task 3 fills `clauses`):

```json
{
  "scan_roots": ["claude", "codex", "pi", "shared"],
  "clauses": []
}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m pytest -q shared/seam-contracts`
Expected: 15 passed. `python3 shared/seam-contracts/check_clauses.py` prints `ok — 0 clause(s), every copy agrees`, exit 0.

- [ ] **Step 6: Wire it into the suites list and the hook**

In `shared/suites/suites.txt`, add after the `shared/keep-code-simple` line:

```text
shared/seam-contracts
```

In `.githooks/pre-commit`, after `run_pytest shared/keep-code-simple             # mirror contract of the shared protocol`, add:

```bash
run_pytest shared/seam-contracts               # a rule's copies are revisited when it changes (ADR-0010)
```

- [ ] **Step 7: Commit, then confirm suite coverage**

```bash
git add shared/seam-contracts
git commit -F - -- shared/seam-contracts shared/suites/suites.txt .githooks/pre-commit <<'EOF'
seam-contracts: a rule's copies go red until revisited when the rule changes

ADR-0010 criterion 4 had no implementation for prose: 85776b36 left six
stale copies of the user_steps rule, and ed8d5d5f and 98aa98e9 each missed
the Codex run template — all found by grep. The authority marks the rule
between clause-begin/clause-end; every copy carries a stamp of that
section's hash, so an edit to the rule reddens every copy until it is
reread and restamped. Required phrases catch deletions, retired wording
is forbidden, and a missing copy is unchecked, not passed. The hook runs it.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
python3 -m pytest -q shared/suites
```

Expected: the hook passes during the commit; `shared/suites` passes afterwards (the new test file is tracked and listed).

---

### Task 3: Register the run-template clauses and the `user_steps` rule, reconciling the copies first

**Files:**
- Modify: `shared/seam-contracts/clauses.json`
- Modify: `claude/meta-skill/knowledge/orchestrator-template.md` (authority markers)
- Modify: `claude/meta-skill/knowledge/bootstrap-planning.md` (authority markers)
- Modify (stamps, and reconciled text where Step 2 finds drift): `codex/meta-skill/knowledge/orchestrator-template.md`, `pi/meta-skill/knowledge/orchestrator-template.md`, `claude/meta-skill/knowledge/suppress-rules.md`, `claude/meta-skill/skills/bootstrap/SKILL.md`, `codex/meta-skill/skills/bootstrap.md`, `pi/meta-skill/skills/bootstrap/SKILL.md`, `claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py`
- Modify: `CLAUDE.md` (Tests section, one sentence)

**Interfaces:**
- Consumes: `check_clauses.violations`, `stamp`, `main(['--hashes'])`, the registry shape (Task 2); the Pi phrases `acceptance_argv` and `always exits 0` (Task 1).

- [ ] **Step 1: Mark the authority sections**

In `claude/meta-skill/knowledge/orchestrator-template.md` wrap each section with begin/end lines (blank line before and after each marker so Markdown rendering is unchanged):

| Clause id | `<!-- clause-begin:<id> -->` goes directly above | `<!-- clause-end:<id> -->` goes directly below |
|---|---|---|
| `run-preflight-readiness` | `Before executing any workflow node, run unattended readiness:` | the paragraph ending `before re-running \`/run\`.` |
| `run-repair-ledger-origin` | `Then record the repair-ledger origin, still before the first node — this is the` | the line `blocked until reconstructed.` |
| `run-freshness-publish` | `Every node follows \`.allforai/bootstrap/protocols/input-freshness.md\`: after its` | the line `but does not prove completion. The independent artifact gate consumes this state.` |
| `run-termination-user-steps` | `- All nodes' exit_artifacts are ready → success report. The report ends with` | the line `(CLI, library-sdk: no UI to critique); \`/cross-exam\` is never dropped.` |
| `run-delegations-disclosure` | the line containing `Run \`python3 .allforai/bootstrap/scripts/product_intent.py . --delegations\`.` | the line containing `If the list is empty, print \`No delegated decisions.\`` (end of that sentence's line) |

Inside a numbered list or bullet (termination, delegations), indent the marker to the list item's text column so the item is not split. In `claude/meta-skill/knowledge/bootstrap-planning.md`, wrap the bullet that begins `- The only exemption is a suppress rule (\`suppress-rules.md\`)` (through `reason to drop them.`) with `<!-- clause-begin:user-steps-cross-exam-kept -->` / `<!-- clause-end:user-steps-cross-exam-kept -->`.

- [ ] **Step 2: Reconcile every copy against its authority before stamping**

A stamp asserts "this copy was brought in line with the authority as it now reads", so stamping without reading would recreate the gap this plan closes. For each clause, read the authority section and each copy's corresponding section side by side and bring the copy in line, or register an `exempt` with the host-specific reason. One drift is already known and must be resolved here: the Claude repair-ledger section (`98aa98e9`) offers `adopt_history` with `{"reconstruct_from": "transition_log", "complete": true}` when declared repair nodes did run; the Codex operator-recovery paragraph (added in `6818bec5`, in the "Zero is a claim about history" bullet) offers only the absence form. Add the reconstruct form there, matching the Claude wording:

```markdown
  the transition log and `repair_routes`. If declared repair nodes did run, the same
  `adopt_history` takes `{"reconstruct_from": "transition_log", "complete": true}` and
  rebuilds one settled attempt per repair transition, bounded by the declared loops. Any
  other history stays blocked until reconstructed.
```

(replacing the existing `the transition log and \`repair_routes\`. Any other history stays blocked until\n  reconstructed.` lines). Record every other difference you find and how you resolved it in the commit message.

- [ ] **Step 3: Fill the registry**

Replace `shared/seam-contracts/clauses.json` with:

```json
{
  "scan_roots": ["claude", "codex", "pi", "shared"],
  "clauses": [
    {
      "id": "run-preflight-readiness",
      "rule": "Every /run checks unattended readiness before the first node and records preflight_blocked when it stops.",
      "authority": {"path": "claude/meta-skill/knowledge/orchestrator-template.md",
                    "require": ["validate_unattended_readiness.py . --write-report"]},
      "copies": [
        {"path": "codex/meta-skill/knowledge/orchestrator-template.md",
         "require": ["validate_unattended_readiness.py . --write-report", "preflight_blocked"]},
        {"path": "pi/meta-skill/knowledge/orchestrator-template.md",
         "require": ["validate_unattended_readiness.py . --write-report", "preflight_blocked"]}
      ]
    },
    {
      "id": "run-repair-ledger-origin",
      "rule": "The repair ledger is initialized before the first node; a run that executed first recovers only through verified adopt_history — the zero-spend absence form, or reconstruction from the transition log.",
      "authority": {"path": "claude/meta-skill/knowledge/orchestrator-template.md",
                    "require": ["\"operation\":\"initialize\"",
                                "\"absence_of\": \"repair_history\", \"complete\": true",
                                "\"reconstruct_from\": \"transition_log\", \"complete\": true"]},
      "copies": [
        {"path": "pi/meta-skill/knowledge/orchestrator-template.md",
         "require": ["\"operation\":\"initialize\"",
                     "\"absence_of\": \"repair_history\", \"complete\": true",
                     "\"reconstruct_from\": \"transition_log\", \"complete\": true"]},
        {"path": "codex/meta-skill/knowledge/orchestrator-template.md",
         "require": ["The native driver calls `initialize` itself",
                     "\"absence_of\": \"repair_history\", \"complete\": true",
                     "\"reconstruct_from\": \"transition_log\", \"complete\": true"]}
      ]
    },
    {
      "id": "run-freshness-publish",
      "rule": "Freshness is published with the node's own acceptance command — one that can fail — before the artifact gate reads it.",
      "authority": {"path": "claude/meta-skill/knowledge/orchestrator-template.md",
                    "require": ["input-freshness.md", "publish evidence with its actual acceptance command"]},
      "copies": [
        {"path": "codex/meta-skill/knowledge/orchestrator-template.md",
         "require": ["\"operation\":\"publish\"", "verification_command"]},
        {"path": "pi/meta-skill/knowledge/orchestrator-template.md",
         "require": ["acceptance_argv", "always exits 0", "which reads the freshness just published"]}
      ],
      "forbid": ["parallelize only when exit artifacts do not overlap"]
    },
    {
      "id": "run-termination-user-steps",
      "rule": "Completion ends with workflow.json.user_steps in order; /cross-exam is never dropped.",
      "authority": {"path": "claude/meta-skill/knowledge/orchestrator-template.md",
                    "require": ["user_steps", "is never dropped"]},
      "copies": [
        {"path": "codex/meta-skill/knowledge/orchestrator-template.md", "require": ["user_steps", "is never dropped"]},
        {"path": "pi/meta-skill/knowledge/orchestrator-template.md", "require": ["user_steps", "is never dropped"]}
      ],
      "forbid": ["An empty list means the project was exempted"]
    },
    {
      "id": "run-delegations-disclosure",
      "rule": "Completion discloses every decision the user delegated to the model.",
      "authority": {"path": "claude/meta-skill/knowledge/orchestrator-template.md",
                    "require": ["product_intent.py . --delegations", "No delegated decisions."]},
      "copies": [
        {"path": "codex/meta-skill/knowledge/orchestrator-template.md",
         "require": ["product_intent.py . --delegations", "No delegated decisions."]},
        {"path": "pi/meta-skill/knowledge/orchestrator-template.md",
         "require": ["product_intent.py . --delegations", "No delegated decisions."]}
      ]
    },
    {
      "id": "user-steps-cross-exam-kept",
      "rule": "A CLI or library-sdk project drops only /product-review; no workflow drops /cross-exam.",
      "authority": {"path": "claude/meta-skill/knowledge/bootstrap-planning.md",
                    "require": ["[\"/cross-exam\"]", "is never dropped"]},
      "copies": [
        {"path": "claude/meta-skill/knowledge/suppress-rules.md", "require": ["user_steps: [\"/cross-exam\"]"]},
        {"path": "claude/meta-skill/skills/bootstrap/SKILL.md", "require": ["[\"/cross-exam\"]"]},
        {"path": "codex/meta-skill/skills/bootstrap.md", "require": ["[\"/cross-exam\"]"]},
        {"path": "pi/meta-skill/skills/bootstrap/SKILL.md", "require": ["[\"/cross-exam\"]"]},
        {"path": "claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py",
         "require": ["missing_cross_exam_step"]}
      ],
      "forbid": ["no product to examine", "user_steps` is `[]`", "被 suppress 时为 `[]`", "无后续用户步骤"]
    }
  ]
}
```

(`preflight_blocked` sits just below the Claude readiness section, so the authority requires only the readiness command; `run-freshness-publish` forbids the stale Pi step-4 wording fixed in Task 1.)

- [ ] **Step 4: Stamp every copy**

Run: `python3 shared/seam-contracts/check_clauses.py --hashes`
It prints six lines `clause:<id>@<8 hex>`. Put each clause's stamp into each of its copies next to the corresponding text — in Markdown as `<!-- clause:<id>@<hash> -->` on its own line directly above the copy's section (inside a list, at the item's text indentation); in `validate_unattended_readiness.py` as a comment `# clause:user-steps-cross-exam-kept@<hash>` directly above the `if "user_steps" not in workflow:` line.

- [ ] **Step 5: Run the checker**

Run: `python3 shared/seam-contracts/check_clauses.py`
Expected: `ok — 6 clause(s), every copy agrees`, exit 0. A violation means a copy, a phrase or a stamp is wrong — read the authority section and the copy before changing either; never loosen a phrase until a real copy matches it.

- [ ] **Step 6: Replay the incidents against the real tree (mutation check, nothing committed)**

```bash
python3 - <<'EOF'
import sys
sys.path.insert(0, 'shared/seam-contracts')
import check_clauses
from pathlib import Path
reg = check_clauses.load_registry()
cases = [
    # 98aa98e9 shape: the authority gains a sentence; the Codex copy must go red on its stamp
    ('claude/meta-skill/knowledge/orchestrator-template.md', 'blocked until reconstructed.',
     'blocked until reconstructed. A new sentence.',
     'run-repair-ledger-origin: codex/meta-skill/knowledge/orchestrator-template.md was stamped'),
    # 85776b36 shape: the rule changes at its authority; a copy must go red on its stamp
    ('claude/meta-skill/knowledge/bootstrap-planning.md', 'reason to drop them.', 'reason to drop them. Changed.',
     'user-steps-cross-exam-kept: claude/meta-skill/knowledge/suppress-rules.md was stamped'),
    # a copy loses its phrase
    ('codex/meta-skill/knowledge/orchestrator-template.md', 'The native driver calls `initialize` itself', 'REMOVED',
     "run-repair-ledger-origin: codex/meta-skill/knowledge/orchestrator-template.md no longer says"),
    # retired wording comes back
    ('pi/meta-skill/skills/bootstrap/SKILL.md', '["/cross-exam"]', '["/cross-exam"] no product to examine',
     "user-steps-cross-exam-kept: pi/meta-skill/skills/bootstrap/SKILL.md still says retired"),
]
for rel, old, new, expected in cases:
    path = Path(rel)
    original = path.read_text(encoding='utf-8')
    assert old in original, (rel, old)
    try:
        path.write_text(original.replace(old, new, 1), encoding='utf-8')
        found = check_clauses.violations(check_clauses.ROOT, reg, exclude=(check_clauses.REGISTRY.parent,))
        assert any(line.startswith(expected) for line in found), found
        print('reddens:', expected.split(':')[0], '<-', rel)
    finally:
        path.write_text(original, encoding='utf-8')
EOF
python3 shared/seam-contracts/check_clauses.py
```

Expected: four `reddens:` lines, then `ok — 6 clause(s), every copy agrees` (every file restored).

- [ ] **Step 7: Run the affected suites**

Run: `python3 -m pytest -q shared/seam-contracts shared/suites pi/meta-skill/test_contract.py codex/meta-skill/test_flow.py && (cd claude/meta-skill && python3 -m pytest -q tests/unit/test_template_snippets.py tests/unit/test_validate_unattended_readiness.py)`
Expected: all pass (the markers are HTML comments / Python comments and change no asserted phrase).

- [ ] **Step 8: Document the registry in CLAUDE.md**

In `CLAUDE.md`, section `## Tests`, append to the end of the paragraph:

```markdown
A rule stated in several files (the three run templates, the `user_steps` rule) is registered in `shared/seam-contracts/clauses.json`: the authority marks it with `clause-begin:<id>` / `clause-end:<id>`, every copy carries a `clause:<id>@<hash>` stamp, and the hook fails until each copy is reread and restamped after the rule changes (`check_clauses.py --hashes` prints the current stamps). Every bash block in a run template is marked `snippet:` (executed by `test_template_snippets.py`) or `illustrative:` with a reason.
```

- [ ] **Step 9: Commit**

```bash
git commit -F - -- shared/seam-contracts/clauses.json CLAUDE.md \
  claude/meta-skill/knowledge/orchestrator-template.md claude/meta-skill/knowledge/bootstrap-planning.md \
  codex/meta-skill/knowledge/orchestrator-template.md pi/meta-skill/knowledge/orchestrator-template.md \
  claude/meta-skill/knowledge/suppress-rules.md claude/meta-skill/skills/bootstrap/SKILL.md \
  codex/meta-skill/skills/bootstrap.md pi/meta-skill/skills/bootstrap/SKILL.md \
  claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py <<'EOF'
seam-contracts: register the run-template clauses and the user_steps rule

Six clauses — preflight readiness, repair-ledger origin, freshness publish,
termination user_steps and delegation disclosure across the Claude, Codex
and Pi run templates, and "no workflow drops /cross-exam" across its six
copies — with authorities marked and every copy stamped after being read
against them. Reconciled while stamping: the Codex template now offers
adopt_history's reconstruct_from form that 98aa98e9 added to the others.
Replaying 85776b36, 98aa98e9, a deleted phrase and returning retired
wording each reddened the check.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```

(Add to the message any further drift Step 2 resolved.)

---

## After the last task

Run `shared/suites/run_suites.sh > <scratchpad>/suites.log 2>&1; echo "exit=$?"` (about 13 minutes; the script continues past a failing suite, so read the exit code, not the tail).

## Self-review record (闭环思维, 2026-09-23)

Each guard was replayed against the incident that motivated it; a guard that would not have gone red on replay was redesigned.

| Finding | Loop that was open | Change |
|---|---|---|
| Required phrases only | Replaying `85776b36`: the author edits the authority, updates its phrase in the registry, copies keep their old phrases → green, stale. Required phrases catch deletion, not a rule that moved. | Authority section hash + per-copy stamps: any authority edit reddens every copy until revisited (Task 2). |
| Stamping without reading | A stamp can be renewed mechanically, recreating the gap. | Task 3 Step 2 reconciles before stamping; the known Codex `reconstruct_from` drift (`98aa98e9`, found during this review — the third missed Codex update this session) is fixed there. |
| Pi publish placed after its gate | Verified: the fixture gate says `all_exist: false` before publish, `true` after; Pi step 7 (gate) before step 8 (publish) cannot complete a scoped node. The first draft only fixed the argv. | Publish becomes step 7, gate step 8; a test pins the order and the publish→gate completion (Task 1). |
| `<acceptance_argv_json>` had no source | The driver cannot know the node's acceptance command; it would fill a no-op, reopening the `--json` hole. | The Pi worker returns `acceptance_argv`; missing = failed transition; the helper reruns it, so the orchestrator verifies the worker (ADR-0010 criterion 1). |
| Only chosen snippets tested | A new bash block would be silently unguarded. | Every bash block in the three templates must be `snippet:` (executed) or `illustrative:` with a reason; a `snippet:` name with no test is red. |
| Stale Pi Core Loop step 4 | `cffc1115` changed the predicate in Pi Dispatch; step 4 still states the old one — a drifted copy inside one file. | Fixed in Task 1; the old wording is forbidden in the registry (Task 3). |

Still open after this plan — unchecked, not passed:
- A rule added in a brand-new section of one template is guarded only once someone registers it; the registry guards registered rules.
- The template → generated `run.md` / `.pi/skills/run/SKILL.md` seam: `/bootstrap` renders templates through an LLM, and nothing checks that the generated file kept the snippets verbatim.
- The two `illustrative:` QA-binding blocks (Codex, Pi) still carry `[...]` for the argv; their correctness rests on `input-freshness.md`, not on execution.
- The Codex `scripts/` copy is exercised by `codex/meta-skill/test_flow.py`, not by the template snippet test.
