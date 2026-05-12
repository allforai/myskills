---
name: game-level-20-spec-teaching-beat-spec
description: Internal bundled meta-skill module for game-level/20-spec/teaching-beat-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Teaching Beat Spec Skill

> Internal sub-skill for game-level pipelines. Status: bundled, inactive, not wired.

## Overview

Defines how levels teach mechanics through layout, enemy placement, hazards,
repetition, and safe practice.

## Input Contract

Required: level flow design and mechanics/onboarding specs.

Optional: tutorial step spec, level layout spec, level difficulty budget, enemy
list, UI prompts, and player experience contract.

## Output Contract

Writes `.allforai/game-design/levels/teaching-beat-spec.json` and a report.
Beats include `beat_id`, `level_id`, `teaches_feature`, `setup`,
`safe_practice`, `test_moment`, `failure_recovery`, `required_layout`,
`difficulty_budget_refs`, `psychological_phase_refs`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_mechanics`.

## Invocation Contract

```json
{
  "skill": "game-level/teaching-beat-spec",
  "mode": "spec_validate",
  "input_paths": {
    "level_flow": ".allforai/game-design/levels/level-flow-design.json",
    "mechanics": ".allforai/game-design/systems/mechanics-spec.json",
    "level_layout": ".allforai/game-design/levels/level-layout-spec.json",
    "difficulty_budget": ".allforai/game-design/levels/level-difficulty-budget-spec.json"
  },
  "output_root": ".allforai/game-design/levels"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check each taught feature has introduction, practice, test, and recovery. Do
not require text prompts when layout can teach, but record the teaching method.
When a level difficulty budget is present, verify teaching beats align with
`learn` and `confirm` phases, stay within cognitive-load and stress budgets,
and provide confidence recovery before any referenced `peak_test`.

Repair routing: missing mechanics route to game-design mechanics; layout gaps
route to level-layout-spec; difficulty or psychological budget mismatches route
to level-difficulty-budget-spec; onboarding gaps route to game-onboarding.

## Completion Conditions

Return `COMPLETED` when teaching beats are playable and scoped. Return
`FAILED_VALIDATION` when a required feature lacks a teachable moment.
