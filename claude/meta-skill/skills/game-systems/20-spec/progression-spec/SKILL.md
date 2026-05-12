---
name: game-systems-20-spec-progression-spec
description: Internal bundled meta-skill module for game-systems/20-spec/progression-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Progression Spec Skill

> Internal sub-skill for game-systems pipelines. Status: bundled, inactive, not wired.

## Overview

Defines XP, levels, unlocks, gates, difficulty pacing, reward cadence, content
sequence, and progression events.

## Input Contract

Required: core loop or progression context. Optional: level flow, economy spec,
combat spec, narrative quest specs.

## Output Contract

Writes `.allforai/game-design/systems/progression-spec.json` and
`.allforai/game-design/systems/progression-report.json`.

Progression schema:

```json
{
  "schema_version": "1.0",
  "progression_nodes": [
    {
      "node_id": "level_01",
      "kind": "level | ability | item | area | quest | rank",
      "unlock_conditions": [],
      "rewards": [],
      "difficulty_target": "intro | easy | normal | hard | boss",
      "depends_on": [],
      "unlocks": [],
      "consumer_refs": []
    }
  ]
}
```

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_economy`,
`blocked_by_level_flow`.

Downstream consumers: `game-systems/balance-sanity-qa`,
`game-level/level-flow-design`, `game-narrative/quest-text-spec`,
`game-ui/ui-mockup-generation`, `icon-generation`, and runtime progression
import.

## Invocation Contract

```json
{"skill":"game-systems/progression-spec","mode":"spec_validate","input_paths":{"core_loop":".allforai/game-design/systems/core-loop-design.json","level_flow":".allforai/game-design/levels/level-flow-design.json","economy_spec":".allforai/game-design/systems/economy-spec.json"},"output_root":".allforai/game-design/systems"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check unlock graph reachability, reward cadence, gates, difficulty ramp, economy
dependencies, level dependencies, and dead-end progression.

Every unlock must be reachable from an entry node. Any gate that depends on
currency, combat power, or quest state must reference the owning spec.

Repair routing: dead unlock graphs repair here; missing level sequence repairs
`level-flow-design`; missing currency or reward semantics repair
`economy-spec`; missing quest wording repairs `quest-text-spec`; missing reward
icons route to art generation skills.

## Completion Conditions

Return `COMPLETED` when progression spec validates. Return
`FAILED_VALIDATION` for unrecoverable progression dead ends.
