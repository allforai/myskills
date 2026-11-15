export const meta = {
  name: 'run-engine',
  description: 'Autonomous DAG executor for meta-skill /run (Phase B): schedule, parallel-execute, self-heal, commit.',
  phases: [
    { title: 'Load' },
    { title: 'Expand' },
    { title: 'Execute' }
  ]
}

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
        soft_retry_max: { type: 'integer' },
        // Declared at bootstrap on a node whose output a later QA node judges: review it
        // against its own acceptance right after it passes, while nothing consumes it yet.
        inline_review: { type: 'object', properties: { qa_node_id: { type: 'string' } } }
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
    qa_node_id: { type: 'string' },
    progress: { type: 'boolean' },
    spent: { type: 'integer' },
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
    // How many distinct blocking findings a failed QA report holds. The findings above may
    // summarize; this is the figure a declared repair loop's progress is read from.
    blocking_count: { type: 'integer' },
    assumed_decisions: { type: 'array', items: { type: 'object' } }, // fix C1: engine persists these, not the subagent
    verification: { type: 'object',                                  // verification-honesty: evidence of real working behavior
      properties: {
        method: { type: 'string', enum: ['real-run', 'real-test', 'real-api', 'db-query', 'screenshot', 'none'] },
        evidence_path: { type: 'string' }, // captured proof file; must EXIST for the node to count as 'verified'
        verifier: { type: 'string' },      // identity that verified — must differ from the generator
        claim: { type: 'string' },         // one line: what was proven to actually work
        served_by: { type: 'object',       // where the exercised code's requests went (ADR-0008, #64):
          properties: {                    // required for every runtime method; the hollow refusals read it
            host: { type: 'string' },
            process: { type: 'string' },
            mock_layers: { type: 'array', items: { type: 'string' } },
            fixtures: { type: 'array', items: { type: 'string' } }
          },
          required: ['host', 'process', 'mock_layers'] }
      } },
    summary: { type: 'string' },
    safety_warnings: { type: 'array', items: { type: 'string' } },
    // The concept-acceptance coverage gate's output, copied verbatim from its report:
    // every behaviour mapping the concept declares either has evidence or is named here.
    // Empty means proceed. It renders no score and no verdict (ADR 0008).
    missing_mappings: { type: 'array', items: { type: 'object' } }
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

// An inline review of a node's own output, by an agent that never saw it being made.
const INLINE_REVIEW_SCHEMA = {
  type: 'object',
  required: ['node_id', 'status', 'blocking_count'],
  properties: {
    node_id: { type: 'string' },
    status: { type: 'string', enum: ['passed', 'findings'] },
    blocking_count: { type: 'integer' },
    findings_path: { type: 'string' }
  }
}
// Reviews that find no fewer blocking findings than the best so far before the node is let
// through with what remains, and the ceiling on reviews of one node whatever the progress.
const INLINE_REVIEW_STALLS = 2
const INLINE_REVIEW_ROUNDS = 6

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

// ADR-0018: a node takes an unsettled user-visible choice on its own recommendation and
// records it in `run-decisions/`, so this path is no longer how a run meets one. It
// stays for a node-spec bootstrapped under ADR-0011, which still tells its node to fail
// with structured `unresolved_product_decision` findings: that failure blocks the node
// and its successors, never unrelated branches. A claim without that structure is not
// trusted as one: it stays a diagnosis case.
function productDecisionGap(result) {
  if (!result || result.outcome !== 'hard_fail') return false
  const findings = result.blocking_findings || []
  if (findings.length === 0) return false
  return findings.every(f => f && f.type === 'unresolved_product_decision' &&
    typeof f.needed_decision === 'string' && f.needed_decision.trim() !== '' &&
    Array.isArray(f.options) && f.options.filter(o => typeof o === 'string' && o.trim()).length >= 2)
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

// A runtime method exercises the product, so the node must say where its requests went; without
// served_by nothing can tell a real backend from a mock, and compute_completeness will not count it.
// real-test is a suite run (mechanical) and none never counted.
const RUNTIME_METHODS = ['real-run', 'real-api', 'db-query', 'screenshot']

function runtimeVerificationReason(result) {
  const v = (result && result.verification) || {}
  if (!RUNTIME_METHODS.includes(v.method)) return ''
  const sb = v.served_by
  if (!sb || typeof sb !== 'object' || typeof sb.host !== 'string' || typeof sb.process !== 'string'
      || !Array.isArray(sb.mock_layers)) {
    return 'runtime verification without served_by (host / process / mock_layers): the node did not say where its requests went'
  }
  return ''
}

function routeOutcome(result) {
  if (result.outcome === 'accepted_with_gaps') return 'accepted'
  const unbacked = runtimeVerificationReason(result)
  if (unbacked && result.outcome === 'passed') {
    result.blocking_findings = [...(result.blocking_findings || []),
      { type: 'unbacked_runtime_verification', detail: unbacked }]
  }
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
    'exit_artifacts, node_spec_path, decision_mode, decision_inputs, closure_verify, soft_retry_max, inline_review,',
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
    'Run `python3 .allforai/bootstrap/scripts/validate_unattended_readiness.py . --write-report`.',
    'Read .allforai/bootstrap/unattended-run-readiness.json. Return status "ready" only when',
    'the command succeeds and the report status is exactly "ready"; otherwise return',
    '{status:"not_ready", blockers:[...]}. Never weaken or bypass a blocker.'
  ].join(' ')
}

// A node owns what it declares it writes and nothing else. Editing another node's output
// stales that node's evidence from outside it, and the owner never learns its work was
// wrong; the finding goes back to the owner instead. The second half is the receiving side
// of the same rule: a file whose producer has not published in this run is a leftover of an
// earlier cycle or a sibling's work in progress, and the freshness `read` refuses it.
const OWN_OUTPUTS_RULE = [
  'Write only what this node owns: its exit_artifacts, its required_documents and the files its',
  'declared parallel_write_scopes cover. Never create, edit or delete any other file another node',
  'produces, unless this dispatch names you the repair of a failed QA node, which grants exactly',
  'what it states. If one is wrong or missing, stop and report',
  'blocking_findings [{type: "cross_node", detail, suspected_root_node: <the producing node>}] so',
  'its owner repairs it.',
  'A file another node produces is an input only along a declared dependency, once that node has',
  'published it in this run: when the freshness `read` answers unpublished_producer (a leftover or',
  'unfinished work) or producer_outside_graph (a node the plan does not order before this one),',
  'do not consume the file in any way; if this node cannot be done without it, report the missing',
  'dependency as a blocking finding instead.'
].join(' ')

function gateNodePrompt(node) {
  return [
    `Run python3 .allforai/bootstrap/scripts/check_artifacts.py`,
    `.allforai/bootstrap/workflow.json --node ${node.node_id} --json.`,
    'Read the JSON, every declared exit artifact, and every validation command result.',
    'Return status "passed" only when all_exist is true and there are no unresolved gaps.',
    'The exit declaration is the acceptance: a report status the checker printed as',
    'declared_status.accepted true, with no status_error, is this node\'s declared outcome, so do',
    'not return "repair" for that status. When it also printed declared_status.limited true, the',
    'checker has verified that the report names each limit with evidence in known_limits; those',
    'recorded limits are not gaps. Still return "repair" for anything outside the declaration:',
    'code_gaps or test_gaps, a conditional/partial/warning status the exit does not declare, a',
    'limited completion not declared in limited_statuses, a placeholder, a fallback or',
    'degradation the report does not record in known_limits, a missing side effect, or a failed',
    'validation. Cross-node, environment, authority, or unsafe blockers return "hard_fail".',
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
    'or hide them.', OWN_OUTPUTS_RULE,
    'Rerun affected QA evidence, but do not mark the workflow node complete;',
    'the controller will rerun the original node and its independent artifact gate.'
  ].join(' ')
}

// The repair node of an open loop is dispatched to deliver, not to complete: the QA node it
// repairs stays stale until that node reruns, so this node's freshness publish is refused by
// construction. Telling it so keeps it from reporting the refusal as its own failure; the
// engine does not rely on that either way, it measures the delivery (see runNode).
function deliveryNote(delivery) {
  if (!delivery) return ''
  return [
    `This dispatch repairs the failure of QA node(s) ${JSON.stringify(delivery.qa || [])}.`,
    'Their evidence stays stale until they rerun, so your freshness publish being refused because',
    'of them is expected, not a failure.',
    'For this dispatch you may also change an exit artifact or required document of a node those QA',
    'node(s) are hard_blocked_by, directly or transitively (see workflow.json) — but only a file a QA',
    'finding requires changed, and never a decision input. Changing such a file stales the evidence',
    'of the node that produced it, and a stale producer withholds the QA rerun and you alike: before',
    'you finish, each node whose file you changed must have valid evidence again — observe it, run',
    'its own declared validation commands and publish it through the freshness helper. If its',
    'validation fails on your change, the change is wrong.',
    'Make the repair, write your exit artifacts, run your own',
    'validation, and return "passed" when your own work is done; the engine measures what you',
    'delivered and reruns the QA node, which judges it.'
  ].join(' ')
}

// The reviewer sees the artifacts and the criteria, never how the node reasoned its way to
// them, and the node that revises sees the findings file, never the review. Everything
// passes through files so no context carries one role's reasoning into another.
function inlineReviewPath(node) {
  return `.allforai/bootstrap/inline-review/${node.node_id}.json`
}

function inlineReviewPrompt(node, round) {
  const qa = node.inline_review && node.inline_review.qa_node_id
  const artifacts = (node.exit_artifacts || []).map(a => (a && a.path) || a).filter(Boolean)
  return [
    `You are an independent reviewer of node ${node.node_id}, which has just finished. You did not produce its output`,
    'and you change none of it.',
    `Read its node-spec at ${node.node_spec_path} for what it had to deliver and its acceptance criteria.`,
    qa ? `Node ${qa} will judge this output later: read that node's node-spec (its path is in .allforai/bootstrap/workflow.json) and apply the same criteria it will, to this node's output alone.` : '',
    `Then read what the node produced: ${JSON.stringify(artifacts)} and the files those name.`,
    'Judge only against those criteria. A blocking finding is a criterion the output does not meet, stated so the',
    'producer can fix it in its own files; a preference, or a defect only a later node can see, is not one.',
    `Write ${inlineReviewPath(node)} as {node_id, round: ${round}, status, blocking: [{id, criterion, artifact, detail}]}`,
    'and nothing else: no product file, no report of the node, no freshness record.',
    `Return {node_id, status ("passed" when blocking is empty, otherwise "findings"), blocking_count, findings_path}.`
  ].filter(Boolean).join(' ')
}

function inlineReviseNote(node, round) {
  return ` [inline review ${round}: an independent reviewer found blocking findings in what you delivered. Read ` +
    `${inlineReviewPath(node)} directly (never register it with the freshness \`read\`) and fix every finding in your own ` +
    'outputs; change nothing the findings do not require, then validate and publish as usual.]'
}

function runNodePrompt(node, strict, delivery = null) {
  const di = (node.decision_inputs || [])
  const cv = (node.closure_verify || [])
  return [
    `Read and execute the node-spec at ${node.node_spec_path}.`,
    di.length ? `First read these required decision inputs: ${di.join(', ')} — if any is missing, return outcome "hard_fail".` : '',
    `If .allforai/bootstrap/diagnosis-corrections/${node.node_id}.json exists, read it before starting: it holds`,
    'corrections a diagnosis of an earlier failure assigned to this node, and they bind this run as the node-spec does.',
    'Read that file directly and never register it with the freshness `read`: it is the run\'s instruction, deleted',
    'when this node completes, not a product input.',
    'A correction refines how this node meets its spec; it never settles a user-visible rule. If applying one needs a',
    'choice your decision inputs do not settle, take and record it as a run decision (below).',
    deliveryNote(delivery),
    `Project context (profile_slice): ${JSON.stringify(node.profile_slice || {})}.`,
    'Write all exit_artifacts and run their validation_commands to self-check.',
    OWN_OUTPUTS_RULE,
    'Follow .allforai/bootstrap/protocols/input-freshness.md: after implementation settles, observe current inputs, register additional reads, refresh required documents and publish evidence with the actual acceptance command. Reobserve and reverify stale inputs; contract-only publication cannot prove completion.',
    cv.length ? `Additionally run closure verification for: ${cv.join(', ')}.` : '',
    'STRICTLY forbid placeholder / stub / debug-residue / pure-color placeholder outputs.',
    'VERIFICATION (epistemic honesty): if you actually exercised the real built behavior, capture',
    'external proof to a file (real run output / real API round-trip with real data / db row / screenshot)',
    'and RETURN verification: {method, evidence_path, verifier, claim, served_by}. served_by is',
    'REQUIRED for real-run / real-api / db-query / screenshot: {host, process, mock_layers[], fixtures[]}',
    '— the dev server or binary your requests reached, the mock layers in effect (MSW, nock, an',
    'in-memory DB; [] when none) and the fixture files a canned answer could have come from. A runtime',
    'claim without it is not counted as verified. If you only generated code',
    'without exercising it, RETURN verification.method "none" — do NOT claim verified. "Generated"',
    'must never masquerade as "verified".',
    'If you must assume an unforeseen emergent decision, pick a sensible default and RETURN it in',
    'assumed_decisions: [{id, decision, default_chosen, rationale}] — do NOT write any file yourself',
    '(the engine persists it during the serialized commit).',
    'A building block your inputs leave open (an engine, framework, library, data store, storage or other service the',
    'existing code does not already use) is such a decision: pick the option that fits the existing code and settled',
    'inputs, return it with kind "building_block", and keep going; the person sees it in the run report.',
    'Return a NODE_RESULT { node_id, outcome (passed|soft_fail|hard_fail), artifacts_written,',
    'blocking_findings: [{type, detail, suspected_root_node?}], assumed_decisions? }. Attach',
    'suspected_root_node when the root cause is in another node. When this node is a QA node and it fails on its own',
    'report, also return blocking_count: the number of distinct blocking findings in that report — count the defects,',
    'never the summary lines, and count the same way on every run.',
    'Return safety_warnings[] for non-blocking warnings. When this node is the concept-acceptance coverage gate, return',
    'missing_mappings[] copied verbatim from .allforai/concept-acceptance/acceptance-report.json — the behaviour mappings',
    'with no evidence; an empty list means every mapping has evidence. Return no score, threshold or verdict.',
    'The run is unattended and never stops for a question (ADR-0018). A user-visible choice this node owns that the recorded',
    'decision_inputs do not settle is taken here: weigh at least two options, build with the one you recommend, and write',
    '.allforai/bootstrap/run-decisions/<node_id>.json as {node_id, decisions: [{decision_id, needed_decision, options (two or more),',
    'recommended, taken, why, blocking_intent_ids}]} so completion can list it and the user can overturn it at the next interactive',
    'bootstrap. It is not a failure and not a reason to stop. A choice that contradicts a recorded decision_input is never taken.',
    strict || ''
  ].filter(Boolean).join(' ')
}

// An interrupted engine leaves the nodes it was running half-recorded: dynamic reads they
// registered, evidence they published, and no transition saying how the attempt ended. The
// freshness helper owns both stores, so it brackets each wave and, at the next start,
// returns whatever a wave that never closed left behind to its state before that wave.
function wavePrompt(operation, nodeIds) {
  const request = operation === 'recover-waves' ? { operation } : { operation, node_ids: nodeIds }
  return [
    'Run EXACTLY this command, once, and return its stdout parsed as your JSON result:',
    `\`printf '%s' ${shellQuote(JSON.stringify(request))} | python3 .allforai/bootstrap/scripts/evidence_freshness.py .\``,
    '(the command is everything between the backticks; its final `.` is the project-root argument, not punctuation).',
    'Do not edit any file yourself and do not retry.'
  ].join(' ')
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
    `Then delete .allforai/bootstrap/diagnosis-corrections/${result.node_id}.json if it exists: the node completed`,
    'with its corrections applied, and diagnosis_history keeps their record.',
    'Append only; do not touch other entries.'
  ].filter(Boolean).join(' ')
}

function repairRoutePrompt(qaNodeId, loop, attempt) {
  return [
    `Append a failed transition for ${qaNodeId} to .allforai/bootstrap/workflow.json transition_log`,
    `with error "QA failed; routed to declared repair node ${loop.repair_node_id}`,
    `(attempt ${attempt} of ${repairBudget(loop)} without progress)".`,
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
    `\`printf '%s' ${shellQuote(JSON.stringify(request))} | python3 .allforai/bootstrap/scripts/repair_authorization.py .\``,
    '(the command is everything between the backticks; its final `.` is the project-root argument, not punctuation).',
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
    'Append these hard failures to .allforai/bootstrap/workflow.json diagnosis_history,',
    'one entry each as {kind: "failure", failed_node, blocking_findings} and nothing else:',
    `${JSON.stringify((hardFailures || []).map(h => h.node_id))}.`,
    'This records the failure only. Do not add root_cause: that field belongs to the diagnosis',
    'the orchestrator records afterwards, and only a diagnosis counts toward the diagnosis cap.'
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
  // Deliberately NOT required here: the repair node's own readiness, and an input binding
  // unchanged across the attempt. A repair edits the very source its QA node checks, so
  // both move by doing the work — demanding they stand still made every real repair
  // unmeasurable and burned the loop's budget on a rule no repair could satisfy. What a
  // delivery claims is narrow: this attempt wrote its declared artifacts, and nothing but
  // its own QA node is withholding it. Whether the repair was RIGHT is not measured here
  // and never was: the QA rerun that follows is the proof, and the declared budget bounds
  // the attempts either way (ADR-0005, ADR-0006).
  // Measured across the attempt, by the same independent step: something the attempt wrote
  // has to differ from what was there before it ran. A pre-existing or touched artifact is
  // not a delivery.
  const before = open && open.before
  if (!before || !Array.isArray(before.artifacts)) return null
  const wasThere = new Map(before.artifacts.filter(a => a && a.path).map(a => [a.path, a.digest]))
  const produced = declared.filter(rel => wasThere.get(rel) !== measured.get(rel).digest)
  if (produced.length === 0) return null
  return { binding_identity: m.binding_identity,
           produced: Object.fromEntries(produced.map(rel => [rel, measured.get(rel).digest])) }
}

// The halt a user actually sees when auto_fix_once has no declared loop: name the planning
// declaration, not just "unauthorized", so the fix is found at bootstrap (#65).
function undeclaredCoverageLoopMessage(gateNodeId) {
  return `auto_fix_once: no required_repair_loops entry names ${gateNodeId} in qa_node_ids; the repair is unauthorized (ADR-0006). Declare the loop at bootstrap (bootstrap-planning: "The coverage gate's repair loop") or choose halt_with_report.`
}

// deliveryOnly: this node is the declared repair node of a currently open loop. Its
// independent gate cannot pass yet — it is `hard_blocked_by` the QA node it repairs, so
// while that node is failing the repair node's own evidence is stale and the gate
// withholds it by construction. Retrying inside the node would burn the artifact repair
// budget against something no repair can fix. Its delivery closes the loop instead, the
// QA rerun is the check, and the node is dispatched again afterwards as an ordinary node
// and must pass this same gate on its own merits before anything commits it.
async function runNode(node, agent, policy = {}, deliveryOnly = null, note = '') {
  const max = node.soft_retry_max ?? 2
  const repairMax = node.repair_retry_max ?? 3
  let attempt = 0
  let repairAttempt = 0
  let strict = note
  while (true) {
    const r = await agent(runNodePrompt(node, strict, deliveryOnly), { schema: NODE_RESULT_SCHEMA, label: node.node_id })
    if (!r || r.node_id !== node.node_id) {
      return { node_id: node.node_id, outcome: 'hard_fail', artifacts_written: [],
        blocking_findings: [{ type: 'invalid_artifact_gate', detail: 'executor result missing or names a different node' }] }
    }
    if ((r.safety_warnings || []).length) {
      await agent(`Record these safety warnings without asking a question: ${JSON.stringify(r.safety_warnings)}.`, { label: `safety-report:${node.node_id}` })
      if (policy.on_safety_warning !== 'continue') return { ...r, outcome: 'hard_fail',
        blocking_findings: [{ type: 'safety_warning', detail: 'Recorded Run Policy requires halt' }] }
    }
    // A delivery dispatch is judged by measurement, not by the repair node's own verdict. Its
    // freshness publish is refused by construction while the QA node it repairs is stale, and
    // a node that reports that refusal as its failure has told the engine nothing the gate
    // will not measure. Taking it at its word charged every attempt of the loop without the
    // QA node ever rerunning. Structural verdicts and a missing product decision stay its own.
    const selfFailed = routeOutcome(r) === 'hard'
    const measureInstead = selfFailed && deliveryOnly && !productDecisionGap(r) &&
      !(r.blocking_findings || []).some(f => f && NON_QA_FAILURE_TYPES.has(f.type))
    if (selfFailed && !measureInstead) return { ...r, outcome: 'hard_fail' }
    if (r.acceptance_verdict !== undefined) {
      // The coverage gate names missing behaviour mappings; it renders no verdict. A
      // result that still carries one is a scored report, not this gate's output (ADR 0008).
      return { ...r, outcome: 'hard_fail', blocking_findings: [{ type: 'invalid_artifact_gate',
        detail: 'acceptance_verdict is a scored verdict; the concept-acceptance gate reports missing_mappings only' }] }
    }
    if (r.missing_mappings !== undefined && !Array.isArray(r.missing_mappings)) {
      return { ...r, outcome: 'hard_fail', blocking_findings: [{ type: 'invalid_artifact_gate',
        detail: 'missing_mappings is not a list; the coverage gate produced no decidable output' }] }
    }
    if ((r.missing_mappings || []).length > 0) {
      const missing = r.missing_mappings
      const event = await agent('Run `python3 .allforai/bootstrap/scripts/product_intent.py . --policy-event on_needs_iteration`. Return its JSON verbatim; do not ask questions.', {
        label: 'policy:on_needs_iteration', schema: { type: 'object', required: ['action'], properties: { action: { type: 'string' } } }
      })
      const action = event && event.action
      await agent('Write concept-acceptance/acceptance-report.md naming these behaviour mappings without evidence: ' +
        JSON.stringify(missing) + ', and the recorded policy action ' + action + '. ' +
        (action === 'accept' ? 'Append accepted_with_gaps to .allforai/bootstrap/assumed-decisions.json; do not mark the node completed or verified.' :
          'List fix / re-bootstrap / accept for the next interactive entry; never ask now.'), { label: `iteration-report:${node.node_id}` })
      if (action === 'accept') return { ...r, outcome: 'accepted_with_gaps' }
      if (action === 'auto_fix_once') {
        // One bounded repair request, and only through the declared loop and its ledger
        // (ADR 0005, ADR 0006). The gate's failure is routed like any other QA verdict:
        // a gate no loop declares a repair for, or whose budget is spent, stops the run.
        // Nothing is repaired in-node here — that would be an attempt nobody charged.
        return { ...r, outcome: 'hard_fail', iteration_repair: true,
          blocking_findings: missing.map(mapping => ({ type: 'missing_mapping',
            detail: `behaviour mapping without evidence: ${JSON.stringify(mapping)}`, mapping })) }
      }
      return { ...r, outcome: 'hard_fail', blocking_findings: [{ type: 'needs_iteration', detail: 'Recorded policy halted with report' }] }
    }
    const cls = measureInstead ? 'done' : routeOutcome(r)
    if (cls === 'done') {
      const gate = await agent(gateNodePrompt(node), {
        schema: NODE_GATE_SCHEMA, label: `verify:${node.node_id}`
      })
      if (!gate || gate.node_id !== node.node_id) {
        return { ...r, outcome: 'hard_fail', blocking_findings: [{
          type: 'invalid_artifact_gate', detail: 'independent artifact gate missing or mismatched'
        }] }
      }
      if (gate.status === 'passed' && (gate.blocking_findings || []).length === 0) {
        return measureInstead ? { ...r, outcome: 'hard_fail' } : r
      }
      // A withheld gate on an open loop's repair node is the expected state, not a gap to
      // retry, whether the gate step called the stale upstream "repair" or "hard_fail". The
      // measurement is what decides: a delivery wrote its declared artifacts and is withheld
      // by its own QA node and nothing else, so an environment, authority or other
      // cross-node blocker still fails it here.
      const structural = (gate.blocking_findings || []).some(f => f && NON_QA_FAILURE_TYPES.has(f.type))
      if (deliveryOnly && !(gate.status === 'hard_fail' && structural)) {
        const delivery = measuredDelivery(node, gate, deliveryOnly)
        if (delivery) {
          return { ...r, outcome: 'passed', blocking_findings: [], delivered: true, delivery,
            node_findings: r.blocking_findings || [], gate_findings: gate.blocking_findings || [] }
        }
        return { ...r, outcome: 'hard_fail', blocking_findings: [
          ...(measureInstead ? r.blocking_findings || [] : []), {
            type: 'unmeasured_repair_delivery',
            detail: 'the gate did not measure this repair as having delivered its declared exit ' +
                    'artifacts, bound to an input snapshot, withheld only by its own QA node'
          }] }
      }
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
      strict = `${note} [repair ${repairAttempt}: rerun affected QA evidence; all gaps must be empty]`
      continue
    }
    if (cls === 'hard') return { ...r, outcome: 'hard_fail' }
    if (attempt >= max && (policy.on_repeated_failure !== 'continue' || attempt >= 4)) {
      return { ...r, outcome: 'hard_fail',
        blocking_findings: [{ type: 'exhausted_retries', detail: `soft retried ${max}x without passing` }] }
    }
    attempt += 1
    strict = `${note} [retry ${attempt}: must fix all blocking findings]`
  }
}

// A node that declares inline_review is reviewed the moment it passes, and revises its own
// output while nothing has consumed it: no other node's file is touched and no evidence
// goes stale downstream. Reviews continue while each finds fewer blocking findings than the
// best so far. When they stop falling the node is let through with what remains recorded in
// its findings file — the QA node planned downstream still judges it, so a review that does
// not converge is never the reason a run stops. Only a revision that fails the node's own
// gate fails the node.
async function runNodeWithReview(node, agent, policy = {}, deliveryOnly = null) {
  let result = await runNode(node, agent, policy, deliveryOnly)
  if (!node.inline_review || deliveryOnly || routeOutcome(result) !== 'done' || result.delivered) return result
  let best = Infinity
  let stalls = 0
  for (let round = 1; round <= INLINE_REVIEW_ROUNDS; round++) {
    const review = await agent(inlineReviewPrompt(node, round), {
      schema: INLINE_REVIEW_SCHEMA, label: `inline-review:${node.node_id}:${round}`
    })
    // An unusable review settles nothing either way; the node stands on its own gate.
    if (!review || review.node_id !== node.node_id) return { ...result, inline_review: { status: 'unreviewed', rounds: round } }
    const count = Number.isInteger(review.blocking_count) ? review.blocking_count : 0
    if (review.status === 'passed' || count <= 0) return { ...result, inline_review: { status: 'passed', rounds: round } }
    stalls = count < best ? 0 : stalls + 1
    best = Math.min(best, count)
    if (stalls >= INLINE_REVIEW_STALLS || round === INLINE_REVIEW_ROUNDS) {
      return { ...result, inline_review: { status: 'open', rounds: round, blocking_count: count,
        findings_path: inlineReviewPath(node) } }
    }
    const revised = await runNode(node, agent, policy, null, inlineReviseNote(node, round))
    if (routeOutcome(revised) !== 'done') return revised
    result = revised
  }
  return result
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
    'Run `python3 .allforai/bootstrap/scripts/product_intent.py . --run-policy` and return its JSON verbatim. ' +
    'The script records the defaults itself when no usable policy exists; never ask the user and never choose values here.',
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
  // Before the graph is read: what an interrupted wave left behind must not be loaded as state.
  await agent(wavePrompt('recover-waves'), { label: 'recover-waves' })
  const dag = await agent(loadDagPrompt(), { schema: DAG_SCHEMA, label: 'load-dag' })
  const done = new Set(dag.completed || [])
  // A completion inherited from an earlier session is a claim read out of transition_log, not a
  // measurement. Before anything is dispatched on it, the gate re-measures each inherited
  // completion that a remaining node depends on; one that no longer passes is not done, so it
  // runs again instead of handing its consumer a missing, stale or unusable artifact. The receiving
  // side verifies (ADR-0010). This is narrower than the Codex driver, which measures EVERY node on
  // every pass: a completed node that nothing remaining depends on — typically the last verify
  // node — is not re-measured here, so the two hosts can still disagree about it (ADR-0004).
  // Closing that residual gap is a separate decision: it costs one gate run per completed node.
  const nodeById = new Map((dag.nodes || []).map(n => [n.node_id, n]))
  const measured = new Set()
  for (let changed = true; changed;) {
    changed = false
    // every completion a not-yet-done node depends on, asked about once
    const inherited = [...new Set((dag.nodes || [])
      .filter(n => !done.has(n.node_id))
      .flatMap(n => n.hard_blocked_by || []))]
      .filter(id => done.has(id) && nodeById.has(id) && !measured.has(id))
    for (const id of inherited) {
      measured.add(id)
      const gate = await agent(gateNodePrompt(nodeById.get(id)), {
        schema: NODE_GATE_SCHEMA, label: `inherit:${id}`
      })
      if (!gate || gate.node_id !== id || gate.status !== 'passed') {
        done.delete(id)
        changed = true
        log(`inherited completion of ${id} did not pass the gate; it will run again`)
      }
    }
    // What was built on a completion that must rerun is suspect too: a completed node with a
    // dependency that is no longer done is not done either. Each removal makes a node
    // "remaining", so the next pass also asks about what that node depends on.
    for (const n of dag.nodes || []) {
      if (done.has(n.node_id) && (n.hard_blocked_by || []).some(dep => nodeById.has(dep) && !done.has(dep))) {
        done.delete(n.node_id)
        changed = true
        log(`${n.node_id} was built on a completion that must rerun; it will run again`)
      }
    }
  }
  const repair = { loops: dag.repair_loops || [], open: new Map() }
  const blockedFailures = new Map()
  // `${repair_node_id}::${qa_node_id}` -> repair dispatches already granted to that QA node.
  // Keyed by the pair because one repair node may serve several QA nodes and each carries
  // its own declared budget; seeded from the recorded history so a restart resumes it.
  const repairAttempts = new Map()
  // Every attempt ever granted to the pair, across invocations. The spend above starts again
  // with each invocation and each QA verdict that was progress, so it cannot name a dispatch
  // uniquely; this count only grows.
  const repairGranted = new Map()
  // Coverage gates whose missing-mapping failure was routed to their declared repair in
  // this session. The recorded auto_fix_once policy grants exactly one iteration repair,
  // whatever the loop's remaining budget: a rerun that passes stops the run as
  // iteration_repair_stopped, and one that still names missing mappings is a policy
  // verdict, never a second route. The ledger's spent count answers the same question
  // across a restart, so an attempt charged by an earlier session counts too.
  const iterationRepaired = new Set()
  const stopRepeatedIteration = result => {
    if (!result || !result.iteration_repair) return result
    const loop = repairLoopFor(repair.loops, result.node_id)
    const spent = loop ? (repairAttempts.get(`${loop.repair_node_id}::${result.node_id}`) || 0) : 0
    if (!iterationRepaired.has(result.node_id) && spent === 0) return result
    return { ...result, iteration_repair: false, blocking_findings: [{ type: 'needs_iteration',
      detail: 'behaviour mappings still lack evidence after the one recorded iteration repair; the recorded policy stops here' }] }
  }
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
      repairGranted.set(`${record.repair_node_id}::${record.qa_node_id}`,
        Number.isInteger(record.granted) ? record.granted : record.spent)
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
      const priorGranted = {}
      const budgets = {}
      for (const qaNodeId of authorizedQa) {
        priorSpent[qaNodeId] = repairAttempts.get(`${repairNodeId}::${qaNodeId}`) || 0
        priorGranted[qaNodeId] = repairGranted.get(`${repairNodeId}::${qaNodeId}`) || 0
        budgets[qaNodeId] = repairBudget(repair.open.get(qaNodeId))
      }
      const grantId = authorizationId(ledgerRunId, repairNodeId, priorGranted)
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
        repairGranted.set(`${repairNodeId}::${qaNodeId}`, priorGranted[qaNodeId] + 1)
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
    const waveIds = ready.map(n => n.node_id)
    await agent(wavePrompt('begin-wave', waveIds), { label: 'begin-wave' })
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
    const outcomes = (await pipeline(ready, async node => {
      try {
        return await runNodeWithReview(node, waveAgent, policy, openDelivery.get(node.node_id) || null)
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
    })).map(stopRepeatedIteration)
    // Every result of the wave is known here, whatever it was; only a wave the engine never
    // saw end stays open for recovery.
    await agent(wavePrompt('end-wave', waveIds), { label: 'end-wave' })
    if (safetyHalted) {
      const hardFailures = outcomes.filter(r => r && routeOutcome(r) === 'hard')
      const quotedNodes = "'" + JSON.stringify(ready.map(n => n.node_id)).replace(/'/g, "'\\''") + "'"
      const quarantine = await agent('Run `python3 .allforai/bootstrap/scripts/run_safety.py . --nodes-json ' +
        quotedNodes + " --reason 'Recorded Run Policy requires a run-wide safety halt'`. " +
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
        if (productDecisionGap(failure)) return false
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
        if (!loop && failure.iteration_repair) {
          // auto_fix_once found missing mappings but no declared loop names this gate: the
          // halt report gets the actionable reason, not just the missing-mapping findings.
          failure.blocking_findings = [...(failure.blocking_findings || []),
            { type: 'unauthorized_repair', detail: undeclaredCoverageLoopMessage(failure.node_id) }]
        }
        // A missing product decision is not a defect a repair can fix: nobody may choose it.
        if (!loop || !qaReportUsable(failure) || productDecisionGap(failure)) continue
        const budget = repairBudget(loop)
        if (budget === null) continue          // unusable declared budget: route nothing
        const key = `${loop.repair_node_id}::${failure.node_id}`
        // The ledger reads this verdict against the earlier ones of the invocation: fewer
        // blocking findings than any before is progress, and the count of attempts starts
        // again. Its answer is the spend; a verdict it could not record renews nothing.
        const count = Number.isInteger(failure.blocking_count) && failure.blocking_count > 0
          ? failure.blocking_count : (failure.blocking_findings || []).length
        const judged = await agent(authorizationPrompt({ operation: 'verdict',
          repair_node_id: loop.repair_node_id, qa_node_id: failure.node_id, blocking_count: count
        }), { schema: LEDGER_VERDICT_SCHEMA, label: `repair-verdict:${failure.node_id}` })
        if (judged && judged.status === 'ok' && judged.qa_node_id === failure.node_id &&
            Number.isInteger(judged.spent) && judged.spent >= 0) repairAttempts.set(key, judged.spent)
        // Peek, never charge: the attempt is spent when the repair is dispatched, so a
        // route that opens and is then interrupted before any dispatch costs nothing.
        const spent = repairAttempts.get(key) || 0
        if (spent >= budget) continue
        repair.open.set(failure.node_id, loop)
        await agent(repairRoutePrompt(failure.node_id, loop, spent + 1), {
          label: `repair-route:${failure.node_id}:${spent + 1}`
        })
        routed.push(failure.node_id)
        // The coverage gate's one recorded iteration repair is this dispatch; the
        // charge itself is taken by the ledger when the repair node is dispatched.
        if (failure.iteration_repair) iterationRepaired.add(failure.node_id)
      }
      // Every failure must be a declared, budgeted, report-backed QA failure, or a repair
      // node still inside its own funded loop, to continue; anything else is a real stop.
      const handled = new Set([...routed, ...retained.map(f => f.node_id)])
      const unhandled = hardFailures.filter(f => !handled.has(f.node_id))
      if (unhandled.length > 0) {
        await agent(commitFailuresPrompt(hardFailures), { label: 'commit-failures' })
        // A usable QA verdict blocks its obligation and successors, not unrelated
        // branches. Infrastructure/authority/policy failures still stop the run.
        // A missing product decision blocks the same way (ADR-0011): the user answers it
        // at the next interactive bootstrap, and only its own subgraph waits for that.
        if (unhandled.some(f => !qaReportUsable(f) && !productDecisionGap(f))) {
          const earlier = [...blockedFailures.values()].filter(f => !handled.has(f.node_id) &&
            !unhandled.some(u => u.node_id === f.node_id))
          return { status: 'needs_diagnosis', hardFailures: [...hardFailures, ...earlier] }
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
    // The gate's rerun after its one recorded repair passed and was committed above; the
    // recorded policy still ends the run here rather than continuing past it.
    if (outcomes.some(r => r && routeOutcome(r) === 'done' && iterationRepaired.has(r.node_id))) return { status: 'iteration_repair_stopped' }
  }
  const remaining = dag.nodes.filter(n => !done.has(n.node_id))
  if (blockedFailures.size > 0) {
    const blocked = [...blockedFailures.values()]
    if (blocked.every(productDecisionGap)) {
      return { status: 'needs_product_decision', decisions: blocked.flatMap(f =>
        f.blocking_findings.map(finding => ({ node_id: f.node_id, ...finding }))) }
    }
    return { status: 'needs_diagnosis', hardFailures: blocked }
  }
  if (remaining.length > 0 && repair.open.size > 0) {
    // The repair budget is spent and the QA node still has not passed.
    const hardFailures = [...repair.open].map(([qaNodeId, loop]) => ({
      node_id: qaNodeId, outcome: 'hard_fail',
      blocking_findings: [{ type: 'exhausted_repair_loop',
        detail: `declared repair loop ${loop.repair_node_id} stopped: ${repairBudget(loop)} attempts in a row left its ` +
          'QA node with no fewer blocking findings, or the invocation\'s ceiling on attempts was reached. ' +
          'The next invocation of the run starts the count again' }]
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

const result = await runEngine({ agent, pipeline, log, phase })
return result
