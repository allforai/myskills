---
name: game-design-30-generate-level-plan-generation
description: Internal bundled meta-skill module for game-design/30-generate/level-plan-generation; use within generated bootstrap node-specs when this exact contract is selected.
---

# Level Plan Generation Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Generates game design level plan contracts: layout diagrams, tile/map
metadata, spawn points, goals, rewards, encounters, collision/walkability, and
preview requirements.

## Input Contract

Required: level design spec and mechanics spec.

Optional: progression spec, economy spec, combat spec, content taxonomy,
tileset requirements, target engine, and game-level layout/blockout outputs.

## Output Contract

Writes:

- `.allforai/game-design/levels/level-blockout-manifest.json`
- `.allforai/game-design/levels/level-blockout-report.json`
- blockout files under `.allforai/game-design/levels/blockouts/`

Blockout entries must include `level_id`, `blockout_kind`, `dimensions`,
`regions`, `critical_path`, `spawn_points`, `goal_points`, `encounter_points`,
`reward_points`, `collision_layers`, `camera_rules`, `asset_placeholders`,
`preview_refs`, `runtime_consumer_refs`, `state`, and `consumer_refs`.

Allowed states: `draft`, `generated`, `validated`, `needs_revision`,
`blocked_by_level_spec`, `blocked_by_mechanics`.

## Invocation Contract

```json
{
  "skill": "game-design/level-plan-generation",
  "mode": "generate_validate",
  "input_paths": {
    "level_design": ".allforai/game-design/design/level-design-spec.json",
    "mechanics": ".allforai/game-design/systems/mechanics-spec.json"
  },
  "output_root": ".allforai/game-design/levels"
}
```

Supported modes: `generate_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check reachability, objective path, collision consistency, spawn/goal presence,
reward placement, and mapping to level design beats. If an executable map
validator is unavailable, state that validation cannot run; do not substitute.

Repair routing: missing level intent routes to `level-design-spec`; collision
and layout details route to `game-level/level-layout-spec`; art placeholders
route to `content-taxonomy-spec` and `game-art`.

## Completion Conditions

Return `COMPLETED` when blockouts are generated and validated with available
tools. Return `FAILED_VALIDATION` when required maps cannot be validated.
