---
name: ui-forge
description: >
  Use when a frontend screen is already implemented and needs UI refinement.
  This skill is for polishing visual quality or restoring design fidelity in a
  real codebase without taking over feature implementation. Best for engineers
  working after functionality is complete, especially when specs, tokens, or
  screenshots already exist.
---

# UI Forge Skill

`ui-forge` is a post-implementation UI refinement skill forked from the ideas of
`frontend-design`, but constrained for production codebases and technical teams.

It keeps the original bias toward intentional, high-quality frontend aesthetics,
but applies that taste under product and code constraints rather than in a blank
canvas setting.

Its core rule is simple: restore fidelity first, then polish.

## Hard Boundary

Do not treat this as a greenfield UI generation skill.

- Do not redesign product flows unless the current implementation is impossible to refine safely.
- Do not rewrite unrelated business logic.
- Do not invent new product requirements to justify visual changes.
- Do not replace `dev-forge` responsibilities.

If the page is not functionally complete, stop and tell the user the work should
return to implementation flow first.

## Refinement Mindset

Before changing code, form a fast opinion on all four layers:

- **product layer** - what user goal this screen serves right now
- **structure layer** - what layout and component hierarchy already exists
- **system layer** - what tokens, components, and states should be reused
- **finish layer** - what visual or interaction details are currently under-designed

Refine from the top down. Do not start by randomly changing colors or spacing.

## Operating Modes

Internally begin with a fidelity check, then choose exactly one execution mode.

### Stage: fidelity-check

Before editing, determine whether a trustworthy design baseline exists and how
far the implementation has drifted from it.

Check for:

- `ui-design-spec.json`
- `tokens.json`
- `component-spec.json`
- `screenshots/`
- code-level evidence of token drift or component drift

Read `${CLAUDE_PLUGIN_ROOT}/docs/fidelity-checklist.md` when a design baseline exists
or when the correct mode is not immediately obvious.

Questions to answer:

- Is the current screen structurally aligned with the intended design?
- Are tokens and component rules being followed?
- Are the visible states consistent with the expected system?
- Is the gap mostly fidelity drift, or mostly finish quality?

If drift is material, choose `restore`.
If alignment is already good enough, choose `polish`.

### Mode: polish

Use only when the target screen already works, is broadly aligned with the
intended design, and still feels rough.

Typical signals:

- layout hierarchy is flat or noisy
- spacing, typography, or color semantics are inconsistent
- loading, empty, error, disabled, and success states feel incomplete
- responsive behavior exists but looks unfinished
- interactions work but lack feedback, motion, or affordance

Goal:

- increase perceived quality without changing product semantics or lowering fidelity

### Mode: restore

Use when the target screen exists but has drifted away from the expected design baseline.

Typical signals:

- does not match `ui-design-spec.json`
- ignores `tokens.json` or `component-spec.json`
- differs materially from reference screenshots
- component shapes, density, hierarchy, or states violate the design system

Goal:

- recover fidelity to the existing design contract before adding flourish

## Inputs to Read

Read only what helps the current refinement task. Prefer this priority order:

1. current implementation files for the target screen/component
2. `.allforai/ui-design/ui-design-spec.json` if present
3. `.allforai/ui-design/tokens.json` if present
4. `.allforai/ui-design/component-spec.json` if present
5. `.allforai/ui-design/screenshots/` if present
6. `.allforai/experience-map/experience-map.json` if needed for state or interaction intent

If none of the `.allforai` UI artifacts exist, continue using only code context and user intent.
In that case, skip fidelity restoration and bias toward `polish`.

## Workflow

### Step 1: Establish boundary

Quickly determine:

- which screen or component is in scope
- whether the page is functionally complete
- whether a trusted design baseline exists
- which files are the real implementation surface

State the chosen mode briefly before editing.

Also state the guardrail in one line:

- what you will improve
- what you will not change

### Step 2: Measure drift against the baseline

If a baseline exists, compare the implementation against it at four levels:

- layout and information hierarchy
- component language and density
- token usage and styling rules
- state presentation and interaction cues

Do not jump straight into beautification when the implementation is still off-baseline.

### Step 3: Read constraints

Extract only the constraints that matter to the target:

- layout pattern
- component structure
- token usage
- visual hierarchy
- state behavior
- responsive expectations

When screenshots exist, treat them as fidelity references, not pixel-perfect prison.
Match the intended hierarchy, density, tone, and component language first.

### Step 4: Refine in place

Prefer local, layered improvements:

- strengthen typography hierarchy
- improve spacing rhythm and grouping
- enforce token usage
- improve component affordance and state clarity
- add restrained motion where it supports comprehension
- improve mobile and desktop balance

For visual decisions, prefer this order:

1. fix hierarchy
2. fix spacing rhythm
3. fix token usage
4. fix component affordance
5. add selective polish

Avoid large rewrites unless the current code shape makes safe refinement impossible.

Keep the code production-oriented:

- respect the existing framework and project conventions
- reuse component boundaries where possible
- avoid decorative complexity that is hard to maintain
- avoid adding dependencies only for cosmetic gain unless clearly justified

Execution priority:

1. restore fidelity gaps
2. normalize tokens and component rules
3. improve state clarity
4. polish finish and motion

### Step 5: Preserve product intent

Do not change:

- task flow
- field meaning
- API behavior
- routing semantics
- permissions logic

If a requested UI improvement requires one of these changes, call it out explicitly.

### Step 6: Verify

Check the result against the chosen mode:

- `restore` -> closer to spec/tokens/screenshots, less drift, same product behavior
- `polish` -> better visual quality, better interaction clarity, same product behavior, no new drift

Also verify practical engineering quality:

- no broken responsive layout
- no missing visible states
- no token drift introduced by hardcoded values unless justified
- no unnecessary component duplication
- no accessibility regression in focus, contrast, labels, or feedback

## What Good Looks Like

Use concrete heuristics when deciding whether the work is done.

- primary action is obvious within 2 seconds
- information groups can be scanned without reading every line
- empty/loading/error/success states feel part of the same system
- repeated UI uses repeated rules
- the screen feels intentionally designed rather than merely styled
- the implementation is visibly closer to the intended design system than before

## Default Output Pattern

When completing a refinement task, report in this shape:

1. chosen mode and why
2. fidelity check result
3. files changed
4. main UI improvements
5. constraints respected
6. any remaining gap or tradeoff

## Quality Standard

Aim for interfaces that feel intentionally designed, not merely cleaned up.

- strong hierarchy
- disciplined spacing
- clear state transitions
- non-generic styling
- responsive stability
- accessibility-aware interaction cues

## Response Style

Communicate like a senior frontend engineer speaking to another engineer.

- be concrete
- name the tradeoff
- explain what changed and why
- avoid vague design language with no implementation consequence

## Typical Triggers

This skill is especially appropriate when the user says things like:

- "the page works but looks rough"
- "polish this UI"
- "make this screen feel production ready"
- "restore this page to match the design"
- "the implementation drifted from tokens or screenshots"
- "improve the frontend without changing the business logic"
- "make the implementation closer to the design"
- "check whether this page drifted from our UI spec"
