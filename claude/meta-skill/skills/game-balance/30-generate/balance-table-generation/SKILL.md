---
name: game-balance-30-generate-balance-table-generation
description: Internal bundled meta-skill module for game-balance/30-generate/balance-table-generation; use within generated bootstrap node-specs when this exact contract is selected.
---

# Balance Table Generation Skill

> Internal sub-skill for game-balance pipelines. Status: bundled, inactive, not wired.

## Overview

Generates JSON/CSV balance tables from validated numeric specs.

## Input Contract

Required: validated numeric specs and balance registry.

Optional: player experience, game pillars, content taxonomy, target platform, runtime constraints, existing tables, and tuning notes.

## Output Contract

Writes:

- `.allforai/game-design/balance/balance-table-manifest.json`
- `.allforai/game-design/balance/balance-table-manifest-report.json`

Outputs must include `schema_version`, stable IDs, `source_refs`, `owner_skill_refs`, `consumer_refs`, `state`, validation notes, and repair targets.

Allowed states/statuses: `draft, generated, validated, needs_revision, blocked_by_schema`.

## Invocation Contract

```json
{
  "skill": "game-balance/balance-table-generation",
  "mode": "spec_validate",
  "input_paths": {},
  "output_root": ".allforai/game-design/balance"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check required tables exist, columns match specs, IDs resolve, numeric types parse, and runtime consumers are declared. Do not substitute missing numeric evidence with prose judgment.

Repair routing: schema gaps route to owning spec; missing rows route to content/design list skills.

## Completion Conditions

Return `COMPLETED` when tables validate and map to consumers. Return `FAILED_VALIDATION` when required table or schema field is missing.
