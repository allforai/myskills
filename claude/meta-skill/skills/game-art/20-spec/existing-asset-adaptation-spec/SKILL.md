---
name: game-art-20-spec-existing-asset-adaptation-spec
description: Internal bundled meta-skill module for game-art/20-spec/existing-asset-adaptation-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Existing Asset Adaptation Spec Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Defines how existing or user-provided 2D or 3D assets must be adapted to match
the project's art, metadata, engine, and handoff contracts. It covers renaming,
resizing, palette/style normalization, slicing, atlas grouping, pivots, anchors,
animation metadata, tile metadata, UI sizing, VFX timing, 3D source preparation,
and runtime import requirements.

Use this only after license/provenance QA passes.

## Input Contract

Required: passed license/provenance QA report and selected asset candidate or
local asset manifest.

Optional: source strategy spec, visual style tokens, view mode, layering spec,
engine export profile, production tool capability registry, artifact handoff
contract, atlas packaging rules, 3D source asset spec, and runtime import
requirements.

## Output Contract

Writes:

- `.allforai/game-design/art/sourcing/existing-asset-adaptation-spec.json`
- `.allforai/game-design/art/sourcing/existing-asset-adaptation-manifest.json`
- `.allforai/game-design/art/sourcing/existing-asset-adaptation-report.json`

Adaptation entries must include `asset_id`, `source_candidate_id`,
`source_paths`, `license_verdict_ref`, `adaptation_actions`,
`target_paths`, `rename_policy`, `scale_policy`, `style_adjustment_policy`,
`slice_policy`, `pivot_anchor_policy`, `animation_metadata_policy`,
`tile_metadata_policy`, `atlas_group`, `handoff_entry_ref`, `qa_requirements`,
`runtime_import_requirements`, `source_3d_policy`, `target_2d_outputs`, `state`,
and `consumer_refs`.

Allowed adaptation actions: `rename`, `resize`, `crop`, `slice`,
`palette_adjust`, `style_normalize`, `alpha_cleanup`, `atlas_pack`,
`pivot_anchor_set`, `animation_metadata_create`, `tile_metadata_create`,
`ui_scale_fit`, `vfx_timing_map`, `3d_unit_scale_normalize`,
`3d_axis_orientation_fix`, `3d_material_simplify`, `3d_rig_animation_cleanup`,
`3d_render_pass_setup`, `3d_source_register`, `register_only`, `reject`.

Allowed states: `draft`, `adapted`, `registered_existing`, `needs_revision`,
`blocked_by_license`, `blocked_by_missing_source`, `blocked_by_tooling`.

Downstream consumers: `artifact-handoff-contract`, `atlas-packaging`,
`2d-style-consistency-qa`, `asset-pack-integration-qa`,
`3d-source-asset-spec`, `render-to-2d-asset-generation`, `runtime-import-check`,
and `engine-ready-art-output-contract`.

## Invocation Contract

```json
{
  "skill": "game-art/existing-asset-adaptation-spec",
  "mode": "adapt_validate",
  "input_paths": {
    "license_report": ".allforai/game-design/art/sourcing/asset-license-provenance-qa-report.json",
    "search_results": ".allforai/game-design/art/sourcing/asset-pack-search-results.json",
    "engine_export_profile": ".allforai/game-design/art/export/engine-export-profile.json"
  },
  "output_root": ".allforai/game-design/art/sourcing"
}
```

Supported modes: `spec_only`, `adapt_validate`, `register_existing`,
`validate_existing`, `repair_existing`.

## Automatic Validation

Check that each adapted asset has a passed license verdict, source path, target
path, adaptation action list, QA route, runtime route, and artifact handoff
entry. Adaptation must preserve attribution and license metadata.

Adaptation requirements by asset kind:

| Asset kind | Required adaptation metadata |
|---|---|
| character sheet | frame grid, pivots, anchors, action/state refs |
| tileset | tile size, collision/walkability, terrain rules, preview map |
| UI pack | component states, safe sizes, text-free variants when needed |
| icon pack | size set, alpha, naming, semantic refs |
| VFX pack | frame timing, blend mode, event refs, intensity |
| prop/background | scale, layer refs, alpha/crop, collision helper refs |
| 3D model/source | unit scale, axis/orientation, material policy, camera/render purpose, runtime exclusion |
| 3D animation pack | clip names, frame ranges, skeleton/rig notes, render-to-2D mapping |
| 3D material/texture pack | texture slots, style simplification, render pass usage, license carry-through |

3D adaptation rules:

- Existing 3D assets are production sources by default, not runtime assets.
- Adapted 3D source entries must route to `3d-source-asset-spec`.
- Required Blender CLI capability must be verified in
  `production-tool-capability-registry` before adaptation can claim render
  readiness.
- Runtime exclusion metadata must be preserved into
  `engine-ready-art-output-contract`.
- If a 3D asset cannot be opened, scaled, oriented, or mapped to a 2D output,
  return `blocked_by_tooling` or `needs_revision`; do not register it as usable.

State progression gates:

```text
draft
-> adapted                    target files/manifests generated
-> registered_existing        existing files registered without mutation
-> needs_revision             adaptation conflicts with style/runtime/handoff
-> blocked_by_license         license does not allow required adaptation
-> blocked_by_missing_source  source files unavailable
-> blocked_by_tooling         required image/atlas/script tool unavailable
```

Repair routing: missing license routes to `asset-license-provenance-qa`; style
fit routes to `2d-style-consistency-qa`; handoff field gaps route to
`artifact-handoff-contract`; atlas issues route to `atlas-packaging`; runtime
format issues route to `engine-export-profile`; 3D source mapping routes to
`3d-source-asset-spec`; missing Blender/tool support routes to
`production-tool-capability-registry`.

## Completion Conditions

Return `COMPLETED` when adapted or registered assets have valid manifests,
handoff entries, QA routes, runtime routes, and license metadata. Return
`FAILED_VALIDATION` when license, source files, or adaptation evidence are
insufficient.
