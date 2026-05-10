# Content Pack Plan Generation Skill

> Internal sub-skill for game-content pipelines. Status: bundled, inactive, not wired.

## Overview

Generates concrete content pack plans from roadmap, quest, activity, level,
narrative, economy, and art/UI/audio requirements.

## Input Contract

Required: content roadmap spec and content registry.

Optional: quest chains, activities, level plans, enemy/item lists, and production
capacity constraints.

## Output Contract

Writes `.allforai/game-design/content/content-pack-plan-manifest.json` and a
report. Packs include `pack_id`, `content_refs`, `scope`, `required_assets`,
`required_tables`, `required_levels`, `required_text`, `risk_level`, `state`,
and `consumer_refs`.

Allowed states: `draft`, `generated`, `validated`, `needs_revision`,
`blocked_by_roadmap`.

## Invocation Contract

```json
{"skill":"game-content/content-pack-plan-generation","mode":"generate_validate","input_paths":{},"output_root":".allforai/game-design/content"}
```

Supported modes: `generate_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check each pack has content, owners, downstream requirements, scope risk, and no
unresolved hard dependency.

Repair routing: roadmap gaps route to content-roadmap-spec; quest/activity gaps
route to owning specs; asset gaps route to game-design content taxonomy.

## Completion Conditions

Return `COMPLETED` when pack plans are complete and owned. Return
`FAILED_VALIDATION` when packs lack required content or ownership.
