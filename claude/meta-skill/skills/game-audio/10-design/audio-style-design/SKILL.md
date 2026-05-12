---
name: game-audio-10-design-audio-style-design
description: Internal bundled meta-skill module for game-audio/10-design/audio-style-design; use within generated bootstrap node-specs when this exact contract is selected.
---

# Audio Style Design Skill

> Internal sub-skill for game-audio pipelines. Status: bundled, inactive, not wired.

## Overview

Defines sonic palette, mood, instrumentation, texture, intensity levels, UI
sound language, and mix priorities.

## Input Contract

Required: game tone or concept. Optional: narrative tone, art style, genre,
platform constraints.

## Output Contract

Writes `.allforai/game-design/audio/audio-style-design.json` and
`.allforai/game-design/audio/audio-style-report.json`.

Style schema:

```json
{
  "schema_version": "1.0",
  "sonic_palette": {
    "mood": [],
    "instruments": [],
    "texture": "8bit | orchestral | synthetic | acoustic | hybrid",
    "ui_language": "soft | clicky | magical | mechanical | organic",
    "forbidden_traits": []
  },
  "mix_priorities": ["critical_gameplay", "ui_feedback", "music", "ambience"]
}
```

Allowed states: `draft`, `validated`, `needs_revision`.

Downstream consumers: `game-audio/sfx-spec`, `game-audio/music-cue-spec`,
`game-audio/audio-loudness-qa`, `game-narrative/narrative-tone-design`,
`game-ui/ui-mockup-generation`, and runtime audio mix import.

## Invocation Contract

```json
{"skill":"game-audio/audio-style-design","mode":"design_validate","input_paths":{"concept_contract":".allforai/concept-contract.json","game_design_doc":".allforai/game-design/game-design-doc.json"},"output_root":".allforai/game-design/audio"}
```

Supported modes: `design_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check mood/instrumentation consistency, UI/gameplay distinction, intensity
tiers, forbidden audio traits, and target platform constraints.

SFX and music specs must reference this style contract rather than inventing
their own sonic language.

Repair routing: missing tone context returns to the concept or narrative tone
skill; contradictory sonic rules repair here; generated music/SFX mismatches
route back through their producer only after this style contract is stable.

## Completion Conditions

Return `COMPLETED` when style contract validates. Return
`COMPLETED_WITH_WARNINGS` when defaults are inferred.
