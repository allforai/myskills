# UI Forge — OpenCode Execution Playbook

This document defines how the UI Forge skill orchestrates in OpenCode.

## Trigger

The user asks to polish, refine, or restore a frontend UI that is already implemented.
Typical phrases: "polish this UI", "make it match the design", "the page works but looks rough".

## Orchestration Flow

```
Step 1  Establish Boundary
        Read: target screen files, .allforai/ui-design/ artifacts (if present)
        Output: triage block (baseline / completeness / drift / mode)
        Gate: if functionally incomplete → stop and explain

Step 2  Measure Drift
        Compare implementation against baseline at 4 levels:
          layout hierarchy, component language, token usage, state presentation
        Severity: low | medium | high
        If no baseline exists → skip, bias toward polish

Step 3  Read Constraints
        Extract only constraints relevant to the target:
          layout pattern, component structure, token usage,
          visual hierarchy, state behavior, responsive expectations
        Reference: docs/fidelity-checklist.md

Step 4  Refine In Place
        Mode restore: fix fidelity gaps first
        Mode polish: strengthen finish quality
        Mixed: Phase A restore → Phase B polish (no new drift)
        Priority: hierarchy → spacing → tokens → affordance → polish

Step 5  Preserve Product Intent
        Do not change: task flow, field meaning, API behavior,
        routing semantics, permissions logic

Step 6  Verify
        Check against chosen mode criteria
        Verify: responsive, states, token drift, duplication, accessibility
```

## Decision Gate

Ask the user only when:

- The target screen or component is ambiguous and cannot be inferred
- Functional completeness is borderline (unclear whether to stop or proceed)
- Drift is mixed and the user should confirm restore-then-polish vs polish-only

Do not ask for confirmation on routine mode selection or file choices.

## Input Priority

1. Current implementation files for the target screen/component
2. `.allforai/ui-design/ui-design-spec.json`
3. `.allforai/ui-design/tokens.json`
4. `.allforai/ui-design/component-spec.json`
5. `.allforai/ui-design/screenshots/`
6. `.allforai/experience-map/experience-map.json`

If no `.allforai` UI artifacts exist, work from code context and user intent only.

## Output Shape

```
1. Triage block
2. Chosen mode and rationale
3. Files changed
4. Restore work completed (if any)
5. Polish work completed (if any)
6. Constraints respected
7. Remaining gaps or tradeoffs
```
