---
name: game-art-20-spec-animation-state-machine-spec
description: Internal bundled meta-skill module for game-art/20-spec/animation-state-machine-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Animation State Machine Spec Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Defines runtime animation states, transitions, priorities, interrupt rules,
event frames, fallback states, and asset references for 2D characters, props,
UI elements, and VFX-driven animation.

This skill turns motion intent and generated animation assets into a contract
that gameplay code can import without guessing names or transition behavior.

## Input Contract

Required: 2D animation production plan, motion design, and target animated
assets.

Optional: frame animation spec, skeletal animation manifests, frame animation
manifests, character layer sheet, combat spec, UI component states, engine
export profile, 2D layering spec, and runtime input/action list.

## Output Contract

Writes:

- `.allforai/game-design/art/animation/animation-state-machine-spec.json`
- `.allforai/game-design/art/animation/animation-state-machine-report.json`

State machine entries must include `machine_id`, `asset_id`, `runtime_owner`,
`default_state`, `states`, `transitions`, `parameters`, `event_bindings`,
`priority_rules`, `interrupt_rules`, `fallback_state`, `asset_refs`,
`export_profile_ref`, `qa_requirements`, `state`, and `consumer_refs`.

Each state must include `state_id`, `animation_ref`, `loop`, `speed`,
`blend_or_cut`, `min_duration_ms`, `exit_conditions`, `event_frames`,
`hitbox_refs`, `vfx_refs`, `sfx_refs`, and `ui_feedback_refs`.

Transitions must include `from`, `to`, `condition`, `priority`,
`interrupt_policy`, `transition_style`, `exit_time`, `cooldown_ms`,
`preserve_facing`, and `fallback_transition`.

Allowed machine states: `draft`, `validated`, `needs_revision`,
`blocked_by_motion_design`, `blocked_by_animation_asset`,
`blocked_by_runtime_profile`.

Downstream consumers: runtime implementation, `engine-export-profile`,
`2d-layering-spec`, `runtime-import-check`, `animation-event-fx`, `game-audio/sfx-spec`,
`game-ui/component-state-spec`, combat systems, level playability QA, and
playtest QA.

Minimum state sets:

| Asset role | Required states |
|---|---|
| player platformer | `idle`, `move`, `jump`, `fall`, `land`, `action`, `hit`, `disabled` |
| top-down player | `idle_{dir}`, `move_{dir}`, `action_{dir}`, `hit`, `disabled` |
| enemy | `idle`, `move_or_patrol`, `telegraph`, `attack`, `hit`, `defeated` |
| interactable prop | `idle`, `highlight`, `activate`, `cooldown_or_opened` |
| UI animated component | `default`, `hover_or_focus`, `press`, `disabled`, `success_or_error` |

## Invocation Contract

```json
{
  "skill": "game-art/animation-state-machine-spec",
  "mode": "spec_validate",
  "input_paths": {
    "animation_plan": ".allforai/game-design/art/animation/2d-animation-production-plan.json",
    "motion_design": ".allforai/game-design/systems/motion-design.json",
    "engine_export_profile": ".allforai/game-design/art/export/engine-export-profile.json"
  },
  "output_root": ".allforai/game-design/art/animation"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that each machine has a default state, no unreachable required state, no
dead transition, stable animation refs, and explicit fallback behavior. Player
characters must include idle, locomotion, damage/fail, and action feedback
states when the gameplay loop needs them. Attack, cast, interact, and hit states
must declare event frames when they trigger gameplay, VFX, SFX, or UI feedback.

Transitions must define whether they cut, blend, queue, or interrupt. Priority
rules must prevent low-priority loops from overriding damage, death, cutscene,
or UI-blocking states. Animation refs must point to generated or registered
manifests and cannot be display names.

State progression gates:

```text
draft
-> validated                    states, transitions, events, fallbacks, refs all resolve
-> needs_revision               unreachable states, invalid priorities, unsafe interrupts
-> blocked_by_motion_design     required action semantics are missing
-> blocked_by_animation_asset   animation refs do not exist or failed QA
-> blocked_by_runtime_profile   runtime cannot represent transitions/events
```

Event frame validation:

- Gameplay-impacting events must be tied to frame index, normalized time, or
  bone/part event.
- Hit/damage events must occur after readable telegraph/startup.
- SFX/VFX refs must use stable event IDs.
- Landing, pickup, open, equip, and cast events must have fallback behavior when
  animation is reduced.

Repair routing: missing gameplay events return to combat/core-loop specs;
missing animation assets return to `frame-animation-generation` or
`skeletal-animation`; invalid state topology repairs here; export naming or
format failures route to `engine-export-profile`; style/readability failures
route to `2d-style-consistency-qa` and then the relevant producer.

## Completion Conditions

Return `COMPLETED` when every required runtime animation state has an animation
ref, transition rule, event binding, fallback, and export profile reference.
Return `COMPLETED_WITH_LIMITS` when optional states intentionally fall back to
idle or pose swaps. Return `FAILED_VALIDATION` when required states are
unreachable or unsafe for runtime import.
