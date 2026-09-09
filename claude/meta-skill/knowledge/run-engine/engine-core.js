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
      } } }
  }
}

// One verdict from the canonical repair-authorization ledger. The helper decides; this
// schema only says what a verdict looks like so a receipt can be checked rather than
// believed. `status` is the whole answer — everything else is evidence for it.
const LEDGER_VERDICT_SCHEMA = {
  type: 'object',
  required: ['status'],
  properties: {
    status: { type: 'string' },
    reason: { type: 'string' },
    untrusted: { type: 'string' },
    run_id: { type: 'string' },
    origin: { type: 'string' },
    authorization_id: { type: 'string' },
    repair_node_id: { type: 'string' },
    state: { type: 'string' },
    outcome: { type: 'string' },
    execution_allowed: { type: 'boolean' },
    replayed: { type: 'boolean' },
    refunded: { type: 'boolean' },
    charged: { type: 'object' },
    remaining: { type: 'object' },
    obligations: { type: 'array' },
    unresolved: { type: 'array' }
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
    'Do NOT report repair budgets here. The spent budget is not summarized from workflow.json:',
    'it is read from the canonical repair-authorization ledger by its own helper, because a',
    'count inferred by reading a file is not accounting.',
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
    'passes. Append only; do not touch other entries, and do not write the repair_routes entry',
    'here — that is appended separately, immediately before the repair node is dispatched.'
  ].join(' ')
}

// Single-quote a value for a POSIX shell command line embedded in a prompt.
function shellQuote(value) {
  return "'" + String(value).replace(/'/g, "'\\''") + "'"
}

// Every ledger operation is one run of the canonical helper. This engine has no
// filesystem of its own — its only actuator is an agent — so the accounting is not
// something it can do: it is something it asks a deterministic Python CLI to do and then
// checks the receipt of. The prompt therefore carries the exact command and forbids the
// agent from producing a verdict any other way. A verdict that was written rather than
// executed is a forged receipt, and the caller below refuses one.
function authorizationPrompt(request) {
  return [
    'Run EXACTLY this command, once, and return its stdout parsed as your JSON result:',
    `printf '%s' ${shellQuote(JSON.stringify(request))} | python3 .allforai/bootstrap/scripts/repair_authorization.py .`,
    'This is the canonical repair-authorization ledger at',
    '.allforai/bootstrap/repair-authorizations.json. Return the verdict object exactly as the',
    'command printed it. Do NOT invent, summarize, complete, correct or re-order it; do NOT',
    'edit the ledger file by hand; do NOT re-run the command with different input; do NOT',
    'retry a refusal. A refusal exits non-zero and still prints a verdict — that verdict is',
    'the answer, so return it. Only if the command cannot be run at all, return',
    '{"status": "invalid", "reason": "<what actually happened>"}.'
  ].join(' ')
}

// The dispatch identity. Durable and unique: it is derived from the run, the repair node
// and each obligation's spend at the moment the dispatch was decided, so a driver that
// dies and restarts recomputes the same id and the helper recognises the replay instead
// of charging a second attempt. A new attempt always has a different prior spend, so it
// always gets a different id.
// A run identity that is stable across restarts of the same plan, so a resumed run finds
// its own ledger instead of a foreign one. Derived from the declared graph rather than a
// clock or a random source, both of which would make every restart a different run — and
// the helper refuses a second identity over an existing ledger, which is what keeps a
// silent reset impossible.
function runIdentity(dag) {
  const shape = JSON.stringify({
    nodes: (dag.nodes || []).map(n => n && n.node_id).filter(Boolean).sort(),
    loops: (dag.repair_loops || []).map(l => ({
      repair_node_id: l && l.repair_node_id,
      qa_node_ids: [...((l && (l.qa_node_ids || l.qa_nodes)) || [])].sort(),
      max_attempts: l && l.max_attempts
    })).sort((a, b) => String(a.repair_node_id).localeCompare(String(b.repair_node_id)))
  })
  let hash = 2166136261
  for (let i = 0; i < shape.length; i++) {
    hash ^= shape.charCodeAt(i)
    hash = Math.imul(hash, 16777619) >>> 0
  }
  return `run-${hash.toString(16).padStart(8, '0')}`
}

function authorizationId(runId, repairNodeId, priorSpent) {
  const parts = Object.keys(priorSpent).sort().map(qa => `${qa}#${priorSpent[qa]}`)
  return `${runId}::${repairNodeId}::${parts.join(',')}`
}

// A receipt is checked, never believed. The helper's own verdict is the only evidence
// that a charge or a launch claim is durable, so a verdict that names another dispatch,
// omits its identity, or answers a question that was not asked is refused exactly like a
// refusal — nothing may execute on it.
function ledgerReceiptError(verdict, expect) {
  if (!verdict || typeof verdict !== 'object') return 'the ledger helper returned no verdict'
  if (verdict.status !== expect.status) {
    return `ledger refused ${expect.operation}: ${verdict.status}` +
      (verdict.untrusted ? ` (${verdict.untrusted})` : '') +
      (verdict.reason ? ` — ${verdict.reason}` : '')
  }
  if (expect.authorization_id !== undefined && verdict.authorization_id !== expect.authorization_id) {
    return `receipt names authorization ${JSON.stringify(verdict.authorization_id)}, not ${JSON.stringify(expect.authorization_id)}`
  }
  if (expect.repair_node_id !== undefined && verdict.repair_node_id !== undefined &&
      verdict.repair_node_id !== expect.repair_node_id) {
    return `receipt names repair node ${JSON.stringify(verdict.repair_node_id)}, not ${JSON.stringify(expect.repair_node_id)}`
  }
  if (expect.execution_allowed !== undefined && verdict.execution_allowed !== expect.execution_allowed) {
    return `receipt reports execution_allowed ${JSON.stringify(verdict.execution_allowed)}, expected ${JSON.stringify(expect.execution_allowed)}`
  }
  return null
}

function ledgerBlocker(nodeId, detail) {
  return { status: 'needs_diagnosis', hardFailures: [{
    node_id: nodeId, outcome: 'hard_fail', artifacts_written: [],
    blocking_findings: [{ type: 'invalid_repair_authorization', detail }] }] }
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
    if (!r || r.node_id !== node.node_id) {
      return { node_id: node.node_id, outcome: 'hard_fail', artifacts_written: [],
        blocking_findings: [{ type: 'invalid_artifact_gate', detail: 'executor result missing or names a different node' }] }
    }
    if ((r.safety_warnings || []).length) {
      await agent(`Record these safety warnings without asking a question: ${JSON.stringify(r.safety_warnings)}.`, { label: `safety-report:${node.node_id}` })
      if (policy.on_safety_warning !== 'continue') return { ...r, outcome: 'hard_fail',
        blocking_findings: [{ type: 'safety_warning', detail: 'Recorded Run Policy requires halt' }] }
    }
    if (routeOutcome(r) === 'hard') return { ...r, outcome: 'hard_fail' }
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
  const blockedFailures = new Map()
  // `${repair_node_id}::${qa_node_id}` -> repair dispatches already granted to that QA node.
  // Keyed by the pair because one repair node may serve several QA nodes and each carries
  // its own declared budget; seeded from the recorded history so a restart resumes it.
  const repairAttempts = new Map()
  let ledgerRunId = null
  if (repair.loops.length > 0) {
    // Consumption first. The canonical ledger is the authority on what every obligation
    // has spent, and — unlike a count summarized out of workflow.json — an obligation it
    // does not list really has spent nothing, because the ledger's own origin was proved
    // when it was created. That proof is why absence may be read as zero here and could
    // not be before.
    let consumption = await agent(authorizationPrompt({ operation: 'consumption' }),
      { schema: LEDGER_VERDICT_SCHEMA, label: 'ledger:consumption' })
    if (consumption && consumption.status === 'blocked' && consumption.untrusted === 'missing_ledger') {
      // The only path to a fresh budget, and this engine does not assert it: the helper
      // reads workflow.json itself and refuses to record zero for a run that already
      // shows execution. Any other refusal — an unreadable ledger, a foreign run, an
      // ambiguous history — is untrusted state and stops the run right here.
      const started = await agent(
        authorizationPrompt({ operation: 'initialize', run_id: runIdentity(dag) }),
        { schema: LEDGER_VERDICT_SCHEMA, label: 'ledger:initialize' })
      const refused = ledgerReceiptError(started, { status: 'ok', operation: 'initialize' })
      if (refused) return ledgerBlocker('repair-authorization-ledger', refused)
      consumption = await agent(authorizationPrompt({ operation: 'consumption' }),
        { schema: LEDGER_VERDICT_SCHEMA, label: 'ledger:consumption' })
    }
    const refused = ledgerReceiptError(consumption, { status: 'ok', operation: 'consumption' })
    if (refused) return ledgerBlocker('repair-authorization-ledger', refused)
    if (typeof consumption.run_id !== 'string' || !consumption.run_id) {
      return ledgerBlocker('repair-authorization-ledger',
        'the ledger reported no run identity; its consumption cannot be attributed to this run')
    }
    ledgerRunId = consumption.run_id
    // A grant that never reached an outcome leaves it unknown whether that attempt ran.
    // Resuming would either replay uncertain work or spend a budget twice, so the run
    // stops for reconciliation rather than guessing which (ADR 0006).
    const unresolved = consumption.unresolved === undefined ? [] : consumption.unresolved
    if (!Array.isArray(unresolved)) {
      return ledgerBlocker('repair-authorization-ledger',
        'the ledger did not report its unresolved authorizations')
    }
    if (unresolved.length > 0) {
      return ledgerBlocker('repair-authorization-ledger',
        `unresolved repair authorization(s) ${JSON.stringify(unresolved.map(u => u && u.authorization_id))}: ` +
        'whether their execution occurred is unknown. Reconcile them against evidence before ' +
        'resuming — this run neither replays nor refunds them')
    }
    for (const record of (consumption.obligations || [])) {
      if (!record || typeof record.repair_node_id !== 'string' || typeof record.qa_node_id !== 'string' ||
          !Number.isInteger(record.spent) || record.spent < 0) {
        return ledgerBlocker('repair-authorization-ledger',
          `unreadable ledger obligation: ${JSON.stringify(record)}`)
      }
      repairAttempts.set(`${record.repair_node_id}::${record.qa_node_id}`, record.spent)
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
    const funded = (qa, loop) => repairBudget(loop) !== null &&
      (repairAttempts.get(`${loop.repair_node_id}::${qa}`) || 0) < repairBudget(loop)
    // A node may repair one loop and owe a QA obligation in another; ADR 0006 keeps that
    // shape supported. What it does not allow is the repair hat settling the obligation.
    // A node whose own obligation has nothing left to fix it is blocked in every role: a
    // repairer may not accept its own work, and dispatching it here would let it write the
    // very verdict it owes — on a budget authorized against a different loop.
    const unfundedObligation = nodeId => repair.loops.some(loop => {
      const qaIds = (loop && (loop.qa_node_ids || loop.qa_nodes)) || []
      if (!qaIds.includes(nodeId) || done.has(nodeId)) return false
      const budget = repairBudget(loop)
      return budget === null ||
        (repairAttempts.get(`${loop.repair_node_id}::${nodeId}`) || 0) >= budget
    })
    const ready = computeReady(dag.nodes, done, repair).filter(node => {
      if (blockedFailures.has(node.node_id)) return false
      if (repair.open.has(node.node_id) && unfundedObligation(node.node_id)) return false
      const obligations = [...repair.open].filter(([, loop]) => loop.repair_node_id === node.node_id)
      return obligations.length === 0 || obligations.some(([qa, loop]) => funded(qa, loop))
    })
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
      // Charge every QA node this dispatch answers before anything else the dispatch
      // does. The declared budget is per QA node, so one repair node serving several
      // spends one attempt of each; a sibling is never charged for another's failure, and
      // an exhausted one is left out of the grant entirely rather than charged again.
      const authorizedQa = qaIds.filter(qa => funded(qa, repair.open.get(qa))).sort()
      if (authorizedQa.length === 0) {
        // Unreachable while the `ready` filter holds, and a stop rather than a skip if it
        // ever stops holding: a repair attempt that reaches the executor without a grant
        // is exactly the unpaid dispatch the ledger exists to prevent.
        return ledgerBlocker(repairNodeId,
          'no obligation of this dispatch has budget left; a repair attempt may not run unpaid')
      }
      const priorSpent = {}
      const budgets = {}
      for (const qaNodeId of authorizedQa) {
        priorSpent[qaNodeId] = repairAttempts.get(`${repairNodeId}::${qaNodeId}`) || 0
        budgets[qaNodeId] = repairBudget(repair.open.get(qaNodeId))
      }
      const grantId = authorizationId(ledgerRunId, repairNodeId, priorSpent)
      // One atomic grant for the whole dispatch: every obligation is charged or none is,
      // so a partial charge can never leave a sibling paying for an attempt that was
      // never authorized. It is still not permission to run.
      const granted = await agent(authorizationPrompt({
        operation: 'authorize', run_id: ledgerRunId, authorization_id: grantId,
        repair_node_id: repairNodeId, obligations: authorizedQa, budgets,
        provenance: { host: 'claude-run-engine' }
      }), { schema: LEDGER_VERDICT_SCHEMA, label: `repair-authorize:${repairNodeId}` })
      const grantError = ledgerReceiptError(granted, { status: 'authorized', operation: 'authorize',
        authorization_id: grantId, repair_node_id: repairNodeId, execution_allowed: false })
      if (grantError) return ledgerBlocker(repairNodeId, grantError)
      // The charge is authoritative, not this engine's arithmetic.
      for (const qaNodeId of authorizedQa) {
        const charged = granted.charged && granted.charged[qaNodeId]
        if (!Number.isInteger(charged) || charged !== priorSpent[qaNodeId] + 1) {
          return ledgerBlocker(repairNodeId,
            `receipt charged ${JSON.stringify(charged)} to ${qaNodeId}, expected ${priorSpent[qaNodeId] + 1}`)
        }
        repairAttempts.set(`${repairNodeId}::${qaNodeId}`, charged)
      }
      // The launch claim is separate and succeeds once. A replay, a resumed engine and a
      // second worker are all told no, so nothing executes twice on one charge.
      const claimed = await agent(authorizationPrompt({
        operation: 'start', run_id: ledgerRunId, authorization_id: grantId
      }), { schema: LEDGER_VERDICT_SCHEMA, label: `repair-start:${repairNodeId}` })
      const claimError = ledgerReceiptError(claimed, { status: 'started', operation: 'start',
        authorization_id: grantId, execution_allowed: true })
      if (claimError) return ledgerBlocker(repairNodeId, claimError)
      const before = await agent(measurePrompt(node), {
        schema: MEASUREMENT_SCHEMA, label: `measure:${repairNodeId}`
      })
      openDelivery.set(repairNodeId, { qa: qaIds, authorized_qa: authorizedQa,
        authorization_id: grantId, before: (before && before.measurement) || null })
    }
    // Workflow pipelines have no stage barrier. Hold every completion until all
    // in-flight results are known, otherwise a late safety halt can follow a sibling's
    // already-published completion. The latch also fences further retries/gates.
    let safetyHalted = false
    const waveAgent = async (prompt, opts = {}) => {
      if (safetyHalted && !(opts.label || '').startsWith('safety-report:')) {
        throw new Error('run safety halt prohibits further agent dispatch')
      }
      const result = await agent(prompt, opts)
      if (result && ((policy.on_safety_warning !== 'continue' && (result.safety_warnings || []).length) ||
          (result.blocking_findings || []).some(f => f && f.type === 'safety_warning'))) safetyHalted = true
      return result
    }
    const outcomes = await pipeline(ready, async node => {
      try {
        return await runNode(node, waveAgent, policy, openDelivery.get(node.node_id) || null)
      } catch (error) {
        // A thrown stage is otherwise swallowed by Workflow as null. Unknown execution
        // is a blocker, never absence of a failure or permission to repeat the node.
        // `execution_unknown` is what stops the settlement below: this engine did not
        // observe how the attempt ended, so its authorization stays unresolved rather
        // than being recorded as a delivery or a failure it cannot vouch for.
        return { node_id: node.node_id, outcome: 'hard_fail', artifacts_written: [],
          execution_unknown: true,
          blocking_findings: [{ type: safetyHalted ? 'safety_warning' : 'invalid_artifact_gate',
            detail: safetyHalted ? 'in-flight result quarantined after run safety halt' : 'node execution did not return a usable result' }] }
      }
    })
    if (safetyHalted) {
      const hardFailures = outcomes.filter(r => r && routeOutcome(r) === 'hard')
      const quotedNodes = "'" + JSON.stringify(ready.map(n => n.node_id)).replace(/'/g, "'\\''") + "'"
      const quarantine = await agent('Run python3 .allforai/bootstrap/scripts/run_safety.py . --nodes-json ' +
        quotedNodes + " --reason 'Recorded Run Policy requires a run-wide safety halt'. " +
        'Return its JSON verbatim. Do not invent a persistence receipt, delete artifacts, mark nodes complete, or clear the halt.',
        { label: 'quarantine-wave', schema: { type: 'object', required: ['status'], properties: {
          status: { type: 'string' }, node_ids: { type: 'array', items: { type: 'string' } }
        } } })
      if (!quarantine || quarantine.status !== 'quarantined' || !Array.isArray(quarantine.node_ids) ||
          ready.some(n => !quarantine.node_ids.includes(n.node_id))) {
        hardFailures.push({ node_id: 'safety-quarantine', outcome: 'hard_fail', artifacts_written: [],
          blocking_findings: [{ type: 'invalid_readiness_gate', detail: 'safety quarantine persistence was not confirmed' }] })
      }
      await agent(commitFailuresPrompt(hardFailures), { label: 'commit-failures' })
      // Deliberately not settled. The wave's outputs are quarantined pending independent
      // revalidation, so whether those attempts delivered anything is not this engine's
      // to record; the grants stay unresolved and the next run stops for reconciliation.
      return { status: 'needs_diagnosis', hardFailures }
    }
    // Settle only what this engine actually watched end. Settling returns no budget — the
    // attempt was granted, so it is spent either way — it only removes the uncertainty
    // about whether the attempt ran. An unknown outcome is left unresolved on purpose:
    // guessing would either replay uncertain work or refund an attempt already spent.
    for (const [repairNodeId, grant] of openDelivery) {
      if (!grant || !grant.authorization_id) continue
      const result = outcomes.find(r => r && r.node_id === repairNodeId)
      if (!result || result.execution_unknown) continue
      const outcome = (result.delivered || routeOutcome(result) === 'done') ? 'delivered' : 'failed'
      const settled = await agent(authorizationPrompt({
        operation: 'settle', authorization_id: grant.authorization_id, outcome
      }), { schema: LEDGER_VERDICT_SCHEMA, label: `repair-settle:${repairNodeId}` })
      const settleError = ledgerReceiptError(settled, { status: 'settled', operation: 'settle',
        authorization_id: grant.authorization_id })
      if (settleError) return ledgerBlocker(repairNodeId, settleError)
    }
    // A delivery is not a completion. Serialize actual completions only after the
    // safety barrier; the independent QA must still judge a repair delivery.
    for (const result of outcomes) {
      if (result && routeOutcome(result) === 'done' && !result.delivered) {
        await serializeCommit(() => commitNode(result, agent, done))
      }
    }
    // A repair node that delivered or completed this wave closes its loop; the QA node
    // reruns next, and that rerun — not the delivery — is what releases closure.
    const delivered = new Set(outcomes.filter(r => r && r.delivered).map(r => r.node_id))
    for (const [qaNodeId, loop] of [...repair.open]) {
      const grant = openDelivery.get(loop.repair_node_id)
      if (grant && grant.authorized_qa.includes(qaNodeId) &&
          (done.has(loop.repair_node_id) || delivered.has(loop.repair_node_id))) repair.open.delete(qaNodeId)
    }
    const hardFailures = outcomes.filter(r => r && routeOutcome(r) === 'hard')
    if (hardFailures.length > 0) {
      // A declared repair node that failed inside its own still-open loop is not a
      // terminal verdict while that loop has budget left. Its attempt was already charged
      // before it ran, so the loop simply dispatches the next one; a repair that errors or
      // delivers nothing is bounded by the declared max_attempts exactly like one that
      // delivered and did not fix the finding. When the budget is gone it is retained no
      // longer and stops the run with its own findings.
      //
      // NON_QA_FAILURE_TYPES are the exception, and the same reason applies as when a QA
      // node carries them: they are structural, environmental or policy verdicts, not an
      // attempt that fell short. A recorded safety halt or a broken readiness gate is not
      // made truer by dispatching it again, so it stops the run now.
      const retained = hardFailures.filter(failure => {
        if ((failure.blocking_findings || []).some(f => f && NON_QA_FAILURE_TYPES.has(f.type))) return false
        // Its repair role does not answer its own obligation. A node that owes a QA
        // obligation with no attempt left to fix it is blocked, not retained, however
        // funded the loop it repairs still is (ADR 0005, ADR 0006).
        if (unfundedObligation(failure.node_id)) return false
        return [...repair.open].some(([qa, loop]) => {
          if (!loop || loop.repair_node_id !== failure.node_id) return false
          const budget = repairBudget(loop)
          return budget !== null && (repairAttempts.get(`${loop.repair_node_id}::${qa}`) || 0) < budget
        })
      })
      const routed = []
      for (const failure of hardFailures) {
        const loop = repairLoopFor(repair.loops, failure.node_id)
        if (!loop || !qaReportUsable(failure)) continue
        const budget = repairBudget(loop)
        if (budget === null) continue          // unusable declared budget: route nothing
        const key = `${loop.repair_node_id}::${failure.node_id}`
        // Peek, never charge: the attempt is spent when the repair is dispatched, so a
        // route that opens and is then interrupted before any dispatch costs nothing.
        const spent = repairAttempts.get(key) || 0
        if (spent >= budget) continue
        repair.open.set(failure.node_id, loop)
        await agent(repairRoutePrompt(failure.node_id, loop, spent + 1), {
          label: `repair-route:${failure.node_id}:${spent + 1}`
        })
        routed.push(failure.node_id)
      }
      // Every failure must be a declared, budgeted, report-backed QA failure, or a repair
      // node still inside its own funded loop, to continue; anything else is a real stop.
      const handled = new Set([...routed, ...retained.map(f => f.node_id)])
      const unhandled = hardFailures.filter(f => !handled.has(f.node_id))
      if (unhandled.length > 0) {
        await agent(commitFailuresPrompt(hardFailures), { label: 'commit-failures' })
        // A usable QA verdict blocks its obligation and successors, not unrelated
        // branches. Infrastructure/authority/policy failures still stop the run.
        if (unhandled.some(f => !qaReportUsable(f))) {
          return { status: 'needs_diagnosis', hardFailures }
        }
        for (const failure of unhandled) {
          blockedFailures.set(failure.node_id, failure)
          const loop = repairLoopFor(repair.loops, failure.node_id)
          if (loop) repair.open.set(failure.node_id, loop)
        }
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
  if (blockedFailures.size > 0) {
    return { status: 'needs_diagnosis', hardFailures: [...blockedFailures.values()] }
  }
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
  runNodePrompt, commitPrompt, commitFailuresPrompt, repairRoutePrompt,
  LEDGER_VERDICT_SCHEMA, authorizationPrompt, authorizationId, ledgerReceiptError, shellQuote
}
