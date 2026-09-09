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
  const dag = { nodes: nodes(), completed: [], repair_loops: [LOOP] }
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
  const dag = { nodes: nodes(), completed: [], repair_loops: [LOOP] }
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
  const dag = { nodes: nodes(), completed: [], repair_loops: [LOOP] }
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
