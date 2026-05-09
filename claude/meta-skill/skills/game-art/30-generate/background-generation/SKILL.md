# Background Generation Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Generates or registers backgrounds, scene plates, parallax layers, menu
backgrounds, and environment backdrops without replacing tilesets or props.

## Input Contract

Required: background target with `asset_id`, purpose, view/camera, style, and
output path. Optional: `asset-registry.json`, `visual-style-tokens.json`,
`image-generation-contract`, level context.

## Output Contract

Writes:
- `.allforai/game-design/art/backgrounds/background-generation-spec.json`
- `.allforai/game-design/art/backgrounds/background-manifest.json`
- `.allforai/game-design/art/backgrounds/background-report.json`
- generated images under `.allforai/game-design/art/backgrounds/` when enabled.

Manifest entries must include `asset_id`, `file_prefix`, `purpose`,
`presentation_layer`, `camera_or_view`, `dimensions`, `parallax_layer`,
`image_request_id`, `path`, `state`, `consumers`, and `validation`.

Allowed states: `spec_ready`, `generated`, `preview_ready`, `approved`,
`needs_revision`, `automation_limited`.

Downstream consumers include level previews, menu screens, UI mockups, runtime
import checks, and art-preview QA.

Image requests must follow `image-generation-contract` with
`generation_profile.task_type=background` and
`prompt_template=background_prompt`. Use a model profile suited to scene
composition, camera/view control, and style lock.

## Invocation Contract

```json
{
  "skill": "game-art/background-generation",
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

Check output path, style consistency, camera/view, parallax layer order,
non-overlap with UI-critical space, no text artifacts, and downstream feedback
from level/UI previews.

If level or UI QA reports `STYLE_DRIFT`, `WRONG_VIEW`, `LOW_READABILITY`,
`CROPPED_SUBJECT`, or `TEXT_ARTIFACT`, route the defect through
`image-generation-contract` and regenerate only the affected request when root
cause is image generation or prompt contract.

## Completion Conditions

Return `COMPLETED` when manifest/report validate and generated images pass
available visual checks. Return `COMPLETED_WITH_LIMITS` for spec-only fallback.
