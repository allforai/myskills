---
name: game-art-20-spec-engine-export-profile
description: Internal bundled meta-skill module for game-art/20-spec/engine-export-profile; use within generated bootstrap node-specs when this exact contract is selected.
---

# Engine Export Profile Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Defines engine and tool export decisions for 2D art assets before runtime
import. It normalizes the decisions that must be made for atlas metadata,
pivots, frame naming, animation metadata, tilemap exports, skeleton formats,
compression, validation, and fallback behavior.

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
`format_decisions`, `format_decision_rationale`, `import_validation`,
`fallback_policy`, `adapter_policy`, `native_project_mutation`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_runtime_choice`, `blocked_by_tooling`, `automation_limited`.

Downstream consumers: `atlas-packaging`, `runtime-import-check`,
`2d-layering-spec`, `animation-state-machine-spec`, `skeletal-animation`,
`frame-animation-generation`, `tileset-generation`, `game-ui` export surfaces,
and runtime implementation nodes.

The profile must normalize these runtime-sensitive policies:

```json
{
  "target_runtime": "godot | unity | phaser | pixi | cocos | defold | love2d | custom_web | custom_native",
  "adapter_policy": "profile_only | generate_import_manifest | run_importer | native_project_edit",
  "native_project_mutation": false,
  "format_decisions": {
    "atlas_manifest": "<LLM-selected format for this runtime/project>",
    "animation_manifest": "<LLM-selected format for this runtime/project>",
    "tilemap_manifest": "<LLM-selected format or none>",
    "skeleton_manifest": "<LLM-selected format or none>"
  },
  "format_decision_rationale": [],
  "coordinate_system": {"origin": "top_left | bottom_left | center", "y_axis": "down | up"},
  "pivot_policy": {"default": "bottom_center", "per_layer_override": true},
  "atlas_policy": {"format": "json_hash | json_array | engine_native", "padding": 2, "trim": false},
  "animation_clip_policy": {"naming": "{asset_id}/{state_id}", "fps_source": "spec"},
  "sorting_policy": {"world_layers": true, "y_sort": false, "ui_sort": "z_index"},
  "validation_plan": {
    "preferred_method": "headless_engine_import | engine_editor_import | import_manifest_parse | runtime_preview_render | screenshot_probe | adapter_dry_run",
    "commands": [],
    "expected_evidence": [],
    "unavailable_status": "engine_unavailable"
  }
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

| Runtime | Atlas metadata | Animation metadata | Tilemap path | Adapter policy |
|---|---|---|---|---|
| Godot | `.tres`, `.import`, or JSON atlas | SpriteFrames, AnimationPlayer, or JSON clips | Tiled JSON, TMX, or Godot tile set | `generate_import_manifest` unless project files must be edited |
| Unity | SpriteAtlas/import settings or JSON atlas | Animator clips, AnimationController refs, or JSON clips | Unity Tilemap or Tiled JSON | `generate_import_manifest` unless `.meta`/asset DB edits are required |
| Phaser | Texture atlas JSON | frame tags or JSON state machine | Tiled JSON | `profile_only` or `generate_import_manifest` |
| Pixi | Texture atlas JSON | JSON clips/state machine | Tiled JSON | `profile_only` or `generate_import_manifest` |
| Cocos | plist/JSON atlas | animation clip metadata or JSON | Tiled JSON/TMX | `generate_import_manifest` |
| Defold | atlas/collection metadata | flipbook or JSON clips | tile source metadata | `generate_import_manifest` |
| Love2D | image plus JSON quads | custom Lua/JSON clips | Tiled JSON | `profile_only` |
| Custom web | JSON atlas | JSON state machine | JSON map | `profile_only` |
| Custom native | declared by runtime adapter | declared by runtime adapter | declared by runtime adapter | `generate_import_manifest` |

The runtime defaults are guidance, not a complete format matrix. The LLM may
choose a more appropriate concrete format when the target project already has
conventions, dependencies, importer code, or engine constraints. The chosen
format must be recorded in `format_decisions`, explain why it was selected, and
define how `runtime-import-check` can validate it.

Do not create engine-specific child skills by default. Add a future
engine-specific adapter only when at least one condition is true:

- the engine project files must be modified directly,
- native importer/editor/CLI execution is required,
- engine asset database or `.meta` files must be generated,
- validation needs engine-specific screenshots or scene loading,
- profile-only manifests cannot represent the import behavior.

Until then, represent engine differences in this profile and validate them via
`runtime-import-check` and `engine-ready-art-output-contract`.

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
- `adapter_policy=native_project_edit` must name the exact project files and
  owning implementation node.
- Concrete output formats may be LLM-selected, but none may be implicit. Every
  selected format must have a consumer, rationale, validation path, and fallback.
- `validation_plan` must define an executable automatic import check and
  expected evidence files. Static metadata checks are diagnostics only and must
  not be accepted as validation.
- Runtime import check must have a deterministic manifest path even when no
  engine command is available.

Repair routing: missing runtime choice returns to project/bootstrap planning;
invalid atlas or pivot data repairs here before asset regeneration; missing
export files route to `atlas-packaging`; runtime import failures route to
`runtime-import-check`; native adapter failures route to the future
engine-specific adapter only when this profile cannot express the repair;
animation naming failures route to `animation-state-machine-spec`.

## Completion Conditions

Return `COMPLETED` when the target runtime or adapter, metadata formats,
coordinate system, export paths, executable validation plan, and failure
statuses are all defined. Return `FAILED_VALIDATION` when no executable import
validation path can be defined. Return `UPSTREAM_DEFECT` when no runtime or
import surface can be inferred.
