# Frame Animation Spec Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

This sub-skill defines frame-sequence animation contracts for pixel art,
non-rigged sprites, simple effects, UI mascots, and small characters.

## Input Contract

Required: target assets with `asset_id`, animation intent or gameplay state, and
art style. Optional: `motion-design.json`, `asset-registry.json`,
`art-style-guide.json`, requested FPS/frame counts.

If a project requires skeletal animation instead, return `NOT_APPLICABLE`.

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

Return `COMPLETED` when specs and report validate. Return
`COMPLETED_WITH_LIMITS` when reduced frame counts are used as fallback.
