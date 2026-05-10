# Faction System Spec Skill

> Internal sub-skill for game-genre-common pipelines. Status: bundled, inactive, not wired.

## Overview

Defines factions, relations, reputation, diplomacy, territory, conflict,
resource behavior, and narrative/system consequences.

## Input Contract

Required: content taxonomy or world bible with faction candidates.

Optional: economy, level map, AI behavior, relationship system, quest patterns,
and progression constraints.

## Output Contract

Writes `.allforai/game-design/genre-common/faction-system-spec.json` and a
report. Factions include `faction_id`, `role`, `relationship_matrix`,
`reputation_rules`, `territory_rules`, `conflict_rules`, `reward_penalty_rules`,
`quest_refs`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_world`.

## Invocation Contract

```json
{"skill":"game-genre-common/faction-system-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/genre-common"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check faction purpose, relation symmetry or asymmetry, reputation effects,
content use, and whether conflicts have gameplay consequences.

Repair routing: world gaps route to world-bible-spec; quest gaps to
quest-pattern/quest-chain; economy gaps to economy specs.

## Completion Conditions

Return `COMPLETED` when faction rules are meaningful and traceable. Return
`FAILED_VALIDATION` when factions have no consequence or impossible relations.
