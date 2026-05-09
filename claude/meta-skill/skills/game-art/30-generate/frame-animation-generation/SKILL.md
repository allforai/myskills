# Frame Animation Generation Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Generates or registers frame-animation sheets from `frame-animation-spec.json`,
including frame metadata, anchors, previews, and repair loops.

## Input Contract

Required: `.allforai/game-design/systems/frame-animation-spec.json`. Optional:
`asset-registry.json`, `art-style-guide.json`, `image-generation-contract`,
existing sprite sheets.

## Output Contract

Writes:
- `.allforai/game-design/art/animations/frame-animation-generation-spec.json`
- `.allforai/game-design/art/animations/frame-animation-manifest.json`
- `.allforai/game-design/art/animations/frame-animation-report.json`
- generated sheets/previews when enabled.

Manifest entries must include `asset_id`, `animation_id`, `file_prefix`, `fps`,
`frame_count`, `frame_size`, `anchor`, `event_frames`, `sheet_path`,
`metadata_path`, `preview_path`, `state`, `consumers`, and `validation`.

Allowed states: `spec_ready`, `generated`, `preview_ready`, `approved`,
`needs_revision`, `automation_limited`.

Downstream consumers include runtime import, combat event timing, UI mascots,
VFX animation-event bindings, and art-preview QA.

Image requests must follow `image-generation-contract` with
`generation_profile.task_type=frame_animation` and
`prompt_template=frame_animation_prompt`. Use a model profile suited to exact
frame grids, anchor consistency, and multi-frame consistency. If that profile is
unavailable, produce metadata/spec-only fallback instead of pretending the sheet
is final.

## Invocation Contract

```json
{
  "skill": "game-art/frame-animation-generation",
  "mode": "spec_generate_validate",
  "input_paths": {
    "frame_animation_spec": ".allforai/game-design/systems/frame-animation-spec.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "image_generation_contract": "${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/image-generation-contract/SKILL.md"
  },
  "output_root": ".allforai/game-design"
}
```

Supported modes: `spec_only`, `spec_generate_validate`, `validate_existing`.

## Automatic Validation

Check frame count, order, crop, anchor consistency, loop closure, event frame
visibility, preview readability, style consistency, and runtime import feedback.

If runtime import or animation-event FX reports bad frame order, anchor drift,
wrong event frame, crop, or style drift, repair frame metadata first when image
content is valid; regenerate via `image-generation-contract` only for sheet image
defects.

## Completion Conditions

Return `COMPLETED` when generated sheets, metadata, previews, and reports
validate. Return `COMPLETED_WITH_LIMITS` for reduced frame fallback.
