---
name: game-2d-asset-binding-visual-qa
description: Validate that 2D assets are actually bound in runtime, readable in context, and not accepted from manifests alone.
---

# Asset Binding Visual QA

## Input Contract

Read asset-runtime binding contract, playable slice manifest, runtime profile,
runtime-gameplay-visual-acceptance report, visual acceptance criteria, runtime
probe evidence when available, and engine-ready art manifest.

## Output Contract

Write `.allforai/game-2d/qa/asset-binding-visual-qa-report.json` with asset
coverage, screenshot evidence, missing/placeholder findings, readability
findings, and repair routing. Findings must be classified into `code_gaps`,
`asset_gaps`, `contract_gaps`, and `environment_blockers`.

## Invocation Contract

Batch screenshots by scene, screen, level, and asset family. Use pull-mode
Codex CLI review for visual scoring where possible.

```json
{
  "skill": "game-2d-production/40-qa/asset-binding-visual-qa",
  "mode": "visual_runtime_qa",
  "input_paths": [
    ".allforai/game-2d/spec/asset-runtime-binding-contract.json",
    ".allforai/game-2d/assembly/playable-slice-manifest.json"
  ],
  "output_root": ".allforai/game-2d/qa"
}
```

## Automatic Validation

Fail if required assets are only present on disk or in JSON but absent from
runtime screenshots. Fail if generated art is not distinguishable at target
size, mismatches the approved art direction, or uses placeholders without
approval.

Read `.allforai/visual-qa/visual-acceptance-criteria.json` and
`.allforai/visual-qa/visual-acceptance-criteria.md` before building visual QA
batches. If criteria are missing or do not cover the current asset family or
runtime scene, return `blocked_by_missing_visual_criteria`.

Prototype/placeholder detection is a hard gate. The runtime screenshot review
must reject:

- prototype-only components, debug scenes, sample scenes, or files whose stated
  purpose is gameplay feel validation rather than production presentation;
- pure-color rectangle/circle blocks used in place of engine-ready tile, icon,
  character, background, UI, or VFX assets;
- black/flat debug backgrounds when the scene contract requires a themed
  background, board frame, HUD, or gameplay context;
- screenshots where the core loop is visible but required HUD, background,
  tile art, character art, VFX, or UI layers are absent;
- runtime visuals that cannot be traced from visible elements back to
  `.allforai/game-runtime/art/engine-ready-art-manifest.json` by
  `asset_id`/`runtime_id`.

For Cocos, Phaser, Godot, Unity, web canvas, or custom runtimes, the QA task
must inspect project files for a declared prototype/debug entrypoint when a
screenshot looks placeholder-like. If a scene such as `Prototype`, a component
such as `PrototypeBoard`, or equivalent debug renderer is active in a production
slice, classify the issue as `code_gaps` plus `asset_gaps` and block closure.

When runtime probe evidence exists, cross-check the screenshot against probe
counts and binding refs. A visible board with 70 tile nodes when the invariant
requires 64, a node id containing `[object Set]`, or a visible Sprite/SpriteFrame
without a runtime binding is a blocker even if the screenshot appears playable.

## Completion Conditions

Complete when every required visible `asset_id`/`runtime_id` has runtime
screenshot evidence, the visible scene is not a prototype/debug renderer, and
no blocker or major visual binding finding remains.
