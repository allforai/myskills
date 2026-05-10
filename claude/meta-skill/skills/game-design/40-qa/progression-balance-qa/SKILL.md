# Progression Balance QA Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Validates progression pacing, unlock usefulness, difficulty ramp, content gates,
grind risk, and dead-end risks.

## Input Contract

Required: progression spec, core loop spec, and content taxonomy.

Optional: economy spec, level design spec, item/skill set, enemy roster, data
tables, and target session model.

## Output Contract

Writes `.allforai/game-design/systems/progression-balance-qa-report.json`.

Issues must include `issue_id`, `progression_id`, `severity`, `qa_axis`,
`expected`, `actual`, `root_cause`, `repair_target`, `blocks_runtime`, and
`consumer_refs`.

Allowed root causes: `unlock_dead_end`, `pacing_spike`, `missing_content`,
`reward_redundant`, `grind_risk`, `difficulty_gap`, `unknown`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_spec`, `failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-design/progression-balance-qa",
  "mode": "validate",
  "input_paths": {
    "progression": ".allforai/game-design/systems/progression-spec.json",
    "content_taxonomy": ".allforai/game-design/content/content-taxonomy-spec.json"
  },
  "output_root": ".allforai/game-design/systems"
}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Check that every unlock is reachable, useful, and paced for the session model.
Numeric uncertainty may pass only as `passed_with_warnings` with explicit
tuning fields; it cannot be marked final.

Repair routing: pacing defects route to `progression-spec`; missing content to
`content-taxonomy-spec`; economy costs to `economy-spec`.

## Completion Conditions

Return `COMPLETED` when progression has no blocker issues. Return
`FAILED_VALIDATION` when required progression cannot be reached or used.
