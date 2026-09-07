---
name: game-frontend-40-qa-visual-runtime-regression-qa
description: Validate runtime screenshots and probes against scene composition, asset visibility, HUD placement, layer order, scale, animation/VFX readability, and baselines through dual independent visual review; writes game-frontend/qa/runtime-visual-review-2.json and runtime-visual-closure-audit.json.
---

# Visual Runtime Regression QA Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled.

## Overview

Validates runtime screenshots and probes against expected scene composition,
asset visibility, HUD placement, layer order, scale, animation/VFX readability,
and known baseline screenshots.

Screenshot-based visual judgment runs through the shared batch visual acceptance
workflow, which is dual-reviewer: reviewer two and reviewer one each inspect the
screenshots independently and blocking findings are the union of the two. This
skill owns game-frontend standards, evidence preparation, and repair routing, not
the review mechanics.

## Input Contract

Required: playable smoke test report, scene composition spec, asset import
bindings, HUD/UI binding, and screenshot/probe evidence.

Optional: previous baseline screenshots, art QA reports, style consistency QA,
runtime import report, Playwright traces, viewport matrix, and
`.allforai/visual-qa/visual-model-routing-report.json`.

## Output Contract

Writes:

- `.allforai/game-frontend/qa/visual-runtime-regression-report.json`
- `.allforai/game-frontend/qa/visual-runtime-regression-batches/`
- `.allforai/game-frontend/qa/runtime-visual-review-2.json`
- `.allforai/game-frontend/qa/runtime-visual-review-2.md`
- `.allforai/game-frontend/qa/runtime-visual-closure-audit.json`
- `.allforai/game-frontend/qa/runtime-visual-closure-audit.md`
- `.allforai/game-frontend/qa/runtime-visual-repair-loop-report.json`
- `.allforai/game-frontend/qa/runtime-visual-repair-loop-report.md`

Findings must include `finding_id`, `scene_id`, `viewport`, `expected`,
`actual`, `evidence_path`, `severity`, `root_cause`, `repair_target`,
`blocks_runtime`, and `state`.

Allowed states: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_screenshot`, `failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-frontend/visual-runtime-regression-qa",
  "mode": "validate",
  "input_paths": {
    "smoke_report": ".allforai/game-frontend/qa/playable-smoke-test-report.json",
    "scene_composition": ".allforai/game-frontend/bindings/scene-composition-spec.json",
    "asset_bindings": ".allforai/game-frontend/bindings/asset-import-binding-spec.json",
    "hud_ui": ".allforai/game-frontend/bindings/hud-ui-binding-spec.json"
  },
  "output_root": ".allforai/game-frontend/qa"
}
```

Supported modes: `validate`, `compare_baseline`, `repair_targets`.

## Automatic Validation

Build batch documents from the screenshot/probe evidence and invoke:

```text
${CLAUDE_PLUGIN_ROOT}/skills/visual-qa/40-qa/batch-visual-acceptance/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/codex-cli-delegation/30-execute/codex-cli-task/SKILL.md
```

reviewer two must inspect screenshots for blank canvas, missing assets, wrong layer
order, incorrect scale/pivot, HUD overlap, cropped text, unreadable VFX, missing
animation state, and responsive viewport issues. Use pixel/canvas probes as
supporting evidence, but do not pass from probes or metadata alone.

Prototype/placeholder visuals are blocking regressions. Reject screenshots that
show pure-color blocks, black debug backgrounds, generic geometric sprites,
sample/prototype scenes, missing production HUD, or a core loop rendered without
the assets declared in the engine-ready art manifest. For suspected
placeholder output, require reviewer two to inspect the scene entrypoint/config,
scene composition spec, asset import bindings, and screenshot evidence by path.
The finding must name the repair target: wrong entrypoint, prototype component,
missing scene binding, missing asset loader mapping, or missing runtime art.

reviewer one performs its own independent screenshot review and then the
reconciliation and closure audit: both review reports exist, inspected evidence
paths are listed in both, blocker/major findings from either reviewer have repair
targets, affected batches were rerun by both reviewers after repair, and
unresolved blockers remain `FAILED_VALIDATION`.

Repair routing: missing assets route to asset import binding; visual asset
defects route to game-art QA; layout/HUD defects route to HUD/UI binding or
game-ui; scene/camera defects route to scene composition or input-camera
binding.

## Completion Conditions

Return `COMPLETED` when runtime visuals match the declared scene and UI
contracts and neither reviewer has unresolved blocker/major findings. Return
`FAILED_VALIDATION` when screenshots/probes are missing, either reviewer reports
blocking visual regressions after the repair budget, or the closure audit is
incomplete. A missing cross-platform CLI is recorded as `missing_cross_platform_cli` and reviewer two runs as a second fresh-context sub-agent; return `blocked_by_missing_second_review` only if two independent reports cannot be produced.
