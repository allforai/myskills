---
name: game-balance-20-spec-economy-source-sink-spec
description: Internal bundled meta-skill module for game-balance/20-spec/economy-source-sink-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Economy Source Sink Spec Skill

> Internal sub-skill for game-balance pipelines. Status: bundled, inactive, not wired.

## Overview

Specifies resource sources, sinks, caps, exchange rates, earning rates, spending rates, and deadlock prevention.

## Input Contract

Required: economy spec and balance goals.

Optional: player experience, game pillars, content taxonomy, target platform, runtime constraints, existing tables, and tuning notes.

## Output Contract

Writes:

- `.allforai/game-design/balance/economy-source-sink-spec.json`
- `.allforai/game-design/balance/economy-source-sink-spec-report.json`

Outputs must include `schema_version`, stable IDs, `source_refs`, `owner_skill_refs`, `consumer_refs`, `state`, validation notes, and repair targets.

Allowed states/statuses: `draft, validated, needs_revision, blocked_by_economy`.

## Invocation Contract

```json
{
  "skill": "game-balance/economy-source-sink-spec",
  "mode": "spec_validate",
  "input_paths": {},
  "output_root": ".allforai/game-design/balance"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check each spendable resource has reachable sources, meaningful sinks, caps when needed, and no infinite positive loops. Do not substitute missing numeric evidence with prose judgment.

Repair routing: missing economy semantics route to game-design/economy-spec; pricing gaps route to reward-pricing-spec.

## Completion Conditions

Return `COMPLETED` when source/sink loops are closed. Return `FAILED_VALIDATION` when resource can deadlock, inflate, or exploit.
