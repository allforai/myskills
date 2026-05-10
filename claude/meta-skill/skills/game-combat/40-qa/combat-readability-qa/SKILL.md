# Combat Readability QA Skill

> Internal sub-skill for game-combat pipelines. Status: bundled, inactive, not wired.

## Overview

Validates whether combat can be read by players: telegraphs, hit feedback,
states, status effects, VFX/audio/UI clarity, failure cause, and fairness.

## Input Contract

Required: skill design, enemy behavior, and combat spec.

Optional: status effect spec, boss encounter spec, animation/VFX/audio manifests,
UI mockups, playtest traces, and balance reports.

## Output Contract

Writes `.allforai/game-design/combat/combat-readability-qa-report.json`.
Issues include `issue_id`, `combat_ref`, `severity`, `readability_axis`,
`expected`, `actual`, `evidence_paths`, `root_cause`, `repair_target`,
`blocks_runtime`, and `consumer_refs`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_evidence`, `failed_validation`.

## Invocation Contract

```json
{"skill":"game-combat/combat-readability-qa","mode":"validate","input_paths":{},"output_root":".allforai/game-design/combat"}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Check telegraph duration, action feedback, status visibility, enemy state
clarity, VFX/audio overload, and whether failure cause is understandable. If
visual/runtime evidence is required but unavailable, report missing evidence.

Repair routing: skill issues route to skill-design-spec; enemy issues route to
enemy-behavior-spec; status issues route to status-effect-spec; visual/audio
issues route to game-art/game-audio.

## Completion Conditions

Return `COMPLETED` when combat readability has no blockers. Return
`FAILED_VALIDATION` when required combat feedback is unreadable or unverifiable.
