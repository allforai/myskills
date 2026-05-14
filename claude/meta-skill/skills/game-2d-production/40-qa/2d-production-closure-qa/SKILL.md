---
name: game-2d-production-closure-qa
description: Final closure gate for a playable 2D game slice across design, art, UI, audio, frontend, runtime, screenshots, and tests.
---

# 2D Production Closure QA

## Input Contract

Read all `game-2d` reports, game-frontend QA reports, engine-ready art manifest,
UI/audio manifests, build/export reports, and project-local specialized QA
reports.

## Output Contract

Write:

- `.allforai/game-2d/qa/2d-production-closure-report.json`
- `.allforai/game-2d/qa/2d-production-closure.html`

The report must include status, blockers, major findings, screenshots reviewed,
functional assertions, Codex CLI review paths, repair loop count, and final
accept/reject decision.

## Invocation Contract

This is the final 2D game production gate. It must not create new design,
change art direction, or invent a fallback acceptance path.

```json
{
  "skill": "game-2d-production/40-qa/2d-production-closure-qa",
  "mode": "final_closure",
  "input_paths": [
    ".allforai/game-2d/assembly/playable-slice-assembly-report.json",
    ".allforai/game-2d/qa/core-loop-playability-qa-report.json",
    ".allforai/game-2d/qa/asset-binding-visual-qa-report.json",
    ".allforai/game-2d/qa/session-completion-qa-report.json"
  ],
  "output_root": ".allforai/game-2d/qa"
}
```

## Automatic Validation

Require:

- engine-ready art manifest bindings through `runtime_id` and `asset_id`
- playable vertical slice assembly report
- core-loop playability QA
- asset-binding visual QA
- session-completion QA
- runtime-gameplay-visual-acceptance
- frontend build/export or explicit `blocked_by_unrunnable_client`
- functional assertions and Codex CLI screenshot review

Do not accept static review. Do not accept logs, DOM, probes, source inspection,
or manifest existence alone. If validation cannot run, report
`blocked_by_unrunnable_client`, `blocked_by_missing_screenshot`,
`blocked_by_missing_runtime_command`, `blocked_by_missing_codex_cli`,
`blocked_by_missing_visual_model_capability`, or `failed_validation`.

## Completion Conditions

Pass only when there are no blocker or major findings, all required screenshots
exist, all runtime assertions pass, the repair loop has revalidated affected
screenshots, and the final HTML can be read by humans in Chinese.
