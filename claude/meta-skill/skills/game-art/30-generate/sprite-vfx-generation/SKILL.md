# Sprite VFX Generation Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill produces sprite-sheet VFX artifacts for explosions, impact
bursts, shockwaves, magic casts, slash arcs, reward pops, and other frame-based
effects. It is called by `vfx-generation` when `implementation_mode` includes
`sprite_sheet`.

## Scope

In scope:
- sprite-sheet prompt/spec generation,
- frame count, FPS, frame size, loop and alpha policy,
- generated or registered sheet images,
- frame metadata and preview manifests,
- deterministic and visual validation,
- repair loops for unreadable timing, cropped frames, style drift, or bad alpha.

Out of scope:
- choosing VFX semantics,
- particle emitter configs,
- shader code,
- final engine import implementation,
- human cleanup.

## Input Contract

| Input | Required fields | Missing behavior |
|---|---|---|
| Sprite-sheet VFX request | `vfx_id`, `file_prefix`, `presentation_layer`, `dimension`, `lifecycle`, `sprite_sheet` | Return `UPSTREAM_DEFECT`. |

Optional inputs: `vfx-spec.json`, `art-style-guide.json`,
`asset-registry.json`, `ui-registry.json`, existing sprite sheets, and caller
generation capabilities.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/art/vfx/sprites/sprite-vfx-spec.json` | yes | Sheet prompts, frame metadata, timing, validation rules. | vfx-generation, runtime import, QA. |
| `.allforai/game-design/art/vfx/sprites/sprite-vfx-manifest.json` | yes | Paths, frames, layer routing, states, previews. | vfx-generation, asset/ui registries. |
| `.allforai/game-design/art/vfx/sprites/sprite-vfx-report.json` | yes | Validation results, repair log, limits. | diagnostics and QA. |

Layer-routed image files are written under the correct VFX layer root.

## Invocation Contract

```json
{
  "skill": "game-art/sprite-vfx-generation",
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
1. Every sheet has frame count, FPS, frame size, loop behavior, alpha policy, and
   output path.
2. Paths route to the correct presentation layer and start with `file_prefix`.
3. Frame timing matches `vfx-spec.json`.
4. Non-looping sheets have a clear final/dissipate frame.
5. UI sheets include text/control occlusion limits.

Run visual validation when sheets/previews exist:
1. Frames are not cropped.
2. Motion reads in order at target FPS.
3. Alpha/background policy is respected.
4. Effect remains readable at gameplay/UI scale.
5. Style matches the art style guide.

Repair prompt/spec and regenerate up to 3 times; otherwise mark
`automation_limited` and emit a reduced frame-count fallback.

## Completion Conditions

Return `COMPLETED` only when specs, manifest, report, and available previews
validate. Return `COMPLETED_WITH_LIMITS` for spec-only or reduced-frame fallback.
