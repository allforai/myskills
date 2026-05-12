---
name: game-frontend-20-spec-game-state-model-spec
description: Internal bundled meta-skill module for game-frontend/20-spec/game-state-model-spec; use within generated bootstrap node-specs when a game client needs runtime state, scene state, gameplay state, UI state, save state, and probeable state transitions before implementation.
---

# Game State Model Spec Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the frontend game state model: boot state, scene state, in-level state,
meta progression state, UI modal state, settings/save state, transient effect
state, and probeable transitions. This spec is the reference for implementation
and automated playability probes.

## Input Contract

Required: runtime architecture design, game design doc, frontend runtime
profile, and core-loop/objective requirements.

Optional: level specs, progression/economy specs, save-state binding,
UI registry, backend schema, telemetry events, existing store/state code, and
game templates.

## Output Contract

Writes:

- `.allforai/game-frontend/bindings/game-state-model-spec.json`
- `.allforai/game-frontend/bindings/game-state-model-report.json`

The state model must include `state_id`, `state_kind`, `owner_module`,
`source_contract`, `schema`, `initial_value`, `allowed_transitions`,
`mutation_events`, `derived_selectors`, `persistence_policy`,
`reset_policy`, `probe_points`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_missing_game_contract`, `blocked_by_runtime_profile`,
`blocked_by_unprobeable_state`.

## Invocation Contract

```json
{
  "skill": "game-frontend/game-state-model-spec",
  "mode": "spec_validate",
  "input_paths": {
    "runtime_architecture": ".allforai/game-frontend/design/runtime-architecture-design.json",
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json"
  },
  "output_root": ".allforai/game-frontend/bindings"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Every state entry must have an owner module and at least one probeable
transition. Persistent state must reference save-state binding or declare why it
is local-only/transient. UI state must not own gameplay truth. Gameplay state
must not be inferred only from visuals when a probe is required.

Repair routing: missing state requirements route to game design or system
specs; missing persistence routes to save-state binding; unprobeable state
routes to playable-client-assembly or diagnostics hooks.

## Completion Conditions

Return `COMPLETED` when all required frontend state has schema, ownership,
transitions, and probes. Return `FAILED_VALIDATION` when state is missing,
ambiguous, or cannot be observed by automated QA.
