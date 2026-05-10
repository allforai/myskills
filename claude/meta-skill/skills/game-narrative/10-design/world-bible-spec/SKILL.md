# World Bible Spec Skill

> Internal sub-skill for game-narrative pipelines. Status: bundled, inactive, not wired.

## Overview

Defines world setting, rules, factions, locations, terminology, tone, and
constraints that narrative, level, art, UI, and content planning must preserve.

## Input Contract

Required: player experience or game concept.

Optional: narrative tone, art direction, content taxonomy, level design, and
reference constraints.

## Output Contract

Writes `.allforai/game-design/narrative/world-bible-spec.json` and a report.
Entries include `setting`, `era`, `tone`, `world_rules`, `factions`,
`locations`, `terminology`, `forbidden_lore`, `asset_requirements`, `state`,
and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_concept`.

## Invocation Contract

```json
{"skill":"game-narrative/world-bible-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/narrative"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check internal consistency, usable terminology, art/content implications, and
that rules do not contradict gameplay pillars.

Repair routing: tone gaps route to narrative-tone-design; content gaps route to
content-taxonomy; art implications route to game-art art direction.

## Completion Conditions

Return `COMPLETED` when world rules are consistent and usable. Return
`FAILED_VALIDATION` when world rules contradict themselves or gameplay.
