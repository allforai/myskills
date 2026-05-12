---
name: game-level-20-spec-level-difficulty-budget-spec
description: Internal bundled meta-skill module for game-level/20-spec/level-difficulty-budget-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Level Difficulty Budget Spec Skill

> Internal sub-skill for game-level pipelines. Status: bundled, inactive, not wired.

## Overview

Defines per-level, per-region, or per-room difficulty and psychological budgets
that translate the global difficulty experience into concrete level
constraints. It bridges difficulty intent, encounter pressure, hazards,
rewards, recovery, retry cost, counterplay, player emotion, cognitive load,
frustration risk, and automated validation probes.

Use this before encounter/reward placement QA or frontend playability probes
when a game needs controlled level difficulty rather than ad hoc "easy/medium"
labels.

## Input Contract

Required: difficulty experience spec, level flow design, level layout spec,
objective system requirements, and core loop requirements.

Optional: encounter placement spec, reward placement spec, teaching beats,
progression curve, combat balance report, enemy list, item/skill tables,
player ability model, accessibility constraints, telemetry model, blockout
manifest, and playtest/probe evidence.

## Output Contract

Writes:

- `.allforai/game-design/levels/level-difficulty-budget-spec.json`
- `.allforai/game-design/levels/level-difficulty-budget-report.json`

Budget entries must include `budget_id`, `level_id`, `region_ref`,
`source_refs`, `target_difficulty`, `skill_requirement`, `pressure_budget`,
`psychological_curve`, `enemy_budget`, `hazard_budget`, `resource_budget`,
`recovery_budget`, `teaching_budget`, `reward_budget`,
`expected_failure_count`, `retry_cost`, `difficulty_spike_limit`,
`counterplay_requirements`, `assist_or_accessibility_rules`,
`telemetry_signals`, `validation_probe`, `state`, and `consumer_refs`.

`psychological_curve` must include `entry_state`, `target_emotion`,
`pacing_phase`, `tension_level`, `cognitive_load`, `stress_budget`,
`relief_windows`, `confidence_recovery`, `frustration_risk`,
`motivation_payoff`, `fatigue_risk`, and `evidence_signal`.

Example:

```json
{
  "psychological_curve": {
    "entry_state": "curious",
    "target_emotion": "mastery",
    "pacing_phase": "learn",
    "tension_level": 0.62,
    "cognitive_load": 0.45,
    "stress_budget": 0.55,
    "relief_windows": [{"after": "first_enemy_wave", "duration_seconds": 8}],
    "confidence_recovery": [{"trigger": "checkpoint", "expected_effect": "reduce_retry_friction"}],
    "frustration_risk": "medium",
    "motivation_payoff": "new_skill_mastery",
    "fatigue_risk": "low",
    "evidence_signal": "death_count <= 2 and retry_time_seconds <= 20"
  }
}
```

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_difficulty_spec`, `blocked_by_level_layout`,
`blocked_by_missing_balance`, `blocked_by_missing_probe`.

## Invocation Contract

```json
{
  "skill": "game-level/level-difficulty-budget-spec",
  "mode": "spec_validate",
  "input_paths": {
    "difficulty_experience": ".allforai/game-design/design/difficulty-experience-spec.json",
    "core_loop": ".allforai/game-design/design/core-game-loop-spec.json",
    "level_flow": ".allforai/game-design/levels/level-flow-design.json",
    "level_layout": ".allforai/game-design/levels/level-layout-spec.json",
    "objective_system": ".allforai/game-design/systems/objective-system-spec.json"
  },
  "output_root": ".allforai/game-design/levels"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Psychological Pacing Methodology

Design level psychology as a sequence of player states, not as a flat
difficulty number. A healthy short-form level loop usually follows:

```text
safe_intro -> learn -> confirm -> ramp -> peak_test -> release -> recovery -> anticipation
```

Allowed `pacing_phase` values:

| Phase | Player state | Design function |
|---|---|---|
| `safe_intro` | curious, oriented | Let the player observe goal, space, controls, and threat without high punishment. |
| `learn` | lightly uncertain | Introduce one new mechanic or rule with low risk. |
| `confirm` | gaining control | Let the player repeat success and receive clear feedback. |
| `ramp` | focused, tense | Increase pressure through enemy, hazard, space, time, or resource constraints. |
| `peak_test` | highly engaged | Combine learned mechanics under readable pressure. |
| `release` | relief, payoff | Reduce pressure and deliver reward, spectacle, story, or clear progress. |
| `recovery` | preparing | Offer checkpoint, refill, shop, choice, route planning, or quiet exploration. |
| `anticipation` | curious to continue | Show a new goal, ability, enemy, region, mystery, or reward promise. |

Phase transition rules:

- New mechanics should move `safe_intro -> learn -> confirm` before
  `peak_test`.
- `ramp` may raise pressure only when the required skill was introduced or is
  already part of the player model.
- `peak_test` should be followed by `release` or `recovery` unless the design
  intentionally creates endurance pressure and has an explicit fatigue budget.
- `release` should connect payoff to the pressure just survived, not appear at
  a random time.
- `recovery` must scale with failure cost. Longer retry cost needs stronger
  checkpoint, refill, shortcut, or rest support.
- `anticipation` should create a next-step motivation before the level/session
  ends.

Anti-patterns to reject:

- New mechanic + complex layout + strong enemy + time pressure in the same beat.
- Multiple `peak_test` beats in a row without relief or recovery.
- Hidden or unreadable danger counted as "tension".
- Reward placed before pressure when the intended emotion is mastery or relief.
- High failure cost with no retry shortcut or confidence recovery.
- Long low-pressure traversal with no anticipation, choice, story, or planning.
- Dynamic difficulty that changes outcomes invisibly and breaks player trust.

## Automatic Validation

Check that every required level or region has a measurable budget for pressure,
enemy/hazard density, recovery, reward cadence, retry cost, spike limits, and
psychological curve. The budget must match the target player skill model,
session length, progression curve, emotional arc, and failure/recovery
expectations.

Methodology:

- Convert difficulty intent into measurable budget axes, not labels.
- Convert psychological intent into measurable curve axes, not mood labels.
- Express difficulty with both pressure and recovery; harder levels may raise
  pressure only when counterplay and recovery are defined.
- Express psychological pressure with entry state, target emotion, tension,
  cognitive load, relief, confidence recovery, and frustration risk.
- Limit spikes by comparing each region against previous and next regions.
- Limit psychological spikes by ensuring relief windows or confidence recovery
  after high stress, high cognitive load, or repeated failure points.
- Tie enemy/hazard budgets to available player mechanics and teaching beats.
- Tie resource/reward budgets to expected attrition and economy/progression
  pacing.
- Define at least one validation probe per budget: static blockout check,
  simulated encounter estimate, frontend playability probe, telemetry event, or
  playtest trace.
- Define at least one psychological evidence signal per budget, such as death
  count, retry duration, idle/backtracking time, health/resource depletion,
  objective completion time, input error repetition, pause/menu openings,
  tutorial hint usage, or explicit telemetry event.
- Validate pacing-phase order and transitions. Reject phase sequences that skip
  learning/confirmation before tests, stack high-pressure beats without
  recovery, or declare payoff emotions without a matching release/reward beat.

If no executable or probeable validation path exists for a required budget,
return `blocked_by_missing_probe`; do not accept prose judgment as evidence.

Repair routing: vague difficulty routes to `difficulty-experience-spec`;
vague emotion or motivation routes to `player-experience-contract`; layout gaps
route to `level-layout-spec`; encounter pressure gaps route to
`encounter-placement-spec`; reward/recovery or relief-window gaps route to
`reward-placement-spec`; teaching or cognitive-load gaps route to
`teaching-beat-spec`; numeric gaps route to `game-balance`; probe gaps route to
`game-frontend/playability-probe-qa` or `level-playability-qa`.

## Completion Conditions

Return `COMPLETED` when level difficulty budgets are measurable, source-traced,
and tied to validation probes. Return `FAILED_VALIDATION` when required levels
lack budgets, psychological curves, spike limits, counterplay, recovery, or
verifiable evidence.
