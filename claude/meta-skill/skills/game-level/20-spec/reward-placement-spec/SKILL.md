# Reward Placement Spec Skill

> Internal sub-skill for game-level pipelines. Status: bundled, inactive, not wired.

## Overview

Defines reward placement in levels: pickups, chests, exits, secrets, shops,
quest rewards, and economy/progression pacing.

## Input Contract

Required: level layout spec and economy/progression context.

Optional: encounter placement, content roadmap, drop tables, and UI feedback
requirements.

## Output Contract

Writes `.allforai/game-design/levels/reward-placement-spec.json` and a report.
Rewards include `reward_placement_id`, `level_id`, `region_ref`, `reward_ref`,
`visibility`, `risk_cost`, `access_rule`, `pacing_role`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_economy`.

## Invocation Contract

```json
{"skill":"game-level/reward-placement-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/levels"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check reward reachability, risk/reward fit, economy pacing, visibility,
backtracking cost, and whether mandatory rewards are missable.

Repair routing: economy gaps route to reward-pricing/economy specs; layout gaps
route to level-layout-spec; content gaps route to content registry.

## Completion Conditions

Return `COMPLETED` when rewards are placed and paced. Return
`FAILED_VALIDATION` when mandatory rewards are unreachable or economy-breaking.
