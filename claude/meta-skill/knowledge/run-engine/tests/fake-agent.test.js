const test = require('node:test')
const assert = require('node:assert/strict')
const { makeFakeAgent, makeDeferred } = require('./fake-agent.js')

test('fake agent: returns scripted response by label, records calls', async () => {
  const agent = makeFakeAgent({ 'load-dag': { nodes: [], completed: [] } })
  const r = await agent('load the dag', { label: 'load-dag' })
  assert.deepEqual(r, { nodes: [], completed: [] })
  assert.equal(agent.calls.length, 1)
  assert.equal(agent.calls[0].label, 'load-dag')
})

test('fake agent: array response returns per-call in sequence', async () => {
  const agent = makeFakeAgent({ b: [{ outcome: 'soft_fail' }, { outcome: 'passed' }] })
  assert.equal((await agent('x', { label: 'b' })).outcome, 'soft_fail')
  assert.equal((await agent('x', { label: 'b' })).outcome, 'passed')
  assert.equal((await agent('x', { label: 'b' })).outcome, 'passed') // clamps to last
  assert.equal(agent.counters.b, 3)
})

test('fake agent: deferred response resolves on demand', async () => {
  const d = makeDeferred()
  const agent = makeFakeAgent({ c: { __promise: d.promise } })
  let resolved = false
  const p = agent('x', { label: 'c' }).then(v => { resolved = true; return v })
  await Promise.resolve()
  assert.equal(resolved, false)
  d.resolve({ outcome: 'passed' })
  assert.equal((await p).outcome, 'passed')
})

test('fake agent: label defaults to prompt when no opts.label', async () => {
  const agent = makeFakeAgent({ 'commit:a': { ok: true } })
  await agent('commit:a')
  assert.equal(agent.calls[0].label, 'commit:a')
})
