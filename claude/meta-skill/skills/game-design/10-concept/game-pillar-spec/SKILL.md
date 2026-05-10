# Game Pillar Spec Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the design pillars that guide design tradeoffs. Pillars are enforceable
constraints, not marketing slogans.

## Input Contract

Required: player experience contract and game-design registry.

Optional: product concept, target platform, monetization stance, known risks,
and competitor/reference notes.

## Output Contract

Writes:

- `.allforai/game-design/design/game-pillar-spec.json`
- `.allforai/game-design/design/game-pillar-report.json`

Each pillar must include `pillar_id`, `statement`, `player_value`,
`design_constraints`, `positive_examples`, `negative_examples`,
`tradeoff_rules`, `acceptance_signals`, `affected_systems`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_player_contract`.

## Invocation Contract

```json
{
  "skill": "game-design/game-pillar-spec",
  "mode": "spec_validate",
  "input_paths": {
    "player_experience": ".allforai/game-design/design/player-experience-contract.json",
    "registry": ".allforai/game-design/design/game-design-registry.json"
  },
  "output_root": ".allforai/game-design/design"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Require 3-5 pillars unless the game is intentionally tiny. Check that each
pillar has observable acceptance signals and rejects at least one tempting but
wrong design direction.

Repair routing: vague player value routes to `player-experience-contract`;
mechanical contradictions route to `mechanics-spec`; feasibility contradictions
route to `implementation-feasibility-qa`.

## Completion Conditions

Return `COMPLETED` when all pillars are testable and mapped to downstream
systems. Return `FAILED_VALIDATION` when pillars are vague or contradictory.
