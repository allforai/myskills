# Product Design Execution Playbook For Codex Native

This playbook adapts the `product-design` pipeline into a Codex-native workflow
while preserving the original `.allforai/` artifact contract.

## Purpose

Use this workflow to drive product-design artifacts from concept discovery
through structural mapping, journey analysis, experience design, gap analysis,
and final audit.

## Workflow modes

| Requested mode | Meaning |
|---|---|
| `full` or unspecified | Run the entire pipeline from the start |
| `full skip: concept` | Start from product-map and skip concept discovery |
| `resume` | Detect existing artifacts and continue from the first incomplete phase |

Treat source slash commands such as `/product-design full` as workflow labels,
not literal commands.

## High-level phases

| Phase | Goal | Primary outputs |
|---|---|---|
| 0 | Artifact detection and routing | phase selection only |
| 1 | product concept | `.allforai/product-concept/` |
| 2 | product map | `.allforai/product-map/` |
| 3 | journey emotion | `.allforai/journey-emotion/` or equivalent journey outputs |
| 4 | experience map + interaction gate | `.allforai/experience-map/` |
| 5 | feature gap | `.allforai/feature-gap/` |
| 6 | design audit | `.allforai/design-audit/` |

## Codex orchestration rules

- Move phase-to-phase without asking for confirmation after every stage.
- Ask the user only when a missing decision would materially corrupt the next
  phase.
- Preserve the original rule that user review is optional and may be launched
  on demand rather than forced as a blocking gate.
- Keep outputs in the original `.allforai/` locations.

## Phase 0: Detect state

Inspect the expected artifact locations and determine whether the run is:

- a fresh full run
- a full run skipping concept
- a resume run

Use the same completion concepts as the source command:

- concept artifacts present
- product-map task inventory present and non-empty
- journey outputs present
- experience map present
- feature-gap outputs present
- audit report present

For `resume`, continue from the first incomplete phase.

## Phase 1: Product concept

Primary sources:

- `../../product-design-skill/skills/product-concept.md`

Objectives:

- define the core problem space
- identify product direction
- generate concept artifacts

Codex rule:

- source files may describe many `AskUserQuestion` checkpoints, but Codex
  should collapse them into only the minimum blocking set of questions
  necessary to produce a sound concept.

## Phase 2: Product map

Primary sources:

- `../../product-design-skill/skills/product-map.md`

Objectives:

- identify roles, tasks, constraints, and flows
- produce the structured map that downstream phases consume

Critical check:

- `task-inventory.json` must exist and contain tasks

If the source product clearly includes consumer or mixed end-user surfaces,
carry forward `experience_priority` because downstream standards depend on it.

## Phase 3: Journey emotion

Primary sources:

- `../../product-design-skill/skills/journey-emotion.md`

Objectives:

- map emotional highs and lows across real user journeys
- identify recovery points and high-risk moments

Codex rule:

- interrupt the user only for severe unresolved ambiguity, not for routine
  confirmations.

## Phase 4: Experience map and interaction gate

Primary sources:

- `../../product-design-skill/skills/experience-map.md`
- `../../product-design-skill/skills/interaction-gate.md`

Objectives:

- translate tasks and journeys into screens, navigation, states, and failures
- verify interaction quality and risk points

Checks:

- screen coverage exists for core tasks
- navigation is not dead-ended
- failure states have recovery paths

## Phase 5: Feature gap

Primary source:

- `../../product-design-skill/skills/feature-gap.md`

Objectives:

- identify missing task coverage
- identify missing screens or interactions
- identify journey and recovery gaps

Output:

- `.allforai/feature-gap/gap-tasks.json`

## Phase 6: Design audit

Primary source:

- `../../product-design-skill/skills/design-audit.md`

Objectives:

- perform reverse traceability checks
- perform coverage checks
- perform cross-layer consistency checks

Outputs:

- `.allforai/design-audit/audit-report.json`
- `.allforai/design-audit/audit-report.md`

## Review hub behavior in Codex

The source plugin includes `/review` as a unified review hub.

In Codex:

- treat it as an optional review workflow, not a mandatory blocking step
- if the user asks for review processing, use the source review command and
  review artifacts as the authority
- do not pause the main product-design pipeline only to ask whether the user
  wants to review

## Verification standard

At the end of the pipeline, Codex should summarize:

- which phases ran
- which phases were resumed or skipped
- the most important outputs generated
- any blocking unresolved issue
- where the final audit artifacts live

## Safety rules

- Keep product-design stages read/write only within their defined artifact
  outputs.
- Do not silently rewrite upstream phases from downstream findings unless the
  source workflow explicitly requires regeneration and the user intent supports
  it.
- Prefer explicit reporting of unresolved issues over hidden assumptions.
