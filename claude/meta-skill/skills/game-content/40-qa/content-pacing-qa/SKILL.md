# Content Pacing QA Skill

> Internal sub-skill for game-content pipelines. Status: bundled, inactive, not wired.

## Overview

Validates content cadence, repetition, coverage, dependency order, novelty, and
fatigue risk.

## Input Contract

Required: content roadmap and content pack plan manifest.

Optional: quest chains, activity specs, progression curve, economy spec, and
playtest/analytics evidence.

## Output Contract

Writes `.allforai/game-design/content/content-pacing-qa-report.json`. Issues
include `issue_id`, `content_id`, `severity`, `pacing_axis`, `expected`,
`actual`, `root_cause`, `repair_target`, `blocks_release`, and `consumer_refs`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_manifest`, `failed_validation`.

## Invocation Contract

```json
{"skill":"game-content/content-pacing-qa","mode":"validate","input_paths":{},"output_root":".allforai/game-design/content"}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Check content spacing, repeated objective density, reward cadence, dependency
order, novelty, and missing content owners.

Repair routing: cadence defects route to content-roadmap-spec; repetition
defects route to activity-design-spec; quest issues route to quest-chain-spec.

## Completion Conditions

Return `COMPLETED` when content pacing has no blockers. Return
`FAILED_VALIDATION` when required content cadence cannot sustain the target loop.
