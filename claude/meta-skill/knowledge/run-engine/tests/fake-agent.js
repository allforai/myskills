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
    if (spec === undefined && label === 'run-policy') {
      spec = { status: 'run_policy_ready', policy: {
        on_repeated_failure: 'halt', on_needs_iteration: 'halt_with_report', on_safety_warning: 'continue'
      } }
    }
    for (const prefix of ['verify:', 'inherit:']) {   // both are the independent gate, asked at different moments
      if (spec === undefined && label.startsWith(prefix)) {
        spec = { node_id: label.slice(prefix.length), status: 'passed', blocking_findings: [] }
      }
    }
    // record_transition.py's receipt, unless a test answers the relay itself. `{}` is how
    // older tests said "the commit happened"; it means the same receipt.
    const recorded = /^(commit|repair-route):([^:]+)/.exec(label)
    if (recorded && (spec === undefined || (spec && typeof spec === 'object' && !Array.isArray(spec) &&
        Object.keys(spec).length === 0))) {
      spec = { status: 'recorded', node_id: recorded[2], transition_index: 0, replayed: false }
    }
    // Unknown labels may be answered by a fallback: the ledger double registers one,
    // because the engine's authorize/start/settle labels carry the repair node id.
    if (spec === undefined && typeof responses.__fallback === 'function') {
      spec = responses.__fallback(label, prompt, idx)
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
