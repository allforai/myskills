---
name: game-2d-asset-runtime-binding-contract
description: Bind approved 2D art, UI, animation, VFX, and audio manifests to runtime identifiers, anchors, pivots, atlases, and event hooks.
---

# Asset Runtime Binding Contract

## Input Contract

Read engine-ready art manifest, UI manifest, audio manifest, animation/VFX
manifests, and frontend asset import specs.

## Output Contract

Write `.allforai/game-2d/spec/asset-runtime-binding-contract.json` with:

- every `asset_id` mapped to a `runtime_id`
- source manifest path, atlas/spritesheet path, frame names, anchors, pivots
- animation, VFX, and audio event bindings
- placeholder policy and missing-asset blocking rules
- runtime screenshot checkpoints proving assets are visible in context.

## Invocation Contract

Program code must consume this contract instead of hardcoding raw asset paths.

```json
{
  "skill": "game-2d-production/20-spec/asset-runtime-binding-contract",
  "mode": "write_contract",
  "input_paths": [
    ".allforai/game-runtime/art/engine-ready-art-manifest.json",
    ".allforai/game-frontend/bindings/asset-import-binding-spec.json"
  ],
  "output_root": ".allforai/game-2d/spec"
}
```

## Automatic Validation

Fail if a required gameplay/UI element lacks `asset_id`, `runtime_id`, anchor,
pivot, or screenshot proof. Placeholder use is a blocker unless explicitly
approved by the design handoff.

## Completion Conditions

Complete when all required visible assets have runtime bindings and QA evidence
requirements.
