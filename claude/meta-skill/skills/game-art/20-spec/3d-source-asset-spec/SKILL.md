# 3D Source Asset Spec Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Defines 3D source assets that are used only for art production in a 2D runtime
pipeline. It describes model purpose, cameras, materials, lighting hooks, render
passes, ownership, and explicit runtime exclusion.

Use this when 3D models, blockouts, or scenes help produce final 2D sprites,
tiles, props, backgrounds, thumbnails, shadows, normal maps, or depth helpers.

## Input Contract

Required: 2.5D production mode spec, production tool capability registry, and
asset IDs that require 3D assistance.

Optional: visual style tokens, 2D view mode, 2D layering spec, lighting/shadow
spec, existing 3D source files, Blender/project files, camera references, and
render-to-2D requirements.

## Output Contract

Writes:

- `.allforai/game-design/art/2-5d/3d-source-asset-spec.json`
- `.allforai/game-design/art/2-5d/3d-source-asset-report.json`

Source entries must include `source_asset_id`, `target_2d_asset_id`,
`source_kind`, `production_purpose`, `source_path`, `camera_rig_ref`,
`lighting_ref`, `material_style`, `render_passes`, `angle_set`,
`scale_reference`, `runtime_allowed`, `runtime_exclusion_reason`,
`generated_2d_outputs`, `owner`, `state`, and `consumer_refs`.

Allowed `source_kind` values: `blockout`, `character_model`, `prop_model`,
`building_model`, `environment_scene`, `lighting_rig`, `camera_rig`,
`material_library`, `helper_mesh`.

Allowed states: `planned`, `source_ready`, `render_ready`, `needs_revision`,
`blocked_by_tooling`, `blocked_by_style`, `runtime_excluded`.

Downstream consumers: `2-5d-lighting-shadow-spec`,
`render-to-2d-asset-generation`, `3d-assisted-2d-qa`,
`engine-ready-art-output-contract`, and production tooling nodes.

## Invocation Contract

```json
{
  "skill": "game-art/3d-source-asset-spec",
  "mode": "spec_validate",
  "input_paths": {
    "production_mode": ".allforai/game-design/art/2-5d/2-5d-production-mode-spec.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "visual_style_tokens": ".allforai/game-design/art/visual-style-tokens.json"
  },
  "output_root": ".allforai/game-design/art/2-5d"
}
```

Supported modes: `spec_validate`, `validate_existing`, `register_existing`,
`repair_existing`.

## Automatic Validation

Check that every source asset maps to at least one final 2D output and has
`runtime_allowed=false` unless an explicit hybrid-runtime contract exists.
Validate camera angle, scale reference, material style, render passes, source
path, owner, and required tool availability. Raw 3D sources must not be added to
engine-ready output by default.

Source-to-output requirements:

| Source purpose | Required 2D output |
|---|---|
| character pose/model | sprite render, pose sheet, or reference image |
| isometric building/prop | angle-locked 2D render with alpha |
| scene blockout | background plate, layout guide, or paintover reference |
| lighting rig | baked shadow/light pass or documented no-output helper |
| helper mesh | collision/depth/normal helper map or production-only reference |

State progression gates:

```text
planned
-> source_ready                 source path or generation plan exists
-> render_ready                 camera, lighting, passes, and outputs are defined
-> needs_revision               source/output mapping or style is inconsistent
-> blocked_by_tooling           source cannot be opened/rendered by available tooling
-> blocked_by_style             source cannot satisfy visual style constraints
-> runtime_excluded             valid production source, explicitly excluded from runtime
```

Repair routing: missing asset IDs route to `asset-registry`; projection/camera
issues route to `2d-view-mode-spec`; lighting issues route to
`2-5d-lighting-shadow-spec`; output mapping issues route to
`render-to-2d-asset-generation`; missing source/render tools route to
`production-tool-capability-registry`; runtime leakage routes to
`engine-ready-art-output-contract`.

## Completion Conditions

Return `COMPLETED` when all 3D source assets have validated source policy,
render requirements, final 2D output mapping, and runtime exclusion status.
Return `FAILED_VALIDATION` when a source asset cannot be mapped to a 2D output
or may leak into runtime. Return `UPSTREAM_DEFECT` when production mode is
missing.
