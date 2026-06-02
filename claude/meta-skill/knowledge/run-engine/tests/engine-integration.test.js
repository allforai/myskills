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
