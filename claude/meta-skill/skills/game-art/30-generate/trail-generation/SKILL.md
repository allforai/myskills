---
name: game-art-30-generate-trail-generation
description: Internal bundled meta-skill module for game-art/30-generate/trail-generation; use within generated bootstrap node-specs when this exact contract is selected.
---

# Trail Generation Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill produces trail and ribbon VFX artifacts for projectiles, sword
swings, dashes, speed lines, beam paths, cursor streaks, and UI motion accents.
It is called by `vfx-generation` when `implementation_mode` includes `trail`.

## Scope

In scope:
- trail timing and anchor specs,
- width/color/alpha over life,
- strip texture specs,
- generated or registered trail textures,
- preview manifests and validation,
- repair loops for unclear path, excessive occlusion, or style mismatch.

Out of scope:
- particle emitters,
- full sprite-sheet VFX,
- gameplay movement logic,
- final engine-specific trail renderer code.

## Input Contract

| Input | Required fields | Missing behavior |
|---|---|---|
| Trail VFX request | `vfx_id`, `file_prefix`, `presentation_layer`, `dimension`, `anchor`, `lifecycle`, `trail` | Return `UPSTREAM_DEFECT`. |

Optional inputs: `vfx-spec.json`, `art-style-guide.json`, registries, existing
trail textures, and preview capabilities.

## Image Generation Upstream Contract

When trail strip textures are generated, each bitmap request must follow
`game-art/30-generate/image-generation-contract/SKILL.md`.

Use normalized image requests with `purpose=trail_texture` and
`generation_profile.task_type=trail_texture`. The request must use
`prompt_template=trail_texture_prompt` and a model profile that supports
transparent strip/gradient texture output. It must include trail width/length,
color over life, alpha/fade rule, layer, style, output path, positive prompt,
negative prompt, stretch suitability checks, fade checks, and
`downstream_feedback.enabled=true`.

If trail preview, VFX generation, runtime import, or visual QA reports
`BAD_ALPHA`, `STYLE_DRIFT`, `WRONG_SCALE`, `CROPPED_SUBJECT`, or
`LOW_READABILITY` for a trail texture, process the defect through
`image-generation-contract` and regenerate when root cause is `image_generation`
or `prompt_contract`.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/art/vfx/trails/trail-spec.json` | yes | Trail renderer-neutral specs, strip textures, timing. | vfx-generation, runtime import, QA. |
| `.allforai/game-design/art/vfx/trails/trail-manifest.json` | yes | Paths, anchors, textures, previews, states. | vfx-generation, registries. |
| `.allforai/game-design/art/vfx/trails/trail-report.json` | yes | Validation and repair results. | diagnostics and QA. |

## Invocation Contract

```json
{
  "skill": "game-art/trail-generation",
  "mode": "spec_generate_validate",
  "input_paths": {
    "vfx_spec": ".allforai/game-design/art/vfx/vfx-spec.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "ui_registry": ".allforai/game-design/ui/ui-registry.json"
  },
  "generation": {
    "image_generation_available": true,
    "preview_renderer_available": true,
    "vision_validation_available": true,
    "max_repair_attempts": 3
  },
  "output_root": ".allforai/game-design"
}
```

Supported modes: `spec_only`, `spec_generate_validate`, `validate_existing`,
`register_existing`.

## Automatic Validation

Run deterministic checks:
1. Trail has anchor, duration, width over life, color over life, fade rule, and
   output path.
2. Paths route to the correct presentation layer and start with `file_prefix`.
3. Trail duration matches the associated VFX timing.
4. UI trails define max attention duration.
5. World trails define occlusion and gameplay-readability limits.

Run visual validation when previews exist:
1. Trail direction and origin are readable.
2. Trail does not hide critical gameplay/UI content.
3. Fade and width transitions are smooth.
4. Strip texture style matches the art style guide.

Repair up to 3 times; otherwise emit a simplified solid-color or no-texture
fallback.

## Completion Conditions

Return `COMPLETED` only when specs, manifest, report, and available previews
validate. Return `COMPLETED_WITH_LIMITS` for simplified or spec-only trails.
