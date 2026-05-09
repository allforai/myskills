# Item Art Generation Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Generates item and equipment art for inventories, shops, loot, crafting, cards,
and pickups. Icons remain handled by `icon-generation`; this skill handles
larger item depictions and variants.

## Input Contract

Required: item id, category, rarity/state, gameplay meaning, style, output path.
Optional: `asset-registry.json`, economy/item specs, `image-generation-contract`.

## Output Contract

Writes:
- `.allforai/game-design/art/items/item-art-spec.json`
- `.allforai/game-design/art/items/item-art-manifest.json`
- `.allforai/game-design/art/items/item-art-report.json`
- generated item images when enabled.

Manifest entries must include `item_id`, `asset_id`, `file_prefix`, `category`,
`rarity`, `state_variant`, `inventory_size`, `shop_use`, `image_request_id`,
`path`, `state`, `consumers`, and `validation`.

Allowed states: `spec_ready`, `generated`, `approved`, `needs_revision`,
`automation_limited`.

Downstream consumers include economy specs, inventory UI, shop UI, loot tables,
runtime import checks, and icon generation when smaller icons are derived.

Image requests must follow `image-generation-contract` with
`generation_profile.task_type=item_art` and `prompt_template=item_art_prompt`.
Use a model profile suited to isolated item output, alpha/background control,
category readability, and rarity/state clarity.

## Invocation Contract

```json
{
  "skill": "game-art/item-art-generation",
  "mode": "spec_generate_validate",
  "input_paths": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "style_tokens": ".allforai/game-design/art/visual-style-tokens.json",
    "image_generation_contract": "${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/image-generation-contract/SKILL.md"
  },
  "output_root": ".allforai/game-design"
}
```

Supported modes: `spec_only`, `spec_generate_validate`, `validate_existing`.

## Automatic Validation

Check item category, rarity/readability, style consistency, no text/crop, alpha
policy, UI/shop/inventory feedback, and duplicate visual confusion.

If shop/inventory QA reports rarity confusion, category mismatch, bad alpha,
wrong scale, crop, or style drift, classify root cause. Regenerate through
`image-generation-contract` for image defects; repair economy/item metadata for
semantic defects.

## Completion Conditions

Return `COMPLETED` when required item images and manifest validate. Return
`COMPLETED_WITH_LIMITS` for placeholder items.
