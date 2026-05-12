---
name: game-art-10-design-art-concept-validation
description: Generate and validate a human-readable HTML gate that checks art concept alignment against product/game concept, gameplay readability, audience fit, visual style tokens, and asset family direction before bulk game art production.
---

# Art Concept Validation Skill

> Internal sub-skill for game-art pipelines. Status: bundled,
> bootstrap-wired through art-concept node injection.

## Overview

Creates the art concept approval gate between product/game concept and bulk
asset generation. It validates whether the selected art direction can carry the
game concept, audience promise, gameplay readability, UI/world consistency, and
human visual preferences before asset registry, source strategy, and art-gen
nodes proceed.

This is not final art QA. It is a concept-level gate that prevents producing
many technically correct assets in the wrong visual direction.

## Input Contract

Required: product/game concept, game design doc or art input handoff, art
direction input contract, art pipeline config, visual style guide or visual
style tokens, and human preference notes when available.

Optional: concept-contract, sample/reference images, negative references,
scenario template, target runtime constraints, UI direction, narrative tone,
accessibility requirements, and early thumbnail/mockup previews.

## Output Contract

Writes:

- `.allforai/game-design/art/art-concept-validation.html`
- `.allforai/game-design/art/art-concept-validation.json`
- `.allforai/game-design/art/art-concept-validation-report.json`

The JSON must include `validation_id`, `source_refs`,
`product_concept_alignment`, `gameplay_readability`, `audience_fit`,
`visual_pillars`, `style_token_consistency`, `asset_family_preview_plan`,
`ui_world_consistency`, `vfx_motion_consistency`, `runtime_feasibility`,
`accessibility_risks`, `human_preference_decisions`, `risk_flags`,
`approval_summary`, `state`, and `consumer_refs`.

The HTML must be human-readable and written in Chinese. It must organize
related findings as collapsible or tree-like sections so the review page does
not become visually oppressive.

Allowed states: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_concept`, `blocked_by_missing_art_direction`,
`blocked_by_preference_conflict`, `failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-art/art-concept-validation",
  "mode": "generate_validate",
  "input_paths": {
    "art_direction": ".allforai/game-design/art/art-direction-input-contract.json",
    "art_pipeline_config": ".allforai/game-design/art-pipeline-config.json",
    "art_input_handoff": ".allforai/game-design/design/art-input-handoff.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "style_tokens": ".allforai/game-design/art/visual-style-tokens.json",
    "human_preferences": ".allforai/game-design/art/human-preferences.json"
  },
  "output_root": ".allforai/game-design/art"
}
```

Supported modes: `generate_validate`, `validate_existing`, `repair_existing`.

## HTML Review Requirements

The HTML page must show:

- product/game concept summary and the art promise in one first-screen section;
- visual pillars and how each maps to gameplay, audience, and emotion;
- asset family tree: characters, environments, tiles, UI/icons, VFX, animation;
- style-token summary: palette, shape, line, lighting, material, typography,
  motion, VFX intensity;
- human preference decisions: accepted, rejected, unresolved, and why;
- risk flags: readability, scope, runtime, accessibility, style conflict,
  generation risk, and downstream import risk;
- approval summary with explicit `pass`, `pass_with_warnings`, or
  `needs_revision` recommendation.

Do not hide blockers in prose. Every blocker must have `owner_skill`,
`repair_target`, and `blocks_art_gen: true`.

## Automatic Validation

Check that:

- art direction cites product/game concept, gameplay, target audience, runtime,
  and human preference sources;
- every visual pillar maps to at least one gameplay or audience reason;
- style tokens are internally consistent and compatible with game UI;
- asset family plan covers every active art-gen family from
  `art-pipeline-config.active_nodes`;
- UI and world art share visual language but keep readability boundaries;
- VFX/motion intensity respects gameplay readability and accessibility;
- runtime constraints do not contradict visual complexity;
- unresolved preference conflicts are surfaced before asset generation.

If product concept or art direction is missing, return the relevant blocked
state. Do not infer the entire art concept from conversation memory.

Repair routing: missing product/game context routes to game-design concept
nodes; missing art input routes to `art-direction-input-contract`; inconsistent
style routes to `visual-style-tokens`; runtime feasibility gaps route to
`engine-export-profile`; asset family gaps route to `asset-registry` or the
relevant art-gen family; UI/world conflicts route to `game-ui` and
`2d-style-consistency-qa`.

## Completion Conditions

Return `COMPLETED` only when the HTML and JSON exist and the JSON state is
`passed` or `passed_with_warnings`. Return `FAILED_VALIDATION` when the concept
does not justify safe entry into bulk art production.
