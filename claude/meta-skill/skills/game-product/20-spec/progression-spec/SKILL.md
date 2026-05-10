# Progression Spec Skill

> Internal sub-skill for game-product pipelines. Status: bundled, inactive, not wired.

## Overview

Defines player growth, unlocks, difficulty ramp, chapters, mastery, rewards,
and meta progression.

## Input Contract

Required: core game loop spec, player experience contract, and registry.

Optional: mechanics spec, economy spec, level design spec, item/skill list,
content taxonomy, and target session count.

## Output Contract

Writes:

- `.allforai/game-design/systems/progression-spec.json`
- `.allforai/game-design/systems/progression-report.json`

Progression entries must include `progression_id`, `progression_axis`,
`unlock_condition`, `reward`, `player_value`, `difficulty_effect`,
`content_gate_refs`, `economy_refs`, `level_refs`, `ui_requirements`,
`data_table_refs`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_loop`, `blocked_by_missing_content`.

## Invocation Contract

```json
{
  "skill": "game-product/progression-spec",
  "mode": "spec_validate",
  "input_paths": {
    "core_loop": ".allforai/game-design/product/core-game-loop-spec.json",
    "player_experience": ".allforai/game-design/product/player-experience-contract.json",
    "registry": ".allforai/game-design/product/game-design-registry.json"
  },
  "output_root": ".allforai/game-design/systems"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that progression rewards create useful new options, unlocks are reachable,
difficulty does not spike without counterplay, and no content gate references a
missing content entry.

Repair routing: missing content routes to `content-taxonomy-spec`; economy
costs route to `economy-spec`; level pacing route to `level-design-spec`.

## Completion Conditions

Return `COMPLETED` when progression is reachable and motivates repeated play.
Return `FAILED_VALIDATION` for dead-end unlocks, unreachable rewards, or missing
gates.
