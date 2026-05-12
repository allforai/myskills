---
name: game-level-20-spec-player-skill-model-spec
description: Define the target player skill baseline that lets an LLM produce effective, measurable level difficulty instead of vague easy/medium/hard labels.
---

# Player Skill Model Spec Skill

> Internal sub-skill for game-level pipelines. Status: bundled,
> bootstrap-wired through level-design sub-skill mapping.

## Overview

Defines "difficulty for whom" before level difficulty budgets are written. It
turns audience, controls, mechanics, platform, session length, accessibility
needs, and progression intent into a measurable target player skill baseline.

Use this when an LLM must design level difficulty without relying on telemetry
or human playtest statistics. The output becomes the reference ruler for
`level-difficulty-budget-spec` and `level-difficulty-validation-qa`.

## Input Contract

Required: player experience contract, audience positioning, core loop, mechanics
spec, difficulty experience spec, level flow design, and target platform/input
constraints.

Optional: combat spec, objective system spec, progression spec, tutorial/FTUE
spec, accessibility preferences, control scheme, camera/view mode, session
length target, and genre references.

## Output Contract

Writes:

- `.allforai/game-design/levels/player-skill-model-spec.json`
- `.allforai/game-design/levels/player-skill-model-report.json`

The model must include `model_id`, `target_player_refs`, `platform_refs`,
`control_model`, `skill_tiers`, `mechanic_mastery_ladder`,
`execution_capabilities`, `reaction_capabilities`, `cognitive_capabilities`,
`combat_capabilities`, `navigation_capabilities`, `resource_management_capabilities`,
`failure_tolerance`, `learning_assumptions`, `accessibility_constraints`,
`difficulty_axis_scale`, `design_thresholds`, `invalid_difficulty_patterns`,
`validation_guidance`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_player_experience`, `blocked_by_mechanics`,
`blocked_by_platform_constraints`.

## Invocation Contract

```json
{
  "skill": "game-level/player-skill-model-spec",
  "mode": "spec_validate",
  "input_paths": {
    "player_experience": ".allforai/game-design/concept/player-experience-contract.json",
    "audience": ".allforai/game-design/concept/audience-positioning-spec.json",
    "core_loop": ".allforai/game-design/design/core-game-loop-spec.json",
    "mechanics": ".allforai/game-design/design/mechanics-spec.json",
    "difficulty_experience": ".allforai/game-design/design/difficulty-experience-spec.json",
    "level_flow": ".allforai/game-design/levels/level-flow-design.json"
  },
  "output_root": ".allforai/game-design/levels"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Skill Axis Methodology

Define skill as measurable capability bands, not vague audience labels.

Required axes:

- `execution_capabilities`: input sequence length, timing tolerance, movement
  precision, aim precision, cancel/dodge/combo complexity, and consistency.
- `reaction_capabilities`: minimum readable telegraph window, simultaneous
  threat count, expected response type, and panic-recovery allowance.
- `cognitive_capabilities`: active rule count, new-mechanic count per beat,
  memory burden, route ambiguity, puzzle state complexity, and UI/objective
  interpretation load.
- `combat_capabilities`: enemy pattern recognition, spacing/kiting, target
  priority, resource usage under pressure, and defensive decision timing.
- `navigation_capabilities`: route reading, platform spacing, camera/view
  interpretation, backtracking tolerance, and spatial memory.
- `resource_management_capabilities`: expected attrition planning, consumable
  timing, economy/reward tradeoff reading, and risk/reward tolerance.
- `failure_tolerance`: acceptable retry duration, repeated traversal length,
  expected failure count, loss severity, and confidence recovery need.

Use a 1-5 scale for each axis:

| Tier | Meaning | Design implication |
|---|---|---|
| 1 | First-time or casual | One pressure source, generous timing, low punishment, explicit teaching. |
| 2 | Familiar beginner | Two simple pressures, readable hazards, short retry, clear recovery. |
| 3 | Core target | Combined mechanics under moderate pressure, visible counterplay, fair failure. |
| 4 | Skilled | Multi-axis pressure, tighter timing, longer planning, explicit challenge framing. |
| 5 | Expert | Precision/execution mastery, high pressure stacking, optional or late-game only. |

For each tier and axis, define concrete thresholds. Examples:

- `minimum_telegraph_ms`
- `max_simultaneous_threats`
- `max_new_mechanics_per_region`
- `max_precision_jump_chain`
- `max_retry_seconds`
- `max_uninterrupted_high_pressure_seconds`
- `max_cognitive_rules_active`
- `required_recovery_after_failures`

## Automatic Validation

Reject a model that only says "casual", "hardcore", "easy", "medium", or
"difficult" without thresholds. Check every core mechanic has a mastery ladder:
`observe -> safe_practice -> confirm -> pressure_use -> combined_use`.

Check the target player is compatible with platform/input constraints. A mobile
touch game, keyboard precision platformer, controller action game, and
turn-based tactics game need different thresholds.

Check every difficulty axis has:

- measurable thresholds,
- examples of allowed pressure,
- examples of invalid pressure,
- repair guidance for over-budget level regions,
- consumer refs to difficulty budget and difficulty validation.

Do not use user telemetry or statistical assumptions as required input. This
skill defines an explicit design baseline from concept and mechanics.

Repair routing: unclear target player routes to `player-experience-contract`
or `audience-positioning-spec`; unclear mechanic mastery routes to
`mechanics-spec`; unclear difficulty goals route to
`difficulty-experience-spec`; unclear level sequence routes to
`level-flow-design`.

## Completion Conditions

Return `COMPLETED` when the model can be used as a ruler for level budgets and
difficulty QA. Return `FAILED_VALIDATION` when any major difficulty axis lacks a
measurable target-player threshold.
