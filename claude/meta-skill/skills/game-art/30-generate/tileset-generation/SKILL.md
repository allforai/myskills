---
name: game-art-30-generate-tileset-generation
description: Internal bundled meta-skill module for game-art/30-generate/tileset-generation; use within generated bootstrap node-specs when this exact contract is selected.
---

# Tileset Generation Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill produces tileset prompts/specs, generated tile sheets, atlas
manifests, metadata, preview maps, and validation reports from
`tileset-spec.json`. It validates whether generated tiles are repeatable,
readable, and compatible with the selected tilemap mode.

The goal is not just to make attractive squares. A usable tileset must join
cleanly, preserve gameplay meaning, expose collision/walkability metadata, and
survive preview-map assembly.

## Scope

In scope:
- prompt/spec generation for tile images,
- tile sheet generation or spec-only fallback,
- transparent/seam-safe exports,
- atlas manifests and tile metadata,
- preview map generation,
- deterministic and visual validation,
- repair loops for seams, inconsistent scale, unreadable terrain, or bad
  collision semantics.

Out of scope:
- level design,
- procedural map generation beyond preview maps,
- full background painting,
- final engine import implementation,
- manual artist cleanup.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| `.allforai/game-design/art/tilesets/tileset-spec.json` | tilemap mode, terrain sets, variants, atlas contract | Return `UPSTREAM_DEFECT`. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/game-design/art-style-guide.json` | palette, rendering style, texture density | Use neutral readable tiles. |
| `.allforai/game-design/asset-registry.json` | registered tile assets and prefixes | Use prefixes from tileset spec. |
| `.allforai/concept-contract.json` | visual promise and naming | Use tileset spec. |
| Existing tile images | validation and atlas registration | Generate missing specs only. |
| Caller context | image generation, vision validation, atlas tool availability | Produce specs and manifests if tools are unavailable. |

## Generation Workflow

| Stage | Purpose | Main output |
|---|---|---|
| 1. Load tile contract | Read mode, variants, metadata, atlas rules. | `normalized_tileset` |
| 2. Write tile prompts | One prompt/spec per terrain set or sheet. | `tile_generation_specs[]` |
| 3. Generate or register images | Create tile sheet or individual tiles. | `tiles/*.png` |
| 4. Slice/manifest | Record tile coordinates, variants, metadata. | `tileset-manifest.json` |
| 5. Build preview maps | Assemble representative maps from tiles. | `preview_maps/*.png` |
| 6. Validate | Seams, readability, metadata, mode rules. | `tileset-generation-report.json` |
| 7. Repair | Update prompts/specs and regenerate up to capped attempts. | `repair_log[]` |
| 8. Accept | Mark generated, approved, or automation-limited. | `acceptance` |

## Prompt Rules

Tile prompts must specify:
- exact tile size,
- projection,
- render style,
- background policy,
- required terrain set and variants,
- seamless edge requirements,
- no labels/text,
- no shadows or decorations crossing tile boundaries unless variant rules allow
  them,
- consistent camera and lighting,
- small-size readability.

For connected tiles, prompts must request edge-compatible variants and avoid
unique landmarks that break repetition.

## Image Generation Upstream Contract

Every generated tile image or tile sheet must follow
`game-art/30-generate/image-generation-contract/SKILL.md`.

Use normalized image requests with `purpose=tileset` and
`generation_profile.task_type=tileset`. The request must use
`prompt_template=tileset_prompt` and a model profile that supports consistent
tile/texture output. It must include tile size, projection, connectivity,
terrain id, variant id, atlas contract, positive prompt, negative prompt, output
path, seam checks, preview-map checks, and `downstream_feedback.enabled=true`.

If atlas packing, preview-map assembly, level generation, or runtime import
reports `SEAM_FAILURE`, `WRONG_SCALE`, `STYLE_DRIFT`, `BAD_ALPHA`,
`LOW_READABILITY`, or `CROPPED_SUBJECT`, classify the root cause through
`image-generation-contract`. Regenerate tiles when the image violates the
request or the prompt was underspecified.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/art/tilesets/tileset-generation-spec.json` | yes | Prompts, target sheets, generation settings, repair plan. | image generation and QA. |
| `.allforai/game-design/art/tilesets/tileset-manifest.json` | yes | Tile paths, atlas coordinates, variants, metadata, states. | runtime import, level generation, UI previews, QA. |
| `.allforai/game-design/art/tilesets/tileset-generation-report.json` | yes | Validation verdict, issues, repair attempts, limits. | diagnostics and QA. |
| `.allforai/game-design/art/tilesets/*.png` | when generated | Tile sheets or individual tile images. | runtime import and previews. |
| `.allforai/game-design/art/tilesets/previews/*.png` | when generated | Preview maps proving seams and readability. | QA and diagnostics. |

## Invocation Contract

```json
{
  "skill": "game-art/tileset-generation",
  "mode": "spec_generate_validate",
  "input_paths": {
    "tileset_spec": ".allforai/game-design/art/tilesets/tileset-spec.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "concept_contract": ".allforai/concept-contract.json"
  },
  "generation": {
    "image_generation_available": true,
    "vision_validation_available": true,
    "atlas_tool_available": false,
    "max_repair_attempts": 3
  },
  "output_root": ".allforai/game-design"
}
```

Supported modes:

| Mode | Behavior |
|---|---|
| `spec_only` | Write generation specs and manifest placeholders for planning only; this mode cannot complete a production art-gen node. |
| `spec_generate_validate` | Generate/register tiles, assemble preview maps, validate, repair, report. |
| `validate_existing` | Validate existing tile images and manifest. |
| `register_existing` | Register existing tile files without regenerating. |

## Manifest Schema

```json
{
  "schema_version": "1.0",
  "tilemap": {
    "mode": "top_down_rpg",
    "projection": "orthographic",
    "tile_size": 32,
    "connectivity": "autotile_47"
  },
  "tiles": [
    {
      "tile_id": "grass_center",
      "terrain_id": "grass",
      "variant_id": "center",
      "file_prefix": "tile_grass",
      "path": ".allforai/game-design/art/tilesets/tile_grass_center.png",
      "atlas": {"x": 0, "y": 0, "w": 32, "h": 32},
      "walkability": "walkable",
      "collision": "none",
      "state": "generated | approved | needs_revision | automation_limited"
    }
  ],
  "preview_maps": []
}
```

## Automatic Validation

Run deterministic checks:
1. Every required tile variant from `tileset-spec.json` exists in the manifest or
   has a documented reduced fallback.
2. Every tile path starts with `.allforai/game-design/art/tilesets/`.
3. Every tile path starts with the terrain `file_prefix`.
4. Tile sizes match the atlas contract.
5. Walkability and collision metadata match the spec.
6. Preview maps exist when generation is available.
7. No tile is marked `approved` without deterministic validation.

Run visual validation when images exist:
1. Tile edges connect without obvious seams for connected modes.
2. Terrain categories are distinguishable at gameplay scale.
3. Collision meaning is visually readable.
4. Repeated tiles do not create distracting unique patterns.
5. Isometric tiles share the same diamond perspective and height logic.
6. Platformer solids have readable top/side boundaries.
7. Tower-defense paths and buildable zones cannot be confused.
8. Puzzle interactive cells have clear state symbols.

If validation fails, repair the prompt/spec and regenerate up to 3 times. If it
still fails, mark affected tiles `automation_limited` and preserve a reduced
fallback set that downstream systems can consume.

## Mode-Specific Acceptance

| Mode | Must pass |
|---|---|
| `platformer` | top surface readable, side walls distinct, one-way/slope metadata clear. |
| `top_down_rpg` | walkable/blocking/transition terrain visibly distinct. |
| `tactics_grid` | each cell boundary and terrain type remains readable. |
| `roguelike_dungeon` | walls, floors, doors, corridors assemble without ambiguity. |
| `sim_builder` | roads/floors repeat cleanly and buildability is visible. |
| `tower_defense` | route, buildable, blocked, spawn, and goal are unmistakable. |
| `puzzle_grid` | interaction state survives small-scale view. |
| `isometric` | diamond edges align and height/ramps are coherent. |

## Completion Conditions

Return `COMPLETED` only when specs, manifest, accepted image entries, preview
maps, and report validate, and generated tiles pass visual validation when
generation is required.

Return `COMPLETED_WITH_LIMITS` only for planning/spec stages or when a reduced
variant set is explicitly out of launch scope after actual image evidence was
inspected. For launch, launch-prep, production, or unattended run goals, reduced
variant fallback, generic tiles, missing chapter/theme variants, missing images,
missing preview maps, or skipped visual validation must return
`FAILED_VALIDATION` or `blocked_by_missing_visual_evidence`; spec-only output
must not be treated as completed generated art.
