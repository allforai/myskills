# Inherited Completions Are Re-Measured Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The Claude run engine never dispatches a node on an upstream "completed" it only read from `transition_log`: before the first dispatch of a resumed run, the independent gate re-measures every inherited completion a remaining node depends on, and one that no longer passes runs again — and the engine's own test suite is run by the pre-commit hook.

**Architecture:** `engine-core.js` seeds `done` from `dag.completed` (what an agent read out of `transition_log`). A short loop right after that seeding asks the existing gate step (`gateNodePrompt` + `NODE_GATE_SCHEMA`, the same one used after a node runs) about each inherited dependency and removes the ones that do not pass. The Workflow shell inlines `engine-core.js` between markers and is re-synced. The Codex driver already measures every node with `independent_artifact_gate` instead of trusting the log, so this restores cross-host agreement rather than adding a Claude-only rule.

**Tech Stack:** JavaScript (Node ≥ 21, `node:test`), bash, Python 3 + pytest for the coverage test.

**Spec:** `docs/adr/0010-seams-are-guarded-from-the-receiving-side.md` — criterion 1 ("The receiver verifies … A producer's self-report of success is an input to that check, never a substitute") and criterion 4 ("A check that no hook or pipeline invokes does not count as existing"); `docs/adr/0004-cross-host-behavioral-parity.md` — hosts agree on workflow admission.

## Global Constraints

- Work directly on `main`, one commit per task. No worktree, no `git stash` / `checkout` / `reset` / `restore` / `clean`.
- Commit with an explicit pathspec (`git commit -F - -- <paths>`). Never `--no-verify`.
- End every commit message with exactly `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` — do not substitute another model name.
- No CI. Do not create anything under `.github/`. Do not push.
- Edit engine logic only in `claude/meta-skill/knowledge/run-engine/engine-core.js`. `run-engine.workflow.js` inlines it verbatim between `// <<<ENGINE-CORE-START>>>` and `// <<<ENGINE-CORE-END>>>`; after editing, copy the region across and let `tests/sync-check.test.js` prove there is no drift.
- Do not modify `codex/meta-skill/knowledge/flow-template.py`.
- The new gate label is exactly `` `inherit:${node_id}` ``.
- JS suite command, exactly: `node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'` (143 tests, ~5 s on 2026-09-22).

## Facts established on 2026-09-22

- `engine-core.js` `computeReady` admits a node when every `hard_blocked_by` id is in `done`; `done` starts as `new Set(dag.completed || [])`, and `dag.completed` is "node_ids whose transition_log status is completed" as read by the `load-dag` agent step. Nothing re-measures those nodes. The template's "Session Resume: trust artifact existence over transition_log" is prose the engine does not implement.
- The gate is already the engine's only independent measurement: after a node runs, `agent(gateNodePrompt(node), { schema: NODE_GATE_SCHEMA, label: \`verify:${node.node_id}\` })` runs `check_artifacts.py --node <id> --json`, which re-runs the artifact's `validation_commands` and folds freshness into `all_exist`.
- `codex/meta-skill/knowledge/flow-template.py` builds `complete = {id: independent_artifact_gate(project_root, id) for every node}` — it measures, it does not read the log.
- `tests/fake-agent.js` answers any label starting with `verify:` with `{node_id, status: 'passed', blocking_findings: []}` by default.
- The JS suite is invoked by no hook and is not in `shared/suites/suites.txt` (that list is pytest-only). The only tracked `*.test.js` files are the 10 under `claude/meta-skill/knowledge/run-engine/tests/`.

---

### Task 1: The run-engine suite gets an invoker

**Files:**
- Modify: `.githooks/pre-commit` (new block directly before the line `STAGED_AFTER="$(staged_tree)"`)
- Modify: `shared/suites/test_suite_coverage.py` (one new test at the end)
- Modify: `CLAUDE.md` (`## Tests` section, one sentence)

**Interfaces:**
- Consumes: the hook's existing `HOOK` constant and `git ls-files` helper style in `shared/suites/test_suite_coverage.py`.
- Produces: a hook that runs the JS suite when `node` is installed and says so loudly when it is not; a coverage test that fails when a tracked `*.test.js` sits in a directory the hook never names.

- [ ] **Step 1: Write the failing coverage test**

Append to `shared/suites/test_suite_coverage.py`:

```python
def tracked_js_test_dirs():
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    listing = subprocess.run(["git", "ls-files"], cwd=ROOT, env=env,
                             capture_output=True, text=True, check=True).stdout
    return sorted({str(Path(f).parent) for f in listing.splitlines()
                   if f.endswith((".test.js", ".test.mjs", ".test.ts"))
                   and "node_modules/" not in f and not f.startswith(EXEMPT_PREFIXES)})


def test_every_js_test_directory_is_named_in_the_hook():
    """suites.txt is a pytest list; a node:test suite has only the hook to run it."""
    hook = HOOK.read_text()
    unnamed = [d for d in tracked_js_test_dirs() if d not in hook]
    assert unnamed == [], f"the pre-commit hook runs no test in: {unnamed}"
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `python3 -B -m pytest -q -p no:cacheprovider shared/suites`
Expected: 1 FAILED naming `claude/meta-skill/knowledge/run-engine/tests`. (If `HOOK` is not a module-level name in the file, stop and report — an earlier task was expected to have defined it as `ROOT / ".githooks/pre-commit"`.)

- [ ] **Step 3: Add the hook block**

In `.githooks/pre-commit`, directly before the line `STAGED_AFTER="$(staged_tree)"`, insert:

```bash
# The run engine decides what /run dispatches; its node:test suite (~5 s) had no invoker at all.
# A machine without node cannot run it — that is "not checked", said out loud, never a silent pass.
echo "[pre-commit] run-engine (node:test)"
if command -v node >/dev/null 2>&1; then
  run_node() { env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_PREFIX node --test "$@"; }
  run_node 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js' >/dev/null \
    || { run_node 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'; exit 1; }
else
  echo "[pre-commit] node not found — run-engine tests were NOT run (unchecked, not passed)" >&2
fi

```

- [ ] **Step 4: Document it**

In `CLAUDE.md`, in the `## Tests` section, append this sentence to the end of the paragraph:

` The run engine's `node:test` suite (`claude/meta-skill/knowledge/run-engine/tests/`) is run by the hook when `node` is installed; without `node` the hook prints that it was not run.`

- [ ] **Step 5: Run the coverage test and the hook**

Run: `python3 -B -m pytest -q -p no:cacheprovider shared/suites`
Expected: 0 failed.

Run: `time bash .githooks/pre-commit`
Expected: exit 0, output contains `[pre-commit] run-engine (node:test)` and no `NOT run` line; wall time about 5 s more than before.

- [ ] **Step 6: Prove the block bites**

```bash
F=claude/meta-skill/knowledge/run-engine/tests/zz-probe.test.js
printf "const test = require('node:test')\nconst assert = require('node:assert/strict')\ntest('probe', () => assert.equal(1, 2))\n" > "$F"
bash .githooks/pre-commit; echo "exit=$?"
rm "$F"
git status --short
```
Expected: `exit=1` with the failing `probe` test shown; after `rm`, `git status --short` lists only `.githooks/pre-commit`, `CLAUDE.md` and `shared/suites/test_suite_coverage.py`.

- [ ] **Step 7: Commit**

```bash
git commit -F - -- .githooks/pre-commit shared/suites/test_suite_coverage.py CLAUDE.md <<'EOF'
chore(hooks): run-engine 的 node:test 套件进 pre-commit，没装 node 就明说没跑

决定 /run 派发什么的引擎有 143 条测试，却没有任何钩子或清单跑它（suites.txt 只列 pytest）。
钩子里有 node 就跑（约 5 秒），没有就打印「未检查，不算通过」；覆盖测试新增一条：
被跟踪的 *.test.js 所在目录必须在钩子里出现。

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```

---

### Task 2: A resumed run re-measures the completions it inherits

**Files:**
- Modify: `claude/meta-skill/knowledge/run-engine/engine-core.js` (inside `runEngine`, directly after `const done = new Set(dag.completed || [])`)
- Modify: `claude/meta-skill/knowledge/run-engine/run-engine.workflow.js` (the inlined region between the two ENGINE-CORE markers)
- Modify: `claude/meta-skill/knowledge/run-engine/tests/fake-agent.js` (default answer for `inherit:` labels)
- Test: `claude/meta-skill/knowledge/run-engine/tests/engine-integration.test.js`
- Modify: `claude/meta-skill/knowledge/orchestrator-template.md` (`## Session Resume`)
- Modify: `claude/meta-skill/knowledge/cross-phase-protocols.md` (§F, the sentence that calls this uncovered)

**Interfaces:**
- Consumes: existing `gateNodePrompt(node)`, `NODE_GATE_SCHEMA`, and the `log` callback of `runEngine({ agent, pipeline, log, phase })`.
- Produces: one agent call per inherited dependency, labelled `` `inherit:${node_id}` ``, answered with the `NODE_GATE_SCHEMA` shape `{node_id, status: 'passed'|'repair'|'hard_fail', blocking_findings}`. Only `status === 'passed'` with the matching `node_id` keeps the node in `done`.

- [ ] **Step 1: Write the failing tests**

Append to `claude/meta-skill/knowledge/run-engine/tests/engine-integration.test.js`:

```js
test('runEngine: an inherited completion that no longer passes the gate runs again before its consumer', async () => {
  const dag = { nodes: [
    { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'b', capability: 'x', hard_blocked_by: ['a'], exit_artifacts: [] }
  ], completed: ['a'] }
  const order = []
  const agent = makeFakeAgent({
    'load-dag': dag,
    'inherit:a': { node_id: 'a', status: 'repair', blocking_findings: [{ type: 'missing_artifact' }] },
    a: () => { order.push('a'); return passed('a') },
    b: () => { order.push('b'); return passed('b') },
    'commit:a': {}, 'commit:b': {}
  })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'complete')
  assert.equal(agent.counters['inherit:a'], 1)
  assert.deepEqual(order, ['a', 'b'])      // a ran again, and before b
})

test('runEngine: an inherited completion that still passes is not rerun', async () => {
  const dag = { nodes: [
    { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'b', capability: 'x', hard_blocked_by: ['a'], exit_artifacts: [] }
  ], completed: ['a'] }
  const agent = makeFakeAgent({ 'load-dag': dag, b: passed('b'), 'commit:b': {} })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'complete')
  assert.equal(agent.counters['inherit:a'], 1)
  assert.equal(agent.counters.a, undefined)
})

test('runEngine: a gate answer that is missing or names another node does not keep the completion', async () => {
  for (const answer of [undefined, null, { node_id: 'zzz', status: 'passed', blocking_findings: [] }]) {
    const dag = { nodes: [
      { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
      { node_id: 'b', capability: 'x', hard_blocked_by: ['a'], exit_artifacts: [] }
    ], completed: ['a'] }
    const agent = makeFakeAgent({ 'load-dag': dag, 'inherit:a': () => answer,
      a: passed('a'), b: passed('b'), 'commit:a': {}, 'commit:b': {} })
    const res = await core.runEngine({ agent, pipeline })
    assert.equal(res.status, 'complete')
    assert.equal(agent.counters.a, 1, JSON.stringify(answer))
  }
})

test('runEngine: what was built on a completion that must rerun reruns too, in order', async () => {
  const dag = { nodes: [
    { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'b', capability: 'x', hard_blocked_by: ['a'], exit_artifacts: [] },
    { node_id: 'c', capability: 'x', hard_blocked_by: ['b'], exit_artifacts: [] }
  ], completed: ['a', 'b'] }
  const order = []
  const ran = id => () => { order.push(id); return passed(id) }
  // b fails, which makes b a remaining node — so a, which b depends on, is asked about next
  // (it passes by default) and stays done
  const agent = makeFakeAgent({ 'load-dag': dag,
    'inherit:b': { node_id: 'b', status: 'repair', blocking_findings: [] },
    a: ran('a'), b: ran('b'), c: ran('c'), 'commit:a': {}, 'commit:b': {}, 'commit:c': {} })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'complete')
  assert.deepEqual(order, ['b', 'c'])
  assert.equal(agent.counters['inherit:b'], 1)
  assert.equal(agent.counters['inherit:a'], 1)
})

test('runEngine: a failed inherited dependency takes its completed consumers with it', async () => {
  const dag = { nodes: [
    { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'b', capability: 'x', hard_blocked_by: ['a'], exit_artifacts: [] },
    { node_id: 'c', capability: 'x', hard_blocked_by: ['a', 'b'], exit_artifacts: [] }
  ], completed: ['a', 'b'] }
  const order = []
  const ran = id => () => { order.push(id); return passed(id) }
  const agent = makeFakeAgent({ 'load-dag': dag,
    'inherit:a': { node_id: 'a', status: 'repair', blocking_findings: [] },
    a: ran('a'), b: ran('b'), c: ran('c'), 'commit:a': {}, 'commit:b': {}, 'commit:c': {} })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'complete')
  assert.deepEqual(order, ['a', 'b', 'c'])   // b was done and passed its own gate, but a must rerun
})

test('runEngine: a completed node nothing remaining depends on is not re-measured', async () => {
  const dag = { nodes: [
    { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'c', capability: 'x', hard_blocked_by: [], exit_artifacts: [] }
  ], completed: ['a'] }
  const agent = makeFakeAgent({ 'load-dag': dag, c: passed('c'), 'commit:c': {} })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'complete')
  assert.equal(agent.counters['inherit:a'], undefined)
})
```

- [ ] **Step 2: Run them and confirm they fail for the right reason**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-integration.test.js`
Expected: five of the six new tests FAIL (`agent.counters['inherit:a']` is `undefined`; `order` is `['b']`, `['c']` and `['c']` in the three ordering tests); `a completed node nothing remaining depends on is not re-measured` passes already.

- [ ] **Step 3: Give the fake agent a default for the new label**

In `claude/meta-skill/knowledge/run-engine/tests/fake-agent.js`, replace

```js
    if (spec === undefined && label.startsWith('verify:')) {
      spec = {
        node_id: label.slice('verify:'.length),
        status: 'passed',
        blocking_findings: []
      }
    }
```

with

```js
    for (const prefix of ['verify:', 'inherit:']) {   // both are the independent gate, asked at different moments
      if (spec === undefined && label.startsWith(prefix)) {
        spec = { node_id: label.slice(prefix.length), status: 'passed', blocking_findings: [] }
      }
    }
```

(The third new test answers `inherit:a` with a function returning `undefined`; `typeof spec === 'function'` is handled after this block, so that test still receives `undefined`.)

- [ ] **Step 4: Re-measure inherited completions in the engine**

In `claude/meta-skill/knowledge/run-engine/engine-core.js`, inside `runEngine`, replace the single line

```js
  const done = new Set(dag.completed || [])
```

with

```js
  const done = new Set(dag.completed || [])
  // A completion inherited from an earlier session is a claim read out of transition_log, not a
  // measurement. Before anything is dispatched on it, the gate re-measures each inherited
  // completion that a remaining node depends on; one that no longer passes is not done, so it
  // runs again instead of handing its consumer a missing, stale or unusable artifact. The Codex
  // driver measures every node the same way (ADR-0004), and the receiving side verifies (ADR-0010).
  const nodeById = new Map((dag.nodes || []).map(n => [n.node_id, n]))
  const measured = new Set()
  for (let changed = true; changed;) {
    changed = false
    // every completion a not-yet-done node depends on, asked about once
    const inherited = [...new Set((dag.nodes || [])
      .filter(n => !done.has(n.node_id))
      .flatMap(n => n.hard_blocked_by || []))]
      .filter(id => done.has(id) && nodeById.has(id) && !measured.has(id))
    for (const id of inherited) {
      measured.add(id)
      const gate = await agent(gateNodePrompt(nodeById.get(id)), {
        schema: NODE_GATE_SCHEMA, label: `inherit:${id}`
      })
      if (!gate || gate.node_id !== id || gate.status !== 'passed') {
        done.delete(id)
        changed = true
        log(`inherited completion of ${id} did not pass the gate; it will run again`)
      }
    }
    // What was built on a completion that must rerun is suspect too: a completed node with a
    // dependency that is no longer done is not done either. Each removal makes a node
    // "remaining", so the next pass also asks about what that node depends on.
    for (const n of dag.nodes || []) {
      if (done.has(n.node_id) && (n.hard_blocked_by || []).some(dep => nodeById.has(dep) && !done.has(dep))) {
        done.delete(n.node_id)
        changed = true
        log(`${n.node_id} was built on a completion that must rerun; it will run again`)
      }
    }
  }
```

- [ ] **Step 5: Re-sync the Workflow shell**

Copy everything between `// <<<ENGINE-CORE-START>>>` and `// <<<ENGINE-CORE-END>>>` so that the shell's region is again the verbatim content of `engine-core.js` that the sync check compares (read `tests/sync-check.test.js` first — it states exactly which text is compared and how). Do not hand-edit the shell's copy of the new block separately; regenerate the region from `engine-core.js`.

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/sync-check.test.js`
Expected: all pass, including `workflow shell inlines engine-core verbatim (no drift)`.

- [ ] **Step 6: Run the whole JS suite**

Run: `node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'`
Expected: 149 pass, 0 fail (143 before + 6 new). If an existing test now fails because it counts agent calls or lists `agent.calls` labels exactly and sees an extra `inherit:` call, do not delete the assertion: add the expected `inherit:<id>` call to that test's expectation and name the test in your report. If `tests/declared-loop.test.js` or `tests/real-gate.js` (which answer gates from the real `check_artifacts.py`) need to route `inherit:` labels, route them exactly as they route `verify:` labels.

- [ ] **Step 7: Make the two documents say what the engine now does**

In `claude/meta-skill/knowledge/orchestrator-template.md`, replace

```
On first iteration if transition_log is non-empty:
1. Run check_artifacts.py to see current state
2. Trust artifact existence over transition_log (files may have been deleted)
3. Continue from where things stand
```

with

```
On first iteration if transition_log is non-empty:
1. Run check_artifacts.py to see current state
2. Trust the gate over transition_log: a completion read from the log is a claim. The engine
   re-measures every inherited completion that a remaining node depends on (`inherit:<node_id>`,
   the same independent gate that follows a node's own run) and reruns one that no longer passes —
   a deleted file, a failed validation command and a stale input all count.
3. Continue from where things stand
```

In `claude/meta-skill/knowledge/cross-phase-protocols.md` §F there is no sentence to remove; instead append this sentence to the end of the bullet that begins `- **Usable, not just present.**`:

` The same commands guard the seam a second time when a run resumes: the engine re-measures each inherited completion before dispatching a node that depends on it, so a consumer never starts on an upstream "done" that was only read from a log.`

- [ ] **Step 8: Run the validators that cover those two files, then the hook**

Run: `python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py; echo "exit=$?"`
Expected: `exit=0`.

Run: `python3 -B -m pytest -q -p no:cacheprovider pi/meta-skill/test_contract.py && python3 -B shared/scripts/orchestrator/check_codex_meta_skill_parity.py >/dev/null; echo "exit=$?"`
Expected: 0 failed and `exit=0`. (Pi and Codex keep their own `orchestrator-template.md`; this task does not touch them. The Codex driver already measures every node, and Pi's generated run loop re-reads `check_artifacts.py` state each iteration.)

Run: `bash .githooks/pre-commit`
Expected: exit 0.

- [ ] **Step 9: Commit**

```bash
git commit -F - -- claude/meta-skill/knowledge/run-engine/engine-core.js claude/meta-skill/knowledge/run-engine/run-engine.workflow.js claude/meta-skill/knowledge/run-engine/tests/fake-agent.js claude/meta-skill/knowledge/run-engine/tests/engine-integration.test.js claude/meta-skill/knowledge/orchestrator-template.md claude/meta-skill/knowledge/cross-phase-protocols.md <<'EOF'
fix(run-engine): 续跑时继承来的「已完成」先过独立门再用，过不了就重跑

引擎的 done 集合直接取自 transition_log 里读出的 completed，computeReady 据此放行下游；
模板里「以产物为准而不是日志」只是一句话，引擎没有实现。Codex 驱动对每个节点都用
independent_artifact_gate 实测，两个宿主在准入上不一致（ADR-0004）。
现在派发第一个节点之前，对剩余节点依赖的每个继承完成项跑一次同一个门（inherit:<node_id>），
没过、没回答或回答了别的节点，都从 done 里拿掉重跑（ADR-0010 第一条：接收方自己验证）。

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```
