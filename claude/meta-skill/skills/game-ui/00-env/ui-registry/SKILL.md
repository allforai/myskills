---
name: game-ui-00-env-ui-registry
description: Internal bundled meta-skill module for game-ui/00-env/ui-registry; use within generated bootstrap node-specs when this exact contract is selected.
---

# UI Registry Skill

> Internal sub-skill for game UI pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill defines the canonical registry for UI screens, UI components, UI
assets, and their file prefixes. It prevents downstream UI skills from inventing
alternate names and gives the code, art, and QA flows a shared source of truth.

## Scope

Use this skill when a UI flow needs:
- deterministic `screen_id`, `component_id`, `ui_asset_id`, and `file_prefix`
  values,
- paths for screen specs, component specs, mockups, and exported UI art,
- lifecycle states for UI artifacts,
- references to shared game-art assets such as icons, portraits, items, and
  currencies,
- validation that UI IDs do not collide with game-art asset IDs.

Out of scope:
- Designing screen flows.
- Designing HUD information hierarchy.
- Producing mockup images.
- Implementing frontend code.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| `.allforai/game-design/game-design-doc.json` or caller UI inventory | major modes, loops, screens, player actions | Infer minimal UI set once; if no gameplay context exists, return `UPSTREAM_DEFECT`. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/concept-contract.json` | product tone, canonical registry, naming | Derive from game design. |
| `.allforai/game-design/art-style-guide.json` | style, tone, typography hints, color mood | Use neutral readable UI defaults. |
| `.allforai/game-design/asset-registry.json` | icons, portraits, items, currencies, character art | Register UI references as unresolved. |
| Caller context | target platform, orientation, required screens | Use responsive web/mobile-safe defaults. |

## Default UI Inventory

If no explicit UI inventory exists, infer a minimal set:

```json
{
  "screens": ["boot", "main_menu", "gameplay", "pause", "settings", "results"],
  "components": ["primary_button", "secondary_button", "modal", "resource_bar", "status_badge"],
  "ui_assets": ["button_panel", "panel_frame", "currency_icon_placeholder"]
}
```

Add screens only when gameplay requires them: `inventory`, `shop`, `level_select`,
`character_select`, `quest_log`, `dialogue`, `battle_results`, `upgrade`, and
`leaderboard`.

## ID Rules

| Entity | ID rule | Prefix rule |
|---|---|---|
| Screen | `screen_<purpose>` | `ui_screen_<purpose>` |
| HUD area | `hud_<purpose>` | `ui_hud_<purpose>` |
| Component | `cmp_<role>` | `ui_cmp_<role>` |
| UI asset | `ui_<asset>` | `ui_asset_<asset>` |
| Icon reference | use existing `asset_id` when present | do not mint duplicate art asset |

Rules:
- IDs must be lowercase snake-case.
- Do not reuse a world-art `asset_id` as a UI asset ID unless referencing it.
- Once this skill runs, downstream UI skills must use these IDs.
- If a caller passes a conflicting ID, return `FAILED_VALIDATION`.

## Lifecycle States

| State | Meaning |
|---|---|
| `planned` | Required but not specified. |
| `spec_ready` | Structural spec exists and validates. |
| `mockup_ready` | Visual mockup exists or mockup spec is ready. |
| `implemented` | Runtime UI code exists. |
| `qa_ready` | Screenshot or mockup is ready for validation. |
| `approved` | Automatic QA passed. |
| `needs_revision` | Validation failed and can be repaired. |
| `automation_limited` | Automation can produce a fallback only. |
| `not_applicable` | Not required for this game. |

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/ui/ui-registry.json` | yes | Canonical UI IDs, paths, states, shared asset references. | All game-ui sub-skills, frontend, QA. |
| `.allforai/game-design/ui/ui-registry-report.json` | yes | Validation results, missing dependencies, conflicts. | Diagnostics and QA. |

## Invocation Contract

```json
{
  "skill": "game-ui/ui-registry",
  "mode": "build_or_update",
  "input_paths": {
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "concept_contract": ".allforai/concept-contract.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "asset_registry": ".allforai/game-design/asset-registry.json"
  },
  "platform": {
    "target": "web | mobile | desktop | unknown",
    "orientation": "portrait | landscape | responsive"
  },
  "output_root": ".allforai/game-design/ui"
}
```

Supported modes:

| Mode | Behavior |
|---|---|
| `build_or_update` | Build registry and preserve existing stable IDs. |
| `validate_existing` | Validate registry against current artifacts. |
| `resolve_ids` | Return canonical IDs and paths for selected screens/components. |
| `register_outputs` | Register outputs from downstream UI-producing skills. |

## Registry Schema

Write `.allforai/game-design/ui/ui-registry.json`:

```json
{
  "schema_version": "1.0",
  "output_root": ".allforai/game-design/ui",
  "style_sources": {
    "concept_contract": ".allforai/concept-contract.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "asset_registry": ".allforai/game-design/asset-registry.json"
  },
  "screens": [
    {
      "screen_id": "screen_gameplay",
      "name": "Gameplay",
      "file_prefix": "ui_screen_gameplay",
      "state": "planned",
      "paths": {
        "flow": ".allforai/game-design/ui/flows/ui_screen_gameplay.json",
        "layout": ".allforai/game-design/ui/screens/ui_screen_gameplay.json",
        "mockup": ".allforai/game-design/ui/mockups/ui_screen_gameplay.png"
      },
      "components": ["cmp_primary_button"],
      "referenced_assets": []
    }
  ],
  "components": [
    {
      "component_id": "cmp_primary_button",
      "role": "primary_action",
      "file_prefix": "ui_cmp_primary_button",
      "state": "planned",
      "paths": {
        "spec": ".allforai/game-design/ui/components/ui_cmp_primary_button.json",
        "art": ".allforai/game-design/ui/art/ui_cmp_primary_button.png"
      }
    }
  ],
  "ui_assets": []
}
```

## Automatic Validation

Run these checks:
1. IDs are lowercase snake-case and unique within their entity type.
2. UI IDs do not accidentally collide with game-art `asset_id` values.
3. Every path starts with `.allforai/game-design/ui/`.
4. Every screen references only registered components.
5. Every referenced game-art asset exists or is marked `unresolved_reference`.
6. Every entity has a lifecycle state.
7. Existing stable IDs are preserved across updates.

## Completion Conditions

Return `COMPLETED` only when:
- `ui-registry.json` exists and validates,
- `ui-registry-report.json` exists and validates,
- all required screens/components have canonical IDs and paths.

Return `COMPLETED_WITH_WARNINGS` when optional shared art references are missing
but placeholder UI can proceed.
