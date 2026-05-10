# Matchmaking Service Spec Skill

> Internal sub-skill for game-runtime pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the service-facing matchmaking contract: queues, rating inputs,
eligibility, party/region/platform logic, expansion timeline, bot/backfill
policy, abuse hooks, observability, and automated service validation.

## Input Contract

Required: game mode spec, network architecture spec or network requirements,
player experience contract, and platform/region constraints.

Optional: competitive balance spec, progression spec, anti-cheat architecture,
account/social model, telemetry requirements, and deployment constraints.

## Output Contract

Writes:

- `.allforai/game-runtime/server/matchmaking-service-spec.json`
- `.allforai/game-runtime/server/matchmaking-service-report.json`

Queues must include `queue_id`, `mode_refs`, `eligibility_rule`,
`rating_inputs`, `party_rule`, `region_rule`, `platform_rule`,
`expansion_timeline`, `bot_policy`, `backfill_policy`, `target_wait_seconds`,
`quality_thresholds`, `abuse_controls`, `observability`,
`test_command_or_validation_path`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_mode`, `blocked_by_network_architecture`,
`blocked_by_population_model`, `blocked_by_validation_unavailable`.

## Invocation Contract

```json
{
  "skill": "game-runtime/matchmaking-service-spec",
  "mode": "spec_validate",
  "input_paths": {
    "game_modes": ".allforai/game-design/systems/game-mode-spec.json",
    "network_architecture": ".allforai/game-runtime/network/network-architecture-spec.json",
    "player_experience": ".allforai/game-design/design/player-experience-contract.json"
  },
  "output_root": ".allforai/game-runtime/server"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every multiplayer queue has a rating basis, eligibility, fallback,
observability, and executable validation path. Do not accept queue prose without
service-facing inputs, outputs, and failure behavior.

Repair routing: missing player-facing queue promise routes to game design;
missing networking routes to `network-architecture-spec`; abuse surfaces route
to `anti-cheat-architecture-spec`.

## Completion Conditions

Return `COMPLETED` when queues can be implemented and validated. Return
`FAILED_VALIDATION` when a queue lacks population assumptions, fairness signals,
fallback behavior, or testability.
