---
name: game-genre-common-20-spec-tech-tree-spec
description: Internal bundled meta-skill module for game-genre-common/20-spec/tech-tree-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Tech Tree Spec Skill

> Internal sub-skill for game-genre-common pipelines. Status: bundled, inactive, not wired.

## Overview

Defines research/tech trees: prerequisites, unlocks, eras, costs, pacing,
branches, mutually exclusive choices, and UI/data requirements.

## Input Contract

Required: progression spec and content taxonomy.

Optional: economy, building/crafting systems, faction system, strategy/sim
context, and balance goals.

## Output Contract

Writes `.allforai/game-design/genre-common/tech-tree-spec.json` and a report.
Tech entries include `tech_id`, `tier`, `prerequisite_refs`, `cost_refs`,
`unlock_refs`, `choice_group`, `pacing_target`, `ui_requirements`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_progression`.

## Invocation Contract

```json
{"skill":"game-genre-common/tech-tree-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/genre-common"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check acyclic prerequisites, reachable costs, useful unlocks, no dead branches,
and readable UI requirements.

Repair routing: progression gaps route to progression spec; economy gaps route
to reward-pricing; content gaps route to content registry.

## Completion Conditions

Return `COMPLETED` when tech tree is reachable and useful. Return
`FAILED_VALIDATION` when prerequisites cycle or unlocks are dead.
