---
name: game-art-40-qa-in-game-beauty-gate
description: Validate that accepted art looks commercially appealing inside the actual game runtime screens, using screenshots, benchmark scoring, and repair/revalidation.
---

# In-Game Beauty Gate Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive,
> art-qa and runtime visual QA invoked.

## Purpose

The final question is not whether PNGs are valid. It is whether the game looks
good when the player sees it. This gate scores runtime screenshots against the
project art benchmark and blocks closure when the actual game still looks like
a prototype.

## Input Contract

Required:

```text
.allforai/game-design/art/art-direction-benchmark.json
.allforai/game-design/art/asset-acceptance-criteria.json
.allforai/game-runtime/art/engine-ready-art-manifest.json
.allforai/game-frontend/qa/runtime-screenshot-manifest.json
```

Optional:

```text
.allforai/game-frontend/qa/codex-runtime-visual-review.json
.allforai/game-design/art/qa/asset-family-consistency-report.json
.allforai/visual-qa/visual-acceptance-criteria.json
.allforai/bootstrap/specialized-skills/
```

If the game cannot run or screenshots cannot be captured, return
`blocked_by_missing_runtime_screenshots`. Do not use static mockups as a
substitute for runtime screenshots.

## Output Contract

Writes:

```text
.allforai/game-design/art/qa/in-game-beauty-gate-report.json
.allforai/game-design/art/qa/in-game-beauty-gate-report.md
```

The JSON must include:

```json
{
  "status": "passed | failed | blocked",
  "screens_reviewed": [],
  "screen_scores": {},
  "beauty_gaps": [],
  "runtime_visual_gaps": [],
  "repair_routes": [],
  "feedback_report_paths": [],
  "visual_repair_loop_refs": [],
  "requires_revalidation": []
}
```

## Method

1. Read the project benchmark and screenshot manifest. Screens must come from
   the actual runtime.
2. Select the player-facing screens that matter for first impression and
   retention: first screen, main menu or map, core gameplay, reward/win/loss,
   shop or economy surface when present, dialogue/tutorial when present, and
   store-facing screenshot candidate when available.
3. For each screenshot, score:
   immediate appeal, concept fit, visual hierarchy, gameplay readability,
   asset integration, UI/world cohesion, color/material quality, motion/VFX
   implication, mobile/desktop framing, and absence of prototype artifacts.
4. Compare screenshots to raw asset QA. If assets pass but runtime looks bad,
   classify as `composition_problem`, `background_problem`,
   `layout_or_scale_problem`, `asset_binding_problem`, `lighting_or_palette`,
   `ui_world_mismatch`, `missing_polish`, or `screenshot_capture_problem`.
5. Route repair to the narrowest upstream step: art regeneration/edit,
   layout/UI changes, asset binding, runtime camera/composition, VFX timing, or
   screenshot capture setup.
6. Require revalidation after repair. A fixed report without fresh runtime
   screenshots is invalid. fresh runtime screenshots are mandatory after
   every visual repair.

## Repair And Revalidation Loop

Runtime beauty failures must trigger repair and fresh screenshot revalidation;
they must not remain as passive comments.

Loop:

1. Classify each `beauty_gaps` or `runtime_visual_gaps` item by owner:
   - art generation/edit: write
     `.allforai/game-design/art/image-generation/image-feedback-report.json`;
   - UI/layout/composition: write
     `.allforai/game-frontend/qa/runtime-visual-feedback-report.json`;
   - asset binding/import: route to `runtime-import-check` or frontend asset
     binding;
   - screenshot capture issue: route to runtime screenshot capture setup.
2. Repair the smallest upstream owner. Do not regenerate images for layout,
   camera, binding, or capture failures unless the image itself is the root
   cause.
3. Rebuild affected runtime screens and capture fresh runtime screenshots.
4. Rerun Codex CLI runtime visual review for affected screenshots.
5. Rerun this in-game beauty gate.
6. Append the iteration to
   `.allforai/game-design/art/qa/visual-repair-loop-report.json` and
   `.allforai/game-design/art/qa/visual-repair-loop-report.md`, referencing the
   feedback report and fresh screenshot paths.

Default budget: 3 repair attempts per screen family. If the game still fails
the benchmark after budget exhaustion, return `FAILED_VALIDATION` with
unresolved `beauty_gaps` or `runtime_visual_gaps`. Do not downgrade the issue to
`passed_with_warnings`.

## Automatic Validation

Reject with `FAILED_VALIDATION` when:

- runtime screenshots are missing or stale;
- screenshot review only checks non-black/non-empty pixels;
- any player-facing screen scores below 4/5 in an art-heavy game;
- prototype backgrounds, pure-color placeholder assets, unreadable tiles/icons,
  or generic AI mismatches are marked non-blocking;
- repair routes do not identify upstream art, UI, runtime, or binding nodes;
- closure passes without fresh screenshots after repair.
- runtime beauty gaps were not written to an owner-specific feedback report;
- no visual repair loop report links the failed screenshot, repair action,
  fresh screenshot, and rerun review.

## Completion Conditions

Return `COMPLETED` only when actual runtime screenshots exist, every reviewed
screen reaches the benchmark pass score, no `beauty_gaps` or
`runtime_visual_gaps` remain, and any repair has been followed by fresh
runtime screenshots plus review. The visual repair loop report must record any
repair attempt. Do not pass from asset manifests, probes, or static mockups
alone.
