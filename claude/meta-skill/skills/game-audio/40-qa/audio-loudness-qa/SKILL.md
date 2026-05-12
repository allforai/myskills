---
name: game-audio-40-qa-audio-loudness-qa
description: Internal bundled meta-skill module for game-audio/40-qa/audio-loudness-qa; use within generated bootstrap node-specs when this exact contract is selected.
---

# Audio Loudness QA Skill

> Internal sub-skill for game-audio pipelines. Status: bundled, inactive, not wired.

## Overview

Validates audio outputs for loudness, clipping, silence, duration, loopability,
mix priority, and event alignment.

## Input Contract

Required: audio manifest or SFX/music files. Optional: audio style, SFX spec,
music cue spec.

## Output Contract

Writes `.allforai/game-design/audio/audio-loudness-qa-report.json`.

Issues must include `audio_id`, `severity`, `metric`, `expected`, `actual`,
`root_cause`, `repair_target`, and `blocks_runtime`.

Downstream consumers: runtime audio import, playtest QA, `sfx-generation`,
`music-prompt-generation`, UI feedback QA, and VFX timing QA.

## Invocation Contract

```json
{"skill":"game-audio/audio-loudness-qa","mode":"validate","input_paths":{"sfx_manifest":".allforai/game-design/audio/sfx/sfx-manifest.json","music_manifest":".allforai/game-design/audio/music/music-manifest.json"},"output_root":".allforai/game-design/audio"}
```

Supported modes: `validate`, `validate_artifacts_only`, `validate_existing`.

## Automatic Validation

Check clipping, silence, loudness ranges, duration, loops, fades, filename/path
rules, and event/cue coverage.

Classify defects as `audio_generation`, `audio_spec`, `registry`, or
`runtime_tooling` so repair routes to the correct upstream skill.

## Completion Conditions

Return `COMPLETED` when no blocker/major audio issues remain. Return
`FAILED_VALIDATION` with repair targets for blockers.
