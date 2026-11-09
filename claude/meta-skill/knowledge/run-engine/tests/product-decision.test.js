// ADR-0011 D: a structured unresolved product decision blocks its own subgraph, not the
// run. Unrelated branches finish; the run ends `needs_product_decision` with the
// questions for the next interactive bootstrap. A finding without that structure is not
// trusted as one and still ends in diagnosis.
const test = require('node:test')
const assert = require('node:assert/strict')
const core = require('../engine-core.js')
const { pipeline } = require('./harness-doubles.js')
const { makeFakeAgent } = require('./fake-agent.js')

const passed = id => ({ node_id: id, outcome: 'passed', artifacts_written: [`art/${id}`], blocking_findings: [] })
const decision = {
  type: 'unresolved_product_decision', decision_id: 'scope-a-b',
  needed_decision: 'Is the kept value shared across instances or kept per instance?',
  options: ['shared', 'per-instance'], recommended: 'per-instance', blocking_intent_ids: ['i-1']
}
const gapResult = (id, finding = decision) => ({
  node_id: id, outcome: 'hard_fail',
  artifacts_written: [`.allforai/bootstrap/product-decision-gaps/${id}.json`],
  blocking_findings: [finding]
})

// design -> build depends on the gap; other -> other-build is an unrelated branch.
const dag = () => ({ nodes: [
  { node_id: 'design', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
  { node_id: 'build', capability: 'x', hard_blocked_by: ['design'], exit_artifacts: [] },
  { node_id: 'other', capability: 'x', hard_blocked_by: [], exit_artifacts: [] },
  { node_id: 'other-build', capability: 'x', hard_blocked_by: ['other'], exit_artifacts: [] }
], completed: [] })

test('productDecisionGap: only the full structure counts', () => {
  assert.equal(core.productDecisionGap(gapResult('design')), true)
  const { options, ...noOptions } = decision
  assert.equal(core.productDecisionGap(gapResult('design', noOptions)), false)
  assert.equal(core.productDecisionGap(gapResult('design', { ...decision, needed_decision: ' ' })), false)
  assert.equal(core.productDecisionGap(gapResult('design', { ...decision, options: ['only one'] })), false)
  assert.equal(core.productDecisionGap({ ...gapResult('design'), outcome: 'passed' }), false)
  // Mixed with any other finding, the failure is not only a missing decision.
  const mixed = gapResult('design')
  mixed.blocking_findings.push({ type: 'cross_node', detail: 'broken' })
  assert.equal(core.productDecisionGap(mixed), false)
})

test('a product-decision gap blocks its subgraph while the unrelated branch finishes', async () => {
  const agent = makeFakeAgent({
    'load-dag': dag(),
    design: gapResult('design'), other: passed('other'), 'other-build': passed('other-build'),
    'commit:other': {}, 'commit:other-build': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'needs_product_decision')
  assert.deepEqual(res.decisions.map(d => [d.node_id, d.decision_id]), [['design', 'scope-a-b']])
  assert.equal(agent.counters['other-build'], 1)
  assert.equal(agent.counters.build, undefined) // its dependent never ran
  assert.equal(agent.counters.design, 1)        // not retried, not diagnosed
})

test('an unstructured decision claim still ends in diagnosis', async () => {
  const { options, ...noOptions } = decision
  const agent = makeFakeAgent({
    'load-dag': dag(),
    design: gapResult('design', noOptions), other: passed('other'), 'other-build': passed('other-build'),
    'commit:other': {}, 'commit:other-build': {}, 'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'needs_diagnosis')
})

test('a gap beside a real failure ends in diagnosis, carrying both', async () => {
  const agent = makeFakeAgent({
    'load-dag': dag(),
    design: gapResult('design'),
    other: { node_id: 'other', outcome: 'hard_fail', artifacts_written: [],
             blocking_findings: [{ type: 'invalid_artifact_gate', detail: 'gate crashed' }] },
    'commit-failures': {}
  })
  const res = await core.runEngine({ agent, pipeline })
  assert.equal(res.status, 'needs_diagnosis')
  assert.deepEqual(res.hardFailures.map(f => f.node_id).sort(), ['design', 'other'])
})
