# Core Loop Design Skill

> Internal sub-skill for game-systems pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the primary game loop, session structure, goals, failure/retry rules,
player decisions, rewards, and mode boundaries.

## Input Contract

Required: concept and gameplay intent. Optional: UI flow, level flow, genre,
target session length.

## Output Contract

Writes `.allforai/game-design/systems/core-loop-design.json` and
`.allforai/game-design/systems/core-loop-report.json`.

Core loop schema:

```json
{
  "schema_version": "1.0",
  "loops": [
    {
      "loop_id": "primary",
      "entry_state": "main_menu",
      "player_actions": [],
      "system_responses": [],
      "feedback_events": [],
      "reward_events": [],
      "failure_states": [],
      "retry_rule": "restart_level | resume_checkpoint | abandon_run",
      "session_target_seconds": 180,
      "consumers": ["game-ui/ui-flow-design", "game-level/level-flow-design"]
    }
  ]
}
```

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_concept`.

## Invocation Contract

```json
{"skill":"game-systems/core-loop-design","mode":"design_validate","input_paths":{"concept_contract":".allforai/concept-contract.json","game_design_doc":".allforai/game-design/game-design-doc.json"},"output_root":".allforai/game-design/systems"}
```

Supported modes: `design_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check loop start/end, player action, feedback, reward, failure, retry, session
length, and compatibility with UI/level/audio/event pipelines.

Every loop must expose events that UI, audio, VFX, progression, and level skills
can reference. Missing event coverage is a contract defect, not a downstream
implementation detail.

Repair routing: missing gameplay purpose returns to the concept contract;
missing feedback/reward/failure events repair here; missing UI, level, audio, or
VFX implementation references route downstream only after loop event IDs are
stable.

## Completion Conditions

Return `COMPLETED` when core loop validates. Return `FAILED_VALIDATION` when no
gameplay loop can be inferred or loop events cannot be exposed to downstream
systems.
