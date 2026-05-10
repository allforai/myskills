# Activity Design Spec Skill

> Internal sub-skill for game-content pipelines. Status: bundled, inactive, not wired.

## Overview

Defines repeatable or optional activities: objective, cadence, entry cost,
reward, failure rules, fatigue limits, and content requirements.

## Input Contract

Required: core loop context and content registry.

Optional: liveops task spec, economy spec, progression spec, level design, and
UI flow.

## Output Contract

Writes `.allforai/game-design/content/activity-design-spec.json` and a report.
Activities include `activity_id`, `activity_type`, `entry_rule`, `objective`,
`duration`, `reward_refs`, `repeat_rule`, `fatigue_limit`, `ui_requirements`,
`state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_loop`.

## Invocation Contract

```json
{"skill":"game-content/activity-design-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/content"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that activities serve a loop, have clear entry/exit, rewards, limits, and
do not create mandatory grind unless explicitly accepted.

Repair routing: loop gaps route to core-loop spec; reward gaps route to economy;
fatigue issues route to content-pacing-qa.

## Completion Conditions

Return `COMPLETED` when activities are loop-aligned and bounded. Return
`FAILED_VALIDATION` when activities are repetitive, unrewarded, or unbounded.
