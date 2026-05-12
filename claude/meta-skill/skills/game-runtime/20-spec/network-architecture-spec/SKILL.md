---
name: game-runtime-20-spec-network-architecture-spec
description: Internal bundled meta-skill module for game-runtime/20-spec/network-architecture-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Network Architecture Spec Skill

> Internal sub-skill for game-runtime pipelines. Status: bundled, inactive, not wired.

## Overview

Defines implementation-facing multiplayer architecture: topology, authority,
replication, prediction, reconciliation, persistence, reconnect, failure
handling, observability, and executable validation. It consumes product-level
network play requirements from game design when present.

## Input Contract

Required: game mode spec, player experience contract, core loop, target
runtime/engine constraints, and multiplayer/network play requirements.

Optional: combat spec, matchmaking spec, anti-cheat architecture spec, account
requirements, save model, deployment constraints, and budget.

## Output Contract

Writes:

- `.allforai/game-runtime/network/network-architecture-spec.json`
- `.allforai/game-runtime/network/network-architecture-report.json`

Architecture entries must include `system_id`, `modes_supported`,
`topology`, `authority_model`, `replicated_state`, `client_prediction`,
`reconciliation_rule`, `tick_or_update_rate`, `latency_budget_ms`,
`bandwidth_budget`, `reconnect_rule`, `failure_modes`, `persistence_boundary`,
`observability`, `test_command_or_validation_path`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_runtime_unknown`, `blocked_by_network_requirements`,
`blocked_by_validation_unavailable`.

## Invocation Contract

```json
{
  "skill": "game-runtime/network-architecture-spec",
  "mode": "spec_validate",
  "input_paths": {
    "player_experience": ".allforai/game-design/design/player-experience-contract.json",
    "game_modes": ".allforai/game-design/systems/game-mode-spec.json",
    "core_loop": ".allforai/game-design/design/core-game-loop-spec.json"
  },
  "output_root": ".allforai/game-runtime/network"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every networked mode has authority, replicated state, failure
behavior, persistence boundary, and an executable validation path. If runtime
tools are missing or the app cannot run, return `blocked_by_validation_unavailable`.

Repair routing: missing player-facing requirements route to game-design network
requirements; mode ambiguity routes to `game-mode-spec`; runtime gaps route to
implementation feasibility QA.

## Completion Conditions

Return `COMPLETED` when network architecture can be implemented and validated.
Return `FAILED_VALIDATION` when a networked feature lacks authority, state,
failure, or testability.
