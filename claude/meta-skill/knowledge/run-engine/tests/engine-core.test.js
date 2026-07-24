const test = require('node:test')
const assert = require('node:assert/strict')
const core = require('../engine-core.js')
const { makeFakeAgent } = require('./fake-agent.js')

test('exports schemas and functions', () => {
  assert.equal(core.DAG_SCHEMA.type, 'object')
  assert.equal(core.NODE_RESULT_SCHEMA.type, 'object')
  assert.equal(core.EXPAND_SCHEMA.type, 'object')
  assert.equal(core.NODE_GATE_SCHEMA.type, 'object')
  assert.equal(core.READINESS_SCHEMA.type, 'object')
  for (const fn of ['computeReady','routeOutcome','mergeExpanded','pickExit','convergenceCheck','serializeCommit','runNode','commitNode','runEngine']) {
    assert.equal(typeof core[fn], 'function', `missing ${fn}`)
  }
})

test('computeReady: ready when all hard_blocked_by are done', () => {
  const nodes = [
    { node_id: 'a', hard_blocked_by: [] },
    { node_id: 'b', hard_blocked_by: ['a'] }
  ]
  assert.deepEqual(core.computeReady(nodes, new Set()).map(n => n.node_id), ['a'])
  assert.deepEqual(core.computeReady(nodes, new Set(['a'])).map(n => n.node_id), ['b'])
})

test('computeReady: completed nodes are skipped', () => {
  const nodes = [{ node_id: 'a', hard_blocked_by: [] }]
  assert.deepEqual(core.computeReady(nodes, new Set(['a'])), [])
})

test('computeReady: alignment_refs do NOT block', () => {
  const nodes = [
    { node_id: 'a', hard_blocked_by: [] },
    { node_id: 'b', hard_blocked_by: ['a'], alignment_refs: ['c'] },
    { node_id: 'c', hard_blocked_by: ['a'], alignment_refs: ['b'] }
  ]
  // after a done, both b and c ready even though they reference each other
  assert.deepEqual(core.computeReady(nodes, new Set(['a'])).map(n => n.node_id), ['b', 'c'])
})

test('routeOutcome: passed -> done', () => {
  assert.equal(core.routeOutcome({ outcome: 'passed', blocking_findings: [] }), 'done')
})
test('routeOutcome: passed with blocking findings is not done', () => {
  assert.equal(core.routeOutcome({
    outcome: 'passed', blocking_findings: [{ type: 'code_gaps' }]
  }), 'soft')
})
test('routeOutcome: hard_fail -> hard', () => {
  assert.equal(core.routeOutcome({ outcome: 'hard_fail', blocking_findings: [] }), 'hard')
})
test('routeOutcome: soft_fail with placeholder -> soft', () => {
  assert.equal(core.routeOutcome({ outcome: 'soft_fail', blocking_findings: [{ type: 'placeholder' }] }), 'soft')
})
test('routeOutcome: soft_fail with cross_node -> hard', () => {
  assert.equal(core.routeOutcome({ outcome: 'soft_fail', blocking_findings: [{ type: 'cross_node' }] }), 'hard')
})
test('routeOutcome: soft_fail with suspected_root_node -> hard', () => {
  assert.equal(core.routeOutcome({ outcome: 'soft_fail', blocking_findings: [{ type: 'failed_validation', suspected_root_node: 'x' }] }), 'hard')
})

test('mergeExpanded: appends new nodes', () => {
  const out = core.mergeExpanded([{ node_id: 'a' }], [{ node_id: 'b' }])
  assert.deepEqual(out.map(n => n.node_id), ['a', 'b'])
})
test('mergeExpanded: idempotent on existing node_id', () => {
  const out = core.mergeExpanded([{ node_id: 'a' }], [{ node_id: 'a' }, { node_id: 'b' }])
  assert.deepEqual(out.map(n => n.node_id), ['a', 'b'])
})
test('mergeExpanded: repairs an existing node definition', () => {
  const out = core.mergeExpanded(
    [{ node_id: 'a', hard_blocked_by: ['old'], capability: 'x' }],
    [{ node_id: 'a', hard_blocked_by: ['new'] }]
  )
  assert.deepEqual(out[0], {
    node_id: 'a', hard_blocked_by: ['new'], capability: 'x'
  })
})

test('pickExit: all done -> complete', () => {
  assert.equal(core.pickExit([], []), 'complete')
})
test('pickExit: hard failures -> needs_diagnosis', () => {
  assert.equal(core.pickExit([], [{ node_id: 'c' }]), 'needs_diagnosis')
})
test('pickExit: remaining nodes but no progress -> needs_diagnosis (stuck graph)', () => {
  assert.equal(core.pickExit([{ node_id: 'x' }], []), 'needs_diagnosis')
})

test('convergenceCheck: under cap -> false', () => {
  const hist = [{ root_cause: 'r1' }]
  assert.equal(core.convergenceCheck(hist, 'r1'), false)
})
test('convergenceCheck: at/over cap (>=2 same root) -> true (UNRESOLVED)', () => {
  const hist = [{ root_cause: 'r1' }, { root_cause: 'r1' }, { root_cause: 'r2' }]
  assert.equal(core.convergenceCheck(hist, 'r1'), true)
  assert.equal(core.convergenceCheck(hist, 'r2'), false)
})

test('runNode: passes first try -> returns passed', async () => {
  const agent = makeFakeAgent({ a: { node_id: 'a', outcome: 'passed', artifacts_written: [], blocking_findings: [] } })
  const r = await core.runNode({ node_id: 'a' }, agent)
  assert.equal(r.outcome, 'passed')
  assert.equal(agent.counters.a, 1)
  assert.equal(agent.counters['verify:a'], 1)
})

test('runNode: soft-fails then passes within retry budget', async () => {
  const agent = makeFakeAgent({ b: [
    { node_id: 'b', outcome: 'soft_fail', artifacts_written: [], blocking_findings: [{ type: 'placeholder', detail: 'stub bgm' }] },
    { node_id: 'b', outcome: 'passed', artifacts_written: [], blocking_findings: [] }
  ] })
  const r = await core.runNode({ node_id: 'b' }, agent)
  assert.equal(r.outcome, 'passed')
  assert.equal(agent.counters.b, 2) // one retry
})

test('runNode: cross_node -> hard immediately, no retry', async () => {
  const agent = makeFakeAgent({ c: { node_id: 'c', outcome: 'soft_fail', artifacts_written: [], blocking_findings: [{ type: 'cross_node', detail: 'upstream missing', suspected_root_node: 'n1' }] } })
  const r = await core.runNode({ node_id: 'c' }, agent)
  assert.equal(r.outcome, 'hard_fail')
  assert.equal(agent.counters.c, 1) // not retried
})

test('runNode: exhausts soft retries -> hard_fail', async () => {
  const soft = { node_id: 'd', outcome: 'soft_fail', artifacts_written: [], blocking_findings: [{ type: 'placeholder', detail: 'still stub' }] }
  const agent = makeFakeAgent({ d: soft })
  const r = await core.runNode({ node_id: 'd', soft_retry_max: 2 }, agent)
  assert.equal(r.outcome, 'hard_fail')
  assert.equal(r.blocking_findings[0].type, 'exhausted_retries')
  assert.equal(agent.counters.d, 3) // initial + 2 retries
})

test('runNode: artifact gaps invoke repair loop and rerun QA', async () => {
  const agent = makeFakeAgent({
    qa: [
      { node_id: 'qa', outcome: 'passed', artifacts_written: ['qa.json'],
        blocking_findings: [] },
      { node_id: 'qa', outcome: 'passed', artifacts_written: ['qa.json'],
        blocking_findings: [] }
    ],
    'verify:qa': [
      { node_id: 'qa', status: 'repair',
        blocking_findings: [{ type: 'code_gaps', detail: 'missing retry path' }] },
      { node_id: 'qa', status: 'passed', blocking_findings: [] }
    ],
    'repair:qa:1': {}
  })
  const result = await core.runNode({ node_id: 'qa' }, agent)
  assert.equal(result.outcome, 'passed')
  assert.equal(agent.counters.qa, 2)
  assert.equal(agent.counters['repair:qa:1'], 1)
  assert.equal(agent.counters['verify:qa'], 2)
})

test('runNode: missing artifact gate is a hard failure', async () => {
  const agent = makeFakeAgent({
    x: { node_id: 'x', outcome: 'passed', artifacts_written: [], blocking_findings: [] },
    'verify:x': null
  })
  const result = await core.runNode({ node_id: 'x' }, agent)
  assert.equal(result.outcome, 'hard_fail')
  assert.equal(result.blocking_findings[0].type, 'invalid_artifact_gate')
})
