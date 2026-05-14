---
name: game-art-20-spec-vfx-spec
description: Internal bundled meta-skill module for game-art/20-spec/vfx-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# VFX Spec Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill defines visual effects before generation. It turns gameplay
events, UI events, and screen feedback needs into a machine-readable VFX
contract with semantics, timing, presentation layer, dimension, implementation
mode, anchors, readability budgets, accessibility limits, and automatic
acceptance rules.

Particle effects are one implementation mode inside VFX. Do not create a
separate particle-only contract unless a downstream generator explicitly needs a
particle-only export.

## Scope

Use this skill when a game needs:
- impact, hit, cast, heal, spawn, death, explosion, status, telegraph, reward, or
  warning effects,
- UI button/card/reward/purchase effects,
- full-screen feedback such as flash, shake, vignette, slow-motion cue, or radial
  burst,
- particle, sprite-sheet, trail, shader, decal, screen effect, mesh burst,
  light-pulse, or animation-event effects.

Out of scope:
- final rendered VFX images or engine configs,
- audio-only feedback,
- character skeletal animation,
- UI layout,
- manual artist or technical artist approval.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| Gameplay/UI event context | event name, trigger condition, feedback purpose | Infer common event types once from game design; if no event exists, return `UPSTREAM_DEFECT`. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/game-design/asset-registry.json` | VFX asset IDs, file prefixes, world anchors | Derive `vfx_{event}` prefixes. |
| `.allforai/game-design/ui/ui-registry.json` | UI component/screen anchors | Use generic UI anchors. |
| `.allforai/game-design/art-style-guide.json` | palette, render style, dimension, camera | Use readable neutral VFX defaults. |
| `.allforai/game-design/game-design-doc.json` | combat, rewards, economy, progression, fail states | Infer VFX inventory from events. |
| `.allforai/concept-contract.json` | visual promise and canonical naming | Use derived naming. |
| `.allforai/game-design/ui/component-state-spec.json` | UI component states and feedback needs | Use generic button/reward feedback. |

### Normalized input

```json
{
  "schema_version": "1.0",
  "vfx": [
    {
      "vfx_id": "fireball_impact",
      "file_prefix": "vfx_fireball_impact",
      "semantic": "fire damage impact",
      "trigger": {
        "event": "projectile_hit",
        "source": "combat"
      },
      "presentation_layer": "world | ui | screen_space",
      "dimension": "2d | 3d | screen_space",
      "implementation_mode": "particle | sprite_sheet | shader | trail | decal | screen_effect | mesh_burst | light_pulse | animation_event_fx | hybrid",
      "anchor": {
        "kind": "actor | projectile | tile | world_position | ui_component | screen_region | camera",
        "id": "enemy"
      }
    }
  ]
}
```

## Layer Model

| Presentation layer | Use for | Primary QA concern |
|---|---|---|
| `world` | combat, movement, projectiles, environment impacts, tile hazards | Event alignment, scale, occlusion, gameplay readability. |
| `ui` | buttons, cards, rewards, currency, level-up panels, shop feedback | Text readability, component state consistency, attention budget. |
| `screen_space` | flash, shake, vignette, global warning, radial burst | Accessibility, duration, intensity, UI legibility. |

Layer rules:
- `world` VFX should register through `asset-registry.json`.
- `ui` VFX should register through `ui-registry.json` and may reference
  `asset-registry.json`.
- `screen_space` VFX should register as runtime effect metadata and must include
  accessibility limits.

## Dimension and Implementation Modes

| Dimension | Valid implementation modes |
|---|---|
| `2d` | `particle`, `sprite_sheet`, `shader`, `trail`, `decal`, `screen_effect`, `animation_event_fx`, `hybrid` |
| `3d` | `particle`, `shader`, `trail`, `decal`, `mesh_burst`, `light_pulse`, `screen_effect`, `animation_event_fx`, `hybrid` |
| `screen_space` | `screen_effect`, `shader`, `particle`, `light_pulse`, `hybrid` |

Particle mode must define:
- emitter shape,
- spawn behavior,
- lifetime,
- velocity,
- color over life,
- size over life,
- blend mode,
- gravity or drag when relevant.

Sprite-sheet mode must define:
- frame count,
- FPS,
- frame size,
- loop behavior,
- alpha/background policy.

Trail mode must define:
- anchor,
- width over life,
- color over life,
- duration,
- fade rule.

Shader/screen-effect mode must define:
- parameters,
- duration,
- intensity cap,
- affected region,
- accessibility fallback.

Mesh-burst mode must define:
- shard count,
- shape vocabulary,
- velocity/spread,
- lifetime,
- material reference,
- non-3D fallback.

Light-pulse mode must define:
- light type,
- color,
- intensity/radius/falloff,
- timing curve,
- reduced-intensity fallback.

Animation-event FX mode must define:
- source animation id,
- event name,
- event time or normalized frame,
- child implementation branch,
- fallback when animation timing is unavailable.

## Spec Workflow

| Stage | Purpose | Main output |
|---|---|---|
| 1. Build event inventory | Resolve gameplay, UI, and screen feedback events. | `event_inventory[]` |
| 2. Assign semantics | Define what each VFX communicates. | `semantic_contract[]` |
| 3. Select layer | `world`, `ui`, or `screen_space`. | `presentation_layer` |
| 4. Select dimension | `2d`, `3d`, or `screen_space`. | `dimension` |
| 5. Select implementation | Particle, sprite sheet, trail, shader, decal, mesh burst, light pulse, animation event, screen effect, or hybrid. | `implementation_mode` |
| 6. Define timing | Start, loop, impact, dissipate, event sync. | `lifecycle` |
| 7. Define readability budgets | Occlusion, attention, intensity, duration. | `readability_budget` |
| 8. Define acceptance | Automatic validation criteria and fallbacks. | `acceptance_rules` |

## Timing Model

Every VFX must define:
- `start_ms`,
- `duration_ms`,
- `lifecycle`: `start`, `loop`, `impact`, `dissipate`,
- `event_sync`: event frame or timestamp that must align with gameplay/UI event,
- `loop`: true/false,
- `interrupt_policy`.

Rules:
- Damage/impact VFX must align with the hit event.
- Telegraph VFX must appear before the dangerous event.
- UI feedback VFX should usually complete within 120-700 ms.
- Screen-space flash/shake must be short and capped.
- Looping VFX must define stop conditions.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/art/vfx/vfx-spec.json` | yes | VFX event contracts, layer/dimension/mode selection, timing, anchors, acceptance. | vfx-generation, game-ui, runtime import, QA. |
| `.allforai/game-design/art/vfx/vfx-spec-report.json` | yes | Validation, inferred defaults, missing events, fallback decisions. | Diagnostics and QA. |

## Invocation Contract

```json
{
  "skill": "game-art/vfx-spec",
  "mode": "spec_validate",
  "input_paths": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "ui_registry": ".allforai/game-design/ui/ui-registry.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "concept_contract": ".allforai/concept-contract.json",
    "component_state": ".allforai/game-design/ui/component-state-spec.json"
  },
  "vfx_filter": {
    "event_ids": [],
    "presentation_layers": [],
    "implementation_modes": []
  },
  "output_root": ".allforai/game-design"
}
```

Supported modes:

| Mode | Behavior |
|---|---|
| `spec_validate` | Create VFX spec and validate it. |
| `validate_existing` | Validate an existing VFX spec. |
| `repair_existing` | Repair missing timing, anchors, modes, or acceptance rules. |

## Schema

```json
{
  "schema_version": "1.0",
  "vfx": [
    {
      "vfx_id": "fireball_impact",
      "file_prefix": "vfx_fireball_impact",
      "semantic": "fire damage impact",
      "presentation_layer": "world",
      "dimension": "2d",
      "implementation_mode": "particle",
      "anchor": {"kind": "projectile", "id": "fireball"},
      "lifecycle": {
        "start_ms": 0,
        "duration_ms": 450,
        "phases": ["impact", "dissipate"],
        "event_sync": {"event": "damage_applied", "time_ms": 80},
        "loop": false
      },
      "particle": {
        "emitter_shape": "point",
        "spawn_behavior": "burst",
        "lifetime_ms": 320,
        "velocity": "outward_burst",
        "color_over_life": ["yellow", "orange", "red", "transparent"],
        "size_over_life": "fast_expand_then_fade",
        "blend_mode": "additive"
      },
      "readability_budget": {
        "max_occlusion_percent": 18,
        "max_duration_ms": 700,
        "attention": "critical | active | ambient",
        "accessibility_fallback": "reduced_motion"
      }
    }
  ]
}
```

## Automatic Validation

Run these checks:
1. Every VFX has `vfx_id`, `file_prefix`, semantic, trigger, layer, dimension,
   implementation mode, anchor, lifecycle, and readability budget.
2. Layer and anchor are compatible.
3. Dimension and implementation mode are compatible.
4. Particle mode includes emitter, lifetime, velocity, color, size, and blend.
5. Sprite-sheet mode includes frame count, FPS, frame size, and loop behavior.
6. Screen-space effects include duration/intensity caps and reduced-motion
   fallback.
7. World hit/impact effects sync with gameplay events.
8. UI effects reference registered components or screens when available.
9. Looping effects define stop conditions.
10. File prefixes are stable and do not collide.

Layer-specific checks:
- `world`: max occlusion and event alignment are defined.
- `ui`: text readability and component-state compatibility are defined.
- `screen_space`: accessibility fallback and intensity cap are defined.

## Completion Conditions

Return `COMPLETED` only when `vfx-spec.json` and `vfx-spec-report.json` validate
and every selected VFX has layer, dimension, implementation, timing, anchor, and
acceptance rules.

Return `COMPLETED_WITH_LIMITS` only for planning/spec phases when complex
effects are intentionally reduced and out of launch scope. For launch,
launch-prep, production, or unattended run goals, placeholder VFX specs or
reduced required effects are blockers unless routed to a concrete generation
branch and validated. Return `UPSTREAM_DEFECT` when required event context is
missing and cannot be inferred.
