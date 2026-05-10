# Status Effect Spec Skill

> Internal sub-skill for game-combat pipelines. Status: bundled, inactive, not wired.

## Overview

Defines buffs, debuffs, DOT/HOT, crowd control, shields, immunities, stacking,
duration, cleanse rules, UI icons, VFX, and balance constraints.

## Input Contract

Required: combat spec or skill design spec.

Optional: damage formula spec, item/skill list, enemy behavior spec, UI/icon
requirements, and accessibility constraints.

## Output Contract

Writes `.allforai/game-design/combat/status-effect-spec.json` and a report.
Effects include `status_id`, `kind`, `source_refs`, `duration`, `stack_rule`,
`tick_rule`, `cleanse_rule`, `immunity_rule`, `ui_requirements`,
`vfx_requirements`, `balance_refs`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_combat`.

## Invocation Contract

```json
{"skill":"game-combat/status-effect-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/combat"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check stacking, duration, cleanse, immunity, UI readability, and whether each
effect has source and counterplay.

Repair routing: source gaps route to skill/enemy specs; numeric gaps route to
damage-formula-spec; UI/icon gaps route to game-ui and game-art.

## Completion Conditions

Return `COMPLETED` when statuses are bounded and readable. Return
`FAILED_VALIDATION` when effects can stack infinitely or lack counterplay.
