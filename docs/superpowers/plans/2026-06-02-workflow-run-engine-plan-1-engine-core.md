# Workflow Run-Engine — Plan 1: Engine Core & Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the deterministic, unit-tested core of the Workflow-based `/run` engine — pure scheduling logic plus a thin Workflow shell — verified against hand-authored fixtures with zero dependency on bootstrap.

**Architecture:** All decision logic lives in one canonical CommonJS module `engine-core.js` (pure functions + an injectable `runEngine(deps)` loop). The Workflow script `run-engine.workflow.js` is a thin shell that **inlines** that module verbatim (the Workflow sandbox forbids `require`/file I/O) and calls `runEngine` with the harness globals. A sync-check test guarantees the inlined copy never drifts. Tests inject a scriptable fake `agent()` and faithful `pipeline()` doubles, so the four concurrency assertions and all pure logic run in plain Node — fast and deterministic.

**Tech Stack:** Node.js v26 (built-in `node:test` runner + `node:assert/strict`), CommonJS for the testable module, Claude Code `Workflow` tool primitives (`agent`, `pipeline`, `phase`, `log`) for the shell.

**Scope note:** This is Plan 1 of 3. Plan 2 wires the engine into bootstrap + the `/run` skill; Plan 3 adds the G0/A0/Phase A planning audits. Plan 1 stands alone: it produces a working engine that executes a fixture `workflow.json` end-to-end with L1/L2/L3 tests passing.

---

## File Structure

All new files under `claude/meta-skill/knowledge/run-engine/` (NOT `engines/` — that already holds game-engine knowledge files):

| File | Responsibility |
|------|----------------|
| `engine-core.js` | **Canonical.** Schemas + pure functions (`computeReady`, `routeOutcome`, `mergeExpanded`, `pickExit`, `convergenceCheck`) + `runNode`/`commitNode`/`runEngine`. Logic lives between `// <<<ENGINE-CORE-START>>>` / `// <<<ENGINE-CORE-END>>>` markers; `module.exports` sits outside them. |
| `run-engine.workflow.js` | Thin Workflow shell: `export const meta`, the verbatim inlined core region (same markers), then `await runEngine({ agent, pipeline, log, phase })`. |
| `tests/harness-doubles.js` | Test implementations of `pipeline()` / `parallel()` matching the documented semantics (per-item staging, no barrier). |
| `tests/fake-agent.js` | `makeFakeAgent(responses)` (scriptable, records calls) + `makeDeferred()` (manual promise ordering). |
| `tests/engine-core.test.js` | **L1** — pure-function unit tests. |
| `tests/engine-integration.test.js` | **L2** — `runEngine` with fake agent + doubles; the four pipeline assertions. |
| `tests/sync-check.test.js` | Anti-drift: asserts the inlined region in `run-engine.workflow.js` byte-matches `engine-core.js`. |
| `tests/fixtures/mini-workflow.json` | **L3** fixture (7 nodes). |
| `tests/L3-runbook.md` | **L3** manual procedure (real-agent end-to-end). |

**Canonical interfaces** (every task below must match these exactly):

```js
DAG_SCHEMA, NODE_RESULT_SCHEMA, EXPAND_SCHEMA            // JSON-Schema objects
computeReady(nodes, done: Set<string>) -> node[]
routeOutcome(result) -> 'done' | 'soft' | 'hard'
mergeExpanded(nodes, newNodes) -> node[]
pickExit(remaining: node[], hardFailures: any[]) -> 'complete' | 'needs_diagnosis'
convergenceCheck(diagnosisHistory, rootCause) -> boolean   // true = UNRESOLVED cap hit
runNode(node, agent) -> Promise<result>                    // outcome 'passed' | 'hard_fail'
commitNode(result, agent, done: Set) -> Promise<void>
runEngine({ agent, pipeline, log?, phase? }) -> Promise<{status, hardFailures?}>
```

---

## Task 1: Scaffold `engine-core.js` with schemas + module wiring

**Files:**
- Create: `claude/meta-skill/knowledge/run-engine/engine-core.js`
- Test: `claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`

- [ ] **Step 1: Write the failing test**

Create `claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`:

```js
const test = require('node:test')
const assert = require('node:assert/strict')
const core = require('../engine-core.js')

test('exports schemas and functions', () => {
  assert.equal(core.DAG_SCHEMA.type, 'object')
  assert.equal(core.NODE_RESULT_SCHEMA.type, 'object')
  assert.equal(core.EXPAND_SCHEMA.type, 'object')
  for (const fn of ['computeReady','routeOutcome','mergeExpanded','pickExit','convergenceCheck','serializeCommit','runNode','commitNode','runEngine']) {
    assert.equal(typeof core[fn], 'function', `missing ${fn}`)
  }
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: FAIL — `Cannot find module '../engine-core.js'`.

- [ ] **Step 3: Write minimal implementation**

Create `claude/meta-skill/knowledge/run-engine/engine-core.js`:

```js
// <<<ENGINE-CORE-START>>>
const DAG_SCHEMA = {
  type: 'object',
  required: ['nodes', 'completed'],
  properties: {
    nodes: { type: 'array', items: { type: 'object',
      required: ['node_id', 'capability', 'hard_blocked_by', 'exit_artifacts'],
      properties: {
        node_id: { type: 'string' },
        capability: { type: 'string' },
        hard_blocked_by: { type: 'array', items: { type: 'string' } },
        alignment_refs: { type: 'array', items: { type: 'string' } },
        exit_artifacts: { type: 'array', items: { type: 'object' } },
        node_spec_path: { type: 'string' },
        profile_slice: { type: 'object' },
        decision_mode: { type: 'string', enum: ['brainstorm', 'none'] },
        decision_inputs: { type: 'array', items: { type: 'string' } },
        closure_verify: { type: 'array', items: { type: 'string' } },
        soft_retry_max: { type: 'integer' }
      } } },
    completed: { type: 'array', items: { type: 'string' } },
    expanders: { type: 'array', items: { type: 'string' } },
    applied_expanders: { type: 'array', items: { type: 'string' } } // fix C5: cross-session double-expansion guard
  }
}

const NODE_RESULT_SCHEMA = {
  type: 'object',
  required: ['node_id', 'outcome', 'artifacts_written', 'blocking_findings'],
  properties: {
    node_id: { type: 'string' },
    outcome: { type: 'string', enum: ['passed', 'soft_fail', 'hard_fail'] },
    artifacts_written: { type: 'array', items: { type: 'string' } },
    blocking_findings: { type: 'array', items: { type: 'object' } },
    assumed_decisions: { type: 'array', items: { type: 'object' } }, // fix C1: engine persists these, not the subagent
    summary: { type: 'string' }
  }
}

const EXPAND_SCHEMA = {
  type: 'object',
  required: ['new_nodes'],
  properties: { new_nodes: { type: 'array', items: { type: 'object' } } }
}
// <<<ENGINE-CORE-END>>>

module.exports = {
  DAG_SCHEMA, NODE_RESULT_SCHEMA, EXPAND_SCHEMA,
  computeReady, routeOutcome, mergeExpanded, pickExit, convergenceCheck,
  serializeCommit, runNode, commitNode, runEngine
}
```

Add minimal stubs inside the marker block (just before `// <<<ENGINE-CORE-END>>>`):

```js
function computeReady() { return [] }
function routeOutcome() { return 'soft' }
function mergeExpanded(nodes) { return nodes }
function pickExit() { return 'complete' }
function convergenceCheck() { return false }
function serializeCommit(fn) { return Promise.resolve().then(fn) }
async function runNode() {}
async function commitNode() {}
async function runEngine() { return { status: 'complete' } }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: PASS (1 test).

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/run-engine/engine-core.js claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js
git commit -m "feat(run-engine): scaffold engine-core schemas + module wiring"
```

---

## Task 2: `computeReady`

**Files:**
- Modify: `claude/meta-skill/knowledge/run-engine/engine-core.js` (replace the `computeReady` stub)
- Test: `claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`

- [ ] **Step 1: Write the failing test** (append to `engine-core.test.js`)

```js
test('computeReady: ready when all hard_blocked_by are done', () => {
  const nodes = [
    { node_id: 'a', hard_blocked_by: [] },
    { node_id: 'b', hard_blocked_by: ['a'] }
  ]
  assert.deepEqual(core.computeReady(nodes, new Set()).map(n => n.node_id), ['a'])
  assert.deepEqual(core.computeReady(nodes, new Set(['a'])).map(n => n.node_id), ['b'])
})

test('computeReady: completed nodes are skipped', () => {
  const nodes = [{ node_id: 'a', hard_blocked_by: [] }]
  assert.deepEqual(core.computeReady(nodes, new Set(['a'])), [])
})

test('computeReady: alignment_refs do NOT block', () => {
  const nodes = [
    { node_id: 'a', hard_blocked_by: [] },
    { node_id: 'b', hard_blocked_by: ['a'], alignment_refs: ['c'] },
    { node_id: 'c', hard_blocked_by: ['a'], alignment_refs: ['b'] }
  ]
  // after a done, both b and c ready even though they reference each other
  assert.deepEqual(core.computeReady(nodes, new Set(['a'])).map(n => n.node_id), ['b', 'c'])
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: FAIL — `computeReady` returns `[]`.

- [ ] **Step 3: Write implementation** (replace the stub inside the marker block)

```js
function computeReady(nodes, done) {
  return nodes.filter(n =>
    !done.has(n.node_id) &&
    (n.hard_blocked_by || []).every(dep => done.has(dep)))
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: PASS (all computeReady tests).

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/run-engine/engine-core.js claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js
git commit -m "feat(run-engine): computeReady (alignment_refs non-blocking)"
```

---

## Task 3: `routeOutcome`

**Files:**
- Modify: `claude/meta-skill/knowledge/run-engine/engine-core.js`
- Test: `claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`

- [ ] **Step 1: Write the failing test** (append)

```js
test('routeOutcome: passed -> done', () => {
  assert.equal(core.routeOutcome({ outcome: 'passed', blocking_findings: [] }), 'done')
})
test('routeOutcome: hard_fail -> hard', () => {
  assert.equal(core.routeOutcome({ outcome: 'hard_fail', blocking_findings: [] }), 'hard')
})
test('routeOutcome: soft_fail with placeholder -> soft', () => {
  assert.equal(core.routeOutcome({ outcome: 'soft_fail', blocking_findings: [{ type: 'placeholder' }] }), 'soft')
})
test('routeOutcome: soft_fail with cross_node -> hard', () => {
  assert.equal(core.routeOutcome({ outcome: 'soft_fail', blocking_findings: [{ type: 'cross_node' }] }), 'hard')
})
test('routeOutcome: soft_fail with suspected_root_node -> hard', () => {
  assert.equal(core.routeOutcome({ outcome: 'soft_fail', blocking_findings: [{ type: 'failed_validation', suspected_root_node: 'x' }] }), 'hard')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: FAIL — stub returns `'soft'` for all.

- [ ] **Step 3: Write implementation** (replace stub)

```js
function routeOutcome(result) {
  if (result.outcome === 'passed') return 'done'
  if (result.outcome === 'hard_fail') return 'hard'
  const findings = result.blocking_findings || []
  if (findings.some(f => f.type === 'cross_node' || f.suspected_root_node)) return 'hard'
  return 'soft'
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/run-engine/engine-core.js claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js
git commit -m "feat(run-engine): routeOutcome soft/hard routing"
```

---

## Task 4: `mergeExpanded`

**Files:**
- Modify: `claude/meta-skill/knowledge/run-engine/engine-core.js`
- Test: `claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`

- [ ] **Step 1: Write the failing test** (append)

```js
test('mergeExpanded: appends new nodes', () => {
  const out = core.mergeExpanded([{ node_id: 'a' }], [{ node_id: 'b' }])
  assert.deepEqual(out.map(n => n.node_id), ['a', 'b'])
})
test('mergeExpanded: idempotent on existing node_id', () => {
  const out = core.mergeExpanded([{ node_id: 'a' }], [{ node_id: 'a' }, { node_id: 'b' }])
  assert.deepEqual(out.map(n => n.node_id), ['a', 'b'])
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: FAIL — stub returns `nodes` unchanged.

- [ ] **Step 3: Write implementation** (replace stub)

```js
function mergeExpanded(nodes, newNodes) {
  const seen = new Set(nodes.map(n => n.node_id))
  return [...nodes, ...(newNodes || []).filter(n => !seen.has(n.node_id))]
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/run-engine/engine-core.js claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js
git commit -m "feat(run-engine): mergeExpanded (idempotent)"
```

---

## Task 5: `pickExit`

**Files:**
- Modify: `claude/meta-skill/knowledge/run-engine/engine-core.js`
- Test: `claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`

- [ ] **Step 1: Write the failing test** (append)

```js
test('pickExit: all done -> complete', () => {
  assert.equal(core.pickExit([], []), 'complete')
})
test('pickExit: hard failures -> needs_diagnosis', () => {
  assert.equal(core.pickExit([], [{ node_id: 'c' }]), 'needs_diagnosis')
})
test('pickExit: remaining nodes but no progress -> needs_diagnosis (stuck graph)', () => {
  assert.equal(core.pickExit([{ node_id: 'x' }], []), 'needs_diagnosis')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: FAIL — stub returns `'complete'`.

- [ ] **Step 3: Write implementation** (replace stub)

```js
function pickExit(remaining, hardFailures) {
  if ((hardFailures || []).length > 0) return 'needs_diagnosis'
  if ((remaining || []).length === 0) return 'complete'
  return 'needs_diagnosis' // remaining-but-unready = planning bug / deadlock
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/run-engine/engine-core.js claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js
git commit -m "feat(run-engine): pickExit (two exits, stuck->needs_diagnosis)"
```

---

## Task 6: `convergenceCheck`

**Files:**
- Modify: `claude/meta-skill/knowledge/run-engine/engine-core.js`
- Test: `claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`

- [ ] **Step 1: Write the failing test** (append)

```js
test('convergenceCheck: under cap -> false', () => {
  const hist = [{ root_cause: 'r1' }]
  assert.equal(core.convergenceCheck(hist, 'r1'), false)
})
test('convergenceCheck: at/over cap (>=2 same root) -> true (UNRESOLVED)', () => {
  const hist = [{ root_cause: 'r1' }, { root_cause: 'r1' }, { root_cause: 'r2' }]
  assert.equal(core.convergenceCheck(hist, 'r1'), true)
  assert.equal(core.convergenceCheck(hist, 'r2'), false)
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: FAIL — stub returns `false`.

- [ ] **Step 3: Write implementation** (replace stub)

```js
function convergenceCheck(diagnosisHistory, rootCause) {
  const count = (diagnosisHistory || []).filter(d => d.root_cause === rootCause).length
  return count >= 2
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/run-engine/engine-core.js claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js
git commit -m "feat(run-engine): convergenceCheck (cap=2 per root cause)"
```

---

## Task 7: Test doubles for `pipeline` / `parallel`

**Files:**
- Create: `claude/meta-skill/knowledge/run-engine/tests/harness-doubles.js`
- Test: `claude/meta-skill/knowledge/run-engine/tests/harness-doubles.test.js`

- [ ] **Step 1: Write the failing test**

Create `claude/meta-skill/knowledge/run-engine/tests/harness-doubles.test.js`:

```js
const test = require('node:test')
const assert = require('node:assert/strict')
const { pipeline, parallel } = require('./harness-doubles.js')

test('pipeline: each item flows through all stages', async () => {
  const out = await pipeline([1, 2], x => x + 1, x => x * 10)
  assert.deepEqual(out, [20, 30])
})

test('pipeline: a throwing stage drops that item to null', async () => {
  const out = await pipeline([1, 2], x => { if (x === 1) throw new Error('boom'); return x }, x => x)
  assert.deepEqual(out, [null, 2])
})

test('pipeline: no barrier — item with fast chain finishes without waiting for slow item', async () => {
  const order = []
  const defer = () => { let r; const p = new Promise(res => { r = res }); return { p, r } }
  const slow = defer()
  await pipeline(
    ['fast', 'slow'],
    item => item === 'slow' ? slow.p.then(() => item) : item,
    item => { order.push(item); if (item === 'fast') slow.r(); return item }
  )
  assert.deepEqual(order, ['fast', 'slow']) // fast reached stage 2 before slow resolved stage 1
})

test('parallel: awaits all, failures become null', async () => {
  const out = await parallel([() => 1, () => { throw new Error('x') }, async () => 3])
  assert.deepEqual(out, [1, null, 3])
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/harness-doubles.test.js`
Expected: FAIL — `Cannot find module './harness-doubles.js'`.

- [ ] **Step 3: Write implementation**

Create `claude/meta-skill/knowledge/run-engine/tests/harness-doubles.js`:

```js
// Faithful-enough re-implementations of the Workflow harness primitives,
// per their documented semantics, for deterministic in-Node testing.
// pipeline: each item runs all stages independently, NO barrier between stages.
async function pipeline(items, ...stages) {
  return Promise.all(items.map(async (item, i) => {
    let v = item
    for (const stage of stages) {
      try { v = await stage(v, item, i) } catch { return null }
    }
    return v
  }))
}

// parallel: run all thunks concurrently, await all; a throwing thunk -> null.
async function parallel(thunks) {
  return Promise.all(thunks.map(async t => {
    try { return await t() } catch { return null }
  }))
}

module.exports = { pipeline, parallel }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/harness-doubles.test.js`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/run-engine/tests/harness-doubles.js claude/meta-skill/knowledge/run-engine/tests/harness-doubles.test.js
git commit -m "test(run-engine): pipeline/parallel harness doubles"
```

---

## Task 8: Scriptable fake `agent()`

**Files:**
- Create: `claude/meta-skill/knowledge/run-engine/tests/fake-agent.js`
- Test: `claude/meta-skill/knowledge/run-engine/tests/fake-agent.test.js`

- [ ] **Step 1: Write the failing test**

Create `claude/meta-skill/knowledge/run-engine/tests/fake-agent.test.js`:

```js
const test = require('node:test')
const assert = require('node:assert/strict')
const { makeFakeAgent, makeDeferred } = require('./fake-agent.js')

test('fake agent: returns scripted response by label, records calls', async () => {
  const agent = makeFakeAgent({ 'load-dag': { nodes: [], completed: [] } })
  const r = await agent('load the dag', { label: 'load-dag' })
  assert.deepEqual(r, { nodes: [], completed: [] })
  assert.equal(agent.calls.length, 1)
  assert.equal(agent.calls[0].label, 'load-dag')
})

test('fake agent: array response returns per-call in sequence', async () => {
  const agent = makeFakeAgent({ b: [{ outcome: 'soft_fail' }, { outcome: 'passed' }] })
  assert.equal((await agent('x', { label: 'b' })).outcome, 'soft_fail')
  assert.equal((await agent('x', { label: 'b' })).outcome, 'passed')
  assert.equal((await agent('x', { label: 'b' })).outcome, 'passed') // clamps to last
  assert.equal(agent.counters.b, 3)
})

test('fake agent: deferred response resolves on demand', async () => {
  const d = makeDeferred()
  const agent = makeFakeAgent({ c: { __promise: d.promise } })
  let resolved = false
  const p = agent('x', { label: 'c' }).then(v => { resolved = true; return v })
  await Promise.resolve()
  assert.equal(resolved, false)
  d.resolve({ outcome: 'passed' })
  assert.equal((await p).outcome, 'passed')
})

test('fake agent: label defaults to prompt when no opts.label', async () => {
  const agent = makeFakeAgent({ 'commit:a': { ok: true } })
  await agent('commit:a')
  assert.equal(agent.calls[0].label, 'commit:a')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/fake-agent.test.js`
Expected: FAIL — `Cannot find module './fake-agent.js'`.

- [ ] **Step 3: Write implementation**

Create `claude/meta-skill/knowledge/run-engine/tests/fake-agent.js`:

```js
function makeDeferred() {
  let resolve, reject
  const promise = new Promise((res, rej) => { resolve = res; reject = rej })
  return { promise, resolve, reject }
}

// responses: { [label]: response | response[] | (callIndex, prompt) => response | { __promise } }
function makeFakeAgent(responses) {
  const calls = []
  const counters = {}
  const agent = async (prompt, opts = {}) => {
    const label = opts.label || prompt
    calls.push({ label, prompt, opts })
    counters[label] = (counters[label] || 0) + 1
    const idx = counters[label] - 1
    let spec = responses[label]
    if (typeof spec === 'function') spec = spec(idx, prompt)
    if (Array.isArray(spec)) spec = spec[Math.min(idx, spec.length - 1)]
    if (spec && spec.__promise) return spec.__promise
    return spec
  }
  agent.calls = calls
  agent.counters = counters
  return agent
}

module.exports = { makeFakeAgent, makeDeferred }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/fake-agent.test.js`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/run-engine/tests/fake-agent.js claude/meta-skill/knowledge/run-engine/tests/fake-agent.test.js
git commit -m "test(run-engine): scriptable fake agent + deferred helper"
```

---

## Task 9: `runNode` (soft-retry loop)

**Files:**
- Modify: `claude/meta-skill/knowledge/run-engine/engine-core.js` (replace `runNode` stub)
- Test: `claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`

- [ ] **Step 1: Write the failing test** (append to `engine-core.test.js`; add the require at top if not present)

At the top of `engine-core.test.js`, ensure this require exists (add if missing):

```js
const { makeFakeAgent } = require('./fake-agent.js')
```

Append:

```js
test('runNode: passes first try -> returns passed', async () => {
  const agent = makeFakeAgent({ a: { node_id: 'a', outcome: 'passed', artifacts_written: [], blocking_findings: [] } })
  const r = await core.runNode({ node_id: 'a' }, agent)
  assert.equal(r.outcome, 'passed')
  assert.equal(agent.counters.a, 1)
})

test('runNode: soft-fails then passes within retry budget', async () => {
  const agent = makeFakeAgent({ b: [
    { node_id: 'b', outcome: 'soft_fail', artifacts_written: [], blocking_findings: [{ type: 'placeholder', detail: 'stub bgm' }] },
    { node_id: 'b', outcome: 'passed', artifacts_written: [], blocking_findings: [] }
  ] })
  const r = await core.runNode({ node_id: 'b' }, agent)
  assert.equal(r.outcome, 'passed')
  assert.equal(agent.counters.b, 2) // one retry
})

test('runNode: cross_node -> hard immediately, no retry', async () => {
  const agent = makeFakeAgent({ c: { node_id: 'c', outcome: 'soft_fail', artifacts_written: [], blocking_findings: [{ type: 'cross_node', detail: 'upstream missing', suspected_root_node: 'n1' }] } })
  const r = await core.runNode({ node_id: 'c' }, agent)
  assert.equal(r.outcome, 'hard_fail')
  assert.equal(agent.counters.c, 1) // not retried
})

test('runNode: exhausts soft retries -> hard_fail', async () => {
  const soft = { node_id: 'd', outcome: 'soft_fail', artifacts_written: [], blocking_findings: [{ type: 'placeholder', detail: 'still stub' }] }
  const agent = makeFakeAgent({ d: soft })
  const r = await core.runNode({ node_id: 'd', soft_retry_max: 2 }, agent)
  assert.equal(r.outcome, 'hard_fail')
  assert.equal(r.blocking_findings[0].type, 'exhausted_retries')
  assert.equal(agent.counters.d, 3) // initial + 2 retries
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: FAIL — `runNode` stub returns `undefined`.

- [ ] **Step 3: Write implementation** (replace `async function runNode() {}` inside the marker block)

```js
async function runNode(node, agent) {
  const max = node.soft_retry_max ?? 2
  let attempt = 0
  let strict = ''
  while (true) {
    const r = await agent(`run:${node.node_id}${strict}`, { schema: NODE_RESULT_SCHEMA, label: node.node_id })
    const cls = routeOutcome(r)
    if (cls === 'done') return r
    if (cls === 'hard') return { ...r, outcome: 'hard_fail' }
    if (attempt >= max) {
      return { ...r, outcome: 'hard_fail',
        blocking_findings: [{ type: 'exhausted_retries', detail: `soft retried ${max}x without passing` }] }
    }
    attempt += 1
    strict = ` [retry ${attempt}: must fix all blocking findings]`
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/run-engine/engine-core.js claude/meta-skill/knowledge/run-engine/tests/engine-core.test.js
git commit -m "feat(run-engine): runNode soft-retry loop"
```

---

## Task 10: `commitNode` + `runEngine` loop

**Files:**
- Modify: `claude/meta-skill/knowledge/run-engine/engine-core.js` (replace `commitNode` + `runEngine` stubs)
- Test: `claude/meta-skill/knowledge/run-engine/tests/engine-integration.test.js`

- [ ] **Step 1: Write the failing test**

Create `claude/meta-skill/knowledge/run-engine/tests/engine-integration.test.js`:

```js
const test = require('node:test')
const assert = require('node:assert/strict')
const core = require('../engine-core.js')
const { pipeline } = require('./harness-doubles.js')
const { makeFakeAgent } = require('./fake-agent.js')

const passed = id => ({ node_id: id, outcome: 'passed', artifacts_written: [`art/${id}`], blocking_findings: [] })

test('runEngine: linear DAG completes', async () => {
  const dag = { nodes: [
    { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'b', capability: 'x', hard_blocked_by: ['a'], exit_artifacts: [] }
  ], completed: [] }
  const agent = makeFakeAgent({
    'load-dag': dag,
    a: passed('a'), b: passed('b'),
    'commit:a': {}, 'commit:b': {}
  })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'complete')
  assert.equal(agent.counters['commit:a'], 1)
  assert.equal(agent.counters['commit:b'], 1)
})

test('runEngine: idempotent — completed nodes skipped', async () => {
  const dag = { nodes: [
    { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'b', capability: 'x', hard_blocked_by: ['a'], exit_artifacts: [] }
  ], completed: ['a'] }
  const agent = makeFakeAgent({ 'load-dag': dag, b: passed('b'), 'commit:b': {} })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'complete')
  assert.equal(agent.counters.a, undefined) // never ran a
})

test('runEngine: expander adds a node that then runs', async () => {
  const dag = { nodes: [
    { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] }
  ], completed: [], expanders: ['mk_b'] }
  const agent = makeFakeAgent({
    'load-dag': dag,
    'expand:mk_b': { new_nodes: [{ node_id: 'b', capability: 'x', hard_blocked_by: ['a'], exit_artifacts: [] }] },
    a: passed('a'), b: passed('b'), 'commit:a': {}, 'commit:b': {}
  })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'complete')
  assert.equal(agent.counters.b, 1) // expanded node executed
})

test('runEngine: applied_expanders are NOT re-run (fix C5)', async () => {
  const dag = { nodes: [
    { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] }
  ], completed: ['a'], expanders: ['mk_b'], applied_expanders: ['mk_b'] }
  const agent = makeFakeAgent({ 'load-dag': dag })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'complete')
  assert.equal(agent.counters['expand:mk_b'], undefined) // already applied -> skipped
})

test('runEngine: stuck graph -> needs_diagnosis with synthesized deadlock (fix C3)', async () => {
  const dag = { nodes: [
    { node_id: 'a', capability: 'x', hard_blocked_by: ['ghost'], exit_artifacts: [] }
  ], completed: [] }
  const agent = makeFakeAgent({ 'load-dag': dag })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(res.hardFailures.length, 1)
  assert.equal(res.hardFailures[0].blocking_findings[0].type, 'deadlock')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-integration.test.js`
Expected: FAIL — `runEngine` stub returns `{status:'complete'}` but never calls commit/expand (counter + status assertions fail).

- [ ] **Step 3: Write implementation** (replace `commitNode` + `runEngine` stubs inside the marker block)

Also **replace the `serializeCommit` stub** (from Task 1) with the real serialized queue, and add the module-level queue var just before it:

```js
let _commitQueue = Promise.resolve()
function serializeCommit(fn) {           // fix C1: physical commits never overlap
  const next = _commitQueue.then(fn, fn) // chain regardless of prior outcome
  _commitQueue = next.then(() => {}, () => {})
  return next
}

async function commitNode(result, agent, done) {
  // The commit agent appends transition_log + any result.assumed_decisions to
  // assumed-decisions.json (real prompt wired in Plan 2). Engine persists; subagent does not.
  await agent(`commit:${result.node_id}`, { label: `commit:${result.node_id}` })
  done.add(result.node_id)
}

async function runEngine({ agent, pipeline, log = () => {}, phase = () => {} }) {
  phase('Load')
  const dag = await agent('load workflow.json into DAG_SCHEMA', { schema: DAG_SCHEMA, label: 'load-dag' })
  const done = new Set(dag.completed || [])
  const applied = new Set(dag.applied_expanders || [])   // fix C5

  phase('Expand')
  for (const exp of (dag.expanders || [])) {
    if (applied.has(exp)) continue                        // fix C5: don't re-run on resume
    const r = await agent(`run expander ${exp}; return new_nodes`, { schema: EXPAND_SCHEMA, label: `expand:${exp}` })
    dag.nodes = mergeExpanded(dag.nodes, (r && r.new_nodes) || [])
    applied.add(exp)
  }

  phase('Execute')
  while (true) {
    const ready = computeReady(dag.nodes, done)
    if (ready.length === 0) break
    log(`running ${ready.length} ready node(s)`)
    const outcomes = await pipeline(
      ready,
      node => runNode(node, agent),
      result => routeOutcome(result) === 'done'
        ? serializeCommit(() => commitNode(result, agent, done)).then(() => result)  // fix C1: serialized
        : result,
      result => routeOutcome(result) === 'done' ? null : result
    )
    const hardFailures = outcomes.filter(r => r && routeOutcome(r) === 'hard')
    if (hardFailures.length > 0) {
      await agent('record hard failures to diagnosis_history', { label: 'commit-failures' })
      return { status: 'needs_diagnosis', hardFailures }
    }
  }
  const remaining = dag.nodes.filter(n => !done.has(n.node_id))
  if (pickExit(remaining, []) === 'needs_diagnosis') {
    // fix C3: stuck graph (cycle / missing dep) — synthesize a deadlock failure so the
    // /run handler always receives a non-empty hardFailures[].
    return { status: 'needs_diagnosis', hardFailures: [{
      node_id: remaining[0].node_id, outcome: 'hard_fail',
      blocking_findings: [{ type: 'deadlock',
        detail: `stuck: ${remaining.map(n => n.node_id).join(',')} unreachable (cycle or missing dep)` }]
    }] }
  }
  return { status: 'complete' }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-integration.test.js`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/run-engine/engine-core.js claude/meta-skill/knowledge/run-engine/tests/engine-integration.test.js
git commit -m "feat(run-engine): commitNode + runEngine loop (load/expand/execute/exits)"
```

---

## Task 11: L2 — the four pipeline concurrency assertions

**Files:**
- Modify: `claude/meta-skill/knowledge/run-engine/tests/engine-integration.test.js`

- [ ] **Step 1: Write the failing test** (append; add `makeDeferred` to the require at top of the file)

Update the top require line to:

```js
const { makeFakeAgent, makeDeferred } = require('./fake-agent.js')
```

Append:

```js
// Fixture: A fast-pass, B soft-then-pass, C cross_node hard-fail. All siblings (ready together).
function siblingDag() {
  return { nodes: [
    { node_id: 'A', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'B', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'C', capability: 'x', hard_blocked_by: [], exit_artifacts: [] }
  ], completed: [] }
}

test('L2.1 no cross-talk: committing A does not commit C', async () => {
  const agent = makeFakeAgent({
    'load-dag': siblingDag(),
    A: passed('A'),
    B: passed('B'),
    C: { node_id: 'C', outcome: 'hard_fail', artifacts_written: [], blocking_findings: [{ type: 'cross_node', suspected_root_node: 'n1' }] },
    'commit:A': {}, 'commit:B': {}, 'commit-failures': {}
  })
  await core.runEngine({ agent, pipeline })
  assert.equal(agent.counters['commit:A'], 1)
  assert.equal(agent.counters['commit:B'], 1)
  assert.equal(agent.counters['commit:C'], undefined) // C never committed
})

test('L2.2 retry isolation: B retries without re-running A or C', async () => {
  const agent = makeFakeAgent({
    'load-dag': siblingDag(),
    A: passed('A'),
    B: [
      { node_id: 'B', outcome: 'soft_fail', artifacts_written: [], blocking_findings: [{ type: 'placeholder', detail: 'x' }] },
      { node_id: 'B', outcome: 'passed', artifacts_written: [], blocking_findings: [] }
    ],
    C: passed('C'),
    'commit:A': {}, 'commit:B': {}, 'commit:C': {}
  })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'complete')
  assert.equal(agent.counters.A, 1)
  assert.equal(agent.counters.C, 1)
  assert.equal(agent.counters.B, 2) // exactly one retry
})

test('L2.3 hard-fail bubbles: C cross_node -> needs_diagnosis, C not retried', async () => {
  const agent = makeFakeAgent({
    'load-dag': siblingDag(),
    A: passed('A'), B: passed('B'),
    C: { node_id: 'C', outcome: 'soft_fail', artifacts_written: [], blocking_findings: [{ type: 'cross_node', suspected_root_node: 'n1' }] },
    'commit:A': {}, 'commit:B': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(res.hardFailures.length, 1)
  assert.equal(res.hardFailures[0].node_id, 'C')
  assert.equal(agent.counters.C, 1) // not retried
})

test('L2.4 mid-batch commit does not corrupt the in-flight batch', async () => {
  // C is slow (deferred). A passes fast and commits while C is still running.
  // Assert: each ready node runs exactly once; the batch is not recomputed mid-flight.
  const cGate = makeDeferred()
  const agent = makeFakeAgent({
    'load-dag': siblingDag(),
    A: passed('A'),
    B: passed('B'),
    C: { __promise: cGate.promise },
    'commit:A': {}, 'commit:B': {}, 'commit:C': {}
  })
  const runPromise = core.runEngine({ agent, pipeline })
  await Promise.resolve()
  // A and B already committed while C is parked:
  // resolve C only after the others have progressed
  cGate.resolve(passed('C'))
  const res = await runPromise
  assert.equal(res.status, 'complete')
  assert.equal(agent.counters.A, 1)
  assert.equal(agent.counters.B, 1)
  assert.equal(agent.counters.C, 1) // C ran exactly once — never re-queued by a recompute
})

test('L2.5 commit serialization: second commit waits for the first (fix C1)', async () => {
  // Two passing siblings; gate the first commit so we can observe the second has not started.
  const firstCommit = makeDeferred()
  const started = []
  const agent = makeFakeAgent({
    'load-dag': { nodes: [
      { node_id: 'A', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
      { node_id: 'B', capability: 'x', hard_blocked_by: [], exit_artifacts: [] }
    ], completed: [] },
    A: passed('A'), B: passed('B'),
    'commit:A': (i, p) => { started.push('A'); return firstCommit.promise },
    'commit:B': (i, p) => { started.push('B'); return {} }
  })
  const run = core.runEngine({ agent, pipeline })
  await new Promise(r => setImmediate(r))
  // Only the first commit may have started; B's commit must be queued behind it.
  assert.deepEqual(started, ['A'])
  firstCommit.resolve({})
  await run
  assert.deepEqual(started, ['A', 'B']) // serialized order
})
```

(Spec §7 Layer 2 assertion 6 — stuck-graph deadlock — is already covered by the `runEngine: stuck graph` test in Task 10.)

- [ ] **Step 2: Run test to verify it fails (or passes)**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/engine-integration.test.js`
Expected: PASS — the engine from Task 10 already satisfies L2.1–L2.5. (If any fail, the engine logic — not the test — is wrong; fix `runEngine`/`runNode` until green. These are the core acceptance criteria from spec §7 Layer 2.)

- [ ] **Step 3: (No new implementation expected.)** If L2.4 reveals the batch is recomputed mid-flight, confirm `computeReady` is called only at the top of the `while` loop (it is, in Task 10). If L2.5 fails, confirm `serializeCommit` chains onto `_commitQueue` (Task 10). No code change should be needed.

- [ ] **Step 4: Run the full test dir**

Run: `node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'`
Expected: PASS — all suites green.

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/run-engine/tests/engine-integration.test.js
git commit -m "test(run-engine): L2 four pipeline concurrency assertions"
```

---

## Task 12: Workflow shell `run-engine.workflow.js` + anti-drift sync check

**Files:**
- Create: `claude/meta-skill/knowledge/run-engine/run-engine.workflow.js`
- Create: `claude/meta-skill/knowledge/run-engine/tests/sync-check.test.js`

- [ ] **Step 1: Write the failing test**

Create `claude/meta-skill/knowledge/run-engine/tests/sync-check.test.js`:

```js
const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')

const dir = path.join(__dirname, '..')
const START = '// <<<ENGINE-CORE-START>>>'
const END = '// <<<ENGINE-CORE-END>>>'

function coreRegion(file) {
  const src = fs.readFileSync(path.join(dir, file), 'utf8')
  const a = src.indexOf(START)
  const b = src.indexOf(END)
  assert.ok(a !== -1 && b !== -1 && b > a, `markers missing/ordered wrong in ${file}`)
  return src.slice(a, b + END.length).trim()
}

test('workflow shell inlines engine-core verbatim (no drift)', () => {
  assert.equal(coreRegion('run-engine.workflow.js'), coreRegion('engine-core.js'))
})

test('workflow shell has the meta block and invokes runEngine', () => {
  const src = fs.readFileSync(path.join(dir, 'run-engine.workflow.js'), 'utf8')
  assert.match(src, /export const meta = \{/)
  assert.match(src, /runEngine\(\s*\{\s*agent/)
})

test('workflow shell does NOT require/import engine-core (sandbox-safe)', () => {
  const src = fs.readFileSync(path.join(dir, 'run-engine.workflow.js'), 'utf8')
  assert.doesNotMatch(src, /require\(|import .* from/)
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/sync-check.test.js`
Expected: FAIL — `run-engine.workflow.js` does not exist.

- [ ] **Step 3: Write implementation**

Create `claude/meta-skill/knowledge/run-engine/run-engine.workflow.js`. **Copy the marker region from `engine-core.js` verbatim** (everything from `// <<<ENGINE-CORE-START>>>` through `// <<<ENGINE-CORE-END>>>` inclusive), then wrap it:

```js
export const meta = {
  name: 'run-engine',
  description: 'Autonomous DAG executor for meta-skill /run (Phase B): schedule, parallel-execute, self-heal, commit.',
  phases: [
    { title: 'Load' },
    { title: 'Expand' },
    { title: 'Execute' }
  ]
}

// <<<ENGINE-CORE-START>>>
// ... PASTE THE ENTIRE MARKER REGION FROM engine-core.js HERE, VERBATIM ...
// <<<ENGINE-CORE-END>>>

const result = await runEngine({ agent, pipeline, log, phase })
return result
```

The pasted region defines `DAG_SCHEMA`, `NODE_RESULT_SCHEMA`, `EXPAND_SCHEMA`, `computeReady`, `routeOutcome`, `mergeExpanded`, `pickExit`, `convergenceCheck`, `serializeCommit` (+ its `_commitQueue` var), `runNode`, `commitNode`, `runEngine`. The shell adds ONLY the `meta` block above it and the `runEngine(...)` call below it — no `require`, no `module.exports`, no `import`. (The sync-check test compares the whole marker region byte-for-byte, so a verbatim copy is what matters — this list is just orientation.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test claude/meta-skill/knowledge/run-engine/tests/sync-check.test.js`
Expected: PASS (3 tests). Also run `node --check claude/meta-skill/knowledge/run-engine/run-engine.workflow.js` — note this MAY error on the top-level `await`/`return`/`export` (those are Workflow-sandbox constructs, not plain-module valid); if `node --check` errors only on top-level `await`/`return`, that is expected. The authoritative syntax gate for the shell is the sync-check test + the L3 real run.

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/run-engine/run-engine.workflow.js claude/meta-skill/knowledge/run-engine/tests/sync-check.test.js
git commit -m "feat(run-engine): Workflow shell + anti-drift sync check"
```

---

## Task 13: L3 fixture + runbook (real-agent end-to-end)

**Files:**
- Create: `claude/meta-skill/knowledge/run-engine/tests/fixtures/mini-workflow.json`
- Create: `claude/meta-skill/knowledge/run-engine/tests/L3-runbook.md`

- [ ] **Step 1: Write the fixture**

Create `claude/meta-skill/knowledge/run-engine/tests/fixtures/mini-workflow.json`:

```json
{
  "schema_version": "2.0",
  "project_name": "run-engine-L3-fixture",
  "nodes": [
    { "node_id": "n1", "capability": "noop", "hard_blocked_by": [], "exit_artifacts": [{ "path": ".allforai/_l3/n1.json" }] },
    { "node_id": "n2", "capability": "noop", "hard_blocked_by": ["n1"], "alignment_refs": ["n3"], "exit_artifacts": [{ "path": ".allforai/_l3/n2.json" }] },
    { "node_id": "n3", "capability": "noop", "hard_blocked_by": ["n1"], "alignment_refs": ["n2"], "exit_artifacts": [{ "path": ".allforai/_l3/n3.json" }], "soft_retry_max": 2 },
    { "node_id": "n4", "capability": "noop", "hard_blocked_by": ["n1"], "decision_inputs": [".allforai/_l3/decision-n4.json"], "exit_artifacts": [{ "path": ".allforai/_l3/n4.json" }] },
    { "node_id": "n5", "capability": "noop", "hard_blocked_by": ["n1"], "exit_artifacts": [{ "path": ".allforai/_l3/n5.json" }] },
    { "node_id": "n6", "capability": "noop", "hard_blocked_by": ["n4", "n5"], "exit_artifacts": [{ "path": ".allforai/_l3/n6.json" }] }
  ],
  "completed": [],
  "expanders": ["mk_n7"],
  "transition_log": []
}
```

- [ ] **Step 2: Write the runbook**

Create `claude/meta-skill/knowledge/run-engine/tests/L3-runbook.md`:

```markdown
# L3 Runbook — Real-Agent End-to-End

Run inside a real Claude Code session (the Workflow tool requires the harness).
Token cost is acceptable: this tests the engine, not a user project.

## Setup
1. Stage the fixture at the engine's canonical path (fix R2 — `loadDagPrompt` reads
   `.allforai/bootstrap/workflow.json`, NOT the fixtures dir):
   `mkdir -p .allforai/bootstrap .allforai/_l3 && cp claude/meta-skill/knowledge/run-engine/tests/fixtures/mini-workflow.json .allforai/bootstrap/workflow.json`
2. Ensure `.allforai/_l3/decision-n4.json` EXISTS (Phase A would have produced it):
   `{"decision":"variant-A","rationale":"L3 fixture preset"}`
3. Node subagents are "noop": each writes its `exit_artifacts` path with `{"ok":true}` and returns
   `{node_id, outcome:"passed", artifacts_written:[...], blocking_findings:[]}` — EXCEPT the seeded behaviors below.

## Seeded behaviors (to exercise every path)
- **n3**: first attempt returns `outcome:"soft_fail"` with a `placeholder` finding; retry returns `passed`. → verifies soft self-heal.
- **n5**: returns `outcome:"soft_fail"` with `{type:"cross_node", suspected_root_node:"n1"}`. → verifies hard-fail → needs_diagnosis. After diagnosis removes n1 from `completed` and reruns, n5 returns `passed`.
- **expander mk_n7**: appends `n7` (hard_blocked_by `["n6"]`). → verifies "plan auto-updates during run".

## Pass criteria
- [ ] Engine invoked ≥2× (initial run → post-diagnosis resume).
- [ ] n2 and n3 ran concurrently (both ready after n1; check phase/log output).
- [ ] Final `transition_log` marks n1..n7 all `completed`; no `placeholder` residue in any artifact.
- [ ] n4 ran without any stop (its `decision_inputs` artifact was present).
- [ ] Deleting `decision-n4.json` and re-running yields a `hard_fail` for n4 (planning bug), NOT a stop.
- [ ] n7 was expanded and executed.
- [ ] Kill mid-run and re-invoke: already-`completed` nodes are NOT re-run (idempotency).
```

- [ ] **Step 3: Validate the fixture is well-formed JSON**

Run: `node -e "JSON.parse(require('fs').readFileSync('claude/meta-skill/knowledge/run-engine/tests/fixtures/mini-workflow.json','utf8')); console.log('valid json')"`
Expected: `valid json`

- [ ] **Step 4: (No automated assertion — L3 is a manual real-agent procedure.)**

The runbook is executed during integration/acceptance, not in `node --test`. This task delivers the fixture + procedure.

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/run-engine/tests/fixtures/mini-workflow.json claude/meta-skill/knowledge/run-engine/tests/L3-runbook.md
git commit -m "test(run-engine): L3 fixture + real-agent runbook"
```

---

## Task 14: Test entry point + README

**Files:**
- Create: `claude/meta-skill/knowledge/run-engine/README.md`

- [ ] **Step 1: Write the README** (documents how to run the suite — no failing test needed; this is docs)

Create `claude/meta-skill/knowledge/run-engine/README.md`:

```markdown
# run-engine

Deterministic Workflow-based executor for meta-skill `/run` (Phase B). See the
design spec at `docs/superpowers/specs/2026-06-02-workflow-run-engine-design.md`.

## Files
- `engine-core.js` — canonical logic (pure fns + `runEngine`). Edit logic HERE.
- `run-engine.workflow.js` — Workflow shell; inlines `engine-core.js` verbatim
  between `// <<<ENGINE-CORE-START>>>` / `// <<<ENGINE-CORE-END>>>`. After editing
  `engine-core.js`, copy the marker region into the shell, then run sync-check.
- `tests/` — L1 unit, L2 fake-agent integration, sync-check; `tests/L3-runbook.md` for real-agent E2E.

## Run tests (L1 + L2 + sync-check)
    node --test claude/meta-skill/knowledge/run-engine/tests/

All suites must be green before invoking the Workflow shell in a real run.
```

- [ ] **Step 2: Run the whole suite to confirm green**

Run: `node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'`
Expected: PASS — every suite (engine-core, harness-doubles, fake-agent, engine-integration, sync-check).

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/knowledge/run-engine/README.md
git commit -m "docs(run-engine): README + test entry point"
```

---

## Task 15: Version bump

**Files:**
- Modify: `claude/meta-skill/.claude-plugin/plugin.json`
- Modify: `claude/meta-skill/.claude-plugin/marketplace.json`
- Modify: the bootstrap skill version marker (see step 1)

- [ ] **Step 1: Read current versions**

Run: `grep -n '"version"' claude/meta-skill/.claude-plugin/plugin.json claude/meta-skill/.claude-plugin/marketplace.json; grep -niE 'version|Protocol v' claude/meta-skill/skills/bootstrap.md | head -3`
Expected: shows the current plugin/marketplace versions and the bootstrap body version marker.

- [ ] **Step 2: Bump all three (minor — new engine subsystem)**

Edit `claude/meta-skill/.claude-plugin/plugin.json` and `claude/meta-skill/.claude-plugin/marketplace.json`: increment the middle version number (e.g. `0.8.11` → `0.9.0`). **Add a `version:` field to `skills/bootstrap.md` YAML frontmatter** set to the same string (fix R3 — the frontmatter `version:` is now the canonical third location; if a body header `# Bootstrap Protocol vX.Y.Z` exists, demote it to a non-authoritative comment). Use the SAME version string in all three. (Per repo discipline: versions live in 3 places and drift easily.)

- [ ] **Step 3: Verify they match**

Run: `grep -rn '0.9.0' claude/meta-skill/.claude-plugin/ claude/meta-skill/skills/bootstrap.md`
Expected: three matches with the identical new version (substitute your chosen version for `0.9.0`).

- [ ] **Step 4: Final full-suite run**

Run: `node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'`
Expected: PASS — all green.

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/.claude-plugin/plugin.json claude/meta-skill/.claude-plugin/marketplace.json claude/meta-skill/skills/bootstrap.md
git commit -m "chore(meta-skill): bump version for run-engine Plan 1"
```

---

## Self-Review

**1. Spec coverage (Plan 1 portion):**

| Spec §  | Covered by |
|---------|------------|
| §4.1 DAG_SCHEMA / NODE_RESULT_SCHEMA / EXPAND_SCHEMA | Task 1 |
| §4.2.3 computeReady (alignment_refs non-blocking) | Task 2 |
| §4.3 routeOutcome soft/hard routing | Task 3 |
| §4.2.2 mergeExpanded idempotent | Task 4 |
| §4.2.7 two exits / pickExit | Task 5 |
| §4.5 per-cause convergence cap | Task 6 — `convergenceCheck` is the **tested reference** for the ≥2-per-cause policy; diagnosis runs in the `/run` markdown layer, which applies the same rule inline (Plan 2 Task 5 step 3d) + the global cap (L1, step 3b). Kept as a unit-tested spec of the policy, like the engine documents its own contracts. |
| §4.2.5 runNode soft-retry | Task 9 |
| §4.2.6 commitNode + §4.2 full loop | Task 10 |
| §4.4 pipeline shape + §7 Layer 2 four assertions | Tasks 7, 11 |
| §7 Layer 1 unit tests | Tasks 2–6, 9 |
| §7 Layer 3 fixture + runbook | Task 13 |
| §3.2 `knowledge/run-engine/` naming (avoid `engines/`) | all tasks |
| §3.3.1 CC-superset fields in schema | Task 1 |
| §3.3.2 idempotency (completed skip) | Task 10 (idempotent test) |
| §7 DoD version bump (3 locations, R3 frontmatter) | Task 15 |
| §8.1 C1 serialized commit + assumed_decisions | Tasks 1, 10, 11 (L2.5) |
| §8.1 C2 repair-cascade closure | **Plan 2** (Python `compute_reset_closure.py` — repair runs in the /run main loop, not the JS engine) |
| §8.1 C3 stuck-graph deadlock exit | Task 10 (`stuck graph` integration test) |
| §8.1 C5 applied_expanders skip | Tasks 1, 10 |
| §8.1 R2 L3 fixture at canonical path | Task 13 |

**Deferred to Plan 2/3 (intentionally NOT in this plan):** load-DAG/expander/commit *agents'* real prompts + file I/O (Plan 2 wires real agents; Plan 1 uses fakes), `/run` skill exit-handling + diagnosis resume (§4.5, Plan 2), bootstrap emitting superset fields + `expanders` list (§9, Plan 2), G0/A0/Phase A audits (§4.6–4.8, Plan 3), `human_gate`→`decision_inputs` migration in bootstrap (Plan 2), Codex/OpenCode superset-ignore check (Plan 2).

**2. Placeholder scan:** No "TBD"/"handle errors"/"similar to". Task 12 intentionally instructs a verbatim copy (the only correct way to inline for the sandbox) and Task 13's L3 is a manual runbook by design (real-agent E2E can't run in `node --test`). Both are explicit, not placeholders.

**3. Type consistency:** `done` is a `Set` everywhere (Tasks 2, 10). `routeOutcome` returns `'done'|'soft'|'hard'` consistently (Tasks 3, 9, 10, 11). `runNode(node, agent)` / `commitNode(result, agent, done)` / `runEngine({agent,pipeline,log,phase})` signatures match across Tasks 9–11 and the README. Fake-agent labels (`load-dag`, `run:<id>` keyed by `label:<id>`, `commit:<id>`, `expand:<name>`, `commit-failures`) are consistent between `runEngine` (Task 10) and every integration test (Tasks 10, 11). Marker strings `// <<<ENGINE-CORE-START>>>` / `// <<<ENGINE-CORE-END>>>` identical in Tasks 1 and 12.
