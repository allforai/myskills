---
name: game-art-20-spec-tileset-spec
description: Internal bundled meta-skill module for game-art/20-spec/tileset-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Tileset Spec Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill defines the contract for tilemap-based game art. It selects the
tilemap mode, terrain vocabulary, tile sizes, connectivity rules, collision and
walkability metadata, atlas layout requirements, and preview-map acceptance
rules before any tile images are generated.

The skill is not a generic background generator. It exists for games whose maps,
levels, boards, or buildable spaces are assembled from repeatable cells.

## Scope

Use this skill when a game needs:
- platformer blocks,
- top-down RPG terrain,
- tactics or strategy grids,
- roguelike dungeon rooms and corridors,
- simulation/building floors and roads,
- tower-defense paths and build zones,
- puzzle grid cells,
- isometric terrain.

Out of scope:
- full painted background scenes,
- 3D terrain meshes,
- UI board tokens that are not map terrain,
- one-off decorative props,
- final generated tile images.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| Gameplay context | map/level/board structure, camera/view, player movement model | Infer mode once from genre keywords; if no grid/tile/map signal exists, return `NOT_APPLICABLE`. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/game-design/asset-registry.json` | tile assets, file prefixes, paths | Derive `tile_{asset_id}` prefixes. |
| `.allforai/game-design/art-asset-inventory.json` | terrain and map asset list | Create minimal terrain vocabulary from mode. |
| `.allforai/game-design/art-style-guide.json` | dimension, projection, style, palette | Use readable 2D orthographic defaults. |
| `.allforai/game-design/game-design-doc.json` | genre, movement, collision, level structure | Infer tilemap mode and collision model. |
| `.allforai/concept-contract.json` | canonical prefixes and visual promise | Use derived prefixes. |

### Normalized input

```json
{
  "schema_version": "1.0",
  "tilemap": {
    "mode": "platformer | top_down_rpg | tactics_grid | roguelike_dungeon | sim_builder | tower_defense | puzzle_grid | isometric",
    "projection": "orthographic | isometric",
    "tile_size": 32,
    "connectivity": "single_tiles | 4_way | 8_way | wang | autotile_16 | autotile_47",
    "collision_model": "solid | walkable | blocked | one_way | slope | height | none"
  },
  "terrain_sets": [
    {
      "terrain_id": "grass",
      "meaning": "walkable outdoor ground",
      "walkability": "walkable",
      "collision": "none"
    }
  ],
  "style": {
    "dimension": "2d",
    "render_style": "pixel | painted | vector | hand_drawn | flat | unknown"
  }
}
```

## Mode Selection

Select exactly one primary mode unless the caller explicitly requests multiple
tileset families.

| Mode | Trigger signals | Required tile concerns |
|---|---|---|
| `platformer` | side view, jump, ground, wall, slope, platform | solids, one-way platforms, slopes, edge readability. |
| `top_down_rpg` | overworld, town, indoor, walkable, water, road | terrain transitions, walkability, decorative restraint. |
| `tactics_grid` | turn-based grid, movement range, attack range, cover | clear cells, terrain categories, height/cover hints. |
| `roguelike_dungeon` | rooms, corridors, doors, traps, procedural maps | floor/wall separation, door readability, repeatability. |
| `sim_builder` | build, place, road, farm, floor, zoning | repeatable surfaces, directional roads, occupied footprint. |
| `tower_defense` | enemy path, buildable, blocked, spawn, goal | path clarity, build zone clarity, route readability. |
| `puzzle_grid` | board, pressure plate, hazard, goal, switch | state symbols, interaction affordance, cell boundaries. |
| `isometric` | diamond tiles, height, iso map, angled view | perspective consistency, height edge rules, seamless joins. |

If signals conflict, choose the mode that controls collision and navigation. For
example, a tower-defense map with decorative top-down terrain uses
`tower_defense`, not `top_down_rpg`.

## Mode Defaults

| Mode | Default tile size | Connectivity | Collision model |
|---|---:|---|---|
| `platformer` | 32 | `autotile_47` | `solid` |
| `top_down_rpg` | 32 | `autotile_47` | `walkable` |
| `tactics_grid` | 64 | `single_tiles` | `height` |
| `roguelike_dungeon` | 32 | `autotile_16` | `walkable` |
| `sim_builder` | 32 | `4_way` | `blocked` |
| `tower_defense` | 32 | `4_way` | `walkable` |
| `puzzle_grid` | 64 | `single_tiles` | `none` |
| `isometric` | 64 | `wang` | `height` |

## Spec Workflow

| Stage | Purpose | Main output |
|---|---|---|
| 1. Detect applicability | Confirm the game uses map/grid tiles. | `applicability` |
| 2. Select mode | Choose tilemap mode and projection. | `tilemap.mode` |
| 3. Define terrain vocabulary | Ground, wall, water, path, hazard, etc. | `terrain_sets[]` |
| 4. Define tile variants | Center, edge, corner, transition, special. | `tile_variants[]` |
| 5. Define metadata | Collision, walkability, height, buildability. | `tile_metadata[]` |
| 6. Define atlas contract | Naming, size, spacing, margins, tile order. | `atlas_contract` |
| 7. Define preview maps | Small maps that prove repeatability. | `preview_maps[]` |
| 8. Validate | Check mode-specific completeness. | `tileset_validation` |

## Tile Variant Rules

Every terrain set must define:
- `terrain_id`,
- `semantic`,
- `base_tile`,
- `walkability`,
- `collision`,
- `variants[]`,
- `preview_usage`.

Variant requirements by connectivity:

| Connectivity | Required variants |
|---|---|
| `single_tiles` | base plus optional state variants. |
| `4_way` | center, end_n/e/s/w, straight_h/v, corner_ne/nw/se/sw, cross, t-junctions. |
| `8_way` | 4-way set plus diagonals and inner corners. |
| `autotile_16` | 16 mask-compatible variants. |
| `autotile_47` | 47 mask-compatible variants or documented reduced fallback. |
| `wang` | edge/color-coded transition set with compatible neighboring rules. |

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/art/tilesets/tileset-spec.json` | yes | Tilemap mode, terrain vocabulary, variants, metadata, atlas contract. | tileset-generation, level generation, runtime import, QA. |
| `.allforai/game-design/art/tilesets/tileset-spec-report.json` | yes | Applicability, validation, inferred defaults, missing inputs. | Diagnostics and QA. |

## Invocation Contract

```json
{
  "skill": "game-art/tileset-spec",
  "mode": "spec_validate",
  "input_paths": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "art_asset_inventory": ".allforai/game-design/art-asset-inventory.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "concept_contract": ".allforai/concept-contract.json"
  },
  "tilemap_request": {
    "mode": null,
    "tile_size": null,
    "projection": null,
    "connectivity": null
  },
  "output_root": ".allforai/game-design"
}
```

Supported modes:

| Mode | Behavior |
|---|---|
| `spec_validate` | Create tile contract and validate it. |
| `validate_existing` | Validate existing tile contract. |
| `repair_existing` | Repair missing variants, metadata, or atlas rules. |

## Schema

```json
{
  "schema_version": "1.0",
  "tilemap": {
    "mode": "top_down_rpg",
    "projection": "orthographic",
    "tile_size": 32,
    "connectivity": "autotile_47",
    "collision_model": "walkable"
  },
  "terrain_sets": [
    {
      "terrain_id": "grass",
      "file_prefix": "tile_grass",
      "semantic": "walkable grass terrain",
      "walkability": "walkable",
      "collision": "none",
      "variants": [
        {"variant_id": "center", "mask": "11111111", "required": true}
      ]
    }
  ],
  "atlas_contract": {
    "tile_size": 32,
    "margin": 2,
    "spacing": 2,
    "background": "transparent",
    "naming": "{file_prefix}_{variant_id}.png"
  },
  "preview_maps": []
}
```

## Automatic Validation

Run these checks:
1. Tilemap mode is one of the supported modes.
2. Projection, tile size, connectivity, and collision model are defined.
3. Every terrain set has `terrain_id`, `file_prefix`, semantic, walkability, and
   collision.
4. Required variants match the selected connectivity or declare a reduced
   fallback.
5. Mode-specific required terrain exists.
6. Atlas contract defines size, margin, spacing, background, and naming.
7. Preview maps include at least one seam/transition test when connectivity is
   not `single_tiles`.
8. Pixel style uses integer tile sizes and avoids fractional scaling.

Mode-specific minimums:
- `platformer`: ground, wall, platform, hazard or gap marker.
- `top_down_rpg`: ground, path, blocking terrain, transition terrain.
- `tactics_grid`: at least three terrain types with distinct movement meaning.
- `roguelike_dungeon`: floor, wall, door, corridor, special/hazard.
- `sim_builder`: base floor, road/path, blocked footprint, buildable marker.
- `tower_defense`: path, buildable, blocked, spawn, goal.
- `puzzle_grid`: normal, goal, blocker, interactive, hazard or special.
- `isometric`: base diamond, edge, corner, height face or ramp.

## Completion Conditions

Return `COMPLETED` only when `tileset-spec.json` and
`tileset-spec-report.json` validate and every selected mode has sufficient
terrain and variant contracts.

Return `NOT_APPLICABLE` when the game has no tilemap/grid/map assembly need.
Return `COMPLETED_WITH_LIMITS` only for planning/spec phases when a reduced
connectivity set is intentionally out of launch scope. For launch, launch-prep,
production, or unattended run goals, missing required terrain variants, generic
placeholder tiles, or reduced connectivity fallbacks are blockers.
