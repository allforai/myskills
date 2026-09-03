---
name: game-art-20-spec-visual-style-tokens
description: Convert art direction into shared visual tokens (palette, line, shape, material, camera, lighting, typography feel, icon language, effect intensity, motion tone); writes art/visual-style-tokens.json. Sole token author on game projects.
---

# Visual Style Tokens Skill

> Internal sub-skill for game art pipelines. Status: bundled.

## Overview

This sub-skill converts art direction into shared visual tokens used by game art
and game UI generators. It is the source for palette, line, shape, material,
camera, lighting, typography feel, icon language, effect intensity, and motion
tone.

**It is the only token author on a game project.** `game-ui` consumes these
tokens rather than defining its own, and the `ui-design` capability's
`tokens.json` must be derived from `visual-style-tokens.json` with a
`source_token` reference per value, never invented in parallel. On a non-game
project this skill does not run and `ui-design/tokens.json` is the authority.

## Input Contract

Required: `.allforai/game-design/art-style-guide.json` or equivalent art
direction with style, dimension, tone, and target view. Optional:
`concept-contract.json`, `asset-registry.json`, `ui-registry.json`.

Missing required art direction returns `UPSTREAM_DEFECT`; weak style details
produce conservative readable defaults and `COMPLETED_WITH_WARNINGS`.

## Output Contract

Writes:
- `.allforai/game-design/art/visual-style-tokens.json`
- `.allforai/game-design/art/visual-style-tokens-report.json`

Tokens must include color, line, shape, material, camera/view, lighting,
typography mood, UI compatibility, VFX intensity, and image-generation prompt
constraints.

## Invocation Contract

```json
{
  "skill": "game-art/visual-style-tokens",
  "mode": "build_validate",
  "input_paths": {
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "concept_contract": ".allforai/concept-contract.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "ui_registry": ".allforai/game-design/ui/ui-registry.json"
  },
  "output_root": ".allforai/game-design/art"
}
```

Supported modes: `build_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that required token groups exist, color values are valid, style rules are
not contradictory, UI and art tokens share compatible palette/shape language,
and image-generation prompt constraints include both positive and negative
style guidance.

## Completion Conditions

Return `COMPLETED` when token and report files validate. Return
`COMPLETED_WITH_WARNINGS` when optional style details are inferred.
