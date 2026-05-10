# Genre Hybridization Spec Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Defines how multiple game genres are combined into one coherent product
concept. It turns ideas like "raising + tower defense" or "SLG + MMOARPG" into
a primary loop, supporting genre roles, system interfaces, risk controls, and
downstream design constraints.

## Input Contract

Required: product brief or initial game idea, target genre ingredients, and
audience positioning.

Optional: human preference notes, reference games, target platform, production
scope, monetization constraints, session length target, game-genre-common
pattern candidates, and excluded genre patterns.

## Output Contract

Writes `.allforai/game-design/design/genre-hybridization-spec.json`.

The spec includes `hybrid_id`, `primary_genre`, `secondary_genres`,
`flavor_genres`, `genre_role_map`, `core_loop_owner`, `supporting_loop_refs`,
`genre_interface_contracts`, `player_expectation_contracts`,
`session_layering`, `progression_layering`, `economy_interfaces`,
`combat_or_challenge_interfaces`, `content_interfaces`,
`social_or_liveops_interfaces`, `ui_complexity_constraints`,
`art_audio_implications`, `genre_common_skill_refs`, `integration_risks`,
`anti_patterns`, `downstream_constraints`, `validation_cases`, `state`, and
`consumer_refs`.

Each `genre_interface_contract` includes `source_genre`, `target_genre`,
`transferred_resource_or_goal`, `feedback_signal`, `frequency`, `failure_mode`,
`repair_rule`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_positioning`, `blocked_by_genre_inputs`.

## Invocation Contract

```json
{
  "skill": "game-design/genre-hybridization-spec",
  "mode": "spec_validate",
  "input_paths": {
    "audience_positioning": ".allforai/game-design/design/audience-positioning-spec.json",
    "brief": ".allforai/game-design/design/product-brief.json"
  },
  "output_root": ".allforai/game-design/design"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that exactly one genre owns the primary moment-to-moment loop unless the
spec explicitly defines a mode-based split. Every secondary genre must
contribute a concrete role such as progression, content structure, combat
resolution, economy, social pressure, session framing, collection, or liveops.

Check that genre interfaces transfer an observable resource, goal, risk,
reward, constraint, or feedback signal. Reject hybrids where genres are only
theme labels or where two complete games sit side by side without shared
resources, goals, feedback, or progression.

Validate the 30-second, 3-minute, 30-minute, and 3-day experience ladder:
players must be able to perceive what the hybrid is doing at each timescale.
Check for conflicting player expectations, excessive UI complexity, incompatible
session lengths, monetization pressure against core fun, and production scope
explosion.

If reference games, genre ingredients, or audience positioning are required but
missing, return `blocked_by_positioning` or `blocked_by_genre_inputs`; do not
invent market proof or pretend a genre role is validated.

Repair routing: unclear target player routes to `audience-positioning-spec`;
unclear experience promise routes to `player-experience-contract`; missing
genre pattern contracts route to `game-genre-common`; overloaded loops route to
`core-game-loop-spec`; economy conflicts route to `economy-spec`; progression
conflicts route to `progression-spec`; UI complexity risks route to `game-ui`.

## Completion Conditions

Return `COMPLETED` when the hybrid has one coherent primary loop, explicit
secondary genre roles, concrete cross-genre interfaces, validated timescale
experience, and downstream constraints. Return `FAILED_VALIDATION` when the
hybrid is only a label, duplicates complete games without integration, or cannot
be converted into system, content, economy, UI, level, and runtime contracts.
