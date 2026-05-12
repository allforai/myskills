---
name: game-systems-20-spec-achievement-system-spec
description: Internal bundled meta-skill module for game-systems/20-spec/achievement-system-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Achievement System Spec Skill

> Internal sub-skill for game-systems pipelines. Status: bundled, inactive, not wired.

## Overview

Defines achievements, challenges, trophies, milestones, tracking conditions,
rewards, visibility, hidden rules, and UI/content ownership.

## Input Contract

Required: core loop or content taxonomy.

Optional: progression, economy, retention loop, level design, combat spec, UI
requirements, and platform achievement constraints.

## Output Contract

Writes `.allforai/game-design/systems/achievement-system-spec.json` and a
report. Achievements include `achievement_id`, `goal`, `tracking_rule`,
`completion_condition`, `reward_refs`, `visibility_rule`, `difficulty_tier`,
`ui_requirements`, `state`, and `consumer_refs`.

Allowed states: `not_applicable`, `draft`, `validated`, `needs_revision`,
`blocked_by_tracking`.

## Invocation Contract

```json
{"skill":"game-systems/achievement-system-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/systems"}
```

Supported modes: `spec_validate`, `not_applicable`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check achievements are trackable, meaningful, non-contradictory, and mapped to
content/progression/reward owners. Hidden achievements need spoiler-safe UI.

Repair routing: tracking gaps route to implementation feasibility; reward gaps
route to economy; content gaps route to content registry.

## Completion Conditions

Return `COMPLETED` when achievements are trackable or not applicable. Return
`FAILED_VALIDATION` when required tracking or rewards are undefined.
