---
name: game-balance-00-env-balance-registry
description: Internal bundled meta-skill module for game-balance/00-env/balance-registry; use within generated bootstrap node-specs when this exact contract is selected.
---

# Balance Registry Skill

> Internal sub-skill for game-balance pipelines. Status: bundled, inactive, not wired.

## Overview

Registers numeric tables, curves, formulas, balance entities, owners, states, and downstream consumers.

## Input Contract

Required: game design registry or selected system specs.

Optional: player experience, game pillars, content taxonomy, target platform, runtime constraints, existing tables, and tuning notes.

## Output Contract

Writes:

- `.allforai/game-design/balance/balance-registry.json`
- `.allforai/game-design/balance/balance-registry-report.json`

Outputs must include `schema_version`, stable IDs, `source_refs`, `owner_skill_refs`, `consumer_refs`, `state`, validation notes, and repair targets.

Allowed states/statuses: `draft, validated, needs_revision, blocked_by_missing_design`.

## Invocation Contract

```json
{
  "skill": "game-balance/balance-registry",
  "mode": "spec_validate",
  "input_paths": {},
  "output_root": ".allforai/game-design/balance"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check duplicate numeric IDs, missing owners, unresolved table refs, invalid lifecycle states, and orphan formulas. Do not substitute missing numeric evidence with prose judgment.

Repair routing: missing game design routes to game-design registry; missing system owner routes to owning spec; table gaps route to balance-table-generation.

## Completion Conditions

Return `COMPLETED` when stable numeric IDs and owners exist. Return `FAILED_VALIDATION` when no game design or numeric scope exists.
