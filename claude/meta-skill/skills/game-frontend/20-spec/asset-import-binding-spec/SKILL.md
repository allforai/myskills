# Asset Import Binding Spec Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Maps engine-ready art manifest entries into frontend loader keys, runtime IDs,
atlas frames, animation frames, tilemap references, UI/icon refs, VFX configs,
fallbacks, and file existence checks.

## Input Contract

Required: frontend runtime profile,
`.allforai/game-runtime/art/engine-ready-art-manifest.json`,
`.allforai/game-design/art/export/engine-export-profile.json`, and
`.allforai/game-design/art/qa/runtime-import-check-report.json`.

Optional: asset registry, atlas manifests, animation manifests, UI registry,
VFX manifests, level specs, generated import manifests, runtime adapter output,
and existing frontend asset loader code.

## Output Contract

Writes:

- `.allforai/game-frontend/bindings/asset-import-binding-spec.json`
- `.allforai/game-frontend/bindings/asset-import-binding-report.json`

Bindings must include `binding_id`, `asset_id`, `runtime_id`, `frontend_key`,
`asset_kind`, `source_paths`, `manifest_refs`, `atlas_frame_refs`,
`animation_refs`, `tilemap_refs`, `ui_refs`, `vfx_refs`, `fallback_status`,
`target_runtime`, `engine_profile_ref`, `adapter_policy`,
`format_decision_refs`, `loader_target`, `validation_probe`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_missing_manifest`, `blocked_by_missing_file`,
`blocked_by_runtime_profile`, `blocked_by_import_validation`.

## Invocation Contract

```json
{
  "skill": "game-frontend/asset-import-binding-spec",
  "mode": "spec_validate",
  "input_paths": {
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "engine_ready_art": ".allforai/game-runtime/art/engine-ready-art-manifest.json",
    "engine_export_profile": ".allforai/game-design/art/export/engine-export-profile.json",
    "runtime_import_report": ".allforai/game-design/art/qa/runtime-import-check-report.json"
  },
  "output_root": ".allforai/game-frontend/bindings"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every required frontend-visible asset has a loader key, runtime ID,
file path, manifest reference, engine profile ref, adapter policy, fallback
policy, and validation probe. File paths must exist unless the manifest
explicitly marks the asset as placeholder or disabled. Hardcoded raw paths
without manifest refs are invalid.

Engine/profile compatibility checks:

- `engine-ready-art-manifest.target_runtime` must match
  `frontend-runtime-profile.runtime_family` or have an explicit adapter.
- `engine-ready-art-manifest.engine_profile_ref` must resolve to the selected
  `engine-export-profile`.
- `adapter_policy` must be one of the profile's allowed policies.
- `format_decisions` must provide enough atlas, animation, tilemap, UI, and VFX
  metadata for the frontend loader.
- `runtime_import_report` must include executable import/parse/render evidence
  for the chosen profile and adapter policy.
- If import evidence is `engine_unavailable`, `unsupported`, or missing, return
  `blocked_by_import_validation`; do not bind assets as runtime-ready.

Repair routing: missing art routes to `game-art/engine-ready-art-output-contract`;
engine/profile mismatch routes to `game-art/engine-export-profile`; loader
ambiguity routes to `frontend-runtime-detection`; atlas/frame issues route to
`game-art/atlas-packaging` or the producing art skill.

## Completion Conditions

Return `COMPLETED` when all client-visible assets are bound to frontend loader
keys and validation probes. Return `FAILED_VALIDATION` when a required asset
cannot be imported, found, or traced to the engine-ready manifest.
