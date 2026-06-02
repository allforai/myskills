const test = require('node:test')
const assert = require('node:assert/strict')
const { pipeline, parallel } = require('./harness-doubles.js')

test('pipeline: each item flows through all stages', async () => {
  const out = await pipeline([1, 2], x => x + 1, x => x * 10)
  assert.deepEqual(out, [20, 30])
})

test('pipeline: a throwing stage drops that item to null', async () => {
  const out = await pipeline([1, 2], x => { if (x === 1) throw new Error('boom'); return x }, x => x)
  assert.deepEqual(out, [null, 2])
})

test('pipeline: no barrier — item with fast chain finishes without waiting for slow item', async () => {
  const order = []
  const defer = () => { let r; const p = new Promise(res => { r = res }); return { p, r } }
  const slow = defer()
  await pipeline(
    ['fast', 'slow'],
    item => item === 'slow' ? slow.p.then(() => item) : item,
    item => { order.push(item); if (item === 'fast') slow.r(); return item }
  )
  assert.deepEqual(order, ['fast', 'slow']) // fast reached stage 2 before slow resolved stage 1
})

test('parallel: awaits all, failures become null', async () => {
  const out = await parallel([() => 1, () => { throw new Error('x') }, async () => 3])
  assert.deepEqual(out, [1, null, 3])
})
