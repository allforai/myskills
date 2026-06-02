// <<<ENGINE-CORE-START>>>
const DAG_SCHEMA = {
  type: 'object',
  required: ['nodes', 'completed'],
  properties: {
    nodes: { type: 'array', items: { type: 'object',
      required: ['node_id', 'capability', 'hard_blocked_by', 'exit_artifacts'],
      properties: {
        node_id: { type: 'string' },
        capability: { type: 'string' },
        hard_blocked_by: { type: 'array', items: { type: 'string' } },
        alignment_refs: { type: 'array', items: { type: 'string' } },
        exit_artifacts: { type: 'array', items: { type: 'object' } },
        node_spec_path: { type: 'string' },
        profile_slice: { type: 'object' },
        decision_mode: { type: 'string', enum: ['brainstorm', 'none'] },
        decision_inputs: { type: 'array', items: { type: 'string' } },
        closure_verify: { type: 'array', items: { type: 'string' } },
        soft_retry_max: { type: 'integer' }
      } } },
    completed: { type: 'array', items: { type: 'string' } },
    expanders: { type: 'array', items: { type: 'string' } },
    applied_expanders: { type: 'array', items: { type: 'string' } } // fix C5: cross-session double-expansion guard
  }
}

const NODE_RESULT_SCHEMA = {
  type: 'object',
  required: ['node_id', 'outcome', 'artifacts_written', 'blocking_findings'],
  properties: {
    node_id: { type: 'string' },
    outcome: { type: 'string', enum: ['passed', 'soft_fail', 'hard_fail'] },
    artifacts_written: { type: 'array', items: { type: 'string' } },
    blocking_findings: { type: 'array', items: { type: 'object' } },
    assumed_decisions: { type: 'array', items: { type: 'object' } }, // fix C1: engine persists these, not the subagent
    summary: { type: 'string' }
  }
}

const EXPAND_SCHEMA = {
  type: 'object',
  required: ['new_nodes'],
  properties: { new_nodes: { type: 'array', items: { type: 'object' } } }
}

function computeReady(nodes, done) {
  return nodes.filter(n =>
    !done.has(n.node_id) &&
    (n.hard_blocked_by || []).every(dep => done.has(dep)))
}

function routeOutcome(result) {
  if (result.outcome === 'passed') return 'done'
  if (result.outcome === 'hard_fail') return 'hard'
  const findings = result.blocking_findings || []
  if (findings.some(f => f.type === 'cross_node' || f.suspected_root_node)) return 'hard'
  return 'soft'
}

function mergeExpanded(nodes, newNodes) {
  const seen = new Set(nodes.map(n => n.node_id))
  return [...nodes, ...(newNodes || []).filter(n => !seen.has(n.node_id))]
}

function pickExit(remaining, hardFailures) {
  if ((hardFailures || []).length > 0) return 'needs_diagnosis'
  if ((remaining || []).length === 0) return 'complete'
  return 'needs_diagnosis' // remaining-but-unready = planning bug / deadlock
}

function convergenceCheck(diagnosisHistory, rootCause) {
  const count = (diagnosisHistory || []).filter(d => d.root_cause === rootCause).length
  return count >= 2
}

let _commitQueue = Promise.resolve()
function serializeCommit(fn) {           // fix C1: physical commits never overlap
  const next = _commitQueue.then(fn, fn) // chain regardless of prior outcome
  _commitQueue = next.then(() => {}, () => {})
  return next
}

async function runNode(node, agent) {
  const max = node.soft_retry_max ?? 2
  let attempt = 0
  let strict = ''
  while (true) {
    const r = await agent(`run:${node.node_id}${strict}`, { schema: NODE_RESULT_SCHEMA, label: node.node_id })
    const cls = routeOutcome(r)
    if (cls === 'done') return r
    if (cls === 'hard') return { ...r, outcome: 'hard_fail' }
    if (attempt >= max) {
      return { ...r, outcome: 'hard_fail',
        blocking_findings: [{ type: 'exhausted_retries', detail: `soft retried ${max}x without passing` }] }
    }
    attempt += 1
    strict = ` [retry ${attempt}: must fix all blocking findings]`
  }
}

async function commitNode(result, agent, done) {
  // The commit agent appends transition_log + any result.assumed_decisions to
  // assumed-decisions.json (real prompt wired in Plan 2). Engine persists; subagent does not.
  await agent(`commit:${result.node_id}`, { label: `commit:${result.node_id}` })
  done.add(result.node_id)
}

async function runEngine({ agent, pipeline, log = () => {}, phase = () => {} }) {
  phase('Load')
  const dag = await agent('load workflow.json into DAG_SCHEMA', { schema: DAG_SCHEMA, label: 'load-dag' })
  const done = new Set(dag.completed || [])
  const applied = new Set(dag.applied_expanders || [])   // fix C5

  phase('Expand')
  for (const exp of (dag.expanders || [])) {
    if (applied.has(exp)) continue                        // fix C5: don't re-run on resume
    const r = await agent(`run expander ${exp}; return new_nodes`, { schema: EXPAND_SCHEMA, label: `expand:${exp}` })
    dag.nodes = mergeExpanded(dag.nodes, (r && r.new_nodes) || [])
    applied.add(exp)
  }

  phase('Execute')
  while (true) {
    const ready = computeReady(dag.nodes, done)
    if (ready.length === 0) break
    log(`running ${ready.length} ready node(s)`)
    const outcomes = await pipeline(
      ready,
      node => runNode(node, agent),
      result => routeOutcome(result) === 'done'
        ? serializeCommit(() => commitNode(result, agent, done)).then(() => result)  // fix C1: serialized
        : result,
      result => routeOutcome(result) === 'done' ? null : result
    )
    const hardFailures = outcomes.filter(r => r && routeOutcome(r) === 'hard')
    if (hardFailures.length > 0) {
      await agent('record hard failures to diagnosis_history', { label: 'commit-failures' })
      return { status: 'needs_diagnosis', hardFailures }
    }
  }
  const remaining = dag.nodes.filter(n => !done.has(n.node_id))
  if (pickExit(remaining, []) === 'needs_diagnosis') {
    // fix C3: stuck graph (cycle / missing dep) — synthesize a deadlock failure so the
    // /run handler always receives a non-empty hardFailures[].
    return { status: 'needs_diagnosis', hardFailures: [{
      node_id: remaining[0].node_id, outcome: 'hard_fail',
      blocking_findings: [{ type: 'deadlock',
        detail: `stuck: ${remaining.map(n => n.node_id).join(',')} unreachable (cycle or missing dep)` }]
    }] }
  }
  return { status: 'complete' }
}
// <<<ENGINE-CORE-END>>>

module.exports = {
  DAG_SCHEMA, NODE_RESULT_SCHEMA, EXPAND_SCHEMA,
  computeReady, routeOutcome, mergeExpanded, pickExit, convergenceCheck,
  serializeCommit, runNode, commitNode, runEngine
}
