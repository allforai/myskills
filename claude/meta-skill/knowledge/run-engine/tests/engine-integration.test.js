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
