# Character Arc Spec Skill

> Internal sub-skill for game-narrative pipelines. Status: bundled, inactive, not wired.

## Overview

Defines character motivations, relationships, arcs, state changes, voice needs,
portrait needs, and quest/story dependencies.

## Input Contract

Required: world bible or narrative tone plus character/content list.

Optional: quest chains, dialogue spec, art direction, voice/audio constraints,
and localization needs.

## Output Contract

Writes `.allforai/game-design/narrative/character-arc-spec.json` and a report.
Character entries include `character_id`, `role`, `motivation`, `arc_beats`,
`relationship_refs`, `dialogue_requirements`, `portrait_requirements`,
`voice_requirements`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_world`.

## Invocation Contract

```json
{"skill":"game-narrative/character-arc-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/narrative"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every major character has purpose, arc, voice, relationship, and content
use. Reject characters that are required but have no gameplay/narrative role.

Repair routing: world gaps route to world-bible-spec; quest gaps route to
quest-chain/narrative quest specs; portrait gaps route to game-art.

## Completion Conditions

Return `COMPLETED` when character arcs are traceable. Return
`FAILED_VALIDATION` when required characters lack role or arc.
