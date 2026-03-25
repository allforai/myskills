# Codex Generic Fixtures Spec

Date: 2026-03-26

Purpose:
- Define generic, stack-agnostic validation fixtures for Codex plugins
- Replace reliance on domain-specific sample projects as the primary validation mechanism

## Fixture Design Rules

Each fixture should be:
- minimal
- schema-valid
- composable
- domain-neutral
- technology-neutral where possible

Each fixture should test one or two capabilities, not ten at once.

## Proposed Fixture Set

### F01. minimal-product-map

Purpose:
- Upstream input for `dev-forge`, `demo-forge`, and downstream design consumers

Contents:
- `.allforai/product-map/product-map.json`
- `.allforai/product-map/task-inventory.json`
- `.allforai/product-map/role-profiles.json`
- `.allforai/product-map/business-flows.json`

Checks enabled:
- prerequisite satisfaction
- upstream artifact loading
- phase routing

### F02. minimal-experience-chain

Purpose:
- Upstream input for `use-case`, `feature-gap`, `ui-design`, `interaction-gate`

Contents:
- `.allforai/experience-map/journey-emotion-map.json`
- `.allforai/experience-map/experience-map.json`
- `.allforai/experience-map/interaction-gate.json`

Checks enabled:
- downstream contract consumption
- resume logic
- UI-related closure

### F03. minimal-ui-baseline

Purpose:
- Upstream baseline for `ui-forge`

Contents:
- `.allforai/ui-design/ui-design-spec.json`
- `.allforai/ui-design/tokens.json`
- optional screenshots directory

Checks enabled:
- restore vs polish routing
- design baseline priority order
- token fidelity checks

### F04. minimal-project-forge

Purpose:
- Resume / downstream input for `code-tuner` and verification workflows

Contents:
- `.allforai/project-forge/forge-decisions.json`
- `.allforai/project-forge/project-manifest.json`
- `.allforai/project-forge/build-log.json`

Checks enabled:
- resume markers
- downstream profile consumption
- task execution completion semantics

### F05. minimal-runtime-config

Purpose:
- Runtime-dependent workflows without binding to a real app

Contents:
- app URL
- optional credentials block
- phase-specific runtime metadata

Checks enabled:
- default assumption handling
- blocking-question behavior
- runtime-required phase detection

### F06. minimal-replicate-source

Purpose:
- Input fixture for `code-replicate`

Contents:
- a tiny synthetic source tree
- a tiny summary/index fixture

Checks enabled:
- discovery output shape
- artifact generation lower bounds
- handoff compatibility

## Assertion Strategy

Fixtures should be validated with:

1. file existence checks
2. JSON parse checks
3. required-key checks
4. cross-reference checks
5. lower-bound checks

Do not require:
- exact generated counts
- one exact wording
- one exact score

## Relationship to Existing Test Prompts

Existing prompts remain useful as scenario-level smoke tests:
- they exercise richer human workflows
- they expose prompt drift

Generic fixtures should become the lower-level regression base:
- faster
- more stable
- less domain-sensitive

## Recommended Repository Layout

Suggested future layout:

```text
docs/validation/
  codex-capability-matrix.md
  codex-generic-fixtures.md
fixtures/
  codex/
    minimal-product-map/
    minimal-experience-chain/
    minimal-ui-baseline/
    minimal-project-forge/
    minimal-runtime-config/
    minimal-replicate-source/
```
