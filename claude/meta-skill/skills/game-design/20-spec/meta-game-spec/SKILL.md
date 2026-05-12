---
name: game-design-20-spec-meta-game-spec
description: Internal bundled meta-skill module for game-design/20-spec/meta-game-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Meta Game Spec Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the long-term game outside a single run/session: collection, account
progression, daily/weekly loops, social surfaces, seasonal goals, mastery,
cosmetic pursuit, and re-entry motivation.

## Input Contract

Required: player experience contract, core game loop, progression spec, and
game-design registry.

Optional: economy spec, game mode spec, retention brief, monetization
constraints, content taxonomy, social/multiplayer constraints, and liveops
calendar.

## Output Contract

Writes:

- `.allforai/game-design/systems/meta-game-spec.json`
- `.allforai/game-design/systems/meta-game-report.json`

Meta-game systems must include `system_id`, `player_motivation`,
`session_bridge`, `long_term_goal`, `progression_refs`, `reward_model`,
`reset_or_season_rule`, `content_refresh_rule`, `ui_surfaces`,
`economy_refs`, `social_refs`, `art_requirements`, `audio_requirements`,
`runtime_system_refs`, `telemetry_signals`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_progression`, `blocked_by_economy`, `blocked_by_scope`.

## Invocation Contract

```json
{
  "skill": "game-design/meta-game-spec",
  "mode": "spec_validate",
  "input_paths": {
    "player_experience": ".allforai/game-design/design/player-experience-contract.json",
    "core_loop": ".allforai/game-design/design/core-game-loop-spec.json",
    "progression": ".allforai/game-design/systems/progression-spec.json",
    "registry": ".allforai/game-design/design/game-design-registry.json"
  },
  "output_root": ".allforai/game-design/systems"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every long-term motivation has an in-session action, reward, UI
surface, economy/progression owner, and content refresh path. The meta game
must not contradict the target session length, complexity budget, monetization
promise, or genre hybrid contract.

Repair routing: missing re-entry motivation routes to
`player-experience-contract`; missing unlock structure routes to
`progression-spec`; missing rewards route to `economy-spec`; missing content
types route to `content-taxonomy-spec`.

## Completion Conditions

Return `COMPLETED` when meta-game loops connect back into core play and all
long-term goals have downstream owners. Return `FAILED_VALIDATION` when the
meta game is only decorative or cannot be executed by progression/economy/UI.
