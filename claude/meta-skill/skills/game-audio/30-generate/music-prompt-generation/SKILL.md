---
name: game-audio-30-generate-music-prompt-generation
description: Internal bundled meta-skill module for game-audio/30-generate/music-prompt-generation; use within generated bootstrap node-specs when this exact contract is selected.
---

# Music Prompt Generation Skill

> Internal sub-skill for game-audio pipelines. Status: bundled, inactive, not wired.

## Overview

Produces music generation prompts, stem specs, loop instructions, transition
notes, and manifests from `music-cue-spec.json`.

## Input Contract

Required: music cue spec. Optional: audio style, narrative tone, existing music.

## Output Contract

Writes `.allforai/game-design/audio/music/music-prompt-spec.json`,
`.allforai/game-design/audio/music/music-manifest.json`, and
`.allforai/game-design/audio/music/music-generation-report.json`.

Manifest entries must include `cue_id`, `prompt_id`, `style_ref`, `duration`,
`loop`, `transition`, `stem_plan`, `path`, `state`, `qa_status`, and
`consumer_refs`.

Allowed states: `prompt_ready`, `generated`, `registered`, `approved`,
`needs_revision`, `automation_limited`.

## Invocation Contract

```json
{"skill":"game-audio/music-prompt-generation","mode":"spec_generate_validate","input_paths":{"music_cue_spec":".allforai/game-design/audio/music-cue-spec.json","audio_style":".allforai/game-design/audio/audio-style-design.json"},"output_root":".allforai/game-design/audio"}
```

Supported modes: `spec_only`, `spec_generate_validate`, `validate_existing`,
`register_existing`.

## Automatic Validation

Check cue coverage, loopability instructions, duration, stem mapping, transition
metadata, style consistency, and loudness QA readiness.

If audio generation is unavailable, emit prompt-only output with
`automation_limited` state and keep cue IDs stable for downstream runtime wiring.

Root causes for failed outputs must be classified as `music_prompt`,
`music_generation`, `music_cue_spec`, `audio_style`, `loudness_qa`, or
`runtime_import`. Prompt wording and stem-plan failures repair here; unreachable
cue IDs repair `music-cue-spec`; style mismatches repair `audio-style-design`;
clipping, silence, or bad loops repair through `audio-loudness-qa`.

## Completion Conditions

Return `COMPLETED` when prompts/manifests validate. Return
`COMPLETED_WITH_LIMITS` when generated audio is unavailable.
