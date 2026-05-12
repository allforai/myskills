---
name: game-audio-30-generate-sfx-generation
description: Internal bundled meta-skill module for game-audio/30-generate/sfx-generation; use within generated bootstrap node-specs when this exact contract is selected.
---

# SFX Generation Skill

> Internal sub-skill for game-audio pipelines. Status: bundled, inactive, not wired.

## Overview

Generates or registers SFX files and manifests from `sfx-spec.json`.

## Input Contract

Required: SFX spec. Optional: audio registry, audio style, existing audio files,
generation capability.

## Output Contract

Writes `.allforai/game-design/audio/sfx/sfx-generation-spec.json`,
`.allforai/game-design/audio/sfx/sfx-manifest.json`, and
`.allforai/game-design/audio/sfx/sfx-generation-report.json`.

Manifest entries must include `audio_id`, `event_ref`, `file_prefix`, `path`,
`duration_ms`, `loudness`, `format`, `state`, `variants`, and `validation`.

Allowed states: `prompt_ready`, `generated`, `registered`, `approved`,
`needs_revision`, `automation_limited`.

Downstream consumers: `game-audio/audio-loudness-qa`, runtime audio import,
`game-ui/ui-mockup-generation`, `sprite-vfx-generation`,
`particle-system`, `trail-generation`, and combat/event playback.

## Invocation Contract

```json
{"skill":"game-audio/sfx-generation","mode":"spec_generate_validate","input_paths":{"sfx_spec":".allforai/game-design/audio/sfx-spec.json","audio_registry":".allforai/game-design/audio/audio-registry.json"},"output_root":".allforai/game-design/audio"}
```

Supported modes: `spec_only`, `spec_generate_validate`, `validate_existing`,
`register_existing`.

## Automatic Validation

Check file paths, duration, loudness target, clipping, silence, loop flags,
event timing, variants, and downstream runtime feedback.

If loudness QA fails, repair audio generation or normalization metadata. If an
event mapping is wrong, repair `sfx-spec` instead of regenerating audio.

Root causes for failed outputs must be classified as `sfx_prompt`,
`sfx_generation`, `sfx_spec`, `audio_registry`, `loudness_qa`, or
`runtime_import`. Do not mark an SFX as `approved` until loudness QA has passed
or explicitly returned `COMPLETED_WITH_LIMITS`.

## Completion Conditions

Return `COMPLETED` when generated/registered audio and reports validate. Return
`COMPLETED_WITH_LIMITS` for prompt-only output.
