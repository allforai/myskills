export const meta = {
  name: 'pxo-1-2-1-3-critic-plan',
  description: 'Superstorm 1.2 closure critique then 1.3 per-module implementation planning (session model)',
  phases: [
    { title: 'Closure critique', detail: 'one fresh critic over all six designs, self-fix up to 3 rounds' },
    { title: 'Plan', detail: 'one plan agent per module' },
  ],
}

const REPO = '/Users/aa/workspace/myskills'
const SPECS = REPO + '/docs/superpowers/specs'
const PLANS = REPO + '/docs/superpowers/plans'
const RUN = REPO + '/docs/superpowers/runs/2026-09-18-product-experience-overhaul'
const OVERVIEW = SPECS + '/2026-09-18-product-experience-overhaul-overview.md'

const MODULES = [
  { module: 'M1', slug: 'design-routing' },
  { module: 'M2', slug: 'experience-intent' },
  { module: 'M3', slug: 'experience-gate' },
  { module: 'M4', slug: 'spec-gap-discipline' },
  { module: 'M5', slug: 'regression-parity' },
  { module: 'M6', slug: 'review-alignment' },
]

const ESCALATION = {
  type: 'object', required: ['status'],
  properties: {
    status: { type: 'string', enum: ['ok', 'escalate'] },
    reason: { type: 'string' }, evidence: { type: 'string' },
    changed_files: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
  },
}

const PLAN_SCHEMA = {
  type: 'object', required: ['status', 'plan_path', 'tasks'],
  properties: {
    status: { type: 'string', enum: ['ok', 'escalate'] },
    plan_path: { type: 'string' },
    tasks: { type: 'array', items: {
      type: 'object', required: ['id', 'title', 'touched_paths', 'acceptance_cmd', 'depends_on'],
      properties: {
        id: { type: 'string' }, title: { type: 'string' },
        touched_paths: { type: 'array', items: { type: 'string' }, minItems: 1 },
        acceptance_cmd: { type: 'string' },
        depends_on: { type: 'array', items: { type: 'string' } },
        implements: { type: 'array', items: { type: 'string' } },
        requires: { type: 'array', items: { type: 'string' } },
        resources: { type: 'array', items: { type: 'string' } },
        reality_gate: { type: 'boolean' },
        runbook_ptr: { type: 'string' },
      } } },
    size_warning: { type: 'object', properties: { count: { type: 'integer' }, seams: { type: 'array', items: { type: 'string' } } } },
    reason: { type: 'string' }, evidence: { type: 'string' },
  },
}

const COMMON = [
  'You are headless. You CANNOT ask the human anything. Target repository: ' + REPO + ' (NOT your cwd) — use absolute paths.',
  'Branch `product-experience-overhaul`. Do NOT run any git mutation (commit/checkout/reset/stash); the orchestrator commits.',
  'Frozen registry: between the superstorm-registry markers in ' + OVERVIEW + ' (also ' + RUN + '/registry.json). Never invent requirement IDs or interface names.',
  'Design manifests: ' + RUN + '/manifests.json. Design agents\' notes (spec corrections, consequences): ' + RUN + '/design-notes.json.',
].join('\n')

const CRITIC = [
  '# Closure critic — 闭环思维 (LLM half)', '', COMMON, '',
  'The deterministic half (coverage / interface / orphan) already ran via check_closure.py and passed.',
  'The six module design docs are ' + SPECS + '/2026-09-18-{design-routing,experience-intent,experience-gate,spec-gap-discipline,regression-parity,review-alignment}-design.md.',
  'Each has the approved requirements at the top (FROZEN — never delete, renumber or weaken) and a `## Detailed design` section appended by a design agent.',
  '',
  '## Check',
  '- For each covers_req_ids claim: read the requirement and the design section. Is the requirement genuinely met, or only name-matched? Flag hollow coverage.',
  '- For each exposes/consumes pair: do the two sides agree on shape and semantics, not just the name? In particular check:',
  '  * data:experiencePriority — M1\'s profile field shape vs how M2 (validate_scope blocker) and M3 (gate trigger) read it;',
  '  * data:experienceDesignArtifacts — M1\'s artifact path contract vs M3\'s design-stage inputs and M4\'s settings spec paths (M1 corrected the game design doc path; do siblings agree?);',
  '  * data:experienceDirectionIntent — M2\'s generated intent entry (id scheme, fields, auto_decided/delegated) vs how M3 reads its acceptance and M6 reads who/circumstance;',
  '  * data:experienceCritiqueReport / data:experienceReviewDoc / data:experienceLensVocabulary — M3\'s paths, stage names and the five lens identifiers vs M6\'s reads and parity test;',
  '  * data:settingsAudience / data:unspecifiedDecisionGap — M4\'s field names and enum values vs M3\'s audience_leak dimension and M5\'s thought-test cases;',
  '  * the blocker codes each validator emits vs the codes M5\'s regression fixture asserts (M5 already noted the three gates do not report all codes in one call).',
  '- Shared hot files (scripts/orchestrator/validate_bootstrap.py, validate_meta_contracts.py, knowledge/bootstrap-planning.md, tests/unit/test_validate_bootstrap.py, tests/unit/test_bootstrap_scope.py, skills/bootstrap/SKILL.md, scripts/orchestrator/check_artifacts.py): do two designs make contradictory edits to the same region or the same shared fixture? They will be applied serially in order M1 → (M2 ∥ M4) → M3 → M6 → M5.',
  '- Any design element that traces to NO requirement (dead design)?',
  '',
  '## Self-fix loop (≤3 rounds)',
  'If you find fixable gaps, EDIT the `## Detailed design` sections to close them (never the frozen requirement sections). Re-check only what you changed.',
  '',
  '## Output (escalation schema)',
  '- All closed → {status:"ok", changed_files, summary}.',
  '- A gap requires a choice that changes module boundaries / registry / user-visible scope, or cannot converge in 3 rounds → {status:"escalate", reason, evidence} with viable options and a ranked recommendation. Never ask the human.',
].join('\n')

function planPrompt(m) {
  const design = SPECS + '/2026-09-18-' + m.slug + '-design.md'
  const plan = PLANS + '/2026-09-18-' + m.slug + '-plan.md'
  return [
    '# Plan agent — turns one module design into task contracts', '', COMMON, '',
    'Module: ' + m.module + ' (' + m.slug + '). Design (requirements + Detailed design): ' + design,
    'Write the plan to: ' + plan + ' (create the file; you may modify ONLY that file).',
    '',
    '## What a task is',
    'A task is a contract, not a script. The executor is a capable engineer who needs to know what must be true, not which keystrokes to make. Each task states:',
    '1. Interface and behaviour: what becomes true when the task is done, in the registry\'s vocabulary; which contract it implements or consumes.',
    '2. Test intent: what the failing test asserts and why that assertion proves the behaviour — the assertion, not the test file\'s source.',
    '3. Acceptance: the exact acceptance_cmd, structurally unable to pass on zero tests.',
    '4. Write set: touched_paths complete enough that the executor never has to leave it. Check every new literal, enum member, blocker code, config key against the file that defines its legal set — that file belongs in touched_paths.',
    'Code appears only where the contract is the code: a schema shape, a function signature. Never a full implementation body.',
    '',
    '## HARD CONSTRAINTS — every task object MUST carry',
    '- id: `T-' + m.module + '-NN`. title: one line.',
    '- touched_paths: REPO-RELATIVE paths (relative to ' + REPO + '), every file the task creates/modifies, non-empty. These drive serialization: two tasks that list the same path never run concurrently.',
    '- acceptance_cmd: a machine-checkable shell command that exits 0 iff the task is truly done. It is executed with cwd = ' + REPO + '. Rules for this repo:',
    '  * use `python3 -m pytest -q <explicit test file paths>`; never `pytest pi/meta-skill` or `pytest codex/meta-skill` as directories (symlink collection clash); never run claude/superstorm/scripts and codex/cross-exam-skill/scripts in one pytest invocation (duplicate basenames);',
    '  * do NOT use the full `claude/meta-skill/tests/unit` directory as a task acceptance (≈6 min and has 4 known pre-existing failures: test_decision_gate ... fresh_evidence[claude|codex], test_evidence_freshness ... cannot_claim_completion[claude|codex]). Only M5\'s full-validation task may run it, and it must compare the failure SET to exactly those four rather than require exit 0;',
    '  * prose-only edits need a real check too: a validator run (validate_meta_contracts.py, validate_skills.py, validate_app_experience_pipeline.py), or `grep -q` for the exact pinned literals combined with `&&`. A command that would pass before the task is done is a defect;',
    '  * when selecting tests with -k, the command must fail if zero tests are selected (e.g. add `--co -q | grep -q <name> &&` before it, or select by explicit node id).',
    '- depends_on: INTRA-module task ids only ([] if none). Never guess a foreign task id.',
    '',
    '## Cross-module ordering',
    '- Tag `implements: ["<kind>:<name>"]` on THE one task whose acceptance_cmd proves that exposed interface consumable. Every interface this module exposes (see manifests.json) MUST be implemented by exactly one of your tasks.',
    '- Tag `requires: ["<kind>:<name>"]` on each task that consumes an interface from another module (this module\'s `consumes`). Omitting it lets your task run before its dependency exists.',
    '- Names verbatim from the frozen registry.',
    '',
    '## Reality-gate classification (mandatory pass over every task)',
    'Tag `reality_gate: true` ONLY for a task whose acceptance genuinely needs a real interactive LLM host session with a human (real /bootstrap dialogue quality). Thought tests run with fresh-context subagents ARE autonomous here — the executor may spawn subagents — so they are NOT reality-gated. A reality_gate task still needs a real non-empty acceptance_cmd, must carry `runbook_ptr` (plan path + heading anchor) with exact human steps written into the plan markdown, and must never be a depends_on of another task.',
    '',
    '## Granularity',
    'Bite-sized TDD tasks: test first where a test exists. Keep each task\'s touched_paths small. Shared hot files (validate_bootstrap.py, validate_meta_contracts.py, bootstrap-planning.md, test_validate_bootstrap.py, test_bootstrap_scope.py, skills/bootstrap/SKILL.md, check_artifacts.py) are serialized across modules by path collision, so prefer one task per hot file rather than touching a hot file in many tasks.',
    'Roughly 20 tasks is a signal to look for a seam, not a limit. Never merge tasks to hide size, never drop scope. If larger, emit in full and add size_warning {count, seams}.',
    '',
    '## Output',
    'Return JSON {status, plan_path, tasks:[...], size_warning?, reason?, evidence?}. plan_path repo-relative: docs/superpowers/plans/2026-09-18-' + m.slug + '-plan.md. If the design is under-specified, return status:"escalate" with viable options and a ranked recommendation.',
  ].join('\n')
}

phase('Closure critique')
const critique = await agent(CRITIC, { label: 'closure-critic', phase: 'Closure critique', schema: ESCALATION })
log('closure critic: ' + (critique ? critique.status : 'null'))

phase('Plan')
const plans = await parallel(MODULES.map(m => () =>
  agent(planPrompt(m), { label: 'plan:' + m.module, phase: 'Plan', schema: PLAN_SCHEMA })
    .then(r => r ? Object.assign({ module: m.module }, r) : { module: m.module, status: 'escalate', plan_path: '', tasks: [], reason: 'agent returned null (infrastructure)' })
))
return { critique, plans }
