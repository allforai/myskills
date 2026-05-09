# Narrative Tone Design Skill

> Internal sub-skill for game-narrative pipelines. Status: bundled, inactive, not wired.

## Overview

Defines narrative voice, world language, humor/drama level, character voice
rules, terminology, and forbidden wording.

## Input Contract

Required: concept, genre, audience, and game tone. Optional: character list,
world notes, UI tone, audio style.

## Output Contract

Writes `.allforai/game-design/narrative/narrative-tone-design.json` and
`.allforai/game-design/narrative/narrative-tone-report.json`.

Tone schema:

```json
{
  "schema_version": "1.0",
  "voice": "concise | whimsical | dramatic | dry | epic | cozy",
  "terminology": {},
  "forbidden_terms": [],
  "character_voice_rules": [],
  "ui_copy_rules": [],
  "localization_notes": []
}
```

Allowed states: `draft`, `validated`, `needs_revision`.

Downstream consumers: `game-narrative/dialogue-spec`,
`game-narrative/dialogue-generation`, `game-narrative/quest-text-spec`,
`game-narrative/text-consistency-qa`, `game-audio/audio-style-design`,
`game-ui/ui-mockup-generation`, and localization import.

## Invocation Contract

```json
{"skill":"game-narrative/narrative-tone-design","mode":"design_validate","input_paths":{"concept_contract":".allforai/concept-contract.json","game_design_doc":".allforai/game-design/game-design-doc.json"},"output_root":".allforai/game-design/narrative"}
```

Supported modes: `design_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check tone consistency, terminology, character voice separability, UI/narrative
compatibility, and forbidden style conflicts.

Dialogue, quest text, UI copy, and audio voice prompts must use this terminology
contract when narrative is active.

Repair routing: missing concept or audience context returns to the concept
contract; contradictory voice/terminology rules repair here; generated text
failures route to the producer only after this tone contract validates.

## Completion Conditions

Return `COMPLETED` when tone contract validates. Return
`COMPLETED_WITH_WARNINGS` when optional world details are inferred.
