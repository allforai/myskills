# Codex Test — Project 4: PulseCRM UI Restore

## Context

You are testing the myskills plugin suite on the Codex platform. Plugins at `/path/to/myskills/codex/`.

Test project directory: `test-pulsecrm-ui/`

## Goal

Validate the `ui-forge` plugin as a post-implementation UI refinement workflow.

This is not a feature-build task. The target page is already functionally complete.

## Project Description

PulseCRM is a B2B CRM admin product.

Target screen:
- `CustomerDetailPage`

Current state:
- Data loads correctly
- Edit, archive, assign-owner, and add-note actions all work
- Desktop and tablet breakpoints render without runtime errors
- But the page has obvious design drift:
  - spacing is inconsistent
  - typography hierarchy is weak
  - token usage is mixed with hardcoded values
  - status badges do not match design language
  - side panel and main content feel visually disconnected

Available baseline artifacts:
- `.allforai/ui-design/ui-design-spec.json`
- `.allforai/ui-design/tokens.json`
- optional screenshots in `.allforai/ui-design/screenshots/`

## Task

Read these files first:

- `codex/ui-forge-skill/AGENTS.md`
- `codex/ui-forge-skill/execution-playbook.md`
- `codex/ui-forge-skill/SKILL.md`

Then execute a thought-experiment run of `ui-forge` on `CustomerDetailPage`.

## Expected Triage

Before editing, produce the triage block defined by the playbook:

```text
Baseline: present
Functional Completeness: complete
Drift Assessment: medium or high
Chosen Mode: restore
```

## Expected Actions

1. Confirm the page is functionally complete and should not be routed back to `dev-forge`
2. Use the design baseline to identify restore work
3. Prioritize:
   - layout and hierarchy drift
   - token normalization
   - component language drift
   - state presentation drift
4. Only after restore is complete, optionally apply limited polish
5. Respect all guardrails:
   - no API changes
   - no routing changes
   - no permissions changes
   - no business logic changes

## Expected Output Shape

The final report should contain:

1. Triage block
2. Chosen mode and rationale
3. Files changed
4. Restore work completed
5. Polish work completed, if any
6. Constraints respected
7. Remaining gaps or tradeoffs

## Quality Criteria

- The workflow chooses `restore` before `polish`
- It explicitly refuses to use UI refinement to hide unfinished implementation
- It references the available baseline artifacts in priority order
- It preserves product behavior and business semantics
- It checks responsive layout, visible states, token consistency, and accessibility risk
