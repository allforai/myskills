# 2.5D Production Mode Spec Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Defines whether and how a game uses 3D-assisted production while shipping a 2D
runtime. It decides which assets are produced from 3D sources, which remain
native 2D, which render passes are needed, and which artifacts are allowed to
enter the final engine-ready output.

Use this after `art-direction-input-contract`, `2d-view-mode-spec`, and
`2d-layering-spec` when a project needs 3D blockouts, models, lighting rigs, or
rendered angles to produce 2D sprites, tiles, props, backgrounds, icons, or
helper maps.

## Input Contract

Required: art direction input contract, production tool capability registry, 2D
view mode, target runtime, and asset list or asset registry.

Optional: visual style tokens, 2D layering spec, engine export profile, level
layout, character animation plan, performance budget, available 3D tools, and
human preferences about 2D/3D look.

## Output Contract

Writes:

- `.allforai/game-design/art/2-5d/2-5d-production-mode-spec.json`
- `.allforai/game-design/art/2-5d/2-5d-production-mode-report.json`

The spec must include `mode_id`, `runtime_art_mode`, `source_3d_policy`,
`asset_selection`, `render_strategy`, `pass_requirements`,
`angle_requirements`, `style_integration_rules`, `runtime_exclusion_rules`,
`downstream_skill_refs`, `qa_requirements`, `state`, and `consumer_refs`.

Allowed `runtime_art_mode` values: `2d_only`, `2d_with_baked_3d`,
`2d_with_helper_maps`, `hybrid_runtime_allowed`.

Allowed `source_3d_policy` values: `production_source_only`,
`runtime_excluded`, `runtime_optional`, `runtime_allowed_with_explicit_contract`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_view_mode`, `blocked_by_runtime`, `blocked_by_tooling`.

Downstream consumers: `3d-source-asset-spec`, `2-5d-lighting-shadow-spec`,
`render-to-2d-asset-generation`, `2d-layering-spec`, `engine-export-profile`,
`3d-assisted-2d-qa`, `runtime-import-check`, and
`engine-ready-art-output-contract`.

## Invocation Contract

```json
{
  "skill": "game-art/2-5d-production-mode-spec",
  "mode": "spec_validate",
  "input_paths": {
    "art_direction": ".allforai/game-design/art/art-direction-input-contract.json",
    "view_mode": ".allforai/game-design/art/view/2d-view-mode-spec.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "engine_export_profile": ".allforai/game-design/art/export/engine-export-profile.json"
  },
  "output_root": ".allforai/game-design/art/2-5d"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every 3D-assisted asset has a final 2D output type, render strategy,
required tool capability, runtime exclusion rule, QA route, and import
validation route. The spec must not mark raw 3D source files as runtime-ready
unless `runtime_art_mode` explicitly allows hybrid runtime and the engine-ready
output contract names the consumer.

Decision rules:

| Asset need | Recommended mode |
|---|---|
| isometric buildings or props with consistent angle | 3D source -> 2D render |
| many costume/item preview angles | 3D source -> 2D turntable renders |
| side-view characters with 2D runtime | 3D pose/blockout -> 2D sprite reference or bake |
| background plates with depth consistency | 3D blockout -> painted/rendered 2D background |
| dynamic runtime lighting required | 2D with helper maps only if engine supports them |
| simple hand-drawn/pixel assets | native 2D, no 3D source |

State progression gates:

```text
draft
-> validated                    each selected asset has source policy and final 2D output
-> needs_revision               3D/runtime boundary, angle, or output policy conflicts
-> blocked_by_view_mode         camera/projection is not defined
-> blocked_by_runtime           target runtime cannot consume required helper maps/imports
-> blocked_by_tooling           required 3D render/bake tooling is unavailable
```

Repair routing: ambiguous spatial projection returns to `2d-view-mode-spec`;
layer/sorting conflicts return to `2d-layering-spec`; missing runtime support
returns to `engine-export-profile`; missing source decisions repair here; source
asset details route to `3d-source-asset-spec`; missing tools route to
`production-tool-capability-registry`.

## Completion Conditions

Return `COMPLETED` when all 3D-assisted assets have source policy, final 2D
outputs, QA, and runtime import validation routes. Return `FAILED_VALIDATION`
when 3D source and 2D runtime boundaries are ambiguous. Return `UPSTREAM_DEFECT`
when view mode, runtime, or asset list cannot be resolved.
