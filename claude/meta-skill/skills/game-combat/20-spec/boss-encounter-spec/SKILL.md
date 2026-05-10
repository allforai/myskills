# Boss Encounter Spec Skill

> Internal sub-skill for game-combat pipelines. Status: bundled, inactive, not wired.

## Overview

Defines boss encounters: phases, mechanics, arena constraints, adds, tells,
failure recovery, rewards, narrative hooks, and asset requirements.

## Input Contract

Required: combat spec, level design or encounter placement, and progression context.

Optional: enemy behavior spec, status effects, damage formulas, narrative beats,
reward pricing, and art/VFX/audio requirements.

## Output Contract

Writes `.allforai/game-design/combat/boss-encounter-spec.json` and a report.
Boss entries include `boss_id`, `phase_rules`, `arena_requirements`,
`mechanic_refs`, `telegraph_requirements`, `counterplay`, `failure_recovery`,
`reward_refs`, `narrative_refs`, `asset_requirements`, `state`, and `consumer_refs`.

Allowed states: `not_applicable`, `draft`, `validated`, `needs_revision`,
`blocked_by_level`, `blocked_by_combat`.

## Invocation Contract

```json
{"skill":"game-combat/boss-encounter-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/combat"}
```

Supported modes: `spec_validate`, `not_applicable`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check phase readability, arena support, counterplay, recovery, rewards, and no
unannounced instant-fail mechanics unless explicitly accepted by design pillars.

Repair routing: arena gaps route to game-level; numeric gaps route to
game-balance; asset gaps route to game-art and game-audio.

## Completion Conditions

Return `COMPLETED` when boss encounters are readable or not applicable. Return
`FAILED_VALIDATION` when required boss mechanics cannot be read or recovered.
