---
name: game-2d-playable-slice-assembly
description: Assemble the approved 2D contracts into a runnable playable vertical slice in the target client/runtime.
---

# Playable Slice Assembly

## Input Contract

Read all `.allforai/game-2d/spec/*.json` contracts, game-frontend assembly
reports, engine-ready art manifest, UI/audio manifests, runtime profile, and
project-local specialized skills when present.

## Output Contract

Write:

- `.allforai/game-2d/assembly/playable-slice-manifest.json`
- `.allforai/game-2d/assembly/playable-slice-assembly-report.json`

The manifest must list runtime entrypoint, scenes/screens, bound assets,
automation commands, screenshots to capture, and known blockers.

## Invocation Contract

Use the target project code and runtime. Do not accept a separate static demo
as proof unless the handoff explicitly defines that demo as the target runtime.

```json
{
  "skill": "game-2d-production/30-generate/playable-slice-assembly",
  "mode": "assemble_runtime_slice",
  "input_paths": [
    ".allforai/game-2d/spec/core-loop-playable-contract.json",
    ".allforai/game-2d/spec/asset-runtime-binding-contract.json",
    ".allforai/game-frontend/assembly/playable-client-assembly-report.json"
  ],
  "output_root": ".allforai/game-2d/assembly"
}
```

## Automatic Validation

Run build/start smoke commands from the runtime profile. If the project cannot
run, emit `blocked_by_unrunnable_client`. Missing runtime artifacts are
`failed_validation`.

The assembled slice must use the declared production runtime entrypoint and
scene/screen. It must not use a prototype, sample, debug, or gameplay-feel
validation scene as the production smoke target. For Cocos, Phaser, Godot,
Unity, web canvas, or custom engines, inspect the actual launch URL/scene,
startup scene config, and runtime component names before accepting the slice.

Reject the assembly with `failed_validation` when any of these are true:

- the active scene, route, or entrypoint contains `Prototype`, `Sample`,
  `Debug`, test-only naming, or an equivalent project-local prototype marker;
- a component/renderer such as `PrototypeBoard`, `debugRenderer`,
  `placeholderRenderer`, or a project-local pure-color renderer owns the
  primary gameplay surface;
- core gameplay objects are drawn as `Graphics`/canvas rectangles/circles or
  generic geometry instead of production SpriteFrame/texture/UI bindings;
- generated or searched assets exist on disk but the runtime manifest cannot
  trace visible nodes back to `asset_id`/`runtime_id`;
- HUD, board frame, themed background, selected-state feedback, completion
  feedback, or required VFX/audio triggers are absent from the smoke surface.

When important visible objects are created dynamically at runtime, require a
QA-only runtime probe or engine-native test API before assembly can pass. The
probe must report active scene, visible object counts, node/entity ids,
coordinates/layers, asset binding refs, and prototype/placeholder flags. Probe
data supports diagnosis only; it cannot replace screenshot evidence.

The playable-slice manifest must declare the screenshot tasks and runtime probe
paths that downstream visual QA will use. If screenshots or probes cannot be
captured in the target runtime, return a blocking status instead of accepting a
static review.

## Completion Conditions

Complete when a runnable production slice exists, the production entrypoint is
proven, screenshot/probe evidence tasks are declared, required runtime assets
are bound by `asset_id`/`runtime_id`, and no prototype/debug/placeholder
renderer owns the gameplay surface. Otherwise write a blocking report explaining
which upstream or runtime contract prevents production assembly.
