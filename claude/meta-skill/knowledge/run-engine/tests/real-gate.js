// A fully declared project and its REAL independent artifact gate.
//
// The rest of the suite drives `runEngine` against fake gates, which cannot see the
// boundary that matters here: `check_artifacts.py` folds the recorded freshness state
// into `all_exist`, and a declared repair node is `hard_blocked_by` the QA node it
// repairs, so while that QA node is failing the repair node's own evidence is stale and
// its gate refuses it. This builds the project with the shipped orchestrator helpers and
// answers gate prompts from the real checker.
const { execFileSync } = require('node:child_process')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')

const ORCHESTRATOR = path.join(__dirname, '../../../scripts/orchestrator')

function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(value, null, 2))
}

function freshnessCli(root, request) {
  // The helper exits non-zero for stale/invalid and still prints its JSON verdict, which
  // is exactly the answer a caller needs; only a crash with no output is an error.
  try {
    return JSON.parse(execFileSync('python3',
      [path.join(root, '.allforai/bootstrap/scripts/evidence_freshness.py'), root],
      { input: JSON.stringify(request), cwd: root, encoding: 'utf8' }))
  } catch (err) {
    if (err.stdout) return JSON.parse(err.stdout)
    throw err
  }
}

// The canonical declared loop, every node declaring its inputs. Same shape as the Codex
// side's routing_project, so both hosts are judged against one graph.
function declaredLoopProject() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'declared-loop-'))
  const scripts = path.join(root, '.allforai/bootstrap/scripts')
  fs.mkdirSync(scripts, { recursive: true })
  for (const name of ['check_artifacts.py', 'evidence_freshness.py', 'repair_authorization.py']) {
    fs.copyFileSync(path.join(ORCHESTRATOR, name), path.join(scripts, name))
  }
  fs.mkdirSync(path.join(root, 'src'), { recursive: true })
  fs.writeFileSync(path.join(root, 'src/orders.py'), 'def export():\n    return []\n')

  const nodes = [
    { node_id: 'verify', capability: 'qa', hard_blocked_by: [], source_inputs: [],
      input_dependencies: ['src/orders.py'], exit_artifacts: ['verify.json'] },
    { node_id: 'repair', capability: 'qa', hard_blocked_by: ['verify'], source_inputs: [],
      input_dependencies: ['src/orders.py'], exit_artifacts: ['repair.json'] },
    // Closure is hard_blocked_by the repair node (readiness) and by every QA node
    // (validate_bootstrap: it would otherwise close on the repair alone).
    { node_id: 'accept', capability: 'qa', hard_blocked_by: ['repair', 'verify'], source_inputs: [],
      input_dependencies: ['src/orders.py'], exit_artifacts: ['accept.json'] }
  ]
  writeJson(path.join(root, '.allforai/bootstrap/workflow.json'), { nodes, transition_log: [] })
  writeJson(path.join(root, '.allforai/bootstrap/unattended-run-readiness-spec.json'), {
    version: 1,
    required_repair_loops: [{ scope: 'orders-export', qa_node_ids: ['verify'],
      repair_node_id: 'repair', closure_node_ids: ['accept'], max_attempts: 2 }]
  })
  for (const id of ['verify', 'repair', 'accept']) {
    const spec = path.join(root, `.allforai/bootstrap/node-specs/${id}.md`)
    fs.mkdirSync(path.dirname(spec), { recursive: true })
    fs.writeFileSync(spec, `${id} node\n`)
    const observed = freshnessCli(root, { operation: 'observe', node_id: id, kind: 'contract' })
    const published = freshnessCli(root, { operation: 'publish', observation: observed.observation,
      verification_command: ['python3', '-c', 'pass'] })
    if (published.status !== 'valid') throw new Error(`contract publish ${id}: ${JSON.stringify(published)}`)
  }
  return { root, nodes }
}

function checkArtifacts(root, nodeId) {
  const out = execFileSync('python3', [
    path.join(root, '.allforai/bootstrap/scripts/check_artifacts.py'),
    path.join(root, '.allforai/bootstrap/workflow.json'), '--node', nodeId, '--json'
  ], { cwd: root, encoding: 'utf8' })
  return JSON.parse(out)
}

// The checker's structured output, reported verbatim — nothing computed here. Every field
// the engine reads comes from `check_artifacts.py --json`: per-artifact digest/digest_error,
// and binding_identity / binding_kind / readiness_status from the freshness object.
function realMeasurementOf(payload) {
  const freshness = payload.freshness || {}
  const measurement = {
    artifacts: (payload.artifacts || []).map(a => {
      const entry = { path: a.path, exists: a.exists }
      if (a.status_error) entry.status_error = a.status_error
      if (a.digest) entry.digest = a.digest
      if (a.digest_error) entry.digest_error = a.digest_error
      return entry
    }),
    withheld_by: (freshness.diff || {}).upstream || []
  }
  if (freshness.binding_identity) measurement.binding_identity = freshness.binding_identity
  if (freshness.binding_kind) measurement.binding_kind = freshness.binding_kind
  if (freshness.readiness_status) measurement.readiness_status = freshness.readiness_status
  return measurement
}

// The same reading with the measurement fields stripped, to exercise the fail-closed path
// against a checker that does not publish them.
function withoutMeasurementFields(measurement) {
  return {
    artifacts: measurement.artifacts.map(({ path: p, exists, status_error }) => {
      const entry = { path: p, exists }
      if (status_error) entry.status_error = status_error
      return entry
    }),
    withheld_by: measurement.withheld_by
  }
}

// The gate the engine's `verify:<node>` prompt describes, answered by the real checker:
// all_exist true and nothing outstanding is a pass; anything else is a repair finding.
function realGate(root, nodeId, { unmeasured = false } = {}) {
  const payload = checkArtifacts(root, nodeId)
  const full = realMeasurementOf(payload)
  const measurement = unmeasured ? withoutMeasurementFields(full) : full
  if (payload.all_exist === true) {
    return { node_id: nodeId, status: 'passed', blocking_findings: [], measurement }
  }
  const findings = [{ type: 'artifact_gate', detail: JSON.stringify(payload.freshness || payload.artifacts) }]
  return { node_id: nodeId, status: 'repair', blocking_findings: findings, measurement }
}

function realMeasurement(root, nodeId, { unmeasured = false } = {}) {
  const full = realMeasurementOf(checkArtifacts(root, nodeId))
  return { measurement: unmeasured ? withoutMeasurementFields(full) : full }
}

function publishEvidence(root, nodeId) {
  const observed = freshnessCli(root, { operation: 'observe', node_id: nodeId, kind: 'evidence' })
  return freshnessCli(root, { operation: 'publish', observation: observed.observation,
    verification_command: ['python3', '-c', 'pass'] }).status
}

// The REAL canonical repair-authorization ledger, driven exactly the way the engine's own
// prompt tells the agent to drive it: the request is parsed back out of the command line
// the prompt built, and the helper's stdout is returned verbatim. Nothing here
// re-implements a decision — this is the boundary `ledger-double.js` stands in for
// everywhere else, so if the two ever disagree, this one is right.
function realLedger(root) {
  return prompt => {
    const match = /printf '%s' '([\s\S]*?)' \| python3 (\S+)/.exec(prompt)
    if (!match) throw new Error(`prompt does not carry a ledger request: ${prompt}`)
    const request = match[1].replace(/'\\''/g, "'")
    try {
      return JSON.parse(execFileSync('python3', [path.join(root, match[2]), '.'],
        { input: request, cwd: root, encoding: 'utf8' }))
    } catch (err) {
      // A refusal exits non-zero and still prints its verdict; that verdict is the answer.
      if (err.stdout) return JSON.parse(err.stdout)
      throw err
    }
  }
}

module.exports = { declaredLoopProject, checkArtifacts, realGate, realMeasurement,
  realMeasurementOf, withoutMeasurementFields, publishEvidence, freshnessCli, writeJson,
  realLedger }
