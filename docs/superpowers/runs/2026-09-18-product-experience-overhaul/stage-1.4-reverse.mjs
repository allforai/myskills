export const meta = {
  name: 'pxo-1-4-reverse-review',
  description: 'Superstorm 1.4: whole-plan reverse review (backward feasibility, weak acceptance commands)',
  phases: [{ title: 'Reverse review', detail: 'two fresh critics split by module group, then a cross-module pass' }],
}

const REPO = '/Users/aa/workspace/myskills'
const SPECS = REPO + '/docs/superpowers/specs'
const PLANS = REPO + '/docs/superpowers/plans'
const RUN = REPO + '/docs/superpowers/runs/2026-09-18-product-experience-overhaul'

const SCHEMA = {
  type: 'object', required: ['status'],
  properties: {
    status: { type: 'string', enum: ['ok', 'escalate'] },
    reason: { type: 'string' }, evidence: { type: 'string' },
    changed_files: { type: 'array', items: { type: 'string' } },
    findings_fixed: { type: 'array', items: { type: 'string' } },
    residual_risks: { type: 'array', items: { type: 'string' } },
  },
}

function prompt(scope, focus) {
  return [
    '# Reverse critic — 逆向思维', '',
    'You are headless. You CANNOT ask the human anything. Target repository: ' + REPO + ' (NOT your cwd) — use absolute paths.',
    'Branch `product-experience-overhaul`. Do NOT run any git mutation; the orchestrator commits. Do not modify product source files — only the docs named below.',
    '',
    'Work BACKWARD from the plans/designs to the specs. Do not read forward and nod along — actively try to refute that this will work.',
    '',
    'Inputs:',
    '- Overview + frozen registry: ' + SPECS + '/2026-09-18-product-experience-overhaul-overview.md',
    '- Designs (frozen requirements on top, `## Detailed design` below): ' + SPECS + '/2026-09-18-*-design.md',
    '- Plans: ' + PLANS + '/2026-09-18-*-plan.md',
    '- Machine-readable task contracts (what the executor and the DAG actually consume): ' + RUN + '/tasks/M1.json … M6.json',
    '- Task validator: python3 /Users/aa/.claude/plugins/cache/myskills/superstorm/0.42.2/scripts/validate_plan_tasks.py <tasks.json> ' + RUN + '/registry.json',
    '',
    'Your scope: ' + scope,
    '',
    '## Check (backward feasibility)',
    '- Take each plan and ask: if an engineer executes exactly these task contracts, do they end up satisfying the design and every frozen requirement? Where does it break?',
    '- Hunt hidden assumptions, missing prerequisites, infeasible steps, unhandled error/edge paths. Open the real files the tasks touch and check the claims.',
    '- For each acceptance_cmd (it runs with cwd = ' + REPO + '): is it a meaningful check, or a tautology that would pass WITHOUT the feature working? Would it already pass today, before the task? (You may run read-only commands such as pytest --co, grep, and the validators to find out; do not leave any file changed by doing so.) Could it pass on zero selected tests? Does it name a test file the task does not create or list in touched_paths? Does it run a directory that is known to fail collection (pi/meta-skill, codex/meta-skill) or the full 6-minute meta-skill suite?',
    '- touched_paths completeness: does the task write any file it does not list (fixtures, the file defining an enum/blocker-code set it extends, a pre-commit hook, a twin file)? A missing path lets two tasks edit one file concurrently.',
    '- depends_on / implements / requires: is every exposed registry interface implemented by exactly one task, is every consumed interface tagged `requires` on the task that needs it, and does any task depend on a reality_gate task?',
    focus,
    '',
    '## Self-fix loop (≤3 rounds)',
    'Fixable issues → edit the plan markdown AND the matching entries in ' + RUN + '/tasks/<module>.json so the two stay identical in meaning (ids stable; never delete a task that carries an `implements` tag without moving the tag). You may also edit a `## Detailed design` section. NEVER edit the frozen requirement sections, the registry, or another scope\'s files unless the defect is cross-module. After editing a tasks JSON, re-run the task validator on it and make it pass.',
    '',
    '## Output (escalation schema)',
    '- Sound → {status:"ok", changed_files, findings_fixed, residual_risks}.',
    '- Requires a choice that changes module boundaries / the registry / user-visible scope, or is non-convergent → {status:"escalate", reason, evidence} with viable options and a ranked recommendation. Never request human input.',
  ].join('\n')
}

phase('Reverse review')
const [a, b] = await parallel([
  () => agent(prompt('modules M1 (design-routing), M2 (experience-intent), M4 (spec-gap-discipline). Edit only their plans, their tasks JSON and their Detailed design sections.',
    '- M1/M2 specific: M1 registers a new structural check into gates that ~10 existing test files exercise through shared fixtures; M2 adds a topic that changes gap-question generation and freeze total-coverage. Verify the plans really keep the existing suites green, in the order M1 → M2.'),
    { label: 'reverse:M1-M2-M4', phase: 'Reverse review', schema: SCHEMA }),
  () => agent(prompt('modules M3 (experience-gate), M6 (review-alignment), M5 (regression-parity). Edit only their plans, their tasks JSON and their Detailed design sections.',
    '- M3/M5/M6 specific: M3 registers a second structural check after M1 and M2 land; M5 builds good/bad workflow fixtures that must be rejected/accepted by ALL of M1+M2+M3\'s checks plus the pre-existing ones (mobile UI coverage, repair-loop declaration, plan confirmation); M6 dual-writes claude and codex twins. M5\'s thought-test tasks spawn fresh-context subagents: check that their acceptance commands verify recorded evidence files with real content (case ids, verdicts) rather than mere file existence, and that T-M5-16 (reality gate) has a runbook and nothing depends on it.'),
    { label: 'reverse:M3-M6-M5', phase: 'Reverse review', schema: SCHEMA }),
])
return { group_a: a, group_b: b }
