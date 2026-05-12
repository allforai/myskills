---
name: game-frontend-20-spec-scene-composition-spec
description: Internal bundled meta-skill module for game-frontend/20-spec/scene-composition-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Scene Composition Spec Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Defines how approved design, level, art, UI, and audio contracts appear in
frontend scenes: scene list, layer order, spawn points, camera bounds, visible
assets, HUD overlays, audio cues, and smoke-test targets.

## Input Contract

Required: game design doc, frontend runtime profile, asset import bindings, and
at least one level or scene requirement.

Optional: level layout specs, blockouts, tileset manifests, UI registry, audio
cue specs, animation/VFX bindings, and existing scene code.

## Output Contract

Writes:

- `.allforai/game-frontend/bindings/scene-composition-spec.json`
- `.allforai/game-frontend/bindings/scene-composition-report.json`

Scenes must include `scene_id`, `scene_type`, `source_requirements`,
`entry_condition`, `asset_bindings`, `level_refs`, `layer_order`,
`spawn_points`, `camera_bounds`, `hud_refs`, `audio_refs`, `expected_visible`,
`smoke_actions`, `validation_probe`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_level_contract`, `blocked_by_asset_binding`,
`blocked_by_runtime_profile`.

## Invocation Contract

```json
{
  "skill": "game-frontend/scene-composition-spec",
  "mode": "spec_validate",
  "input_paths": {
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "asset_bindings": ".allforai/game-frontend/bindings/asset-import-binding-spec.json"
  },
  "output_root": ".allforai/game-frontend/bindings"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every required playable scene has a level/source requirement,
visible asset bindings, layer order, spawn, camera bounds, and smoke target.
Scene composition must preserve art layering and not let UI or VFX obscure
required gameplay readability.

Repair routing: missing level refs route to `game-level`; missing assets route
to `asset-import-binding-spec`; missing UI refs route to `hud-ui-binding-spec`.

## Completion Conditions

Return `COMPLETED` when scenes can be assembled and smoke-tested. Return
`FAILED_VALIDATION` when no required scene can be loaded, seen, or traced to
approved contracts.
