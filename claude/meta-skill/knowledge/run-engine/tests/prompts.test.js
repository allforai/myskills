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

test('expandPrompt names the expander and asks for new_nodes', () => {
  const p = core.expandPrompt('expand_game_2d_production.py')
  assert.match(p, /expand_game_2d_production\.py/)
  assert.match(p, /new_nodes/)
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

test('commitFailuresPrompt references diagnosis_history', () => {
  assert.match(core.commitFailuresPrompt([{ node_id: 'c' }]), /diagnosis_history/)
})
