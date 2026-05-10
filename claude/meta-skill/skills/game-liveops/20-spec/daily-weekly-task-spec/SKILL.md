# Daily Weekly Task Spec Skill

> Internal sub-skill for game-liveops pipelines. Status: bundled, inactive, not wired.

## Overview

Defines daily/weekly task cadence, objective pools, reset rules, rewards,
fatigue limits, and UI requirements.

## Input Contract

Required: retention loop spec and activity design spec or content roadmap.

Optional: economy spec, progression spec, monetization spec, and analytics goals.

## Output Contract

Writes `.allforai/game-design/liveops/daily-weekly-task-spec.json` and a report.
Tasks include `task_id`, `cadence`, `objective`, `eligibility`, `reward_refs`,
`reset_rule`, `replacement_rule`, `fatigue_limit`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_content`.

## Invocation Contract

```json
{"skill":"game-liveops/daily-weekly-task-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/liveops"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check objective variety, reward fairness, reset clarity, completion time, and
whether tasks create unwanted grind.

Repair routing: content gaps route to activity-design-spec; reward gaps route to
economy/reward-pricing; UI gaps route to game-ui.

## Completion Conditions

Return `COMPLETED` when recurring tasks are fair and bounded. Return
`FAILED_VALIDATION` when tasks are impossible, repetitive, or coercive.
