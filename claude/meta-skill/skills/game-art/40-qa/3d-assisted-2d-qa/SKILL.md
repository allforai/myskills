# 3D Assisted 2D QA Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Validates 2D runtime assets produced from 3D-assisted production. It checks that
3D-derived renders still behave like coherent 2D game art: perspective,
projection, scale, light, shadow, edge quality, pivots, anchors, layers, atlas
metadata, style fit, and runtime exclusion of raw 3D source assets.

Use this before `runtime-import-check` and `engine-ready-art-output-contract`.

## Input Contract

Required: render-to-2D manifest, 2.5D production mode spec, 3D source asset
spec, lighting/shadow spec, production tool capability registry, and 2D view
mode.

Optional: 2D layering spec, visual style tokens, art preview QA, atlas manifest,
runtime screenshots, generated render previews, and engine export profile.

## Output Contract

Writes:

- `.allforai/game-design/art/2-5d/qa/3d-assisted-2d-qa-report.json`

Issues must include `issue_id`, `output_asset_id`, `source_asset_id`,
`severity`, `qa_axis`, `expected`, `actual`, `evidence_paths`, `root_cause`,
`repair_target`, `blocks_runtime`, and `consumer_refs`.

Allowed root causes: `production_mode`, `3d_source_asset`, `lighting_shadow`,
`render_to_2d`, `2d_view_mode`, `2d_layering`, `visual_style_tokens`,
`atlas_packaging`, `engine_export_profile`, `runtime_import`, and `unknown`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_evidence`, `blocked_by_runtime_leak`,
`blocked_by_import_validation`.

Downstream consumers: `runtime-import-check`,
`engine-ready-art-output-contract`, `2d-style-consistency-qa`,
`atlas-packaging`, level/UI/runtime implementation, and playtest QA.

## Invocation Contract

```json
{
  "skill": "game-art/3d-assisted-2d-qa",
  "mode": "validate",
  "input_paths": {
    "render_manifest": ".allforai/game-design/art/2-5d/renders/render-to-2d-manifest.json",
    "production_mode": ".allforai/game-design/art/2-5d/2-5d-production-mode-spec.json",
    "source_assets": ".allforai/game-design/art/2-5d/3d-source-asset-spec.json",
    "lighting_shadow": ".allforai/game-design/art/2-5d/2-5d-lighting-shadow-spec.json",
    "tool_registry": ".allforai/game-design/art/tools/production-tool-capability-registry.json",
    "view_mode": ".allforai/game-design/art/view/2d-view-mode-spec.json"
  },
  "output_root": ".allforai/game-design/art/2-5d/qa"
}
```

Supported modes: `validate`, `validate_previews`, `validate_runtime_screenshots`,
`repair_targets`.

## Automatic Validation

Check these axes when evidence exists:

- projection and camera angle match `2d-view-mode-spec`,
- render scale and pivot match `2d-layering-spec`,
- lighting direction and contact shadows match `2-5d-lighting-shadow-spec`,
- alpha/edge cleanup is suitable for atlas and runtime composition,
- helper maps have paired color assets and runtime consumers,
- render dimensions, frame grids, and atlas groups are consistent,
- style does not look like unprocessed 3D if the art direction requires 2D,
- raw 3D source paths are not included in engine-ready runtime manifests,
- Blender/render/import/probe tool evidence exists for generated 3D-assisted
  outputs,
- runtime screenshots or previews show correct visibility/sorting when available.

Severity rules:

| Severity | Meaning |
|---|---|
| `blocker` | raw 3D leaked to runtime, import blocked, or projection unusable |
| `major` | visible perspective/lighting/style defect affects gameplay readability |
| `minor` | polish issue that does not block runtime use |
| `warning` | missing evidence or risk without confirmed defect |

State progression gates:

```text
passed
  no blocker/major issues and runtime exclusion validated
passed_with_warnings
  only minor/warning issues remain
needs_revision
  projection, lighting, edge, scale, pivot, style, or helper-map issue remains
blocked_by_missing_evidence
  render previews/manifests are insufficient
blocked_by_runtime_leak
  raw 3D source appears in runtime output
blocked_by_import_validation
  target runtime import evidence is missing or failed
```

Repair routing: projection issues route to `2d-view-mode-spec` or source camera
setup; lighting/shadow issues route to `2-5d-lighting-shadow-spec`; render
quality issues route to `render-to-2d-asset-generation`; runtime leakage routes
to `engine-ready-art-output-contract`; atlas/pivot issues route to
`atlas-packaging`, `2d-layering-spec`, or `engine-export-profile`; missing or
unverified tools route to `production-tool-capability-registry`.

## Completion Conditions

Return `COMPLETED` when 3D-assisted 2D outputs pass QA and raw 3D sources are
excluded from runtime delivery. Return `FAILED_VALIDATION` when projection,
lighting, render, style, or runtime leakage blocks use. Return `UPSTREAM_DEFECT`
when required production-mode/source/render evidence is missing.
