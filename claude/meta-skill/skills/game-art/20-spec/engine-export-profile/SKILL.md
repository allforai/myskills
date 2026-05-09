# Engine Export Profile Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Defines engine and tool export contracts for 2D art assets before runtime
import. It normalizes atlas format, pivot coordinates, frame naming, animation
metadata, tilemap exports, skeleton formats, compression, and fallback behavior.

Use this when the art pipeline must target Godot, Unity, Phaser, Pixi, Cocos,
Defold, Love2D, Tiled, Aseprite, TexturePacker, Spine, DragonBones, or a custom
runtime adapter.

## Input Contract

Required: target runtime or engine, asset classes, and desired import surface.

Optional: asset registry, atlas manifests, tilemap specs, animation state
machine spec, skeletal animation manifests, frame animation manifests, UI
registry, 2D view mode, 2D layering spec, performance budget, and existing
project conventions.

## Output Contract

Writes:

- `.allforai/game-design/art/export/engine-export-profile.json`
- `.allforai/game-design/art/export/engine-export-profile-report.json`

The profile must include `profile_id`, `target_runtime`, `coordinate_system`,
`unit_scale`, `pivot_policy`, `anchor_policy`, `atlas_policy`,
`animation_clip_policy`, `state_machine_policy`, `tilemap_policy`,
`skeleton_policy`, `ui_asset_policy`, `naming_policy`, `compression_policy`,
`import_validation`, `fallback_policy`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_runtime_choice`, `blocked_by_tooling`, `automation_limited`.

Downstream consumers: `atlas-packaging`, `runtime-import-check`,
`2d-layering-spec`, `animation-state-machine-spec`, `skeletal-animation`,
`frame-animation-generation`, `tileset-generation`, `game-ui` export surfaces,
and runtime implementation nodes.

The profile must normalize these runtime-sensitive policies:

```json
{
  "coordinate_system": {"origin": "top_left | bottom_left | center", "y_axis": "down | up"},
  "pivot_policy": {"default": "bottom_center", "per_layer_override": true},
  "atlas_policy": {"format": "json_hash | json_array | engine_native", "padding": 2, "trim": false},
  "animation_clip_policy": {"naming": "{asset_id}/{state_id}", "fps_source": "spec"},
  "sorting_policy": {"world_layers": true, "y_sort": false, "ui_sort": "z_index"},
  "validation_commands": []
}
```

## Invocation Contract

```json
{
  "skill": "game-art/engine-export-profile",
  "mode": "profile_validate",
  "input_paths": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "animation_state_machine": ".allforai/game-design/art/animation/animation-state-machine-spec.json",
    "atlas_manifest": ".allforai/game-design/art/atlases/atlas-manifest.json"
  },
  "output_root": ".allforai/game-design/art/export"
}
```

Supported modes: `profile_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that the profile names one target runtime or adapter, one coordinate
system, one pivot convention, one atlas metadata format, one animation clip
naming rule, and one runtime import validation path. Tilemap projects must
declare map format and tile ID conventions. Skeletal projects must declare
whether the runtime consumes Spine, DragonBones, generated JSON, or simplified
transform timelines.

Common runtime defaults:

| Runtime | Atlas metadata | Animation metadata | Tilemap path |
|---|---|---|---|
| Godot | `.tres` or JSON atlas | AnimationPlayer or sprite frames | Tiled JSON or Godot tile set |
| Unity | SpriteAtlas metadata | Animator clips or custom JSON | Unity Tilemap or Tiled JSON |
| Phaser/Pixi | Texture atlas JSON | frame tags or custom JSON | Tiled JSON |
| Love2D | image plus JSON quads | custom Lua/JSON clips | Tiled JSON |
| Custom web | JSON atlas | JSON state machine | JSON map |

State progression gates:

```text
draft
-> validated                    runtime, coordinates, pivots, atlas, clips, import checks defined
-> needs_revision               policies conflict with layer, atlas, or animation specs
-> blocked_by_runtime_choice    target runtime is missing or contradictory
-> blocked_by_tooling           required exporter/importer is unavailable
-> automation_limited           profile is valid but validation command cannot run
```

Validation requirements:

- Pivot and anchor policy must match `2d-layering-spec`.
- Atlas padding/trim rules must be consumable by `atlas-packaging`.
- State machine export must preserve event frame IDs.
- Tilemap policy must preserve collision and walkability metadata.
- UI assets must not inherit world y-sort.
- Runtime import check must have a deterministic manifest path even when no
  engine command is available.

Repair routing: missing runtime choice returns to project/bootstrap planning;
invalid atlas or pivot data repairs here before asset regeneration; missing
export files route to `atlas-packaging`; runtime import failures route to
`runtime-import-check`; animation naming failures route to
`animation-state-machine-spec`.

## Completion Conditions

Return `COMPLETED` when the target runtime, metadata formats, coordinate system,
export paths, validation commands, and fallbacks are all defined. Return
`COMPLETED_WITH_LIMITS` when the target runtime is generic but the profile still
defines a custom JSON adapter. Return `UPSTREAM_DEFECT` when no runtime or
import surface can be inferred.
