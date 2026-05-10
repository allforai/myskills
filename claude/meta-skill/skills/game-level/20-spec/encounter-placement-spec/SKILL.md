# Encounter Placement Spec Skill

> Internal sub-skill for game-level pipelines. Status: bundled, inactive, not wired.

## Overview

Defines encounter placement, enemy/hazard composition, spawn rules, difficulty
beats, counterplay, and level pacing constraints.

## Input Contract

Required: level flow design, level layout spec, and enemy/combat context.

Optional: level difficulty budget, progression curve, economy rewards, teaching
beats, and art/VFX/audio requirements.

## Output Contract

Writes `.allforai/game-design/levels/encounter-placement-spec.json` and a
report. Encounters include `encounter_id`, `level_id`, `region_ref`,
`enemy_refs`, `hazards`, `spawn_rule`, `difficulty_intent`, `counterplay`,
`difficulty_budget_ref`, `pressure_budget_ref`, `reward_refs`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_layout`.

## Invocation Contract

```json
{
  "skill": "game-level/encounter-placement-spec",
  "mode": "spec_validate",
  "input_paths": {
    "level_flow": ".allforai/game-design/levels/level-flow-design.json",
    "level_layout": ".allforai/game-design/levels/level-layout-spec.json",
    "enemy_design_list": ".allforai/game-design/content/enemy-design-list.json",
    "combat": ".allforai/game-design/systems/combat-spec.json",
    "difficulty_budget": ".allforai/game-design/levels/level-difficulty-budget-spec.json",
    "teaching_beats": ".allforai/game-design/levels/teaching-beat-spec.json"
  },
  "output_root": ".allforai/game-design/levels"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check encounter reachability, spacing, difficulty order, enemy role coverage,
reward placement, and recovery after failure. When a level difficulty budget is
present, verify enemy/hazard density, spike limits, counterplay requirements,
expected failure count, retry cost, and psychological pressure match the
referenced budget.

Repair routing: layout gaps route to level-layout-spec; enemy gaps route to
enemy-design-list-generation; budget mismatches route to
level-difficulty-budget-spec; numeric outliers route to game-balance.

## Completion Conditions

Return `COMPLETED` when encounters are placed and paced. Return
`FAILED_VALIDATION` when encounters are unreachable, unfair, or unowned.
