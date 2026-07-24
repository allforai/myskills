function makeDeferred() {
  let resolve, reject
  const promise = new Promise((res, rej) => { resolve = res; reject = rej })
  return { promise, resolve, reject }
}

// responses: { [label]: response | response[] | (callIndex, prompt) => response | { __promise } }
function makeFakeAgent(responses) {
  const calls = []
  const counters = {}
  const agent = async (prompt, opts = {}) => {
    const label = opts.label || prompt
    calls.push({ label, prompt, opts })
    counters[label] = (counters[label] || 0) + 1
    const idx = counters[label] - 1
    let spec = responses[label]
    if (spec === undefined && label.startsWith('verify:')) {
      spec = {
        node_id: label.slice('verify:'.length),
        status: 'passed',
        blocking_findings: []
      }
    }
    if (typeof spec === 'function') spec = spec(idx, prompt)
    if (Array.isArray(spec)) spec = spec[Math.min(idx, spec.length - 1)]
    if (spec && spec.__promise) return spec.__promise
    return spec
  }
  agent.calls = calls
  agent.counters = counters
  return agent
}

module.exports = { makeFakeAgent, makeDeferred }
