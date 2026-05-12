---
name: game-balance-10-design-balance-goal-spec
description: Internal bundled meta-skill module for game-balance/10-design/balance-goal-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Balance Goal Spec Skill

> Internal sub-skill for game-balance pipelines. Status: bundled, inactive, not wired.

## Overview

Defines numeric design goals for pacing, difficulty, economy pressure, fairness, skill expression, and tuning tolerance.

## Input Contract

Required: player experience contract, core loop, and balance registry.

Optional: player experience, game pillars, content taxonomy, target platform, runtime constraints, existing tables, and tuning notes.

## Output Contract

Writes:

- `.allforai/game-design/balance/balance-goal-spec.json`
- `.allforai/game-design/balance/balance-goal-spec-report.json`

Outputs must include `schema_version`, stable IDs, `source_refs`, `owner_skill_refs`, `consumer_refs`, `state`, validation notes, and repair targets.

Allowed states/statuses: `draft, validated, needs_revision, blocked_by_missing_loop`.

## Invocation Contract

```json
{
  "skill": "game-balance/balance-goal-spec",
  "mode": "spec_validate",
  "input_paths": {},
  "output_root": ".allforai/game-design/balance"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every goal has measurable target range, player-facing rationale, affected systems, and QA method. Do not substitute missing numeric evidence with prose judgment.

Repair routing: vague experience goals route to game-design/player-experience-contract; missing loops route to core-loop-spec.

## Completion Conditions

Return `COMPLETED` when goals are measurable and routed. Return `FAILED_VALIDATION` when goals contradict player experience or cannot be measured.
