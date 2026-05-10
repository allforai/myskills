# FTUE Friction QA Skill

> Internal sub-skill for game-onboarding pipelines. Status: bundled, inactive, not wired.

## Overview

Validates first-time user experience friction: cognitive load, controls, UI,
pacing, failure recovery, skip safety, and drop-off risk.

## Input Contract

Required: first-session experience spec, tutorial step spec, and feature unlock
teaching spec.

Optional: UI mockups, level plans, playtest traces, analytics targets, and
runtime evidence.

## Output Contract

Writes `.allforai/game-design/onboarding/ftue-friction-qa-report.json`.
Issues include `issue_id`, `step_id`, `severity`, `friction_axis`, `expected`,
`actual`, `root_cause`, `repair_target`, `blocks_release`, and `consumer_refs`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_evidence`, `failed_validation`.

## Invocation Contract

```json
{"skill":"game-onboarding/ftue-friction-qa","mode":"validate","input_paths":{},"output_root":".allforai/game-design/onboarding"}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Check tutorial step count, time budget, unexplained controls, UI overload,
failure dead ends, and unsupported skip paths. If a playable build or trace is
required but unavailable, report missing evidence.

Repair routing: pacing defects route to first-session spec; step defects route
to tutorial-step-spec; UI defects route to game-ui.

## Completion Conditions

Return `COMPLETED` when FTUE has no blocker friction. Return
`FAILED_VALIDATION` when a first-time player can get stuck or overloaded.
