---
name: game-art-20-spec-frame-animation-spec
description: Define frame-sequence animation contracts for pixel art, non-rigged sprites, simple effects, UI mascots, and small characters from motion-design.json; writes systems/frame-animation-spec.json.
---

# Frame Animation Spec Skill

> Internal sub-skill for game art pipelines. Status: bundled.

## Overview

This sub-skill defines frame-sequence animation contracts for pixel art,
non-rigged sprites, simple effects, UI mascots, and small characters.

## Input Contract

Required: target assets with `asset_id`, animation intent or gameplay state, and
art style. Optional: `motion-design.json`, `asset-registry.json`,
`art-style-guide.json`, requested FPS/frame counts.

This is the default 2D character animation path. If an upstream config still
names skeletal, DragonBones, or Spine production, remap to frame animation and
continue. Do not return `NOT_APPLICABLE` just because a rig field is stale.

## Output Contract

Writes:
- `.allforai/game-design/systems/frame-animation-spec.json`
- `.allforai/game-design/systems/frame-animation-spec-report.json`

Each animation defines animation id, loop, FPS, frame count, event frames,
anchor, hitbox/collision expectations, output naming, preview requirements, and
acceptance rules.

## Invocation Contract

```json
{
  "skill": "game-art/frame-animation-spec",
  "mode": "spec_validate",
  "input_paths": {
    "motion_design": ".allforai/game-design/systems/motion-design.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json"
  },
  "output_root": ".allforai/game-design"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check frame count, FPS, event timing, loop closure, anchor consistency, naming,
fallback frames, and whether required animations from motion design are covered.

## Completion Conditions

Return `COMPLETED` when specs and report validate and every required production
animation has a downstream generation/QA route. Return `COMPLETED_WITH_LIMITS`
only for planning/spec phases. For launch, launch-prep, production, or
unattended run goals, reduced frame-count fallback for required animation is a
blocker unless explicitly accepted by project production policy.
