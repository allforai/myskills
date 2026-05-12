---
name: game-level-10-design-level-flow-design
description: Internal bundled meta-skill module for game-level/10-design/level-flow-design; use within generated bootstrap node-specs when this exact contract is selected.
---

# Level Flow Design Skill

> Internal sub-skill for game-level pipelines. Status: bundled, inactive, not wired.

## Overview

Defines level order, pacing, objectives, failure/retry flow, unlocks, and
difficulty beats before layout generation.

## Input Contract

Required: level registry or level list plus core loop. Optional: progression
spec, combat/economy specs, narrative beats.

## Output Contract

Writes `.allforai/game-design/levels/level-flow-design.json` and
`.allforai/game-design/levels/level-flow-report.json`.

Flow entries must include `level_id`, `objective`, `entry_condition`,
`success_condition`, `failure_condition`, `retry_rule`, `difficulty_beat`,
`reward_refs`, `narrative_refs`, and `next_levels`.

Each flow entry must also include `progression_refs`, `economy_refs`,
`combat_refs`, `consumer_refs`, and `state`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_level_registry`, `blocked_by_systems`, `blocked_by_narrative`.

Downstream consumers: `game-level/level-layout-spec`,
`game-level/level-playability-qa`, `game-systems/progression-spec`,
`game-systems/economy-spec`, `game-narrative/quest-text-spec`,
`game-audio/music-cue-spec`, `game-ui/ui-mockup-generation`, and runtime level
select/import.

## Invocation Contract

```json
{"skill":"game-level/level-flow-design","mode":"design_validate","input_paths":{"level_registry":".allforai/game-design/levels/level-registry.json","game_design_doc":".allforai/game-design/game-design-doc.json"},"output_root":".allforai/game-design/levels"}
```

Supported modes: `design_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every level has objective, entry, exit, failure/retry, pacing beat,
difficulty intent, unlock rules, and no unreachable progression node.

If progression or economy specs disagree with reward/unlock references, mark
root cause as `systems_spec` and do not change level flow until upstream systems
are repaired.

Repair routing: missing or duplicate `level_id` repairs `level-registry`; dead
level order or invalid retry logic repairs here; missing rewards or gates route
to systems specs; missing quest/narrative beats route to narrative specs.

## Completion Conditions

Return `COMPLETED` when flow validates. Return `FAILED_VALIDATION` for dead-end
progression that cannot be repaired.
