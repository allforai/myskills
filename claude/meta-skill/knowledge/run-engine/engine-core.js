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
    expanders: { type: 'array', items: { type: 'string' } }
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
    verification: { type: 'object',                                  // verification-honesty: evidence of real working behavior
      properties: {
        method: { type: 'string', enum: ['real-run', 'real-test', 'real-api', 'db-query', 'screenshot', 'none'] },
        evidence_path: { type: 'string' }, // captured proof file; must EXIST for the node to count as 'verified'
        verifier: { type: 'string' },      // identity that verified — must differ from the generator
        claim: { type: 'string' }          // one line: what was proven to actually work
      } },
    summary: { type: 'string' },
    safety_warnings: { type: 'array', items: { type: 'string' } },
    acceptance_verdict: { type: 'string' }
  }
}

const EXPAND_SCHEMA = {
  type: 'object',
  required: ['new_nodes'],
  properties: { new_nodes: { type: 'array', items: { type: 'object' } } }
}

const NODE_GATE_SCHEMA = {
  type: 'object',
  required: ['node_id', 'status', 'blocking_findings'],
  properties: {
    node_id: { type: 'string' },
    status: { type: 'string', enum: ['passed', 'repair', 'hard_fail'] },
    blocking_findings: { type: 'array', items: { type: 'object' } }
  }
}

const READINESS_SCHEMA = {
  type: 'object',
  required: ['status', 'blockers'],
  properties: {
    status: { type: 'string', enum: ['ready', 'not_ready'] },
    blockers: { type: 'array', items: { type: 'object' } }
  }
}

function computeReady(nodes, done) {
  return nodes.filter(n =>
    !done.has(n.node_id) &&
    (n.hard_blocked_by || []).every(dep => done.has(dep)))
}

function routeOutcome(result) {
  if (result.outcome === 'accepted_with_gaps') return 'accepted'
  const findings = result.blocking_findings || []
  if (result.outcome === 'passed' && findings.length === 0) return 'done'
  if (result.outcome === 'hard_fail') return 'hard'
  if (findings.some(f => f.type === 'cross_node' || f.suspected_root_node)) return 'hard'
  return 'soft'
}

function mergeExpanded(nodes, newNodes) {
  const updates = new Map((newNodes || []).map(node => [node.node_id, node]))
  const merged = nodes.map(node => updates.has(node.node_id)
    ? { ...node, ...updates.get(node.node_id) }
    : node)
  const seen = new Set(nodes.map(node => node.node_id))
  return [...merged, ...(newNodes || []).filter(node => !seen.has(node.node_id))]
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

function loadDagPrompt() {
  return [
    'Read .allforai/bootstrap/workflow.json and .allforai/bootstrap/bootstrap-profile.json.',
    'Return a DAG object: nodes[] (each with node_id, capability, hard_blocked_by, alignment_refs,',
    'exit_artifacts, node_spec_path, decision_mode, decision_inputs, closure_verify, soft_retry_max,',
    'and a profile_slice carrying only the bootstrap-profile fields that node needs — tech stack,',
    'scenario, target paths); completed[] = node_ids whose transition_log status is "completed";',
    'expanders[] = the declared idempotent expander scripts.',
    'Do not execute any node. Read and summarize only.'
  ].join(' ')
}

function expandPrompt(expander) {
  return [
    `Run the project-local expander ${expander} (it mutates .allforai/bootstrap/workflow.json in place,`,
    'the existing behavior). Then return { new_nodes: [...] } listing the nodes it added',
    '(node_id, capability, hard_blocked_by, exit_artifacts, and any superset fields).',
    'Return both added and repaired nodes. Do not duplicate node IDs. The controller runs',
    'expanders again after every execution wave because new trigger artifacts may appear mid-run.'
  ].join(' ')
}

function readinessPrompt() {
  return [
    'Run python3 .allforai/bootstrap/scripts/validate_unattended_readiness.py . --write-report.',
    'Read .allforai/bootstrap/unattended-run-readiness.json. Return status "ready" only when',
    'the command succeeds and the report status is exactly "ready"; otherwise return',
    '{status:"not_ready", blockers:[...]}. Never weaken or bypass a blocker.'
  ].join(' ')
}

function gateNodePrompt(node) {
  return [
    `Run python3 .allforai/bootstrap/scripts/check_artifacts.py`,
    `.allforai/bootstrap/workflow.json --node ${node.node_id} --json.`,
    'Read the JSON, every declared exit artifact, and every validation command result.',
    'Return status "passed" only when all_exist is true and there are no unresolved gaps.',
    'Any code_gaps or test_gaps, conditional/partial/warning status, placeholder, fallback,',
    'missing side effect, or failed validation returns status "repair". Cross-node,',
    'environment, authority, or unsafe blockers return "hard_fail".'
  ].join(' ')
}

function repairPrompt(node, findings) {
  return [
    `Read ${'${CLAUDE_PLUGIN_ROOT}'}/skills/meta-orchestration/40-qa/execution-repair-loop/SKILL.md.`,
    `Repair node ${node.node_id} findings: ${JSON.stringify(findings || [])}.`,
    'Apply the generic repair loop to all code_gaps and test_gaps. Do not downgrade, waive,',
    'or hide them. Rerun affected QA evidence, but do not mark the workflow node complete;',
    'the controller will rerun the original node and its independent artifact gate.'
  ].join(' ')
}

function runNodePrompt(node, strict) {
  const di = (node.decision_inputs || [])
  const cv = (node.closure_verify || [])
  return [
    `Read and execute the node-spec at ${node.node_spec_path}.`,
    di.length ? `First read these required decision inputs: ${di.join(', ')} — if any is missing, return outcome "hard_fail".` : '',
    `Project context (profile_slice): ${JSON.stringify(node.profile_slice || {})}.`,
    'Write all exit_artifacts and run their validation_commands to self-check.',
    'Follow .allforai/bootstrap/protocols/input-freshness.md: after implementation settles, observe current inputs, register additional reads, refresh required documents and publish evidence with the actual acceptance command. Reobserve and reverify stale inputs; contract-only publication cannot prove completion.',
    cv.length ? `Additionally run closure verification for: ${cv.join(', ')}.` : '',
    'STRICTLY forbid placeholder / stub / debug-residue / pure-color placeholder outputs.',
    'VERIFICATION (epistemic honesty): if you actually exercised the real built behavior, capture',
    'external proof to a file (real run output / real API round-trip with real data / db row / screenshot)',
    'and RETURN verification: {method, evidence_path, verifier, claim}. If you only generated code',
    'without exercising it, RETURN verification.method "none" — do NOT claim verified. "Generated"',
    'must never masquerade as "verified".',
    'If you must assume an unforeseen emergent decision, pick a sensible default and RETURN it in',
    'assumed_decisions: [{id, decision, default_chosen, rationale}] — do NOT write any file yourself',
    '(the engine persists it during the serialized commit).',
    'Return a NODE_RESULT { node_id, outcome (passed|soft_fail|hard_fail), artifacts_written,',
    'blocking_findings: [{type, detail, suspected_root_node?}], assumed_decisions? }. Attach',
    'suspected_root_node when the root cause is in another node.',
    'Return safety_warnings[] for non-blocking warnings and acceptance_verdict "needs_iteration" when concept-acceptance needs another pass.',
    'Product requirements can only come from recorded user decision_inputs; an unresolved product choice is a hard failure, never an assumed decision.',
    strict || ''
  ].filter(Boolean).join(' ')
}

function commitPrompt(result) {
  const ad = result.assumed_decisions || []
  const v = result.verification || { method: 'none' }
  return [
    `Append to .allforai/bootstrap/workflow.json transition_log: node_id ${result.node_id},`,
    `status "completed", artifacts_created ${JSON.stringify(result.artifacts_written || [])},`,
    `verification ${JSON.stringify(v)}.`,
    '(verification is recorded verbatim — do NOT upgrade method or invent evidence; completeness is',
    'computed from this field by compute_completeness.py.)',
    ad.length ? `Also append these to .allforai/bootstrap/assumed-decisions.json: ${JSON.stringify(ad)}.` : '',
    'Append only; do not touch other entries.'
  ].filter(Boolean).join(' ')
}

function commitFailuresPrompt(hardFailures) {
  return [
    'Append these hard failures to .allforai/bootstrap/workflow.json diagnosis_history',
    `(failed_node + blocking_findings): ${JSON.stringify((hardFailures || []).map(h => h.node_id))}.`
  ].join(' ')
}

async function runNode(node, agent, policy = {}) {
  const max = node.soft_retry_max ?? 2
  const repairMax = node.repair_retry_max ?? 3
  let attempt = 0
  let repairAttempt = 0
  let iterationRepair = false
  let strict = ''
  while (true) {
    const r = await agent(runNodePrompt(node, strict), { schema: NODE_RESULT_SCHEMA, label: node.node_id })
    if (routeOutcome(r) === 'hard') return { ...r, outcome: 'hard_fail' }
    if ((r.safety_warnings || []).length) {
      await agent(`Record these safety warnings without asking a question: ${JSON.stringify(r.safety_warnings)}.`, { label: `safety-report:${node.node_id}` })
      if (policy.on_safety_warning !== 'continue') return { ...r, outcome: 'hard_fail',
        blocking_findings: [{ type: 'safety_warning', detail: 'Recorded Run Policy requires halt' }] }
    }
    if (r.acceptance_verdict === 'needs_iteration') {
      const event = await agent('Run python3 .allforai/bootstrap/scripts/product_intent.py . --policy-event on_needs_iteration. Return its JSON verbatim; do not ask questions.', {
        label: 'policy:on_needs_iteration', schema: { type: 'object', required: ['action'], properties: { action: { type: 'string' } } }
      })
      const action = event && event.action
      await agent('Write concept-acceptance/acceptance-report.md with the actual gaps and recorded policy action ' + action + '. ' +
        (action === 'accept' ? 'Append accepted_with_gaps to .allforai/bootstrap/assumed-decisions.json; do not mark the node completed or verified.' :
          'List fix / re-bootstrap / accept for the next interactive entry; never ask now.'), { label: `iteration-report:${node.node_id}` })
      if (action === 'accept') return { ...r, outcome: 'accepted_with_gaps' }
      if (action === 'auto_fix_once' && !iterationRepair) {
        iterationRepair = true
        await agent(repairPrompt(node, r.blocking_findings), { label: `iteration-repair:${node.node_id}` })
        strict = 'Rerun concept-acceptance and its independent verification after the one recorded repair; then stop.'
        continue
      }
      return { ...r, outcome: 'hard_fail', blocking_findings: [{ type: 'needs_iteration', detail: 'Recorded policy halted with report' }] }
    }
    const cls = routeOutcome(r)
    if (cls === 'done') {
      const gate = await agent(gateNodePrompt(node), {
        schema: NODE_GATE_SCHEMA, label: `verify:${node.node_id}`
      })
      if (!gate || gate.node_id !== node.node_id) {
        return { ...r, outcome: 'hard_fail', blocking_findings: [{
          type: 'invalid_artifact_gate', detail: 'independent artifact gate missing or mismatched'
        }] }
      }
      if (gate.status === 'passed' && (gate.blocking_findings || []).length === 0) return iterationRepair ? { ...r, iteration_repair_stopped: true } : r
      if (gate.status === 'hard_fail') {
        return { ...r, outcome: 'hard_fail', blocking_findings: gate.blocking_findings || [] }
      }
      if (repairAttempt >= repairMax) {
        return { ...r, outcome: 'hard_fail', blocking_findings: [{
          type: 'exhausted_repair_loop',
          detail: `artifact repair loop exhausted after ${repairMax} attempts`
        }] }
      }
      repairAttempt += 1
      await agent(repairPrompt(node, gate.blocking_findings), {
        label: `repair:${node.node_id}:${repairAttempt}`
      })
      strict = ` [repair ${repairAttempt}: rerun affected QA evidence; all gaps must be empty]`
      continue
    }
    if (cls === 'hard') return { ...r, outcome: 'hard_fail' }
    if (attempt >= max && (policy.on_repeated_failure !== 'continue' || attempt >= 4)) {
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
  await agent(commitPrompt(result), { label: `commit:${result.node_id}` })
  done.add(result.node_id)
}

async function runEngine({ agent, pipeline, log = () => {}, phase = () => {} }) {
  phase('Load')
  const recorded = await agent(
    'Run python3 .allforai/bootstrap/scripts/product_intent.py . --run-policy and return its JSON verbatim. ' +
    'Missing or invalid policy blocks execution; return to the interactive run entry, never ask or choose defaults here.',
    { label: 'run-policy', schema: { type: 'object', required: ['status'], properties: {
      status: { type: 'string' }, policy: { type: 'object' }
    } } })
  const policy = recorded && recorded.policy
  if (!recorded || recorded.status !== 'run_policy_ready' || !policy ||
      !['continue', 'halt'].includes(policy.on_repeated_failure) ||
      !['continue', 'halt'].includes(policy.on_safety_warning) ||
      !['halt_with_report', 'auto_fix_once', 'accept'].includes(policy.on_needs_iteration)) {
    return { status: 'needs_run_policy', hardFailures: [] }
  }
  const dag = await agent(loadDagPrompt(), { schema: DAG_SCHEMA, label: 'load-dag' })
  const done = new Set(dag.completed || [])

  phase('Execute')
  while (true) {
    phase('Expand')
    let expanded = false
    for (const exp of (dag.expanders || [])) {
      const r = await agent(expandPrompt(exp), {
        schema: EXPAND_SCHEMA, label: `expand:${exp}`
      })
      const changed = (r && r.new_nodes) || []
      dag.nodes = mergeExpanded(dag.nodes, changed)
      expanded = expanded || changed.length > 0
    }
    if (expanded) {
      const readiness = await agent(readinessPrompt(), {
        schema: READINESS_SCHEMA, label: 'validate-readiness'
      })
      if (!readiness || readiness.status !== 'ready') {
        return { status: 'needs_diagnosis', hardFailures: [{
          node_id: 'dynamic-expansion-readiness',
          outcome: 'hard_fail',
          blocking_findings: (readiness && readiness.blockers) || [{
            type: 'invalid_readiness_gate', detail: 'readiness gate missing'
          }]
        }] }
      }
    }
    phase('Execute')
    const ready = computeReady(dag.nodes, done)
    if (ready.length === 0) break
    log(`running ${ready.length} ready node(s)`)
    const outcomes = await pipeline(
      ready,
      node => runNode(node, agent, policy),
      result => routeOutcome(result) === 'done'
        ? serializeCommit(() => commitNode(result, agent, done)).then(() => result)  // fix C1: serialized
        : result,
      result => routeOutcome(result) === 'done' && !result.iteration_repair_stopped ? null : result
    )
    const hardFailures = outcomes.filter(r => r && routeOutcome(r) === 'hard')
    if (hardFailures.length > 0) {
      await agent(commitFailuresPrompt(hardFailures), { label: 'commit-failures' })
      return { status: 'needs_diagnosis', hardFailures }
    }
    if (outcomes.some(r => r && routeOutcome(r) === 'accepted')) {
      return { status: 'accepted_with_gaps', verified: false }
    }
    if (outcomes.some(result => result && result.iteration_repair_stopped)) return { status: 'iteration_repair_stopped' }
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
  DAG_SCHEMA, NODE_RESULT_SCHEMA, EXPAND_SCHEMA, NODE_GATE_SCHEMA, READINESS_SCHEMA,
  computeReady, routeOutcome, mergeExpanded, pickExit, convergenceCheck,
  serializeCommit, runNode, commitNode, runEngine,
  loadDagPrompt, expandPrompt, readinessPrompt, gateNodePrompt, repairPrompt,
  runNodePrompt, commitPrompt, commitFailuresPrompt
}
