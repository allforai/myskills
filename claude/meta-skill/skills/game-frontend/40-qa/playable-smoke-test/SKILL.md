---
name: game-frontend-40-qa-playable-smoke-test
description: Internal bundled meta-skill module for game-frontend/40-qa/playable-smoke-test; use within generated bootstrap node-specs when this exact contract is selected.
---

# Playable Smoke Test Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Runs the assembled client and validates that a playable scene loads, assets are
visible, input works, camera moves or frames correctly, HUD renders, animation
or VFX triggers, and logs contain no blocking runtime errors.

## Input Contract

Required: frontend runtime profile, playable client assembly report, scene
composition spec, input/camera binding, HUD/UI binding, animation/VFX binding,
and asset import bindings.

Optional: Playwright config, engine CLI, screenshot probes, expected pixel
regions, dev server URL, and smoke route.

## Output Contract

Writes:

- `.allforai/game-frontend/qa/playable-smoke-test-report.json`
- `.allforai/game-frontend/qa/playable-smoke-test-screenshot.png` when screenshots are available

The report must include `test_id`, `command`, `url_or_scene`, `actions`,
`status`, `log_evidence`, `screenshot_evidence`, `asset_visibility`,
`input_result`, `camera_result`, `hud_result`, `animation_vfx_result`,
`errors`, `repair_targets`, and `blocks_runtime`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_unrunnable_client`, `blocked_by_missing_tools`,
`failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-frontend/playable-smoke-test",
  "mode": "run",
  "input_paths": {
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "assembly_report": ".allforai/game-frontend/assembly/playable-client-assembly-report.json",
    "scene_composition": ".allforai/game-frontend/bindings/scene-composition-spec.json"
  },
  "output_root": ".allforai/game-frontend/qa"
}
```

Supported modes: `run`, `rerun`, `repair_targets`.

## Automatic Validation

Start the dev server or engine command when available, navigate/load the smoke
scene, perform configured input actions, collect logs, and capture screenshots.
Check that expected assets and HUD elements are visible and that at least one
core input path changes game state or camera state.

Smoke status must not pass from canvas existence alone. The screenshot evidence
must prove the loaded scene is the production smoke scene, not a prototype/debug
scene. If the visible output is pure-color blocks, a black debug background,
generic geometric placeholders, missing HUD, or a sample/prototype component,
return `failed_validation` and route repair to scene-flow, playable client
assembly, asset import binding, or frontend code assembly.

If the client cannot run, return `blocked_by_unrunnable_client`. Do not replace
runtime evidence with source-code inspection.

## Completion Conditions

Return `COMPLETED` when the smoke test passes or only non-blocking warnings
remain. Return `FAILED_VALIDATION` when the client cannot load, render, respond,
or produce required evidence.
