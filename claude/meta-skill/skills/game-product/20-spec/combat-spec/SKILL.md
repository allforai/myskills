# Combat Spec Skill

> Internal sub-skill for game-product pipelines. Status: bundled, inactive, not wired.

## Overview

Defines combat rules when the game includes conflict, hazards, damage, enemies,
skills, statuses, or boss encounters.

## Input Contract

Required: core game loop spec and mechanics spec.

Optional: player experience contract, progression spec, economy spec, level
design spec, enemy roster, item/skill generation, animation/VFX requirements,
and runtime engine constraints.

## Output Contract

Writes:

- `.allforai/game-design/systems/combat-spec.json`
- `.allforai/game-design/systems/combat-report.json`

Combat entries must include `combat_id`, `damage_model`, `hit_rule`,
`defense_rule`, `enemy_role_refs`, `skill_refs`, `status_effects`,
`encounter_rhythm`, `readability_requirements`, `failure_recovery`,
`animation_requirements`, `vfx_requirements`, `audio_requirements`,
`runtime_system_refs`, `state`, and `consumer_refs`.

Allowed states: `not_applicable`, `draft`, `validated`, `needs_revision`,
`blocked_by_mechanics`, `blocked_by_readability`.

## Invocation Contract

```json
{
  "skill": "game-product/combat-spec",
  "mode": "spec_validate",
  "input_paths": {
    "core_loop": ".allforai/game-design/product/core-game-loop-spec.json",
    "mechanics": ".allforai/game-design/systems/mechanics-spec.json"
  },
  "output_root": ".allforai/game-design/systems"
}
```

Supported modes: `spec_validate`, `not_applicable`, `validate_existing`,
`repair_existing`.

## Automatic Validation

If combat is applicable, check that damage, hit, defense, enemy roles,
readability, feedback, fail states, and recovery are defined. If combat is not
part of the game, return `not_applicable` with rationale.

Repair routing: missing actions route to `mechanics-spec`; missing enemies
route to `enemy-roster-generation`; animation/VFX gaps route to game-art motion
and VFX skills.

## Completion Conditions

Return `COMPLETED` when combat rules are executable or explicitly not
applicable. Return `FAILED_VALIDATION` when combat exists but cannot be read,
resolved, or recovered from.
