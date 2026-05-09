# Runtime Import Check Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Validates that generated art manifests can be consumed by the target runtime or
frontend. It does not implement runtime code; it checks paths, formats,
metadata, and preview/import evidence.

## Input Contract

Required: runtime target and at least one asset manifest. Optional:
`asset-registry.json`, `ui-registry.json`, atlas manifests, tileset manifests,
animation/VFX manifests, screenshots.

## Output Contract

Writes `.allforai/game-design/art/qa/runtime-import-check-report.json` with
import verdicts, missing files, invalid metadata, fallback states, and repair
targets.

Each verdict must include `artifact_id`, `manifest_path`, `runtime`, `status`,
`missing_files`, `invalid_fields`, `unsupported_features`, `repair_target`, and
`blocks_runtime`.

Allowed statuses: `import_ready`, `import_ready_with_warnings`,
`needs_revision`, `unsupported`, `missing_artifact`.

## Invocation Contract

```json
{
  "skill": "game-art/runtime-import-check",
  "mode": "validate",
  "input_paths": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "ui_registry": ".allforai/game-design/ui/ui-registry.json"
  },
  "runtime": "phaser | three | unity | godot | web | unknown",
  "manifests": [],
  "output_root": ".allforai/game-design/art"
}
```

Supported modes: `validate`, `validate_artifacts_only`, `validate_preview`.

## Automatic Validation

Check file existence, path roots, formats, sizes, atlas coordinates, animation
metadata, VFX configs, UI references, fallback states, and whether generated
assets are still provisional.

Generated assets in `generated` or `preview_ready` state must not be treated as
runtime-ready. Runtime failures caused by image content route to
`image-generation-contract`; metadata failures route to the producer manifest.

## Completion Conditions

Return `COMPLETED` when import checks pass or only warnings remain. Return
`FAILED_VALIDATION` with repair targets for missing/invalid runtime artifacts.
