---
name: game-frontend-20-spec-gameplay-system-binding-spec
description: Internal bundled meta-skill module for game-frontend/20-spec/gameplay-system-binding-spec; use within generated bootstrap node-specs when a game client needs design rules, levels, economy, items, abilities, objectives, and templates bound to frontend runtime systems.
---

# Gameplay System Binding Spec Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Maps product/game design systems into frontend runtime systems. It binds rules,
levels, objectives, puzzle/combat mechanics, item/economy/progression data,
templates, rewards, and failure/retry loops to code modules and probes.

## Input Contract

Required: runtime architecture design, game state model, game data binding, game
design doc, and at least one gameplay system spec.

Optional: level specs, difficulty budget, puzzle/combat specs, economy model,
progression curve, templates, backend schema, UI/HUD binding, and existing
gameplay code.

## Output Contract

Writes:

- `.allforai/game-frontend/bindings/gameplay-system-binding-spec.json`
- `.allforai/game-frontend/bindings/gameplay-system-binding-report.json`

System bindings must include `system_id`, `source_contract`,
`frontend_module`, `data_refs`, `state_refs`, `event_inputs`,
`event_outputs`, `ui_feedback_refs`, `asset_feedback_refs`,
`audio_feedback_refs`, `validation_probe`, `fallback_or_disabled_policy`,
`state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_missing_design_system`, `blocked_by_missing_data_binding`,
`blocked_by_unprobeable_system`.

## Invocation Contract

```json
{
  "skill": "game-frontend/gameplay-system-binding-spec",
  "mode": "spec_validate",
  "input_paths": {
    "runtime_architecture": ".allforai/game-frontend/design/runtime-architecture-design.json",
    "game_state_model": ".allforai/game-frontend/bindings/game-state-model-spec.json",
    "game_data": ".allforai/game-frontend/bindings/game-data-binding-spec.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json"
  },
  "output_root": ".allforai/game-frontend/bindings"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Every core-loop system must be bound to a frontend module, data source, state
mutation, feedback route, and automated probe. Systems that are planned but not
implemented for the current milestone must have an explicit disabled policy and
must not appear as working UI.

Repair routing: missing gameplay contracts route to game-design/game-level;
missing data routes to game-data-binding-spec; missing feedback routes to
HUD/UI, animation/VFX, audio, or asset bindings; unprobeable modules route to
playable-client-assembly.

## Completion Conditions

Return `COMPLETED` when all milestone gameplay systems have bindings and probes.
Return `FAILED_VALIDATION` when gameplay rules cannot be traced into frontend
modules or automated playability probes.
