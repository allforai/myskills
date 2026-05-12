---
name: game-ui-20-spec-component-state-spec
description: Internal bundled meta-skill module for game-ui/20-spec/component-state-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Component State Spec Skill

> Internal sub-skill for game UI pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill defines UI components and all states needed for gameplay menus,
HUDs, overlays, and feedback. It creates a component state contract that can be
used by mockup generation, frontend implementation, and QA.

## Scope

In scope:
- buttons, toggles, sliders, bars, badges, cards, modals, list rows, tabs,
  icons, control prompts,
- default/hover/pressed/focused/disabled/loading/error/selected states,
- state transitions and feedback,
- accessibility and touch target rules,
- validation for missing states.

Out of scope:
- screen graph,
- final screen layout,
- final frontend implementation.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| `.allforai/game-design/ui/ui-registry.json` | `components[]` | Return `UPSTREAM_DEFECT`; no components exist. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/game-design/ui/screen-layout-spec.json` | component placement, density, viewport constraints | Use platform default sizing. |
| `.allforai/game-design/ui/hud-information-design.json` | HUD signal semantics | Use generic HUD component states. |
| `.allforai/game-design/art-style-guide.json` | visual tone, color mood, icon style | Use neutral readable game UI style. |
| `.allforai/game-design/asset-registry.json` | icon refs and portrait refs | Use placeholder refs. |

## Component Vocabulary

Use these canonical roles:

```json
[
  "primary_button",
  "secondary_button",
  "icon_button",
  "toggle",
  "slider",
  "resource_bar",
  "progress_bar",
  "status_badge",
  "item_card",
  "skill_card",
  "modal",
  "toast",
  "tab",
  "list_row",
  "control_prompt",
  "currency_display"
]
```

## Required States

| Component kind | Required states |
|---|---|
| Button | `default`, `hover`, `pressed`, `focused`, `disabled`, `loading` |
| Toggle | `off`, `on`, `focused`, `disabled` |
| Slider | `default`, `dragging`, `focused`, `disabled` |
| Resource bar | `normal`, `low`, `critical`, `gain`, `loss`, `empty`, `full` |
| Card | `default`, `selected`, `locked`, `disabled`, `new`, `upgradable` |
| Modal | `entering`, `open`, `confirming`, `closing`, `blocked` |
| Toast | `info`, `success`, `warning`, `error`, `expired` |

## State Workflow

| Stage | Purpose | Main output |
|---|---|---|
| 1. Classify components | Map components to canonical kind. | `component_kind` |
| 2. Assign required states | Add state set by kind. | `states[]` |
| 3. Define visual tokens | Colors, type, spacing, icon usage. | `style_tokens` |
| 4. Define interactions | Hover, press, focus, drag, disable. | `interaction_rules` |
| 5. Define feedback | Sound cue refs, motion cue refs, toasts. | `feedback_rules` |
| 6. Validate | Missing states, unreadable states, tap targets. | `component_validation` |

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/ui/component-state-spec.json` | yes | Canonical component states, tokens, interactions, refs. | mockup-generation, frontend, QA. |
| `.allforai/game-design/ui/component-state-report.json` | yes | Missing states, conflicts, repair log. | Diagnostics and QA. |

## Invocation Contract

```json
{
  "skill": "game-ui/component-state-spec",
  "mode": "spec_validate",
  "input_paths": {
    "ui_registry": ".allforai/game-design/ui/ui-registry.json",
    "screen_layout": ".allforai/game-design/ui/screen-layout-spec.json",
    "hud_information": ".allforai/game-design/ui/hud-information-design.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "asset_registry": ".allforai/game-design/asset-registry.json"
  },
  "output_root": ".allforai/game-design/ui"
}
```

Supported modes:

| Mode | Behavior |
|---|---|
| `spec_validate` | Create component state spec and validate it. |
| `validate_existing` | Validate an existing component state spec. |
| `repair_existing` | Add missing states and fix invalid interactions. |

## Schema

```json
{
  "schema_version": "1.0",
  "components": [
    {
      "component_id": "cmp_primary_button",
      "kind": "primary_button",
      "states": [
        {
          "state": "default",
          "visual": {
            "token_refs": ["button.primary.fill", "text.on_primary"],
            "icon_ref": null
          },
          "interaction": {"enabled": true, "tap_target_min_px": 44}
        }
      ],
      "transitions": []
    }
  ]
}
```

## Automatic Validation

Run these checks:
1. Every component exists in `ui-registry.json`.
2. Every component has a canonical kind.
3. Required states exist for each component kind.
4. Disabled/loading/locked states are visually distinct from default.
5. Tap targets are at least 44px for touch platforms unless marked
   non-interactive.
6. Icon references exist or are marked placeholder.
7. Text-bearing components define wrapping or truncation behavior.
8. Critical HUD components define low/critical feedback states.

## Completion Conditions

Return `COMPLETED` only when all registered components have valid state specs.
Return `COMPLETED_WITH_WARNINGS` when optional icon or sound references are
placeholders.
