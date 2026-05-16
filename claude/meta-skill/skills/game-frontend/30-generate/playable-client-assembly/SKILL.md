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
animation/VFX binding. When runtime-created visible objects need probe evidence,
also consume the runtime debug bridge contract.

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
`state`, `consumer_refs`, `module_wiring_proofs`, and `preserved_exports`.

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
    "animation_vfx": ".allforai/game-frontend/bindings/animation-vfx-binding-spec.json",
    "runtime_debug_bridge": ".allforai/game-frontend/bindings/runtime-debug-bridge-contract.json"
  },
  "output_root": ".allforai/game-frontend/assembly"
}
```

Supported modes: `assemble`, `validate_existing`, `repair_assembly`.

## Automatic Validation

After editing the project, run the strongest available build/typecheck/import
command from the runtime profile. If no command can run, return a blocking
state. Do not mark the client assembled based only on file edits.

For every newly created production runtime module, prove it is wired into the
production boot path. The report must list the module path, exported class or
factory, consumer import path, constructor/init/load/registration call, and a
runtime probe or test proving the initialized instance is active. A module that
exists but has zero production consumers, or is imported but never initialized,
is `failed_validation`.

Before rewriting an existing module, scan project imports/requires that target
that module and record the imported export names. The rewritten module must
preserve those exports or update every consumer in the same assembly slice and
prove the build still passes. Silent deletion of an imported export is
`failed_validation`, even if the rewritten module matches the new node-spec.

For Canvas2D/Web Canvas/WebView Canvas projects, read the project-local
frontend-runtime specialization generated from
`knowledge/engines/canvas2d.md`. Audio managers, VFX systems, renderers,
resource manifests, and gameplay systems must each have module interface cards
or equivalent report entries. Assembly cannot pass with dead-code modules or
manifest-only integration.

Repair routing: missing bindings route to their owning spec; build/type errors
route to the changed frontend files; missing assets route to asset import
binding or game-art engine-ready manifest.

## Completion Conditions

Return `COMPLETED` when the client builds or reaches the declared runnable
surface, every new module has a production consumer and init/load proof, and
rewritten modules preserve or migrate existing exports. Return
`FAILED_VALIDATION` when assembly cannot be built, launched, wired, initialized,
or traced to approved bindings.
