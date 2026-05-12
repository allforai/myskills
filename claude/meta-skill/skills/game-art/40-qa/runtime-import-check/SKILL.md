---
name: game-art-40-qa-runtime-import-check
description: Internal bundled meta-skill module for game-art/40-qa/runtime-import-check; use within generated bootstrap node-specs when this exact contract is selected.
---

# Runtime Import Check Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Validates that generated art manifests can be consumed by the target runtime or
frontend after export. It does not implement gameplay code, but it must define
and execute, when available, an automatic import validation path for the target
engine/runtime.

## Input Contract

Required: runtime target, engine export profile, and at least one asset
manifest. Optional: `asset-registry.json`, `ui-registry.json`, atlas manifests,
tileset manifests, animation/VFX manifests, generated import manifests, engine
project path, validation commands, screenshots, scene-load logs, and importer
logs.

## Output Contract

Writes `.allforai/game-design/art/qa/runtime-import-check-report.json` with
import verdicts, missing files, invalid metadata, fallback states, and repair
targets.

Each verdict must include `artifact_id`, `manifest_path`, `runtime`,
`adapter_policy`, `validation_method`, `status`, `evidence_paths`,
`missing_files`, `invalid_fields`, `unsupported_features`, `import_errors`,
`render_errors`, `repair_target`, and `blocks_runtime`.

Allowed statuses: `import_ready`, `import_ready_with_warnings`,
`needs_revision`, `unsupported`, `missing_artifact`, `engine_unavailable`.

Allowed validation methods:

- `import_manifest_parse`
- `headless_engine_import`
- `engine_editor_import`
- `scene_load_smoke`
- `runtime_preview_render`
- `screenshot_probe`
- `adapter_dry_run`

## Invocation Contract

```json
{
  "skill": "game-art/runtime-import-check",
  "mode": "validate",
  "input_paths": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "ui_registry": ".allforai/game-design/ui/ui-registry.json",
    "engine_export_profile": ".allforai/game-design/art/export/engine-export-profile.json"
  },
  "runtime": "phaser | three | unity | godot | web | unknown",
  "manifests": [],
  "output_root": ".allforai/game-design/art"
}
```

Supported modes: `validate`, `validate_artifacts_only`, `validate_preview`,
`validate_engine_import`, `validate_scene_load`, `validate_screenshot_probe`.

## Automatic Validation

Check file existence, path roots, formats, sizes, atlas coordinates, animation
metadata, VFX configs, UI references, fallback states, and whether generated
assets are still provisional. Then run the strongest validation method allowed
by `engine-export-profile.adapter_policy` and available tools.

Validation ladder:

```text
native project/editor available
-> run engine/editor import or headless command
-> load a minimal scene/preview when possible
-> capture logs and screenshot/probe output

runtime adapter or importer available
-> run adapter dry-run/import-manifest parse
-> validate IDs, paths, pivots, atlas frames, animation events

no runtime tools available
-> return engine_unavailable or unsupported
-> do not substitute static checks as acceptance
```

Minimum engine-facing evidence:

| Method | Required evidence |
|---|---|
| `import_manifest_parse` | parser/importer log and parsed artifact count |
| `headless_engine_import` | command, exit code, log path, imported asset count |
| `engine_editor_import` | editor/import log and changed/generated import artifacts |
| `scene_load_smoke` | scene path, load result, missing refs/errors |
| `runtime_preview_render` | preview path plus dimensions/non-empty render check |
| `screenshot_probe` | screenshot path plus expected asset visibility probes |
| `adapter_dry_run` | adapter output and unsupported feature list |

Runtime-specific validation guidance:

| Runtime | Preferred automatic validation |
|---|---|
| Godot | headless import or scene load when project exists; otherwise parse generated import manifest |
| Unity | batchmode/editor import when project exists; otherwise validate import manifest and `.meta` expectations |
| Phaser/Pixi/custom web | load atlas/images in a minimal runtime or parse JSON and render preview canvas |
| Cocos/Defold/Love2D | run available importer/preview command; otherwise adapter dry-run plus static manifest |
| Unknown/custom | adapter dry-run only; if no adapter exists, return `engine_unavailable` |

Generated assets in `generated` or `preview_ready` state must not be treated as
runtime-ready. Runtime failures caused by image content route to
`image-generation-contract`; metadata failures route to the producer manifest.
Validation cannot be marked `import_ready` unless at least one engine/importer,
adapter, scene-load, render, screenshot, or manifest-parse evidence path exists.
Static checks may be included as diagnostics, but they are never sufficient for
acceptance. If no executable validation method can run, return
`engine_unavailable` and expose the missing tool/project/importer requirement.

Repair routing: engine command unavailable routes to `engine-export-profile` to
declare the missing validation capability; parse/import errors route to
`engine-export-profile` or the specific producer manifest; missing files route
to the producing skill; visibility/render failures route to
`art-preview-qa`, `2d-style-consistency-qa`, or runtime implementation depending
on root cause.

## Completion Conditions

Return `COMPLETED` when engine/importer, adapter, scene-load, render, screenshot,
or manifest-parse validation passes with no blockers. Return `FAILED_VALIDATION`
with repair targets for missing/invalid runtime artifacts, unavailable engines,
or missing executable import validation.
