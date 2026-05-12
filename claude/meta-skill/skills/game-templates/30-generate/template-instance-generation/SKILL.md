---
name: game-templates-30-generate-template-instance-generation
description: Internal bundled meta-skill module for game-templates/30-generate/template-instance-generation; use within generated bootstrap node-specs when this exact contract is selected.
---

# Template Instance Generation Skill

> Internal sub-skill for game-templates pipelines. Status: bundled, inactive, not wired.

## Overview

Generates concrete template instances from approved schemas, inheritance rules,
reference bindings, and upstream content/system requirements.

## Input Contract

Required: template registry, template schemas, inheritance rules, reference
binding spec, and source content/system artifacts.

Optional: existing instances, balance tables, art/audio/UI manifests, level
plans, localization keys, and runtime loader constraints.

## Output Contract

Writes:

- `.allforai/game-templates/instances/<template_kind>.json`
- `.allforai/game-templates/instances/template-instance-generation-report.json`

Each instance must follow the shared envelope and include `template_id`,
`template_kind`, `schema_id`, `source_refs`, `fields`, `balance_refs`,
`art_refs`, `audio_refs`, `ui_refs`, `level_refs`, `runtime_consumers`,
`validation`, and `state`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_schema`, `blocked_by_missing_refs`, `blocked_by_source_contract`.

## Invocation Contract

```json
{
  "skill": "game-templates/template-instance-generation",
  "mode": "generate_validate",
  "input_paths": {
    "registry": ".allforai/game-templates/template-registry.json",
    "schemas": ".allforai/game-templates/schemas",
    "reference_map": ".allforai/game-templates/template-reference-map.json"
  },
  "output_root": ".allforai/game-templates/instances"
}
```

Supported modes: `generate_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Validate generated instances against schemas and reference bindings. Do not
invent missing design, art, audio, UI, or balance refs. When a field cannot be
filled from source contracts, mark the instance blocked or set an explicit
schema-approved default.

Repair routing: schema failures route to template-schema-spec; missing refs
route to template-reference-binding-spec; missing values route to the owning
source domain.

## Completion Conditions

Return `COMPLETED` when instances validate and are traceable. Return
`FAILED_VALIDATION` when instances contain invented values, unresolved refs, or
schema violations.
