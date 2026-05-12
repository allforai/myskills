---
name: game-balance-40-qa-combat-balance-qa
description: Internal bundled meta-skill module for game-balance/40-qa/combat-balance-qa; use within generated bootstrap node-specs when this exact contract is selected.
---

# Combat Balance QA Skill

> Internal sub-skill for game-balance pipelines. Status: bundled, inactive, not wired.

## Overview

Validates combat numeric balance including TTK, DPS, survivability, counterplay, skill cost, and outliers.

## Input Contract

Required: damage formula spec, enemy list, item/skill list, and balance tables.

Optional: player experience, game pillars, content taxonomy, target platform, runtime constraints, existing tables, and tuning notes.

## Output Contract

Writes:

- `.allforai/game-design/balance/combat-balance-qa-report.json`
- `.allforai/game-design/balance/combat-balance-qa-report-report.json`

Outputs must include `schema_version`, stable IDs, `source_refs`, `owner_skill_refs`, `consumer_refs`, `state`, validation notes, and repair targets.

Allowed states/statuses: `passed, passed_with_warnings, needs_revision, blocked_by_missing_spec, failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-balance/combat-balance-qa",
  "mode": "spec_validate",
  "input_paths": {},
  "output_root": ".allforai/game-design/balance"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check TTK/DPS ranges, class/enemy outliers, survivability bands, dominant strategies, and missing counterplay. Do not substitute missing numeric evidence with prose judgment.

Repair routing: formula defects route to damage-formula-spec; roster defects route to enemy-design-list-generation; skill defects route to item-skill-design-generation.

## Completion Conditions

Return `COMPLETED` when no blocker combat balance issues exist. Return `FAILED_VALIDATION` when required combat numeric evidence is missing or invalid.
