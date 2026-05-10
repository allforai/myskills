# Relationship System Spec Skill

> Internal sub-skill for game-genre-common pipelines. Status: bundled, inactive, not wired.

## Overview

Defines affinity, trust, romance, rivalry, loyalty, gifts, dialogue thresholds,
relationship events, and consequences.

## Input Contract

Required: character arc spec or content taxonomy with relationship candidates.

Optional: quest patterns, narrative triggers, economy/gift items, UI registry,
and progression constraints.

## Output Contract

Writes `.allforai/game-design/genre-common/relationship-system-spec.json` and a
report. Relationships include `relationship_id`, `participant_refs`,
`score_rule`, `thresholds`, `event_refs`, `gift_rules`, `dialogue_unlocks`,
`consequences`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_characters`.

## Invocation Contract

```json
{"skill":"game-genre-common/relationship-system-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/genre-common"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check participants, score changes, thresholds, event reachability, consequence
clarity, and UI feedback.

Repair routing: character gaps route to character-arc-spec; event gaps to
narrative-event-trigger-spec; gift/economy gaps to economy specs.

## Completion Conditions

Return `COMPLETED` when relationship rules are reachable and meaningful. Return
`FAILED_VALIDATION` when relationship states cannot change or be observed.
