const test = require('node:test')
const assert = require('node:assert/strict')
const core = require('../engine-core.js')

test('loadDagPrompt references workflow.json + bootstrap-profile + profile_slice', () => {
  const p = core.loadDagPrompt()
  assert.match(p, /workflow\.json/)
  assert.match(p, /bootstrap-profile\.json/)
  assert.match(p, /profile_slice/)
  assert.match(p, /completed/)
})

test('expandPrompt names the expander and requires wave-by-wave reconciliation', () => {
  const p = core.expandPrompt('expand_game_2d_production.py')
  assert.match(p, /expand_game_2d_production\.py/)
  assert.match(p, /new_nodes/)
  assert.match(p, /after every execution wave/)
  assert.doesNotMatch(p, /applied_expanders/)
})

test('gate and repair prompts require real artifact checks and rerun evidence', () => {
  const node = { node_id: 'qa' }
  assert.match(core.gateNodePrompt(node), /check_artifacts\.py/)
  assert.match(core.gateNodePrompt(node), /code_gaps/)
  assert.match(core.repairPrompt(node, []), /execution-repair-loop/)
  assert.match(core.repairPrompt(node, []), /Rerun affected QA evidence/)
})

test('runNodePrompt includes node_spec_path, decision_inputs, no-placeholder rule, closure_verify', () => {
  const node = { node_id: 'audio', node_spec_path: 'node-specs/audio.md',
    decision_inputs: ['.allforai/game-design/decision-audio.json'],
    closure_verify: ['audio'], profile_slice: { stack: 'unity' } }
  const p = core.runNodePrompt(node, ' [retry 1]')
  assert.match(p, /node-specs\/audio\.md/)
  assert.match(p, /decision-audio\.json/)
  assert.match(p, /placeholder/i)
  assert.match(p, /audio/)               // closure_verify value
  assert.match(p, /\[retry 1\]/)         // strictness suffix threaded through
})

// The commit is a relay of record_transition.py, never an agent editing workflow.json.
const relayed = p => JSON.parse(/printf '%s' '(.*?)' \| python3/.exec(p)[1])

test('commitPrompt relays record_transition.py with the assumed_decisions (fix C1)', () => {
  const p = core.commitPrompt({ node_id: 'a', artifacts_written: ['x'], assumed_decisions: [{ id: 'tone', decision: 'warm' }] })
  assert.match(p, /`printf '%s' '.*' \| python3 \.allforai\/bootstrap\/scripts\/record_transition\.py \.`/)
  assert.match(p, /Do not edit any file yourself/)
  assert.doesNotMatch(p, /Append to \.allforai\/bootstrap\/workflow\.json/)
  assert.deepEqual(relayed(p), { node_id: 'a', status: 'completed', artifacts_created: ['x'],
    verification: { method: 'none' }, clear_corrections: true,
    assumed_decisions: [{ id: 'tone', decision: 'warm' }] })
})

test('runNodePrompt tells the subagent to RETURN assumed_decisions, not write them (fix C1)', () => {
  const p = core.runNodePrompt({ node_id: 'n', node_spec_path: 's.md' }, '')
  assert.match(p, /assumed_decisions/)
})

test('runNodePrompt demands real evidence and forbids generated-as-verified (verification honesty)', () => {
  const p = core.runNodePrompt({ node_id: 'n', node_spec_path: 's.md' }, '')
  assert.match(p, /verification/)
  assert.match(p, /evidence_path/)
  assert.match(p, /masquerade as "verified"/)
})

test('commitPrompt records verification verbatim (no upgrade)', () => {
  const verification = { method: 'real-test', evidence_path: 'e.txt', verifier: 'qa' }
  const p = core.commitPrompt({ node_id: 'a', artifacts_written: [], verification })
  assert.deepEqual(relayed(p).verification, verification)
})

test('commitFailuresPrompt references diagnosis_history', () => {
  assert.match(core.commitFailuresPrompt([{ node_id: 'c' }]), /diagnosis_history/)
  assert.match(core.commitFailuresPrompt([{ node_id: 'c' }]), /kind: "failure"/)
  assert.match(core.commitFailuresPrompt([{ node_id: 'c' }]), /Do not add root_cause/)
})

// The project-root argument is a bare `.`. Written at the end of a sentence it reads as
// punctuation, and an agent that drops it runs the helper with no root at all. Every
// command an agent must run verbatim is therefore delimited, root argument inside.
test('commands with a bare project-root argument are delimited so the root is not punctuation', () => {
  const ledger = core.authorizationPrompt({ operation: 'consumption' })
  assert.match(ledger, /`printf '%s' '\{"operation":"consumption"\}' \| python3 \.allforai\/bootstrap\/scripts\/repair_authorization\.py \.`/)
  assert.doesNotMatch(ledger, /repair_authorization\.py \. [A-Z]/)
  const readiness = core.readinessPrompt()
  assert.match(readiness, /`python3 \.allforai\/bootstrap\/scripts\/validate_unattended_readiness\.py \. --write-report`/)
})

test('runNodePrompt points the node at its diagnosis corrections and bounds them', () => {
  const p = core.runNodePrompt({ node_id: 'n', node_spec_path: 's.md' }, '')
  assert.match(p, /\.allforai\/bootstrap\/diagnosis-corrections\/n\.json/)
  assert.match(p, /never settles a user-visible rule/)
})

test('commitPrompt removes the completed node\'s corrections file', () => {
  const p = core.commitPrompt({ node_id: 'n', artifacts_written: [] })
  assert.equal(relayed(p).clear_corrections, true)
})

test('repairRoutePrompt records a failed QA transition through the helper', () => {
  const p = core.repairRoutePrompt('verify', { repair_node_id: 'fix', max_attempts: 2 }, 1)
  const request = relayed(p)
  assert.equal(request.node_id, 'verify')
  assert.equal(request.status, 'failed')
  assert.match(request.error, /routed to declared repair node fix \(attempt 1 of 2 without progress\)/)
})

test('transitionReceiptError accepts only a recorded receipt for this node', () => {
  const ok = { status: 'recorded', node_id: 'a', transition_index: 3, replayed: false }
  assert.equal(core.transitionReceiptError(ok, 'a'), null)
  assert.equal(core.transitionReceiptError({ ...ok, replayed: true }, 'a'), null)
  assert.match(core.transitionReceiptError(null, 'a'), /no receipt/)
  assert.match(core.transitionReceiptError({ ...ok, node_id: 'b' }, 'a'), /names node "b"/)
  assert.match(core.transitionReceiptError({ status: 'refused', node_id: 'a', reason: 'x' }, 'a'), /not recorded: refused — x/)
  assert.match(core.transitionReceiptError({ status: 'recorded', node_id: 'a' }, 'a'), /transition_index/)
})

test('deliveryNote is empty for an ordinary dispatch', () => {
  assert.equal(core.deliveryNote(null), '')
  assert.doesNotMatch(core.runNodePrompt({ node_id: 'n', node_spec_path: 's.md' }, ''), /freshness publish being refused/)
})

test('runNodePrompt has a node pick an open building block and disclose it, never stop', () => {
  const p = core.runNodePrompt({ node_id: 'n', node_spec_path: 's.md' }, '')
  assert.match(p, /building block your inputs leave open/)
  assert.match(p, /kind "building_block", and keep going/)
})

test('the gate accepts a status the exit declares and still refuses what it does not', () => {
  const p = core.gateNodePrompt({ node_id: 'qa' })
  assert.match(p, /declared_status\.accepted true/)
  assert.match(p, /declared_status\.limited true/)
  assert.match(p, /known_limits/)
  assert.match(p, /limited completion not declared in limited_statuses/)
  assert.match(p, /status the exit does not declare/)
})

test('a node and its repair write only their own outputs and report an upstream defect', () => {
  for (const p of [core.runNodePrompt({ node_id: 'n', node_spec_path: 's.md' }, ''),
    core.repairPrompt({ node_id: 'n' }, [])]) {
    assert.match(p, /Never create,\s+edit or delete any other file another node produces/)
    assert.match(p, /cross_node/)
    assert.match(p, /unpublished_producer/)
    assert.match(p, /producer_outside_graph/)
    assert.match(p, /declared parallel_write_scopes cover/)
    assert.match(p, /unless this dispatch names you the repair of a failed QA node/)
    // A defect it merely noticed is reported, not a reason to fail.
    assert.match(p, /fails this node only when it keeps this node from\s+meeting its own acceptance/)
    assert.match(p, /is not a failure: finish the node and return\s+it in safety_warnings/)
    assert.match(p, /the run sends\s+it back to that node to fix once every node has run/)
  }
})

test('the repair of an open loop may change what its QA node judged, and republishes it', () => {
  const plain = core.runNodePrompt({ node_id: 'n', node_spec_path: 's.md' }, '')
  assert.doesNotMatch(plain, /For this dispatch you may also change/)
  const p = core.runNodePrompt({ node_id: 'fix', node_spec_path: 's.md' }, '', { qa: ['critique'] })
  assert.match(p, /repairs the failure of QA node\(s\) \["critique"\]/)
  assert.match(p, /may also change an exit artifact or required document of a node those QA\s+node\(s\) are hard_blocked_by, directly or transitively/)
  assert.match(p, /only a file a QA\s+finding requires changed, and never a decision input/)
  assert.match(p, /each node whose file you changed must have valid evidence again/)
})

test('a diagnosis correction is read directly, never registered as an input', () => {
  const p = core.runNodePrompt({ node_id: 'n', node_spec_path: 's.md' }, '')
  assert.match(p, /never register it with the freshness `read`/)
})

test('wavePrompt runs the freshness helper with the exact request', () => {
  assert.match(core.wavePrompt('begin-wave', ['a', 'b']),
    /'\{"operation":"begin-wave","node_ids":\["a","b"\]\}' \| python3 \.allforai\/bootstrap\/scripts\/evidence_freshness\.py \./)
  assert.match(core.wavePrompt('recover-waves'), /'\{"operation":"recover-waves"\}'/)
})

// ADR-0018: `/run` is unattended. A node takes an unsettled user-visible choice on its
// recommendation and records it for disclosure; it is not told to fail and wait.
test('runNodePrompt: an unsettled product choice is taken, recorded and never a stop', () => {
  const p = core.runNodePrompt({ node_id: 'n', node_spec_path: 's.md' }, '')
  assert.match(p, /run-decisions\/<node_id>\.json/)
  assert.match(p, /recommended, taken, why/)
  assert.match(p, /not a failure and not a reason to stop/)
  assert.doesNotMatch(p, /unresolved_product_decision|product-decision-gaps/)
})
