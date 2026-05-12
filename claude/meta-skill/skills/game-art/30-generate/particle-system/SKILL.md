---
name: game-art-30-generate-particle-system
description: Internal bundled meta-skill module for game-art/30-generate/particle-system; use within generated bootstrap node-specs when this exact contract is selected.
---

# Particle System Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill produces reusable particle-system artifacts for game VFX. It
accepts particle requirements from `vfx-spec.json` or `vfx-generation`, then
creates engine-neutral emitter specs, optional particle textures, preview
manifests, validation reports, and repair decisions.

Particle is an implementation branch of VFX. This skill does not decide whether
an effect should exist or what gameplay meaning it carries. It only turns a
particle requirement into a usable particle asset.

## Scope

Use this skill when a VFX requires:
- burst particles,
- continuous emitters,
- smoke, sparks, dust, embers, rain, snow, magic motes, debris, coins, stars,
- UI celebratory particles,
- 2D or 3D particle configs,
- screen-space particle overlays.

Out of scope:
- choosing VFX semantics,
- non-particle sprite-sheet animation,
- shader-only effects,
- trails that do not emit particles,
- final engine-specific implementation code,
- human tuning or manual approval.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| Particle request from `vfx-spec.json` or caller | `vfx_id`, `file_prefix`, `presentation_layer`, `dimension`, `anchor`, `lifecycle`, `particle` | Return `UPSTREAM_DEFECT`; no particle requirement exists. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/game-design/art/vfx/vfx-spec.json` | particle blocks, timing, readability budget | Use caller particle request. |
| `.allforai/game-design/art-style-guide.json` | palette, glow, texture style, camera | Use neutral readable particles. |
| `.allforai/game-design/asset-registry.json` | file prefixes and world references | Use caller file prefix. |
| `.allforai/game-design/ui/ui-registry.json` | UI anchors and component refs | Use caller anchor. |
| Existing particle textures/configs | registration and validation | Generate missing specs only. |
| Caller context | image generation, preview renderer, vision validator | Produce spec-only fallback if unavailable. |

### Normalized input

```json
{
  "schema_version": "1.0",
  "particles": [
    {
      "vfx_id": "fireball_impact",
      "particle_id": "fireball_impact_sparks",
      "file_prefix": "vfx_fireball_impact",
      "presentation_layer": "world | ui | screen_space",
      "dimension": "2d | 3d | screen_space",
      "anchor": {"kind": "projectile", "id": "fireball"},
      "lifecycle": {"duration_ms": 450, "event_sync_ms": 80, "loop": false},
      "emitter": {
        "shape": "point | cone | circle | box | sphere | line",
        "spawn_behavior": "burst | continuous | pulse",
        "spawn_count": 24,
        "spawn_rate": 0,
        "lifetime_ms": 320,
        "velocity": "outward_burst",
        "gravity": 0.2,
        "drag": 0.1,
        "color_over_life": ["yellow", "orange", "red", "transparent"],
        "size_over_life": "fast_expand_then_fade",
        "blend_mode": "alpha | additive | multiply | screen"
      }
    }
  ]
}
```

## Particle Modes

| Mode | Use for | Required behavior |
|---|---|---|
| `burst` | impacts, rewards, explosions, coin pop | Finite count, short lifetime, event sync. |
| `continuous` | fire, aura, rain, smoke, magic field | Spawn rate, loop stop condition, performance cap. |
| `pulse` | warning zones, UI highlight, charging spell | Period, phase, visibility budget. |

## Image Generation Upstream Contract

When particle textures are generated, each bitmap request must follow
`game-art/30-generate/image-generation-contract/SKILL.md`.

Use normalized image requests with `purpose=particle_texture` and
`generation_profile.task_type=particle_texture`. The request must use
`prompt_template=particle_texture_prompt` and a model profile that supports
simple transparent sprite output. It must include particle role, layer, blend
mode, texture shape, alpha policy, style, output path, positive prompt, negative
prompt, scale readability checks, blend suitability checks, and
`downstream_feedback.enabled=true`.

If particle preview, VFX generation, runtime import, or visual QA reports
`BAD_ALPHA`, `LOW_READABILITY`, `STYLE_DRIFT`, `CROPPED_SUBJECT`, or
`WRONG_SCALE` for a particle texture, process the defect through
`image-generation-contract` and regenerate when root cause is `image_generation`
or `prompt_contract`.

## Layer Rules

| Presentation layer | Output root | QA focus |
|---|---|---|
| `world` | `.allforai/game-design/art/vfx/world/particles/` | Event alignment, scale, occlusion, gameplay readability. |
| `ui` | `.allforai/game-design/ui/vfx/particles/` | Text/control readability, attention budget, component anchoring. |
| `screen_space` | `.allforai/game-design/art/vfx/screen/particles/` | Accessibility, intensity, duration, reduced motion. |

## Production Workflow

| Stage | Purpose | Main output |
|---|---|---|
| 1. Normalize request | Resolve layer, dimension, timing, emitter fields. | `normalized_particles[]` |
| 2. Build emitter spec | Engine-neutral particle config. | `particle-system-spec.json` |
| 3. Build texture spec | Optional particle sprite prompt/spec. | `particle-texture-spec[]` |
| 4. Generate/register assets | Configs, textures, preview metadata. | particle files by layer. |
| 5. Render or specify preview | GIF/HTML/static preview or preview spec. | `particle-preview-manifest.json` |
| 6. Validate | Deterministic and visual checks. | `particle-system-report.json` |
| 7. Repair | Adjust emitter/texture and retry up to cap. | `repair_log[]` |
| 8. Accept | Approved, needs revision, or automation-limited. | `acceptance` |

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/art/vfx/particles/particle-system-spec.json` | yes | Canonical particle emitter specs and texture specs. | vfx-generation, runtime import, QA. |
| `.allforai/game-design/art/vfx/particles/particle-system-manifest.json` | yes | Paths, configs, textures, previews, states. | vfx-generation, asset-registry, ui-registry. |
| `.allforai/game-design/art/vfx/particles/particle-system-report.json` | yes | Validation, repair attempts, limits. | diagnostics and QA. |
| Layer-routed particle config files | when generated | Engine-neutral particle config JSON. | runtime import and previews. |
| Layer-routed particle textures | when generated | Particle sprites/textures. | particle configs and previews. |

## Invocation Contract

```json
{
  "skill": "game-art/particle-system",
  "mode": "spec_generate_validate",
  "input_paths": {
    "vfx_spec": ".allforai/game-design/art/vfx/vfx-spec.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "ui_registry": ".allforai/game-design/ui/ui-registry.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json"
  },
  "particle_filter": {
    "vfx_ids": [],
    "particle_ids": [],
    "presentation_layers": []
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

Supported modes:

| Mode | Behavior |
|---|---|
| `spec_only` | Write emitter specs, texture specs, and manifest placeholders. |
| `spec_generate_validate` | Generate/register configs/textures, preview, validate, repair, report. |
| `validate_existing` | Validate existing particle configs/textures/previews. |
| `register_existing` | Register existing particle files without regenerating. |

## Manifest Schema

```json
{
  "schema_version": "1.0",
  "particles": [
    {
      "vfx_id": "fireball_impact",
      "particle_id": "fireball_impact_sparks",
      "file_prefix": "vfx_fireball_impact",
      "presentation_layer": "world",
      "dimension": "2d",
      "config_path": ".allforai/game-design/art/vfx/world/particles/vfx_fireball_impact_sparks.json",
      "texture_path": ".allforai/game-design/art/vfx/world/particles/vfx_fireball_impact_spark.png",
      "preview_path": ".allforai/game-design/art/vfx/world/particles/previews/vfx_fireball_impact_sparks.png",
      "state": "generated | approved | needs_revision | automation_limited"
    }
  ]
}
```

## Automatic Validation

Run deterministic checks:
1. Every particle has `vfx_id`, `particle_id`, `file_prefix`, layer, dimension,
   anchor, lifecycle, and emitter.
2. Every particle path is routed to the correct layer output root.
3. Every generated path starts with `file_prefix`.
4. Burst emitters have finite count and lifetime.
5. Continuous emitters have spawn rate, stop condition, and performance cap.
6. Color and size over life are defined.
7. Blend mode is valid for the layer.
8. Screen-space particles include reduced-motion fallback.
9. UI particles define max attention duration and do not cover primary controls.
10. World particles define max occlusion and event sync when tied to impacts.

Run visual validation when previews exist:
1. Particles are visible at gameplay/UI scale.
2. Burst timing matches the specified event.
3. Continuous particles loop without obvious popping.
4. UI particles do not obscure text or controls.
5. Screen-space particles do not exceed intensity/duration caps.
6. Particle texture style matches the art style guide.
7. Similar particle effects remain distinguishable.

If validation fails, repair emitter values or texture specs and retry up to 3
times. If still failing, mark `automation_limited` and emit a simplified
fallback such as static sparkle, reduced burst count, or no-texture particles.

## Completion Conditions

Return `COMPLETED` only when particle specs, manifest, report, and available
previews validate.

Return `COMPLETED_WITH_LIMITS` when only specs/manifests can be produced, or
when complex particle behavior is reduced to an automated fallback.
