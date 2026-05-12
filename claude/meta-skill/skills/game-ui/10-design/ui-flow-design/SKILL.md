---
name: game-ui-10-design-ui-flow-design
description: Internal bundled meta-skill module for game-ui/10-design/ui-flow-design; use within generated bootstrap node-specs when this exact contract is selected.
---

# UI Flow Design Skill

> Internal sub-skill for game UI pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill defines how players move between screens, overlays, modals, and
gameplay states. It turns gameplay structure into a machine-readable UI flow map
with entry points, exits, transitions, blocked states, and recovery paths.

## Scope

In scope:
- screen graph,
- modal and overlay behavior,
- first-session and repeat-session flows,
- pause, settings, failure, and recovery paths,
- screen transition intent,
- automatic validation and repair at the flow level.

Out of scope:
- visual layout details,
- component styling,
- final mockup generation,
- frontend implementation.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| `.allforai/game-design/ui/ui-registry.json` or screen list | `screens[].screen_id` | Return `UPSTREAM_DEFECT`; no screen IDs exist. |
| Gameplay context | game loop, start condition, failure/success condition | Infer minimal arcade flow once; if impossible, return `UPSTREAM_DEFECT`. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/game-design/game-design-doc.json` | loops, modes, progression, economy, sessions | Use minimal `main_menu -> gameplay -> results` flow. |
| `.allforai/concept-contract.json` | product promise, target user, tone | Use neutral game UI tone. |
| Caller context | required screens, platform, onboarding need | Use no-onboarding default for simple games. |

## Creative Workflow

| Stage | Purpose | Main output |
|---|---|---|
| 1. Identify session types | First play, repeat play, failed run, completed run. | `session_flows[]` |
| 2. Build screen graph | Define nodes and legal transitions. | `screen_graph` |
| 3. Define overlays | Pause, settings, confirmation, error, reward. | `overlays[]` |
| 4. Define blockers | Loading, locked content, insufficient currency, missing save. | `blocked_states[]` |
| 5. Recovery paths | Back, cancel, retry, resume, restore. | `recovery_paths[]` |
| 6. Validate | Check reachability and dead ends. | `flow_validation` |

## Flow Rules

- Every game must have a valid path to gameplay.
- Every gameplay state must have a pause or exit path unless the game genre
  explicitly forbids interruption.
- Every modal must have an explicit close, confirm, or cancel rule.
- Every failure state must have a retry or return path.
- Every purchase, delete, quit, or irreversible action must have confirmation.
- Onboarding must be skippable after first completion unless gameplay depends
  on a tutorial state.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/ui/ui-flow-map.json` | yes | Screen graph, transitions, overlays, blocked states, recovery paths. | screen-layout-spec, frontend, QA. |
| `.allforai/game-design/ui/ui-flow-report.json` | yes | Validation, reachability, dead ends, repairs. | Diagnostics and QA. |

## Invocation Contract

```json
{
  "skill": "game-ui/ui-flow-design",
  "mode": "design_validate",
  "input_paths": {
    "ui_registry": ".allforai/game-design/ui/ui-registry.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "concept_contract": ".allforai/concept-contract.json"
  },
  "flow_filter": {
    "screen_ids": [],
    "session_types": []
  },
  "output_root": ".allforai/game-design/ui"
}
```

Supported modes:

| Mode | Behavior |
|---|---|
| `design_validate` | Create and validate flow map. |
| `validate_existing` | Validate an existing flow map. |
| `repair_existing` | Repair reachability, missing exits, and invalid modal behavior. |

## Flow Map Schema

```json
{
  "schema_version": "1.0",
  "screens": [
    {
      "screen_id": "screen_main_menu",
      "entry_conditions": ["app_start"],
      "exit_transitions": [
        {
          "to": "screen_gameplay",
          "trigger": "start_game",
          "transition": "instant | fade | slide | gameplay_safe"
        }
      ],
      "overlays_allowed": ["overlay_settings"],
      "back_behavior": "exit_app | previous_screen | close_overlay | disabled"
    }
  ],
  "overlays": [],
  "blocked_states": [],
  "recovery_paths": []
}
```

## Automatic Validation

Run these checks:
1. Every `screen_id` exists in `ui-registry.json`.
2. The graph has at least one app entry node.
3. Gameplay is reachable from an entry node.
4. Every non-terminal screen has an exit.
5. Every modal/overlay has close behavior.
6. Every transition target exists.
7. Back behavior is defined for every screen.
8. Failure and results screens can return or retry.

## Completion Conditions

Return `COMPLETED` only when the flow map is valid and every required screen is
reachable. Return `FAILED_VALIDATION` if a dead end cannot be repaired without a
missing upstream gameplay decision.
