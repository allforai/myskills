---
name: game-art-30-generate-render-to-2d-asset-generation
description: Internal bundled meta-skill module for game-art/30-generate/render-to-2d-asset-generation; use within generated bootstrap node-specs when this exact contract is selected.
---

# Render To 2D Asset Generation Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Generates or registers 2D runtime assets from 3D-assisted production sources.
Outputs may include sprite sheets, prop renders, isometric tile renders,
background plates, character turnarounds, shadow passes, normal/depth/helper
maps, thumbnails, and preview images.

The final runtime output is 2D unless the production mode explicitly permits a
hybrid runtime. Raw 3D source files are production inputs, not engine-ready art.

## Input Contract

Required: production tool capability registry, 2.5D production mode spec, 3D
source asset spec, lighting/shadow spec, and engine export profile.

Optional: 2D layering spec, visual style tokens, image-generation contract,
atlas packaging rules, runtime import requirements, existing renders, and
available render tools.

## Output Contract

Writes:

- `.allforai/game-design/art/2-5d/renders/render-to-2d-generation-spec.json`
- `.allforai/game-design/art/2-5d/renders/scripts/{output_asset_id}_render.py`
- `.allforai/game-design/art/2-5d/renders/render-to-2d-manifest.json`
- `.allforai/game-design/art/2-5d/renders/render-to-2d-report.json`
- generated 2D image/pass files when tooling is available.

Manifest entries must include `output_asset_id`, `source_asset_id`,
`runtime_asset_kind`, `render_method`, `render_script_path`,
`render_command`, `render_log_path`, `camera_ref`, `lighting_ref`, `passes`,
`paths`, `dimensions`, `frame_grid`, `angle`, `pivot`, `anchor`, `layer_refs`,
`atlas_group`, `qa_status`, `runtime_import_status`, `state`, and
`consumer_refs`.

Each output must also emit or update an artifact handoff entry compatible with
`artifact-handoff-contract`. The manifest must include `downstream_routes`:

```json
{
  "output_asset_id": "player_run_sheet",
  "handoff_contract_ref": ".allforai/game-design/art/handoff/artifact-handoff-contract.json",
  "output_type": "character_sprite_sheet",
  "downstream_routes": [
    {
      "consumer_skill": "game-art/frame-animation-generation",
      "handoff_kind": "source_sheet",
      "required_fields": ["paths", "frame_grid", "pivot", "fps", "alpha_policy"],
      "blocks_if_missing": true
    }
  ]
}
```

Allowed states: `spec_ready`, `rendered`, `registered_existing`,
`preview_ready`, `qa_ready`, `needs_revision`, `blocked_by_tooling`,
`blocked_by_source`, `blocked_by_runtime_profile`.

Downstream consumers: `atlas-packaging`, `3d-assisted-2d-qa`,
`2d-style-consistency-qa`, `artifact-handoff-contract`, `runtime-import-check`,
`engine-ready-art-output-contract`, level/UI/runtime implementation, and
animation/state-machine specs when frames are produced.

## Invocation Contract

```json
{
  "skill": "game-art/render-to-2d-asset-generation",
  "mode": "generate_validate",
  "input_paths": {
    "production_mode": ".allforai/game-design/art/2-5d/2-5d-production-mode-spec.json",
    "tool_registry": ".allforai/game-design/art/tools/production-tool-capability-registry.json",
    "source_assets": ".allforai/game-design/art/2-5d/3d-source-asset-spec.json",
    "lighting_shadow": ".allforai/game-design/art/2-5d/2-5d-lighting-shadow-spec.json",
    "engine_export_profile": ".allforai/game-design/art/export/engine-export-profile.json"
  },
  "output_root": ".allforai/game-design/art/2-5d/renders"
}
```

Supported modes: `spec_only`, `generate_validate`, `register_existing`,
`validate_existing`, `repair_existing`.

## Automatic Validation

Before render execution, call `production-tool-capability-registry` in
`ensure_required_tools` mode. If Blender CLI or the declared equivalent renderer
is missing, the registry must attempt installation and re-verify. If the tool
still cannot run, return `blocked_by_tooling`; do not emit rendered outputs.

Check source refs, Blender CLI availability, generated script path, render
command, render log, camera refs, render passes, alpha/background policy, frame
grid, pivot/anchor, dimensions, layer refs, atlas group, helper map consumers,
and final 2D runtime path. Do not mark outputs runtime-ready until
`3d-assisted-2d-qa` and `runtime-import-check` pass.

Blender Python execution contract:

```text
generate deterministic script
-> run blender --background [source.blend] --python script.py
-> write render log
-> write PNG sequence/sheets/helper maps
-> write manifest entries with render_command and evidence paths
-> validate outputs before downstream handoff
```

The script must set camera, resolution, transparent background, render passes,
frame/angle iteration, output paths, and machine-readable summary output. Do not
use Blender UI automation as the production path.

Output requirements:

| Output type | Required fields |
|---|---|
| sprite sheet | frame grid, FPS/clip ref, pivot, alpha, state-machine consumer |
| prop render | angle, alpha, scale reference, collision/helper metadata |
| tile render | tile size, projection, collision/walkability metadata |
| background plate | camera, layer/parallax refs, safe crop, optional depth pass |
| helper map | map kind, paired color asset, runtime consumer, import validation |
| thumbnail/icon render | crop, size, UI consumer, style QA route |

Output-to-downstream routing:

| 3D-assisted output | Required downstream routes |
|---|---|
| `character_sprite_sheet` | `frame-animation-generation`, `animation-state-machine-spec`, `atlas-packaging`, `3d-assisted-2d-qa`, `runtime-import-check` |
| `multi_direction_character_sheet` | `frame-animation-generation`, `animation-state-machine-spec`, `2d-view-mode-spec`, `atlas-packaging`, `runtime-import-check` |
| `pose_sheet` | `motion-design`, `frame-animation-spec`, `character-layer-sheet`, `3d-assisted-2d-qa` |
| `character_part_render_set` | `character-layer-sheet`, `2d-layering-spec`, `skeletal-animation`, `atlas-packaging` |
| `prop_render` | `prop-generation`, `2d-layering-spec`, `atlas-packaging`, `runtime-import-check` |
| `building_render` | `prop-generation`, `tileset-generation` when tile-like, `level-layout-spec`, `atlas-packaging` |
| `isometric_tile_render` | `tileset-generation`, `level-layout-spec`, `atlas-packaging`, `runtime-import-check` |
| `background_plate` | `background-generation`, `2d-layering-spec`, `level-layout-spec`, `2d-style-consistency-qa` |
| `shadow_pass` | `2-5d-lighting-shadow-spec`, `2d-layering-spec`, `atlas-packaging`, `runtime-import-check` |
| `normal_depth_height_map` | `engine-export-profile`, `runtime-import-check`, `engine-ready-art-output-contract` |
| `item_thumbnail_render` | `item-art-generation`, `icon-generation`, `game-ui`, `2d-style-consistency-qa` |
| `vfx_sprite_render` | `sprite-vfx-generation`, `vfx-generation`, `animation-event-fx`, `3d-assisted-2d-qa` |
| `preview_contact_sheet` | `art-preview-qa`, `3d-assisted-2d-qa`, `2d-style-consistency-qa` |

Routing validation rules:

- Every output must have at least one QA route and one final runtime/export route.
- Every output must validate against `artifact-handoff-contract` before a
  downstream consumer treats it as input.
- Frame or direction sheets must route to animation/state-machine consumers.
- Tiles, props, and buildings must route to level or atlas consumers.
- Helper maps must route to `engine-export-profile` and executable
  `runtime-import-check`; otherwise they are invalid.
- Thumbnails/icons must route to UI or inventory consumers, not world layering
  only.
- Preview-only outputs must be marked `runtime_asset_kind=preview_only` and must
  not enter `engine-ready-art-output-contract` as runtime assets.
- Raw 3D source paths may be referenced by provenance fields only; they must not
  appear in `paths` for runtime outputs.

State progression gates:

```text
spec_ready
-> rendered                    output files generated
-> registered_existing         existing 2D renders registered
-> preview_ready               preview/contact sheet exists
-> qa_ready                    ready for 3D-assisted QA and runtime import
-> needs_revision              render does not match spec/style/runtime needs
-> blocked_by_tooling          render tool unavailable
-> blocked_by_source           source asset, camera, or pass missing
-> blocked_by_runtime_profile  output format/import policy undefined
```

Repair routing: missing source/camera/pass returns to `3d-source-asset-spec`;
lighting mismatch returns to `2-5d-lighting-shadow-spec`; layer/pivot mismatch
returns to `2d-layering-spec`; output format issues return to
`engine-export-profile`; invalid handoff fields route to
`artifact-handoff-contract`; missing or unverified Blender CLI routes to
`production-tool-capability-registry`; visual defects route to
`3d-assisted-2d-qa`.

## Completion Conditions

Return `COMPLETED` when generation/registration, manifest, preview, and reports
validate and outputs are ready for QA. Return `COMPLETED_WITH_LIMITS` only when
the caller explicitly accepts registered existing renders without generation.
Return `FAILED_VALIDATION` when render outputs cannot be produced or registered
with enough evidence for downstream import validation.
