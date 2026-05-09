# Light Pulse Generation Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill produces light-pulse VFX specs for 2.5D and 3D games: explosion
flashes, spell charge glow, hit flashes, warning lights, pickup glints, and
environment pulses. It is called by `vfx-generation` when `implementation_mode`
includes `light_pulse`.

## Scope

In scope:
- light type, color, intensity, radius, falloff,
- timing and curve specs,
- target/anchor binding,
- accessibility and photosensitivity caps,
- preview manifests,
- validation and repair loops.

Out of scope:
- final engine lighting implementation,
- full shader authoring,
- gameplay visibility balance,
- manual lighting polish.

## Input Contract

| Input | Required fields | Missing behavior |
|---|---|---|
| Light-pulse VFX request | `vfx_id`, `file_prefix`, `presentation_layer`, `dimension`, `anchor`, `lifecycle`, `light_pulse` | Return `UPSTREAM_DEFECT`. |

Optional inputs: `vfx-spec.json`, `art-style-guide.json`, registries, and preview
capabilities.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/art/vfx/lights/light-pulse-spec.json` | yes | Light parameters, curves, anchors, fallback rules. | vfx-generation, runtime import, QA. |
| `.allforai/game-design/art/vfx/lights/light-pulse-manifest.json` | yes | Paths, configs, previews, states. | vfx-generation and registries. |
| `.allforai/game-design/art/vfx/lights/light-pulse-report.json` | yes | Validation and repair results. | diagnostics and QA. |

## Invocation Contract

```json
{
  "skill": "game-art/light-pulse-generation",
  "mode": "spec_generate_validate",
  "input_paths": {
    "vfx_spec": ".allforai/game-design/art/vfx/vfx-spec.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "asset_registry": ".allforai/game-design/asset-registry.json"
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
1. Light pulse has type, color, intensity, radius, falloff, duration, curve, and
   anchor.
2. Intensity and frequency stay inside accessibility caps.
3. Paths route to `.allforai/game-design/art/vfx/lights/` and start with
   `file_prefix`.
4. Timing matches `vfx-spec.json`.
5. Reduced-intensity fallback exists.

Run visual validation when previews exist:
1. Pulse communicates the event.
2. It does not wash out UI or critical gameplay.
3. Color and intensity match the art style guide.
4. Fade-in/fade-out is smooth.

Repair up to 3 times; otherwise downgrade to low-intensity color flash or no-op
placeholder.

## Completion Conditions

Return `COMPLETED` only when specs, manifest, report, and available previews
validate. Return `COMPLETED_WITH_LIMITS` for reduced or placeholder output.
