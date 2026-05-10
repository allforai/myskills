# Template Reference Binding Spec Skill

> Internal sub-skill for game-templates pipelines. Status: bundled, inactive, not wired.

## Overview

Defines how templates reference design, balance, art, UI, audio, level, and
runtime/frontend contracts without embedding or duplicating those domains.

## Input Contract

Required: template registry, template schemas, game design doc, and at least one
upstream source domain for selected template kinds.

Optional: balance/data manifests, engine-ready art manifest, UI registry, audio
manifest, level specs, frontend runtime profile, runtime system specs, and
existing reference maps.

## Output Contract

Writes:

- `.allforai/game-templates/template-reference-map.json`
- `.allforai/game-templates/template-reference-binding-report.json`

Reference bindings must include `template_id_or_kind`, `source_refs`,
`balance_refs`, `art_refs`, `audio_refs`, `ui_refs`, `level_refs`,
`runtime_consumers`, `required_refs`, `optional_refs`, `missing_refs`,
`validation_probe`, `state`, and `repair_target`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_missing_source`, `blocked_by_missing_resource`,
`blocked_by_missing_consumer`.

## Invocation Contract

```json
{
  "skill": "game-templates/template-reference-binding-spec",
  "mode": "spec_validate",
  "input_paths": {
    "registry": ".allforai/game-templates/template-registry.json",
    "schemas": ".allforai/game-templates/schemas",
    "engine_ready_art": ".allforai/game-runtime/art/engine-ready-art-manifest.json",
    "ui_registry": ".allforai/game-design/ui/ui-registry.json"
  },
  "output_root": ".allforai/game-templates"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every required ref resolves to an upstream artifact and every runtime
consumer exists. Optional refs need explicit absence behavior. Templates may
reference art/audio/UI/runtime IDs, but must not hardcode raw paths when a
manifest runtime ID exists.

Repair routing: missing design refs route to game-design/content; missing art
refs route to game-art engine-ready manifest; missing UI/audio refs route to
their packs; missing consumers route to game-frontend/game-runtime.

## Completion Conditions

Return `COMPLETED` when refs are resolvable and consumer-aware. Return
`FAILED_VALIDATION` when required refs are missing or unowned.
