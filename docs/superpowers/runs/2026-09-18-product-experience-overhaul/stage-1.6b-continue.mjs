export const meta = {
  name: 'pxo-1-6-execute-cont',
  description: 'Superstorm 1.6: continuation after D-0003: T-M5-14 (amended acceptance), T-M5-15, T-M5-16 (executor opus, fresh supervisor on session model, cap 3, path mutex)',
  phases: [
    { title: 'Execute', detail: 'one executor per ready task', model: 'opus' },
    { title: 'Supervise', detail: 'fresh-context supervisor reruns the real acceptance_cmd' },
  ],
}

const REPO = '/Users/aa/workspace/myskills'
const RUN = REPO + '/docs/superpowers/runs/2026-09-18-product-experience-overhaul'
const CAP = 3
const EXECUTOR_MODEL = 'opus'
const TASKS = [
 {
  "id": "T-M5-14",
  "title": "Full validation and baseline comparison: failure set must be within the four known failures; write verification-M5.md",
  "touched_paths": [
   "docs/superpowers/runs/2026-09-18-product-experience-overhaul/verification-M5.md"
  ],
  "acceptance_cmd": "python3 -c 'import subprocess,re,sys; r=subprocess.run([sys.executable,\"-m\",\"pytest\",\"-q\",\"-rfE\",\"claude/meta-skill/tests/unit\"],capture_output=True,text=True); out=r.stdout; bad={l.split()[1] for l in out.splitlines() if l.startswith((\"FAILED \",\"ERROR \"))}; U=\"claude/meta-skill/tests/unit/\"; base={U+\"test_decision_gate.py::test_a_resolved_choice_restores_readiness_only_with_fresh_evidence[claude]\",U+\"test_decision_gate.py::test_a_resolved_choice_restores_readiness_only_with_fresh_evidence[codex]\",U+\"test_evidence_freshness.py::test_fresh_contract_allows_execution_but_cannot_claim_completion[claude]\",U+\"test_evidence_freshness.py::test_fresh_contract_allows_execution_but_cannot_claim_completion[codex]\"}; m=re.search(r\"(\\d+) passed\",out); print(out[-2000:]); print(\"unexpected:\",sorted(bad-base)); sys.exit(0 if r.returncode in (0,1) and m and int(m.group(1))>=1198 and bad<=base else 1)' && python3 -m pytest -q claude/superstorm/scripts && python3 -m pytest -q codex/cross-exam-skill/scripts && python3 -m pytest -q shared/evidence-engine && python3 -m pytest -q shared/visual-acceptance && python3 -m pytest -q shared/scripts/orchestrator && python3 -m pytest -q shared/keep-code-simple && python3 -m pytest -q pi/cross-exam && python3 -m pytest -q pi/meta-skill/test_contract.py codex/meta-skill/test_flow.py codex/meta-skill/test_install.py && python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py && python3 claude/superstorm/scripts/check_skill_refs.py && python3 -m pytest -q claude/meta-skill/tests/unit/test_consumer_product_regression.py && python3 -m pytest -q claude/superstorm/scripts/test_package_manifests.py && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py && ! grep -rn \"experience_priority\" claude/meta-skill/knowledge | grep -v \"experience_priority.mode\" | grep -v bootstrap | grep -q . && grep -q '^status: pass' docs/superpowers/runs/2026-09-18-product-experience-overhaul/verification-M5.md && grep -q '6a59fe44' docs/superpowers/runs/2026-09-18-product-experience-overhaul/verification-M5.md",
  "deps": [],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md",
  "extra": "ORCHESTRATOR NOTE (decision D-0003): the acceptance_cmd you escalated has been amended — its sixth segment is now three separate pytest invocations. Your earlier work is committed (see git log: 4d9e666f, d2e94dbf, 4c4f4329). Re-run the amended acceptance_cmd at the current HEAD; if verification-M5.md needs to reflect the current HEAD or the amended command string, update and commit it. Do not fabricate numbers: record what the run actually printed."
 },
 {
  "id": "T-M5-15",
  "title": "Release commit message draft with verification numbers, baseline SHA and upgrade impact",
  "touched_paths": [
   "docs/superpowers/runs/2026-09-18-product-experience-overhaul/release-commit-message.txt"
  ],
  "acceptance_cmd": "F=docs/superpowers/runs/2026-09-18-product-experience-overhaul/release-commit-message.txt; head -1 \"$F\" | grep -q '^release: superstorm 0.43.0, meta-skill 0.20.0' && grep -q '6a59fe44' \"$F\" && grep -q 'missing_experience_priority' \"$F\" && grep -q 'local-change' \"$F\" && grep -q '尚未验证' \"$F\" && grep -Eq '[0-9]+ passed' \"$F\" && grep -q '^status: pass' docs/superpowers/runs/2026-09-18-product-experience-overhaul/verification-M5.md",
  "deps": [
   "T-M5-14"
  ],
  "resources": [],
  "reality_gate": false,
  "runbook_ptr": "",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md",
  "extra": ""
 },
 {
  "id": "T-M5-16",
  "title": "Real-host acceptance: rerun the original ink-scent request through /bootstrap, /run, /product-review and record the three symptoms",
  "touched_paths": [
   "docs/validation/product-experience-host-run.md"
  ],
  "acceptance_cmd": "F=docs/validation/product-experience-host-run.md; grep -q '^## 症状对照' \"$F\" && grep -q '症状 1' \"$F\" && grep -q '症状 2' \"$F\" && grep -q '症状 3' \"$F\" && [ \"$(grep -c 'verdict: \\(fixed\\|not-fixed\\|partial\\)' \"$F\")\" -ge 3 ] && grep -q '^host-run: pass' \"$F\"",
  "deps": [
   "T-M5-14"
  ],
  "resources": [],
  "reality_gate": true,
  "runbook_ptr": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md#runbook-real-host-bootstrap-run",
  "plan": "docs/superpowers/plans/2026-09-18-regression-parity-plan.md",
  "design": "docs/superpowers/specs/2026-09-18-regression-parity-design.md",
  "extra": "ORCHESTRATOR NOTE: this is a reality_gate task. A real interactive host session with a human is NOT available to you. You MUST NOT write `host-run: pass`, MUST NOT invent symptom verdicts, and MUST NOT simulate the host run with subagents. Your job is only to make the human runbook complete and executable: create the touched file as an explicitly UNFILLED template (e.g. `host-run: pending`, verdict fields left as `verdict: <fixed|not-fixed|partial — to be filled by the human>` in a form that does NOT match the acceptance grep), containing the exact steps from the runbook, then commit it. The acceptance_cmd is expected to FAIL here; report self_reported_done:false with the reason \"awaiting real-host verification\". That is the correct outcome, not a failure on your part."
 }
]

const EXEC_SCHEMA = { type: 'object', required: ['status', 'task_id', 'self_reported_done'],
  properties: { status: { type: 'string', enum: ['ok', 'escalate'] }, task_id: { type: 'string' },
    acceptance_cmd: { type: 'string' }, self_reported_done: { type: 'boolean' }, notes: { type: 'string' },
    commit: { type: 'string' }, reason: { type: 'string' }, evidence: { type: 'string' },
    proposed_touched_paths: { type: 'array', items: { type: 'string' } } } }

const VERDICT_SCHEMA = { type: 'object', required: ['done', 'rerun_exit_code', 'evidence'],
  properties: { done: { type: 'boolean' }, rerun_exit_code: { type: 'integer' }, evidence: { type: 'string' },
    refutation: { type: 'string' }, vacuous: { type: 'boolean' }, reality_gated: { type: 'boolean' },
    observations: { type: 'array', items: { type: 'object', required: ['scope', 'finding', 'evidence'],
      properties: { scope: { type: 'string' }, finding: { type: 'string' }, evidence: { type: 'string' } } } } } }

function execPrompt(t, attempt, refutation, vacuous) {
  return [
    '# Executor agent — implements one task against its contract',
    '',
    'You implement ONE task. You are headless: never ask a human anything.',
    'Target repository: ' + REPO + ' (NOT your cwd — `cd` there or use absolute paths). Branch: product-experience-overhaul (already checked out; never switch branches, never reset, never stash, never push, never rebase, never amend other commits).',
    'There is NO worktree isolation: other executors are editing OTHER files in this same tree right now. Never touch, stage, revert or "fix" a file outside your touched_paths, even if it looks broken or half-written — it belongs to a running task.',
    '',
    'Task id: ' + t.id,
    'Title: ' + t.title,
    'Full task contract (interface & behaviour, test intent, acceptance, write set): read the section for ' + t.id + ' in ' + REPO + '/' + t.plan,
    'Module design (frozen requirements + Detailed design): ' + REPO + '/' + t.design,
    'touched_paths (repo-relative): ' + JSON.stringify(t.touched_paths),
    'acceptance_cmd (run with cwd = ' + REPO + '): ' + t.acceptance_cmd,
    '',
    '## Discipline',
    '1. TDD: write the failing test the task\'s test intent describes, see it fail, implement, see it pass. The interface and behaviour are fixed; the route inside touched_paths is yours. Match the surrounding code and prose style of each file.',
    '2. Touch ONLY files in touched_paths. If the change genuinely needs a file outside that set, STOP and return status:"escalate" with proposed_touched_paths (exact repo-relative files and why). Never work around it with a stub or an out-of-set edit.',
    '3. Run acceptance_cmd yourself (Bash timeout up to 600000 ms; tee long output to ' + RUN + '/logs/' + t.id + '.log). Do not claim done if it fails. If it fails ONLY because of a file outside your touched_paths that another task is mid-edit on (check `git status --short`), wait ~60s and rerun, up to 5 times, before treating it as your problem.',
    '4. Anti-vacuous: if acceptance selects tests by name/node id, those tests must exist with real assertions and the run must report a non-zero executed count.',
    '5. Divergence circuit-breaker: after 5 consecutive failed acceptance runs without a genuinely new hypothesis, return status:"escalate" with the hypothesis log (what changed, expected, actual).',
    '6. Known baseline: the full claude/meta-skill unit suite has exactly 4 pre-existing failures (test_decision_gate::test_a_resolved_choice_restores_readiness_only_with_fresh_evidence[claude|codex], test_evidence_freshness::test_fresh_contract_allows_execution_but_cannot_claim_completion[claude|codex]). Never edit or "fix" them. Never run `pytest pi/meta-skill` or `pytest codex/meta-skill` as directories.',
    '',
    '## Commit protocol (mandatory — the supervisor verifies the COMMITTED tree)',
    'When acceptance passes, commit exactly your files, serialized with the shared lock:',
    '  cd ' + REPO,
    '  until mkdir /tmp/pxo-commit.lock 2>/dev/null; do sleep 7; done',
    '  git add -- <each touched path that exists> ; git commit -m "<message>" -- <the same paths> ; rc=$? ; rmdir /tmp/pxo-commit.lock',
    'ALWAYS release the lock (rmdir) even if the commit fails. Never use --no-verify, never `git add -A` / `git add .`, never `git commit -a`.',
    'The pre-commit hook runs fast test batteries and validators over the whole working tree (~30s). If it fails because of YOUR files, fix and retry. If it fails because of another task\'s in-progress file, release the lock, wait ~60s, retry (up to 5 times).',
    'Commit message: repo convention — subject names what is now true (Chinese or English, e.g. `feat(meta-skill): …` / `test(meta-skill): …` / `docs(…): …`), mention the task id ' + t.id + ' in the body, and end the body with the trailer line:',
    '  Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>',
    'After committing, `git status --porcelain -- <touched paths>` must print nothing.',
    '',
    t.extra ? ('## ' + t.extra) : '',
    attempt > 1 ? ('## This is attempt ' + attempt + '. An independent supervisor REFUTED the previous attempt:\n' + (refutation || '(no refutation text)') + '\nYour earlier work may already be committed — inspect `git log --oneline -8` and the current files first, then fix what the refutation names and commit again.') : '',
    vacuous ? '## ANTI-VACUOUS: the previous acceptance passed only because ZERO tests ran. Create the named test(s) with at least one real assertion exercising your implementation and prove a non-zero executed-test count.' : '',
    '',
    '## Output',
    'Return JSON {status:"ok"|"escalate", task_id, acceptance_cmd, self_reported_done, notes, commit?, reason?, evidence?, proposed_touched_paths?}. Your self-report is NOT trusted — an independent supervisor reruns acceptance_cmd. Do not inflate.',
  ].join('\n')
}

function supPrompt(t) {
  return [
    '# Supervisor agent — anti-fake-completion verifier',
    '',
    'You independently verify ONE task that is claimed done. You are adversarial; default to disbelief. You are NOT given the executor\'s narrative. You trust reruns, not claims.',
    'Repository: ' + REPO + ' (NOT your cwd). Branch product-experience-overhaul. You are READ-ONLY: never edit, stage, commit, reset or stash anything. Other tasks are concurrently editing OTHER files in this tree.',
    '',
    'Task id: ' + t.id + ' — ' + t.title,
    'Task contract: the section for ' + t.id + ' in ' + REPO + '/' + t.plan + ' ; design: ' + REPO + '/' + t.design,
    'touched_paths: ' + JSON.stringify(t.touched_paths),
    'acceptance_cmd (cwd = ' + REPO + '): ' + t.acceptance_cmd,
    t.reality_gate ? ('This task carries reality_gate:true. Runbook: ' + t.runbook_ptr) : 'This task does NOT carry reality_gate — never set reality_gated.',
    '',
    '## Verify',
    '1. Rerun acceptance_cmd yourself from ' + REPO + ' (Bash timeout 600000 ms; tee output to ' + RUN + '/logs/' + t.id + '.supervisor.log). Capture the real exit code and output.',
    '2. done is true ONLY if exit code == 0 AND the output shows the behaviour genuinely works.',
    '3. Vacuous check: if 0 tests ran / nothing was collected / a grep-only command would have passed before this task → vacuous:true, done:false.',
    '4. Read the real diff (`git log --oneline -12`, `git show --stat`, `git diff` for the touched paths): do the changes correspond to the task\'s intent, in the right files, and ONLY there? A task that edited files outside touched_paths is refuted.',
    '5. Absence check: for each behaviour the contract promises (a blocker code emitted, a gate registered in main() AND structural_gate_blockers, a field written into the journal, a literal pinned by a validator, a twin file dual-written), trace that it is actually wired, not merely defined. Hunt for what SHOULD be present.',
    '6. Committed-tree check: `git status --porcelain -- <each touched path>` must print nothing; any modified/untracked touched path → done:false naming the dirty paths.',
    '7. If the rerun fails ONLY because of a file outside touched_paths that is currently dirty in `git status --short` (another running task mid-edit), wait ~60s and rerun, up to 4 times, before judging. Known baseline: the full claude/meta-skill unit suite has exactly 4 pre-existing failures (test_decision_gate …fresh_evidence[claude|codex], test_evidence_freshness …cannot_claim_completion[claude|codex]); they are not this task\'s defect.',
    '',
    '## Output (verdict schema)',
    '{done, rerun_exit_code, evidence:"<real captured output, trimmed>", refutation?, vacuous?, reality_gated?, observations?}. observations: anything outside THIS task ({scope:"task:<id>"|"repo", finding, evidence}). It never changes done.',
  ].join('\n')
}

const byId = {}
TASKS.forEach(t => { byId[t.id] = t })
const state = {}      // id -> {status, attempts, effective_model, first_model, last_evidence_excerpt, observations}
const running = new Map()
const observations = []
const escalations = []
const realityGated = []

function locksOf(t) { return t.touched_paths.concat((t.resources || []).map(r => 'res:' + r)) }
function conflicts(t) {
  const mine = new Set(locksOf(t))
  for (const id of running.keys()) { if (locksOf(byId[id]).some(p => mine.has(p))) return true }
  return false
}
function satisfied(id) { const s = state[id]; return s && (s.status === 'done' || s.status === 'reality_gated') }
function dead(id) { const s = state[id]; return s && (s.status === 'failed' || s.status === 'skipped') }

async function runTask(t) {
  const st = { status: 'dispatched', attempts: 0, effective_model: EXECUTOR_MODEL, first_model: null, infra_failures: 0 }
  state[t.id] = st
  let refutation = '', vacuous = false, model = EXECUTOR_MODEL, defective = 0
  while (st.attempts < 3) {
    st.attempts += 1
    let ex = await agent(execPrompt(t, st.attempts, refutation, vacuous),
      Object.assign({ label: 'exec:' + t.id + (st.attempts > 1 ? '#' + st.attempts : ''), phase: 'Execute', schema: EXEC_SCHEMA }, model ? { model } : {}))
    if (!ex) {                                   // infrastructure failure: never spends business budget
      st.infra_failures += 1; st.attempts -= 1
      defective += 1
      if (defective >= 2 && model) { st.first_model = model; model = null; st.effective_model = 'session'; log(t.id + ': executor returned null twice on ' + EXECUTOR_MODEL + ' → session model') }
      if (st.infra_failures >= 3) { st.status = 'failed'; st.last_evidence_excerpt = 'infrastructure: executor returned null 3 times'; return }
      continue
    }
    if (ex.status === 'escalate') {
      const extra = (ex.proposed_touched_paths || []).filter(p => !t.touched_paths.includes(p))
      const inRepo = extra.every(p => !p.startsWith('/') && !p.startsWith('..'))
      if (extra.length && inRepo && !st.extended) {
        const busy = extra.some(p => { for (const id of running.keys()) { if (id !== t.id && byId[id].touched_paths.includes(p)) return true } return false })
        st.extended = extra; t.touched_paths = t.touched_paths.concat(extra)
        log(t.id + ': plan defect — touched_paths extended with ' + JSON.stringify(extra) + (busy ? ' (collides with a running task; executor told to wait-and-retry)' : ''))
        st.attempts -= 1; st.status = 'redispatched'
        refutation = 'touched_paths now also includes ' + JSON.stringify(extra) + '. Resume your work-in-progress.'
        continue
      }
      st.status = 'failed'; st.last_evidence_excerpt = ('escalate: ' + (ex.reason || '') + ' | ' + (ex.evidence || '')).slice(0, 1200)
      st.proposed_touched_paths = ex.proposed_touched_paths || []
      return
    }
    const v = await agent(supPrompt(t), { label: 'sup:' + t.id + (st.attempts > 1 ? '#' + st.attempts : ''), phase: 'Supervise', schema: VERDICT_SCHEMA })
    if (!v) { st.infra_failures += 1; st.attempts -= 1; if (st.infra_failures >= 3) { st.status = 'failed'; st.last_evidence_excerpt = 'infrastructure: supervisor returned null'; return } refutation = 'The supervisor could not be reached; re-verify your committed work and report again.'; continue }
    ;(v.observations || []).forEach(o => observations.push(Object.assign({ task_id: t.id }, o)))
    st.last_evidence_excerpt = (v.evidence || '').slice(0, 1200)
    if (v.done) { st.status = 'done'; return }
    if (t.reality_gate && v.reality_gated) { st.status = 'reality_gated'; realityGated.push({ task_id: t.id, reason: (v.evidence || '').slice(0, 800), runbook_ptr: t.runbook_ptr }); return }
    if (t.reality_gate) { st.status = 'failed'; st.last_evidence_excerpt = ('reality_gate task, code defect: ' + (v.refutation || '')).slice(0, 1200); return }
    refutation = v.refutation || v.evidence || ''
    vacuous = !!v.vacuous
    st.status = 'redispatched'
    if (st.attempts === 1 && model) { /* first business failure on the downgraded executor: retry once on the same model */ }
    else if (model) { st.first_model = model; model = null; st.effective_model = 'session'; log(t.id + ': second refutation on ' + EXECUTOR_MODEL + ' → redispatch on session model') }
  }
  st.status = 'failed'
  st.last_evidence_excerpt = ('business retries exhausted. last refutation: ' + refutation).slice(0, 1200)
}

phase('Execute')
while (true) {
  let changed = true
  while (changed) {                                // transitive skip
    changed = false
    for (const t of TASKS) {
      if (state[t.id]) continue
      const blocker = t.deps.find(dead)
      if (blocker) { state[t.id] = { status: 'skipped', blocked_by: state[blocker].blocked_by || blocker, attempts: 0 }; changed = true }
    }
  }
  for (const t of TASKS) {
    if (running.size >= CAP) break
    if (state[t.id] || running.has(t.id)) continue
    if (!t.deps.every(satisfied)) continue
    if (conflicts(t)) continue
    const p = runTask(t).catch(e => { state[t.id] = Object.assign(state[t.id] || {}, { status: 'failed', last_evidence_excerpt: 'orchestrator exception: ' + String(e).slice(0, 600) }) })
      .then(() => { running.delete(t.id); const s = state[t.id]; log(t.id + ' → ' + s.status + ' (attempts ' + s.attempts + ', ' + (s.effective_model || '-') + ')'); if (s.status === 'failed') escalations.push({ task_id: t.id, reason: s.last_evidence_excerpt, retries: s.attempts, proposed_touched_paths: s.proposed_touched_paths || [] }) })
    running.set(t.id, p)
  }
  if (running.size === 0) break
  await Promise.race(Array.from(running.values()))
}
const counts = {}
TASKS.forEach(t => { const s = (state[t.id] || { status: 'never-ready' }).status; counts[s] = (counts[s] || 0) + 1 })
const unscheduled = TASKS.filter(t => !state[t.id]).map(t => t.id)
return { counts, unscheduled, state, escalations, realityGated, observations }
