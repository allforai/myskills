# Level Pacing QA Skill

> Internal sub-skill for game-level pipelines. Status: bundled, inactive, not wired.

## Overview

Validates level pacing across teaching, encounters, rewards, rest points,
difficulty spikes, and objective progress.

## Input Contract

Required: level flow design, level layout spec, teaching beats, encounter
placement, and reward placement when applicable.

Optional: blockout previews, playtest traces, progression curve, and combat
balance report.

## Output Contract

Writes `.allforai/game-design/levels/level-pacing-qa-report.json`. Issues
include `issue_id`, `level_id`, `severity`, `pacing_axis`, `expected`, `actual`,
`root_cause`, `repair_target`, `blocks_runtime`, and `consumer_refs`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_evidence`, `failed_validation`.

## Invocation Contract

```json
{"skill":"game-level/level-pacing-qa","mode":"validate","input_paths":{},"output_root":".allforai/game-design/levels"}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Check teaching density, encounter spacing, reward cadence, rest beats,
difficulty spikes, and objective clarity. If blockout/playtest evidence is
required but unavailable, report missing evidence.

Repair routing: teaching defects route to teaching-beat-spec; encounter defects
route to encounter-placement-spec; reward defects route to reward-placement-spec.

## Completion Conditions

Return `COMPLETED` when level pacing has no blocker issues. Return
`FAILED_VALIDATION` when a level has unplayable pacing or unverifiable evidence.
