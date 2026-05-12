---
name: game-design-20-spec-game-mode-spec
description: Internal bundled meta-skill module for game-design/20-spec/game-mode-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Game Mode Spec Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Defines playable game modes such as campaign, stage, challenge, endless,
practice, co-op, PvP, daily, event, sandbox, and tutorial modes, including how
each mode uses the core loop, content, rewards, difficulty, UI, and runtime
state.

## Input Contract

Required: game-design registry, player experience contract, core game loop, and
game pillars.

Optional: progression spec, economy spec, content taxonomy, level design spec,
combat spec, onboarding spec, liveops spec, target platform, and multiplayer
constraints.

## Output Contract

Writes `.allforai/game-design/design/game-mode-spec.json`.

Each mode includes `mode_id`, `mode_name`, `player_intent`, `entry_condition`,
`exit_condition`, `session_length_target`, `loop_refs`, `objective_refs`,
`content_refs`, `difficulty_rule`, `reward_rule`, `failure_rule`,
`matchmaking_or_party_rule`, `save_state_rule`, `ui_requirements`,
`telemetry_requirements`, `runtime_requirements`, `unlock_rule`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_core_loop`, `blocked_by_content`.

## Invocation Contract

```json
{
  "skill": "game-design/game-mode-spec",
  "mode": "spec_validate",
  "input_paths": {
    "registry": ".allforai/game-design/design/game-design-registry.json",
    "core_loop": ".allforai/game-design/design/core-game-loop-spec.json"
  },
  "output_root": ".allforai/game-design/design"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every mode has a distinct player intent, valid entry and exit condition,
owned content source, objective structure, reward/failure rule, UI entry point,
and runtime state rule. Check that modes do not duplicate each other unless
they serve different audience, session, difficulty, or reward needs.

Reject modes that cannot be reached, completed, failed, rewarded, or tested.
If multiplayer, matchmaking, or event infrastructure is required but undefined,
return `FAILED_VALIDATION`; do not replace it with a single-player assumption.

Repair routing: missing loop ownership routes to `core-game-loop-spec`; missing
objectives route to `objective-system-spec`; missing content routes to
`content-taxonomy-spec`; reward gaps route to `economy-spec`; difficulty gaps
route to `difficulty-experience-spec`.

## Completion Conditions

Return `COMPLETED` when each selected mode is playable, distinguishable,
traceable, and testable. Return `FAILED_VALIDATION` when a mode cannot be
entered, resolved, rewarded, or implemented with declared constraints.
