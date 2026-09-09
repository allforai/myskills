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
    // required_repair_loops, verbatim from unattended-run-readiness-spec.json:
    // the declared route from a failed QA node to its repair node and back.
    repair_loops: { type: 'array', items: { type: 'object',
      required: ['repair_node_id'],
      properties: {
        scope: { type: 'string' },
        qa_node_ids: { type: 'array', items: { type: 'string' } },
        repair_node_id: { type: 'string' },
        closure_node_ids: { type: 'array', items: { type: 'string' } },
        max_attempts: { type: 'integer' }
      } } },
    // Repair dispatches already granted, read back from the durable transition_log so a
    // resumed run continues the same budget instead of restarting it.
    repair_attempts: { type: 'array', items: { type: 'object',
      required: ['repair_node_id', 'qa_node_id', 'attempts'],
      properties: {
        repair_node_id: { type: 'string' },
        qa_node_id: { type: 'string' },
        attempts: { type: 'integer' }
      } } }
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
    blocking_findings: { type: 'array', items: { type: 'object' } },
    // The checker's structured output, reported verbatim by the gate step. This is the
    // engine's only independent measurement: it has no filesystem of its own, so a
    // declared repair node's delivery is judged from what a separate agent read out of
    // `check_artifacts.py --json`, never from the node's own claim about itself.
    measurement: { type: 'object',
      properties: {
        withheld_by: { type: 'array', items: { type: 'string' } }, // node ids whose evidence withholds this one
        artifacts: { type: 'array', items: { type: 'object',
          properties: {
            path: { type: 'string' },
            exists: { type: 'boolean' },
            status_error: { type: 'string' },
            digest: { type: 'string' },        // sha256 of the bytes, null when unreadable
            digest_error: { type: 'string' }   // why the digest is null, when it is
          } } },
        binding_identity: { type: 'string' },  // identity of the recorded observation
        binding_kind: { type: 'string' },      // contract | evidence
        readiness_status: { type: 'string' }   // the node's current readiness
      } }
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

// The documented fallback for a loop that declares no budget at all. A declared
// budget always wins; an unusable one is never replaced by this.
// The checker's structured output on its own, for the before half of a delivery
// measurement. Same command, same independent step, no node result involved.
const MEASUREMENT_SCHEMA = {
  type: 'object',
  required: ['measurement'],
  properties: { measurement: NODE_GATE_SCHEMA.properties.measurement }
}

const DEFAULT_REPAIR_ATTEMPTS = 3

// A failure only opens a repair loop when the QA node reached its own verdict and
// published it. An infrastructure, authority or never-ran failure has no current
// report to repair against, so it stays a diagnosis case.
const NON_QA_FAILURE_TYPES = new Set([
  'invalid_artifact_gate', 'invalid_readiness_gate', 'deadlock',
  'safety_warning', 'needs_iteration', 'exhausted_retries'
])

function qaReportUsable(result) {
  if (!result || result.outcome !== 'hard_fail') return false
  const findings = result.blocking_findings || []
  if (findings.length === 0) return false
  if (findings.some(f => f && NON_QA_FAILURE_TYPES.has(f.type))) return false
  return (result.artifacts_written || []).length > 0
}

function repairLoopFor(loops, qaNodeId) {
  return (loops || []).find(loop => loop && loop.repair_node_id &&
    (loop.qa_node_ids || loop.qa_nodes || []).includes(qaNodeId)) || null
}

// null = this loop has no usable bound. An explicitly declared budget that is not a
// positive integer is a planning error, not a request for the default: falling back
// there would grant attempts the plan never authorized, so the loop routes nothing.
// `validate_unattended_readiness.py` blocks the same shape before /run starts.
function repairBudget(loop) {
  if (!loop || loop.max_attempts === undefined) return DEFAULT_REPAIR_ATTEMPTS
  const declared = loop.max_attempts
  return Number.isInteger(declared) && declared > 0 ? declared : null
}

// repair: { loops: declared required_repair_loops, open: Map<qa_node_id, loop> }.
// `open` holds the QA failures currently routed to their declared repair node.
function computeReady(nodes, done, repair) {
  const loops = (repair && repair.loops) || []
  const open = (repair && repair.open instanceof Map) ? repair.open : new Map()
  // Closure never starts on a repair alone: every QA node of its loop must itself
  // have completed, so a rerun QA pass is the only way past a declared loop.
  const closureBlocked = new Set()
  for (const loop of loops) {
    if (!loop) continue
    const qaOpen = (loop.qa_node_ids || loop.qa_nodes || []).some(qa => !done.has(qa))
    if (!qaOpen) continue
    for (const closure of (loop.closure_node_ids || loop.closure_nodes || [])) closureBlocked.add(closure)
  }
  return nodes.filter(n => {
    if (done.has(n.node_id)) return false
    if (open.has(n.node_id)) return false          // the QA node waits for its declared repair
    if (closureBlocked.has(n.node_id)) return false
    return (n.hard_blocked_by || []).every(dep => {
      if (done.has(dep)) return true
      const loop = open.get(dep)                   // only the declared repair node may
      return Boolean(loop) && loop.repair_node_id === n.node_id  // proceed on a failed QA dep
    })
  })
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
    'Also read .allforai/bootstrap/unattended-run-readiness-spec.json and return its',
    'required_repair_loops verbatim as repair_loops[] (each with qa_node_ids, repair_node_id,',
    'closure_node_ids, max_attempts); return [] when the spec declares none.',
    'Also return repair_attempts[] = one {repair_node_id, qa_node_id, attempts} per declared',
    'qa_node_id, where attempts is the number of transition_log entries for that QA node with',
    'status "failed" — the repair dispatches this run already granted it. Count them; do not',
    'estimate, and return 0 only when the log truly holds none.',
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
    'environment, authority, or unsafe blockers return "hard_fail".',
    'Also return measurement: {artifacts: the checker\'s artifacts[] verbatim (path, exists,',
    'status_error, digest, digest_error), binding_identity, binding_kind and readiness_status',
    'copied from the checker\'s freshness object, and withheld_by: the node ids it reports',
    'this node as waiting on (freshness.diff.upstream)}. Report what the command printed; do',
    'not compute, infer or fill in any of it yourself, and omit a field it did not print.'
  ].join(' ')
}

function measurePrompt(node) {
  return [
    `Run python3 .allforai/bootstrap/scripts/check_artifacts.py`,
    `.allforai/bootstrap/workflow.json --node ${node.node_id} --json.`,
    'Return only measurement: {artifacts: the artifacts[] it printed verbatim (path, exists,',
    'status_error, digest, digest_error), binding_identity, binding_kind and readiness_status',
    'copied from the freshness object it printed, and withheld_by: the node ids it reports',
    'this node as waiting on (freshness.diff.upstream)}.',
    'Do not run the node, do not change anything, and do not compute, infer or fill in any',
    'field the command did not print.'
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

function repairRoutePrompt(qaNodeId, loop, attempt) {
  return [
    `Append a failed transition for ${qaNodeId} to .allforai/bootstrap/workflow.json transition_log`,
    `with error "QA failed; routed to declared repair node ${loop.repair_node_id}`,
    `(attempt ${attempt} of ${repairBudget(loop)})".`,
    'Do NOT mark the QA node completed and do not edit its report: the declared repair node runs',
    'next, this QA node then reruns, and no closure node of this loop may start until that rerun',
    'passes. Append only; do not touch other entries.'
  ].join(' ')
}

function commitFailuresPrompt(hardFailures) {
  return [
    'Append these hard failures to .allforai/bootstrap/workflow.json diagnosis_history',
    `(failed_node + blocking_findings): ${JSON.stringify((hardFailures || []).map(h => h.node_id))}.`
  ].join(' ')
}

// A delivery has to be measured, not asserted. The engine holds no filesystem, so every
// fact below comes from the gate step reading `check_artifacts.py --json`; the node's own
// NODE_RESULT is never the evidence. Fails closed: a measurement that is absent, that does
// not cover every declared exit artifact, that reports one missing or carrying a status
// error, or that does not name the loop's own QA node as the sole reason the gate withheld
// this node, is not a delivery.
function measuredDelivery(node, gate, open) {
  const m = gate && gate.measurement
  if (!m || !Array.isArray(m.artifacts) || !Array.isArray(m.withheld_by)) return null
  const declared = (node.exit_artifacts || []).map(a => (a && a.path) || a).filter(Boolean)
  if (declared.length === 0) return null
  const measured = new Map(m.artifacts.filter(a => a && a.path).map(a => [a.path, a]))
  for (const rel of declared) {
    const entry = measured.get(rel)
    if (!entry || entry.exists !== true || entry.status_error) return null
  }
  // The gate must be withholding this node for the loop's own reason and nothing else.
  const expected = new Set((open && open.qa) || [])
  if (m.withheld_by.length === 0 || !m.withheld_by.every(id => expected.has(id))) return null
  // A digest is always printed for a readable file inside the project, so a null one means
  // missing, outside the project root, or unreadable — never a delivery, whatever `exists`
  // says about a symlink.
  if (declared.some(rel => !measured.get(rel).digest)) return null
  // Content identity and input binding answer different questions and both are required:
  // the bytes moved, and they were judged against inputs that are current now. A digest
  // alone cannot establish a rebinding after a source change.
  if (!m.binding_identity) return null
  if (m.readiness_status !== 'valid') return null
  // Measured across the attempt, by the same independent step: something the attempt wrote
  // has to differ from what was there before it ran. A pre-existing or touched artifact is
  // not a delivery.
  const before = open && open.before
  if (!before || !Array.isArray(before.artifacts)) return null
  if (before.binding_identity !== m.binding_identity) return null   // inputs moved mid-attempt
  const wasThere = new Map(before.artifacts.filter(a => a && a.path).map(a => [a.path, a.digest]))
  const produced = declared.filter(rel => wasThere.get(rel) !== measured.get(rel).digest)
  if (produced.length === 0) return null
  return { binding_identity: m.binding_identity,
           produced: Object.fromEntries(produced.map(rel => [rel, measured.get(rel).digest])) }
}

// deliveryOnly: this node is the declared repair node of a currently open loop. Its
// independent gate cannot pass yet — it is `hard_blocked_by` the QA node it repairs, so
// while that node is failing the repair node's own evidence is stale and the gate
// withholds it by construction. Retrying inside the node would burn the artifact repair
// budget against something no repair can fix. Its delivery closes the loop instead, the
// QA rerun is the check, and the node is dispatched again afterwards as an ordinary node
// and must pass this same gate on its own merits before anything commits it.
async function runNode(node, agent, policy = {}, deliveryOnly = null) {
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
      // A withheld gate on an open loop's repair node is the expected state, not a gap to
      // retry. An environment, authority or cross-node blocker is still a hard failure
      // above, so this defers nothing that a repair could have fixed — and the delivery
      // itself must be measured by the gate step before it counts.
      if (deliveryOnly) {
        const delivery = measuredDelivery(node, gate, deliveryOnly)
        if (delivery) return { ...r, delivered: true, delivery, gate_findings: gate.blocking_findings || [] }
        return { ...r, outcome: 'hard_fail', blocking_findings: [{
          type: 'unmeasured_repair_delivery',
          detail: 'the gate did not measure this repair as having delivered its declared exit ' +
                  'artifacts, bound to an input snapshot, withheld only by its own QA node'
        }] }
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
  const repair = { loops: dag.repair_loops || [], open: new Map() }
  // `${repair_node_id}::${qa_node_id}` -> repair dispatches already granted to that QA node.
  // Keyed by the pair because one repair node may serve several QA nodes and each carries
  // its own declared budget; seeded from the recorded history so a restart resumes it.
  const repairAttempts = new Map()
  const recordedAttempts = dag.repair_attempts === undefined ? [] : dag.repair_attempts
  if (!Array.isArray(recordedAttempts)) {
    return { status: 'needs_diagnosis', hardFailures: [{
      node_id: 'repair-attempt-history', outcome: 'hard_fail',
      blocking_findings: [{ type: 'invalid_repair_attempt_history',
        detail: 'repair_attempts is not an array; the spent budget cannot be read' }] }] }
  }
  for (const entry of recordedAttempts) {
    // Unreadable history means the remaining budget is unknown. Restarting it would hand
    // out attempts the plan already spent, so the run stops instead.
    if (!entry || !entry.repair_node_id || !entry.qa_node_id ||
        !Number.isInteger(entry.attempts) || entry.attempts < 0) {
      return { status: 'needs_diagnosis', hardFailures: [{
        node_id: 'repair-attempt-history', outcome: 'hard_fail',
        blocking_findings: [{ type: 'invalid_repair_attempt_history',
          detail: `unreadable recorded repair attempts: ${JSON.stringify(entry)}` }] }] }
    }
    repairAttempts.set(`${entry.repair_node_id}::${entry.qa_node_id}`, entry.attempts)
  }
  // Every declared QA node must state its attempts, explicit 0 included. An absent
  // entry is missing history, not a fresh budget: assuming zero would silently hand a
  // resumed run the attempts it already spent.
  for (const loop of repair.loops) {
    for (const qaNodeId of ((loop && (loop.qa_node_ids || loop.qa_nodes)) || [])) {
      if (repairAttempts.has(`${loop.repair_node_id}::${qaNodeId}`)) continue
      return { status: 'needs_diagnosis', hardFailures: [{
        node_id: 'repair-attempt-history', outcome: 'hard_fail',
        blocking_findings: [{ type: 'invalid_repair_attempt_history',
          detail: `no recorded repair attempts for QA node ${qaNodeId} of loop ${loop.repair_node_id}` }] }] }
    }
  }

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
    // A repair node that already ran for an earlier attempt must run again for this one.
    for (const loop of repair.open.values()) done.delete(loop.repair_node_id)
    const ready = computeReady(dag.nodes, done, repair)
    if (ready.length === 0) break
    log(`running ${ready.length} ready node(s)`)
    // repair_node_id -> the QA node ids whose failure it is answering right now.
    const openRepairNodes = new Map()
    for (const [qaNodeId, loop] of repair.open) {
      const seen = openRepairNodes.get(loop.repair_node_id) || []
      openRepairNodes.set(loop.repair_node_id, [...seen, qaNodeId])
    }
    // The before half of the delivery measurement, taken by the same independent step
    // before the node runs. Without it a delivery cannot be measured and is refused.
    const openDelivery = new Map()
    for (const [repairNodeId, qaIds] of openRepairNodes) {
      const node = ready.find(n => n.node_id === repairNodeId)
      if (!node) continue
      const before = await agent(measurePrompt(node), {
        schema: MEASUREMENT_SCHEMA, label: `measure:${repairNodeId}`
      })
      openDelivery.set(repairNodeId, { qa: qaIds, before: (before && before.measurement) || null })
    }
    const outcomes = await pipeline(
      ready,
      node => runNode(node, agent, policy, openDelivery.get(node.node_id) || null),
      // A delivery is not a completion: it never commits, so the repair node stays out of
      // `done` and must still pass its own gate later.
      result => routeOutcome(result) === 'done' && !result.delivered
        ? serializeCommit(() => commitNode(result, agent, done)).then(() => result)  // fix C1: serialized
        : result,
      result => routeOutcome(result) === 'done' && !result.iteration_repair_stopped && !result.delivered
        ? null : result
    )
    // A repair node that delivered or completed this wave closes its loop; the QA node
    // reruns next, and that rerun — not the delivery — is what releases closure.
    const delivered = new Set(outcomes.filter(r => r && r.delivered).map(r => r.node_id))
    for (const [qaNodeId, loop] of [...repair.open]) {
      if (done.has(loop.repair_node_id) || delivered.has(loop.repair_node_id)) repair.open.delete(qaNodeId)
    }
    const hardFailures = outcomes.filter(r => r && routeOutcome(r) === 'hard')
    if (hardFailures.length > 0) {
      const routed = []
      for (const failure of hardFailures) {
        const loop = repairLoopFor(repair.loops, failure.node_id)
        if (!loop || !qaReportUsable(failure)) continue
        const budget = repairBudget(loop)
        if (budget === null) continue          // unusable declared budget: route nothing
        const key = `${loop.repair_node_id}::${failure.node_id}`
        const spent = repairAttempts.get(key) || 0
        if (spent >= budget) continue
        repairAttempts.set(key, spent + 1)
        repair.open.set(failure.node_id, loop)
        await agent(repairRoutePrompt(failure.node_id, loop, spent + 1), {
          label: `repair-route:${failure.node_id}:${spent + 1}`
        })
        routed.push(failure.node_id)
      }
      // Every failure must be a declared, budgeted, report-backed QA failure to
      // continue; anything else is a real stop.
      if (routed.length !== hardFailures.length) {
        for (const qaNodeId of routed) repair.open.delete(qaNodeId)
        await agent(commitFailuresPrompt(hardFailures), { label: 'commit-failures' })
        return { status: 'needs_diagnosis', hardFailures }
      }
    }
    // Checked after routing, never instead of it: a repair opened for one node cannot
    // absorb another node's terminal verdict. Both are recorded Run Policy outcomes and
    // neither node is ever re-run into a passing verdict, so neither may become complete.
    if (outcomes.some(r => r && routeOutcome(r) === 'accepted')) {
      return { status: 'accepted_with_gaps', verified: false }
    }
    if (outcomes.some(result => result && result.iteration_repair_stopped)) return { status: 'iteration_repair_stopped' }
  }
  const remaining = dag.nodes.filter(n => !done.has(n.node_id))
  if (remaining.length > 0 && repair.open.size > 0) {
    // The repair budget is spent and the QA node still has not passed.
    const hardFailures = [...repair.open].map(([qaNodeId, loop]) => ({
      node_id: qaNodeId, outcome: 'hard_fail',
      blocking_findings: [{ type: 'exhausted_repair_loop',
        detail: `declared repair loop ${loop.repair_node_id} exhausted after ${repairBudget(loop)} attempts` }]
    }))
    await agent(commitFailuresPrompt(hardFailures), { label: 'commit-failures' })
    return { status: 'needs_diagnosis', hardFailures }
  }
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
  MEASUREMENT_SCHEMA, measuredDelivery, measurePrompt,
  computeReady, routeOutcome, mergeExpanded, pickExit, convergenceCheck,
  qaReportUsable, repairLoopFor, repairBudget,
  serializeCommit, runNode, commitNode, runEngine,
  loadDagPrompt, expandPrompt, readinessPrompt, gateNodePrompt, repairPrompt,
  runNodePrompt, commitPrompt, commitFailuresPrompt, repairRoutePrompt
}
