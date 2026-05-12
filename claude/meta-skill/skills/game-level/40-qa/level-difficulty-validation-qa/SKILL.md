---
name: game-level-40-qa-level-difficulty-validation-qa
description: Validate actual level layout, encounters, hazards, rewards, recovery, retry cost, and probe evidence against the declared level difficulty budget.
---

# Level Difficulty Validation QA Skill

> Internal sub-skill for game-level pipelines. Status: bundled,
> bootstrap-wired through level-design sub-skill mapping.

## Overview

Validates level difficulty as a contract, not prose. It compares the declared
`level-difficulty-budget-spec` against actual level artifacts: flow, layout,
teaching beats, encounters, rewards, blockout metadata, runtime probes, and
playtest evidence when available.

This is the hard gate for difficulty spikes, unfair pressure stacking, missing
recovery, unverified skill requirements, excessive retry cost, and declared
psychological outcomes without evidence.

## Input Contract

Required: player skill model, level difficulty budget, level flow design, level
layout spec, teaching beats, encounter placement, reward placement, and
objective system requirements.

Optional: blockout manifest, collision/walkability graph, combat balance report,
progression curve, player ability model, enemy behavior specs, runtime
screenshots, bot/playability probe results, telemetry/playtest traces, death
heatmaps, completion-time stats, and accessibility constraints.

## Output Contract

Writes:

- `.allforai/game-design/levels/level-difficulty-validation-qa-report.json`
- `.allforai/game-design/levels/level-difficulty-validation-findings.json`

The report must include `validation_status`, `level_results`,
`budget_coverage`, `pressure_axis_findings`, `spike_findings`,
`teaching_readiness_findings`, `counterplay_findings`, `recovery_findings`,
`retry_cost_findings`, `psychological_curve_findings`, `evidence_findings`,
`blocked_items`, `repair_routes`, `state`, and `consumer_refs`.

Each finding must include `finding_id`, `level_id`, `region_ref`,
`budget_ref`, `severity`, `difficulty_axis`, `expected_budget`,
`actual_measurement`, `evidence_refs`, `root_cause`, `repair_target`,
`blocks_level_approval`, and `state`.

Allowed states: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_budget`, `blocked_by_missing_level_artifact`,
`blocked_by_missing_probe`, `failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-level/level-difficulty-validation-qa",
  "mode": "validate",
  "input_paths": {
    "player_skill_model": ".allforai/game-design/levels/player-skill-model-spec.json",
    "difficulty_budget": ".allforai/game-design/levels/level-difficulty-budget-spec.json",
    "level_flow": ".allforai/game-design/levels/level-flow-design.json",
    "level_layout": ".allforai/game-design/levels/level-layout-spec.json",
    "teaching_beats": ".allforai/game-design/levels/teaching-beat-spec.json",
    "encounters": ".allforai/game-design/levels/encounter-placement-spec.json",
    "rewards": ".allforai/game-design/levels/reward-placement-spec.json",
    "objective_system": ".allforai/game-design/systems/objective-system-spec.json"
  },
  "output_root": ".allforai/game-design/levels"
}
```

Supported modes: `validate`, `validate_static_only`, `validate_with_probe`,
`repair_check`.

## Automatic Validation

Validate these axes for every level/region with a budget, using the player
skill model as the threshold source:

- `mechanical_precision`: jump windows, timing windows, aiming/input complexity,
  movement constraints, and required execution consistency.
- `reaction_pressure`: telegraph time, hazard warning time, moving-platform
  timing, chase/time-limit windows, and simultaneous threat count.
- `enemy_pressure`: enemy count, behavior combination, attack frequency,
  range/angle coverage, flanking, crowd-control, and counterplay availability.
- `hazard_pressure`: trap density, visibility, avoidability, recovery after
  hit, and whether hazards combine with enemies or time pressure.
- `cognitive_load`: active rules, newly introduced mechanics, simultaneous
  goals, route ambiguity, UI/objective clarity, and puzzle state.
- `resource_pressure`: expected health/ammo/stamina/item attrition, refill
  cadence, shop/checkpoint support, and economy implications.
- `punishment_severity`: checkpoint distance, repeated traversal, death cost,
  lost resources, reset scope, and retry time.
- `psychological_curve`: entry state, target emotion, tension, stress, relief,
  confidence recovery, frustration risk, motivation payoff, fatigue risk, and
  evidence signal.

Hard-fail conditions:

- A `peak_test` or high-pressure region uses a new mechanic before `learn` and
  `confirm` beats exist.
- More than two high-pressure axes exceed budget in the same region without an
  explicit endurance budget and recovery plan.
- A spike delta exceeds `difficulty_spike_limit` with no counterplay,
  checkpoint, or relief window.
- Failure cost is high while retry path, checkpoint, or confidence recovery is
  weak.
- Hidden/unreadable danger is counted as intended tension.
- Declared psychological payoff has no matching reward, release, mastery,
  story, shortcut, or visible progress beat.
- The required evidence type is unavailable. Mark `blocked_by_missing_probe`
  instead of substituting weaker validation.

Evidence rules:

- If executable/runtime probes are available, use them for reachability,
  completion path, retry cost, timing windows, and screenshot/readability
  evidence.
- If only static artifacts are available, run static validation and mark dynamic
  measurements as `unable_to_validate`, not passed.
- If no level artifact exists for a required budget, return
  `blocked_by_missing_level_artifact`.
- LLM judgment may summarize findings, but may not be the sole evidence for
  numeric difficulty budget compliance.

Repair routing: player capability threshold defects route to
`player-skill-model-spec`; budget target defects route to
`level-difficulty-budget-spec`; layout and route defects route to
`level-layout-spec`; teaching readiness defects route to `teaching-beat-spec`;
enemy/hazard pressure defects route to `encounter-placement-spec`; reward,
recovery, checkpoint, and payoff defects route to `reward-placement-spec`;
combat number defects route to `game-balance`; runtime/probe gaps route to
`game-frontend/playability-probe-qa` or `level-playability-qa`.

## Completion Conditions

Return `COMPLETED` only when `validation_status` is `passed` or
`passed_with_warnings` and no blocker finding remains. Return
`FAILED_VALIDATION` when any level exceeds difficulty budget, lacks evidence for
required axes, or cannot route a defect to an owning skill.
