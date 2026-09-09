// Declared QA repair loops: a failed QA node with a usable current report must
// reach its declared repair node, bounded, without letting an arbitrary failed
// dependency satisfy a successor and without releasing closure before the QA
// rerun passes.
const test = require('node:test')
const assert = require('node:assert/strict')
const core = require('../engine-core.js')
const { pipeline } = require('./harness-doubles.js')
const { makeFakeAgent } = require('./fake-agent.js')

const LOOP = {
  scope: 'orders-export',
  qa_node_ids: ['verify'],
  repair_node_id: 'repair',
  closure_node_ids: ['accept'],
  max_attempts: 2
}

// Every declared QA node must state its recorded attempts, explicit 0 included: an
// absent entry is missing history, not a fresh budget.
const attempts = (spent = {}, loop = LOOP) => (loop.qa_node_ids || []).map(qa => ({
  repair_node_id: loop.repair_node_id, qa_node_id: qa, attempts: spent[qa] || 0
}))

const nodes = () => [
  { node_id: 'implement', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
  { node_id: 'verify', capability: 'x', hard_blocked_by: ['implement'], exit_artifacts: [] },
  { node_id: 'repair', capability: 'x', hard_blocked_by: ['verify'], exit_artifacts: [] },
  { node_id: 'accept', capability: 'x', hard_blocked_by: ['repair'], exit_artifacts: [] }
]

const passed = id => ({ node_id: id, outcome: 'passed', artifacts_written: [`art/${id}`], blocking_findings: [] })
const qaFailed = id => ({
  node_id: id, outcome: 'hard_fail', artifacts_written: [`art/${id}-report.json`],
  blocking_findings: [{ type: 'cross_node', detail: 'export column missing', suspected_root_node: 'implement' }]
})

test('DAG_SCHEMA carries repair_loops', () => {
  assert.ok(core.DAG_SCHEMA.properties.repair_loops, 'repair_loops missing from DAG_SCHEMA')
})

test('loadDagPrompt asks for the declared required_repair_loops', () => {
  const p = core.loadDagPrompt()
  assert.match(p, /unattended-run-readiness-spec\.json/)
  assert.match(p, /required_repair_loops/)
})

test('qaReportUsable: a QA verdict on disk is repairable', () => {
  assert.equal(core.qaReportUsable(qaFailed('verify')), true)
})

test('qaReportUsable: a QA node that published nothing is not repairable', () => {
  assert.equal(core.qaReportUsable({
    node_id: 'verify', outcome: 'hard_fail', artifacts_written: [],
    blocking_findings: [{ type: 'cross_node' }]
  }), false)
})

test('qaReportUsable: infrastructure failures carry no QA verdict', () => {
  for (const type of ['invalid_artifact_gate', 'deadlock', 'safety_warning', 'needs_iteration', 'exhausted_retries']) {
    assert.equal(core.qaReportUsable({
      node_id: 'verify', outcome: 'hard_fail', artifacts_written: ['art/verify-report.json'],
      blocking_findings: [{ type }]
    }), false, `${type} must not open a repair loop`)
  }
})

test('qaReportUsable: a passing node is never a repair trigger', () => {
  assert.equal(core.qaReportUsable(passed('verify')), false)
})

const ctx = (open = []) => ({ loops: [LOOP], open: new Map(open) })

test('computeReady: the declared repair node is ready on an open failed QA', () => {
  const ready = core.computeReady(nodes(), new Set(['implement']), ctx([['verify', LOOP]])).map(n => n.node_id)
  assert.deepEqual(ready, ['repair'])
})

test('computeReady: an undeclared successor never runs on a failed dependency', () => {
  const extra = nodes().concat([{ node_id: 'ship', capability: 'x', hard_blocked_by: ['verify'], exit_artifacts: [] }])
  const ready = core.computeReady(extra, new Set(['implement']), ctx([['verify', LOOP]])).map(n => n.node_id)
  assert.ok(!ready.includes('ship'), 'a failed dependency must not satisfy an undeclared successor')
})

test('computeReady: declared closure waits for the QA rerun, not the repair', () => {
  const ready = core.computeReady(nodes(), new Set(['implement', 'repair']), ctx([['verify', LOOP]])).map(n => n.node_id)
  assert.ok(!ready.includes('accept'), 'closure must not start while its QA node is still failed')
})

test('computeReady: closing the loop re-queues the QA node before closure', () => {
  const ready = core.computeReady(nodes(), new Set(['implement', 'repair']), ctx()).map(n => n.node_id)
  assert.deepEqual(ready, ['verify'], 'closure stays blocked until the QA node itself completes')
})

test('computeReady: closure is released only once the QA node completes', () => {
  const ready = core.computeReady(nodes(), new Set(['implement', 'repair', 'verify']), ctx()).map(n => n.node_id)
  assert.deepEqual(ready, ['accept'])
})

test('runEngine: failed QA reaches repair, reruns QA, then releases closure', async () => {
  const dag = { nodes: nodes(), completed: [], repair_loops: [LOOP], repair_attempts: attempts() }
  const agent = makeFakeAgent({
    'load-dag': dag,
    implement: passed('implement'),
    verify: [qaFailed('verify'), passed('verify')],
    repair: passed('repair'),
    accept: passed('accept'),
    'commit:implement': {}, 'commit:verify': {}, 'commit:repair': {}, 'commit:accept': {}
  })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'complete')
  assert.equal(agent.counters.repair, 1, 'repair node must be dispatched')
  assert.equal(agent.counters.verify, 2, 'QA must rerun after repair')
  assert.equal(agent.counters['commit:verify'], 1, 'only the passing QA run commits')
  const order = agent.calls.filter(c => ['verify', 'repair', 'accept'].includes(c.label)).map(c => c.label)
  assert.deepEqual(order, ['verify', 'repair', 'verify', 'accept'])
})

test('runEngine: a QA failure with no usable report is not routed to repair', async () => {
  const dag = { nodes: nodes(), completed: [], repair_loops: [LOOP], repair_attempts: attempts() }
  const agent = makeFakeAgent({
    'load-dag': dag,
    implement: passed('implement'),
    verify: { node_id: 'verify', outcome: 'hard_fail', artifacts_written: [], blocking_findings: [{ type: 'cross_node' }] },
    'commit:implement': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(agent.counters.repair, undefined)
})

test('runEngine: an undeclared QA failure still stops the run', async () => {
  const dag = { nodes: nodes(), completed: [], repair_loops: [] }
  const agent = makeFakeAgent({
    'load-dag': dag,
    implement: passed('implement'),
    verify: qaFailed('verify'),
    'commit:implement': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(agent.counters.repair, undefined)
})

test('runEngine: repair attempts are bounded by the declared budget', async () => {
  const dag = { nodes: nodes(), completed: [], repair_loops: [LOOP], repair_attempts: attempts() }
  const agent = makeFakeAgent({
    'load-dag': dag,
    implement: passed('implement'),
    verify: qaFailed('verify'),
    repair: passed('repair'),
    'commit:implement': {}, 'commit:repair': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(agent.counters.repair, LOOP.max_attempts, 'repair must stop at max_attempts')
  assert.equal(agent.counters.accept, undefined, 'closure never runs on an unrepaired QA failure')
  assert.equal(agent.counters['commit:verify'], undefined, 'a failed QA node is never committed')
})

// --- a routed repair never swallows another node's terminal policy signal ---

// Wave cap: an engine that never settles must fail loudly instead of spinning.
// phase() is called outside the pipeline's error handling, so a throw here escapes.
const cappedPhase = (max = 40) => {
  let calls = 0
  return () => { if (++calls > max) throw new Error('engine did not settle: wave cap exceeded') }
}

const withIter = () => nodes().concat([
  { node_id: 'iter', capability: 'x', hard_blocked_by: ['implement'], exit_artifacts: [] }
])

const runPolicy = onNeedsIteration => ({
  status: 'run_policy_ready',
  policy: { on_repeated_failure: 'halt', on_safety_warning: 'continue', on_needs_iteration: onNeedsIteration }
})

const needsIteration = id => ({
  node_id: id, outcome: 'passed', artifacts_written: [`art/${id}`],
  blocking_findings: [], acceptance_verdict: 'needs_iteration'
})

test('runEngine: an accepted-with-gaps node in a repair wave is not reported complete', async () => {
  const dag = { nodes: withIter(), completed: [], repair_loops: [LOOP], repair_attempts: attempts() }
  const agent = makeFakeAgent({
    'run-policy': runPolicy('accept'),
    'load-dag': dag,
    implement: passed('implement'),
    verify: [qaFailed('verify'), passed('verify')],
    repair: passed('repair'),
    accept: passed('accept'),
    // A re-run of an accepted node may report anything; it must never be re-run.
    iter: [needsIteration('iter'), passed('iter')],
    'policy:on_needs_iteration': { action: 'accept' },
    'iteration-report:iter': {},
    'commit:implement': {}, 'commit:verify': {}, 'commit:repair': {}, 'commit:accept': {}, 'commit:iter': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'accepted_with_gaps', 'the recorded accept decision must survive the repair route')
  assert.equal(res.verified, false)
  assert.equal(agent.counters.iter, 1, 'an accepted node is never re-run into a passing verdict')
})

test('runEngine: a stopped iteration repair in a repair wave is not reported complete', async () => {
  const dag = { nodes: withIter(), completed: [], repair_loops: [LOOP], repair_attempts: attempts() }
  const agent = makeFakeAgent({
    'run-policy': runPolicy('auto_fix_once'),
    'load-dag': dag,
    implement: passed('implement'),
    verify: [qaFailed('verify'), passed('verify')],
    repair: passed('repair'),
    accept: passed('accept'),
    iter: [needsIteration('iter'), passed('iter')],
    'policy:on_needs_iteration': { action: 'auto_fix_once' },
    'iteration-report:iter': {}, 'iteration-repair:iter': {},
    'commit:implement': {}, 'commit:verify': {}, 'commit:repair': {}, 'commit:accept': {}, 'commit:iter': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'iteration_repair_stopped', 'a one-shot iteration repair must still stop the run')
})

// --- the declared budget is per QA node, and it survives a restart ---

test('repairBudget: an omitted budget falls back to the documented default', () => {
  assert.equal(core.repairBudget({ repair_node_id: 'repair' }), 3)
})

test('repairBudget: an explicitly invalid budget fails closed, never to a default', () => {
  for (const max_attempts of [0, -1, 2.5, '2', null, true, {}]) {
    assert.equal(core.repairBudget({ repair_node_id: 'repair', max_attempts }), null,
      `max_attempts ${JSON.stringify(max_attempts)} must not silently become a default`)
  }
})

test('runEngine: an explicitly invalid budget routes nothing and stops the run', async () => {
  const badLoop = { ...LOOP, max_attempts: 0 }
  const dag = { nodes: nodes(), completed: [], repair_loops: [badLoop], repair_attempts: attempts({}, badLoop) }
  const agent = makeFakeAgent({
    'load-dag': dag,
    implement: passed('implement'),
    verify: qaFailed('verify'),
    'commit:implement': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(agent.counters.repair, undefined, 'an unbounded loop must never dispatch a repair')
})

test('runEngine: recorded prior attempts are not reset by a restart', async () => {
  const dag = {
    nodes: nodes(), completed: ['implement'], repair_loops: [LOOP],
    repair_attempts: [{ repair_node_id: 'repair', qa_node_id: 'verify', attempts: LOOP.max_attempts }]
  }
  const agent = makeFakeAgent({
    'load-dag': dag,
    verify: qaFailed('verify'),
    repair: passed('repair'),
    'commit:repair': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(agent.counters.repair, undefined, 'a spent budget must stay spent across a restart')
})

test('runEngine: a resumed run spends only the attempts it has left', async () => {
  const dag = {
    nodes: nodes(), completed: ['implement'], repair_loops: [LOOP],
    repair_attempts: [{ repair_node_id: 'repair', qa_node_id: 'verify', attempts: 1 }]
  }
  const agent = makeFakeAgent({
    'load-dag': dag,
    verify: qaFailed('verify'),
    repair: passed('repair'),
    'commit:repair': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(agent.counters.repair, 1, 'one attempt was already recorded; only one remains')
})

test('runEngine: an unreadable attempt history stops the run instead of restarting the budget', async () => {
  const dag = {
    nodes: nodes(), completed: ['implement'], repair_loops: [LOOP],
    repair_attempts: [{ repair_node_id: 'repair', qa_node_id: 'verify', attempts: 'two' }]
  }
  const agent = makeFakeAgent({
    'load-dag': dag,
    verify: qaFailed('verify'),
    repair: passed('repair'),
    'commit:repair': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(res.hardFailures[0].blocking_findings[0].type, 'invalid_repair_attempt_history')
  assert.equal(agent.counters.verify, undefined, 'no node runs on unreadable repair state')
})

test('loadDagPrompt asks for the recorded repair attempts', () => {
  assert.match(core.loadDagPrompt(), /repair_attempts/)
})

test('runEngine: one repair node serving two QA nodes budgets each of them separately', async () => {
  const sharedLoop = {
    scope: 'orders-export', qa_node_ids: ['verifyA', 'verifyB'],
    repair_node_id: 'repair', closure_node_ids: ['accept'], max_attempts: 1
  }
  const sharedNodes = [
    { node_id: 'implement', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'verifyA', capability: 'x', hard_blocked_by: ['implement'], exit_artifacts: [] },
    { node_id: 'verifyB', capability: 'x', hard_blocked_by: ['implement'], exit_artifacts: [] },
    { node_id: 'repair', capability: 'x', hard_blocked_by: ['verifyA', 'verifyB'], exit_artifacts: [] },
    { node_id: 'accept', capability: 'x', hard_blocked_by: ['repair'], exit_artifacts: [] }
  ]
  const dag = { nodes: sharedNodes, completed: [], repair_loops: [sharedLoop], repair_attempts: attempts({}, sharedLoop) }
  const agent = makeFakeAgent({
    'load-dag': dag,
    implement: passed('implement'),
    verifyA: [qaFailed('verifyA'), passed('verifyA')],
    verifyB: [qaFailed('verifyB'), passed('verifyB')],
    repair: passed('repair'),
    accept: passed('accept'),
    'commit:implement': {}, 'commit:verifyA': {}, 'commit:verifyB': {},
    'commit:repair': {}, 'commit:accept': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'complete')
  assert.equal(agent.counters.verifyA, 2, 'each QA node keeps its own attempt')
  assert.equal(agent.counters.verifyB, 2, 'a sibling QA node must not consume the budget')
})

test('runEngine: a declared loop with no recorded attempt history stops the run', async () => {
  const dag = { nodes: nodes(), completed: [], repair_loops: [LOOP] }
  const agent = makeFakeAgent({ 'load-dag': dag, implement: passed('implement'), 'commit:implement': {} })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(res.hardFailures[0].blocking_findings[0].type, 'invalid_repair_attempt_history')
  assert.equal(agent.counters.implement, undefined, 'no node runs on missing repair state')
})

test('runEngine: a QA node missing from the recorded history stops the run', async () => {
  const sharedLoop = {
    scope: 'orders-export', qa_node_ids: ['verifyA', 'verifyB'],
    repair_node_id: 'repair', closure_node_ids: [], max_attempts: 1
  }
  const dag = {
    nodes: nodes(), completed: [], repair_loops: [sharedLoop],
    repair_attempts: [{ repair_node_id: 'repair', qa_node_id: 'verifyA', attempts: 1 }]
  }
  const agent = makeFakeAgent({ 'load-dag': dag })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.match(res.hardFailures[0].blocking_findings[0].detail, /verifyB/)
})
