---
name: visual-qa-20-spec-visual-acceptance-criteria
description: Internal bundled meta-skill module for visual-qa/20-spec/visual-acceptance-criteria; use before screenshot, generated-image, HTML gate, runtime visual, art, UI, or app visual QA to define project-specific acceptance standards, forbidden placeholders, evidence requirements, failure codes, and repair routes.
---

# Visual Acceptance Criteria Skill

> Internal sub-skill for reusable visual QA pipelines. Status: bundled,
> inactive, not wired.

## Overview

Defines the standard that visual QA must apply before Codex CLI reviews images
or screenshots. This skill answers "what should this project look like, and what
must be rejected?" The batch visual acceptance skill answers "how to inspect
and report it."

Use this before:
- game art QA;
- game UI QA;
- game frontend runtime screenshot QA;
- 2D production closure QA;
- app UI screenshot QA;
- HTML approval gates;
- generated image/contact-sheet review;
- visual regression checks.

## Input Contract

Required:

| Input | Required fields | Missing behavior |
|---|---|---|
| product or game concept | visual promise, audience, product tone, domain constraints | Return `UPSTREAM_DEFECT`. |
| art/UI direction | style tokens, palette, composition, typography/UI rules when applicable | Return `UPSTREAM_DEFECT` for production visual QA. |
| target surfaces/scenes | scene/screen ids, user states, gameplay or app flows, viewport/device matrix | Return `UPSTREAM_DEFECT` when runtime screenshots will be reviewed. |
| asset/runtime contracts | engine-ready art manifest, UI manifest, asset import bindings, or equivalent runtime IDs | Return `UPSTREAM_DEFECT` when visible assets must be accepted. |
| runtime probe policy | whether runtime-created objects must be inspected through embedded probe code or equivalent engine test API | Return `UPSTREAM_DEFECT` when runtime-created visuals are central and no probe policy exists. |

Optional:

- `.allforai/game-design/art/asset-acceptance-criteria.json`
- `.allforai/game-design/art/visual-style-tokens.json`
- `.allforai/game-runtime/art/engine-ready-art-manifest.json`
- `.allforai/game-frontend/bindings/scene-composition-spec.json`
- `.allforai/game-frontend/bindings/asset-import-binding-spec.json`
- `.allforai/game-frontend/bindings/hud-ui-binding-spec.json`
- app design screen requirements and UI input handoff
- prior baseline screenshots or goldens
- platform-specific rendering constraints
- project-local specialized visual rules

## Output Contract

Writes:

```text
.allforai/visual-qa/visual-acceptance-criteria.json
.allforai/visual-qa/visual-acceptance-criteria.md
.allforai/visual-qa/visual-evidence-requirements.json
```

Domain packs may also copy or reference these outputs under their local QA
roots, but the canonical reusable standard lives under `.allforai/visual-qa/`.

`visual-acceptance-criteria.json` must include:

```json
{
  "schema_version": "1.0",
  "project_id": "glow-island",
  "criteria_id": "runtime-production-visual-v1",
  "scope": "game_art | game_ui | game_runtime | app_ui | html_gate | generated_image | mixed",
  "visual_promise": {
    "summary": "温泉海岛修复、柔和手绘/水彩、轻松治愈、明亮可读",
    "must_feel_like": [],
    "must_not_feel_like": []
  },
  "global_forbidden": [
    {
      "code": "PROTOTYPE_PLACEHOLDER_VISUAL",
      "severity": "blocker",
      "description": "纯色块、黑底调试、sample/prototype scene、generic geometry、未绑定正式 HUD 或未绑定 engine-ready art"
    }
  ],
  "scene_criteria": [
    {
      "scene_id": "level_1_gameplay",
      "required_visible_elements": [],
      "required_absent_elements": [],
      "required_states": [],
      "required_asset_refs": [],
      "screenshot_tasks": []
    }
  ],
  "asset_family_criteria": [
    {
      "family": "tileset",
      "required_runtime_checks": [],
      "visual_checks": [],
      "technical_checks": [],
      "repair_routes": []
    }
  ],
  "state_criteria": [
    {
      "state_id": "tile_selected",
      "expected_visual": [],
      "failure_codes": []
    }
  ],
  "evidence_requirements": {
    "must_include_runtime_screenshots": true,
    "must_include_runtime_probe": true,
    "must_include_before_after_pairs": true,
    "must_trace_visible_assets_to_runtime_ids": true,
    "must_include_viewports": [],
    "must_include_codex_cli_review": true
  },
  "failure_codes": [],
  "repair_routes": []
}
```

The Markdown file must be Chinese when the project/user-facing docs are Chinese.
It is the document Codex CLI should read first for human-readable standards.

## Invocation Contract

```json
{
  "skill": "visual-qa/visual-acceptance-criteria",
  "mode": "derive_project_criteria",
  "input_paths": {
    "concept": ".allforai/concept-contract.json",
    "art_style_tokens": ".allforai/game-design/art/visual-style-tokens.json",
    "asset_acceptance": ".allforai/game-design/art/asset-acceptance-criteria.json",
    "engine_ready_art": ".allforai/game-runtime/art/engine-ready-art-manifest.json",
    "scene_composition": ".allforai/game-frontend/bindings/scene-composition-spec.json"
  },
  "output_root": ".allforai/visual-qa"
}
```

Supported modes: `derive_project_criteria`, `derive_runtime_criteria`,
`derive_asset_criteria`, `derive_ui_criteria`, `validate_existing`,
`repair_existing`.

## Criteria Requirements

Every criteria document must define:

- project visual promise and tone;
- global forbidden visuals;
- scene/screen-level required and forbidden elements;
- asset-family-level standards;
- state-level standards for visual feedback;
- viewport/device coverage;
- evidence requirements;
- blocker/major/minor failure code taxonomy;
- repair routes to the owning skill/node;
- whether final docs/screenshots should be evaluated in Chinese.

Global forbidden visuals must always include:

- blank or black canvas when production scene is expected;
- pure-color blocks standing in for production assets;
- prototype/debug/sample scene or component active in production QA;
- generic geometric placeholders;
- missing production HUD/UI when the screen contract requires it;
- generated art present on disk but absent from runtime screenshot;
- visible assets that cannot be traced to `asset_id`/`runtime_id`;
- layout/text overlap, cropped primary content, or unreadable target-size text;
- visual style mismatch against project art/UI direction.

## Runtime Standard

For runtime screenshots, criteria must require:

- initial loaded production scene;
- primary gameplay/app interaction state;
- before/after pairs around meaningful actions;
- selected/pressed/invalid/success/failure feedback states where applicable;
- win/loss/completion/empty/error states where applicable;
- mobile and desktop viewports when both are supported;
- scene entrypoint/config evidence when placeholder visuals are suspected;
- traceability from visible assets to runtime manifests or binding specs.
- embedded runtime probe or equivalent engine test API when important visible
  objects are created dynamically at runtime.

Canvas, DOM, log, state, or manifest checks may support the review, but cannot
replace screenshot inspection.

## Runtime Probe Requirement

For games, simulations, canvas apps, and dynamic UI where visible objects are
created at runtime, static code review is not sufficient. Criteria must require
an embedded runtime probe or equivalent engine-native test API that records the
actual objects/entities/nodes created during the captured state.

The probe must capture runtime truth needed for QA:

- active scene/screen/route;
- runtime-created object counts by family;
- ids/names/coordinates/layers for important visible objects;
- asset binding refs for visible sprites/textures/UI elements;
- state invariants before/after actions;
- placeholder/debug/prototype flags;
- screenshot task id and timestamp.

The probe is supporting evidence, not a pass condition by itself. Final visual
acceptance still requires real screenshots inspected by Codex CLI. However, if
the probe is missing for runtime-created core objects, return
`blocked_by_missing_runtime_probe` instead of relying on static inspection.

## Integration With Batch Visual Acceptance

`visual-qa/40-qa/batch-visual-acceptance/SKILL.md` must consume this criteria
document through `acceptance_criteria` and `acceptance_criteria_doc`.

Batch documents must quote or link the relevant criteria sections and preserve
failure codes. Codex CLI must not invent a weaker standard. If the criteria
document is missing, stale, or does not cover the visual evidence type being
reviewed, return `UPSTREAM_DEFECT` or `blocked_by_missing_visual_criteria`.

## Automatic Validation

Before returning success:

1. Confirm input concept/style/runtime contracts are sufficient for the target
   scope.
2. Confirm every reviewed scene/screen/asset family has at least one concrete
   acceptance rule and at least one failure code.
3. Confirm global forbidden visuals include prototype/placeholder rejection.
4. Confirm runtime criteria require screenshot evidence, runtime probe evidence
   for dynamic objects, and visible asset traceability when runtime screenshots
   are in scope.
5. Confirm repair routes name owning skills/nodes instead of generic "fix UI".
6. Confirm Markdown and JSON outputs agree on failure codes and required
   evidence.

## Completion Conditions

Return `COMPLETED` when JSON and Markdown criteria exist, cover the requested
visual scope, define blocker-level placeholder/prototype rejection, and can be
consumed by batch visual acceptance.

Return `UPSTREAM_DEFECT` when concept/style/runtime inputs are too incomplete to
define criteria.

Return `FAILED_VALIDATION` or `blocked_by_missing_visual_criteria` when criteria
cannot cover the evidence type or lacks required blocker standards. Do not run
visual QA without an explicit criteria document.
