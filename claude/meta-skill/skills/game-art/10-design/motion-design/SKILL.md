---
name: game-art-10-design-motion-design
description: Internal bundled meta-skill module for game-art/10-design/motion-design; use within generated bootstrap node-specs when this exact contract is selected.
---

# Motion Design Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill defines animation motion at the gameplay and readability level.
It decides what each motion communicates, which key poses are required, where
gameplay events occur, how timing should feel, and how the motion degrades when
full animation is not feasible.

It does not generate final art, frame sequences, DragonBones JSON, particle
effects, or 3D animation clips. Downstream implementation skills consume its
motion plan and convert it into skeletal animation, sprite frame animation, VFX,
UI mascot motion, audio cues, or runtime state-machine hooks.

## Scope

Use this skill when any game-art flow needs a stable animation intent and timing
contract before implementation.

In scope:
- motion intent,
- animation set selection,
- key pose planning,
- timing and curve planning,
- gameplay event frame planning,
- readability rules,
- fallback motion strategies,
- automatic validation and repair loops at the design-spec level.

Out of scope:
- final rendered animation,
- rig hierarchy,
- sprite frame generation,
- particle system generation,
- engine import files,
- human review or manual approval.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| Asset registry or asset list | `asset_id`, `name`, `type` | Return `UPSTREAM_DEFECT`; no target asset exists. |
| Gameplay role/context | role such as player, enemy, boss, NPC, prop, mascot | Infer from asset tags/name once; if unsafe, use `generic_character`. |
| Art context | dimension, style, target view or camera | Infer from art-style-guide when available; otherwise use conservative defaults. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/game-design/asset-registry.json` | `assets[].asset_id`, `file_prefix`, `type`, `state` | Use inventory or caller-provided asset list. |
| `.allforai/game-design/art-style-guide.json` | `art_overview.dimension`, `style`, visual tone | Use neutral 2D side/front-view assumptions. |
| `.allforai/game-design/game-design-doc.json` | combat loop, interaction states, progression, role fantasy | Use generic action taxonomy by gameplay role. |
| Caller animation request | requested ids, durations, events, interrupt rules | Infer baseline set from gameplay role. |
| Runtime constraints | FPS, target platform, input latency, movement speed | Use mobile-safe conservative timing. |

### Normalized input

Build this internal object before planning:

```json
{
  "schema_version": "1.0",
  "assets": [
    {
      "asset_id": "<stable id>",
      "name": "<display name>",
      "file_prefix": "<stable prefix if known>",
      "asset_type": "character | enemy | boss | npc | prop | vfx | ui_mascot | other",
      "gameplay_role": "<resolved role>",
      "target_view": "front | side | three_quarter | top_down | isometric",
      "scale_class": "small | normal | boss | ui"
    }
  ],
  "requested_animations": [],
  "runtime_constraints": {
    "fps": 24,
    "target_platform": "mobile | desktop | web | console | unknown",
    "movement_speed_px_per_sec": null
  }
}
```

## Motion Vocabulary Defaults

If no animation list is provided, infer defaults from role:

| Role | Default animations |
|---|---|
| `player` | `idle`, `walk`, `run`, `attack`, `hit`, `death`, `interact` |
| `enemy` | `idle`, `walk`, `attack`, `hit`, `death` |
| `boss` | `idle`, `walk`, `attack`, `skill`, `hit`, `death`, `stagger` |
| `npc` | `idle`, `talk`, `gesture` |
| `prop` | `idle`, `activate`, `break` |
| `ui_mascot` | `idle`, `bounce`, `celebrate`, `sad` |
| `vfx` | `start`, `loop`, `impact`, `dissipate` |

Every animation must define:
- `animation_id`,
- `gameplay_state`,
- `loop`,
- `priority`,
- `interrupt_policy`,
- `duration_ms`,
- `event_frames[]`.

## Creative Workflow

The workflow has six fixed stages.

| Stage | Purpose | Main output |
|---|---|---|
| 1. Intent | Decide what the motion communicates. | `animation_intent[]` |
| 2. Vocabulary | Select animation ids and priorities. | `animation_set[]` |
| 3. Key poses | Define readable pose beats. | `key_pose_plan[]` |
| 4. Timing | Define duration, events, curves, holds. | `timing_plan[]` |
| 5. Readability | Define automatic checks and preview expectations. | `readability_rules[]` |
| 6. Fallback | Define simplified substitute motion. | `fallback_motion[]` |

### Stage 1: Intent

Each animation starts with a semantic intent. Do not plan poses before intent is
clear.

Required fields:
- `intent`: what the player should understand,
- `emotion`: neutral, playful, heavy, aggressive, frightened, heroic, etc.,
- `readability_priority`: what must be readable first,
- `gameplay_state`: runtime state this motion represents.

Example:

```json
{
  "asset_id": "forest_guardian",
  "animation_id": "attack",
  "intent": "Telegraph a heavy attack before damage occurs.",
  "emotion": "heavy_confident",
  "readability_priority": "windup_before_contact",
  "gameplay_state": "combat_attack"
}
```

### Stage 2: Vocabulary

Select only motions needed by gameplay or UI. Avoid bloated sets.

Priority levels:
- `baseline`: always active, e.g. idle.
- `locomotion`: movement cycles.
- `combat`: attack, hit, stagger, death.
- `interaction`: talk, pickup, open, activate.
- `celebration`: win, reward, level-up.
- `system`: loading mascot, menu feedback.

Interrupt policies:
- `interruptible_anytime`,
- `locked_until_event`,
- `locked_after_contact`,
- `non_interruptible`,
- `state_controlled`.

### Stage 3: Key poses

Key poses are implementation-agnostic. A downstream skill may realize them as
bones, frames, particles, or 3D clips.

Baseline pose patterns:

| Animation | Required poses |
|---|---|
| `idle` | neutral, inhale/up, exhale/down |
| `walk` | contact, down, passing, up, opposite_contact |
| `run` | squash/contact, extension, airborne, opposite_contact |
| `attack` | neutral, anticipation, windup, contact, follow_through, recover |
| `hit` | neutral, impact, recoil, recover |
| `death` | impact, fall, settle |
| `skill` | anticipation, charge, release, impact, recover |
| `activate` | idle, anticipation, active, settle |
| `impact` | pre_hit, burst, dissipate |

Each pose must define:
- `pose_id`,
- `time_ratio`,
- `purpose`,
- `silhouette_note`,
- `required_body_focus` or equivalent visual focus.

### Stage 4: Timing

Convert poses into timing and gameplay events.

Timing rules:
- `duration_ms` must be positive.
- event times must be inside duration.
- looped animations must return to a compatible start pose.
- contact/damage events must occur after visible anticipation.
- UI feedback motion should stay short: usually 120-450 ms.
- combat attacks should reserve readable windup before contact.

Curve vocabulary:
- `sine_in_out`: organic idle, breathing, floating.
- `slow_windup_fast_contact_slow_recover`: attacks.
- `fast_impact_slow_settle`: hit reactions.
- `linear`: mechanical motion.
- `stepped`: snappy UI or pixel-like motion.
- `overshoot_settle`: celebration, bounce, reward.

### Stage 5: Readability rules

Write rules that downstream render/validation loops can check:
- contact pose differs from anticipation pose,
- damage event occurs after anticipation,
- loop end pose is compatible with start pose,
- small-size silhouette remains readable,
- important gameplay event has a distinct visual beat,
- no non-loop animation is marked looped,
- fallback motion still communicates intent.

### Stage 6: Fallback motion

Every animation must have a fallback. Fallbacks are automatic, not human-gated.

Fallback strategies:
- `three_pose`: anticipation, contact, recover.
- `two_pose`: before/after.
- `single_pulse`: scale/opacity pulse.
- `static_flash`: static pose plus flash cue.
- `skip_optional`: omit optional animation and rely on state change.

Fallback output:

```json
{
  "animation_id": "skill",
  "strategy": "three_pose",
  "reason": "Complex trail and secondary motion may fail render validation.",
  "poses": ["anticipation", "release", "recover"],
  "events_preserved": ["skill_cast", "impact"]
}
```

## Automatic Validation

## Automatic Acceptance

Run these deterministic checks:

1. Every selected asset has at least one animation.
2. Every animation has intent, key poses, timing, readability rules, and fallback.
3. Every key pose has `pose_id`, `time_ratio`, and `purpose`.
4. `time_ratio` values are between 0 and 1.
5. `duration_ms` is positive.
6. Event times are within duration.
7. Contact/damage events occur after anticipation when anticipation exists.
8. Looped animations include loop compatibility notes.
9. Fallback preserves critical gameplay events.
10. Animation IDs are unique per asset.

If checks fail, repair the motion plan up to 3 times. If it still fails, return
`FAILED_VALIDATION`.

## Output Contract

Write:

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/systems/motion-design.json` | yes | Canonical motion intent, poses, timing, events, fallbacks. | skeletal-animation, sprite-frame-animation, vfx-animation, audio-design, QA. |
| `.allforai/game-design/systems/motion-design-report.json` | yes | Acceptance verdict, failed checks, repair attempts, next actions. | caller diagnostics and QA. |

## Invocation Contract

Minimal invocation context:

```json
{
  "skill": "game-art/motion-design",
  "mode": "plan_and_validate",
  "input_paths": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json"
  },
  "asset_filter": {
    "asset_ids": [],
    "asset_types": ["character", "enemy", "boss", "npc", "prop", "vfx", "ui_mascot"]
  },
  "requested_animations": [],
  "output_root": ".allforai/game-design"
}
```

Supported modes:

| Mode | Behavior |
|---|---|
| `plan_only` | Produce motion plan without validation repair. |
| `plan_and_validate` | Produce motion plan, run checks, repair, and write verdict. |
| `validate_existing` | Validate existing `motion-design.json`. |

Return statuses:

| Status | Meaning | Caller action |
|---|---|---|
| `COMPLETED` | Motion plan passes validation. | Continue downstream. |
| `COMPLETED_WITH_WARNINGS` | Motion plan passes but uses simplified fallback for some motions. | Continue downstream with fallback notes. |
| `UPSTREAM_DEFECT` | Required asset/context is missing. | Pause caller and fix upstream input. |
| `FAILED_VALIDATION` | Motion plan could not be repaired. | Do not continue downstream. |

## Motion Design Schema

Write `.allforai/game-design/systems/motion-design.json`:

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO timestamp>",
  "source": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json"
  },
  "assets": [
    {
      "asset_id": "<asset id>",
      "file_prefix": "<file prefix>",
      "gameplay_role": "<role>",
      "animations": [
        {
          "animation_id": "attack",
          "gameplay_state": "combat_attack",
          "intent": "Telegraph a heavy attack before damage.",
          "emotion": "heavy_confident",
          "readability_priority": "windup_before_contact",
          "loop": false,
          "priority": "combat",
          "interrupt_policy": "locked_after_contact",
          "duration_ms": 720,
          "key_poses": [
            {
              "pose_id": "anticipation",
              "time_ratio": 0.25,
              "purpose": "telegraph danger",
              "silhouette_note": "weapon pulled back, body compressed",
              "required_body_focus": "weapon_arm"
            }
          ],
          "events": [
            { "event": "sfx_swing", "time_ms": 220 },
            { "event": "damage", "time_ms": 320 }
          ],
          "curve": "slow_windup_fast_contact_slow_recover",
          "readability_rules": [],
          "fallback": {
            "strategy": "three_pose",
            "reason": "<fallback reason>",
            "poses": ["anticipation", "contact", "recover"],
            "events_preserved": ["damage"]
          }
        }
      ]
    }
  ],
  "acceptance": {
    "verdict": "pass | pass_with_warnings | fail",
    "checked_at": "<ISO timestamp>",
    "passed_checks": [],
    "failed_checks": [],
    "repair_attempts": 0,
    "next_action": "<what happens next>"
  }
}
```

## Report Schema

Write `.allforai/game-design/systems/motion-design-report.json`:

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO timestamp>",
  "verdict": "pass | pass_with_warnings | fail",
  "summary": {
    "asset_count": 0,
    "animation_count": 0,
    "fallback_count": 0
  },
  "failed_checks": [],
  "warnings": [],
  "repair_log": [],
  "next_actions": []
}
```

## Downstream Usage

Downstream skills must consume motion design as follows:
- `skeletal-animation` turns `key_poses`, `events`, and `curve` into bones,
  pivots, transform timelines, and render validation.
- `sprite-frame-animation` turns `key_poses` and `duration_ms` into frame counts
  and sprite sheets.
- `vfx-animation` turns `events`, `curve`, and fallback strategy into VFX beats.
- `audio-design` uses `events[]` to place SFX cues.
- QA uses `readability_rules[]` and fallback notes for validation.

Downstream skills must not change motion intent or event timing unless they
write a new motion-design revision.

## Completion Conditions

This skill is complete only when:
- `motion-design.json` exists and is valid JSON,
- `motion-design-report.json` exists and is valid JSON,
- report verdict is `pass` or `pass_with_warnings`,
- every animation has intent, key poses, timing, readability rules, and fallback,
- every failed check has a next action.
