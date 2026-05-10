# Difficulty Experience Spec Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the intended difficulty experience: pressure curve, failure frequency,
skill learning, readability, recovery, assist options, difficulty modes, dynamic
difficulty rules, and how difficulty should feel before numbers are tuned.

## Input Contract

Required: player experience contract, game pillars, core game loop, mechanics
spec, progression spec, and level design spec.

Optional: audience positioning spec, combat spec, economy spec, onboarding
spec, game mode spec, balance reports, accessibility constraints, telemetry
events, and target platform.

## Output Contract

Writes `.allforai/game-design/design/difficulty-experience-spec.json`.

The spec includes `difficulty_profile_id`, `target_skill_model`,
`pressure_curve`, `learning_curve`, `failure_frequency_target`,
`recovery_rules`, `readability_requirements`, `difficulty_modes`,
`dynamic_adjustment_rules`, `assist_options`, `punishment_rules`,
`checkpoint_rules`, `telemetry_signals`, `balance_hooks`, `content_refs`,
`accessibility_requirements`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_mechanics`, `blocked_by_audience`.

## Invocation Contract

```json
{
  "skill": "game-design/difficulty-experience-spec",
  "mode": "spec_validate",
  "input_paths": {
    "player_experience": ".allforai/game-design/design/player-experience-contract.json",
    "mechanics": ".allforai/game-design/systems/mechanics-spec.json",
    "progression": ".allforai/game-design/systems/progression-spec.json"
  },
  "output_root": ".allforai/game-design/design"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that difficulty targets match audience, platform, session length, input
complexity, readability, progression pacing, and failure/retry expectations.
Every difficulty mode or dynamic adjustment must specify what changes, what
does not change, how rewards are affected, and how the player can understand
the rule.

Reject difficulty specs that only say "easy/normal/hard" without measurable
pressure, recovery, readability, and progression consequences. Reject dynamic
difficulty that changes player outcomes invisibly without an explicit design
rule.

Repair routing: unclear target player routes to `audience-positioning-spec` or
`player-experience-contract`; numeric gaps route to `game-balance`; combat
readability gaps route to `game-combat`; teaching gaps route to
`game-onboarding`; level spikes route to `game-level`.

## Completion Conditions

Return `COMPLETED` when difficulty can guide level, combat, balance,
onboarding, accessibility, and telemetry work. Return `FAILED_VALIDATION` when
difficulty cannot be measured, taught, recovered from, or represented in
downstream design.
