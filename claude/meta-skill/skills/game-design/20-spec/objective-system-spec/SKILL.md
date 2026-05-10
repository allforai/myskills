# Objective System Spec Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Defines how goals are created, tracked, completed, failed, displayed, rewarded,
and chained across main objectives, side objectives, moment-to-moment tasks,
quests, achievements, daily tasks, tutorials, and mode-specific win conditions.

## Input Contract

Required: game-design registry, core game loop, mechanics spec, progression
spec, and content taxonomy.

Optional: game mode spec, narrative quest spec, level design spec, economy spec,
onboarding spec, liveops tasks, achievement system spec, UI requirements, and
telemetry requirements.

## Output Contract

Writes `.allforai/game-design/systems/objective-system-spec.json`.

The spec includes `objective_taxonomy`, `objective_id_rules`,
`objective_types`, `tracking_rules`, `completion_rules`, `failure_rules`,
`priority_rules`, `branching_rules`, `reward_rules`, `ui_display_rules`,
`notification_rules`, `telemetry_events`, `save_state_rules`,
`anti_softlock_rules`, `content_integration`, `state`, and `consumer_refs`.

Each objective type includes `objective_type_id`, `source_refs`,
`allowed_scopes`, `required_fields`, `completion_signal`, `failure_signal`,
`reward_signal`, `ui_surface_refs`, and `test_cases`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_content`, `blocked_by_loop`.

## Invocation Contract

```json
{
  "skill": "game-design/objective-system-spec",
  "mode": "spec_validate",
  "input_paths": {
    "registry": ".allforai/game-design/design/game-design-registry.json",
    "core_loop": ".allforai/game-design/design/core-game-loop-spec.json",
    "content_taxonomy": ".allforai/game-design/content/content-taxonomy-spec.json"
  },
  "output_root": ".allforai/game-design/systems"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every objective type has a source, completion signal, failure or recovery
rule, reward or consequence rule, UI display rule, save/load behavior, and at
least one executable test case. Check for contradictory objective priorities,
unreachable objectives, hidden required goals, and softlocks caused by missed
items, destroyed objects, failed dialogue, or expired live events.

Reject objectives that cannot be observed by runtime systems or explained to
the player through UI, level, narrative, or feedback channels.

Repair routing: missing source content routes to `content-taxonomy-spec`;
quest-specific gaps route to `narrative-quest-spec`; level placement gaps route
to `level-design-spec`; reward gaps route to `economy-spec`; UI gaps route to
`game-ui`.

## Completion Conditions

Return `COMPLETED` when objectives are trackable, completable, fail-safe,
rewarded, displayable, and testable. Return `FAILED_VALIDATION` when objective
logic can softlock progression or cannot be represented in runtime state.
