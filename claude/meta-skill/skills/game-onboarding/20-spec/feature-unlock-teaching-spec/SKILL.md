---
name: game-onboarding-20-spec-feature-unlock-teaching-spec
description: Internal bundled meta-skill module for game-onboarding/20-spec/feature-unlock-teaching-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Feature Unlock Teaching Spec Skill

> Internal sub-skill for game-onboarding pipelines. Status: bundled, inactive, not wired.

## Overview

Defines when and how new features unlock, how each is taught, reinforced, and
validated without overloading the player.

## Input Contract

Required: progression spec, first-session experience spec, and tutorial step spec.

Optional: content roadmap, UI flow, economy spec, and level design spec.

## Output Contract

Writes `.allforai/game-design/onboarding/feature-unlock-teaching-spec.json`
and a report. Unlocks include `feature_id`, `unlock_trigger`,
`teaching_context`, `reinforcement_steps`, `practice_window`,
`failure_recovery`, `ui_requirements`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_progression`.

## Invocation Contract

```json
{"skill":"game-onboarding/feature-unlock-teaching-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/onboarding"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check unlock order, spacing, reinforcement, and whether each unlocked feature
gets a meaningful use soon after teaching.

Repair routing: unlock gaps route to progression spec; missing use context
routes to level/content specs; UI gaps route to game-ui.

## Completion Conditions

Return `COMPLETED` when feature teaching is sequenced and reinforced. Return
`FAILED_VALIDATION` when features unlock without teaching or use.
