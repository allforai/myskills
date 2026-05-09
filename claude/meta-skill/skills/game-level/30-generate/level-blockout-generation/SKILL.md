# Level Blockout Generation Skill

> Internal sub-skill for game-level pipelines. Status: bundled, inactive, not wired.

## Overview

Generates level blockouts, tile maps, room graphs, route maps, collision maps,
and preview artifacts from `level-layout-spec.json`.

## Input Contract

Required: level layout spec. Optional: tileset manifest, prop manifest, runtime
target, preview renderer.

## Output Contract

Writes `.allforai/game-design/levels/blockouts/level-blockout-manifest.json`,
`.allforai/game-design/levels/blockouts/level-blockout-report.json`, and map or
preview files when generated.

Manifest entries must include `level_id`, `layout_spec_ref`, `map_path`,
`collision_path`, `preview_path`, `tileset_refs`, `prop_refs`, `state`,
`playability_status`, and `validation`.

Allowed states: `spec_ready`, `generated`, `preview_ready`, `approved`,
`needs_revision`, `automation_limited`.

Downstream consumers: `game-level/level-playability-qa`, runtime map import,
playtest QA, camera validation, art preview QA, and performance validation.

## Invocation Contract

```json
{"skill":"game-level/level-blockout-generation","mode":"generate_validate","input_paths":{"level_layout_spec":".allforai/game-design/levels/level-layout-spec.json","tileset_manifest":".allforai/game-design/art/tilesets/tileset-manifest.json"},"output_root":".allforai/game-design/levels"}
```

Supported modes: `spec_only`, `generate_validate`, `validate_existing`.

## Automatic Validation

Check map dimensions, tile IDs, collision metadata, spawn/goal reachability,
objective placement, preview generation, and downstream playability feedback.

If playability QA fails because the layout spec is impossible, repair
`level-layout-spec`; if it fails because generated blockout metadata is wrong,
repair only the blockout manifest/map.

Root causes for failed outputs must be classified as `layout_spec`,
`blockout_generation`, `tileset_art`, `prop_art`, `collision_metadata`,
`preview_render`, or `runtime_import`. Generated maps can reach `approved` only
after `level-playability-qa` validates reachability and blocker issues are
closed.

## Completion Conditions

Return `COMPLETED` when blockouts and report validate. Return
`COMPLETED_WITH_LIMITS` for preview-less metadata-only blockouts.
