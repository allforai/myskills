---
name: game-art-10-design-2d-animation-production-plan
description: Internal bundled meta-skill module for game-art/10-design/2d-animation-production-plan; use within generated bootstrap node-specs when this exact contract is selected.
---

# 2D Animation Production Plan Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Chooses the animation production strategy for light-animation 2D indie games.
It decides when to use frame animation, skeletal animation, separated-part
tweening, static pose swaps, UI tweening, VFX-only motion, or hybrid fallback.

Use this before detailed animation specs when the project has multiple asset
classes or when production cost, tool support, and runtime constraints matter.

## Input Contract

Required: game concept or art direction, target genres, asset list or gameplay
roles, target runtime, and expected animation complexity.

Optional: `asset-registry.json`, `motion-design.json`, `visual-style-tokens.json`,
`2d-view-mode-spec.json`, `2d-layering-spec.json`, engine constraints,
available tools, image generation capabilities, and target platform performance
budget.

## Output Contract

Writes:

- `.allforai/game-design/art/animation/2d-animation-production-plan.json`
- `.allforai/game-design/art/animation/2d-animation-production-plan-report.json`

Plan entries must include `asset_id`, `asset_role`, `animation_method`,
`required_animation_sets`, `source_art_strategy`, `downstream_skill_refs`,
`runtime_export_profile_ref`, `qa_requirements`, `fallback_method`, `state`,
and `consumer_refs`.

Allowed `animation_method` values:

- `frame_animation`
- `skeletal_animation`
- `part_tween`
- `pose_swap`
- `ui_tween`
- `vfx_only`
- `hybrid`
- `static`

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_assets`,
`blocked_by_runtime`, `automation_limited`.

Downstream consumers: `motion-design`, `character-layer-sheet`,
`frame-animation-spec`, `animation-state-machine-spec`,
`engine-export-profile`, `skeletal-animation`, `frame-animation-generation`,
`2d-layering-spec`, `animation-event-fx`, `art-preview-qa`,
`2d-style-consistency-qa`, `runtime-import-check`, and runtime implementation
nodes.

Plan entries must also carry a `decision_evidence` object:

```json
{
  "asset_id": "player",
  "view_mode_ref": "side_view",
  "layering_ref": "player_layering",
  "animation_method": "skeletal_animation",
  "method_reason": ["many_reused_actions", "outfit_swaps", "low_frame_budget"],
  "complexity": "low | medium | high",
  "direction_count": 1,
  "required_animation_sets": ["idle", "run", "jump", "fall", "attack", "hit"],
  "fallback_method": "part_tween",
  "fallback_trigger": "rig_or_preview_validation_failed",
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
static or pose-swap for minor NPCs, frame animation for small pixel/hand-drawn
loops, skeletal or part-tween animation for reusable characters, and VFX-only
motion for simple feedback assets.

Method selection rules:

| Condition | Prefer | Avoid unless required |
|---|---|---|
| Pixel art, exact silhouettes, short loops | `frame_animation` | `skeletal_animation` |
| Many outfits/equipment swaps | `skeletal_animation` or `part_tween` | full redraw frame sets |
| Small props with open/close/on/off | `pose_swap` | full animation sheets |
| UI affordance or button feedback | `ui_tween` | character animation pipeline |
| Impact, pickup, sparkle, warning | `vfx_only` | persistent rig assets |
| Boss or hero with many reusable actions | `skeletal_animation` or `hybrid` | one-off pose swaps |

State progression gates:

```text
draft
-> validated                 all required assets have method, fallback, consumer refs
-> needs_revision            method conflicts with view mode, layering, or runtime profile
-> blocked_by_assets         asset IDs, roles, or source art are missing
-> blocked_by_runtime        export/import support is unknown
-> automation_limited        method is valid but generation or preview tools are unavailable
```

The plan must not select `skeletal_animation` without either a layer contract or
a declared fallback to `part_tween`, `pose_swap`, or `frame_animation`. It must
not select `frame_animation` without frame count, FPS, anchor, and direction
requirements in downstream refs.

Repair routing: missing asset IDs return to `asset-registry`; unclear motion
intent returns to `motion-design`; missing style constraints return to
`visual-style-tokens`; missing layer/swap/sorting rules return to
`2d-layering-spec`; unavailable export/runtime support returns to
`engine-export-profile`; generation failures route to the selected downstream
producer after this plan remains stable.

## Completion Conditions

Return `COMPLETED` when every relevant 2D asset has an animation method,
fallback, downstream skill route, QA route, and export dependency. Return
`COMPLETED_WITH_LIMITS` when low-priority assets are intentionally static.
Return `UPSTREAM_DEFECT` when assets, runtime, or gameplay roles cannot be
resolved.
