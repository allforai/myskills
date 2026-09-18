export const meta = {
  name: 'pxo-1-1-design',
  description: 'Superstorm 1.1: parallel module design for the product-experience overhaul (6 modules)',
  phases: [{ title: 'Design', detail: 'one design agent per module, session model' }],
}

const REPO = '/Users/aa/workspace/myskills'
const SPECS = REPO + '/docs/superpowers/specs'
const OVERVIEW = SPECS + '/2026-09-18-product-experience-overhaul-overview.md'

const MODULES = [
  { module: 'M1', slug: 'design-routing' },
  { module: 'M2', slug: 'experience-intent' },
  { module: 'M3', slug: 'experience-gate' },
  { module: 'M4', slug: 'spec-gap-discipline' },
  { module: 'M5', slug: 'regression-parity' },
  { module: 'M6', slug: 'review-alignment' },
]

const MANIFEST_SCHEMA = {
  type: 'object',
  required: ['status', 'module', 'design_path', 'covers_req_ids', 'exposes', 'consumes'],
  properties: {
    status: { type: 'string', enum: ['ok', 'escalate'] },
    module: { type: 'string' },
    design_path: { type: 'string' },
    covers_req_ids: { type: 'array', items: { type: 'string' } },
    exposes: { type: 'array', items: { type: 'string' } },
    consumes: { type: 'array', items: { type: 'string' } },
    reason: { type: 'string' },
    evidence: { type: 'string' },
  },
}

function prompt(m) {
  const spec = SPECS + '/2026-09-18-' + m.slug + '-design.md'
  return [
    '# Design agent — one module design from the frozen registry',
    '',
    'You are a headless design agent. You CANNOT ask the human anything — all user decisions were',
    'front-loaded in Phase 0. The target repository is ' + REPO + ' (NOT your cwd). Use absolute paths.',
    'You are on git branch `product-experience-overhaul`. Do NOT run git commit, git checkout, or any',
    'git mutation; the orchestrator commits. Do NOT modify any file except the one design file below.',
    '',
    'Module: ' + m.module + ' (' + m.slug + ')',
    'Approved module spec (requirements are FROZEN — never delete, renumber, or weaken them): ' + spec,
    'Cross-module overview with the frozen registry between the superstorm-registry markers: ' + OVERVIEW,
    'Sibling specs live in ' + SPECS + '/2026-09-18-*-design.md — read the ones whose interfaces you consume or expose.',
    '',
    '## Method',
    '1. Read the module spec, the overview, and the sibling specs you interface with.',
    '2. READ THE ACTUAL CODE AND TEXT the spec cites (file:line references) in ' + REPO + ' before designing.',
    '   The spec line numbers were recorded on 2026-09-18 and may have drifted slightly; trust the file.',
    '   If a cited fact is wrong, say so in the design under "Spec corrections" and design against reality.',
    '3. Design units with clear boundaries: for each unit state what it does, its interface, its',
    '   dependencies, the exact files it touches. Apply YAGNI — no unrequested features.',
    '4. Cover: architecture, components, data flow, error handling, testing (exact test files, the helper',
    '   style to match, and the exact acceptance commands). Name every file that will be created or edited.',
    '5. APPEND a section `## Detailed design` to the END of the module spec file ' + spec + '.',
    '   Do not rewrite the existing sections. Include an "Assumptions" subsection for internal choices',
    '   and a "File touch list" subsection (path → create|edit → which requirement).',
    '',
    '## Repo facts you must respect',
    '- claude/meta-skill is canonical. codex/meta-skill/{scripts,tests} and pi/meta-skill/scripts are symlinks',
    '  into it, as are codex/meta-skill/knowledge/capabilities and 13 theory files. Hand-maintained twins',
    '  (codex/pi bootstrap adapters, orchestrator templates, codex cross-exam/product-review) belong to M5/M6.',
    '- No worktree isolation in this run: modules that touch the same file are serialized. Shared hot files:',
    '  scripts/orchestrator/validate_bootstrap.py, validate_meta_contracts.py, knowledge/bootstrap-planning.md,',
    '  tests/unit/test_validate_bootstrap.py, skills/bootstrap/SKILL.md. Keep each module\'s edits to those files',
    '  additive and localized (new function + one registration line) so serial edits do not conflict.',
    '- validate_meta_contracts.py pins exact literals in the bootstrap corpus (e.g. the implement-goal strings',
    '  around lines 179-195). Do not design edits that remove pinned literals.',
    '- The full meta-skill unit suite has 4 known pre-existing failures (test_decision_gate ... fresh_evidence',
    '  [claude|codex], test_evidence_freshness ... cannot_claim_completion [claude|codex]). Never touch them.',
    '- Never run `pytest pi/meta-skill` or `pytest codex/meta-skill` as directories (symlink collection clash);',
    '  name test files explicitly.',
    '',
    '## Decision boundary',
    '- A choice that would change module boundaries, public interfaces, or user-visible scope → return',
    '  status:"escalate" with options, recommendation, assumptions, risk, reversibility, affected artifacts.',
    '- A pure internal choice (naming, file org, private structures) → decide it, note it under Assumptions.',
    '- You MUST draw requirement IDs and interface names from the frozen registry only. Grammar <kind>:<name>.',
    '  If the module genuinely needs a registry entry that does not exist, return status:"escalate" with the',
    '  exact evidence-backed contract; do not invent names.',
    '',
    '## Output',
    'Return JSON {status, module, design_path, covers_req_ids, exposes, consumes, reason?, evidence?}.',
    '- module: "' + m.module + '"; design_path: the spec path above (repo-relative: docs/superpowers/specs/2026-09-18-' + m.slug + '-design.md).',
    '- covers_req_ids: every R-' + m.module + '-NN this design satisfies (it must be ALL of this module\'s IDs unless you escalate).',
    '- exposes / consumes: registry interface names exactly as written in the spec\'s "接口" section.',
  ].join('\n')
}

phase('Design')
const manifests = await parallel(MODULES.map(m => () =>
  agent(prompt(m), { label: 'design:' + m.module, phase: 'Design', schema: MANIFEST_SCHEMA })
    .then(r => r || { status: 'escalate', module: m.module, design_path: '', covers_req_ids: [], exposes: [], consumes: [], reason: 'agent returned null (infrastructure)' })
))
return { manifests }
