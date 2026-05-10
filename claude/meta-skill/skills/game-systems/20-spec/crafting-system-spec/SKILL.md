# Crafting System Spec Skill

> Internal sub-skill for game-systems pipelines. Status: bundled, inactive, not wired.

## Overview

Defines crafting, upgrading, recipes, stations, materials, unlocks, success
rules, costs, outputs, and economy constraints.

## Input Contract

Required: item/content list and economy spec.

Optional: progression curve, inventory spec, reward pricing, UI requirements,
and level/content placement.

## Output Contract

Writes `.allforai/game-design/systems/crafting-system-spec.json` and a report.
Recipes include `recipe_id`, `input_refs`, `output_refs`, `station_rule`,
`unlock_rule`, `cost_refs`, `success_rule`, `failure_rule`, `ui_requirements`,
`state`, and `consumer_refs`.

Allowed states: `not_applicable`, `draft`, `validated`, `needs_revision`,
`blocked_by_economy`, `blocked_by_items`.

## Invocation Contract

```json
{"skill":"game-systems/crafting-system-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/systems"}
```

Supported modes: `spec_validate`, `not_applicable`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check recipes are reachable, material sources exist, outputs have purpose, and
crafting does not bypass progression/economy constraints.

Repair routing: material gaps route to content/economy specs; pricing gaps
route to reward-pricing; UI gaps route to game-ui.

## Completion Conditions

Return `COMPLETED` when crafting is coherent or not applicable. Return
`FAILED_VALIDATION` when recipes are unreachable or economy-breaking.
