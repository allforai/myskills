---
name: game-2d-runtime-profile
description: Detect the runnable 2D game environment, commands, viewport, platform target, and automation surface before 2D production assembly.
---

# Runtime Profile

## Input Contract

Read `.allforai/bootstrap/bootstrap-profile.json`, package/build files, engine
configuration, and `.allforai/game-design/design/program-development-node-handoff.json`.

## Output Contract

Write `.allforai/game-2d/env/2d-runtime-profile.json` with:

- `runtime_kind`: `browser_canvas | cocos | phaser | unity_2d | godot_2d | native_2d | custom`
- `run_command`, `build_command`, `test_command`, `screenshot_command`
- `viewport_matrix` for desktop and mobile sizes
- `automation_surface`: Playwright, engine test runner, simulator, or custom CLI
- `can_run`: boolean
- `blocking_status` when runtime evidence cannot be produced.

## Invocation Contract

Run before any 2D assembly or QA. Do not install global tools or create symlinks.
Use project-local commands when available.

```json
{
  "skill": "game-2d-production/00-env/runtime-profile",
  "mode": "detect_runtime",
  "input_paths": [
    ".allforai/bootstrap/bootstrap-profile.json",
    ".allforai/game-design/design/program-development-node-handoff.json"
  ],
  "output_root": ".allforai/game-2d/env"
}
```

## Automatic Validation

Execute the configured run/build smoke path when possible. If no runtime command
exists, emit `blocked_by_missing_runtime_command`; if the client cannot start,
emit `blocked_by_unrunnable_client`.

## Completion Conditions

Complete when the report names the exact command that downstream QA can run, or
when it blocks with a concrete reason.
