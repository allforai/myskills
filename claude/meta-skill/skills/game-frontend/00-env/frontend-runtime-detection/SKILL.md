# Frontend Runtime Detection Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Detects the playable client stack, runnable commands, asset loader surface,
browser/engine test tools, and strongest available validation method before
frontend binding or assembly work starts.

## Input Contract

Required: project root and available package/project files.

Optional: program development handoff, target runtime, engine export profile,
engine-ready art manifest, existing dev server command, test command,
Playwright/browser tooling, engine CLI, and build logs.

## Output Contract

Writes:

- `.allforai/game-frontend/env/frontend-runtime-profile.json`
- `.allforai/game-frontend/env/frontend-runtime-detection-report.json`

The profile must include `runtime_id`, `runtime_family`, `framework`,
`project_root`, `entrypoints`, `asset_roots`, `loader_patterns`,
`engine_profile_refs`, `adapter_capabilities`, `dev_server_command`,
`build_command`, `test_command`, `smoke_test_surface`, `screenshot_method`,
`log_capture_method`, `available_tools`, `missing_tools`,
`validation_strength`, `state`, and `consumer_refs`.

Allowed states: `detected`, `detected_with_limits`, `needs_revision`,
`blocked_by_missing_project`, `blocked_by_missing_runtime`,
`blocked_by_missing_validation_tool`.

## Invocation Contract

```json
{
  "skill": "game-frontend/frontend-runtime-detection",
  "mode": "detect",
  "input_paths": {
    "program_handoff": ".allforai/game-design/design/program-development-node-handoff.json",
    "engine_ready_art": ".allforai/game-runtime/art/engine-ready-art-manifest.json",
    "engine_export_profile": ".allforai/game-design/art/export/engine-export-profile.json"
  },
  "output_root": ".allforai/game-frontend/env"
}
```

Supported modes: `detect`, `validate_existing`, `repair_profile`.

## Automatic Validation

Check for package/project files, runnable commands, client entrypoints, asset
roots, loader conventions, browser/engine launch path, log capture, and
screenshot/probe capability. Prefer actual command probing when possible.

Also check whether the detected client can consume the selected engine export
profile directly or needs an adapter. Record supported adapter policies for the
client stack. If the art manifest target runtime conflicts with the detected
frontend runtime and no adapter is available, return `blocked_by_missing_runtime`.

If the frontend cannot be run or no validation surface exists, return a
blocking state. Do not accept static source inspection as proof of playability.

## Completion Conditions

Return `COMPLETED` when the client stack and strongest runnable validation path
are known. Return `FAILED_VALIDATION` when no playable frontend or validation
surface can be identified.
