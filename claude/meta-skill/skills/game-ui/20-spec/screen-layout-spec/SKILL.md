# Screen Layout Spec Skill

> Internal sub-skill for game UI pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill converts UI flow and HUD information contracts into responsive
screen layout specifications. It defines regions, hierarchy, safe zones,
breakpoints, navigation placement, and playfield protection without writing
runtime code.

## Scope

In scope:
- screen regions,
- responsive breakpoints,
- safe zones,
- HUD placement,
- menu and modal layout,
- density rules,
- automatic layout validation.

Out of scope:
- component visual states,
- final raster mockups,
- frontend implementation.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| `.allforai/game-design/ui/ui-registry.json` | `screens[]`, `components[]` | Return `UPSTREAM_DEFECT`. |
| `.allforai/game-design/ui/ui-flow-map.json` | screen graph and overlays | Infer no-overlay layout once; otherwise warn. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/game-design/ui/hud-information-design.json` | HUD signals, protected regions | Use generic gameplay HUD safe zones. |
| `.allforai/game-design/art-style-guide.json` | density, camera, tone | Use readable neutral layout. |
| Caller context | viewport sizes, platform, orientation | Use responsive web defaults: 390x844, 768x1024, 1440x900. |

## Layout Workflow

| Stage | Purpose | Main output |
|---|---|---|
| 1. Select screens | Determine layout targets. | `selected_screens[]` |
| 2. Define regions | Header, footer, content, playfield, side panels. | `regions[]` |
| 3. Place critical elements | HUD, primary action, navigation. | `placement_rules[]` |
| 4. Define breakpoints | Mobile, tablet, desktop, orientation. | `breakpoints[]` |
| 5. Define modals | Bounds, scrim, focus, dismissal. | `modal_layouts[]` |
| 6. Validate | Overlap, safe zones, unreachable actions. | `layout_validation` |

## Layout Rules

- Gameplay screens must reserve a `playfield` region.
- HUD must not occupy protected playfield regions from
  `hud-information-design.json`.
- Primary actions must be reachable on mobile without crossing critical HUD
  labels.
- Modal content must fit the smallest target viewport.
- Navigation must have deterministic back/close behavior from `ui-flow-map`.
- Avoid text-heavy layout on gameplay screens; move explanations to pause,
  tutorial, or results screens.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/ui/screen-layout-spec.json` | yes | Layout regions, breakpoints, safe zones, modal specs. | component-state-spec, mockup-generation, frontend, QA. |
| `.allforai/game-design/ui/screen-layout-report.json` | yes | Validation results, repaired conflicts, warnings. | Diagnostics and QA. |

## Invocation Contract

```json
{
  "skill": "game-ui/screen-layout-spec",
  "mode": "spec_validate",
  "input_paths": {
    "ui_registry": ".allforai/game-design/ui/ui-registry.json",
    "ui_flow_map": ".allforai/game-design/ui/ui-flow-map.json",
    "hud_information": ".allforai/game-design/ui/hud-information-design.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json"
  },
  "viewports": [
    {"name": "mobile", "width": 390, "height": 844},
    {"name": "tablet", "width": 768, "height": 1024},
    {"name": "desktop", "width": 1440, "height": 900}
  ],
  "output_root": ".allforai/game-design/ui"
}
```

Supported modes:

| Mode | Behavior |
|---|---|
| `spec_validate` | Create layout spec and validate it. |
| `validate_existing` | Validate an existing layout spec. |
| `repair_existing` | Repair overlap, missing safe zones, and breakpoint gaps. |

## Schema

```json
{
  "schema_version": "1.0",
  "screens": [
    {
      "screen_id": "screen_gameplay",
      "layout_type": "gameplay | menu | modal | list | shop | results",
      "breakpoints": [
        {
          "name": "mobile",
          "regions": [
            {
              "region_id": "playfield",
              "bounds": {"x": 0, "y": 0, "w": 390, "h": 844},
              "protected": true
            }
          ],
          "safe_zones": []
        }
      ],
      "navigation": {"back_behavior": "pause"}
    }
  ]
}
```

## Automatic Validation

Run these checks:
1. Every screen in the flow map has a layout entry.
2. Every required breakpoint exists for every target screen.
3. Regions do not overlap unless marked as overlay.
4. Critical HUD regions avoid protected playfield zones.
5. Primary actions have reachable placement on mobile.
6. Modal bounds fit the smallest viewport.
7. Every transition in `ui-flow-map` has a source and target layout.
8. Text containers have max width and wrapping rules.

## Completion Conditions

Return `COMPLETED` only when all target screens have valid responsive layouts.
Return `COMPLETED_WITH_WARNINGS` when optional screens are planned but not yet
laid out.
