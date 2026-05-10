# Enemy Behavior Spec Skill

> Internal sub-skill for game-combat pipelines. Status: bundled, inactive, not wired.

## Overview

Defines enemy behavior roles, states, transitions, telegraphs, attacks,
movement, detection, counterplay, and runtime AI requirements.

## Input Contract

Required: combat spec and enemy design list or content taxonomy.

Optional: level encounter placement, damage formulas, animation/VFX/audio
requirements, difficulty tiers, and platform constraints.

## Output Contract

Writes `.allforai/game-design/combat/enemy-behavior-spec.json` and a report.
Enemies include `enemy_id`, `role`, `state_machine`, `detection_rules`,
`attack_rules`, `movement_rules`, `telegraph_requirements`, `counterplay`,
`difficulty_scaling`, `asset_requirements`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_enemy_list`.

## Invocation Contract

```json
{"skill":"game-combat/enemy-behavior-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/combat"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every enemy has a role, readable state transitions, a counterplay window,
and encounter placement or explicit future-use status.

Repair routing: missing enemy purpose routes to enemy-design-list-generation;
placement gaps route to game-level; numeric gaps route to game-balance.

## Completion Conditions

Return `COMPLETED` when enemy behaviors are readable and placed. Return
`FAILED_VALIDATION` when enemies lack role, tell, or counterplay.
