# Social System Spec Skill

> Internal sub-skill for game-systems pipelines. Status: bundled, inactive, not wired.

## Overview

Defines non-technical social features: friends, parties, guilds, chat needs,
gifts, leaderboards, co-op hooks, social rewards, moderation needs, and UI
requirements.

## Input Contract

Required: player experience contract or social feature brief.

Optional: progression, economy, liveops, content roadmap, UI flow, and platform
policy constraints.

## Output Contract

Writes `.allforai/game-design/systems/social-system-spec.json` and a report.
Features include `social_feature_id`, `purpose`, `participant_rules`,
`reward_refs`, `abuse_risks`, `moderation_requirements`, `ui_requirements`,
`privacy_requirements`, `state`, and `consumer_refs`.

Allowed states: `not_applicable`, `draft`, `validated`, `needs_revision`,
`blocked_by_policy`.

## Invocation Contract

```json
{"skill":"game-systems/social-system-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/systems"}
```

Supported modes: `spec_validate`, `not_applicable`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check social feature purpose, abuse risks, privacy/moderation needs, reward
fairness, and UI ownership. This is product design, not network architecture.

Repair routing: reward gaps route to economy/reward-pricing; UI gaps route to
game-ui; policy risks route to implementation feasibility.

## Completion Conditions

Return `COMPLETED` when social features are purposeful or not applicable. Return
`FAILED_VALIDATION` when abuse or policy risks are unowned.
