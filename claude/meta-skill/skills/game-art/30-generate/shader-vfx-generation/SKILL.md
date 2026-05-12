---
name: game-art-30-generate-shader-vfx-generation
description: Internal bundled meta-skill module for game-art/30-generate/shader-vfx-generation; use within generated bootstrap node-specs when this exact contract is selected.
---

# Shader VFX Generation Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill produces engine-neutral shader/material VFX specs for dissolve,
glow, outline, distortion, shield ripple, hit flash, screen warp, and similar
parameter-driven effects. It creates parameter contracts and preview/fallback
specs, not final engine shader code.

## Scope

In scope:
- shader/material parameter specs,
- affected target and mask rules,
- timing/intensity curves,
- reduced fallback specs,
- validation and repair loops.

Out of scope:
- writing production GLSL/HLSL/ShaderGraph code,
- particle systems,
- sprite-sheet generation,
- manual technical artist tuning.

## Input Contract

| Input | Required fields | Missing behavior |
|---|---|---|
| Shader VFX request | `vfx_id`, `file_prefix`, `presentation_layer`, `dimension`, `anchor`, `lifecycle`, `shader` | Return `UPSTREAM_DEFECT`. |

Optional inputs: `vfx-spec.json`, `art-style-guide.json`, registries, existing
material specs, and preview capabilities.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/art/vfx/shaders/shader-vfx-spec.json` | yes | Shader/material parameter specs and fallbacks. | vfx-generation, runtime import, QA. |
| `.allforai/game-design/art/vfx/shaders/shader-vfx-manifest.json` | yes | Paths, parameters, previews, states. | vfx-generation, registries. |
| `.allforai/game-design/art/vfx/shaders/shader-vfx-report.json` | yes | Validation and repair results. | diagnostics and QA. |

## Invocation Contract

```json
{
  "skill": "game-art/shader-vfx-generation",
  "mode": "spec_generate_validate",
  "input_paths": {
    "vfx_spec": ".allforai/game-design/art/vfx/vfx-spec.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "ui_registry": ".allforai/game-design/ui/ui-registry.json"
  },
  "generation": {
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
1. Shader VFX has target, parameters, timing curve, intensity cap, and fallback.
2. Screen-space shaders include reduced-motion and reduced-intensity fallback.
3. UI shaders define text/control readability limits.
4. Paths route to the correct presentation layer and start with `file_prefix`.
5. Parameters are bounded and serializable.

Run visual validation when previews exist:
1. Effect is visible but not overpowering.
2. Target masking is clear.
3. UI text and controls remain readable.
4. Screen-space effects respect intensity/duration caps.

Repair parameters up to 3 times; otherwise downgrade to sprite flash, color
overlay, or no-op placeholder.

## Completion Conditions

Return `COMPLETED` only when specs, manifest, report, and available previews
validate. Return `COMPLETED_WITH_LIMITS` for placeholder or reduced fallback.
