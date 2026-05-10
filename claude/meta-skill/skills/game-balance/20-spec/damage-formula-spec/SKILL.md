# Damage Formula Spec Skill

> Internal sub-skill for game-balance pipelines. Status: bundled, inactive, not wired.

## Overview

Specifies damage, defense, crit, scaling, status, healing, survivability, and TTK formulas.

## Input Contract

Required: combat spec, mechanics spec, and balance goals.

Optional: player experience, game pillars, content taxonomy, target platform, runtime constraints, existing tables, and tuning notes.

## Output Contract

Writes:

- `.allforai/game-design/balance/damage-formula-spec.json`
- `.allforai/game-design/balance/damage-formula-spec-report.json`

Outputs must include `schema_version`, stable IDs, `source_refs`, `owner_skill_refs`, `consumer_refs`, `state`, validation notes, and repair targets.

Allowed states/statuses: `not_applicable, draft, validated, needs_revision, blocked_by_combat`.

## Invocation Contract

```json
{
  "skill": "game-balance/damage-formula-spec",
  "mode": "spec_validate",
  "input_paths": {},
  "output_root": ".allforai/game-design/balance"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check formulas resolve inputs, produce expected TTK bands, preserve counterplay, and avoid overflow/negative invalid states. Do not substitute missing numeric evidence with prose judgment.

Repair routing: missing combat routes to game-design/combat-spec; outliers route to combat-balance-qa.

## Completion Conditions

Return `COMPLETED` when combat formulas are executable or not applicable. Return `FAILED_VALIDATION` when formulas produce invalid or unreadable combat.
