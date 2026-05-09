# Music Cue Spec Skill

> Internal sub-skill for game-audio pipelines. Status: bundled, inactive, not wired.

## Overview

Defines music cues, loops, stems, transitions, intensity states, menu/gameplay
music, victory/failure cues, and ambience relationships.

## Input Contract

Required: audio style and game state flow. Optional: level flow, narrative tone,
progression spec.

## Output Contract

Writes `.allforai/game-design/audio/music-cue-spec.json` and
`.allforai/game-design/audio/music-cue-report.json`.

Cue entries must include `cue_id`, `game_state`, `entry_condition`,
`exit_condition`, `loop`, `duration_target`, `intensity`, `transition`,
`stem_refs`, and `fallback`.

Each cue must also include `style_ref`, `consumer_refs`, `event_refs`,
`mix_priority`, `silence_policy`, and `state`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_audio_style`, `blocked_by_level_flow`, `blocked_by_runtime_state`.

Downstream consumers: `game-audio/music-prompt-generation`,
`game-audio/audio-loudness-qa`, `game-level/level-flow-design`,
`game-ui/ui-mockup-generation`, and runtime audio import.

## Invocation Contract

```json
{"skill":"game-audio/music-cue-spec","mode":"spec_validate","input_paths":{"audio_style":".allforai/game-design/audio/audio-style-design.json","level_flow":".allforai/game-design/levels/level-flow-design.json","game_design_doc":".allforai/game-design/game-design-doc.json"},"output_root":".allforai/game-design/audio"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check cue coverage, loop points, transitions, stem needs, intensity mapping,
duration targets, and fallback ambience.

If level or UI flow references a missing cue, repair cue mapping before music
generation. Do not generate orphan music that is not reachable from game state.

Repair routing: missing style or instrumentation returns to
`audio-style-design`; missing game states return to `level-flow-design` or core
loop design; invalid transition logic returns here; generated loop defects route
to `music-prompt-generation` and then `audio-loudness-qa`.

## Completion Conditions

Return `COMPLETED` when cue spec validates. Return `COMPLETED_WITH_LIMITS` for
prompt-only or placeholder music.
