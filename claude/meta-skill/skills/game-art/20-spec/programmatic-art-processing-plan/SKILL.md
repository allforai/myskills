---
name: game-art-20-spec-programmatic-art-processing-plan
description: Define the deterministic 2D art processing plan that turns LLM raw materials into consistent runtime assets through layers, parts, palettes, atlases, animation, tile rules, masks, shaders, UI components, and previews.
---

# Programmatic Art Processing Plan Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive,
> image-generation upstream.

## Purpose

For 2D games, the first choice is not "LLM generates final assets". The first
choice is:

```text
LLM/raw source produces stable materials
-> deterministic tools process, compose, animate, package, and preview them
-> QA validates the processed runtime result
```

This skill decides which deterministic processing methods apply to each asset
family before prompt compilation and batch generation.

## Input Contract

Required:

```text
.allforai/game-design/art/art-direction-benchmark.json
.allforai/game-design/art/asset-acceptance-criteria.json
.allforai/game-design/asset-registry.json
.allforai/game-design/art-pipeline-config.json
```

Optional:

```text
.allforai/game-design/art/env/2d-animation-toolchain-registry.json
.allforai/game-design/art/env/production-tool-capability-registry.json
.allforai/game-design/art/visual-style-tokens.json
.allforai/game-design/ui/ui-registry.json
.allforai/game-design/design/program-development-node-handoff.json
```

If required processing tools are unavailable, return a blocked status with the
missing automatable capability. Do not silently switch to direct final-image
generation unless the acceptance criteria allow it and the risk is recorded.

## Output Contract

Writes:

```text
.allforai/game-design/art/programmatic-art-processing-plan.json
.allforai/game-design/art/programmatic-art-processing-plan.md
```

The JSON must include:

```json
{
  "status": "ready | blocked",
  "default_policy": "material_first",
  "asset_family_processing": {},
  "processing_methods": [],
  "tool_requirements": [],
  "raw_material_requirements": {},
  "postprocess_outputs": {},
  "preview_outputs": {},
  "fallback_risks": []
}
```

## Processing Methods

Evaluate every active 2D asset family against these methods and apply all that
improve consistency:

- `layer_composition`: background, character, UI, VFX, foreground/midground/
  background, occlusion, shadow, highlight, and light layers.
- `part_assembly`: character outfit/body parts, icon symbol/frame/background,
  tile base/edge/decor, item body/material/glow, UI skin/state parts.
- `palette_recolor`: rarity, faction, seasonal, status, locked/unlocked,
  damage/poison/freeze, and theme variants.
- `atlas_slicing`: sprite atlas, texture pack, nine-slice panels, tilemap
  sheets, animation spritesheets, UI component atlases.
- `skeletal_or_part_animation`: bones, pivots, part tweening, pose swap,
  DragonBones/Spine-compatible data, or runtime tween animation.
- `frame_sequence_processing`: keyframe cleanup, alignment, anchor, bounding
  box, alpha cleanup, FPS, loop metadata, GIF/WebM previews.
- `tile_rule_generation`: autotile, Wang tile, bitmask, edges/corners,
  decoration layers, collision/walkability metadata, preview maps.
- `procedural_decoration`: scatter props, grass/stone/flowers/clouds/water
  lines, cracks, moss, dust, particles, and background decoration.
- `mask_alpha_matte_processing`: cutout, alpha cleanup, edge feather, masks,
  shadow/highlight separation, line separation, edit masks.
- `runtime_material_filters`: outline, glow, blur, drop shadow, color grading,
  dissolve, hit flash, ripple, pixelate, scanline, accessibility-safe effects.
- `ui_componentization`: 9-slice panels, button states, progress fills, icon
  slots, badges, modals, rarity frames, component skins.
- `automatic_preview_generation`: contact sheets, atlas previews, tilemap
  previews, animation previews, UI screenshots, gameplay screenshots, and
  before/after repair sheets.

## Raw Material Requirements

For every selected method, define what the LLM should generate as raw material:

- isolated parts with transparent or neutral backgrounds;
- layered plates instead of flattened scenes;
- clean motifs/textures instead of complete procedural variants;
- pose references or key poses instead of full final animation;
- foreground symbols and frame ingredients instead of baked UI icons;
- VFX source sprites, masks, or gradients instead of final in-engine effects;
- editable base images plus mask regions for image-to-image repair.

## Automatic Validation

Reject with `FAILED_VALIDATION` when:

- an asset family uses direct final-image generation without checking all
  relevant processing methods;
- a selected processing method has no raw material requirements;
- required automatable tools are missing but the plan still says `ready`;
- postprocess outputs and preview outputs are not declared;
- material-first fallback risks are not recorded;
- QA cannot trace a final runtime asset back to raw material and processing
  method.

## Completion Conditions

Return `COMPLETED` only when every active asset family has a processing policy,
raw material requirements, postprocess outputs, preview outputs, and tool
requirements. Direct final-image generation must be justified as an exception,
not the default.
