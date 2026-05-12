---
name: game-level-20-spec-reward-placement-spec
description: Internal bundled meta-skill module for game-level/20-spec/reward-placement-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Reward Placement Spec Skill

> Internal sub-skill for game-level pipelines. Status: bundled, inactive, not wired.

## Overview

Defines reward placement in levels: pickups, chests, exits, secrets, shops,
quest rewards, and economy/progression pacing.

## Input Contract

Required: level layout spec and economy/progression context.

Optional: level difficulty budget, encounter placement, content roadmap, drop
tables, and UI feedback requirements.

## Output Contract

Writes `.allforai/game-design/levels/reward-placement-spec.json` and a report.
Rewards include `reward_placement_id`, `level_id`, `region_ref`, `reward_ref`,
`visibility`, `risk_cost`, `access_rule`, `pacing_role`,
`difficulty_budget_ref`, `recovery_budget_ref`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_economy`.

## Invocation Contract

```json
{
  "skill": "game-level/reward-placement-spec",
  "mode": "spec_validate",
  "input_paths": {
    "level_layout": ".allforai/game-design/levels/level-layout-spec.json",
    "economy": ".allforai/game-design/systems/product-economy-spec.json",
    "progression": ".allforai/game-design/systems/progression-spec.json",
    "difficulty_budget": ".allforai/game-design/levels/level-difficulty-budget-spec.json",
    "encounter_placement": ".allforai/game-design/levels/encounter-placement-spec.json"
  },
  "output_root": ".allforai/game-design/levels"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check reward reachability, risk/reward fit, economy pacing, visibility,
backtracking cost, and whether mandatory rewards are missable. When a level
difficulty budget is present, verify rewards provide the declared relief,
recovery, confidence repair, resource refill, and motivation payoff after the
pressure they are meant to resolve.

Repair routing: economy gaps route to reward-pricing/economy specs; layout gaps
route to level-layout-spec; difficulty/recovery mismatches route to
level-difficulty-budget-spec; content gaps route to content registry.

## Completion Conditions

Return `COMPLETED` when rewards are placed and paced. Return
`FAILED_VALIDATION` when mandatory rewards are unreachable or economy-breaking.
