# SFX Spec Skill

> Internal sub-skill for game-audio pipelines. Status: bundled, inactive, not wired.

## Overview

Defines sound effects for gameplay, UI, VFX, rewards, errors, impacts, movement,
and feedback events.

## Input Contract

Required: audio registry and event context. Optional: audio style, VFX spec, UI
component states, combat spec.

## Output Contract

Writes `.allforai/game-design/audio/sfx-spec.json` and
`.allforai/game-design/audio/sfx-spec-report.json`.

SFX entries must include `audio_id`, `event_ref`, `semantic`, `duration_ms`,
`timing_offset_ms`, `intensity`, `variants`, `loudness_target`, `loop`, and
`fallback`.

Each entry must also include `style_ref`, `consumer_refs`, `mix_priority`,
`state`, and `qa_requirements`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_audio_registry`, `blocked_by_event_spec`, `blocked_by_audio_style`.

Downstream consumers: `game-audio/sfx-generation`,
`game-audio/audio-loudness-qa`, `sprite-vfx-generation`, `particle-system`,
`trail-generation`, `game-ui/ui-mockup-generation`, combat systems, and runtime
audio import.

## Invocation Contract

```json
{"skill":"game-audio/sfx-spec","mode":"spec_validate","input_paths":{"audio_registry":".allforai/game-design/audio/audio-registry.json","audio_style":".allforai/game-design/audio/audio-style-design.json","vfx_spec":".allforai/game-design/art/vfx/vfx-spec.json"},"output_root":".allforai/game-design/audio"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check event coverage, timing, duration, intensity, variants, loop flags,
loudness targets, UI/gameplay distinction, and fallback sound class.

If VFX or UI specs reference missing SFX, return `UPSTREAM_DEFECT` unless a
placeholder SFX prompt is generated and marked `COMPLETED_WITH_LIMITS`.

Repair routing: missing `audio_id` repairs `audio-registry`; missing event
semantics repair the owning UI/VFX/combat spec; bad loudness or duration targets
repair here; bad generated files route to `sfx-generation` and
`audio-loudness-qa`.

## Completion Conditions

Return `COMPLETED` when SFX spec validates. Return `COMPLETED_WITH_LIMITS` when
placeholder prompts replace missing final audio.
