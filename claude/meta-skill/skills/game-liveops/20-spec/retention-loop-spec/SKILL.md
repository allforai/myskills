# Retention Loop Spec Skill

> Internal sub-skill for game-liveops pipelines. Status: bundled, inactive, not wired.

## Overview

Defines daily, weekly, monthly, comeback, streak, social, and collection hooks
that motivate return sessions.

## Input Contract

Required: core loop, progression spec, and player experience contract.

Optional: content roadmap, economy spec, monetization spec, notification policy,
and analytics goals.

## Output Contract

Writes `.allforai/game-design/liveops/retention-loop-spec.json` and a report.
Loops include `retention_loop_id`, `trigger`, `return_motivation`,
`required_action`, `reward`, `cooldown_or_reset`, `fatigue_limit`, `ui_refs`,
`state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_loop`.

## Invocation Contract

```json
{"skill":"game-liveops/retention-loop-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/liveops"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check return motivation, reward usefulness, reset clarity, fatigue limits, and
that retention hooks do not punish healthy non-play.

Repair routing: reward gaps route to reward-pricing; task gaps route to
daily-weekly-task-spec; fairness concerns route to monetization-fairness-qa.

## Completion Conditions

Return `COMPLETED` when return loops are bounded and motivating. Return
`FAILED_VALIDATION` when loops are coercive, unrewarded, or unbounded.
