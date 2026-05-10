# Level Registry Skill

> Internal sub-skill for game-level pipelines. Status: bundled, inactive, not wired.

## Overview

Defines canonical level, map, room, encounter, and blockout IDs plus paths,
states, dependencies, and validation.

## Input Contract

Required: game design level/progression context or caller level list. Optional:
tileset spec, asset registry, systems progression spec.

## Output Contract

Writes `.allforai/game-design/levels/level-registry.json` and
`.allforai/game-design/levels/level-registry-report.json`.

Registry entries must include `level_id`, `file_prefix`, `mode`, `order`,
`state`, `paths`, `dependencies`, `consumers`, and `validation`.

Allowed states: `planned`, `flow_ready`, `layout_ready`, `blockout_ready`,
`qa_ready`, `approved`, `needs_revision`.

## Invocation Contract

```json
{"skill":"game-level/level-registry","mode":"build_or_update","input_paths":{"game_design_doc":".allforai/game-design/game-design-doc.json","tileset_spec":".allforai/game-design/art/tilesets/tileset-spec.json"},"output_root":".allforai/game-design/levels"}
```

Supported modes: `build_or_update`, `validate_existing`, `resolve_ids`.

## Automatic Validation

Check unique IDs, stable prefixes, paths under level root, valid states,
progression ordering, and asset/tileset dependency references.

Downstream blockout and playability QA must reference levels by `level_id`, not
by raw filenames or display names.

Repair routing: duplicate IDs, path collisions, or state errors repair here;
missing gameplay purpose returns to core loop or progression design; missing
display art references route to the relevant art producer after the `level_id`
is stable.

## Completion Conditions

Return `COMPLETED` when registry and report validate. Return
`FAILED_VALIDATION` when no level context can be resolved or required levels
lack stable IDs.
