# Icon Generation Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill defines the production protocol for game icon sets. It creates
consistent icon specs, prompts, generated images, atlases, and validation
reports for skills, items, currencies, resources, buffs, debuffs, achievements,
menus, and HUD indicators.

Icons are game-art assets that UI consumes. `game-ui` must reference icon
outputs through `asset-registry.json` or `ui-registry.json`; it must not
silently regenerate a parallel icon set.

## Scope

In scope:
- icon inventory normalization,
- icon style and shape-language rules,
- icon prompt/spec generation,
- batch generation or spec-only fallback,
- size and background variants,
- atlas and manifest planning,
- deterministic and visual validation,
- automatic repair for inconsistent style, cropped symbols, or unreadable small
  icons.

Out of scope:
- full UI layout,
- button/component states,
- final frontend implementation,
- manually drawn icon cleanup,
- human approval.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| `.allforai/game-design/art-asset-inventory.json` or caller icon list | `asset_id`, `name`, `type` for icon-like assets | Return `UPSTREAM_DEFECT` if no icon targets can be resolved. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/game-design/asset-registry.json` | `asset_id`, `file_prefix`, paths, state | Derive `ico_{asset_id}` prefix. |
| `.allforai/game-design/art-style-guide.json` | palette, rendering style, line weight, material | Use readable neutral icon style. |
| `.allforai/concept-contract.json` | visual promise, canonical prefixes | Use inventory-derived prefixes. |
| `.allforai/game-design/game-design-doc.json` | skills, items, resources, status effects | Infer semantic categories from asset names. |
| `.allforai/game-design/ui/ui-registry.json` | UI icon consumers | Generate icons as shared game-art assets. |

### Normalized input

```json
{
  "schema_version": "1.0",
  "icons": [
    {
      "asset_id": "fireball",
      "name": "Fireball",
      "file_prefix": "ico_fireball",
      "category": "skill | item | currency | resource | buff | debuff | achievement | menu | hud | other",
      "semantic": "fire damage projectile",
      "consumer_refs": ["screen_gameplay", "cmp_skill_card"]
    }
  ],
  "style": {
    "dimension": "2d",
    "render_style": "painted | vector | pixel | flat | hand_drawn | unknown",
    "background_policy": "transparent | framed | both",
    "sizes": [64, 128, 256, 512]
  }
}
```

## Icon Taxonomy

| Category | Examples | Visual rule |
|---|---|---|
| `skill` | fireball, heal, dash, shield | Use strong silhouette and action direction. |
| `item` | potion, key, sword, gem | Object-centered, readable at small size. |
| `currency` | coin, crystal, energy | Simple shape, high contrast, reusable in HUD. |
| `resource` | health, mana, stamina | Distinct color and symbol language. |
| `buff` | haste, armor up, damage up | Upward/positive cue, avoid clutter. |
| `debuff` | poison, slow, burn | Warning cue, clear negative shape language. |
| `achievement` | medal, trophy, badge | Framed or emblem-like. |
| `menu` | settings, shop, inventory | Functional UI glyph, simple and neutral. |
| `hud` | warning, objective, marker | Maximum readability and contrast. |

## Creative Workflow

| Stage | Purpose | Main output |
|---|---|---|
| 1. Select icon targets | Resolve icon assets and consumers. | `selected_icons[]` |
| 2. Define style tokens | Shape, line, fill, contrast, frame, background. | `icon_style_tokens` |
| 3. Define semantic symbols | What each icon must communicate. | `icon_semantics[]` |
| 4. Write icon specs | Prompt, negative prompt, size variants, path plan. | `icon_specs[]` |
| 5. Generate or register images | Use available image tool or existing outputs. | `icons/*.png` |
| 6. Validate | Small-size readability, consistency, cropping, uniqueness. | `icon_validation` |
| 7. Repair | Revise prompt/spec and regenerate up to capped attempts. | `repair_log[]` |
| 8. Export manifest | Stable paths, states, atlas plan. | `icon-manifest.json` |

## Image Generation Upstream Contract

Every generated icon must follow
`game-art/30-generate/image-generation-contract/SKILL.md`.

Use normalized image requests with `purpose` set to `skill_icon`, `item_icon`,
`currency_icon`, `status_icon`, or `ui_icon`. The request must include positive
prompt, negative prompt, output path, small-size readability checks, alpha or
background policy, and `downstream_feedback.enabled=true`.

If a downstream UI, HUD, inventory, shop, or runtime consumer reports
`LOW_READABILITY`, `STYLE_DRIFT`, `TEXT_ARTIFACT`, `CROPPED_SUBJECT`,
`WRONG_SCALE`, or `BAD_ALPHA` against an icon, process the feedback through
`image-generation-contract` before revising downstream specs. Regenerate the
icon when root cause is `image_generation` or `prompt_contract`.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/art/icons/icon-spec.json` | yes | Canonical icon specs, prompts, sizes, semantics. | image generation, QA. |
| `.allforai/game-design/art/icons/icon-manifest.json` | yes | Generated/registered icon paths, variants, atlas refs. | asset-registry, game-ui, frontend. |
| `.allforai/game-design/art/icons/icon-report.json` | yes | Validation, repair log, unresolved limits. | diagnostics and QA. |
| `.allforai/game-design/art/icons/*.png` | when generated | Icon image variants. | UI, HUD, inventory, shop, gameplay. |
| `.allforai/game-design/art/atlases/icon-atlas.json` | optional | Atlas packing plan or runtime atlas metadata. | frontend/runtime import. |

## Invocation Contract

```json
{
  "skill": "game-art/icon-generation",
  "mode": "spec_generate_validate",
  "input_paths": {
    "art_asset_inventory": ".allforai/game-design/art-asset-inventory.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "concept_contract": ".allforai/concept-contract.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "ui_registry": ".allforai/game-design/ui/ui-registry.json"
  },
  "icon_filter": {
    "asset_ids": [],
    "categories": []
  },
  "generation": {
    "image_generation_available": true,
    "vision_validation_available": true,
    "max_repair_attempts": 3
  },
  "output_root": ".allforai/game-design"
}
```

Supported modes:

| Mode | Behavior |
|---|---|
| `spec_only` | Write icon specs and manifest placeholders. |
| `spec_generate_validate` | Write specs, generate/register images, validate, repair, and report. |
| `validate_existing` | Validate existing icon outputs against specs. |
| `register_existing` | Register existing icon files without regenerating. |

## Automatic Validation

Run deterministic checks:
1. Every icon has `asset_id`, `file_prefix`, category, semantic, and output path.
2. Every icon path starts with `.allforai/game-design/art/icons/`.
3. Every path starts with the resolved `file_prefix`.
4. Every generated variant declares size and background policy.
5. No duplicate icon category/semantic pair uses the same visual symbol unless
   intentionally linked.
6. UI consumers reference icon `asset_id` values, not raw filenames.

Run visual validation when images exist:
1. Icon silhouette is readable at 64px.
2. Symbol is not cropped.
3. Background is transparent or framed as requested.
4. Icon style is consistent across the set.
5. Similar gameplay concepts remain distinguishable.
6. Text, letters, and decorative labels are absent unless explicitly required.
7. Important symbol detail does not rely on tiny internal marks.

If validation fails, repair the prompt/spec and regenerate up to 3 times. If it
still fails, mark the icon `automation_limited` and preserve the best validated
spec or placeholder.

## Completion Conditions

Return `COMPLETED` only when required specs and manifests validate, and generated
icons pass validation when generation is available. Return
`COMPLETED_WITH_LIMITS` when only spec artifacts or placeholders can be produced.

## Downstream Use

- `asset-registry` may register `icon-manifest.json` outputs as generated or
  approved assets.
- `game-ui/ui-registry` may reference icons by `asset_id` for HUD, shop,
  inventory, menu, and component specs.
- `game-ui/component-state-spec` may use icon refs in component states.
- `game-ui/ui-mockup-generation` may place icon refs in mockups without
  regenerating the icon art.
