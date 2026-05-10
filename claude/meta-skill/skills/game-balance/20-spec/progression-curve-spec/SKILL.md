# Progression Curve Spec Skill

> Internal sub-skill for game-balance pipelines. Status: bundled, inactive, not wired.

## Overview

Specifies level, XP, unlock, power, mastery, and session pacing curves.

## Input Contract

Required: balance goals and progression spec.

Optional: player experience, game pillars, content taxonomy, target platform, runtime constraints, existing tables, and tuning notes.

## Output Contract

Writes:

- `.allforai/game-design/balance/progression-curve-spec.json`
- `.allforai/game-design/balance/progression-curve-spec-report.json`

Outputs must include `schema_version`, stable IDs, `source_refs`, `owner_skill_refs`, `consumer_refs`, `state`, validation notes, and repair targets.

Allowed states/statuses: `draft, validated, needs_revision, blocked_by_progression`.

## Invocation Contract

```json
{
  "skill": "game-balance/progression-curve-spec",
  "mode": "spec_validate",
  "input_paths": {},
  "output_root": ".allforai/game-design/balance"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check reachability, reward usefulness, curve monotonicity where required, pacing bands, and dead-end unlocks. Do not substitute missing numeric evidence with prose judgment.

Repair routing: missing progression routes to game-design/progression-spec; numeric gaps route to balance-goal-spec.

## Completion Conditions

Return `COMPLETED` when curves validate against pacing goals. Return `FAILED_VALIDATION` when required progression is unreachable or unbounded.
