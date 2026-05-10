# Template Schema Spec Skill

> Internal sub-skill for game-templates pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the common template envelope and per-kind schemas for fields, required
refs, defaults, localizable fields, runtime IDs, and validation rules.

## Input Contract

Required: template registry and upstream source contracts for selected template
kinds.

Optional: JSON schema conventions, existing template schemas, data table
manifest, balance specs, art/UI/audio refs, localization conventions, and
runtime loader constraints.

## Output Contract

Writes:

- `.allforai/game-templates/schemas/<template_kind>.schema.json`
- `.allforai/game-templates/schemas/template-schema-report.json`

Each schema must include `schema_id`, `template_kind`, `schema_version`,
`required_fields`, `optional_fields`, `default_values`, `field_types`,
`source_ref_requirements`, `balance_ref_requirements`,
`art_ref_requirements`, `audio_ref_requirements`, `ui_ref_requirements`,
`runtime_consumer_requirements`, `localization_fields`, `validation_rules`,
and `state`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_registry`, `blocked_by_source_contract`.

## Invocation Contract

```json
{
  "skill": "game-templates/template-schema-spec",
  "mode": "spec_validate",
  "input_paths": {
    "registry": ".allforai/game-templates/template-registry.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json"
  },
  "output_root": ".allforai/game-templates/schemas"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that each schema can validate the common envelope and its `fields`
object. Required refs must be explicit by template kind; optional refs must have
default or absence behavior. Schema must not encode final balance values unless
they come from balance/data sources.

Repair routing: missing meaning routes to game-design/content; missing numeric
source routes to game-balance/data generation; missing resource refs route to
template-reference-binding-spec.

## Completion Conditions

Return `COMPLETED` when schemas are strict enough to validate instances and
flexible enough to carry refs. Return `FAILED_VALIDATION` when fields or refs
are ambiguous, untyped, or ownerless.
