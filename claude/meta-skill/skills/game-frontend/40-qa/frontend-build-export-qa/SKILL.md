# Frontend Build Export QA Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Validates the production build/export path for the playable client: build
command, output directory, asset references, base path, cache/bundle layout,
runtime launch from built output, and final smoke evidence.

## Input Contract

Required: frontend runtime profile, playable assembly report, asset import
bindings, and build/export command.

Optional: smoke test report, performance report, deployment target, static
server command, engine export output, and CI logs.

## Output Contract

Writes:

- `.allforai/game-frontend/qa/frontend-build-export-report.json`

The report must include `build_id`, `build_command`, `exit_code`,
`output_path`, `artifact_count`, `asset_reference_check`, `launch_check`,
`smoke_evidence`, `errors`, `repair_targets`, `status`, and `blocks_release`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_build_command`, `blocked_by_unlaunchable_build`,
`failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-frontend/frontend-build-export-qa",
  "mode": "validate",
  "input_paths": {
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "assembly_report": ".allforai/game-frontend/assembly/playable-client-assembly-report.json",
    "asset_bindings": ".allforai/game-frontend/bindings/asset-import-binding-spec.json"
  },
  "output_root": ".allforai/game-frontend/qa"
}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Run the declared production build/export command when available. Then validate
output files, asset references, and launch the built output through the strongest
available static server or engine launch path. If the build cannot run, return a
blocking status.

Repair routing: missing command routes to frontend runtime detection; asset path
failures route to asset import binding; build/runtime errors route to changed
frontend files and assembly report.

## Completion Conditions

Return `COMPLETED` when the production build exists and launches. Return
`FAILED_VALIDATION` when build/export is missing, broken, or unlaunchable.
