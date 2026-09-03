---
name: game-art-10-design-2d-animation-production-plan
description: Choose per asset class between frame animation, motion-video-to-sprite, static pose swaps, UI tweening, VFX-only motion, or hybrid fallback for light-animation 2D games; writes art/animation/2d-animation-production-plan.json.
---

# 2D Animation Production Plan Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Chooses the animation production strategy for light-animation 2D indie games.
It decides when to use frame animation, motion video to sprite extraction,
static pose swaps, UI tweening, VFX-only motion, or hybrid fallback. Do not
select skeletal, DragonBones, Spine, part-tween, or 3D mesh animation.

Use this before detailed animation specs when the project has multiple asset
classes or when production cost, tool support, and runtime constraints matter.

## Input Contract

Required: game concept or art direction, target genres, asset list or gameplay
roles, target runtime, and expected animation complexity.

Optional: `asset-registry.json`, `motion-design.json`, `visual-style-tokens.json`,
`2d-view-mode-spec.json`, `2d-layering-spec.json`, engine constraints,
available tools, `.allforai/game-design/art/env/2d-animation-toolchain-report.json`,
image generation capabilities, and target platform performance budget.

## Output Contract

Writes:

- `.allforai/game-design/art/animation/2d-animation-production-plan.json`
- `.allforai/game-design/art/animation/2d-animation-production-plan-report.json`

Plan entries must include `asset_id`, `asset_role`, `animation_method`,
`required_animation_sets`, `source_art_strategy`, `downstream_skill_refs`,
`runtime_export_profile_ref`, `toolchain_report_ref`, `qa_requirements`,
`fallback_method`, `state`, and `consumer_refs`.

Allowed `animation_method` values:

- `frame_animation`
- `motion_video_to_sprite`
- `pose_swap`
- `ui_tween`
- `vfx_only`
- `hybrid`
- `static`

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_assets`,
`blocked_by_runtime`, `automation_limited`.

Downstream consumers: `motion-design`,
`frame-animation-spec`, `animation-state-machine-spec`,
`engine-export-profile`, `frame-animation-generation`,
`motion-video-to-sprite-animation`, `2d-layering-spec`, `animation-event-fx`, `art-preview-qa`,
`2d-style-consistency-qa`, `runtime-import-check`, and runtime implementation
nodes.

Plan entries must also carry a `decision_evidence` object:

```json
{
  "asset_id": "player",
  "view_mode_ref": "side_view",
  "layering_ref": "player_layering",
  "animation_method": "frame_animation",
  "method_reason": ["readable_loop", "identity_lock", "no_skeletal_production"],
  "complexity": "low | medium | high",
  "direction_count": 1,
  "required_animation_sets": ["idle", "run", "jump", "fall", "attack", "hit"],
  "fallback_method": "pose_swap",
  "fallback_trigger": "frame_or_preview_validation_failed",
  "toolchain_report_ref": ".allforai/game-design/art/env/2d-animation-toolchain-report.json",
  "max_generation_attempts": 3,
  "acceptance_gates": ["preview_readability", "runtime_import", "style_consistency"]
}
```

## Invocation Contract

```json
{
  "skill": "game-art/2d-animation-production-plan",
  "mode": "plan_validate",
  "input_paths": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "motion_design": ".allforai/game-design/systems/motion-design.json",
    "visual_style_tokens": ".allforai/game-design/art/visual-style-tokens.json"
  },
  "output_root": ".allforai/game-design/art/animation"
}
```

Supported modes: `plan_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every animated asset has one primary method, one fallback method,
stable downstream skill refs, and QA requirements. Player-facing characters
must include idle and locomotion strategy. Interactable props must include state
change or feedback strategy. UI motion must route to UI specs rather than
character animation specs.

For light 2D games, prefer the lowest-cost method that preserves readability:
static or pose-swap for minor NPCs, frame animation for characters and short
loops, motion-video-to-sprite for organic one-off actions, and VFX-only motion
for simple feedback assets.

Method selection rules:

| Condition | Prefer | Avoid unless required |
|---|---|---|
| Pixel art, exact silhouettes, short loops | `frame_animation` | video extraction |
| Short action needs organic motion but no large hand-authored set | `motion_video_to_sprite` | oversized unique frame sets |
| Many outfits/equipment swaps | extra `frame_animation` variants | layer-sheet rigs or part_tween |
| Small props with open/close/on/off | `pose_swap` | full animation sheets |
| UI affordance or button feedback | `ui_tween` | character animation pipeline |
| Impact, pickup, sparkle, warning | `vfx_only` | persistent rig assets |
| Boss or hero with many reusable actions | `frame_animation` or `hybrid` | one-off pose swaps |

State progression gates:

```text
draft
-> validated                 all required assets have method, fallback, consumer refs
-> needs_revision            method conflicts with view mode, layering, or runtime profile
-> blocked_by_assets         asset IDs, roles, or source art are missing
-> blocked_by_runtime        export/import support is unknown
-> automation_limited        method is valid but generation or preview tools are unavailable
```

Canonical remap, apply before planning and record every change:

```text
skeletal_animation | dragonbones | dragonbones_mesh | dragonbones_fx |
spine | skeletal_3d | 3d_skeletal | part_tween
  → animation_system = frame
  → character.rig = frame_sequence
  → animation_method = frame_animation

dimension = 3d → 2d
```

Do not keep the legacy value. The plan must not select `frame_animation`
without frame count, FPS, anchor, and direction requirements in downstream
refs. It must not select `motion_video_to_sprite` without source strategy,
provenance/license rules, target FPS, duration, looping policy, frame size,
anchor, visual acceptance route, and runtime export requirements.

The plan must require `game-art/00-env/2d-animation-toolchain-env` before any
downstream frame, video-to-sprite, pose-swap, UI-tween, or VFX-only
animation generation. If the toolchain report later returns
`blocked_by_missing_toolchain`, do not silently switch methods; only activate a
fallback method that was already declared in this plan.

Repair routing: missing asset IDs return to `asset-registry`; unclear motion
intent returns to `motion-design`; missing style constraints return to
`visual-style-tokens`; missing layer/swap/sorting rules return to
`2d-layering-spec`; unavailable export/runtime support returns to
`engine-export-profile`; generation failures route to the selected downstream
producer after this plan remains stable.

## Completion Conditions

Return `COMPLETED` when every relevant 2D asset has an animation method,
downstream skill route, QA route, export dependency, and explicit production
scope. Fallbacks are repair/scope notes, not production completion. Return
`COMPLETED_WITH_LIMITS` only when low-priority assets are intentionally static
and out of launch scope.
Return `UPSTREAM_DEFECT` when assets, runtime, or gameplay roles cannot be
resolved.
