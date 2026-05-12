---
name: game-art-30-generate-prop-generation
description: Internal bundled meta-skill module for game-art/30-generate/prop-generation; use within generated bootstrap node-specs when this exact contract is selected.
---

# Prop Generation Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Generates or registers reusable props such as chests, rocks, signs, barrels,
doors, decorations, pickups, obstacles, and simple interactables.

## Input Contract

Required: prop assets with `asset_id`, name, gameplay role, scale, style, and
output path. Optional: `asset-registry.json`, `visual-style-tokens.json`,
`tileset-spec.json`, `image-generation-contract`.

## Output Contract

Writes:
- `.allforai/game-design/art/props/prop-generation-spec.json`
- `.allforai/game-design/art/props/prop-manifest.json`
- `.allforai/game-design/art/props/prop-report.json`
- generated prop images or placeholder refs.

Manifest entries must include `asset_id`, `file_prefix`, `prop_kind`,
`gameplay_role`, `scale_class`, `collision_hint`, `anchor`, `variants`,
`image_request_id`, `path`, `state`, `consumers`, and `validation`.

Allowed states: `spec_ready`, `generated`, `approved`, `needs_revision`,
`automation_limited`, `not_applicable`.

Downstream consumers include level blockouts, runtime import checks, inventory
or interaction UI, and art-preview QA.

Image requests must follow `image-generation-contract` with
`generation_profile.task_type=prop` and `prompt_template=prop_prompt`. Use a
model profile suited to isolated object output, alpha/background control, and
scale readability.

## Invocation Contract

```json
{
  "skill": "game-art/prop-generation",
  "mode": "spec_generate_validate",
  "input_paths": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "style_tokens": ".allforai/game-design/art/visual-style-tokens.json",
    "tileset_spec": ".allforai/game-design/art/tilesets/tileset-spec.json",
    "image_generation_contract": "${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/image-generation-contract/SKILL.md"
  },
  "output_root": ".allforai/game-design"
}
```

Supported modes: `spec_only`, `spec_generate_validate`, `validate_existing`.

## Automatic Validation

Check naming, scale, collision/readability metadata, alpha/background policy,
style consistency, no text/crop, and downstream level/runtime feedback.

If level placement or runtime import reports `WRONG_SCALE`, `BAD_ALPHA`,
`CROPPED_SUBJECT`, `STYLE_DRIFT`, or missing collision/readability metadata,
classify root cause. Regenerate via `image-generation-contract` only for image
or prompt defects; otherwise repair prop metadata.

## Completion Conditions

Return `COMPLETED` when specs, manifest, report, and generated assets validate.
Return `COMPLETED_WITH_LIMITS` for placeholders.
