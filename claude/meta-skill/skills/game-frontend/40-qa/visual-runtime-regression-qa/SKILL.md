# Visual Runtime Regression QA Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Validates runtime screenshots and probes against expected scene composition,
asset visibility, HUD placement, layer order, scale, animation/VFX readability,
and known baseline screenshots.

## Input Contract

Required: playable smoke test report, scene composition spec, asset import
bindings, HUD/UI binding, and screenshot/probe evidence.

Optional: previous baseline screenshots, art QA reports, style consistency QA,
runtime import report, Playwright traces, and viewport matrix.

## Output Contract

Writes:

- `.allforai/game-frontend/qa/visual-runtime-regression-report.json`

Findings must include `finding_id`, `scene_id`, `viewport`, `expected`,
`actual`, `evidence_path`, `severity`, `root_cause`, `repair_target`,
`blocks_runtime`, and `state`.

Allowed states: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_screenshot`, `failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-frontend/visual-runtime-regression-qa",
  "mode": "validate",
  "input_paths": {
    "smoke_report": ".allforai/game-frontend/qa/playable-smoke-test-report.json",
    "scene_composition": ".allforai/game-frontend/bindings/scene-composition-spec.json",
    "asset_bindings": ".allforai/game-frontend/bindings/asset-import-binding-spec.json",
    "hud_ui": ".allforai/game-frontend/bindings/hud-ui-binding-spec.json"
  },
  "output_root": ".allforai/game-frontend/qa"
}
```

Supported modes: `validate`, `compare_baseline`, `repair_targets`.

## Automatic Validation

Check screenshots for blank canvas, missing assets, wrong layer order,
incorrect scale/pivot, HUD overlap, cropped text, unreadable VFX, missing
animation state, and responsive viewport issues. Use pixel/canvas probes when
available.

Repair routing: missing assets route to asset import binding; visual asset
defects route to game-art QA; layout/HUD defects route to HUD/UI binding or
game-ui; scene/camera defects route to scene composition or input-camera
binding.

## Completion Conditions

Return `COMPLETED` when runtime visuals match the declared scene and UI
contracts. Return `FAILED_VALIDATION` when screenshots/probes are missing or
show blocking visual regressions.
