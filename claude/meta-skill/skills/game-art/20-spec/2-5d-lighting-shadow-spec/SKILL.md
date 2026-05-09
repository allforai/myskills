# 2.5D Lighting Shadow Spec Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Defines lighting, shadow, and helper-map rules for 3D-assisted production that
ships as 2D runtime art. It keeps 3D renders, 2D sprites, backgrounds, tiles,
VFX, and UI readable as one visual system.

Use this before render-to-2D generation when 3D source assets produce baked
lighting, contact shadows, normal/depth/height maps, or multi-angle renders.

## Input Contract

Required: 2.5D production mode spec, 3D source asset spec, production tool
capability registry, visual style tokens, and 2D view mode.

Optional: 2D layering spec, engine export profile, runtime lighting support,
background/tileset specs, VFX spec, and accessibility constraints.

## Output Contract

Writes:

- `.allforai/game-design/art/2-5d/2-5d-lighting-shadow-spec.json`
- `.allforai/game-design/art/2-5d/2-5d-lighting-shadow-report.json`

The spec must include `lighting_profile_id`, `view_mode_ref`,
`primary_light_direction`, `fill_policy`, `ambient_policy`,
`contact_shadow_policy`, `cast_shadow_policy`, `baked_pass_policy`,
`helper_map_policy`, `runtime_lighting_policy`, `vfx_lighting_policy`,
`ui_lighting_boundary`, `accessibility_limits`, `qa_requirements`, `state`, and
`consumer_refs`.

Allowed helper maps: `none`, `normal_map`, `depth_map`, `height_map`,
`mask_map`, `shadow_pass`, `ambient_occlusion_pass`, `custom`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_view_mode`, `blocked_by_runtime`, `blocked_by_source_assets`.

Downstream consumers: `render-to-2d-asset-generation`, `3d-assisted-2d-qa`,
`2d-style-consistency-qa`, `engine-export-profile`, `runtime-import-check`, and
`engine-ready-art-output-contract`.

## Invocation Contract

```json
{
  "skill": "game-art/2-5d-lighting-shadow-spec",
  "mode": "spec_validate",
  "input_paths": {
    "production_mode": ".allforai/game-design/art/2-5d/2-5d-production-mode-spec.json",
    "source_assets": ".allforai/game-design/art/2-5d/3d-source-asset-spec.json",
    "tool_registry": ".allforai/game-design/art/tools/production-tool-capability-registry.json",
    "visual_style_tokens": ".allforai/game-design/art/visual-style-tokens.json",
    "view_mode": ".allforai/game-design/art/view/2d-view-mode-spec.json"
  },
  "output_root": ".allforai/game-design/art/2-5d"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every 3D-assisted output has a light direction, shadow policy, and
runtime compatibility decision. If helper maps are requested, the target runtime
must support them and `engine-export-profile` must define import validation for
them. UI assets must not inherit world lighting unless explicitly designed.

Lighting consistency rules:

- One primary light direction per gameplay context unless a scene override is
  documented.
- Contact shadows must match view mode and actor footprint.
- Baked shadows must not hide gameplay-critical silhouettes.
- Normal/depth/helper maps must have a runtime consumer and import check.
- VFX brightness must obey readability and accessibility limits.
- 3D render lighting must be stylized enough to match 2D visual tokens.
- Required Blender render/bake capability must be available when the lighting
  plan requires generated shadow, normal, depth, height, or AO passes.

State progression gates:

```text
draft
-> validated                    light, shadow, helper maps, runtime support defined
-> needs_revision               lighting conflicts with style, view, or readability
-> blocked_by_view_mode         projection/footprint is unknown
-> blocked_by_runtime           requested helper maps cannot be imported/validated
-> blocked_by_source_assets     source renders lack required passes
```

Repair routing: projection defects route to `2d-view-mode-spec`; layer shadow
defects route to `2d-layering-spec`; unsupported helper maps route to
`engine-export-profile`; render pass issues route to `3d-source-asset-spec` or
`render-to-2d-asset-generation`; missing render/bake tools route to
`production-tool-capability-registry`; readability defects route to
`3d-assisted-2d-qa`.

## Completion Conditions

Return `COMPLETED` when lighting, shadows, helper maps, runtime support, and QA
expectations validate. Return `FAILED_VALIDATION` when lighting/helper-map
requirements cannot be validated in the target runtime. Return
`UPSTREAM_DEFECT` when production mode or source assets are missing.
