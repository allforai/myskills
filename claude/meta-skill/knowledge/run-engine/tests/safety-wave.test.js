const test = require('node:test')
const assert = require('node:assert/strict')
const core = require('../engine-core.js')
const { pipeline } = require('./harness-doubles.js')
const { makeFakeAgent, makeDeferred } = require('./fake-agent.js')
const { makeLedgerDouble, ledgerResponses } = require('./ledger-double.js')

const node = id => ({ node_id: id, capability: 'x', hard_blocked_by: [], exit_artifacts: [] })
const passed = id => ({ node_id: id, outcome: 'passed', artifacts_written: [`art/${id}`], blocking_findings: [] })
const policy = { status: 'run_policy_ready', policy: {
  on_repeated_failure: 'halt', on_safety_warning: 'halt', on_needs_iteration: 'halt_with_report'
} }

test('a late safety halt withholds every completion in its concurrent wave', async () => {
  const late = makeDeferred()
  const agent = makeFakeAgent({
    'run-policy': policy,
    'load-dag': { nodes: [node('fast'), node('unsafe')], completed: [] },
    fast: passed('fast'), unsafe: { __promise: late.promise },
    'quarantine-wave': { status: 'quarantined', node_ids: ['fast', 'unsafe'] }
  })
  const running = core.runEngine({ agent, pipeline })
  await new Promise(resolve => setImmediate(resolve))
  const prematureCommit = agent.counters['commit:fast'] || 0
  late.resolve({ ...passed('unsafe'), safety_warnings: ['unsafe external write'] })
  const result = await running
  assert.equal(prematureCommit, 0, 'completion must await the wave safety barrier')
  assert.equal(result.status, 'needs_diagnosis')
  assert.equal(agent.counters['commit:fast'], undefined)
  assert.equal(agent.counters['commit:unsafe'], undefined)
  assert.equal(agent.counters['quarantine-wave'], 1)
})

test('safety warning on a hard QA failure cannot open a repair route', async () => {
  const ledger = makeLedgerDouble()
  const agent = makeFakeAgent({
    ...ledgerResponses(ledger),
    'run-policy': policy,
    'load-dag': { nodes: [node('qa'), { ...node('repair'), hard_blocked_by: ['qa'] }], completed: [],
      repair_loops: [{ repair_node_id: 'repair', qa_node_ids: ['qa'], max_attempts: 2 }] },
    qa: { ...passed('qa'), outcome: 'hard_fail', safety_warnings: ['unsafe change'],
      blocking_findings: [{ type: 'cross_node' }] },
    repair: passed('repair'),
    'quarantine-wave': { status: 'quarantined', node_ids: ['qa'] }
  })
  const result = await core.runEngine({ agent, pipeline })
  assert.equal(result.status, 'needs_diagnosis')
  assert.equal(agent.counters.repair, undefined)
  assert.equal(agent.calls.some(c => c.label.startsWith('repair-route:')), false)
  assert.equal(ledger.spentOf('repair', 'qa'), 0, 'a halt charges no repair attempt')
})

test('a safety halt leaves the in-flight authorization unresolved, never settled', async () => {
  // The wave's outputs are quarantined pending independent revalidation, so whether that
  // attempt delivered anything is not this engine's to record. The grant stays open and
  // the next run stops for reconciliation rather than resuming on a guess.
  const ledger = makeLedgerDouble()
  const agent = makeFakeAgent({
    ...ledgerResponses(ledger),
    'run-policy': policy,
    'load-dag': { nodes: [node('qa'), { ...node('repair'), hard_blocked_by: ['qa'] }], completed: [],
      repair_loops: [{ repair_node_id: 'repair', qa_node_ids: ['qa'], max_attempts: 2 }] },
    // First wave: an ordinary QA failure opens the loop and the repair is dispatched.
    qa: { ...passed('qa'), outcome: 'hard_fail', blocking_findings: [{ type: 'cross_node' }] },
    // Second wave: the repair itself raises the safety warning while it is in flight.
    repair: { ...passed('repair'), safety_warnings: ['unsafe external write'] },
    'measure:repair': {},
    'quarantine-wave': { status: 'quarantined', node_ids: ['repair'] },
    'commit-failures': {}
  })
  const result = await core.runEngine({ agent, pipeline })
  assert.equal(result.status, 'needs_diagnosis')
  assert.equal(agent.counters['quarantine-wave'], 1, 'the wave is quarantined')
  assert.equal(ledger.spentOf('repair', 'qa'), 1, 'the dispatched attempt is spent — it was granted')
  assert.deepEqual(ledger.calls.filter(c => c.operation === 'settle'), [],
    'and a quarantined attempt is never settled')
  assert.deepEqual([...ledger.entries.values()].map(e => e.state), ['started'])
})

test('a sibling returning after safety halt cannot start its soft retry', async () => {
  const late = makeDeferred()
  const agent = makeFakeAgent({
    'run-policy': policy,
    'load-dag': { nodes: [node('unsafe'), node('retrying')], completed: [] },
    unsafe: { ...passed('unsafe'), safety_warnings: ['unsafe external write'] },
    retrying: [{ __promise: late.promise }, passed('retrying')],
    'quarantine-wave': { status: 'quarantined', node_ids: ['unsafe', 'retrying'] }
  })
  const running = core.runEngine({ agent, pipeline })
  await new Promise(resolve => setImmediate(resolve))
  late.resolve({ ...passed('retrying'), outcome: 'soft_fail', blocking_findings: [{ type: 'local' }] })
  const result = await running
  assert.equal(result.status, 'needs_diagnosis')
  assert.equal(agent.counters.retrying, 1, 'no new attempt after the safety latch')
  assert.equal(agent.counters['commit:retrying'], undefined)
})

test('ordinary QA failure blocks its dependency chain but independent work continues', async () => {
  const agent = makeFakeAgent({
    'run-policy': policy,
    'load-dag': { nodes: [node('qa'), node('independent'),
      { ...node('dependent'), hard_blocked_by: ['qa'] },
      { ...node('independent-next'), hard_blocked_by: ['independent'] }], completed: [] },
    qa: { ...passed('qa'), outcome: 'hard_fail', blocking_findings: [{ type: 'cross_node' }] },
    independent: passed('independent'), 'independent-next': passed('independent-next')
  })
  const result = await core.runEngine({ agent, pipeline })
  assert.equal(result.status, 'needs_diagnosis')
  assert.equal(agent.counters.qa, 1)
  assert.equal(agent.counters.dependent, undefined)
  assert.equal(agent.counters['independent-next'], 1)
  assert.equal(agent.counters['quarantine-wave'], undefined)
})

test('a missing quarantine receipt is an explicit persistence blocker', async () => {
  const agent = makeFakeAgent({
    'run-policy': policy,
    'load-dag': { nodes: [node('unsafe')], completed: [] },
    unsafe: { ...passed('unsafe'), safety_warnings: ['unsafe write'] }
  })
  const result = await core.runEngine({ agent, pipeline })
  assert.equal(result.status, 'needs_diagnosis')
  assert.ok(result.hardFailures.some(f => f.node_id === 'safety-quarantine'))
  assert.equal(agent.counters['commit:unsafe'], undefined)
})

test('an executor result cannot complete a different node identity', async () => {
  const agent = makeFakeAgent({
    'run-policy': policy,
    'load-dag': { nodes: [node('actual'), { ...node('other'), hard_blocked_by: ['actual'] }], completed: [] },
    actual: passed('other')
  })
  let waves = 0
  const result = await core.runEngine({ agent, pipeline, phase: name => {
    if (name === 'Expand' && ++waves > 4) throw new Error('unexpected repeated dispatch')
  } })
  assert.equal(result.status, 'needs_diagnosis')
  assert.equal(agent.counters['commit:other'], undefined)
  assert.equal(agent.counters.actual, 1)
  assert.ok(result.hardFailures.some(f => f.node_id === 'actual'))
})
