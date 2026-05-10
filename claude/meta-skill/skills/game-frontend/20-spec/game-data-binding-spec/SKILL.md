# Game Data Binding Spec Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Maps game design data tables and system specs into frontend-readable runtime
data modules, loader keys, schema checks, default values, and smoke-test probes.

## Input Contract

Required: frontend runtime profile, game design doc, program development
handoff, and either game templates or at least one game data/source spec.

Optional: template registry, template schemas, template instances, template
reference map, template runtime-load QA report, design data table manifest,
economy/progression/combat/item/enemy tables, level plans, content taxonomy,
localization keys, existing data loader code, and build/test commands.

## Output Contract

Writes:

- `.allforai/game-frontend/bindings/game-data-binding-spec.json`
- `.allforai/game-frontend/bindings/game-data-binding-report.json`

Bindings must include `binding_id`, `source_artifact`, `schema_ref`,
`template_refs`, `frontend_module`, `runtime_key`, `data_kind`,
`required_fields`, `default_policy`, `validation_probe`, `consumer_refs`,
`state`, and `repair_target`.

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
    "template_registry": ".allforai/game-templates/template-registry.json",
    "template_instances": ".allforai/game-templates/instances",
    "template_runtime_load_report": ".allforai/game-templates/qa/template-runtime-load-qa-report.json",
    "data_manifest": ".allforai/game-design/data/game-data-table-manifest.json"
  },
  "output_root": ".allforai/game-frontend/bindings"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Prefer `game-templates` when available. Check that each frontend-required system
has a template instance or source data artifact, stable schema, loader/module
target, default policy, and runtime validation probe. Do not invent missing
templates or tables from prose. If required templates or data tables are absent,
return `blocked_by_missing_data`.

When templates are present, require `template-runtime-load-qa` evidence before
marking bindings `validated`. Static schema inspection is diagnostic only.

Repair routing: missing templates route to `game-templates`; missing data
routes to `game-design/design-data-table-generation`; schema gaps route to the
owning template or system spec; frontend loader gaps route to
`playable-client-assembly`.

## Completion Conditions

Return `COMPLETED` when all required gameplay data can be loaded and probed in
the frontend. Return `FAILED_VALIDATION` when data is missing, schema-incompatible,
or untestable.
