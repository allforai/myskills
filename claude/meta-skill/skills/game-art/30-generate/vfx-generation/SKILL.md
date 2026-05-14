---
name: game-art-30-generate-vfx-generation
description: Internal bundled meta-skill module for game-art/30-generate/vfx-generation; use within generated bootstrap node-specs when this exact contract is selected.
---

# VFX Generation Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill orchestrates VFX production artifacts from `vfx-spec.json`:
particle branches, sprite-sheet specs, trail specs, shader or screen-effect
placeholders, decals, mesh bursts, light pulses, animation-event bindings,
preview manifests, and QA reports. For production 2D game output, fallback VFX
may be recorded as a repair diagnosis but must not be accepted as final runtime
coverage.

The skill supports world, UI, and screen-space VFX across 2D and 3D. It chooses
the output branches from the VFX spec instead of splitting into separate
UI/world or 2D/3D skills. When a VFX uses particles, this skill delegates the
particle branch to `game-art/particle-system`.

## Scope

In scope:
- particle branch delegation and result integration,
- sprite-sheet prompt/spec generation,
- trail, decal, shader, mesh-burst, light-pulse, animation-event, and
  screen-effect specs,
- generated or registered preview assets,
- manifests for world/UI/screen-space outputs,
- deterministic and visual validation,
- automatic repair loops and reduced-motion fallbacks.

Out of scope:
- final engine-specific implementation code,
- audio generation,
- gameplay balance,
- manual VFX artist approval.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| `.allforai/game-design/art/vfx/vfx-spec.json` | VFX IDs, layer, dimension, implementation mode, timing, anchor, readability budget | Return `UPSTREAM_DEFECT`. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/game-design/asset-registry.json` | VFX asset prefixes and world asset refs | Use prefixes from VFX spec. |
| `.allforai/game-design/ui/ui-registry.json` | UI component/screen refs | Use VFX spec anchors. |
| `.allforai/game-design/art-style-guide.json` | palette, effects style, camera, dimension | Use VFX spec defaults. |
| `.allforai/game-design/ui/component-state-spec.json` | component feedback states | Use generic UI feedback. |
| Existing VFX files | registration and validation | Register existing files. |
| Caller context | image generation, preview rendering, vision validation availability | Produce specs/manifests only if unavailable. |

## Output Routing

Route outputs by presentation layer:

| Layer | Output root |
|---|---|
| `world` | `.allforai/game-design/art/vfx/world/` |
| `ui` | `.allforai/game-design/ui/vfx/` |
| `screen_space` | `.allforai/game-design/art/vfx/screen/` |

Route generated artifact types by implementation mode:

| Mode | Outputs |
|---|---|
| `particle` | delegate to `game-art/particle-system`, then integrate emitter JSON, optional texture/sprite, and preview spec. |
| `sprite_sheet` | prompt/spec, spritesheet image, frame metadata. |
| `trail` | trail JSON, optional strip texture, preview spec. |
| `shader` | shader parameter JSON or placeholder material spec. |
| `decal` | decal image/spec and projection metadata. |
| `screen_effect` | screen-effect JSON with accessibility fallback. |
| `mesh_burst` | mesh-burst spec and placeholder refs. |
| `light_pulse` | light pulse JSON. |
| `animation_event_fx` | animation-timeline event binding plus child VFX branch refs. |
| `hybrid` | combination manifest with synchronized child artifacts. |

## Generation Workflow

| Stage | Purpose | Main output |
|---|---|---|
| 1. Load VFX contract | Normalize layer, dimension, mode, timing, anchor. | `normalized_vfx[]` |
| 2. Build branch plan | Decide particle, sprite, trail, shader, decal, screen-effect, mesh-burst, light-pulse, and animation-event branches. | `branch_plan[]` |
| 3. Delegate/generate branches | Call the matching branch sub-skill when needed; generate/register branch outputs. | VFX files by layer. |
| 4. Build previews | Static frames, GIF specs, HTML preview, or preview map. | `previews[]` |
| 5. Write manifest | Paths, metadata, timing, engine-neutral config. | `vfx-manifest.json` |
| 6. Validate | Deterministic, visual, and layer-specific checks. | `vfx-generation-report.json` |
| 7. Repair | Update specs and regenerate up to capped attempts. | `repair_log[]` |
| 8. Accept | Approved, needs revision, or automation-limited. | `acceptance` |

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/art/vfx/vfx-generation-spec.json` | yes | Branch plan and generation specs for particles, sprites, trails, shaders, decals, screen effects, mesh bursts, light pulses, and animation-event FX. | VFX branch generators, runtime import, QA. |
| `.allforai/game-design/art/vfx/vfx-manifest.json` | yes | Canonical paths, layer routing, metadata, timing, states. | asset-registry, ui-registry, frontend/runtime, QA. |
| `.allforai/game-design/art/vfx/vfx-generation-report.json` | yes | Validation verdict, visual checks, repair attempts, limits. | diagnostics and QA. |
| `.allforai/game-design/art/vfx/world/**` | when generated | World VFX artifacts. | runtime import and QA. |
| `.allforai/game-design/ui/vfx/**` | when generated | UI VFX artifacts. | game-ui and frontend. |
| `.allforai/game-design/art/vfx/screen/**` | when generated | Screen-space VFX artifacts. | runtime import and accessibility QA. |

## Invocation Contract

```json
{
  "skill": "game-art/vfx-generation",
  "mode": "spec_generate_validate",
  "input_paths": {
    "vfx_spec": ".allforai/game-design/art/vfx/vfx-spec.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "ui_registry": ".allforai/game-design/ui/ui-registry.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "component_state": ".allforai/game-design/ui/component-state-spec.json",
    "particle_system": ".allforai/game-design/art/vfx/particles/particle-system-manifest.json"
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
| `spec_only` | Write generation specs and manifest placeholders. |
| `spec_generate_validate` | Generate/register artifacts, preview, validate, repair, and report. |
| `validate_existing` | Validate existing VFX artifacts and manifests. |
| `register_existing` | Register existing VFX files without regenerating. |

## Manifest Schema

```json
{
  "schema_version": "1.0",
  "vfx": [
    {
      "vfx_id": "fireball_impact",
      "file_prefix": "vfx_fireball_impact",
      "presentation_layer": "world",
      "dimension": "2d",
      "implementation_mode": "particle",
      "branch_outputs": [
        {
          "branch": "particle",
          "skill": "game-art/particle-system",
          "manifest_ref": ".allforai/game-design/art/vfx/particles/particle-system-manifest.json"
        }
      ],
      "anchor": {"kind": "projectile", "id": "fireball"},
      "timing": {"duration_ms": 450, "event_sync_ms": 80},
      "artifacts": [
        {
          "kind": "particle_config",
          "path": ".allforai/game-design/art/vfx/world/vfx_fireball_impact_particles.json"
        }
      ],
      "preview": {
        "path": ".allforai/game-design/art/vfx/world/previews/vfx_fireball_impact_preview.png",
        "status": "generated | not_generated | automation_limited"
      },
      "state": "generated | approved | needs_revision | automation_limited"
    }
  ]
}
```

## Automatic Validation

Run deterministic checks:
1. Every VFX in `vfx-spec.json` exists in the manifest.
2. Every artifact path is routed to the correct layer output root.
3. Every artifact path starts with the VFX `file_prefix`.
4. Implementation-specific required fields are present.
5. Timing and event sync match `vfx-spec.json`.
6. UI-layer VFX references registered UI components or screens when available.
7. Screen-space VFX includes reduced-motion fallback.
8. Particle VFX has a `particle-system` branch output or an explicit
  branch output; `automation_limited` is a production blocker unless the effect
  is explicitly optional or accessibility-only.
9. Mesh-burst VFX has a `mesh-burst-generation` branch output; fallback-only
   mesh bursts block production VFX completion.
10. Light-pulse VFX has a `light-pulse-generation` branch output; fallback-only
    light pulses block production VFX completion.
11. Animation-event FX has an `animation-event-fx` branch output; timing
    placeholders block production VFX completion.
12. No VFX is marked `approved` without validation.

Run visual validation when previews exist:
1. Effect is visible at gameplay/UI scale.
2. World VFX does not hide critical gameplay beyond the occlusion budget.
3. UI VFX does not hide text or primary controls.
4. Screen-space VFX does not overwhelm the full screen beyond duration/intensity
   caps.
5. Hit/impact/cast/reward timing appears aligned with the specified event.
6. Particle/sprite/trail/shader style matches the art style guide.
7. Similar effects remain distinguishable by color, silhouette, timing, or
   motion.

If validation fails, repair the spec and regenerate up to 3 times. Particle
branch failures should first be routed through `game-art/particle-system` repair.
If validation still fails, mark the affected VFX `automation_limited` and
preserve a simplified fallback only as diagnostic/repair evidence:
- simple particle burst from `particle-system` instead of complex shader,
- sprite flash instead of full animation,
- static decal instead of dynamic effect,
- reduced-motion screen effect instead of shake/flash.

## Completion Conditions

Return `COMPLETED` only when specs, manifest, report, generated or registered
runtime artifacts, previews, and import/visual QA pass.

Return `COMPLETED_WITH_LIMITS` only for planning/spec phases. For launch,
launch-prep, production, or unattended run goals, spec-only manifests,
`not_generated`, `automation_limited`, missing frame directories, placeholder
shader/materials, tween-only effects, and reduced fallback effects are blockers
that must route to the owning VFX branch generator.
