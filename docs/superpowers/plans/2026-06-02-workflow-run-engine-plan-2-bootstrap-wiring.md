# Workflow Run-Engine — Plan 2: Bootstrap Wiring & `/run` Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the Plan 1 engine into the real pipeline — bootstrap emits the CC-superset fields, the engine's `agent()` calls carry real prompts, a bootstrap-time invariant guards decision artifacts, and the generated `/run` orchestrator invokes the Workflow engine and handles its two exits with diagnosis-resume.

**Architecture:** Three seams. (1) **Prompt builders** move from inline strings in `engine-core.js` into tested functions, so the engine's load/expand/run/commit agents get substantive, asserted prompts. (2) **Bootstrap** (`skills/bootstrap.md`) emits `decision_mode`/`decision_inputs`/`closure_verify`/`soft_retry_max`/`profile_slice`/`expanders` and converts former `human_gate` nodes to `decision_inputs`; a new Python invariant check asserts every `decision_inputs` artifact exists before `/run`. (3) **The orchestrator template** (`knowledge/orchestrator-template.md`) is rewritten so the generated `/run` invokes the Workflow engine and routes `complete` / `needs_diagnosis` (→ `diagnosis.md` → repair → resume). Existing orchestrator validators are hardened to ignore unknown superset fields (Codex/OpenCode tolerance).

**Tech Stack:** Node.js v26 (`node:test`) for engine prompt-builders; Python 3 (`unittest`, matching `shared/scripts/orchestrator/test_*.py`) for the invariant + tolerance checks; markdown skill authoring for bootstrap + orchestrator template.

**Depends on:** Plan 1 (engine-core.js + run-engine.workflow.js exist and green).

---

## File Structure

| File | Change | Responsibility |
|------|--------|----------------|
| `claude/meta-skill/knowledge/run-engine/engine-core.js` | Modify | Add prompt-builder fns (`loadDagPrompt`, `expandPrompt`, `runNodePrompt`, `commitPrompt`, `commitFailuresPrompt`); `runEngine` uses them. |
| `claude/meta-skill/knowledge/run-engine/run-engine.workflow.js` | Modify | Re-sync inlined region after engine-core change. |
| `claude/meta-skill/knowledge/run-engine/tests/prompts.test.js` | Create | Assert each prompt builder includes its required references. |
| `shared/scripts/orchestrator/check_decision_inputs.py` | Create | Bootstrap-time invariant: every node `decision_inputs` artifact exists on disk. |
| `shared/scripts/orchestrator/test_check_decision_inputs.py` | Create | Tests for the invariant check. |
| `shared/scripts/orchestrator/test_superset_tolerance.py` | Create | Assert `validate_bootstrap.py` / `check_requires.py` tolerate unknown superset fields. |
| `claude/meta-skill/skills/bootstrap.md` | Modify | Emit superset fields in node generation; convert `human_gate`→`decision_inputs`; emit `expanders` list; run the invariant check before declaring bootstrap done. |
| `claude/meta-skill/knowledge/orchestrator-template.md` | Modify | Generated `/run` invokes the Workflow engine; handle `complete`/`needs_diagnosis`+resume. |
| `claude/meta-skill/commands/run.md` | Create | `/run` slash-command entry that invokes the generated orchestrator. |

---

## Task 1: Prompt builders in `engine-core.js`

**Files:**
- Modify: `claude/meta-skill/knowledge/run-engine/engine-core.js`
- Create: `claude/meta-skill/knowledge/run-engine/tests/prompts.test.js`

- [ ] **Step 1: Write the failing test**

Create `claude/meta-skill/knowledge/run-engine/tests/prompts.test.js`:

```js
const test = require('node:test')
const assert = require('node:assert/strict')
const core = require('../engine-core.js')

test('loadDagPrompt references workflow.json + bootstrap-profile + profile_slice', () => {
  const p = core.loadDagPrompt()
  assert.match(p, /workflow\.json/)
  assert.match(p, /bootstrap-profile\.json/)
  assert.match(p, /profile_slice/)
  assert.match(p, /completed/)
})

test('expandPrompt names the expander and asks for new_nodes', () => {
  const p = core.expandPrompt('expand_game_2d_production.py')
  assert.match(p, /expand_game_2d_production\.py/)
  assert.match(p, /new_nodes/)
})

test('runNodePrompt includes node_spec_path, decision_inputs, no-placeholder rule, closure_verify', () => {
  const node = { node_id: 'audio', node_spec_path: 'node-specs/audio.md',
    decision_inputs: ['.allforai/game-design/decision-audio.json'],
    closure_verify: ['audio'], profile_slice: { stack: 'unity' } }
  const p = core.runNodePrompt(node, ' [retry 1]')
  assert.match(p, /node-specs\/audio\.md/)
  assert.match(p, /decision-audio\.json/)
  assert.match(p, /placeholder/i)
  assert.match(p, /audio/)               // closure_verify value
  assert.match(p, /\[retry 1\]/)         // strictness suffix threaded through
})

test('commitPrompt and commitFailuresPrompt reference the right log targets', () => {
  assert.match(core.commitPrompt({ node_id: 'a', artifacts_written: ['x'] }), /transition_log/)
  assert.match(core.commitFailuresPrompt([{ node_id: 'c' }]), /diagnosis_history/)
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/prompts.test.js`
Expected: FAIL — builders not exported.

- [ ] **Step 3: Write implementation**

Inside the marker block in `engine-core.js`, add the builders (place them above `runNode`):

```js
function loadDagPrompt() {
  return [
    'Read .allforai/bootstrap/workflow.json and .allforai/bootstrap/bootstrap-profile.json.',
    'Return a DAG object: nodes[] (each with node_id, capability, hard_blocked_by, alignment_refs,',
    'exit_artifacts, node_spec_path, decision_mode, decision_inputs, closure_verify, soft_retry_max,',
    'and a profile_slice carrying only the bootstrap-profile fields that node needs — tech stack,',
    'scenario, target paths); completed[] = node_ids whose transition_log status is "completed";',
    'expanders[] = the declared expander scripts. Do not execute any node. Read and summarize only.'
  ].join(' ')
}

function expandPrompt(expander) {
  return [
    `Run the project-local expander ${expander} (it mutates .allforai/bootstrap/workflow.json in place,`,
    'the existing behavior). Then return { new_nodes: [...] } listing the nodes it added',
    '(node_id, capability, hard_blocked_by, exit_artifacts, and any superset fields).',
    'Do not duplicate nodes that already exist.'
  ].join(' ')
}

function runNodePrompt(node, strict) {
  const di = (node.decision_inputs || [])
  const cv = (node.closure_verify || [])
  return [
    `Read and execute the node-spec at ${node.node_spec_path}.`,
    di.length ? `First read these required decision inputs: ${di.join(', ')} — if any is missing, return outcome "hard_fail".` : '',
    `Project context (profile_slice): ${JSON.stringify(node.profile_slice || {})}.`,
    'Write all exit_artifacts and run their validation_commands to self-check.',
    cv.length ? `Additionally run closure verification for: ${cv.join(', ')}.` : '',
    'STRICTLY forbid placeholder / stub / debug-residue / pure-color placeholder outputs.',
    'Return a NODE_RESULT { node_id, outcome (passed|soft_fail|hard_fail), artifacts_written,',
    'blocking_findings: [{type, detail, suspected_root_node?}] }. Attach suspected_root_node when the',
    'root cause is in another node.',
    strict || ''
  ].filter(Boolean).join(' ')
}

function commitPrompt(result) {
  return [
    `Append to .allforai/bootstrap/workflow.json transition_log: node_id ${result.node_id},`,
    `status "completed", artifacts_created ${JSON.stringify(result.artifacts_written || [])}.`,
    'Append only; do not touch other entries.'
  ].join(' ')
}

function commitFailuresPrompt(hardFailures) {
  return [
    'Append these hard failures to .allforai/bootstrap/workflow.json diagnosis_history',
    `(failed_node + blocking_findings): ${JSON.stringify((hardFailures || []).map(h => h.node_id))}.`
  ].join(' ')
}
```

Wire `runEngine` to use them (replace the four `agent(...)` prompt strings):

```js
const dag = await agent(loadDagPrompt(), { schema: DAG_SCHEMA, label: 'load-dag' })
// ...
const r = await agent(expandPrompt(exp), { schema: EXPAND_SCHEMA, label: `expand:${exp}` })
// ...inside the failure branch:
await agent(commitFailuresPrompt(hardFailures), { label: 'commit-failures' })
```

And in `runNode`, replace the agent prompt with `runNodePrompt(node, strict)`; in `commitNode`, replace with `commitPrompt(result)`. Add all five builders to `module.exports`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/` (the Plan 1 integration tests still pass because the fake agent keys on `label`, not prompt text)
Expected: PASS — all suites including the new prompts.test.js.

- [ ] **Step 5: Re-sync the Workflow shell + commit**

Copy the updated marker region from `engine-core.js` into `run-engine.workflow.js` verbatim, then:

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/sync-check.test.js`
Expected: PASS.

```bash
git add claude/meta-skill/knowledge/run-engine/engine-core.js claude/meta-skill/knowledge/run-engine/run-engine.workflow.js claude/meta-skill/knowledge/run-engine/tests/prompts.test.js
git commit -m "feat(run-engine): real prompt builders for load/expand/run/commit agents"
```

---

## Task 2: Bootstrap-time invariant — `decision_inputs` artifacts exist

**Files:**
- Create: `shared/scripts/orchestrator/check_decision_inputs.py`
- Create: `shared/scripts/orchestrator/test_check_decision_inputs.py`

- [ ] **Step 1: Write the failing test**

Create `shared/scripts/orchestrator/test_check_decision_inputs.py`:

```python
import json, os, tempfile, unittest
from check_decision_inputs import check_decision_inputs

class TestCheckDecisionInputs(unittest.TestCase):
    def _wf(self, nodes):
        return {"nodes": nodes}

    def test_all_present_returns_ok(self):
        with tempfile.TemporaryDirectory() as d:
            art = os.path.join(d, "decision-a.json")
            open(art, "w").write("{}")
            wf = self._wf([{"node_id": "a", "decision_inputs": [art]}])
            missing = check_decision_inputs(wf, base_dir=d)
            self.assertEqual(missing, [])

    def test_missing_artifact_reported(self):
        with tempfile.TemporaryDirectory() as d:
            wf = self._wf([{"node_id": "a", "decision_inputs": [os.path.join(d, "nope.json")]}])
            missing = check_decision_inputs(wf, base_dir=d)
            self.assertEqual(len(missing), 1)
            self.assertEqual(missing[0]["node_id"], "a")

    def test_nodes_without_decision_inputs_ignored(self):
        wf = self._wf([{"node_id": "a"}, {"node_id": "b", "decision_inputs": []}])
        self.assertEqual(check_decision_inputs(wf, base_dir="/tmp"), [])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd shared/scripts/orchestrator && python3 -m pytest test_check_decision_inputs.py -q` (or `python3 -m unittest test_check_decision_inputs -v`)
Expected: FAIL — `No module named 'check_decision_inputs'`.

- [ ] **Step 3: Write implementation**

Create `shared/scripts/orchestrator/check_decision_inputs.py`:

```python
"""Bootstrap-time invariant: every node's decision_inputs artifact must exist
before /run is allowed to start. A missing artifact is a planning bug (Phase A
should have produced it)."""
import json
import os
import sys


def check_decision_inputs(workflow, base_dir="."):
    """Return list of {node_id, missing} for nodes whose decision_inputs are absent."""
    missing = []
    for node in workflow.get("nodes", []):
        for path in node.get("decision_inputs", []) or []:
            resolved = path if os.path.isabs(path) else os.path.join(base_dir, path)
            if not os.path.exists(resolved):
                missing.append({"node_id": node.get("node_id"), "missing": path})
    return missing


def main(argv):
    base = argv[1] if len(argv) > 1 else "."
    wf_path = os.path.join(base, ".allforai/bootstrap/workflow.json")
    with open(wf_path) as f:
        workflow = json.load(f)
    missing = check_decision_inputs(workflow, base_dir=base)
    if missing:
        print("BLOCKED: missing decision_inputs artifacts (Phase A incomplete):")
        for m in missing:
            print(f"  - {m['node_id']}: {m['missing']}")
        return 1
    print("OK: all decision_inputs artifacts present")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd shared/scripts/orchestrator && python3 -m unittest test_check_decision_inputs -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add shared/scripts/orchestrator/check_decision_inputs.py shared/scripts/orchestrator/test_check_decision_inputs.py
git commit -m "feat(orchestrator): bootstrap-time decision_inputs existence invariant"
```

---

## Task 3: Superset-field tolerance for existing validators (Codex/OpenCode safety)

**Files:**
- Create: `shared/scripts/orchestrator/test_superset_tolerance.py`
- Modify (only if the test fails): `shared/scripts/orchestrator/validate_bootstrap.py` and/or `check_requires.py`

- [ ] **Step 1: Write the failing test**

Create `shared/scripts/orchestrator/test_superset_tolerance.py`:

```python
import json, tempfile, os, unittest, subprocess, sys

SUPERSET_NODE = {
    "node_id": "n1", "capability": "x", "hard_blocked_by": [], "exit_artifacts": [],
    # CC-only superset fields that Codex/OpenCode validators must IGNORE, not choke on:
    "decision_mode": "brainstorm", "decision_inputs": [".allforai/x/decision-n1.json"],
    "closure_verify": ["audio"], "soft_retry_max": 2, "profile_slice": {"stack": "unity"}
}

class TestSupersetTolerance(unittest.TestCase):
    def _write_wf(self, d):
        wf = {"schema_version": "1.0", "nodes": [SUPERSET_NODE],
              "transition_log": [], "expanders": ["mk_x"]}
        path = os.path.join(d, "workflow.json")
        with open(path, "w") as f:
            json.dump(wf, f)
        return path

    def test_validate_bootstrap_tolerates_superset(self):
        import validate_bootstrap
        with tempfile.TemporaryDirectory() as d:
            wf_path = self._write_wf(d)
            wf = json.load(open(wf_path))
            # Must not raise on unknown fields; node remains structurally valid.
            self.assertEqual(wf["nodes"][0]["node_id"], "n1")
            # If validate_bootstrap exposes a node-shape checker, it must pass:
            if hasattr(validate_bootstrap, "validate_node"):
                ok, _ = validate_bootstrap.validate_node(wf["nodes"][0])
                self.assertTrue(ok)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails or passes**

Run: `cd shared/scripts/orchestrator && python3 -m unittest test_superset_tolerance -v`
Expected: PASS if validators already ignore unknown keys (likely, since Python dict access ignores extra keys); FAIL only if a validator asserts an exact key set.

- [ ] **Step 3: Fix only if needed**

If the test fails because a validator rejects unknown keys, locate the offending assertion (e.g., a `set(node.keys()) == EXPECTED` check) in `validate_bootstrap.py` or `check_requires.py` and relax it to `EXPECTED.issubset(node.keys())`. Show the exact diff in your commit. If the test passed in Step 2, record that no change was needed.

- [ ] **Step 4: Re-run the full orchestrator test suite**

Run: `cd shared/scripts/orchestrator && python3 -m unittest discover -p 'test_*.py' -v`
Expected: PASS — including the existing `test_validate_bootstrap.py`, `test_check_requires.py`, and the new tolerance test.

- [ ] **Step 5: Commit**

```bash
git add shared/scripts/orchestrator/test_superset_tolerance.py
# add validate_bootstrap.py / check_requires.py too ONLY if you modified them
git commit -m "test(orchestrator): superset-field tolerance for Codex/OpenCode validators"
```

---

## Task 4: Bootstrap emits superset fields + runs the invariant

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md`

This task is markdown-skill authoring; the "test" is a fixture round-trip in Step 4.

- [ ] **Step 1: Locate the node-emission + workflow.json schema sections**

Run: `grep -n 'human_gate\|"nodes"\|node_spec_path\|schema_version\|exit_artifacts\|approval' claude/meta-skill/skills/bootstrap.md`
Read the workflow.json schema block (around line 544) and the node-spec generation steps. Note where each node object is written.

- [ ] **Step 2: Add the superset-field emission instructions**

In the node-generation section, insert this directive block (verbatim) where nodes are written:

```markdown
### CC-superset fields (emit on every node — Codex/OpenCode ignore them)

When writing each node into `workflow.json`, add:
- `node_spec_path`: relative path to this node's spec under `node-specs/`.
- `profile_slice`: the subset of `bootstrap-profile.json` this node needs (tech stack, scenario, target paths) — NOT the whole profile.
- `decision_mode`: `"brainstorm"` if this node's direction is a human decision gathered in Phase A; else `"none"`.
- `decision_inputs`: paths to the `.allforai/<domain>/decision-<id>.json` artifacts this node consumes (the former `human_gate` is re-expressed here — see below).
- `closure_verify`: closure types to verify (e.g. `["audio"]`, `["save-load"]`, `["2d-placeholder"]`) when applicable; else omit or `[]`.
- `soft_retry_max`: integer (default 2) — leave unset to use the engine default.

At the top level of `workflow.json`, add:
- `expanders`: the list of project-local expander scripts that apply (e.g. `["expand_game_2d_production.py"]`), promoting today's hardcoded invocation to a declared list.

### human_gate → decision_inputs migration

Do NOT emit `human_gate: true` or `approval_record_path` anymore. For any node that
previously required human approval of a generated artifact, instead:
1. Move the *direction* decision upstream into Phase A (generation-before).
2. Reference the resulting `decision-<id>.json` in this node's `decision_inputs`.
The runtime engine has no gate; a missing `decision_inputs` artifact is a planning bug.
```

- [ ] **Step 3: Add the end-of-bootstrap invariant gate**

At the end of the bootstrap protocol (after node-specs + decisions are written, before declaring success), insert:

```markdown
### Final gate: decision_inputs invariant

Before declaring bootstrap complete, run:
`python3 ${CLAUDE_PLUGIN_ROOT}/../../shared/scripts/orchestrator/check_decision_inputs.py <project_base>`
(or the plugin-local copy under `scripts/`). If it reports BLOCKED, the corresponding
Phase A decision was not gathered — return to Phase A for those node_ids. `/run` must
not be offered until this check returns OK.
```

- [ ] **Step 4: Fixture round-trip validation**

Create a throwaway fixture and confirm the invariant wiring works end to end:

Run:
```bash
mkdir -p /tmp/wf2fix/.allforai/bootstrap /tmp/wf2fix/.allforai/x
printf '{"nodes":[{"node_id":"n1","capability":"x","hard_blocked_by":[],"exit_artifacts":[],"decision_inputs":[".allforai/x/decision-n1.json"]}]}' > /tmp/wf2fix/.allforai/bootstrap/workflow.json
python3 shared/scripts/orchestrator/check_decision_inputs.py /tmp/wf2fix; echo "exit=$?"
printf '{}' > /tmp/wf2fix/.allforai/x/decision-n1.json
python3 shared/scripts/orchestrator/check_decision_inputs.py /tmp/wf2fix; echo "exit=$?"
```
Expected: first run prints BLOCKED + `exit=1`; second prints OK + `exit=0`.

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(bootstrap): emit CC-superset fields, migrate human_gate->decision_inputs, add invariant gate"
```

---

## Task 5: Rewrite the orchestrator template to invoke the Workflow engine

**Files:**
- Modify: `claude/meta-skill/knowledge/orchestrator-template.md`

Markdown authoring; acceptance is the L3 real run from Plan 1's runbook plus the structural checks below.

- [ ] **Step 1: Read the current template loop**

Run: `grep -n 'transition_log\|subagent\|hard_blocked_by\|diagnosis\|expand_\|approval\|parallel' claude/meta-skill/knowledge/orchestrator-template.md`
Read the existing model-driven loop section it generates.

- [ ] **Step 2: Replace the loop section with the engine-invocation protocol**

Replace the "execution loop" portion of the template with this (verbatim):

```markdown
## Phase B execution (CC: Workflow engine)

`/run` is fully autonomous — no questions, no human stops. Drive it as:

1. Invoke the Workflow engine script at
   `${CLAUDE_PLUGIN_ROOT}/knowledge/run-engine/run-engine.workflow.js`.
   It reads `workflow.json`, schedules ready nodes (alignment_refs run in parallel),
   self-heals soft failures, commits each node immediately, and returns one of:
   - `{ status: "complete" }`
   - `{ status: "needs_diagnosis", hardFailures: [...] }`

2. On `complete`: run the learning-protocol extraction, then produce the Phase C report
   (read `.allforai/bootstrap/assumed-decisions.json` + any UNRESOLVED) and stop.

3. On `needs_diagnosis`:
   a. Read `hardFailures` + `workflow.json` `diagnosis_history`.
   b. Run `${CLAUDE_PLUGIN_ROOT}/knowledge/diagnosis.md`: locate the root-cause node
      (use `suspected_root_node` when present). This is autonomous — never ask the user.
   c. Convergence cap: if the same root cause already appears ≥2 times in
      `diagnosis_history`, mark it UNRESOLVED, write best-effort output + TODO, and stop.
   d. Otherwise apply the repair plan: remove the root-cause node_id(s) from the
      `transition_log` completed set, then RESUME the engine
      (same session: resumeFromRunId; cross-session: re-invoke — workflow.json idempotency
      skips already-completed nodes).

4. Repeat until `complete` or an UNRESOLVED stop.

This template is CC-only. Codex/OpenCode keep their existing markdown loop (frozen).
```

- [ ] **Step 3: Structural check of the template**

Run: `grep -n 'run-engine.workflow.js\|needs_diagnosis\|resumeFromRunId\|assumed-decisions' claude/meta-skill/knowledge/orchestrator-template.md`
Expected: all four references present.

- [ ] **Step 4: Confirm no human-stop language remains in Phase B**

Run: `grep -niE 'AskUserQuestion|approval|wait for user|approve' claude/meta-skill/knowledge/orchestrator-template.md`
Expected: zero matches in the Phase B section (any remaining matches must be outside Phase B, e.g. historical notes — remove or relocate if inside Phase B).

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/orchestrator-template.md
git commit -m "feat(orchestrator): generated /run invokes Workflow engine + diagnosis-resume (CC)"
```

---

## Task 6: `/run` slash-command entry point

**Files:**
- Create: `claude/meta-skill/commands/run.md`

- [ ] **Step 1: Write the command file**

Create `claude/meta-skill/commands/run.md`:

```markdown
---
name: run
description: Autonomously execute the bootstrapped workflow via the Workflow engine (Phase B). No human stops.
arguments:
  - name: path
    description: Path to target project (default: current directory)
    required: false
---

Execute the project's bootstrapped workflow autonomously.

> Precondition: `/bootstrap` has completed (workflow.json + all decision_inputs artifacts on disk).
> Follow the generated orchestrator protocol; for CC, invoke the Workflow engine at
> `${CLAUDE_PLUGIN_ROOT}/knowledge/run-engine/run-engine.workflow.js` and handle its
> `complete` / `needs_diagnosis` exits per `${CLAUDE_PLUGIN_ROOT}/knowledge/orchestrator-template.md`.

First verify the invariant:
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_decision_inputs.py <path>` (fallback to the
shared copy). If BLOCKED, tell the user bootstrap/Phase A is incomplete and stop.
```

- [ ] **Step 2: Verify frontmatter parses**

Run: `python3 -c "import sys,re; s=open('claude/meta-skill/commands/run.md').read(); assert s.startswith('---'); print('frontmatter ok')"`
Expected: `frontmatter ok`

- [ ] **Step 3: Ensure the invariant script is reachable from the plugin**

Plugins reference `${CLAUDE_PLUGIN_ROOT}/scripts/`. Copy the invariant check into the plugin's own scripts dir (the repo keeps plugin-local copies of shared scripts):

Run: `mkdir -p claude/meta-skill/scripts && cp shared/scripts/orchestrator/check_decision_inputs.py claude/meta-skill/scripts/check_decision_inputs.py && ls claude/meta-skill/scripts/check_decision_inputs.py`
Expected: the path is listed.

- [ ] **Step 4: Confirm the copy runs**

Run: `python3 claude/meta-skill/scripts/check_decision_inputs.py /tmp/wf2fix; echo "exit=$?"`
Expected: `OK` + `exit=0` (the fixture from Task 4 still has its artifact).

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/commands/run.md claude/meta-skill/scripts/check_decision_inputs.py
git commit -m "feat(meta-skill): /run command entry + plugin-local invariant check"
```

---

## Task 7: Version bump

**Files:**
- Modify: `claude/meta-skill/.claude-plugin/plugin.json`, `claude/meta-skill/.claude-plugin/marketplace.json`, bootstrap version marker

- [ ] **Step 1: Read current versions**

Run: `grep -n '"version"' claude/meta-skill/.claude-plugin/plugin.json claude/meta-skill/.claude-plugin/marketplace.json; grep -niE 'Protocol v[0-9]' claude/meta-skill/skills/bootstrap.md | head -1`

- [ ] **Step 2: Bump all three (patch — wiring on top of Plan 1's minor)**

Increment the patch digit consistently across `plugin.json`, `marketplace.json`, and the bootstrap version marker (e.g. `0.9.0` → `0.9.1`). Same string in all three.

- [ ] **Step 3: Verify match**

Run: `grep -rn '0.9.1' claude/meta-skill/.claude-plugin/ claude/meta-skill/skills/bootstrap.md` (substitute your version)
Expected: three identical matches.

- [ ] **Step 4: Full regression**

Run:
```bash
node --test claude/meta-skill/knowledge/run-engine/tests/
cd shared/scripts/orchestrator && python3 -m unittest discover -p 'test_*.py' && cd -
```
Expected: all green (JS suites + Python orchestrator suites).

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/.claude-plugin/plugin.json claude/meta-skill/.claude-plugin/marketplace.json claude/meta-skill/skills/bootstrap.md
git commit -m "chore(meta-skill): bump version for run-engine Plan 2"
```

---

## Self-Review

**1. Spec coverage (Plan 2 portion):**

| Spec § | Covered by |
|--------|------------|
| §4.2.1 load-DAG real prompt + profile_slice | Task 1 |
| §4.2.2 expander real prompt + script-owns-mutation boundary | Task 1 |
| §4.2.5 runNode real prompt (decision_inputs, no-placeholder, closure_verify) | Task 1 |
| §4.2.6 commit real prompt | Task 1 |
| §4.1 human_gate removal → decision_inputs invariant (bootstrap-time check) | Tasks 2, 4 |
| §9 bootstrap emits decision_mode/decision_inputs/closure_verify/soft_retry_max/expanders | Task 4 |
| §4.1 profile_slice emission | Task 4 |
| §2 Codex/OpenCode ignore superset fields | Task 3 |
| §4.5 main-loop exit handling (complete / needs_diagnosis + diagnosis resume) | Task 5 |
| §4.9 Phase C report reads assumed-decisions.json | Task 5 |
| §3.2 `/run` invokes engine; CC-only, others frozen | Tasks 5, 6 |
| §7 DoD version bump | Task 7 |

**Deferred to Plan 3:** G0 granularity audit, A0 decision-coverage audit, Phase A brainstorming-lite procedure (these PRODUCE the `decision-<id>.json` artifacts that Task 2's invariant checks for; until Plan 3, fixtures supply them).

**2. Placeholder scan:** Markdown-authoring tasks (4, 5, 6) provide the verbatim content to insert + a concrete validation command, not "add appropriate X". Task 3 Step 3 is conditional-by-design (relax a check only if it exists) with an exact transform shown.

**3. Type consistency:** Prompt builder names (`loadDagPrompt`, `expandPrompt`, `runNodePrompt`, `commitPrompt`, `commitFailuresPrompt`) match between Task 1's test, implementation, and `runEngine` wiring. `check_decision_inputs(workflow, base_dir)` signature identical across Task 2 test + impl + Task 4/6 invocations. Field names (`decision_inputs`, `decision_mode`, `closure_verify`, `soft_retry_max`, `profile_slice`, `expanders`) match Plan 1's `DAG_SCHEMA` exactly.
