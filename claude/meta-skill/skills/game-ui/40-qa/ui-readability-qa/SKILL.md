---
name: game-ui-40-qa-ui-readability-qa
description: Internal bundled meta-skill module for game-ui/40-qa/ui-readability-qa; use within generated bootstrap node-specs when this exact contract is selected.
---

# UI Readability QA Skill

> Internal sub-skill for game UI pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill validates that game UI outputs are readable, tappable, visually
consistent, and do not harm gameplay. It combines deterministic artifact checks
with screenshot/mockup visual validation when images or browser previews exist.

## Scope

In scope:
- artifact consistency checks,
- viewport and breakpoint coverage,
- tap target checks,
- text fit and truncation checks,
- contrast/readability checks,
- HUD/playfield occlusion checks,
- visual style consistency checks,
- repair recommendations for upstream UI specs.

Out of scope:
- rewriting frontend code directly,
- generating new UI concepts,
- manual approval.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| `.allforai/game-design/ui/ui-registry.json` | screens, components, states | Return `UPSTREAM_DEFECT`. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/game-design/ui/ui-flow-map.json` | reachability, back behavior | Report flow coverage unavailable. |
| `.allforai/game-design/ui/hud-information-design.json` | critical HUD signals, protected regions | Run generic HUD checks only. |
| `.allforai/game-design/ui/screen-layout-spec.json` | regions, breakpoints, safe zones | Report layout checks unavailable. |
| `.allforai/game-design/ui/component-state-spec.json` | states, tap targets, text rules | Report component checks unavailable. |
| `.allforai/game-design/ui/ui-mockup-manifest.json` | mockup image paths and statuses | Run artifact-only checks. |
| Browser screenshots | pixel evidence | Use visual validation. |

## QA Workflow

| Stage | Purpose | Main output |
|---|---|---|
| 1. Load contracts | Gather registry, flow, HUD, layout, components, mockups. | `qa_inputs` |
| 2. Run consistency checks | IDs, references, paths, missing artifacts. | `deterministic_results` |
| 3. Run usability checks | tap targets, text fit, navigation, critical visibility. | `usability_results` |
| 4. Run visual checks | mockups/screenshots for overlap and style drift. | `visual_results` |
| 5. Classify issues | Blocker, major, minor, warning. | `issues[]` |
| 6. Produce repair targets | Upstream file and field to revise. | `repair_plan[]` |
| 7. Decide status | Approved, needs revision, automation limited. | `acceptance` |

## Severity Model

| Severity | Meaning | Completion impact |
|---|---|---|
| `blocker` | Core flow, critical HUD, tap target, or screen is unusable. | Return `FAILED_VALIDATION`. |
| `major` | Important screen/state is unclear or inconsistent. | Return `NEEDS_REVISION`. |
| `minor` | Cosmetic issue that does not block use. | Return `COMPLETED_WITH_WARNINGS`. |
| `warning` | Missing optional evidence or fallback in use. | Return `COMPLETED_WITH_WARNINGS`. |

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/ui/ui-readability-qa-report.json` | yes | QA verdict, issues, evidence, repair plan. | Caller, diagnostics, upstream repair. |

## Invocation Contract

```json
{
  "skill": "game-ui/ui-readability-qa",
  "mode": "validate",
  "input_paths": {
    "ui_registry": ".allforai/game-design/ui/ui-registry.json",
    "ui_flow_map": ".allforai/game-design/ui/ui-flow-map.json",
    "hud_information": ".allforai/game-design/ui/hud-information-design.json",
    "screen_layout": ".allforai/game-design/ui/screen-layout-spec.json",
    "component_state": ".allforai/game-design/ui/component-state-spec.json",
    "mockup_manifest": ".allforai/game-design/ui/ui-mockup-manifest.json"
  },
  "evidence": {
    "screenshots": [],
    "browser_preview_url": null
  },
  "output_root": ".allforai/game-design/ui"
}
```

Supported modes:

| Mode | Behavior |
|---|---|
| `validate` | Run deterministic and available visual checks. |
| `validate_artifacts_only` | Run checks without images or browser. |
| `validate_screenshots` | Validate provided screenshots/mockups. |

## Automatic Validation

### Deterministic Checks

Run these checks whenever artifacts exist:
1. Every registered screen has flow, layout, or documented `not_applicable`
   status.
2. Every registered component has required states.
3. Every screen transition target has a layout.
4. Every critical HUD signal appears in a gameplay layout.
5. Every touch component has a minimum 44px target unless non-interactive.
6. Every text container has wrap, truncate, or resize behavior.
7. Every mockup target references a registered screen/component.
8. Every shared art reference exists or is marked placeholder.
9. No generated UI path escapes `.allforai/game-design/ui/`.

### Visual Checks

When mockups or screenshots exist, validate:
1. Critical HUD elements are visible and unobstructed.
2. Primary controls are visible and distinct.
3. Text is not cropped, overlapped, or too small.
4. Modals fit inside the viewport and have clear actions.
5. The playfield remains readable and not over-covered.
6. Button states are visually distinguishable.
7. UI palette and materials match the art style guide.
8. Safe-area issues are absent on mobile portrait and landscape.

## Repair Plan Rules

Each issue must name the upstream owner:
- flow issue -> `ui-flow-map.json`,
- missing HUD signal -> `hud-information-design.json`,
- overlap or safe-zone issue -> `screen-layout-spec.json`,
- missing state or tap target issue -> `component-state-spec.json`,
- mockup mismatch -> `ui-mockup-spec.json`,
- naming/path issue -> `ui-registry.json`.

## Completion Conditions

Return `COMPLETED` only when no blocker or major issues remain. Return
`FAILED_VALIDATION` for blockers. Return `COMPLETED_WITH_WARNINGS` when visual
evidence is unavailable but deterministic checks pass.
