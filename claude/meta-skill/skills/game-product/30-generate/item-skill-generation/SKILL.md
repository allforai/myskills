# Item Skill Generation Skill

> Internal sub-skill for game-product pipelines. Status: bundled, inactive, not wired.

## Overview

Generates items, equipment, skills, upgrades, status effects, and their data,
icon, VFX, animation, UI, economy, and runtime requirements.

## Input Contract

Required: mechanics spec, progression spec, economy spec, and content taxonomy.

Optional: combat spec, player experience contract, level design spec, art
direction, UI constraints, runtime data schema, and monetization constraints.

## Output Contract

Writes:

- `.allforai/game-design/content/item-skill-set.json`
- `.allforai/game-design/content/item-skill-report.json`

Entries must include `entry_id`, `entry_kind`, `gameplay_purpose`,
`activation_rule`, `effect_rule`, `cost_refs`, `reward_refs`,
`progression_refs`, `rarity_or_tier`, `counterplay_or_limit`,
`ui_requirements`, `icon_requirements`, `vfx_requirements`,
`animation_event_requirements`, `audio_requirements`, `runtime_requirements`,
`data_table_refs`, `state`, and `consumer_refs`.

Allowed states: `draft`, `generated`, `validated`, `needs_revision`,
`blocked_by_mechanics`, `blocked_by_economy`.

## Invocation Contract

```json
{
  "skill": "game-product/item-skill-generation",
  "mode": "generate_validate",
  "input_paths": {
    "mechanics": ".allforai/game-design/systems/mechanics-spec.json",
    "progression": ".allforai/game-design/systems/progression-spec.json",
    "economy": ".allforai/game-design/systems/product-economy-spec.json",
    "content_taxonomy": ".allforai/game-design/content/content-taxonomy-spec.json"
  },
  "output_root": ".allforai/game-design/content"
}
```

Supported modes: `generate_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that each item/skill has purpose, activation, effect, cost/reward, limit,
UI/icon/VFX ownership, and runtime data mapping. Reject duplicates that do not
create new player choices.

Repair routing: missing mechanics route to `mechanics-spec`; invalid costs
route to `economy-spec`; art/UI/VFX requirements route to content taxonomy and
downstream asset skills.

## Completion Conditions

Return `COMPLETED` when item/skill entries are useful and downstream-owned.
Return `FAILED_VALIDATION` when entries are mechanically redundant or unmapped.
