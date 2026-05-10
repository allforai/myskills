# Engine-Ready Art Output Contract Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Assembles the final art delivery contract that implementation nodes can import
into a game engine or runtime. It verifies that generated art is not just
visually accepted, but has stable IDs, paths, manifests, atlas metadata,
animation clips, state machines, tile metadata, UI/icon refs, VFX configs,
pivots, anchors, sorting layers, QA status, and fallback status.

Use this as the exit boundary for `game-art` before program implementation or
engine integration consumes art assets.

## Input Contract

Required: asset registry, engine export profile, runtime import check report,
and at least one asset manifest.

Optional: atlas manifests, animation state machine spec, skeletal manifests,
frame animation manifests, tileset manifests, UI registry, VFX manifests,
2D layering spec, 2D style consistency QA report, art preview QA report,
image-generation report, and level/UI/runtime consumer requirements.

## Output Contract

Writes:

- `.allforai/game-design/art/export/engine-ready-art-output-contract.json`
- `.allforai/game-design/art/export/engine-ready-art-output-report.json`
- `.allforai/game-runtime/art/engine-ready-art-manifest.json`
- `.allforai/game-runtime/art/engine-ready-art-report.json`

The output contract must include `contract_id`, `target_runtime`,
`engine_export_profile_ref`, `adapter_policy`, `format_decisions`,
`asset_manifest_refs`, `atlas_refs`, `animation_refs`, `state_machine_refs`,
`skeleton_refs`, `tilemap_refs`, `ui_asset_refs`, `vfx_refs`, `layering_refs`,
`source_3d_refs`, `runtime_excluded_source_refs`, `import_paths`,
`runtime_ids`, `pivot_anchor_policy`, `sorting_policy`, `collision_helper_refs`,
`qa_summary`, `fallback_summary`,
`known_limitations`, `consumer_contracts`, `state`, and `validation`.

`engine-ready-art-manifest.json` is the program/frontend-facing subset consumed
by runtime and client implementation nodes. It must include `manifest_id`,
`target_runtime`, `engine_profile_ref`, `adapter_policy`,
`format_decisions_ref`, `source_contract_ref`, `runtime_assets`,
`atlas_manifests`, `animation_manifests`, `tilemap_manifests`, `ui_manifests`,
`vfx_manifests`, `import_validation_ref`, `known_limitations`, `state`, and
`validation`.

Engine-specific differences are represented through `engine_profile_ref`,
`adapter_policy`, and concrete manifest refs, not by changing this common
manifest schema. Frontend/runtime consumers adapt from the common manifest into
their local loader/import format.

Asset entries must include:

```json
{
  "asset_id": "player",
  "runtime_id": "art/player",
  "kind": "character | tileset | background | prop | icon | ui | vfx | audio_visual_ref",
  "paths": [],
  "engine_profile_ref": ".allforai/game-design/art/export/engine-export-profile.json",
  "adapter_policy": "profile_only | generate_import_manifest | run_importer | native_project_edit",
  "format_decision_refs": [],
  "manifest_refs": [],
  "atlas_ref": null,
  "frontend_binding_hints": [],
  "engine_import_hints": [],
  "pivot": {"x": 0.5, "y": 1.0, "space": "normalized"},
  "sorting_layer": "actors",
  "animation_refs": [],
  "state_machine_ref": null,
  "qa_status": "passed | passed_with_warnings | failed | placeholder",
  "fallback_status": "none | simplified | placeholder | disabled",
  "consumer_refs": []
}
```

Allowed states: `draft`, `engine_ready`, `engine_ready_with_limits`,
`needs_revision`, `blocked_by_missing_assets`, `blocked_by_runtime_import`,
`blocked_by_qa`.

Downstream consumers: runtime implementation, engine import scripts, level
implementation, UI implementation, animation controllers, VFX runtime,
playtest QA, build verification, and product/demo verification.

## Invocation Contract

```json
{
  "skill": "game-art/engine-ready-art-output-contract",
  "mode": "assemble_validate",
  "input_paths": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "engine_export_profile": ".allforai/game-design/art/export/engine-export-profile.json",
    "runtime_import_report": ".allforai/game-design/art/qa/runtime-import-check-report.json"
  },
  "output_root": ".allforai/game-design/art/export"
}
```

Supported modes: `assemble_validate`, `validate_existing`,
`repair_contract_refs`, `consumer_summary`.

## Automatic Validation

Check that every engine-facing asset has stable ID, runtime ID, file path,
manifest ref, QA status, fallback status, and consumer refs. No asset may be
marked `engine_ready` if required preview QA, style QA, atlas packaging, or
runtime import checks failed.

Readiness gates:

| Gate | Required evidence |
|---|---|
| registry | every asset has stable `asset_id` and `file_prefix` |
| paths | every path exists or is explicitly placeholder/disabled |
| atlas | packed assets have atlas metadata, padding, pivot, and trim policy |
| animation | clips/state machines preserve event frames and fallback states |
| tiles | tile IDs, collision, walkability, and preview maps are present |
| layers | sorting, occlusion, UI/world separation, and swap layers resolve |
| 3D source exclusion | production-only 3D sources are not runtime assets |
| 3D-assisted QA | 3D-derived 2D assets pass projection, lighting, pivot, edge, and runtime-leak checks |
| runtime | runtime import report has no blocker/major issue |
| QA | visual/style/readability QA blockers are closed or downgraded with limits |
| adapter | engine profile can be consumed without undocumented native mutations |
| format decisions | concrete formats are recorded, justified, and validated |
| import evidence | runtime import report includes evidence paths and validation method |
| common manifest | engine profile ref, adapter policy, runtime IDs, format refs, and import validation refs are present |

State progression gates:

```text
draft
-> engine_ready                 all required gates pass and no blocker/major QA
-> engine_ready_with_limits     placeholders or simplified fallbacks are declared
-> needs_revision               manifest refs, QA, atlas, or runtime IDs conflict
-> blocked_by_missing_assets    required generated/registered assets are absent
-> blocked_by_runtime_import    import validation failed
-> blocked_by_qa                art/style/readability QA blockers remain
```

`engine_ready` requires executable import evidence. Static metadata checks do
not count. If the target engine, importer, adapter, scene load, preview render,
or screenshot probe cannot run, this contract must return
`blocked_by_runtime_import` rather than accepting a fallback.

Repair routing: missing IDs route to `asset-registry`; missing generated art
routes to the producing skill; missing atlas metadata routes to
`atlas-packaging`; failed import routes to `runtime-import-check` or
`engine-export-profile`; animation runtime defects route to
`animation-state-machine-spec`; layer/sorting defects route to
`2d-layering-spec`; visual blockers route to `art-preview-qa` or
`2d-style-consistency-qa`; unsupported native engine edits route back to
`engine-export-profile` to either downgrade to manifest-only output or require a
future engine-specific adapter.

For 3D-assisted production, raw 3D source assets must appear only in
`source_3d_refs` or `runtime_excluded_source_refs`. They must not appear in
`asset_manifest_refs`, `import_paths`, or runtime consumer contracts unless
`2-5d-production-mode-spec.runtime_art_mode` explicitly allows hybrid runtime
and executable import validation passed.

This skill must not require a universal engine-specific schema. It verifies that
the LLM-selected output format is explicit, internally consistent, referenced by
consumers, and covered by runtime validation. If the format cannot be validated,
return `needs_revision` or `blocked_by_runtime_import` rather than inventing a
fake engine import result.

Before completion, verify that every program/frontend-facing runtime asset can
be converted by the declared adapter policy:

- `profile_only` requires a documented loader/import mapping and manifest parse
  evidence.
- `generate_import_manifest` requires a generated manifest path and parser or
  adapter dry-run evidence.
- `run_importer` requires command, exit code, logs, and imported artifact refs.
- `native_project_edit` requires exact project files, owning implementation
  node, and executable engine validation.

## Completion Conditions

Return `COMPLETED` when the output contract is `engine_ready` or
`engine_ready_with_limits` and every limitation is explicit. Return
`FAILED_VALIDATION` when required runtime consumers cannot safely import the art
package. Return `UPSTREAM_DEFECT` when upstream manifests are missing enough
information that this contract cannot assemble.
