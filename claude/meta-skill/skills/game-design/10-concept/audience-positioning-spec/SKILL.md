---
name: game-design-10-concept-audience-positioning-spec
description: Internal bundled meta-skill module for game-design/10-concept/audience-positioning-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Audience Positioning Spec Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the target audience, market positioning, comparable games, player
preferences, platform expectations, content boundaries, and design implications
that constrain the rest of the game design.

## Input Contract

Required: initial game idea or product brief.

Optional: human preference notes, target platform, business goal, genre hints,
reference games, market constraints, content rating target, monetization
constraints, and localization scope.

## Output Contract

Writes `.allforai/game-design/design/audience-positioning-spec.json`.

The spec includes `audience_id`, `primary_player_segments`,
`secondary_player_segments`, `platform_expectations`, `genre_expectations`,
`reference_games`, `differentiation_claims`, `preference_constraints`,
`content_boundaries`, `monetization_sensitivity`, `accessibility_expectations`,
`localization_implications`, `design_implications`, `anti_goals`, `open_risks`,
and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_brief`.

## Invocation Contract

```json
{
  "skill": "game-design/audience-positioning-spec",
  "mode": "spec_validate",
  "input_paths": {
    "brief": ".allforai/game-design/design/product-brief.json"
  },
  "output_root": ".allforai/game-design/design"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that each audience segment has playable motivation, platform expectation,
content tolerance, complexity tolerance, monetization sensitivity, and at least
one concrete implication for loop, UI, art, audio, narrative, difficulty, or
session length.

Reject positioning that only lists demographics without design consequences.
Reject differentiation claims that cannot be reflected in mechanics, content,
visual direction, UX, or progression. If reference games or market evidence are
required but unavailable, return `blocked_by_brief`; do not invent evidence.

Repair routing: missing human preference data routes to product brief
collection; unclear player motivation routes to `player-experience-contract`;
unusable differentiation routes to `game-pillar-spec`.

## Completion Conditions

Return `COMPLETED` when target audience and positioning produce concrete,
traceable design constraints. Return `FAILED_VALIDATION` when the audience is
too vague to constrain product design.
