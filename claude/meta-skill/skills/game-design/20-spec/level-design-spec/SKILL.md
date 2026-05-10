# Level Design Spec Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Defines game design-level level requirements: view mode, level grammar, objectives,
pacing beats, encounters, rewards, teaching points, and downstream art/runtime
needs.

## Input Contract

Required: core game loop spec, mechanics spec, and registry.

Optional: progression spec, combat spec, economy spec, content taxonomy,
view-mode/art constraints, target engine, and platform controls.

## Output Contract

Writes:

- `.allforai/game-design/design/level-design-spec.json`
- `.allforai/game-design/design/level-design-report.json`

Level entries must include `level_id`, `level_role`, `view_mode`,
`objective`, `layout_grammar`, `pacing_beats`, `teaching_points`,
`encounter_refs`, `reward_refs`, `failure_recovery`, `asset_requirements`,
`runtime_requirements`, `blockout_requirements`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_mechanics`, `blocked_by_progression`.

## Invocation Contract

```json
{
  "skill": "game-design/level-design-spec",
  "mode": "spec_validate",
  "input_paths": {
    "core_loop": ".allforai/game-design/design/core-game-loop-spec.json",
    "mechanics": ".allforai/game-design/systems/mechanics-spec.json",
    "registry": ".allforai/game-design/design/game-design-registry.json"
  },
  "output_root": ".allforai/game-design/product"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that each level has an objective, playable action space, reward, failure
recovery, and route to blockout generation. Required art and runtime needs must
be explicit.

Repair routing: missing action space routes to `mechanics-spec`; missing reward
routes to `economy-spec` or `progression-spec`; map/blockout details route to
`game-level/level-layout-spec`.

## Completion Conditions

Return `COMPLETED` when every required level has playable intent and downstream
requirements. Return `FAILED_VALIDATION` when a level cannot be played or
verified.
