# Animation Event FX Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill binds small VFX to animation timeline events such as footstep
dust, landing impact, weapon spark, cast glow, hit flash, breath puff, cloth
snap, and attack contact cues. It is called by `vfx-generation` when a VFX must
sync to skeletal or frame-animation events.

## Scope

In scope:
- animation-event inventory,
- VFX binding to animation ID, pose, frame, or normalized time,
- branch selection for particle, sprite, trail, decal, light pulse, or hybrid
  child effects,
- timing validation against animation timelines,
- preview and repair instructions.

Out of scope:
- creating the primary animation,
- full VFX semantics outside animation context,
- engine-specific event wiring code,
- human animation review.

## Input Contract

| Input | Required fields | Missing behavior |
|---|---|---|
| Animation event FX request | `vfx_id`, `file_prefix`, `animation_id`, `event`, `time`, `implementation_mode` | Return `UPSTREAM_DEFECT`. |

Optional inputs: `skeletal-animation-plan.json`, `motion-design.json`,
`vfx-spec.json`, `art-style-guide.json`, and existing animation previews.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/art/vfx/animation-events/animation-event-fx-spec.json` | yes | Animation event bindings and child VFX branch specs. | vfx-generation, skeletal-animation, runtime import, QA. |
| `.allforai/game-design/art/vfx/animation-events/animation-event-fx-manifest.json` | yes | Bound effects, paths, timing, previews, states. | vfx-generation and animation import. |
| `.allforai/game-design/art/vfx/animation-events/animation-event-fx-report.json` | yes | Validation and repair results. | diagnostics and QA. |

## Invocation Contract

```json
{
  "skill": "game-art/animation-event-fx",
  "mode": "spec_generate_validate",
  "input_paths": {
    "vfx_spec": ".allforai/game-design/art/vfx/vfx-spec.json",
    "skeletal_animation": ".allforai/game-design/systems/skeletal-animation-plan.json",
    "motion_design": ".allforai/game-design/systems/motion-design.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json"
  },
  "generation": {
    "preview_renderer_available": true,
    "vision_validation_available": true,
    "max_repair_attempts": 3
  },
  "output_root": ".allforai/game-design"
}
```

Supported modes: `spec_only`, `spec_generate_validate`, `validate_existing`,
`register_existing`.

## Automatic Validation

Run deterministic checks:
1. Every event references an existing or planned `animation_id`.
2. Event time is inside animation duration.
3. Contact/hit FX align with contact or impact pose.
4. Footstep/landing FX align with ground contact.
5. Child implementation modes are valid VFX branches.
6. File prefixes are stable and start with the parent VFX prefix.
7. Missing animation timelines are reported as `UPSTREAM_DEFECT` or
   `COMPLETED_WITH_LIMITS` with timing placeholders.

Run visual validation when animation previews exist:
1. FX appears at the correct frame or pose.
2. FX scale matches the character or object.
3. FX does not hide the pose that triggered it.
4. Repeated events do not create distracting clutter.

Repair timing or branch specs up to 3 times; otherwise emit a placeholder event
binding with an automation-limited state.

## Completion Conditions

Return `COMPLETED` only when event bindings, manifest, report, and available
previews validate. Return `COMPLETED_WITH_LIMITS` when animation previews are
unavailable but event timing placeholders are valid.
