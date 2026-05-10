# Core Game Loop Spec Skill

> Internal sub-skill for game-product pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the player's repeated action loop: goal, choice, action, feedback,
reward, progression, failure recovery, and next motivation.

## Input Contract

Required: player experience contract, game pillars, and registry.

Optional: mechanics notes, progression notes, economy notes, level concepts,
session length, and platform constraints.

## Output Contract

Writes:

- `.allforai/game-design/product/core-game-loop-spec.json`
- `.allforai/game-design/product/core-game-loop-report.json`

Loop entries must include `loop_id`, `loop_scope`, `entry_trigger`,
`player_goal`, `available_actions`, `feedback_channels`, `reward_outputs`,
`progression_outputs`, `failure_states`, `recovery_paths`,
`next_motivation`, `required_systems`, `required_content`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_missing_pillar`, `blocked_by_dead_loop`.

## Invocation Contract

```json
{
  "skill": "game-product/core-game-loop-spec",
  "mode": "spec_validate",
  "input_paths": {
    "player_experience": ".allforai/game-design/product/player-experience-contract.json",
    "pillars": ".allforai/game-design/product/game-pillar-spec.json",
    "registry": ".allforai/game-design/product/game-design-registry.json"
  },
  "output_root": ".allforai/game-design/product"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Every loop must have a clear action-feedback-reward chain, a next-step
motivation, and a failure recovery path. Reject loops that produce rewards with
no use, costs with no source, or objectives with no player action.

Repair routing: missing actions route to `mechanics-spec`; reward/progression
gaps route to `progression-spec` or `economy-spec`; level pacing gaps route to
`level-design-spec`.

## Completion Conditions

Return `COMPLETED` when all primary loops are closed and downstream systems are
declared. Return `FAILED_VALIDATION` when any required loop is dead or circular.
