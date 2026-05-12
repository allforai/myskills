---
name: game-frontend-40-qa-runtime-architecture-qa
description: Internal bundled meta-skill module for game-frontend/40-qa/runtime-architecture-qa; use within generated bootstrap node-specs when a game client needs automatic validation that frontend architecture, state, scenes, loading, systems, and probes are mutually consistent.
---

# Runtime Architecture QA Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Validates that frontend architecture contracts are coherent before or after
client assembly. It checks architecture, state model, scene flow, scene
composition, asset loading, gameplay bindings, save, UI, VFX, audio, and
performance budgets as a graph.

## Input Contract

Required: runtime architecture design, frontend runtime profile, game state
model, scene flow, scene composition, game data binding, gameplay system
binding, asset loading strategy, and performance budget.

Optional: playable assembly report, smoke test report, runtime logs, screenshots,
existing project structure, and project-local `*-frontend-runtime` specialized
skill outputs.

## Output Contract

Writes:

- `.allforai/game-frontend/qa/runtime-architecture-qa-report.json`

Findings must include `finding_id`, `severity`, `contract_ref`,
`missing_or_conflicting_ref`, `runtime_impact`, `repair_target`,
`blocks_assembly`, `blocks_smoke`, and `state`.

Allowed states: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_contract`, `failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-frontend/runtime-architecture-qa",
  "mode": "validate",
  "input_paths": {
    "runtime_architecture": ".allforai/game-frontend/design/runtime-architecture-design.json",
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "game_state_model": ".allforai/game-frontend/bindings/game-state-model-spec.json",
    "scene_flow": ".allforai/game-frontend/bindings/scene-flow-spec.json",
    "gameplay_systems": ".allforai/game-frontend/bindings/gameplay-system-binding-spec.json",
    "asset_loading": ".allforai/game-frontend/bindings/asset-loading-strategy-spec.json",
    "performance_budget": ".allforai/game-frontend/bindings/performance-budget-spec.json"
  },
  "output_root": ".allforai/game-frontend/qa"
}
```

Supported modes: `validate`, `validate_after_assembly`, `repair_targets`.

## Automatic Validation

Check graph closure:

- every module in runtime architecture has at least one downstream spec or is
  explicitly disabled for the milestone;
- every scene flow target has scene composition and state transfer;
- every gameplay binding mutates or reads declared game state;
- every asset loading group references asset import bindings;
- every UI/VFX/audio feedback path points to a gameplay or scene event;
- every save state has a reset/load probe;
- every blocking performance budget has a measurement method;
- smoke and playability probes can reach the declared core loop.
- project-local frontend runtime specialization exists when runtime
  architecture declares `specialization_required=true`.

If a runnable client exists, use actual project structure, build output, logs,
or screenshots as evidence. If it cannot run, do not substitute static review
for runtime evidence; return a blocked state.

## Completion Conditions

Return `COMPLETED` when architecture contracts are closed and ready for assembly
or smoke QA. Return `FAILED_VALIDATION` when required contracts are missing,
contradictory, or untestable.
