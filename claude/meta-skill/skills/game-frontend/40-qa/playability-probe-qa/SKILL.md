# Playability Probe QA Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Runs a short automated gameplay probe beyond scene smoke: move, interact,
trigger objective feedback, collect or defeat something when applicable, and
verify the game state changes according to design contracts.

## Input Contract

Required: playable smoke test report, frontend runtime profile, scene
composition, input/camera binding, game data binding, and objective/core-loop
requirements.

Optional: level difficulty budget, save-state binding, animation/VFX binding,
audio binding, telemetry events, Playwright traces, engine logs, and expected
state probes.

## Output Contract

Writes:

- `.allforai/game-frontend/qa/playability-probe-report.json`

The report must include `probe_id`, `scene_id`, `actions`, `expected_state_changes`,
`actual_state_changes`, `objective_feedback`, `input_evidence`,
`visual_evidence`, `log_evidence`, `status`, `repair_targets`, and
`blocks_runtime`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_unrunnable_client`, `blocked_by_missing_probe`,
`failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-frontend/playability-probe-qa",
  "mode": "run",
  "input_paths": {
    "smoke_report": ".allforai/game-frontend/qa/playable-smoke-test-report.json",
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "scene_composition": ".allforai/game-frontend/bindings/scene-composition-spec.json",
    "input_camera": ".allforai/game-frontend/bindings/input-camera-binding-spec.json",
    "game_data": ".allforai/game-frontend/bindings/game-data-binding-spec.json",
    "difficulty_budget": ".allforai/game-design/levels/level-difficulty-budget-spec.json"
  },
  "output_root": ".allforai/game-frontend/qa"
}
```

Supported modes: `run`, `rerun`, `repair_targets`.

## Automatic Validation

Drive the client with configured inputs and inspect state/log/screenshot
evidence. At minimum, prove one core-loop action changes state or produces
expected feedback. If state cannot be probed, mark blocked rather than guessing
from visuals.

When a level difficulty budget is present, choose probe actions that exercise
the declared validation probe for the target scene or region. Compare observed
state changes, damage/resource changes, retry/recovery behavior, objective
feedback, and visible counterplay against the budget. If budget probes cannot
run, return `blocked_by_missing_probe`.

If the budget includes a `psychological_curve`, capture available proxy signals
for its evidence signal: time to objective, repeated failed inputs, death/retry
count, health/resource depletion, idle/backtracking time, hint/tutorial usage,
pause/menu openings, relief checkpoint reach, and feedback visibility. These
signals do not prove human emotion by themselves, but they can verify whether
the level supplies the designed pressure, recovery, and frustration-risk
conditions. Missing required psychological evidence should block the probe.

Repair routing: input failures route to input-camera binding; missing state
routes to game-data or save-state binding; visual feedback gaps route to
animation/VFX, HUD, or art QA.

## Completion Conditions

Return `COMPLETED` when a short automated interaction proves the playable loop
responds. Return `FAILED_VALIDATION` when the game only renders but cannot be
played or probed.
