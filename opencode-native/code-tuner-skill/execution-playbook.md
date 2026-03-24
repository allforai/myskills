# Code Tuner Execution Playbook For OpenCode

This playbook turns the source `code-tuner` plugin into a OpenCode-friendly workflow
without changing the original plugin layout.

## When to use

Use this workflow when the user wants to:

- assess backend architecture quality
- check layering or DDD compliance
- find duplicated backend logic
- identify abstraction or refactor opportunities
- generate a technical-debt report for server code

Do not use it for:

- frontend-only repositories
- documentation-only repositories
- design-only repositories

## Workflow modes

| Requested mode | Run phases |
|---|---|
| `full` or unspecified | Phase 0 -> 1 -> 2 -> 3 -> 4 |
| `compliance` | Phase 0 -> 1 -> 4 |
| `duplication` | Phase 0 -> 2 -> 4 |
| `abstraction` | Phase 0 -> 3 -> 4 |
| `report` | Phase 4 from existing artifacts |

## Lifecycle modes

| Lifecycle | Meaning |
|---|---|
| `pre-launch` | Aggressive cleanup and restructuring is acceptable |
| `maintenance` | Recommendations should be conservative and lower-risk |

Default to `pre-launch` unless the user clearly indicates a live maintenance
system.

## Phase checklist

### Phase 0: Project profile

Objectives:

- confirm the target is a backend-capable repository
- detect tech stack
- infer architecture type
- infer logical layer mapping
- identify modules and data model surface

Outputs:

- `.allforai/code-tuner/tuner-profile.json`
- `.allforai/code-tuner/tuner-decisions.json` when explicit confirmations are
  needed

Sources:

- `../../code-tuner-skill/references/phase0-profile.md`
- `../../code-tuner-skill/references/layer-mapping.md`

### Phase 1: Compliance

Objectives:

- check layer responsibility and dependency direction
- check placement of validation logic
- flag architecture violations by rule ID

Output:

- `.allforai/code-tuner/phase1-compliance.json`

Source:

- `../../code-tuner-skill/references/phase1-compliance.md`

### Phase 2: Duplication

Objectives:

- detect repeated API patterns
- detect repeated service logic
- detect repeated repository/query patterns
- detect repeated utility logic

Output:

- `.allforai/code-tuner/phase2-duplicates.json`

Source:

- `../../code-tuner-skill/references/phase2-duplicates.md`

### Phase 3: Abstraction

Objectives:

- find vertical abstractions
- find horizontal abstractions
- find mergeable interfaces
- assess validation placement
- detect over-abstraction

Output:

- `.allforai/code-tuner/phase3-abstractions.json`

Source:

- `../../code-tuner-skill/references/phase3-abstractions.md`

### Phase 4: Report

Objectives:

- score the system
- aggregate findings
- produce an actionable task list

Outputs:

- `.allforai/code-tuner/tuner-report.md`
- `.allforai/code-tuner/tuner-tasks.json`

Source:

- `../../code-tuner-skill/references/phase4-report.md`

## OpenCode translation rules

- Treat slash-command examples from the source plugin as workflow labels.
- Replace `AskUserQuestion` with direct user questions only when the answer is
  required to avoid a bad assumption.
- Keep the workflow read-only unless the user explicitly asks for fixes.
- Preserve the original output contract under `.allforai/code-tuner/`.

## Final response contract

After analysis, OpenCode should provide:

- the selected mode and lifecycle
- a concise score summary
- the highest-severity findings
- the location of generated report artifacts

If no findings are discovered, state that explicitly and mention any residual
coverage gaps.

