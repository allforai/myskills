---
name: game-2d-asset-binding-visual-qa
description: Validate that 2D assets are actually bound in runtime, readable in context, and not accepted from manifests alone.
---

# Asset Binding Visual QA

## Input Contract

Read asset-runtime binding contract, playable slice manifest, runtime profile,
runtime-gameplay-visual-acceptance report, and engine-ready art manifest.

## Output Contract

Write `.allforai/game-2d/qa/asset-binding-visual-qa-report.json` with asset
coverage, screenshot evidence, missing/placeholder findings, readability
findings, and repair routing.

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

## Completion Conditions

Complete when every required visible `asset_id`/`runtime_id` has runtime
screenshot evidence and no blocker or major visual binding finding remains.
