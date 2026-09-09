// Declared QA repair loops: a failed QA node with a usable current report must
// reach its declared repair node, bounded, without letting an arbitrary failed
// dependency satisfy a successor and without releasing closure before the QA
// rerun passes.
const test = require('node:test')
const assert = require('node:assert/strict')
const core = require('../engine-core.js')
const { pipeline } = require('./harness-doubles.js')
const { makeFakeAgent } = require('./fake-agent.js')
const { makeLedgerDouble, ledgerResponses } = require('./ledger-double.js')

const LOOP = {
  scope: 'orders-export',
  qa_node_ids: ['verify'],
  repair_node_id: 'repair',
  closure_node_ids: ['accept'],
  max_attempts: 2
}

// The spent budget is no longer summarized out of workflow.json by the load-dag agent:
// it is read from the canonical repair-authorization ledger. These tests answer the
// engine's ledger prompts from `ledger-double.js` — a documented mock of the helper's
// decisions. `declared-loop.test.js` drives the REAL `repair_authorization.py` through
// the same prompts, and that test is the authority if the two ever disagree.
const ledgerFor = (spent = {}, loop = LOOP) => makeLedgerDouble({
  spent: Object.fromEntries((loop.qa_node_ids || [])
    .map(qa => [`${loop.repair_node_id}::${qa}`, spent[qa] || 0]).filter(([, n]) => n > 0))
})

// A fake agent that answers every ledger label from `ledger` and the rest from the test.
const agentWith = (ledger, responses) => makeFakeAgent({ ...ledgerResponses(ledger), ...responses })

// The authorize/start labels a dispatch of `repairNodeId` produces, in order.
const ledgerLabels = agent => agent.calls.map(c => c.label)
  .filter(l => /^repair-(authorize|start|settle):/.test(l))

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
  const agent = agentWith(ledgerFor(), {
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
  const agent = agentWith(ledgerFor(), {
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
  const agent = agentWith(ledgerFor(), {
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
  const agent = agentWith(ledgerFor(), {
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
  const dag = { nodes: withIter(), completed: [], repair_loops: [LOOP] }
  const agent = agentWith(ledgerFor(), {
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
  const dag = { nodes: withIter(), completed: [], repair_loops: [LOOP] }
  const agent = agentWith(ledgerFor(), {
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
  const dag = { nodes: nodes(), completed: [], repair_loops: [badLoop] }
  const agent = agentWith(ledgerFor(), {
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
  const dag = { nodes: nodes(), completed: ['implement'], repair_loops: [LOOP] }
  const agent = agentWith(ledgerFor({ verify: LOOP.max_attempts }), {
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
  const dag = { nodes: nodes(), completed: ['implement'], repair_loops: [LOOP] }
  const ledger = ledgerFor({ verify: 1 })
  const agent = agentWith(ledger, {
    'load-dag': dag,
    verify: qaFailed('verify'),
    repair: passed('repair'),
    'commit:repair': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(agent.counters.repair, 1, 'one attempt was already recorded; only one remains')
  assert.equal(ledger.spentOf('repair', 'verify'), 2, 'and the ledger records the second, never a third')
})

test('runEngine: an unreadable ledger obligation stops the run instead of restarting the budget', async () => {
  // Consumption answers, but one obligation's spend cannot be read. The remaining budget
  // is then unknown, and a guess would hand out an attempt whose work may already exist.
  const base = ledgerFor()
  const corrupt = { fromPrompt: prompt => {
    const verdict = base.fromPrompt(prompt)
    if (verdict.obligations) {
      verdict.obligations = [{ repair_node_id: 'repair', qa_node_id: 'verify', spent: 'two' }]
    }
    return verdict
  } }
  const agent = agentWith(corrupt, {
    'load-dag': { nodes: nodes(), completed: ['implement'], repair_loops: [LOOP] },
    verify: qaFailed('verify'),
    repair: passed('repair'),
    'commit:repair': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(res.hardFailures[0].blocking_findings[0].type, 'invalid_repair_authorization')
  assert.match(res.hardFailures[0].blocking_findings[0].detail, /unreadable ledger obligation/)
  assert.equal(agent.counters.verify, undefined, 'no node runs on unreadable repair state')
})

test('loadDagPrompt no longer claims any authority over the spent budget', () => {
  const p = core.loadDagPrompt()
  assert.doesNotMatch(p, /repair_attempts/, 'the load-dag agent no longer reports attempts')
  assert.doesNotMatch(p, /repair_routes/, 'and no longer counts the legacy route ledger')
  assert.match(p, /Do NOT report repair budgets here/)
})

test('DAG_SCHEMA no longer accepts an agent-inferred attempt history', () => {
  assert.equal(core.DAG_SCHEMA.properties.repair_attempts, undefined)
})

// --- the attempt is charged through the canonical repair-authorization ledger ---

test('authorizationPrompt runs the canonical helper and forbids inventing a verdict', () => {
  const p = core.authorizationPrompt({ operation: 'consumption' })
  assert.match(p, /repair_authorization\.py/)
  assert.match(p, /repair-authorizations\.json/)
  assert.match(p, /exactly as the/)
  assert.match(p, /Do NOT invent/)
  assert.match(p, /edit the ledger file by hand/)
  assert.match(p, /\{"operation":"consumption"\}/, 'the request travels in the command itself')
})

test('authorizationPrompt shell-quotes a request that contains a quote', () => {
  const p = core.authorizationPrompt({ operation: 'authorize', repair_node_id: "it's" })
  assert.match(p, /'\\''/, 'a single quote is escaped for the shell, never left to split the command')
})

test('authorizationId is durable across a restart and unique per attempt', () => {
  const first = core.authorizationId('run-1', 'repair', { verify: 0 })
  assert.equal(first, core.authorizationId('run-1', 'repair', { verify: 0 }),
    'the same dispatch recomputes the same id, so the helper sees a replay, not a new charge')
  assert.notEqual(first, core.authorizationId('run-1', 'repair', { verify: 1 }),
    'the next attempt has a different prior spend, so it is a different dispatch')
  assert.notEqual(first, core.authorizationId('run-2', 'repair', { verify: 0 }))
  assert.equal(core.authorizationId('r', 'x', { b: 0, a: 1 }), core.authorizationId('r', 'x', { a: 1, b: 0 }),
    'obligation order is not part of the identity')
})

test('ledgerReceiptError refuses a forged, mismatched or missing receipt', () => {
  const ok = { status: 'authorized', authorization_id: 'a1', repair_node_id: 'repair', execution_allowed: false }
  const expect = { status: 'authorized', operation: 'authorize', authorization_id: 'a1',
    repair_node_id: 'repair', execution_allowed: false }
  assert.equal(core.ledgerReceiptError(ok, expect), null)
  assert.match(core.ledgerReceiptError(null, expect), /no verdict/)
  assert.match(core.ledgerReceiptError({ ...ok, authorization_id: 'other' }, expect), /names authorization/)
  assert.match(core.ledgerReceiptError({ ...ok, repair_node_id: 'elsewhere' }, expect), /names repair node/)
  assert.match(core.ledgerReceiptError({ ...ok, execution_allowed: true }, expect), /execution_allowed/)
  assert.match(core.ledgerReceiptError({ status: 'budget_exhausted' }, expect), /budget_exhausted/)
  assert.match(core.ledgerReceiptError({ status: 'blocked', untrusted: 'unresolved_authorization' }, expect),
    /unresolved_authorization/)
})

test('runEngine: the attempt is charged at the dispatch, after the route and before the work', async () => {
  const dag = { nodes: nodes(), completed: [], repair_loops: [LOOP] }
  const agent = agentWith(ledgerFor(), {
    'load-dag': dag,
    implement: passed('implement'),
    verify: [qaFailed('verify'), passed('verify')],
    repair: passed('repair'),
    accept: passed('accept'),
    'commit:implement': {}, 'commit:verify': {}, 'commit:repair': {}, 'commit:accept': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'complete')
  const labels = agent.calls.map(c => c.label)
  assert.deepEqual(ledgerLabels(agent),
    ['repair-authorize:repair', 'repair-start:repair', 'repair-settle:repair'],
    'one dispatch: charge, then the launch claim, then the settlement of what was observed')
  assert.ok(labels.indexOf('repair-route:verify:1') < labels.indexOf('repair-authorize:repair'),
    'the route opens first')
  assert.ok(labels.indexOf('repair-authorize:repair') < labels.indexOf('repair-start:repair'),
    'the charge is durable before the launch is claimed')
  assert.ok(labels.indexOf('repair-start:repair') < labels.indexOf('repair'),
    'and both are durable before the repair node runs')
  assert.ok(labels.indexOf('repair') < labels.indexOf('repair-settle:repair'),
    'the settlement records an execution that already happened')
})

test('runEngine: a repair that never delivers spends the declared budget, then stops', async () => {
  // The failure mode delivery-accounting could not bound: every attempt runs, produces
  // nothing measurable, and would cost nothing if the budget only charged for success.
  const dag = { nodes: nodes(), completed: [], repair_loops: [LOOP] }
  const ledger = ledgerFor()
  const agent = agentWith(ledger, {
    'load-dag': dag,
    implement: passed('implement'),
    verify: qaFailed('verify'),
    repair: passed('repair'),
    'verify:repair': { node_id: 'repair', status: 'repair', blocking_findings: [{ type: 'code_gaps' }] },
    'measure:repair': {},
    'commit:implement': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(res.hardFailures[0].node_id, 'repair')
  assert.equal(res.hardFailures[0].blocking_findings[0].type, 'unmeasured_repair_delivery')
  assert.equal(agent.counters.repair, LOOP.max_attempts, 'each non-delivery spent one declared attempt')
  assert.equal(agent.counters.verify, 1, 'and no non-delivery released the QA rerun')
  assert.equal(agent.counters.accept, undefined, 'closure never runs on an unrepaired QA failure')
  assert.equal(ledger.spentOf('repair', 'verify'), LOOP.max_attempts,
    'the canonical ledger charged one attempt per dispatch, delivery or not')
  assert.equal(ledgerLabels(agent).filter(l => l === 'repair-authorize:repair').length, LOOP.max_attempts)
})

test('runEngine: a structural failure on the repair node stops the run without a retry', async () => {
  // A recorded safety halt or a broken gate is not an attempt that fell short: dispatching
  // it again cannot make it truer, so the loop's budget does not apply to it.
  const dag = { nodes: nodes(), completed: [], repair_loops: [LOOP] }
  const agent = agentWith(ledgerFor(), {
    'load-dag': dag,
    implement: passed('implement'),
    verify: qaFailed('verify'),
    repair: passed('repair'),
    'verify:repair': { node_id: 'repair', status: 'hard_fail',
      blocking_findings: [{ type: 'invalid_readiness_gate', detail: 'readiness gate unreadable' }] },
    'measure:repair': {},
    'commit:implement': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(res.hardFailures[0].blocking_findings[0].type, 'invalid_readiness_gate')
  assert.equal(agent.counters.repair, 1, 'a structural blocker is never re-dispatched')
})

test('runEngine: an interrupted dispatch keeps its charge across a restart', async () => {
  // The restart reads a charged attempt whose repair never finished. It must resume on
  // the remaining attempt, not re-grant the interrupted one.
  const dag = { nodes: nodes(), completed: ['implement'], repair_loops: [LOOP] }
  const ledger = ledgerFor({ verify: 1 })
  const agent = agentWith(ledger, {
    'load-dag': dag,
    verify: qaFailed('verify'),
    repair: passed('repair'),
    'commit:repair': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(ledger.spentOf('repair', 'verify'), 2,
    'the resumed run charges attempt 2, never attempt 1 again')
  assert.deepEqual(ledgerLabels(agent).filter(l => l.startsWith('repair-authorize:')),
    ['repair-authorize:repair'], 'and it authorizes exactly one further dispatch')
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
  const dag = { nodes: sharedNodes, completed: [], repair_loops: [sharedLoop] }
  const ledger = ledgerFor({}, sharedLoop)
  const agent = agentWith(ledger, {
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
  assert.equal(ledger.spentOf('repair', 'verifyA'), 1)
  assert.equal(ledger.spentOf('repair', 'verifyB'), 1)
  assert.deepEqual(ledgerLabels(agent).filter(l => l.startsWith('repair-authorize:')),
    ['repair-authorize:repair'],
    'one dispatch answering two QA nodes is ONE atomic grant charging one attempt of each')
})

test('runEngine: a ledger that cannot be read at all stops the run before any node', async () => {
  // The replacement for the old "no recorded attempt history" rule. Absence of records is
  // still never a fresh budget — but which absence matters has changed. An unreadable or
  // foreign ledger is untrusted state and stops the run; only `missing_ledger` may be
  // initialized, and only the helper decides that.
  const dag = { nodes: nodes(), completed: [], repair_loops: [LOOP] }
  const agent = agentWith({ fromPrompt: () => ({ status: 'blocked', untrusted: 'unreadable_ledger',
    reason: 'Repair-authorization ledger is unreadable' }) },
    { 'load-dag': dag, implement: passed('implement'), 'commit:implement': {} })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(res.hardFailures[0].blocking_findings[0].type, 'invalid_repair_authorization')
  assert.match(res.hardFailures[0].blocking_findings[0].detail, /unreadable_ledger/)
  assert.equal(agent.counters.implement, undefined, 'no node runs on untrusted repair state')
  assert.equal(agent.counters['ledger:initialize'], undefined,
    'and a ledger that exists but cannot be read is never re-initialized')
})

test('runEngine: an unresolved authorization at startup blocks instead of resuming', async () => {
  // A grant that never reached an outcome leaves it unknown whether that attempt ran.
  // Resuming would either replay uncertain work or spend a budget twice, so the run stops
  // for reconciliation and does neither (ADR 0006).
  const dag = { nodes: nodes(), completed: [], repair_loops: [LOOP] }
  const agent = agentWith(makeLedgerDouble({
    unresolved: [{ authorization_id: 'grant-7', state: 'started',
      repair_node_id: 'repair', obligations: ['verify'] }]
  }), { 'load-dag': dag, implement: passed('implement'), 'commit:implement': {} })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(res.hardFailures[0].blocking_findings[0].type, 'invalid_repair_authorization')
  assert.match(res.hardFailures[0].blocking_findings[0].detail, /grant-7/)
  assert.match(res.hardFailures[0].blocking_findings[0].detail, /neither replays nor refunds/)
  assert.equal(agent.counters.implement, undefined, 'no node runs while an attempt is unaccounted for')
})

test('runEngine: only a missing ledger is initialized, and the helper proves it', async () => {
  const dag = { nodes: nodes(), completed: [], repair_loops: [LOOP] }
  const ledger = makeLedgerDouble({ missing: true })
  const agent = agentWith(ledger, {
    'load-dag': dag, implement: passed('implement'),
    verify: passed('verify'), repair: passed('repair'), accept: passed('accept'),
    'commit:implement': {}, 'commit:verify': {}, 'commit:repair': {}, 'commit:accept': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'complete')
  const ops = ledger.calls.map(c => c.operation)
  assert.deepEqual(ops.slice(0, 3), ['consumption', 'initialize', 'consumption'],
    'consumption first; initialize only after the helper reported missing_ledger; then re-read')
  assert.equal(ops.filter(o => o === 'initialize').length, 1, 'and exactly once')
  const init = ledger.calls.find(c => c.operation === 'initialize')
  assert.match(init.run_id, /^run-[0-9a-f]{8}$/, 'a stable run identity, not a clock or a random value')
})

test('shared repair never charges an exhausted sibling while another still has budget', async () => {
  const loop = { qa_node_ids: ['qaA', 'qaB'], repair_node_id: 'repair', max_attempts: 2 }
  const dag = { nodes: [
    { node_id: 'qaA', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'qaB', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'repair', capability: 'x', hard_blocked_by: ['qaA', 'qaB'], exit_artifacts: [] }
  ], completed: [], repair_loops: [loop] }
  const ledger = ledgerFor({ qaA: 1 }, loop)
  const agent = agentWith(ledger, { 'load-dag': dag, qaA: qaFailed('qaA'), qaB: qaFailed('qaB'),
    repair: passed('repair'), 'measure:repair': {},
    'verify:repair': { node_id: 'repair', status: 'repair', blocking_findings: [{ type: 'code_gaps' }] } })
  const result = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(result.status, 'needs_diagnosis')
  assert.equal(ledger.spentOf('repair', 'qaA'), 2, 'qaA spent its last attempt and no more')
  assert.equal(ledger.spentOf('repair', 'qaB'), 2, 'qaB kept its own, untouched by its sibling')
  for (const request of ledger.calls.filter(c => c.operation === 'authorize')) {
    assert.ok(!(request.obligations.includes('qaA') && (ledger.calls.filter(c =>
      c.operation === 'authorize' && c.obligations.includes('qaA')).length > 2)),
      'an exhausted sibling is never named in a further grant')
  }
})

test('overlapping QA and repair roles cannot absorb another terminal failure', async () => {
  const first = { qa_node_ids: ['qa1'], repair_node_id: 'R', max_attempts: 2 }
  const second = { qa_node_ids: ['R'], repair_node_id: 'R2', max_attempts: 2 }
  const node = (id, deps = []) => ({ node_id: id, capability: 'x', hard_blocked_by: deps, exit_artifacts: [] })
  const agent = agentWith(makeLedgerDouble(), {
    'load-dag': { nodes: [node('qa1'), node('trigger'), node('R', ['qa1']),
      node('other', ['trigger']), node('R2', ['R'])], completed: [],
      repair_loops: [first, second] },
    qa1: qaFailed('qa1'), trigger: passed('trigger'), R: qaFailed('R'), R2: passed('R2'),
    other: { ...qaFailed('other'), artifacts_written: [], blocking_findings: [{ type: 'invalid_artifact_gate' }] }
  })
  const result = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(result.status, 'needs_diagnosis')
  assert.equal(agent.counters.other, 1)
  assert.equal(agent.counters.R, 1)
  assert.equal(agent.counters.R2, undefined)
  assert.ok(result.hardFailures.some(f => f.node_id === 'other'))
})

test('an obligation the trusted ledger does not list has provably spent nothing', async () => {
  // This replaces the old "every QA node must state its attempts" rule, and why it can be
  // replaced is the whole point of the ledger. That rule existed because an agent
  // summarizing workflow.json could silently omit a QA node, and an omission was
  // indistinguishable from a zero. The ledger's origin is verified when it is created —
  // `initialize` refuses a workflow that already shows execution — so an obligation with
  // no entry really has no history. Absence is trustworthy only because the document is.
  const sharedLoop = {
    scope: 'orders-export', qa_node_ids: ['verifyA', 'verifyB'],
    repair_node_id: 'repair', closure_node_ids: [], max_attempts: 1
  }
  const sharedNodes = [
    { node_id: 'verifyA', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'verifyB', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
    { node_id: 'repair', capability: 'x', hard_blocked_by: ['verifyA', 'verifyB'], exit_artifacts: [] }
  ]
  // verifyA has spent its only attempt; verifyB is simply absent from the ledger.
  const ledger = makeLedgerDouble({ spent: { 'repair::verifyA': 1 } })
  const agent = agentWith(ledger, {
    'load-dag': { nodes: sharedNodes, completed: [], repair_loops: [sharedLoop] },
    verifyA: qaFailed('verifyA'), verifyB: qaFailed('verifyB'),
    repair: passed('repair'), 'measure:repair': {}, 'commit-failures': {},
    'verify:repair': { node_id: 'repair', status: 'repair', blocking_findings: [{ type: 'code_gaps' }] }
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(ledger.spentOf('repair', 'verifyA'), 1, 'the exhausted sibling is not charged again')
  assert.equal(ledger.spentOf('repair', 'verifyB'), 1, 'and the unlisted one gets its declared attempt')
  assert.deepEqual(ledger.calls.filter(c => c.operation === 'authorize').map(g => g.obligations),
    [['verifyB']], 'the grant names only the obligation that still had budget')
})
