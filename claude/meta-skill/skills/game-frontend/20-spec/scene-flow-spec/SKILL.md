---
name: game-frontend-20-spec-scene-flow-spec
description: Internal bundled meta-skill module for game-frontend/20-spec/scene-flow-spec; use within generated bootstrap node-specs when a game client needs scene routing, screen transitions, entry/exit conditions, loading states, and automated navigation probes.
---

# Scene Flow Spec Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Defines how the frontend moves between boot, menu, map, gameplay, result,
shop, settings, narrative, loading, and error/retry scenes. Scene composition
decides what appears inside a scene; this skill decides how scenes are entered,
exited, restored, and probed.

## Input Contract

Required: runtime architecture design, game state model, game design doc, and
frontend runtime profile.

Optional: UI flow design, level selection/progression specs, monetization/shop
specs, save-state binding, backend availability, and existing router/scene code.

## Output Contract

Writes:

- `.allforai/game-frontend/bindings/scene-flow-spec.json`
- `.allforai/game-frontend/bindings/scene-flow-report.json`

Flow entries must include `flow_id`, `from_scene`, `to_scene`,
`trigger_event`, `preconditions`, `loading_policy`, `transition_effect`,
`state_transfer`, `failure_route`, `restore_policy`, `analytics_or_probe`,
`validation_actions`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_missing_scene`, `blocked_by_state_model`,
`blocked_by_runtime_profile`.

## Invocation Contract

```json
{
  "skill": "game-frontend/scene-flow-spec",
  "mode": "spec_validate",
  "input_paths": {
    "runtime_architecture": ".allforai/game-frontend/design/runtime-architecture-design.json",
    "game_state_model": ".allforai/game-frontend/bindings/game-state-model-spec.json",
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json"
  },
  "output_root": ".allforai/game-frontend/bindings"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Every required scene must be reachable from boot or a declared restore route.
Every transition must have a trigger, precondition, target state mutation, and
automated navigation probe. Loading and error states must be explicit when
assets, network, or save data can delay entry.

Repair routing: missing scene content routes to scene-composition-spec; missing
state routes to game-state-model-spec; missing UI route affordances route to
hud-ui-binding-spec or UI flow design.

## Completion Conditions

Return `COMPLETED` when all required scenes and routes are reachable and
probeable. Return `FAILED_VALIDATION` when the frontend cannot navigate through
the designed loop automatically.
