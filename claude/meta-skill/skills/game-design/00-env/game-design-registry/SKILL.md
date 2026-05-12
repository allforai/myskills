---
name: game-design-00-env-game-design-registry
description: Internal bundled meta-skill module for game-design/00-env/game-design-registry; use within generated bootstrap node-specs when this exact contract is selected.
---

# Game Design Registry Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Defines canonical IDs, names, owners, lifecycle states, and cross-skill routes
for game-design entities: features, systems, loops, resources, levels,
enemies, items, skills, quests, events, and content packs.

## Input Contract

Required: product concept or game brief.

Optional: scenario template, target platform, existing game design docs,
concept contract, art inventory, level list, economy notes, and runtime stack.

## Output Contract

Writes:

- `.allforai/game-design/design/game-design-registry.json`
- `.allforai/game-design/design/game-design-registry-report.json`

Registry entries must include `id`, `kind`, `display_name`, `owner_layer`,
`source_ref`, `consumer_refs`, `state`, `priority`, `risk_level`, and
`handoff_refs`.

Allowed kinds: `feature`, `system`, `loop`, `resource`, `level`, `enemy`,
`item`, `skill`, `quest`, `event`, `content_pack`, `ui_surface`,
`art_requirement`, `audio_requirement`, `runtime_requirement`, `other`.

Allowed states: `planned`, `specified`, `generated`, `validated`,
`needs_revision`, `blocked`, `not_applicable`.

## Invocation Contract

```json
{
  "skill": "game-design/game-design-registry",
  "mode": "init_or_validate",
  "input_paths": {
    "product_concept": ".allforai/product-concept.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json"
  },
  "output_root": ".allforai/game-design/design"
}
```

Supported modes: `init_or_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check for duplicate IDs, missing owners, invalid state transitions, orphaned
requirements, and references to downstream assets without source product
entries. Do not silently rename IDs; report collisions.

Repair routing: missing product concept routes to product/concept capability;
missing content entities route to `content-taxonomy-spec`; invalid runtime
requirements route to `implementation-feasibility-qa`.

## Completion Conditions

Return `COMPLETED` when the registry is valid and every design entity has a
stable ID and owner. Return `FAILED_VALIDATION` when no product concept exists
or required design entities cannot be assigned stable IDs.
