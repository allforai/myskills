# Game Data Binding Spec Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Maps game design data tables and system specs into frontend-readable runtime
data modules, loader keys, schema checks, default values, and smoke-test probes.

## Input Contract

Required: frontend runtime profile, game design doc, program development
handoff, and at least one game data/source spec.

Optional: design data table manifest, economy/progression/combat/item/enemy
tables, level plans, content taxonomy, localization keys, existing data loader
code, and build/test commands.

## Output Contract

Writes:

- `.allforai/game-frontend/bindings/game-data-binding-spec.json`
- `.allforai/game-frontend/bindings/game-data-binding-report.json`

Bindings must include `binding_id`, `source_artifact`, `schema_ref`,
`frontend_module`, `runtime_key`, `data_kind`, `required_fields`,
`default_policy`, `validation_probe`, `consumer_refs`, `state`, and
`repair_target`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_missing_data`, `blocked_by_schema_mismatch`,
`blocked_by_runtime_profile`.

## Invocation Contract

```json
{
  "skill": "game-frontend/game-data-binding-spec",
  "mode": "spec_validate",
  "input_paths": {
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "program_handoff": ".allforai/game-design/design/program-development-node-handoff.json",
    "data_manifest": ".allforai/game-design/data/game-data-table-manifest.json"
  },
  "output_root": ".allforai/game-frontend/bindings"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that each frontend-required system has a source data artifact, stable
schema, loader/module target, default policy, and runtime validation probe.
Do not invent missing tables from prose. If a required data table is absent,
return `blocked_by_missing_data`.

Repair routing: missing data routes to `game-design/design-data-table-generation`;
schema gaps route to the owning system spec; frontend loader gaps route to
`playable-client-assembly`.

## Completion Conditions

Return `COMPLETED` when all required gameplay data can be loaded and probed in
the frontend. Return `FAILED_VALIDATION` when data is missing, schema-incompatible,
or untestable.
