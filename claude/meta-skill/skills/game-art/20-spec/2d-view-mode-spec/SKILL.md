---
name: game-art-20-spec-2d-view-mode-spec
description: Internal bundled meta-skill module for game-art/20-spec/2d-view-mode-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# 2D View Mode Spec Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the 2D game's spatial view mode before asset, animation, level, UI, and
runtime export decisions are made. It classifies whether the game uses side
view, top-down, 3/4 overhead, isometric, beat-em-up 2.5D lane depth, fixed
room, board/grid, visual-novel staging, vertical/horizontal scrolling shooter,
or hybrid presentation.

Use this skill when a project needs consistent rules for camera angle, character
directions, tile projection, background layering, collision, sorting, animation
facings, UI safe regions, and export/import metadata.

## Input Contract

Required: gameplay concept, movement model, camera behavior, level structure, or
genre signal.

Optional: level registry, level flow, tileset spec, animation production plan,
visual style tokens, UI layout constraints, engine export profile, and target
runtime.

## Output Contract

Writes:

- `.allforai/game-design/art/view/2d-view-mode-spec.json`
- `.allforai/game-design/art/view/2d-view-mode-report.json`

The spec must include `view_mode_id`, `primary_view_mode`,
`secondary_view_modes`, `camera_model`, `movement_axes`, `depth_model`,
`sorting_policy`, `tile_projection`, `character_facing_policy`,
`background_layer_policy`, `collision_policy`, `ui_safe_regions`,
`animation_requirements`, `level_requirements`, `export_requirements`,
`fallback_policy`, `state`, and `consumer_refs`.

Allowed `primary_view_mode` values:

- `side_view`
- `top_down`
- `three_quarter_overhead`
- `isometric`
- `beat_em_up_2_5d`
- `fixed_room`
- `board_grid`
- `visual_novel`
- `vertical_shooter`
- `horizontal_shooter`
- `menu_or_card_table`
- `hybrid`

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_gameplay`, `blocked_by_level_structure`, `blocked_by_runtime`.

Downstream consumers: `2d-animation-production-plan`, `motion-design`,
`2d-layering-spec`, `frame-animation-spec`, `character-layer-sheet`, `tileset-spec`,
`background-generation`, `prop-generation`, `level-layout-spec`,
`screen-layout-spec`, `engine-export-profile`, `2d-style-consistency-qa`, and
runtime implementation nodes.

The spec must include a normalized `view_rules` object:

```json
{
  "primary_view_mode": "side_view",
  "camera_model": {"scroll_x": true, "scroll_y": false, "zoom_policy": "fixed"},
  "movement_axes": ["x", "y_gravity"],
  "depth_model": "none | y_sort | lane_depth | isometric_height | screen_stack",
  "character_facing_policy": {"directions": ["right"], "mirror_x": true},
  "tile_projection": {"kind": "orthogonal_side", "cell_size": [32, 32]},
  "sorting_policy": {"primary_key": "layer_z", "secondary_key": "y"},
  "ui_safe_regions": ["top_hud", "bottom_touch_controls"],
  "evidence": ["platformer movement", "scrolling side camera"]
}
```

## Invocation Contract

```json
{
  "skill": "game-art/2d-view-mode-spec",
  "mode": "spec_validate",
  "input_paths": {
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "level_flow": ".allforai/game-design/levels/level-flow-design.json",
    "visual_style_tokens": ".allforai/game-design/art/visual-style-tokens.json"
  },
  "output_root": ".allforai/game-design/art/view"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that the selected view mode is compatible with movement, camera, level,
collision, and art production:

- `side_view` must define gravity/platform assumptions, side-facing animation
  directions, ground line, parallax/background layers, and jump/fall readability.
- `top_down` must define 4-way or 8-way facing, floor/wall distinction,
  collision footprint, and object occlusion rules.
- `three_quarter_overhead` must define partial vertical faces, 4/8-way facing,
  walkable ground projection, and prop height sorting.
- `isometric` must define diamond/staggered grid, projection angle, height
  layers, tile footprint, and y-depth sorting.
- `beat_em_up_2_5d` must define horizontal progress, depth lanes, scale/sort
  rules, ground perspective, and attack range readability.
- `fixed_room` must define room camera bounds, interactable highlight policy,
  foreground/background separation, and click/touch targets.
- `board_grid` must define cell shape, occupancy, selection state, legal move
  preview, and board UI integration.
- `visual_novel` must define background format, character staging, portrait or
  bust layout, expression swap rules, and dialogue UI safe area.
- shooter modes must define scroll axis, enemy/bullet readability, background
  motion, and screen-space danger regions.

Every view mode must define character facing requirements, tile/background
requirements, UI safe regions, and export requirements. Hybrid games must name
which screens or modes use each view mode and which contracts consume them.

Selection heuristics:

| Signal | View mode |
|---|---|
| jump, gravity, platforms, ladders, side scrolling | `side_view` |
| free 2D movement, dungeon rooms, twin-stick, overhead map | `top_down` |
| visible wall faces, RPG rooms, semi-overhead characters | `three_quarter_overhead` |
| diamond tiles, building height, tactics/sim/management | `isometric` |
| brawler lanes, horizontal progress, depth walk bands | `beat_em_up_2_5d` |
| single-room scenes, point-and-click, escape room | `fixed_room` |
| cells, pieces, cards, legal moves, match/tactics board | `board_grid` |
| dialogue backgrounds, busts, expression swaps | `visual_novel` |
| vertical scroll, bullets, enemies from top | `vertical_shooter` |
| horizontal scroll, bullets, enemies from side | `horizontal_shooter` |

State progression gates:

```text
draft
-> validated                    primary mode, camera, axes, sorting, UI regions defined
-> needs_revision               mode conflicts with movement, level, or art needs
-> blocked_by_gameplay          no movement/action model exists
-> blocked_by_level_structure   camera/level topology cannot be inferred
-> blocked_by_runtime           runtime cannot support required sorting/projection
```

Repair routing: unclear movement/camera semantics return to core loop or level
flow; conflicting view modes repair here; layer, occlusion, parallax, dress-up,
or draw-order defects route to `2d-layering-spec`; tile projection defects route
to `tileset-spec`; animation facing defects route to
`2d-animation-production-plan` or `frame-animation-spec`; UI overlap defects
route to `screen-layout-spec`; runtime coordinate/sorting defects route to
`engine-export-profile`.

## Completion Conditions

Return `COMPLETED` when the project has a validated primary view mode,
compatible camera/movement/sorting rules, downstream consumers, and fallback
policy. Return `COMPLETED_WITH_LIMITS` for menu-only or visual-novel projects
with no tile/locomotion requirements. Return `UPSTREAM_DEFECT` when gameplay or
level structure is too ambiguous to choose a view mode.
