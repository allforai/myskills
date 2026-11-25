const test = require('node:test')
const assert = require('node:assert/strict')
const core = require('../engine-core.js')
const { pipeline } = require('./harness-doubles.js')
const { makeFakeAgent, makeDeferred } = require('./fake-agent.js')

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
    'validate-readiness': { status: 'ready', blockers: [] },
    a: passed('a'), b: passed('b'), 'commit:a': {}, 'commit:b': {}
  })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'complete')
  assert.equal(agent.counters.b, 1) // expanded node executed
})

test('runEngine: expander reruns after a wave and discovers a late node', async () => {
  const dag = { nodes: [
    { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] }
  ], completed: [], expanders: ['mk_b'] }
  const agent = makeFakeAgent({
    'load-dag': dag,
    'expand:mk_b': [
      { new_nodes: [] },
      { new_nodes: [{ node_id: 'b', capability: 'x',
        hard_blocked_by: ['a'], exit_artifacts: [] }] },
      { new_nodes: [] }
    ],
    'validate-readiness': { status: 'ready', blockers: [] },
    a: passed('a'), b: passed('b'), 'commit:a': {}, 'commit:b': {}
  })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'complete')
  assert.equal(agent.counters['expand:mk_b'], 3)
  assert.equal(agent.counters.b, 1)
})

test('runEngine: dynamic expansion readiness failure blocks execution', async () => {
  const dag = { nodes: [
    { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] }
  ], completed: [], expanders: ['mk_b'] }
  const agent = makeFakeAgent({
    'load-dag': dag,
    'expand:mk_b': { new_nodes: [{ node_id: 'b', capability: 'x',
      hard_blocked_by: ['a'], exit_artifacts: [] }] },
    'validate-readiness': {
      status: 'not_ready', blockers: [{ type: 'missing_command', detail: 'build unavailable' }]
    }
  })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(res.hardFailures[0].node_id, 'dynamic-expansion-readiness')
  assert.equal(agent.counters.a, undefined)
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

test('L2.4 a slow sibling does not cause completed work to be dispatched twice', async () => {
  // C is slow (deferred). A passes fast, but completion waits for wave safety.
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
  // Resolve C after the others have progressed; no mid-flight rescheduling.
  cGate.resolve(passed('C'))
  const res = await runPromise
  assert.equal(res.status, 'complete')
  assert.equal(agent.counters.A, 1)
  assert.equal(agent.counters.B, 1)
  assert.equal(agent.counters.C, 1) // C ran exactly once — never re-queued by a recompute
})

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

test('runEngine: a completed node that only waits for a node sent back is not rerun', async () => {
  // `--route-defects` reset `strings` and `screen`, which read the file; `icons` waits for
  // `strings` without reading it and keeps its completion.
  const dag = { nodes: [
    { node_id: 'strings', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'screen', capability: 'x', hard_blocked_by: ['strings'], exit_artifacts: [] },
    { node_id: 'icons', capability: 'x', hard_blocked_by: ['strings'], exit_artifacts: [] }
  ], completed: ['icons'] }
  const order = []
  const ran = id => () => { order.push(id); return passed(id) }
  const agent = makeFakeAgent({ 'load-dag': dag, strings: ran('strings'), screen: ran('screen'),
    icons: ran('icons'), 'commit:strings': {}, 'commit:screen': {} })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'complete')
  assert.deepEqual(order, ['strings', 'screen'])
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

const receipt = id => ({ status: 'recorded', node_id: id, transition_index: 0, replayed: false })

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
    'commit:B': (i, p) => { started.push('B'); return receipt('B') }
  })
  const run = core.runEngine({ agent, pipeline })
  await new Promise(r => setImmediate(r))
  // Only the first commit may have started; B's commit must be queued behind it.
  assert.deepEqual(started, ['A'])
  firstCommit.resolve(receipt('A'))
  await run
  assert.deepEqual(started, ['A', 'B']) // serialized order
})

test('runEngine: recovers interrupted waves before loading, and brackets every wave', async () => {
  const dag = { nodes: [
    { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'b', capability: 'x', hard_blocked_by: ['a'], exit_artifacts: [] }
  ], completed: [] }
  const agent = makeFakeAgent({ 'load-dag': dag, a: passed('a'), b: passed('b'), 'commit:a': {}, 'commit:b': {} })
  await core.runEngine({ agent, pipeline })
  const labels = agent.calls.map(c => c.label)
  assert.ok(labels.indexOf('recover-waves') < labels.indexOf('load-dag'))
  const order = labels.filter(l => ['begin-wave', 'a', 'b', 'end-wave', 'commit:a', 'commit:b'].includes(l))
  assert.deepEqual(order, ['begin-wave', 'a', 'end-wave', 'commit:a', 'begin-wave', 'b', 'end-wave', 'commit:b'])
  assert.match(agent.calls.find(c => c.label === 'begin-wave').prompt, /"node_ids":\["a"\]/)
})

test('runEngine: a wave the engine never saw end is left open for recovery', async () => {
  const dag = { nodes: [{ node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] }], completed: [] }
  const agent = makeFakeAgent({ 'load-dag': dag, a: () => { throw new Error('host died') } })
  const dying = async (items, fn) => { await Promise.all(items.map(fn)); throw new Error('engine interrupted') }
  await assert.rejects(core.runEngine({ agent, pipeline: dying }))
  assert.equal(agent.counters['begin-wave'], 1)
  assert.equal(agent.counters['end-wave'], undefined)
})

// A step runs on the model the user named for its tier; a judge is always strong.
test('runEngine: each step runs on its tier, and nothing that judges is ever below strong', async () => {
  const dag = { nodes: [
    { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [], model_tier: 'light' },
    { node_id: 'b', capability: 'x', hard_blocked_by: ['a'], exit_artifacts: [], model_tier: 'standard' },
    { node_id: 'c', capability: 'x', hard_blocked_by: ['b'], exit_artifacts: [] }
  ], completed: [] }
  const responses = { 'load-dag': dag, a: passed('a'), b: passed('b'), c: passed('c'),
    'commit:a': {}, 'commit:b': {}, 'commit:c': {} }
  const routed = makeFakeAgent(responses)
  const models = { strong: 'S', standard: 'M', light: 'L' }
  assert.equal((await core.runEngine({ agent: routed, pipeline, models })).status, 'complete')
  const modelOf = Object.fromEntries(routed.calls.map(c => [c.label, c.opts.model]))
  assert.deepEqual([modelOf.a, modelOf.b, modelOf.c], ['L', 'M', 'S'])
  for (const label of ['run-policy', 'begin-wave', 'commit:a']) assert.equal(modelOf[label], 'L', label)
  for (const label of ['load-dag', 'verify:a', 'verify:b', 'verify:c']) assert.equal(modelOf[label], 'S', label)
  // A tier with no name runs on the session model.
  const lightOnly = makeFakeAgent(responses)
  await core.runEngine({ agent: lightOnly, pipeline, models: { light: 'L' } })
  assert.equal(lightOnly.calls.find(c => c.label === 'b').opts.model, undefined)
  assert.equal(lightOnly.calls.find(c => c.label === 'verify:a').opts.model, undefined)
  const none = makeFakeAgent(responses)
  await core.runEngine({ agent: none, pipeline })
  assert.ok(none.calls.every(c => c.opts.model === undefined))
})

test('every label the engine dispatches has a deliberate tier', () => {
  const src = require('node:fs').readFileSync(require('node:path').join(__dirname, '..', 'engine-core.js'), 'utf8')
  const heads = new Set([...src.matchAll(/label: [`']([a-z-]+)[:'`]/g)].map(m => m[1]))
  const strong = ['verify', 'repair', 'inline-review', 'load-dag', 'inherit', 'expand', 'validate-readiness']
  for (const head of heads) {
    const tier = core.tierOf(head, []) === 'light' || core.tierOf(`${head}:x`, []) === 'light' ? 'light' : 'strong'
    assert.equal(tier === 'strong', strong.includes(head), `${head}: classify it as light or keep it strong on purpose`)
  }
})

// A transition is complete only when record_transition.py's receipt says so.
test('a receipt for another node does not complete this one', async () => {
  const agent = makeFakeAgent({ 'load-dag': { nodes: [
      { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
      { node_id: 'b', capability: 'x', hard_blocked_by: ['a'], exit_artifacts: [] }
    ], completed: [] },
    a: passed('a'), b: passed('b'), 'commit:a': receipt('b') })
  const out = await core.runEngine({ agent, pipeline })
  assert.equal(out.status, 'needs_diagnosis')
  assert.equal(out.hardFailures[0].blocking_findings[0].type, 'unrecorded_transition')
  assert.equal(agent.counters.b, undefined, 'nothing downstream runs on an unrecorded completion')
})

test('a replayed receipt completes the node', async () => {
  const agent = makeFakeAgent({ 'load-dag': { nodes: [
      { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] }], completed: [] },
    a: passed('a'), 'commit:a': { ...receipt('a'), replayed: true } })
  const out = await core.runEngine({ agent, pipeline })
  assert.equal(out.status, 'complete')
})

test('a commit relay that answers nothing is asked once more, then trusted only on a receipt', async () => {
  const agent = makeFakeAgent({ 'load-dag': { nodes: [
      { node_id: 'a', capability: 'x', hard_blocked_by: [], exit_artifacts: [] }], completed: [] },
    a: passed('a'), 'commit:a': () => null, 'commit:a:retry': receipt('a') })
  const out = await core.runEngine({ agent, pipeline })
  assert.equal(out.status, 'complete')
  assert.equal(agent.counters['commit:a:retry'], 1)
})
