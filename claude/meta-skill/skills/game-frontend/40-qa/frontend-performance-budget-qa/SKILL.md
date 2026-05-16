---
name: game-frontend-40-qa-frontend-performance-budget-qa
description: Internal bundled meta-skill module for game-frontend/40-qa/frontend-performance-budget-qa; use within generated bootstrap node-specs when this exact contract is selected.
---

# Frontend Performance Budget QA Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Validates frontend performance budgets for startup, asset loading, frame
stability, texture/atlas count, memory signals, bundle size, draw/update
pressure, and low-end target constraints.

## Input Contract

Required: frontend runtime profile, performance budget spec, playable assembly
report, and smoke or playability report.

Optional: build output, browser performance trace, engine profiler output,
asset manifest, atlas manifest, bundle analyzer output, and runtime logs.

## Output Contract

Writes:

- `.allforai/game-frontend/qa/frontend-performance-budget-report.json`

Metrics must include `metric_id`, `budget`, `actual`, `evidence_path`,
`severity`, `root_cause`, `repair_target`, `blocks_runtime`, and `state`.

Allowed states: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_measurement`, `failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-frontend/frontend-performance-budget-qa",
  "mode": "validate",
  "input_paths": {
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "performance_budget": ".allforai/game-frontend/bindings/performance-budget-spec.json",
    "assembly_report": ".allforai/game-frontend/assembly/playable-client-assembly-report.json",
    "smoke_report": ".allforai/game-frontend/qa/playable-smoke-test-report.json"
  },
  "output_root": ".allforai/game-frontend/qa"
}
```

Supported modes: `validate`, `profile_runtime`, `repair_targets`.

## Automatic Validation

Run available frontend profiling/build commands or collect browser/engine
timing evidence. Static asset counts may explain issues but cannot replace
runtime measurement when a budget is required.

For Canvas2D/Web Canvas/WebView Canvas projects, performance/viewport QA must
rerun after gameplay, renderer, scene, asset, or DPR-related code changes. If
the target includes mobile/WebView, run a high-DPR browser pass (for example
`deviceScaleFactor: 3`) and verify the central gameplay region is visible and
not black/offscreen. A stale DPR report from before renderer fixes is not valid
closure evidence.

Repair routing: oversized assets route to game-art atlas/export; slow startup
routes to assembly/data/asset binding; render pressure routes to scene,
animation/VFX, or frontend implementation.

## Completion Conditions

Return `COMPLETED` when budgets pass or non-blocking warnings are declared.
Return `FAILED_VALIDATION` when required performance evidence is missing or
blocking budgets are exceeded.
