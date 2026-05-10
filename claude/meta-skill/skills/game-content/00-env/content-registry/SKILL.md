# Content Registry Skill

> Internal sub-skill for game-content pipelines. Status: bundled, inactive, not wired.

## Overview

Defines canonical content IDs, packs, cadence, owners, dependencies, states, and
downstream routes for quests, activities, levels, items, enemies, events, and
seasonal content.

## Input Contract

Required: game design registry or content taxonomy.

Optional: roadmap notes, narrative specs, level specs, economy specs, art/UI/audio
registries, and liveops constraints.

## Output Contract

Writes `.allforai/game-design/content/content-registry.json` and a report.
Entries include `content_id`, `content_kind`, `pack_id`, `owner_skill_refs`,
`dependency_refs`, `release_order`, `state`, and `consumer_refs`.

Allowed states: `planned`, `specified`, `generated`, `validated`,
`needs_revision`, `blocked`, `not_applicable`.

## Invocation Contract

```json
{"skill":"game-content/content-registry","mode":"init_or_validate","input_paths":{},"output_root":".allforai/game-design/content"}
```

Supported modes: `init_or_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check duplicate IDs, orphan content, missing owners, invalid dependencies, and
content that lacks a gameplay or narrative purpose.

Repair routing: missing taxonomy routes to game-design/content-taxonomy-spec;
missing quest/activity detail routes to the owning content spec.

## Completion Conditions

Return `COMPLETED` when content IDs and owners are stable. Return
`UPSTREAM_DEFECT` when no content source exists.
