# Template Registry Skill

> Internal sub-skill for game-templates pipelines. Status: bundled, inactive, not wired.

## Overview

Creates the canonical registry of template kinds, schema IDs, owners,
consumers, source domains, lifecycle states, and output paths.

## Input Contract

Required: game design doc or content taxonomy.

Optional: program handoff, game data manifest, balance specs, art manifest, UI
registry, audio manifest, level specs, runtime/frontend profile, and existing
template files.

## Output Contract

Writes:

- `.allforai/game-templates/template-registry.json`
- `.allforai/game-templates/template-registry-report.json`

Registry entries must include `template_kind`, `schema_id`, `owner_domain`,
`source_domains`, `required_ref_domains`, `runtime_consumers`, `instance_path`,
`schema_path`, `lifecycle_state`, and `repair_target`.

Allowed lifecycle states: `planned`, `schema_defined`, `instances_generated`,
`validated`, `runtime_load_validated`, `blocked`.

## Invocation Contract

```json
{
  "skill": "game-templates/template-registry",
  "mode": "generate_validate",
  "input_paths": {
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "content_taxonomy": ".allforai/game-design/content/content-taxonomy-spec.json",
    "program_handoff": ".allforai/game-design/design/program-development-node-handoff.json"
  },
  "output_root": ".allforai/game-templates"
}
```

Supported modes: `generate_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every selected template kind has a source domain, schema owner,
runtime consumer, output path, and repair target. Do not create template kinds
that have no source requirement or consumer.

Repair routing: missing content source routes to `game-content` or
`game-design`; missing consumer routes to `game-frontend` or `game-runtime`.

## Completion Conditions

Return `COMPLETED` when template kinds and consumers are registered. Return
`FAILED_VALIDATION` when template kinds are orphaned or lack ownership.
