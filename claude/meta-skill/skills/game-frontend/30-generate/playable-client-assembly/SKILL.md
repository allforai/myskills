---
name: game-frontend-30-generate-playable-client-assembly
description: Internal bundled meta-skill module for game-frontend/30-generate/playable-client-assembly; use within generated bootstrap node-specs when this exact contract is selected.
---

# Playable Client Assembly Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Applies approved frontend bindings to the target client codebase so a playable
scene can load, render assets, accept input, show HUD, trigger animations/VFX,
and expose a smoke-test route.

## Input Contract

Required: frontend runtime profile, runtime architecture design, game state
model, scene flow, asset loading strategy, gameplay system bindings, asset
import bindings, scene composition, input/camera binding, HUD/UI binding, and
animation/VFX binding.

Optional: game design doc, level data, audio cue manifests, existing client
architecture, dev server command, and test conventions.

## Output Contract

Writes:

- `.allforai/game-frontend/assembly/playable-client-assembly-report.json`
- `.allforai/game-frontend/assembly/frontend-changed-files.json`

The report must include `assembly_id`, `runtime_profile_ref`,
`bindings_consumed`, `files_changed`, `entrypoints`, `asset_loader_changes`,
`scene_changes`, `input_camera_changes`, `hud_changes`,
`animation_vfx_changes`, `known_limitations`, `smoke_test_command`,
`state`, and `consumer_refs`.

Allowed states: `assembled`, `assembled_with_limits`, `needs_revision`,
`blocked_by_missing_bindings`, `blocked_by_runtime_profile`,
`blocked_by_project_write_failure`.

## Invocation Contract

```json
{
  "skill": "game-frontend/playable-client-assembly",
  "mode": "assemble",
  "input_paths": {
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "runtime_architecture": ".allforai/game-frontend/design/runtime-architecture-design.json",
    "game_state_model": ".allforai/game-frontend/bindings/game-state-model-spec.json",
    "scene_flow": ".allforai/game-frontend/bindings/scene-flow-spec.json",
    "asset_loading": ".allforai/game-frontend/bindings/asset-loading-strategy-spec.json",
    "gameplay_systems": ".allforai/game-frontend/bindings/gameplay-system-binding-spec.json",
    "asset_bindings": ".allforai/game-frontend/bindings/asset-import-binding-spec.json",
    "scene_composition": ".allforai/game-frontend/bindings/scene-composition-spec.json",
    "input_camera": ".allforai/game-frontend/bindings/input-camera-binding-spec.json",
    "hud_ui": ".allforai/game-frontend/bindings/hud-ui-binding-spec.json",
    "animation_vfx": ".allforai/game-frontend/bindings/animation-vfx-binding-spec.json"
  },
  "output_root": ".allforai/game-frontend/assembly"
}
```

Supported modes: `assemble`, `validate_existing`, `repair_assembly`.

## Automatic Validation

After editing the project, run the strongest available build/typecheck/import
command from the runtime profile. If no command can run, return a blocking
state. Do not mark the client assembled based only on file edits.

Repair routing: missing bindings route to their owning spec; build/type errors
route to the changed frontend files; missing assets route to asset import
binding or game-art engine-ready manifest.

## Completion Conditions

Return `COMPLETED` when the client builds or reaches the declared runnable
surface. Return `FAILED_VALIDATION` when assembly cannot be built, launched, or
traced to approved bindings.
