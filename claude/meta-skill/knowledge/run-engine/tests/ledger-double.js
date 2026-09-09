// A test double for the canonical repair-authorization ledger.
//
// MOCK BOUNDARY. This re-implements only the decisions `repair_authorization.py` makes
// for the operations this engine calls, so L2 fake-agent tests can drive many waves
// without a Python process per call. It is NOT the helper: it has no file, no lock, no
// durability and no historical recovery, and it is deliberately not used where the
// boundary itself is the subject. `declared-loop.test.js` runs the REAL helper CLI
// through the engine's own prompts; if this double and the helper ever disagree, the
// real-helper test is the one that is right.
//
// Contract mirrored (see docs/.../systematic-authorization-foundation-report.md):
//   consumption -> {status: ok, run_id, obligations[{repair_node_id,qa_node_id,spent,...}], unresolved[]}
//   authorize   -> {status: authorized, execution_allowed: false, charged{}} | replayed | budget_exhausted
//   start       -> first: {status: started, execution_allowed: true}; later: execution_allowed false
//   settle      -> {status: settled, refunded: false}
function makeLedgerDouble({ runId = 'run-double', spent = {}, unresolved = [], missing = false } = {}) {
  const entries = new Map()          // authorization_id -> entry
  const charged = new Map(Object.entries(spent))   // "repair::qa" -> attempts
  let initialized = !missing
  const calls = []

  const obligations = () => [...charged].map(([key, n]) => {
    const [repair_node_id, qa_node_id] = key.split('::')
    return { repair_node_id, qa_node_id, spent: n, budget: null, remaining: null, exhausted: false,
      unresolved: [...entries.values()].filter(e => e.state !== 'settled' &&
        e.repair_node_id === repair_node_id && e.obligations.includes(qa_node_id))
        .map(e => e.authorization_id) }
  })

  const openGrants = () => [...entries.values()].filter(e => e.state !== 'settled')
    .map(e => ({ authorization_id: e.authorization_id, state: e.state,
      repair_node_id: e.repair_node_id, obligations: e.obligations }))

  function respond(request) {
    calls.push(request)
    if (request.operation === 'consumption') {
      if (!initialized) {
        return { status: 'blocked', untrusted: 'missing_ledger',
          reason: 'No repair-authorization ledger; absence of records is not proof of unused budget' }
      }
      return { status: 'ok', reason: 'Consumption read from the authoritative ledger',
        run_id: runId, origin: 'new_run', obligations: obligations(),
        unresolved: [...unresolved, ...openGrants()] }
    }
    if (request.operation === 'initialize') {
      initialized = true
      return { status: 'ok', run_id: request.run_id, origin: 'new_run',
        reason: 'Workflow verified untouched; this run provably starts at zero' }
    }
    if (request.operation === 'authorize') {
      const existing = entries.get(request.authorization_id)
      if (existing) {
        return { status: 'replayed', execution_allowed: false,
          authorization_id: request.authorization_id, repair_node_id: existing.repair_node_id,
          charged: existing.charged, state: existing.state,
          reason: 'This dispatch is already authorized; nothing further charged' }
      }
      const next = {}
      for (const qa of request.obligations) {
        next[qa] = (charged.get(`${request.repair_node_id}::${qa}`) || 0) + 1
        if (next[qa] > request.budgets[qa]) {
          return { status: 'budget_exhausted', authorization_id: request.authorization_id,
            repair_node_id: request.repair_node_id, reason: 'Repair budget is exhausted' }
        }
      }
      for (const qa of request.obligations) charged.set(`${request.repair_node_id}::${qa}`, next[qa])
      entries.set(request.authorization_id, { authorization_id: request.authorization_id,
        repair_node_id: request.repair_node_id, obligations: [...request.obligations],
        charged: next, state: 'authorized' })
      return { status: 'authorized', execution_allowed: false,
        authorization_id: request.authorization_id, repair_node_id: request.repair_node_id,
        run_id: runId, charged: next, state: 'authorized' }
    }
    if (request.operation === 'start') {
      const entry = entries.get(request.authorization_id)
      if (!entry) {
        return { status: 'blocked', untrusted: 'unknown_authorization',
          reason: 'execution without a durable grant is what the grant exists to prevent' }
      }
      if (entry.state !== 'authorized') {
        return { status: entry.state === 'settled' ? 'blocked' : 'started', execution_allowed: false,
          replayed: true, authorization_id: request.authorization_id, state: entry.state,
          reason: 'this attempt was already claimed' }
      }
      entry.state = 'started'
      return { status: 'started', execution_allowed: true, authorization_id: request.authorization_id,
        state: 'started', charged: entry.charged }
    }
    if (request.operation === 'settle') {
      const entry = entries.get(request.authorization_id)
      if (!entry) return { status: 'blocked', untrusted: 'unknown_authorization', reason: 'no such grant' }
      entry.state = 'settled'
      entry.outcome = request.outcome
      return { status: 'settled', authorization_id: request.authorization_id,
        outcome: request.outcome, charged: entry.charged, refunded: false }
    }
    return { status: 'invalid', reason: `unknown operation ${request.operation}` }
  }

  // The engine only ever talks to the ledger through `authorizationPrompt`, so the double
  // reads the request back out of the prompt exactly as the real agent's shell would.
  function fromPrompt(prompt) {
    const match = /printf '%s' '(.*?)' \| python3/s.exec(prompt)
    if (!match) throw new Error(`prompt does not carry a ledger request: ${prompt}`)
    return respond(JSON.parse(match[1].replace(/'\\''/g, "'")))
  }

  return { respond, fromPrompt, calls, entries, charged,
    spentOf: (repairNodeId, qaNodeId) => charged.get(`${repairNodeId}::${qaNodeId}`) || 0 }
}

// The labels the engine uses for ledger work; the rest of the map is the test's own.
const LEDGER_LABEL = /^(ledger:(consumption|initialize)|repair-(authorize|start|settle):)/

// Spread into makeFakeAgent's response map: it answers every ledger label from one double
// and leaves every other label to the test.
function ledgerResponses(ledger) {
  return { __fallback: (label, prompt) => LEDGER_LABEL.test(label) ? ledger.fromPrompt(prompt) : undefined }
}

module.exports = { makeLedgerDouble, ledgerResponses, LEDGER_LABEL }
