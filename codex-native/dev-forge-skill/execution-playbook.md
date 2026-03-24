# Dev Forge Execution Playbook For Codex Native

This playbook adapts the source `dev-forge` plugin into a Codex-native
workflow while preserving the original `.allforai/` artifact contract.

## When to use

Use this workflow when the user wants to:

- turn product-design outputs into implementation specs
- scaffold or extend a real project from `.allforai/` artifacts
- execute development tasks in rounds with progress tracking
- run acceptance, dead-link, field-consistency, or test-forge validation loops
- resume a previously interrupted forge run

Do not use it when:

- `.allforai/product-map/product-map.json` is missing
- the repository is only design documentation with no implementation target
- the user only wants architecture analysis rather than delivery

## Workflow modes

| Requested mode | Meaning |
|---|---|
| `full` or unspecified | Fresh run across all forge phases |
| `existing` or `full existing` | Gap-fill an existing codebase rather than starting from blank scaffolding |
| `resume` | Detect existing forge artifacts and continue from the first incomplete phase |

Treat source slash commands such as `/project-forge full` as workflow labels,
not literal commands.

## High-level phases

| Phase | Goal | Primary outputs |
|---|---|---|
| 0 | detect prerequisites, mode, and tool readiness | `.allforai/project-forge/forge-decisions.json` |
| 1 | technical spike and risk decisions | `forge-decisions.json` technical spikes |
| 2 | project setup and sub-project routing | `.allforai/project-forge/project-manifest.json` |
| 3 | design to spec translation | `requirements.md`, `design.md`, `tasks.md`, `shared-utilities-plan.json` |
| 4 | task execution and build progress | `.allforai/project-forge/build-log.json` |
| 5 | verification loop | `.allforai/product-verify/`, `.allforai/deadhunt/`, `.allforai/testforge/` |
| 6 | demo-forge handoff | `.allforai/demo-forge/demo-plan.json` or explicit skip |
| 7 | conditional cross-end verification | refreshed testforge outputs when needed |
| 8 | final forge report | `.allforai/project-forge/forge-report.md` |

## Codex orchestration rules

- Do not ask for confirmation between every phase.
- Ask the user only when a missing technical decision would corrupt the next
  phase or when required credentials or tooling are unavailable.
- Keep the original artifact locations and naming under `.allforai/`.
- Translate host-specific orchestration syntax into normal Codex execution.
- Treat demo-forge as an external downstream workflow that may be prepared but
  not always executed in the same run.

## Phase 0: Detect state and prerequisites

Objectives:

- confirm `product-design` outputs exist
- detect whether the run is fresh, existing, or resume
- detect existing forge artifacts
- detect tool readiness for Playwright, Maestro, and optional external services
- infer whether the project has consumer-facing apps that require stricter UX
  completion standards

Critical prerequisite:

- `.allforai/product-map/product-map.json` must exist before forge work begins

Resume rule:

- for `resume`, continue from the first incomplete phase rather than restarting
  completed ones

Outputs:

- `.allforai/project-forge/forge-decisions.json`

## Phase 1: Technical spike

Primary source:

- `../../dev-forge-skill/commands/project-forge.md`

Objectives:

- identify non-trivial technical risks before implementation
- record major vendor, architecture, integration, cost, or compliance decisions
- mark each spike as confirmed or explicitly TBD

Codex rule:

- source materials may describe interactive spike selection, but Codex should
  collapse that into only the minimum blocking questions needed for safe
  implementation planning

Output:

- `technical_spikes` inside `.allforai/project-forge/forge-decisions.json`

## Phase 2: Project setup

Primary source:

- `../../dev-forge-skill/skills/project-setup.md`

Objectives:

- split the system into sub-projects
- assign a tech stack to each sub-project
- define monorepo or multi-repo structure
- capture endpoint and role coverage

Output:

- `.allforai/project-forge/project-manifest.json`

Quality check:

- at least one sub-project exists
- each sub-project has a declared type and stack

## Phase 3: Design to spec

Primary source:

- `../../dev-forge-skill/skills/design-to-spec.md`

Objectives:

- convert product-design artifacts into implementation specs
- produce per-sub-project requirements, design, and tasks
- identify shared utilities and shared abstractions early

Outputs per sub-project:

- `requirements.md`
- `design.md`
- `tasks.md`

Shared output:

- `.allforai/project-forge/shared-utilities-plan.json`

Consumer-experience rule:

- if upstream `experience_priority.mode` is `consumer` or `mixed`, do not
  reduce frontend work to page shells and API hookups; tasks must include
  state handling, feedback loops, continuity, and recovery behavior

## Phase 4: Task execute

Primary source:

- `../../dev-forge-skill/skills/task-execute.md`

Objectives:

- initialize the project when needed
- execute tasks in rounds
- track progress in build logs
- verify incrementally rather than waiting until the end

Output:

- `.allforai/project-forge/build-log.json`

Completion standard:

- core tasks are marked completed
- obvious build or lint breakages are not left unresolved without explicit
  reporting

## Phase 5: Verification loop

Primary sources:

- `../../dev-forge-skill/skills/product-verify.md`
- `../../dev-forge-skill/commands/testforge.md`
- `../../dev-forge-skill/commands/deadhunt.md`
- `../../dev-forge-skill/commands/fieldcheck.md`

Objectives:

- validate implementation against product intent
- detect dead links, ghost features, and CRUD gaps
- detect field mismatches across UI, API, entity, and database layers
- generate or run tests needed to converge on acceptable quality

Outputs:

- `.allforai/product-verify/verify-report.md`
- `.allforai/deadhunt/output/validation-report-summary.md`
- `.allforai/deadhunt/output/field-analysis/field-report.md`
- `.allforai/testforge/testforge-report.md`

Codex rule:

- when a validation tool is unavailable, report the downgrade explicitly and
  continue only with the checks that remain valid

## Phase 6: Demo-forge handoff

Objectives:

- prepare the project for the downstream `demo-forge` workflow once core code
  is stable
- either produce a demo plan or explicitly record that demo-forge was skipped

Source:

- `../../demo-forge-skill/commands/demo-forge.md`

## Phase 7: Conditional cross-end verification

Objective:

- run additional cross-end verification when the main Phase 5 loop was skipped
  or only partially completed

Primary output:

- refreshed `.allforai/testforge/` artifacts

## Phase 8: Final report

Objectives:

- summarize what phases ran
- record what was skipped or resumed
- identify unresolved blockers or accepted risks
- point to the final artifact locations

Primary output:

- `.allforai/project-forge/forge-report.md`

## Final response contract

At the end of a forge run, Codex should summarize:

- selected mode
- completed, resumed, and skipped phases
- the most important generated artifacts
- unresolved blockers or tool gaps
- where the final forge report lives

## Safety rules

- Do not silently bypass the missing `product-design` prerequisite.
- Do not claim code execution or verification happened if the repository was
  only analyzed.
- Preserve existing user changes and project structure unless the task clearly
  asks for invasive scaffolding or refactoring.
