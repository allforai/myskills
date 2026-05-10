# Run Structure Spec Skill

> Internal sub-skill for game-genre-common pipelines. Status: bundled, inactive, not wired.

## Overview

Defines run/session structures used by roguelike, dungeon, ladder, challenge,
survival, and repeatable mode games: start, branches, encounters, shops,
rewards, rest points, bosses, failure, and completion.

## Input Contract

Required: core loop spec and content/level context.

Optional: progression, economy, encounter placement, procedural content,
reward pricing, and player session goals.

## Output Contract

Writes `.allforai/game-design/genre-common/run-structure-spec.json` and a report.
Runs include `run_id`, `entry_rule`, `node_types`, `branch_rules`,
`encounter_rules`, `reward_rules`, `failure_rule`, `completion_rule`,
`duration_target`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_loop`.

## Invocation Contract

```json
{"skill":"game-genre-common/run-structure-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/genre-common"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that each run has start/end, choices, reward pacing, failure handling, and
session duration fit. Branches must not create impossible or empty paths.

Repair routing: loop gaps route to core-loop spec; reward gaps to reward-pricing;
branch/path gaps to procedural-content or level specs.

## Completion Conditions

Return `COMPLETED` when run structure is closed and paced. Return
`FAILED_VALIDATION` when runs can dead-end or lack meaningful choices.
