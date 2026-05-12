---
name: game-balance-20-spec-reward-pricing-spec
description: Internal bundled meta-skill module for game-balance/20-spec/reward-pricing-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Reward Pricing Spec Skill

> Internal sub-skill for game-balance pipelines. Status: bundled, inactive, not wired.

## Overview

Specifies rewards, prices, upgrade costs, offer values, affordability, and value anchors.

## Input Contract

Required: economy source/sink spec and progression curve spec.

Optional: player experience, game pillars, content taxonomy, target platform, runtime constraints, existing tables, and tuning notes.

## Output Contract

Writes:

- `.allforai/game-design/balance/reward-pricing-spec.json`
- `.allforai/game-design/balance/reward-pricing-spec-report.json`

Outputs must include `schema_version`, stable IDs, `source_refs`, `owner_skill_refs`, `consumer_refs`, `state`, validation notes, and repair targets.

Allowed states/statuses: `draft, validated, needs_revision, blocked_by_economy`.

## Invocation Contract

```json
{
  "skill": "game-balance/reward-pricing-spec",
  "mode": "spec_validate",
  "input_paths": {},
  "output_root": ".allforai/game-design/balance"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check prices are affordable within intended sessions, rewards have purpose, and value anchors do not contradict monetization fairness. Do not substitute missing numeric evidence with prose judgment.

Repair routing: unreachable costs route to economy-source-sink-spec; reward gaps route to progression-curve-spec.

## Completion Conditions

Return `COMPLETED` when prices and rewards fit pacing goals. Return `FAILED_VALIDATION` when mandatory costs are unreachable or rewards are useless.
