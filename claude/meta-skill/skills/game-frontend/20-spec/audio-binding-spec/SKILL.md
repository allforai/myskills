---
name: game-frontend-20-spec-audio-binding-spec
description: Internal bundled meta-skill module for game-frontend/20-spec/audio-binding-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Audio Binding Spec Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Maps game-audio cue manifests into frontend audio loader keys, scene triggers,
UI triggers, animation/VFX sync points, volume groups, fallback policy, and
runtime audio probes.

## Input Contract

Required: frontend runtime profile and audio cue/spec manifest.

Optional: game design doc, scene composition spec, HUD/UI binding, animation/VFX
binding, audio QA report, asset import bindings, existing audio code, and
platform autoplay constraints.

## Output Contract

Writes:

- `.allforai/game-frontend/bindings/audio-binding-spec.json`
- `.allforai/game-frontend/bindings/audio-binding-report.json`

Bindings must include `cue_id`, `audio_asset_ref`, `frontend_key`,
`trigger_refs`, `scene_refs`, `volume_bus`, `loop_rule`, `sync_rule`,
`fallback_policy`, `autoplay_policy`, `validation_probe`,
`runtime_effect_assertions`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_missing_audio`, `blocked_by_platform_policy`,
`blocked_by_runtime_profile`.

## Invocation Contract

```json
{
  "skill": "game-frontend/audio-binding-spec",
  "mode": "spec_validate",
  "input_paths": {
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "audio_manifest": ".allforai/game-design/audio/audio-manifest.json",
    "scene_composition": ".allforai/game-frontend/bindings/scene-composition-spec.json"
  },
  "output_root": ".allforai/game-frontend/bindings"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that required cues have files, frontend keys,
trigger events, platform-safe playback policy, and a runtime probe. Browser
autoplay limits must be explicit; do not assume audio can play before user
gesture.

Audio binding must define effect-level assertions, not only structure checks.
Required cues need proof that the production runtime fetches/decodes the real
file, stores a non-null `AudioBuffer` or engine-equivalent decoded asset, and
can trigger the cue from the production scene after the platform unlock policy
is satisfied. A mock that only observes `playSFX()` or `playBGM()` being called
is insufficient for launch, production, or unattended goals.

For Canvas2D/Web Audio projects, require a runtime probe that records
`AudioContext.state`, decoded buffer keys, failed fetch/decode errors, user
gesture unlock state, and the scene/module path that called `loadBGM`,
`loadSFX`, or equivalent preload functions. A constructed `AudioManager` with
no preload/load calls is a blocking integration gap.

For launch, launch-prep, production, or unattended run goals, declared fallback
audio is not enough for required cues. Silent files, stubs, prompt-only audio,
missing paths, or fallback-only cues must route to `game-audio` and block
frontend audio binding.

Repair routing: missing audio routes to `game-audio`; missing trigger routes to
scene/HUD/animation binding; platform conflicts route to frontend runtime
detection.

## Completion Conditions

Return `COMPLETED` when required cues can be loaded, decoded, and triggered
with real runtime audio evidence. Return `FAILED_VALIDATION` when required
audio has no file, trigger, runtime validation path, decoded buffer proof,
production preload call, or only fallback/stub/mock coverage.
