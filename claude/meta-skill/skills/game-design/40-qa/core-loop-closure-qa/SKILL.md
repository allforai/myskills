# Core Loop Closure QA Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Validates whether game design loops are closed: goal, action, feedback, reward,
progression, failure recovery, and next motivation.

## Input Contract

Required: core game loop spec, mechanics spec, progression spec, and economy
spec when resources exist.

Optional: level design spec, player experience contract, data tables, and
playtest notes.

## Output Contract

Writes `.allforai/game-design/design/core-loop-closure-qa-report.json`.

Issues must include `issue_id`, `loop_id`, `severity`, `qa_axis`, `expected`,
`actual`, `root_cause`, `repair_target`, `blocks_runtime`, and `consumer_refs`.

Allowed root causes: `missing_goal`, `missing_action`, `missing_feedback`,
`missing_reward`, `dead_progression`, `failure_dead_end`, `economy_deadlock`,
`content_gap`, `unknown`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_spec`, `failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-design/core-loop-closure-qa",
  "mode": "validate",
  "input_paths": {
    "core_loop": ".allforai/game-design/design/core-game-loop-spec.json",
    "mechanics": ".allforai/game-design/systems/mechanics-spec.json",
    "progression": ".allforai/game-design/systems/progression-spec.json"
  },
  "output_root": ".allforai/game-design/product"
}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Check every primary loop for a complete chain and reject circular loops that
consume time/resources without meaningful progress. Missing executable evidence
must be reported, not substituted.

Repair routing: loop defects route to `core-game-loop-spec`; action defects to
`mechanics-spec`; reward/progression defects to `progression-spec` or
`economy-spec`.

## Completion Conditions

Return `COMPLETED` when all required loops close. Return `FAILED_VALIDATION`
when any primary loop is dead, circular, or missing a required step.
