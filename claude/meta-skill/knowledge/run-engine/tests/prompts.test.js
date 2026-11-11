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

test('commitPrompt references transition_log AND persists assumed_decisions (fix C1)', () => {
  const p = core.commitPrompt({ node_id: 'a', artifacts_written: ['x'], assumed_decisions: [{ id: 'tone', decision: 'warm' }] })
  assert.match(p, /transition_log/)
  assert.match(p, /assumed-decisions\.json/)
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
  const p = core.commitPrompt({ node_id: 'a', artifacts_written: [], verification: { method: 'none' } })
  assert.match(p, /verification/)
  assert.match(p, /do NOT upgrade/)
})

test('commitFailuresPrompt references diagnosis_history', () => {
  assert.match(core.commitFailuresPrompt([{ node_id: 'c' }]), /diagnosis_history/)
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
  assert.match(p, /delete \.allforai\/bootstrap\/diagnosis-corrections\/n\.json/)
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
    assert.match(p, /Never create, edit or delete a file another node produces/)
    assert.match(p, /cross_node/)
    assert.match(p, /unpublished_producer/)
  }
})

test('wavePrompt runs the freshness helper with the exact request', () => {
  assert.match(core.wavePrompt('begin-wave', ['a', 'b']),
    /'\{"operation":"begin-wave","node_ids":\["a","b"\]\}' \| python3 \.allforai\/bootstrap\/scripts\/evidence_freshness\.py \./)
  assert.match(core.wavePrompt('recover-waves'), /'\{"operation":"recover-waves"\}'/)
})
