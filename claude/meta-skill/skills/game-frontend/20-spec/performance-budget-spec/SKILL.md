---
name: game-frontend-20-spec-performance-budget-spec
description: Internal bundled meta-skill module for game-frontend/20-spec/performance-budget-spec; use within generated bootstrap node-specs when a game client needs FPS, startup, memory, bundle, draw call, particle, audio, and loading budgets before implementation.
---

# Performance Budget Spec Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Defines frontend performance budgets before implementation and QA. It translates
platform, genre, art, VFX, audio, scene, and loading constraints into measurable
budgets that `frontend-performance-budget-qa` must verify.

## Input Contract

Required: runtime architecture design, frontend runtime profile, target
platform/device class, scene composition or scene flow, and asset/loading
strategy when present.

Optional: engine-ready art manifest, VFX specs, audio bindings, level specs,
existing build stats, and product quality targets.

## Output Contract

Writes:

- `.allforai/game-frontend/bindings/performance-budget-spec.json`
- `.allforai/game-frontend/bindings/performance-budget-report.json`

Budgets must include `budget_id`, `metric`, `target`, `warning_threshold`,
`blocking_threshold`, `measurement_method`, `scene_or_flow_ref`,
`source_constraint`, `repair_routes`, `state`, and `consumer_refs`.

Required metric groups:

- startup/load time
- first playable time
- frame stability/FPS
- texture/atlas memory
- bundle/build size
- draw/update pressure
- particle/VFX counts
- audio channel/decoded size
- screenshot/probe capture availability
- Canvas2D DPR/viewport rendering stability when the runtime uses Web Canvas
  and targets mobile/WebView

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_runtime_profile`, `blocked_by_missing_target_platform`,
`blocked_by_unmeasurable_budget`.

## Invocation Contract

```json
{
  "skill": "game-frontend/performance-budget-spec",
  "mode": "spec_validate",
  "input_paths": {
    "runtime_architecture": ".allforai/game-frontend/design/runtime-architecture-design.json",
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "scene_flow": ".allforai/game-frontend/bindings/scene-flow-spec.json",
    "asset_loading": ".allforai/game-frontend/bindings/asset-loading-strategy-spec.json"
  },
  "output_root": ".allforai/game-frontend/bindings"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Each budget must name a measurement method available in the runtime profile or
return `blocked_by_unmeasurable_budget`. Static estimates may set targets but
cannot replace runtime measurement when a budget is blocking.

For Canvas2D/Web Canvas/WebView Canvas runtimes, define DPR rendering checks as
blocking QA when mobile is a target: at least DPR 1 and target-high DPR
screenshots, central gameplay nonblank/nonblack threshold, viewport-bound
primary elements, and resize/orientation stability where applicable.

Repair routing: missing platform target routes to product/game design; missing
measurement tooling routes to frontend-runtime-detection; oversized assets route
to art/audio/export; expensive scene/VFX routes to scene composition or VFX
binding.

## Completion Conditions

Return `COMPLETED` when budgets are measurable and connected to QA. Return
`FAILED_VALIDATION` when required performance expectations cannot be measured.
