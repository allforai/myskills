---
name: game-art-30-generate-expression-set-generation
description: Internal bundled meta-skill module for game-art/30-generate/expression-set-generation; use within generated bootstrap node-specs when this exact contract is selected.
---

# Expression Set Generation Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Generates character expression sets for dialogue portraits, UI reactions, NPC
states, and cutscene thumbnails.

## Input Contract

Required: character id, base portrait/reference, expression list, style, output
path. Optional: `portrait-generation`, narrative tone, `image-generation-contract`.

## Output Contract

Writes:
- `.allforai/game-design/art/expressions/expression-set-spec.json`
- `.allforai/game-design/art/expressions/expression-set-manifest.json`
- `.allforai/game-design/art/expressions/expression-set-report.json`
- generated expression images when enabled.

Manifest entries must include `character_id`, `expression_id`, `emotion`,
`dialogue_state`, `file_prefix`, `source_portrait_ref`, `image_request_id`,
`path`, `state`, `consumers`, and `validation`.

Allowed states: `spec_ready`, `generated`, `approved`, `needs_revision`,
`automation_limited`.

Downstream consumers include dialogue generation, portrait generation,
narrative QA, UI character panels, and localization screenshots.

Image requests must follow `image-generation-contract` with
`generation_profile.task_type=expression_set` and
`prompt_template=expression_set_prompt`. Use a model profile suited to identity
consistency, expression distinction, crop consistency, and style lock.

## Invocation Contract

```json
{
  "skill": "game-art/expression-set-generation",
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

Check identity consistency, expression distinction, crop, style, no text,
variant naming, narrative/dialogue coverage, and downstream feedback.

If downstream dialogue or UI QA reports emotion mismatch, identity drift, crop,
or style drift, route image defects through `image-generation-contract`; route
speaker/emotion mapping defects to dialogue spec.

## Completion Conditions

Return `COMPLETED` when required expressions validate. Return
`COMPLETED_WITH_LIMITS` when placeholder expressions are used.
