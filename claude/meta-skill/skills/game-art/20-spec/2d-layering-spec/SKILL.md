# 2D Layering Spec Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the unified layer contract for 2D game art. It covers scene layers,
character outfit layers, skeletal part layers, frame-animation overlays, UI
layers, VFX layers, collision/helper layers, export draw order, and runtime
sorting metadata.

Use this after `2d-view-mode-spec` and before asset generation when a game needs
consistent parallax, occlusion, dress-up, equipment swaps, foreground masks,
draw order, or atlas grouping.

## Input Contract

Required: asset list or asset registry, 2D view mode, visual style tokens, and
target runtime/export context.

Optional: 2D animation production plan, character layer sheet plan, background
requirements, UI registry, VFX spec, level layout spec, engine export profile,
existing atlas manifests, and outfit/equipment requirements.

## Output Contract

Writes:

- `.allforai/game-design/art/layers/2d-layering-spec.json`
- `.allforai/game-design/art/layers/2d-layering-report.json`

The spec must include `layering_profile_id`, `view_mode_ref`,
`global_sorting_policy`, `scene_layers`, `character_layers`, `outfit_layers`,
`animation_overlay_layers`, `vfx_layers`, `ui_layers`, `collision_layers`,
`atlas_grouping_policy`, `runtime_export_policy`, `qa_requirements`, `state`,
and `consumer_refs`.

Layer entries must include `layer_id`, `scope`, `display_name`, `z_order`,
`sort_key`, `visibility_rule`, `animation_participation`,
`swap_participation`, `collision_participation`, `export_group`, `atlas_group`,
`masking_policy`, `parallax_factor`, `occlusion_policy`, `asset_refs`,
`fallback_layer`, and `validation`.

Allowed layer scopes:

- `scene_background`
- `scene_midground`
- `scene_playfield`
- `scene_foreground`
- `character_body`
- `character_outfit`
- `character_equipment`
- `character_expression`
- `animation_overlay`
- `vfx_world_back`
- `vfx_world_front`
- `vfx_screen`
- `ui_background`
- `ui_content`
- `ui_overlay`
- `collision_helper`
- `runtime_helper`

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_view_mode`, `blocked_by_asset_registry`,
`blocked_by_runtime_profile`.

Downstream consumers: `character-layer-sheet`, `background-generation`,
`prop-generation`, `frame-animation-generation`, `skeletal-animation`,
`expression-set-generation`, `vfx-generation`, `game-ui` specs,
`atlas-packaging`, `engine-export-profile`, `2d-style-consistency-qa`,
`runtime-import-check`, and runtime rendering/import nodes.

The spec must include both global ordering and per-scope templates:

```json
{
  "global_sorting_policy": {
    "coordinate_space": "screen | world | ui",
    "primary_key": "layer_z",
    "secondary_key": "sort_y",
    "stable_tie_breaker": "asset_id"
  },
  "scene_layers": [
    {"layer_id": "bg_far", "z_order": -300, "parallax_factor": 0.25},
    {"layer_id": "playfield", "z_order": 0, "collision_participation": "runtime"},
    {"layer_id": "fg_occluder", "z_order": 300, "occlusion_policy": "may_cover_actor"}
  ],
  "character_layers": [
    {"layer_id": "body", "z_order": 0, "swap_participation": "locked"},
    {"layer_id": "outfit_torso", "z_order": 20, "swap_participation": "swappable"},
    {"layer_id": "weapon_hand", "z_order": 50, "animation_participation": "rigged"}
  ]
}
```

## Invocation Contract

```json
{
  "skill": "game-art/2d-layering-spec",
  "mode": "spec_validate",
  "input_paths": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "view_mode": ".allforai/game-design/art/view/2d-view-mode-spec.json",
    "visual_style_tokens": ".allforai/game-design/art/visual-style-tokens.json",
    "engine_export_profile": ".allforai/game-design/art/export/engine-export-profile.json"
  },
  "output_root": ".allforai/game-design/art/layers"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every layer has a stable ID, scope, z-order or sort key, export
group, and validation rule. A layer must not be both collision-only and
rendered unless explicitly declared as a debug/runtime helper. Swappable outfit
or equipment layers must define compatible body anchors, occlusion, masks, and
fallback layers. Scene layers must define parallax and foreground/midground
interaction rules when the view mode uses scrolling or depth.

View-mode-specific requirements:

- `side_view`: define sky/far/mid/playfield/foreground layers, ground line,
  foreground occluders, parallax factors, and character/equipment draw order.
- `top_down` and `three_quarter_overhead`: define floor, wall/prop height,
  y-sort policy, overhang/occlusion layers, and character footprint layers.
- `isometric`: define tile height layers, diamond/staggered sorting, building
  occlusion, roof/inside visibility, and character/equipment draw order.
- `beat_em_up_2_5d`: define lane/depth sorting, scale-by-depth rules,
  foreground crowd/prop layers, and attack/VFX front-back layers.
- `fixed_room` and `visual_novel`: define background, character staging,
  expression/pose swap, foreground masks, and dialogue/UI overlay separation.
- `board_grid` and card/table modes: define board cells, pieces/cards,
  selection/target overlays, UI overlays, and VFX feedback layers.

Layer integrity rules:

- `layer_id` must be stable and file-safe.
- Rendered layers must have `z_order`; y-sorted layers must also have `sort_key`.
- Swappable layers must declare compatible anchor, mask, and fallback behavior.
- Character outfit layers must not change the body pivot contract.
- Scene foreground layers that can cover actors must name opacity or cutaway
  behavior.
- VFX layers must declare whether they render behind, on, or in front of the
  actor.
- UI layers must not share world sort keys.
- Atlas groups must not mix incompatible trimming, padding, or pivot policies.

State progression gates:

```text
draft
-> validated                    all required layer scopes have order, export, QA rules
-> needs_revision               layer conflicts, missing fallback, invalid atlas grouping
-> blocked_by_view_mode         projection/sorting rules are missing
-> blocked_by_asset_registry    layer assets cannot be resolved by asset_id
-> blocked_by_runtime_profile   runtime sorting/export policy is unknown
```

Repair routing: missing asset IDs return to `asset-registry`; missing spatial
rules return to `2d-view-mode-spec`; missing outfit/body decomposition returns
to `character-layer-sheet`; runtime sorting or atlas group failures route to
`engine-export-profile` or `atlas-packaging`; visual layer conflicts route to
`2d-style-consistency-qa` and then the relevant producer.

## Completion Conditions

Return `COMPLETED` when scene, character, outfit, VFX, UI, helper, export, and
QA layer rules are defined for the active view mode. Return
`COMPLETED_WITH_LIMITS` when static or menu-only projects need only UI and
background layers. Return `FAILED_VALIDATION` when layer order or swap rules are
ambiguous enough to block generation or runtime import.
