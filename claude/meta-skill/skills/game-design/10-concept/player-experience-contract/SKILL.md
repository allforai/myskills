---
name: game-design-10-concept-player-experience-contract
description: Internal bundled meta-skill module for game-design/10-concept/player-experience-contract; use within generated bootstrap node-specs when this exact contract is selected.
---

# Player Experience Contract Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the player-facing game design contract: target player, play context,
session length, platform, motivation, emotional arc, complexity budget,
accessibility boundaries, monetization stance, and human preference constraints.

## Input Contract

Required: product concept and game-design registry.

Optional: market references, target platform, monetization preference, audience
notes, accessibility constraints, art direction input, and competitor notes.

## Output Contract

Writes:

- `.allforai/game-design/design/player-experience-contract.json`
- `.allforai/game-design/design/player-experience-report.json`

The contract must include `target_player`, `session_model`, `platform_context`,
`core_fantasy`, `motivation_drivers`, `emotion_curve`, `complexity_budget`,
`failure_tolerance`, `reward_expectations`, `monetization_constraints`,
`accessibility_constraints`, `preference_constraints`, `hard_no_goals`,
`downstream_requirements`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_missing_concept`, `blocked_by_conflicting_preferences`.

## Invocation Contract

```json
{
  "skill": "game-design/player-experience-contract",
  "mode": "spec_validate",
  "input_paths": {
    "registry": ".allforai/game-design/design/game-design-registry.json",
    "product_concept": ".allforai/product-concept.json"
  },
  "output_root": ".allforai/game-design/design"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that target player, session, platform, fantasy, motivation, emotion,
complexity, failure, reward, monetization, and preference constraints do not
contradict each other. Strictly expose unresolved preference conflicts.

Repair routing: missing concept routes upstream; inconsistent pillars route to
`game-pillar-spec`; impossible runtime/platform assumptions route to
`implementation-feasibility-qa`.

## Completion Conditions

Return `COMPLETED` when the player experience contract is internally coherent
and every downstream requirement has a consumer. Return `FAILED_VALIDATION` for
unresolved contradictions.
