# Mechanics Spec Skill

> Internal sub-skill for game-product pipelines. Status: bundled, inactive, not wired.

## Overview

Defines core interaction mechanics as executable product rules: inputs,
constraints, risks, rewards, feedback, runtime refs, and content dependencies.

## Input Contract

Required: core game loop spec and game-design registry.

Optional: player experience contract, pillars, combat spec, level design spec,
UI constraints, platform input model, and runtime engine constraints.

## Output Contract

Writes:

- `.allforai/game-design/systems/mechanics-spec.json`
- `.allforai/game-design/systems/mechanics-report.json`

Mechanics must include `mechanic_id`, `loop_refs`, `input_model`,
`activation_rule`, `success_rule`, `failure_rule`, `risk`, `reward`,
`feedback_requirements`, `ui_requirements`, `art_requirements`,
`audio_requirements`, `runtime_system_refs`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_loop`, `blocked_by_input_model`.

## Invocation Contract

```json
{
  "skill": "game-product/mechanics-spec",
  "mode": "spec_validate",
  "input_paths": {
    "core_loop": ".allforai/game-design/product/core-game-loop-spec.json",
    "registry": ".allforai/game-design/product/game-design-registry.json"
  },
  "output_root": ".allforai/game-design/systems"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every core loop action has a mechanic, every mechanic has input,
success/failure rule, feedback, and runtime owner, and no mechanic contradicts
the platform or complexity budget.

Repair routing: missing goals route to `core-game-loop-spec`; impossible input
routes to `player-experience-contract`; combat-specific issues route to
`combat-spec`.

## Completion Conditions

Return `COMPLETED` when core mechanics are rule-complete and mapped to runtime
systems. Return `FAILED_VALIDATION` when a required action has no executable
rule.
