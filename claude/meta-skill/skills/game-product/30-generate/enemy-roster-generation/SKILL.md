# Enemy Roster Generation Skill

> Internal sub-skill for game-product pipelines. Status: bundled, inactive, not wired.

## Overview

Generates a coherent enemy roster from combat, level, progression, economy, and
content taxonomy specs.

## Input Contract

Required: combat spec or explicit non-combat enemy/hazard brief, content
taxonomy, and progression context.

Optional: level design spec, economy spec, art direction, VFX/audio
requirements, runtime AI constraints, and difficulty targets.

## Output Contract

Writes:

- `.allforai/game-design/content/enemy-roster.json`
- `.allforai/game-design/content/enemy-roster-report.json`

Enemy entries must include `enemy_id`, `role`, `difficulty_tier`,
`behavior_summary`, `attack_rules`, `defense_rules`, `counterplay`,
`spawn_contexts`, `drop_refs`, `progression_refs`, `level_refs`,
`art_requirements`, `animation_requirements`, `vfx_requirements`,
`audio_requirements`, `runtime_ai_requirements`, `data_table_refs`, `state`,
and `consumer_refs`.

Allowed states: `not_applicable`, `draft`, `generated`, `validated`,
`needs_revision`, `blocked_by_combat_spec`.

## Invocation Contract

```json
{
  "skill": "game-product/enemy-roster-generation",
  "mode": "generate_validate",
  "input_paths": {
    "combat": ".allforai/game-design/systems/combat-spec.json",
    "content_taxonomy": ".allforai/game-design/content/content-taxonomy-spec.json",
    "progression": ".allforai/game-design/systems/progression-spec.json"
  },
  "output_root": ".allforai/game-design/content"
}
```

Supported modes: `generate_validate`, `not_applicable`, `validate_existing`,
`repair_existing`.

## Automatic Validation

Check that enemy roles cover intended encounters, each enemy has counterplay,
readability requirements, spawn context, and data/art/VFX/audio owners. Reject
rosters that add enemies not tied to levels, combat, or progression.

Repair routing: combat gaps route to `combat-spec`; level placement gaps route
to `level-design-spec`; art/VFX/audio gaps route to content taxonomy and
downstream production skills.

## Completion Conditions

Return `COMPLETED` when the roster is coherent and downstream-owned. Return
`FAILED_VALIDATION` when enemies lack role, counterplay, or placement.
