---
name: game-art-10-design-visual-hook-design
description: Internal bundled meta-skill module for game-art/10-design/visual-hook-design; use within generated bootstrap node-specs when the game needs visual selling points, screenshot-level appeal, and recognizable art hooks before asset production.
---

# Visual Hook Design Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the game's primary visual hooks: the memorable shapes, moments,
contrasts, transformations, feedback motifs, character/world signatures, and
screenshot compositions that make the game recognizable and marketable.

This skill sits before bulk asset generation. It converts product/game design
into art-direction decisions that downstream assets must serve.

## Input Contract

Required: product concept or game design doc, art direction input contract, and
target audience/platform.

Optional: market/competitor references, monetization context, store page goals,
retention hooks, core loop, worldbuilding, visual style tokens, UI direction,
and human visual preferences.

## Output Contract

Writes:

- `.allforai/game-design/art/visual-hook-design.json`
- `.allforai/game-design/art/visual-hook-design-report.html`

Hook entries must include `hook_id`, `hook_type`, `product_signal`,
`player_emotion`, `visual_promise`, `primary_subject`, `supporting_assets`,
`composition_rule`, `motion_or_vfx_rule`, `color_shape_rule`,
`screenshot_use_case`, `downstream_skill_refs`, `acceptance_checks`,
`risk_notes`, `state`, and `consumer_refs`.

Allowed `hook_type` values: `character_silhouette`, `world_signature`,
`mechanic_visualization`, `transformation_moment`, `reward_moment`,
`combat_impact`, `puzzle_state_change`, `collection_fantasy`, `ui_identity`,
`store_screenshot`, `brand_mark`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_product_concept`, `blocked_by_art_direction`.

Downstream consumers: `visual-style-tokens`, `character-layer-sheet`,
`background-generation`, `portrait-generation`, `icon-generation`,
`vfx-spec`, `juice-feedback-art-spec`, `game-ui`, `art-preview-qa`,
`silhouette-readability-qa`, and store/screenshot generation nodes.

## Invocation Contract

```json
{
  "skill": "game-art/visual-hook-design",
  "mode": "design_validate",
  "input_paths": {
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "art_direction": ".allforai/game-design/art/art-direction-input-contract.json",
    "visual_style_tokens": ".allforai/game-design/art/visual-style-tokens.json"
  },
  "output_root": ".allforai/game-design/art"
}
```

Supported modes: `design_validate`, `validate_existing`, `repair_existing`.

## Method

Create no more than 1-3 primary hooks. A hook must be easy to describe in one
sentence and visible in a small screenshot or social thumbnail.

Hook design checklist:
1. Name the product promise the hook supports.
2. Choose the visual subject that carries it.
3. Define the simplest readable shape/color/motion signature.
4. Define how it appears in live gameplay, screenshots, iconography, UI, and
   reward/retention moments.
5. Define what the art pipeline must avoid so the hook does not become generic.

Do not create hooks that rely only on lore text, abstract mood, or invisible
system design. The hook must be visible.

## Automatic Validation

Run these checks:
1. Every hook maps to a product/game-design signal.
2. Every hook names downstream asset categories that must express it.
3. Every hook has small-thumbnail readability expectations.
4. Every hook includes a screenshot or first-impression use case.
5. Hooks are distinct from one another; no duplicate color/shape/motion role.
6. UI and VFX implications are recorded when the hook appears in interaction.
7. The hook does not contradict art direction or target platform constraints.
8. The hook has repair targets for weak silhouette, weak contrast, generic
   subject, overbusy composition, or production cost risk.

## Completion Conditions

Return `COMPLETED` when each selected hook is product-grounded, visually
concrete, downstream-routable, and has acceptance checks.

Return `FAILED_VALIDATION` when hooks are generic, text-only, not visible in
gameplay/screenshots, or conflict with product/art direction.
