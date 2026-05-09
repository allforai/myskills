# Decal Generation Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill produces decal VFX artifacts such as scorch marks, cracks, blood
marks, bullet holes, ice patches, magic runes, target markers, and impact stains.
It is called by `vfx-generation` when `implementation_mode` includes `decal`.

## Scope

In scope:
- decal prompt/spec generation,
- projection/placement metadata,
- generated or registered decal textures,
- lifetime/fade rules,
- validation and repair loops.

Out of scope:
- particle systems,
- full terrain tilesets,
- final engine projector implementation,
- manual texture cleanup.

## Input Contract

| Input | Required fields | Missing behavior |
|---|---|---|
| Decal VFX request | `vfx_id`, `file_prefix`, `presentation_layer`, `dimension`, `anchor`, `lifecycle`, `decal` | Return `UPSTREAM_DEFECT`. |

Optional inputs: `vfx-spec.json`, `tileset-spec.json`, `art-style-guide.json`,
registries, existing decal textures, and preview capabilities.

## Image Generation Upstream Contract

Every generated decal texture must follow
`game-art/30-generate/image-generation-contract/SKILL.md`.

Use normalized image requests with `purpose=decal` and
`generation_profile.task_type=decal`. The request must use
`prompt_template=decal_prompt` and a model profile that supports transparent
texture output. It must include surface compatibility, projection/placement,
size, lifetime, fade, blend policy, output path, positive prompt, negative
prompt, alpha/blend checks, surface readability checks, and
`downstream_feedback.enabled=true`.

If VFX generation, tile preview, runtime projection, or visual QA reports
`BAD_ALPHA`, `CROPPED_SUBJECT`, `STYLE_DRIFT`, `WRONG_SCALE`, or
`LOW_READABILITY`, process the defect through `image-generation-contract` and
regenerate when root cause is `image_generation` or `prompt_contract`.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/art/vfx/decals/decal-spec.json` | yes | Decal texture, placement, projection, lifetime specs. | vfx-generation, runtime import, QA. |
| `.allforai/game-design/art/vfx/decals/decal-manifest.json` | yes | Paths, metadata, previews, states. | vfx-generation, registries. |
| `.allforai/game-design/art/vfx/decals/decal-report.json` | yes | Validation and repair results. | diagnostics and QA. |

## Invocation Contract

```json
{
  "skill": "game-art/decal-generation",
  "mode": "spec_generate_validate",
  "input_paths": {
    "vfx_spec": ".allforai/game-design/art/vfx/vfx-spec.json",
    "tileset_spec": ".allforai/game-design/art/tilesets/tileset-spec.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "asset_registry": ".allforai/game-design/asset-registry.json"
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
1. Decal has texture path, anchor/projection, size, lifetime, fade, and blend.
2. Paths route to a valid VFX output root and start with `file_prefix`.
3. World decals define surface compatibility.
4. UI decals define component/screen compatibility when used.
5. Lifetime and cleanup rules exist.

Run visual validation when previews exist:
1. Decal reads as a mark, not a blocking object.
2. Texture is not cropped.
3. Alpha/blend works on intended surfaces.
4. Decal does not obscure critical gameplay or UI.
5. Style matches the art style guide.

Repair up to 3 times; otherwise emit a simplified flat mark or disabled decal
fallback.

## Completion Conditions

Return `COMPLETED` only when specs, manifest, report, and available previews
validate. Return `COMPLETED_WITH_LIMITS` for placeholder or simplified decals.
