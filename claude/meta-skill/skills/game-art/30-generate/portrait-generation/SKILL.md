# Portrait Generation Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Generates or registers character portraits, busts, dialogue portraits, emotion
variants, speaker icons, and profile images.

## Input Contract

Required: character asset id, identity, role, style, target crop, required
expressions, and output path. Optional: `asset-registry.json`,
`character-layer-sheet`, `expression-set-generation`, `image-generation-contract`.

## Output Contract

Writes:
- `.allforai/game-design/art/portraits/portrait-spec.json`
- `.allforai/game-design/art/portraits/portrait-manifest.json`
- `.allforai/game-design/art/portraits/portrait-report.json`
- generated portrait images when enabled.

Manifest entries must include `character_id`, `asset_id`, `file_prefix`,
`portrait_kind`, `crop`, `expression_id`, `emotion`, `image_request_id`, `path`,
`state`, `dialogue_refs`, `ui_refs`, and `validation`.

Allowed states: `spec_ready`, `generated`, `approved`, `needs_revision`,
`automation_limited`.

Downstream consumers include dialogue, quest UI, character selection, profile
cards, expression sets, narrative QA, and UI mockups.

Image requests must follow `image-generation-contract` with
`generation_profile.task_type=portrait` and `prompt_template=portrait_prompt`.
Use a model profile suited to identity consistency, crop control, expression
clarity, and style lock.

## Invocation Contract

```json
{
  "skill": "game-art/portrait-generation",
  "mode": "spec_generate_validate",
  "input_paths": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "style_tokens": ".allforai/game-design/art/visual-style-tokens.json",
    "image_generation_contract": "${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/image-generation-contract/SKILL.md"
  },
  "output_root": ".allforai/game-design"
}
```

Supported modes: `spec_only`, `spec_generate_validate`, `validate_existing`.

## Automatic Validation

Check character identity consistency, expression coverage, crop, style, no text,
transparent/flat background policy, and narrative/dialogue consumer feedback.

If dialogue or UI QA reports `STYLE_DRIFT`, `WRONG_SCALE`, `CROPPED_SUBJECT`,
identity mismatch, or expression mismatch, route image/prompt defects through
`image-generation-contract`; route speaker or emotion mapping defects to
dialogue or expression specs.

## Completion Conditions

Return `COMPLETED` when all required variants validate. Return
`COMPLETED_WITH_LIMITS` when missing expressions use placeholders.
