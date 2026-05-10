# Game Data Table Generation Skill

> Internal sub-skill for game-product pipelines. Status: bundled, inactive, not wired.

## Overview

Generates program-readable data tables from product specs. Tables may cover
resources, items, skills, enemies, levels, quests, progression, economy, and
runtime config.

## Input Contract

Required: content taxonomy and at least one validated system spec.

Optional: economy spec, progression spec, combat spec, item/skill generation,
enemy roster generation, runtime schema preferences, and target engine.

## Output Contract

Writes:

- `.allforai/game-design/data/game-data-table-manifest.json`
- `.allforai/game-design/data/game-data-table-report.json`
- table files under `.allforai/game-design/data/tables/`

Manifest entries must include `table_id`, `table_kind`, `source_spec_refs`,
`format`, `path`, `required_columns`, `row_count`, `runtime_consumer_refs`,
`validation_status`, `state`, and `consumer_refs`.

Allowed formats: `json`, `jsonl`, `csv`, `yaml`.
Allowed states: `draft`, `generated`, `validated`, `needs_revision`,
`blocked_by_missing_spec`, `blocked_by_schema`.

## Invocation Contract

```json
{
  "skill": "game-product/game-data-table-generation",
  "mode": "generate_validate",
  "input_paths": {
    "content_taxonomy": ".allforai/game-design/content/content-taxonomy-spec.json",
    "economy": ".allforai/game-design/systems/product-economy-spec.json",
    "progression": ".allforai/game-design/systems/progression-spec.json"
  },
  "output_root": ".allforai/game-design/data"
}
```

Supported modes: `generate_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that required tables exist, required columns are present, IDs resolve to
the registry/taxonomy, numeric fields are typed, and runtime consumers are
declared. Do not fabricate missing schema evidence.

Repair routing: missing source specs route to owning spec; missing rows route
to enemy/item/level/quest generators; runtime import gaps route to
`implementation-feasibility-qa`.

## Completion Conditions

Return `COMPLETED` when tables validate and are ready for runtime import.
Return `FAILED_VALIDATION` when required tables or schema fields are missing.
