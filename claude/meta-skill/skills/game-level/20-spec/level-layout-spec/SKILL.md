# Level Layout Spec Skill

> Internal sub-skill for game-level pipelines. Status: bundled, inactive, not wired.

## Overview

Defines layout grammar for maps, rooms, lanes, platforms, grids, routes,
spawns, goals, hazards, checkpoints, and collision metadata.

## Input Contract

Required: level registry and level flow. Optional: tileset spec, prop manifest,
combat spec, target runtime.

## Output Contract

Writes `.allforai/game-design/levels/level-layout-spec.json` and
`.allforai/game-design/levels/level-layout-report.json`.

Layout entries must include `level_id`, `layout_type`, `bounds`, `spawn_points`,
`goals`, `critical_path`, `optional_paths`, `hazards`, `encounters`,
`collision_model`, `tileset_refs`, `prop_refs`, and `camera_rules`.

Each layout entry must also include `level_flow_ref`, `objective_refs`,
`progression_refs`, `combat_refs`, `consumer_refs`, `state`, and
`playability_requirements`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_level_flow`, `blocked_by_systems`, `blocked_by_art`.

Downstream consumers: `game-level/level-blockout-generation`,
`game-level/level-playability-qa`, `tileset-generation`, `prop-generation`,
`combat-spec`, `progression-spec`, and runtime map import.

## Invocation Contract

```json
{"skill":"game-level/level-layout-spec","mode":"spec_validate","input_paths":{"level_registry":".allforai/game-design/levels/level-registry.json","level_flow":".allforai/game-design/levels/level-flow-design.json","tileset_spec":".allforai/game-design/art/tilesets/tileset-spec.json"},"output_root":".allforai/game-design/levels"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check dimensions, spawn/goal placement, connectivity, collision/walkability,
objective coverage, hazard fairness, camera bounds, and tileset compatibility.

If a required tile or prop is missing, return `UPSTREAM_DEFECT` with the owning
art requirement; do not substitute placeholder art as validation evidence.

Repair routing: impossible routes, unreachable objectives, or unfair hazard
grammar repair here; missing level ordering repairs `level-flow-design`; missing
combat or reward semantics repair `combat-spec` or `progression-spec`; visual
tile/prop defects route to the owning art skill.

## Completion Conditions

Return `COMPLETED` when layout spec and report validate. Return
`FAILED_VALIDATION` when required layout, art, collision, or playability
evidence is missing.
