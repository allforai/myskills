---
name: app-design-20-spec-interaction-pattern-spec
description: Define interactive component behavior, state transitions, gesture model, and loading strategy; writes spec/interaction-pattern-spec.json. Sole author of component states for non-game projects; game projects use game-ui component-state-spec.
---

# Interaction Pattern Spec Skill

> Internal sub-skill for app-design pipelines. Status: bundled, bootstrap-wired, invoked by app-design node-specs.

## Overview

**Owns component states for the whole pipeline.** `interaction-design.json`
produced here is the single definition of `components[].states[]`,
`gesture_model`, and `loading_strategy`. The `ui-design` capability references
these by `component_id` and adds only visual/motion realization; it must not
restate or extend the state lists. On game projects this skill does not run and
`game-ui/20-spec/component-state-spec` owns the same ground instead.

Defines interactive component behavior, state transitions, feedback, gestures,
loading, accessibility, and error recovery patterns.

## Input Contract

Required: screen requirements spec and user flow spec.

Optional: platform guidelines, design system, accessibility policy, brand
motion preferences, performance constraints, and existing component library.

## Output Contract

Writes `.allforai/app-design/spec/interaction-pattern-spec.json`.

Patterns must include `pattern_id`, `screen_refs`, `component_role`,
`states`, `transitions`, `feedback`, `gesture_or_input_model`,
`loading_strategy`, `error_recovery`, `accessibility_behavior`,
`motion_level`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_screens`.

## Invocation Contract

```json
{"skill":"app-design/interaction-pattern-spec","mode":"spec_validate","input_paths":{"screens":".allforai/app-design/spec/screen-requirements-spec.json","flows":".allforai/app-design/spec/user-flow-spec.json"},"output_root":".allforai/app-design/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every primary action has visible feedback, disabled/loading/error states,
and accessible keyboard/screen-reader behavior when applicable. Reject gestures
without fallback actions.

Repair routing: missing action semantics route to screen-requirements-spec;
missing flow recovery routes to user-flow-spec; component library conflicts
route to UI design.

## Completion Conditions

Return `COMPLETED` when interaction behavior is implementable and testable.
Return `FAILED_VALIDATION` when key actions lack feedback or recovery states.
