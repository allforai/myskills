# Event Operation Spec Skill

> Internal sub-skill for game-liveops pipelines. Status: bundled, inactive, not wired.

## Overview

Defines time-limited events, seasons, rotations, eligibility, rewards, content
needs, schedule, and operational risks.

## Input Contract

Required: content roadmap and retention loop spec.

Optional: economy, monetization, task spec, narrative/event theme, art/audio/UI
requirements, and regional calendar constraints.

## Output Contract

Writes `.allforai/game-design/liveops/event-operation-spec.json` and a report.
Events include `event_id`, `theme`, `schedule`, `eligibility`, `activities`,
`reward_refs`, `content_requirements`, `asset_requirements`, `risk_level`,
`state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_content`,
`blocked_by_schedule`.

## Invocation Contract

```json
{"skill":"game-liveops/event-operation-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/liveops"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check schedule conflicts, content readiness, reward balance, operational scope,
and whether events can be disabled or delayed cleanly.

Repair routing: content gaps route to content-pack-plan-generation; reward gaps
route to reward-pricing; scope gaps route to implementation feasibility.

## Completion Conditions

Return `COMPLETED` when events are schedulable and owned. Return
`FAILED_VALIDATION` when event scope, rewards, or schedule are not viable.
