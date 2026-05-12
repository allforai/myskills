---
name: game-frontend-20-spec-input-camera-binding-spec
description: Internal bundled meta-skill module for game-frontend/20-spec/input-camera-binding-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Input Camera Binding Spec Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Defines frontend input and camera binding: keyboard/touch/gamepad controls,
camera follow/framing, viewport constraints, dead zones, zoom, shake limits,
and smoke-test actions.

## Input Contract

Required: player experience contract or game design doc, frontend runtime
profile, scene composition spec, and target platform constraints.

Optional: level layout, combat/mechanics specs, accessibility constraints,
existing input code, and camera runtime notes.

## Output Contract

Writes:

- `.allforai/game-frontend/bindings/input-camera-binding-spec.json`
- `.allforai/game-frontend/bindings/input-camera-binding-report.json`

Bindings must include `control_scheme_id`, `platform`, `actions`,
`input_sources`, `camera_mode`, `follow_target`, `bounds_ref`, `viewport_rule`,
`zoom_rule`, `shake_rule`, `accessibility_limits`, `smoke_inputs`,
`validation_probe`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_player_contract`, `blocked_by_scene_composition`,
`blocked_by_platform`.

## Invocation Contract

```json
{
  "skill": "game-frontend/input-camera-binding-spec",
  "mode": "spec_validate",
  "input_paths": {
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "scene_composition": ".allforai/game-frontend/bindings/scene-composition-spec.json"
  },
  "output_root": ".allforai/game-frontend/bindings"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every primary action has an input, every playable scene has camera
behavior, and every smoke test can drive the client without human input. Camera
must preserve gameplay readability and not violate accessibility constraints.

Repair routing: missing actions route to core loop/mechanics; missing bounds
route to scene composition or level layout; platform conflicts route to player
experience contract.

## Completion Conditions

Return `COMPLETED` when input and camera can be bound and automated. Return
`FAILED_VALIDATION` when core play cannot be controlled or viewed in smoke
tests.
