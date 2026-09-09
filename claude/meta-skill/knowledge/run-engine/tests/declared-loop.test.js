// The canonical declared repair loop, judged by the real independent artifact gate.
//
// Every other test in this suite answers `verify:<node>` from a fake gate, so none of
// them can see the boundary this one is about: a declared repair node is
// `hard_blocked_by` the QA node it repairs, and `check_artifacts.py` folds freshness
// into `all_exist`, so while that QA node is failing the repair node's own evidence is
// stale and its gate refuses it. The loop therefore cannot advance on the repair node
// completing; it advances on the repair delivering, and the QA rerun is the check.
const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const core = require('../engine-core.js')
const { pipeline } = require('./harness-doubles.js')
const { makeFakeAgent } = require('./fake-agent.js')
const { declaredLoopProject, realGate, realMeasurement, publishEvidence } = require('./real-gate.js')

const LOOP = {
  scope: 'orders-export',
  qa_node_ids: ['verify'],
  repair_node_id: 'repair',
  closure_node_ids: ['accept'],
  max_attempts: 2
}

const attempts = () => [{ repair_node_id: 'repair', qa_node_id: 'verify', attempts: 0 }]

function writeReport(root, name, value) {
  fs.writeFileSync(path.join(root, name), JSON.stringify(value))
}

// One executor for both hosts' story: the QA node fails, the repair delivers, the QA
// rerun passes and publishes, the repair then publishes what it already delivered.
function declaredLoopAgent(root, nodes, calls = [], { unmeasured = false, executor = null } = {}) {
  const counters = {}
  const bump = id => (counters[id] = (counters[id] || 0) + 1)
  const gate = id => () => realGate(root, id, { unmeasured })
  return makeFakeAgent({
    'measure:repair': () => realMeasurement(root, 'repair', { unmeasured }),
    'load-dag': { nodes, completed: [], repair_loops: [LOOP], repair_attempts: attempts() },
    verify: () => {
      const n = bump('verify')
      calls.push(`verify:${n}`)
      if (n === 1) {
        writeReport(root, 'verify.json', { status: 'failed', gaps: ['missing column'] })
        return { node_id: 'verify', outcome: 'hard_fail', artifacts_written: ['verify.json'],
          blocking_findings: [{ type: 'cross_node', detail: 'export column missing',
            suspected_root_node: 'repair' }] }
      }
      writeReport(root, 'verify.json', { status: 'passed' })
      calls.push(`verify-publish:${publishEvidence(root, 'verify')}`)
      return { node_id: 'verify', outcome: 'passed', artifacts_written: ['verify.json'], blocking_findings: [] }
    },
    repair: () => {
      const n = bump('repair')
      calls.push(`repair:${n}`)
      if (executor) executor(root, n)
      else if (n === 1) writeReport(root, 'repair.json', { status: 'passed' })
      calls.push(`repair-publish:${publishEvidence(root, 'repair')}`)
      return { node_id: 'repair', outcome: 'passed', artifacts_written: ['repair.json'], blocking_findings: [] }
    },
    accept: () => {
      bump('accept')
      calls.push('accept:1')
      writeReport(root, 'accept.json', { status: 'passed' })
      calls.push(`accept-publish:${publishEvidence(root, 'accept')}`)
      return { node_id: 'accept', outcome: 'passed', artifacts_written: ['accept.json'], blocking_findings: [] }
    },
    'verify:verify': gate('verify'),
    'verify:repair': gate('repair'),
    'verify:accept': gate('accept'),
    'commit:verify': {}, 'commit:repair': {}, 'commit:accept': {},
    'commit-failures': {}
  })
}

test('the real gate refuses a declared repair node while its QA node is failing', () => {
  const { root } = declaredLoopProject()
  writeReport(root, 'verify.json', { status: 'failed', gaps: ['missing column'] })
  writeReport(root, 'repair.json', { status: 'passed' })

  const gate = realGate(root, 'repair')
  assert.equal(gate.status, 'repair', 'the independent gate withholds the repair node')
  assert.match(gate.blocking_findings[0].detail, /"upstream": *\["verify"\]/)
  assert.equal(publishEvidence(root, 'repair'), 'stale',
    'and it cannot publish the evidence that would satisfy the gate')

  // Once the QA node passes and publishes, the repair node satisfies its own gate.
  writeReport(root, 'verify.json', { status: 'passed' })
  assert.equal(publishEvidence(root, 'verify'), 'valid')
  assert.equal(publishEvidence(root, 'repair'), 'valid')
  assert.equal(realGate(root, 'repair').status, 'passed')
})

test('an unmeasurable delivery fails closed rather than advancing the loop', async () => {
  // A checker that does not publish the measurement fields leaves the engine unable to
  // prove the delivery, so it refuses it. Fail closed, never a silent advance.
  const { root, nodes } = declaredLoopProject()
  const agent = declaredLoopAgent(root, nodes, [], { unmeasured: true })
  const res = await core.runEngine({ agent, pipeline })

  assert.equal(res.status, 'needs_diagnosis')
  assert.equal(res.hardFailures[0].node_id, 'repair')
  assert.equal(res.hardFailures[0].blocking_findings[0].type, 'unmeasured_repair_delivery')
  assert.equal(agent.counters.accept, undefined, 'closure never ran on an unmeasured delivery')
})

test('runEngine drives the declared loop to closure against the real gate', async () => {
  const { root, nodes } = declaredLoopProject()
  const calls = []
  const agent = declaredLoopAgent(root, nodes, calls)
  const res = await core.runEngine({ agent, pipeline })

  assert.equal(res.status, 'complete', `run did not close: ${JSON.stringify(res)}\n${calls.join(' ')}`)
  assert.equal(agent.counters.verify, 2, 'the QA node reran after the repair delivered')
  assert.equal(agent.counters.repair, 2, 'the repair delivered, then finalized its evidence')
  assert.equal(agent.counters.accept, 1)
  assert.deepEqual(calls.filter(c => c.endsWith('-publish:stale')), ['repair-publish:stale'],
    'only the first repair publication is refused')
  assert.equal(agent.counters['commit:repair'], 1, 'the repair node commits once, on its own merits')
  assert.equal(agent.counters['commit:verify'], 1, 'only the passing QA run commits')
})

test('runEngine does not commit a repair node that only delivered', async () => {
  const { root, nodes } = declaredLoopProject()
  const calls = []
  const agent = declaredLoopAgent(root, nodes, calls)
  await core.runEngine({ agent, pipeline })

  const order = agent.calls.map(c => c.label).filter(l => ['verify', 'repair', 'accept', 'commit:repair'].includes(l))
  assert.deepEqual(order, ['verify', 'repair', 'verify', 'repair', 'commit:repair', 'accept'],
    'the repair is committed only after the QA rerun passed, never on its delivery')
})


// --- what the measurement refuses, at the same real boundary ---

const declared = { node_id: 'repair', exit_artifacts: ['repair.json'] }
const open = digest => ({ qa: ['verify'],
  before: { artifacts: [{ path: 'repair.json', exists: true, digest }],
    withheld_by: ['verify'], binding_identity: 'snapshot-a', readiness_status: 'valid' } })
const gateWith = measurement => ({ node_id: 'repair', status: 'repair', blocking_findings: [], measurement })
// The checker's shape, as landed: digest always printed (null with digest_error when it
// cannot be read), and binding_identity paired with the node's current readiness_status.
const measured = (overrides = {}) => gateWith({
  artifacts: [{ path: 'repair.json', exists: true, digest: 'after', ...(overrides.artifact || {}) }],
  withheld_by: overrides.withheld_by || ['verify'],
  readiness_status: overrides.readiness_status === undefined ? 'valid' : overrides.readiness_status,
  ...(overrides.binding_identity === undefined ? { binding_identity: 'snapshot-a' }
    : { binding_identity: overrides.binding_identity })
})

test('measuredDelivery: a measured write against one snapshot is a delivery', () => {
  const delivery = core.measuredDelivery(declared, measured(), open('before'))
  assert.deepEqual(delivery, { binding_identity: 'snapshot-a', produced: { 'repair.json': 'after' } })
})

test('measuredDelivery: an unchanged or touched artifact is not a delivery', () => {
  assert.equal(core.measuredDelivery(declared, measured(), open('after')), null)
})

test('measuredDelivery: a missing or blocked artifact is not a delivery', () => {
  assert.equal(core.measuredDelivery(declared, measured({ artifact: { exists: false } }), open('before')), null)
  assert.equal(core.measuredDelivery(declared,
    measured({ artifact: { status_error: 'status=failed_env' } }), open('before')), null)
})

test('measuredDelivery: an unbound delivery is not a delivery', () => {
  assert.equal(core.measuredDelivery(declared, measured({ binding_identity: null }), open('before')), null)
  const drifted = { qa: ['verify'], before: { artifacts: [{ path: 'repair.json', exists: true, digest: 'before' }],
    withheld_by: ['verify'], binding_identity: 'snapshot-b', readiness_status: 'valid' } }
  assert.equal(core.measuredDelivery(declared, measured(), drifted), null, 'the snapshot moved mid-attempt')
})

test('measuredDelivery: a binding that is no longer current is not a delivery', () => {
  // Content identity and binding answer different questions: after a source change the
  // recorded observation can still match while the node is no longer readable as current.
  for (const readiness_status of ['stale', 'invalid', 'uncertain', 'undeclared', null]) {
    assert.equal(core.measuredDelivery(declared, measured({ readiness_status }), open('before')), null,
      `readiness_status ${readiness_status} must not deliver`)
  }
})

test('measuredDelivery: an unreadable artifact is not a delivery even when it exists', () => {
  // The checker prints a null digest with digest_error for a file it cannot read through —
  // missing, outside the project root, or a symlink escape — and `exists` is deliberately
  // left as it was.
  assert.equal(core.measuredDelivery(declared,
    measured({ artifact: { digest: null, digest_error: 'outside project root' } }), open('before')), null)
})

test('measuredDelivery: a gate withheld for any other reason is not a delivery', () => {
  assert.equal(core.measuredDelivery(declared, measured({ withheld_by: [] }), open('before')), null)
  assert.equal(core.measuredDelivery(declared, measured({ withheld_by: ['verify', 'somewhere-else'] }),
    open('before')), null)
})

test('measuredDelivery: an absent measurement, or one missing the requested fields, is not a delivery', () => {
  assert.equal(core.measuredDelivery(declared, { node_id: 'repair', status: 'repair', blocking_findings: [] },
    open('before')), null)
  assert.equal(core.measuredDelivery(declared, measured({ artifact: { digest: undefined } }), open('before')), null)
  assert.equal(core.measuredDelivery(declared, measured(), { qa: ['verify'], before: null }), null)
})

test('measurePrompt runs the shipped checker and forbids inventing its fields', () => {
  const prompt = core.measurePrompt(declared)
  assert.match(prompt, /check_artifacts\.py/)
  assert.match(prompt, /do not compute, infer or fill in any/)
})
