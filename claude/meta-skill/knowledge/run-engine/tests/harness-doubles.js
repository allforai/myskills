// Faithful-enough re-implementations of the Workflow harness primitives,
// per their documented semantics, for deterministic in-Node testing.
// pipeline: each item runs all stages independently, NO barrier between stages.
async function pipeline(items, ...stages) {
  return Promise.all(items.map(async (item, i) => {
    let v = item
    for (const stage of stages) {
      try { v = await stage(v, item, i) } catch { return null }
    }
    return v
  }))
}

// parallel: run all thunks concurrently, await all; a throwing thunk -> null.
async function parallel(thunks) {
  return Promise.all(thunks.map(async t => {
    try { return await t() } catch { return null }
  }))
}

module.exports = { pipeline, parallel }
