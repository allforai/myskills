# HUD Information Design Skill

> Internal sub-skill for game UI pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill decides what gameplay information must appear during play, when
it appears, how important it is, and how the HUD avoids hiding the playfield. It
produces an implementation-agnostic HUD information contract.

## Scope

In scope:
- HUD information inventory,
- priority and urgency,
- visibility rules,
- player attention rules,
- playfield protection,
- fallback HUD for small screens or automation limits.

Out of scope:
- final screen layout coordinates,
- component art generation,
- runtime code.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| Gameplay context | core loop, resources, health/failure, score/progress, controls | Infer minimal HUD once; if no gameplay loop exists, return `UPSTREAM_DEFECT`. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/game-design/ui/ui-registry.json` | HUD IDs, component IDs | Create planned HUD entries in output only. |
| `.allforai/game-design/game-design-doc.json` | stats, combat, economy, progression, timers | Use generic health/score/time model where relevant. |
| `.allforai/game-design/art-style-guide.json` | visual density, tone, camera/view | Use readable neutral UI. |
| `.allforai/game-design/asset-registry.json` | icon and portrait references | Use placeholder icon references. |

## Information Priority Model

| Priority | Meaning | Examples |
|---|---|---|
| `critical` | Player may fail if missed. | health, incoming danger, required action, timer under threshold. |
| `active` | Supports current decision. | ammo, cooldown, objective, combo, selected item. |
| `ambient` | Useful but not urgent. | score, coins, wave number, minimap. |
| `post_action` | Only needed after action completes. | rewards, XP gain, damage recap. |
| `hidden` | Not shown during gameplay. | settings, long descriptions, economy details. |

## Creative Workflow

| Stage | Purpose | Main output |
|---|---|---|
| 1. Identify gameplay decisions | What the player must know now. | `decision_points[]` |
| 2. Inventory signals | Health, score, resources, objectives, cooldowns. | `hud_signals[]` |
| 3. Assign priority | Critical, active, ambient, post-action, hidden. | `priority_map` |
| 4. Define visibility | Always, contextual, threshold, hidden. | `visibility_rules[]` |
| 5. Protect playfield | Reserve safe zones and occlusion limits. | `playfield_protection` |
| 6. Define fallback | Compact/small-screen HUD. | `fallback_hud` |
| 7. Validate | Check missing critical info and overload. | `hud_validation` |

## HUD Rules

- Critical information must be visible before the player needs it.
- The HUD must not cover the primary action lane, target reticle, player avatar,
  or enemy telegraph zone.
- Mobile HUD must keep touch controls away from critical labels.
- Contextual information should disappear when no longer actionable.
- Icons may reference `asset-registry.json`; do not duplicate icon generation
  here.
- Small-screen fallback must preserve critical information first.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/ui/hud-information-design.json` | yes | HUD signals, priority, visibility, playfield protection, fallback. | screen-layout-spec, component-state-spec, QA. |
| `.allforai/game-design/ui/hud-information-report.json` | yes | Validation, missing critical signals, overload warnings. | Diagnostics and QA. |

## Invocation Contract

```json
{
  "skill": "game-ui/hud-information-design",
  "mode": "design_validate",
  "input_paths": {
    "ui_registry": ".allforai/game-design/ui/ui-registry.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "asset_registry": ".allforai/game-design/asset-registry.json"
  },
  "target_view": "portrait | landscape | responsive",
  "output_root": ".allforai/game-design/ui"
}
```

Supported modes:

| Mode | Behavior |
|---|---|
| `design_validate` | Create HUD information contract and validate it. |
| `validate_existing` | Validate existing HUD information contract. |
| `compact_fallback` | Generate a small-screen fallback HUD. |

## Schema

```json
{
  "schema_version": "1.0",
  "hud_signals": [
    {
      "signal_id": "health",
      "meaning": "remaining failure buffer",
      "priority": "critical",
      "visibility": "always | contextual | threshold | hidden",
      "asset_refs": ["ico_health"],
      "update_rate": "realtime | event | low_frequency",
      "failure_if_missing": true
    }
  ],
  "playfield_protection": {
    "protected_regions": ["player_focus", "enemy_telegraph", "touch_controls"],
    "max_coverage_percent": 18
  },
  "fallback_hud": {}
}
```

## Automatic Validation

Run these checks:
1. Every critical gameplay failure condition has a visible HUD signal.
2. Every HUD signal has priority, visibility, and update rate.
3. No hidden signal is marked critical.
4. Playfield protection exists for gameplay screens.
5. Small-screen fallback includes all critical signals.
6. Icon references either exist in `asset-registry.json` or are marked
   placeholder.
7. Number of always-visible signals stays within target platform limits.

## Completion Conditions

Return `COMPLETED` only when critical information is covered and overload checks
pass. Return `COMPLETED_WITH_WARNINGS` when optional or cosmetic signals use
placeholders.
