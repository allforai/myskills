# Teaching Beat Spec Skill

> Internal sub-skill for game-level pipelines. Status: bundled, inactive, not wired.

## Overview

Defines how levels teach mechanics through layout, enemy placement, hazards,
repetition, and safe practice.

## Input Contract

Required: level flow design and mechanics/onboarding specs.

Optional: tutorial step spec, level layout spec, enemy list, UI prompts, and
player experience contract.

## Output Contract

Writes `.allforai/game-design/levels/teaching-beat-spec.json` and a report.
Beats include `beat_id`, `level_id`, `teaches_feature`, `setup`, `safe_practice`,
`test_moment`, `failure_recovery`, `required_layout`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_mechanics`.

## Invocation Contract

```json
{"skill":"game-level/teaching-beat-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/levels"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check each taught feature has introduction, practice, test, and recovery. Do
not require text prompts when layout can teach, but record the teaching method.

Repair routing: missing mechanics route to game-design mechanics; layout gaps
route to level-layout-spec; onboarding gaps route to game-onboarding.

## Completion Conditions

Return `COMPLETED` when teaching beats are playable and scoped. Return
`FAILED_VALIDATION` when a required feature lacks a teachable moment.
