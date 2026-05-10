# Building System Spec Skill

> Internal sub-skill for game-systems pipelines. Status: bundled, inactive, not wired.

## Overview

Defines building/base/construction systems: placement, grid, costs,
requirements, upgrades, adjacency, production, destruction, and UI/runtime needs.

## Input Contract

Required: mechanics spec or building feature brief.

Optional: economy spec, crafting spec, level layout, content taxonomy, art
requirements, and runtime constraints.

## Output Contract

Writes `.allforai/game-design/systems/building-system-spec.json` and a report.
Buildings include `building_id`, `placement_rule`, `cost_refs`, `unlock_rule`,
`upgrade_rule`, `adjacency_rule`, `production_rule`, `destruction_rule`,
`ui_requirements`, `art_requirements`, `state`, and `consumer_refs`.

Allowed states: `not_applicable`, `draft`, `validated`, `needs_revision`,
`blocked_by_mechanics`, `blocked_by_layout`.

## Invocation Contract

```json
{"skill":"game-systems/building-system-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/systems"}
```

Supported modes: `spec_validate`, `not_applicable`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check placement validity, cost sources, collision/layout constraints, upgrade
paths, and whether each building has gameplay purpose.

Repair routing: layout issues route to game-level; economy issues route to
economy-source-sink; art gaps route to game-art asset requirements.

## Completion Conditions

Return `COMPLETED` when building rules are playable or not applicable. Return
`FAILED_VALIDATION` when placement, cost, or ownership blocks use.
