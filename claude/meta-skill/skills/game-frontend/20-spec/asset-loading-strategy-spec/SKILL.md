---
name: game-frontend-20-spec-asset-loading-strategy-spec
description: Internal bundled meta-skill module for game-frontend/20-spec/asset-loading-strategy-spec; use within generated bootstrap node-specs when a game client needs preload, lazy-load, cache, bundle, remote/local asset, atlas, audio, and failure handling strategy.
---

# Asset Loading Strategy Spec Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Defines how the frontend loads art, UI, animation, VFX, audio, levels, and data:
preload groups, lazy-load groups, cache lifetime, loading screens, fallback
assets, remote/local policy, and runtime probes. Asset import binding maps
manifest entries to keys; this skill decides when and how those keys load.

## Input Contract

Required: frontend runtime profile, engine-ready art manifest, asset import
bindings, audio bindings when present, and scene flow or scene composition.

Optional: performance budget, bundle/build constraints, CDN/remote config,
localization packs, template/data manifests, and existing loader code.

## Output Contract

Writes:

- `.allforai/game-frontend/bindings/asset-loading-strategy-spec.json`
- `.allforai/game-frontend/bindings/asset-loading-strategy-report.json`

Loading groups must include `group_id`, `load_phase`, `asset_refs`,
`scene_refs`, `priority`, `blocking`, `cache_policy`, `retry_policy`,
`fallback_policy`, `memory_budget_ref`, `progress_ui_ref`,
`validation_probe`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_asset_binding`, `blocked_by_runtime_profile`,
`blocked_by_missing_budget`.

## Invocation Contract

```json
{
  "skill": "game-frontend/asset-loading-strategy-spec",
  "mode": "spec_validate",
  "input_paths": {
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "asset_bindings": ".allforai/game-frontend/bindings/asset-import-binding-spec.json",
    "scene_flow": ".allforai/game-frontend/bindings/scene-flow-spec.json",
    "performance_budget": ".allforai/game-frontend/bindings/performance-budget-spec.json"
  },
  "output_root": ".allforai/game-frontend/bindings"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Each client-visible asset must belong to exactly one primary loading group and
may belong to additional warmup groups. Boot-critical assets must be bounded by
startup budget. Large or optional assets must not block first playable scene
unless design requires it. Missing load-failure fallback is invalid.

Repair routing: missing asset refs route to asset-import-binding-spec; oversized
load groups route to performance-budget-spec or art atlas packaging; missing
progress UI routes to hud-ui-binding-spec.

## Completion Conditions

Return `COMPLETED` when loading groups cover all runtime assets and have probes.
Return `FAILED_VALIDATION` when assets can be bound but not safely loaded or
validated in the frontend.
