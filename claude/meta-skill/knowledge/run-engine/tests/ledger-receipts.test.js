// Receipts are checked, never believed, and an unknown execution is never settled.
//
// The engine has no filesystem: its only evidence that a charge or a launch claim is
// durable is the verdict an agent hands back from the canonical helper. So a verdict that
// names a different dispatch, omits its identity, or answers a question nobody asked has
// to be refused exactly like a refusal — otherwise "the ledger said so" means only "the
// agent said so". These tests forge verdicts on purpose.
const test = require('node:test')
const assert = require('node:assert/strict')
const core = require('../engine-core.js')
const { pipeline } = require('./harness-doubles.js')
const { makeFakeAgent } = require('./fake-agent.js')
const { makeLedgerDouble, ledgerResponses, LEDGER_LABEL } = require('./ledger-double.js')

const LOOP = { scope: 's', qa_node_ids: ['verify'], repair_node_id: 'repair',
  closure_node_ids: ['accept'], max_attempts: 2 }

const nodes = () => [
  { node_id: 'implement', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
  { node_id: 'verify', capability: 'x', hard_blocked_by: ['implement'], exit_artifacts: [] },
  { node_id: 'repair', capability: 'x', hard_blocked_by: ['verify'], exit_artifacts: [] },
  { node_id: 'accept', capability: 'x', hard_blocked_by: ['repair'], exit_artifacts: [] }
]
const passed = id => ({ node_id: id, outcome: 'passed', artifacts_written: [`art/${id}`], blocking_findings: [] })
const qaFailed = id => ({ node_id: id, outcome: 'hard_fail', artifacts_written: [`art/${id}-report.json`],
  blocking_findings: [{ type: 'cross_node', detail: 'gap', suspected_root_node: 'implement' }] })
const cappedPhase = (max = 40) => { let n = 0; return () => { if (++n > max) throw new Error('runaway') } }

// A ledger double whose verdicts are tampered with on the way back to the engine.
function forging(ledger, tamper) {
  return { fromPrompt: prompt => tamper(ledger.fromPrompt(prompt), prompt) }
}

async function runWithLedger(ledger, extra = {}) {
  const agent = makeFakeAgent({
    ...ledgerResponses(ledger),
    'load-dag': { nodes: nodes(), completed: [], repair_loops: [LOOP] },
    implement: passed('implement'),
    verify: qaFailed('verify'),
    repair: passed('repair'),
    'measure:repair': {}, 'commit:implement': {}, 'commit-failures': {},
    ...extra
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  return { res, agent }
}

test('a grant receipt naming another dispatch stops the run before the repair executes', async () => {
  const ledger = makeLedgerDouble()
  const { res, agent } = await runWithLedger(forging(ledger, verdict =>
    verdict.status === 'authorized' ? { ...verdict, authorization_id: 'somebody-elses-grant' } : verdict))
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(res.hardFailures[0].blocking_findings[0].type, 'invalid_repair_authorization')
  assert.match(res.hardFailures[0].blocking_findings[0].detail, /names authorization/)
  assert.equal(agent.counters.repair, undefined, 'nothing executes on a receipt for another dispatch')
})

test('a grant receipt naming another repair node is refused', async () => {
  const ledger = makeLedgerDouble()
  const { res, agent } = await runWithLedger(forging(ledger, verdict =>
    verdict.status === 'authorized' ? { ...verdict, repair_node_id: 'a-different-node' } : verdict))
  assert.equal(res.status, 'needs_diagnosis')
  assert.match(res.hardFailures[0].blocking_findings[0].detail, /names repair node/)
  assert.equal(agent.counters.repair, undefined)
})

test('a grant that claims execution_allowed is refused: authorize never permits a run', async () => {
  const ledger = makeLedgerDouble()
  const { res, agent } = await runWithLedger(forging(ledger, verdict =>
    verdict.status === 'authorized' ? { ...verdict, execution_allowed: true } : verdict))
  assert.equal(res.status, 'needs_diagnosis')
  assert.match(res.hardFailures[0].blocking_findings[0].detail, /execution_allowed/)
  assert.equal(agent.counters.repair, undefined, 'a charge is not a launch, however the receipt is worded')
})

test('a charge the receipt does not account for is refused', async () => {
  // The receipt says "authorized" but reports a spend that is not this attempt. Trusting
  // the engine's own arithmetic over the ledger's is how a budget silently drifts.
  const ledger = makeLedgerDouble()
  const { res, agent } = await runWithLedger(forging(ledger, verdict =>
    verdict.status === 'authorized' ? { ...verdict, charged: { verify: 7 } } : verdict))
  assert.equal(res.status, 'needs_diagnosis')
  assert.match(res.hardFailures[0].blocking_findings[0].detail, /charged 7 to verify, expected 1/)
  assert.equal(agent.counters.repair, undefined)
})

test('a missing charge field is refused rather than read as one attempt', async () => {
  const ledger = makeLedgerDouble()
  const { res } = await runWithLedger(forging(ledger, verdict =>
    verdict.status === 'authorized' ? { ...verdict, charged: {} } : verdict))
  assert.equal(res.status, 'needs_diagnosis')
  assert.match(res.hardFailures[0].blocking_findings[0].detail, /charged undefined to verify/)
})

test('a launch claim that was not granted stops the run', async () => {
  const ledger = makeLedgerDouble()
  const { res, agent } = await runWithLedger(forging(ledger, verdict =>
    verdict.status === 'started' ? { status: 'blocked', untrusted: 'unknown_authorization',
      reason: 'no such grant' } : verdict))
  assert.equal(res.status, 'needs_diagnosis')
  assert.match(res.hardFailures[0].blocking_findings[0].detail, /unknown_authorization/)
  assert.equal(agent.counters.repair, undefined, 'the repair never runs without a claimed launch')
})

test('a replayed launch claim never executes the attempt a second time', async () => {
  // The state a crash between the claim and the work leaves behind: the grant is charged
  // and already `started`. The helper answers the next claim with execution_allowed false,
  // and the engine must treat that as a stop, not as a second attempt.
  const ledger = makeLedgerDouble()
  const { res, agent } = await runWithLedger(forging(ledger, verdict =>
    verdict.status === 'started' ? { ...verdict, execution_allowed: false, replayed: true,
      reason: 'this attempt was already claimed' } : verdict))
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(res.hardFailures[0].blocking_findings[0].type, 'invalid_repair_authorization')
  assert.match(res.hardFailures[0].blocking_findings[0].detail, /execution_allowed/)
  assert.equal(agent.counters.repair, undefined, 'a replay is never a licence to run')
  assert.equal(ledger.spentOf('repair', 'verify'), 1, 'and it charges nothing further')
})

test('the ledger double itself refuses a second launch of one grant', async () => {
  // The double is only trustworthy as a stand-in if it enforces the rule it stands in for.
  const ledger = makeLedgerDouble()
  ledger.respond({ operation: 'authorize', run_id: 'r', authorization_id: 'a1',
    repair_node_id: 'repair', obligations: ['verify'], budgets: { verify: 2 } })
  assert.equal(ledger.respond({ operation: 'start', run_id: 'r', authorization_id: 'a1' }).execution_allowed, true)
  assert.equal(ledger.respond({ operation: 'start', run_id: 'r', authorization_id: 'a1' }).execution_allowed, false)
  const replay = ledger.respond({ operation: 'authorize', run_id: 'r', authorization_id: 'a1',
    repair_node_id: 'repair', obligations: ['verify'], budgets: { verify: 2 } })
  assert.equal(replay.status, 'replayed')
  assert.equal(replay.execution_allowed, false)
  assert.equal(ledger.spentOf('repair', 'verify'), 1, 'a replay charges nothing further')
})

test('an execution whose outcome is unknown is never settled', async () => {
  // The node's stage threw, so this engine did not observe how the attempt ended. Settling
  // it either way would record an outcome nobody watched; the grant stays unresolved and
  // the next run stops for reconciliation.
  const ledger = makeLedgerDouble()
  const agent = makeFakeAgent({
    ...ledgerResponses(ledger),
    'load-dag': { nodes: nodes(), completed: [], repair_loops: [LOOP] },
    implement: passed('implement'),
    verify: qaFailed('verify'),
    repair: () => { throw new Error('host died mid-attempt') },
    'measure:repair': {}, 'commit:implement': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(ledger.spentOf('repair', 'verify'), 1, 'the attempt is spent — it was granted')
  assert.deepEqual(ledger.calls.filter(c => c.operation === 'settle'), [],
    'and nothing settles an execution this engine did not watch end')
  assert.deepEqual([...ledger.entries.values()].map(e => e.state), ['started'],
    'the grant is left unresolved on purpose')
})

test('a settled grant records the observed outcome and refunds nothing', async () => {
  const ledger = makeLedgerDouble()
  const agent = makeFakeAgent({
    ...ledgerResponses(ledger),
    'load-dag': { nodes: nodes(), completed: [], repair_loops: [LOOP] },
    implement: passed('implement'),
    verify: [qaFailed('verify'), passed('verify')],
    repair: passed('repair'), accept: passed('accept'),
    'commit:implement': {}, 'commit:verify': {}, 'commit:repair': {}, 'commit:accept': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'complete')
  const settles = ledger.calls.filter(c => c.operation === 'settle')
  assert.equal(settles.length, 1)
  assert.equal(settles[0].outcome, 'delivered')
  assert.equal(ledger.spentOf('repair', 'verify'), 1, 'a settlement returns no budget')
})

test('a forged settlement receipt stops the run', async () => {
  const ledger = makeLedgerDouble()
  const agent = makeFakeAgent({
    ...ledgerResponses(forging(ledger, verdict =>
      verdict.status === 'settled' ? { ...verdict, authorization_id: 'not-this-one' } : verdict)),
    'load-dag': { nodes: nodes(), completed: [], repair_loops: [LOOP] },
    implement: passed('implement'),
    verify: [qaFailed('verify'), passed('verify')],
    repair: passed('repair'), accept: passed('accept'),
    'commit:implement': {}, 'commit:verify': {}, 'commit:repair': {}, 'commit:accept': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  assert.equal(res.status, 'needs_diagnosis')
  assert.match(res.hardFailures[0].blocking_findings[0].detail, /names authorization/)
})

test('every ledger label the engine emits is one this suite answers', () => {
  // A label the double does not recognise would silently fall through to `undefined`, and
  // an undefined verdict is refused — so a new operation cannot pass unnoticed.
  for (const label of ['ledger:consumption', 'ledger:initialize', 'repair-authorize:r',
    'repair-start:r', 'repair-settle:r']) {
    assert.ok(LEDGER_LABEL.test(label), label)
  }
  assert.ok(!LEDGER_LABEL.test('commit:node'))
  assert.ok(!LEDGER_LABEL.test('repair-route:verify:1'))
})

// --- cross-loop roles: a repair hat never settles the node's own obligation -----------
// ADR 0006 keeps a node in different roles across loops supported, and explicitly rules
// out a repairer accepting its own work: "success in one role cannot cancel another
// role's blocker". Reported against the Codex driver by the independent review
// (systematic-codex-independent-review.md findings 1 and 2); this is the Claude shape.

const CROSS_A = { scope: 'A', qa_node_ids: ['qa1'], repair_node_id: 'shared',
  closure_node_ids: ['closeA'], max_attempts: 2 }
const CROSS_B = { scope: 'B', qa_node_ids: ['shared'], repair_node_id: 'fixer',
  closure_node_ids: ['closeB'], max_attempts: 1 }

const crossNodes = () => [
  { node_id: 'qa1', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
  { node_id: 'shared', capability: 'x', hard_blocked_by: ['qa1'], exit_artifacts: [] },
  { node_id: 'fixer', capability: 'x', hard_blocked_by: ['shared'], exit_artifacts: [] },
  { node_id: 'closeA', capability: 'x', hard_blocked_by: ['shared', 'qa1'], exit_artifacts: [] },
  { node_id: 'closeB', capability: 'x', hard_blocked_by: ['fixer', 'shared'], exit_artifacts: [] }
]

async function runCrossLoop() {
  // Loop B's single attempt is already spent: `shared` is an exhausted obligation.
  const ledger = makeLedgerDouble({ spent: { 'fixer::shared': 1 } })
  const agent = makeFakeAgent({
    ...ledgerResponses(ledger),
    'load-dag': { nodes: crossNodes(), completed: [], repair_loops: [CROSS_A, CROSS_B] },
    qa1: qaFailed('qa1'),
    shared: qaFailed('shared'),
    fixer: passed('fixer'),
    closeA: passed('closeA'), closeB: passed('closeB'),
    'measure:shared': {}, 'measure:fixer': {},
    'commit:qa1': {}, 'commit:shared': {}, 'commit:fixer': {},
    'commit:closeA': {}, 'commit:closeB': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline, phase: cappedPhase() })
  return { res, agent, ledger }
}

test('a repair role never dispatches a node that is an exhausted obligation elsewhere', async () => {
  const { res, agent } = await runCrossLoop()
  assert.equal(res.status, 'needs_diagnosis',
    'an exhausted obligation is refused, never accepted, whatever else the node repairs')
  assert.equal(agent.counters.shared, 1,
    'the node ran once as the QA obligation that failed, and was never re-dispatched as a repairer')
  assert.ok(res.hardFailures.some(f => f.node_id === 'shared'),
    'and its own blocker survives its repair role')
})

test('a node blocked as an obligation never completes by writing its own verdict', async () => {
  const { res, agent } = await runCrossLoop()
  assert.equal(agent.counters['commit:shared'], undefined,
    'a repairer may not accept its own work for the obligation it owes')
  assert.equal(agent.counters.closeA, undefined, 'and no closure opens behind it')
  assert.equal(agent.counters.closeB, undefined)
  assert.notEqual(res.status, 'complete')
})

test('a repair node whose only obligation is exhausted is never dispatched unpaid', async () => {
  const { agent, ledger } = await runCrossLoop()
  assert.equal(agent.counters.fixer, undefined,
    'loop B has nothing left to authorize, so its repair node does not run at all')
  assert.equal(ledger.spentOf('fixer', 'shared'), 1, 'and no further attempt is charged')
  const grants = ledger.calls.filter(c => c.operation === 'authorize')
  for (const grant of grants) {
    assert.ok(!grant.obligations.includes('shared'),
      'an exhausted obligation is never named in a grant')
  }
})
