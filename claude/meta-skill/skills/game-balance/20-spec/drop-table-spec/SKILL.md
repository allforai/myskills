---
name: game-balance-20-spec-drop-table-spec
description: Internal bundled meta-skill module for game-balance/20-spec/drop-table-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Drop Table Spec Skill

> Internal sub-skill for game-balance pipelines. Status: bundled, inactive, not wired.

## Overview

Specifies loot/drop probability, rarity, pity, guarantees, expected value, and content ownership.

## Input Contract

Required: content taxonomy, economy spec, and balance goals.

Optional: player experience, game pillars, content taxonomy, target platform, runtime constraints, existing tables, and tuning notes.

## Output Contract

Writes:

- `.allforai/game-design/balance/drop-table-spec.json`
- `.allforai/game-design/balance/drop-table-spec-report.json`

Outputs must include `schema_version`, stable IDs, `source_refs`, `owner_skill_refs`, `consumer_refs`, `state`, validation notes, and repair targets.

Allowed states/statuses: `draft, validated, needs_revision, blocked_by_content`.

## Invocation Contract

```json
{
  "skill": "game-balance/drop-table-spec",
  "mode": "spec_validate",
  "input_paths": {},
  "output_root": ".allforai/game-design/balance"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check probabilities sum correctly, expected value is within target range, pity/guarantees are explicit, and drops resolve to content IDs. Do not substitute missing numeric evidence with prose judgment.

Repair routing: missing items route to game-content or content-taxonomy-spec; economy value gaps route to reward-pricing-spec.

## Completion Conditions

Return `COMPLETED` when drop tables are coherent and traceable. Return `FAILED_VALIDATION` when probabilities or referenced rewards are invalid.
