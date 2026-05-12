---
name: game-systems-20-spec-inventory-system-spec
description: Internal bundled meta-skill module for game-systems/20-spec/inventory-system-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Inventory System Spec Skill

> Internal sub-skill for game-systems pipelines. Status: bundled, inactive, not wired.

## Overview

Defines inventory rules: item storage, stack limits, categories, sorting,
capacity, equipment slots, loss rules, UI requirements, and data schema.

## Input Contract

Required: content taxonomy or item/skill design list.

Optional: economy spec, progression spec, UI registry, reward pricing, and
target engine data constraints.

## Output Contract

Writes `.allforai/game-design/systems/inventory-system-spec.json` and a report.
Entries include `inventory_id`, `item_categories`, `capacity_rule`, `stack_rule`,
`slot_rules`, `sort_filter_rules`, `loss_rules`, `ui_requirements`,
`data_requirements`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_items`.

## Invocation Contract

```json
{"skill":"game-systems/inventory-system-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/systems"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every storable item has category, stack behavior, capacity impact, and UI
display rule. Reject inventories that can lose required quest/progression items
without recovery.

Repair routing: item gaps route to item-skill-design-generation; UI gaps route
to game-ui; economy interactions route to economy-source-sink.

## Completion Conditions

Return `COMPLETED` when inventory rules are complete. Return
`FAILED_VALIDATION` when required items cannot be stored, found, or recovered.
