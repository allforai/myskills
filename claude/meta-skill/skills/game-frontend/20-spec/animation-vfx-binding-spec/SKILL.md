---
name: game-frontend-20-spec-animation-vfx-binding-spec
description: Internal bundled meta-skill module for game-frontend/20-spec/animation-vfx-binding-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Animation VFX Binding Spec Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Maps animation state machines, clips, sprite sheets, skeletal timelines, VFX,
particles, and event bindings into frontend runtime events and validation
probes.

## Input Contract

Required: frontend runtime profile, asset import bindings, scene composition
spec, and animation or VFX manifests.

Optional: combat/mechanics specs, motion design, animation state machine spec,
runtime import report, audio cue specs, and existing animation code.

## Output Contract

Writes:

- `.allforai/game-frontend/bindings/animation-vfx-binding-spec.json`
- `.allforai/game-frontend/bindings/animation-vfx-binding-report.json`

Bindings must include `binding_id`, `entity_ref`, `state_refs`, `clip_refs`,
`frame_or_bone_refs`, `event_triggers`, `vfx_refs`, `audio_refs`,
`fallback_visual`, `timing_constraints`, `validation_probe`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_asset_binding`, `blocked_by_animation_manifest`,
`blocked_by_vfx_manifest`.

## Invocation Contract

```json
{
  "skill": "game-frontend/animation-vfx-binding-spec",
  "mode": "spec_validate",
  "input_paths": {
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "asset_bindings": ".allforai/game-frontend/bindings/asset-import-binding-spec.json",
    "scene_composition": ".allforai/game-frontend/bindings/scene-composition-spec.json"
  },
  "output_root": ".allforai/game-frontend/bindings"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that each required entity state has an animation,
event frames are preserved, VFX timing does not hide gameplay readability, and
smoke tests can trigger at least one representative animation/VFX path.

For launch, launch-prep, production, or unattended run goals, declared fallback
visuals are not enough for required gameplay feedback. Missing clips, missing
VFX frames/configs, timing placeholders, tween-only substitutions, or
fallback-only effects must block and route to the producing animation/VFX skill.

Repair routing: missing clips route to `game-art/frame-animation-generation` or
`game-art/skeletal-animation`; missing effects route to `game-art/vfx-generation`;
runtime binding ambiguity routes to `asset-import-binding-spec`.

## Completion Conditions

Return `COMPLETED` when animation and VFX bindings can be triggered and probed
with generated or registered production assets.
Return `FAILED_VALIDATION` when required gameplay feedback has no visual state,
event trigger, validation path, or only fallback/placeholder coverage.
