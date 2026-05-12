---
name: game-art-30-generate-screen-effect-generation
description: Internal bundled meta-skill module for game-art/30-generate/screen-effect-generation; use within generated bootstrap node-specs when this exact contract is selected.
---

# Screen Effect Generation Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill produces screen-space VFX specs for flash, shake, vignette,
radial burst, blur, low-health warning, reward burst, slow-motion cue, and
global damage feedback. It emphasizes accessibility and UI readability.

## Scope

In scope:
- screen-space effect parameter specs,
- intensity/duration/accessibility caps,
- reduced-motion and reduced-flash fallbacks,
- preview manifests,
- deterministic and visual validation,
- repair loops.

Out of scope:
- world particles,
- UI component layout,
- final engine implementation code,
- manual accessibility review.

## Input Contract

| Input | Required fields | Missing behavior |
|---|---|---|
| Screen-effect VFX request | `vfx_id`, `file_prefix`, `presentation_layer=screen_space`, `dimension=screen_space`, `lifecycle`, `screen_effect` | Return `UPSTREAM_DEFECT`. |

Optional inputs: `vfx-spec.json`, `ui-registry.json`,
`component-state-spec.json`, `art-style-guide.json`, existing screen-effect
configs, and preview capabilities.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/art/vfx/screen/screen-effect-spec.json` | yes | Screen-space effect parameters and fallbacks. | vfx-generation, runtime import, QA. |
| `.allforai/game-design/art/vfx/screen/screen-effect-manifest.json` | yes | Paths, parameters, previews, states. | vfx-generation, runtime import. |
| `.allforai/game-design/art/vfx/screen/screen-effect-report.json` | yes | Validation and repair results. | diagnostics and QA. |

## Invocation Contract

```json
{
  "skill": "game-art/screen-effect-generation",
  "mode": "spec_generate_validate",
  "input_paths": {
    "vfx_spec": ".allforai/game-design/art/vfx/vfx-spec.json",
    "ui_registry": ".allforai/game-design/ui/ui-registry.json",
    "component_state": ".allforai/game-design/ui/component-state-spec.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json"
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
1. Effect has duration, intensity cap, affected region, trigger, and fallback.
2. Flash/shake/blur effects define reduced-motion or reduced-flash alternative.
3. Duration stays inside the readability budget from `vfx-spec.json`.
4. UI readability limits are defined.
5. Parameters are bounded and serializable.

Run visual validation when previews exist:
1. Effect communicates the event.
2. UI remains readable.
3. Effect does not exceed intensity or duration caps.
4. Reduced fallback is meaningfully calmer.

Repair up to 3 times; otherwise downgrade to low-intensity flash, static tint,
or disabled screen effect.

## Completion Conditions

Return `COMPLETED` only when specs, manifest, report, and available previews
validate. Return `COMPLETED_WITH_LIMITS` for reduced or disabled fallback.
