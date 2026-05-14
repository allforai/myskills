---
name: game-art-30-generate-motion-video-to-sprite-animation
description: Internal bundled meta-skill module for game-art/30-generate/motion-video-to-sprite-animation; use within generated bootstrap node-specs when a 2D runtime sprite animation should be produced from local video, web/reference video, AI video, 3D render capture, or engine capture.
---

# Motion Video To Sprite Animation Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Produces 2D runtime sprite animations by sourcing a short motion video, extracting
frames, normalizing them into a frame sequence/spritesheet, and validating the
actual visual output. The video is an upstream motion source, not the final
asset. Final consumers receive spritesheets, frame metadata, previews, and
engine-ready manifests.

Use this for light 2D game actions where motion continuity matters but full
skeletal production is unnecessary or too costly: mascot idles, enemy actions,
NPC gestures, UI character stingers, attack/skill windups, celebration/fail
loops, ambient props, and stylized VFX-like character motion.

Do not use this as a replacement for skeletal animation when the game requires
runtime outfit swaps, bone-driven hitboxes, strict interactive IK, or many
shared actions from the same rig.

## Input Contract

Required inputs:

| Input | Required fields | Missing behavior |
|---|---|---|
| `.allforai/game-design/art/animation/2d-animation-production-plan.json` | `asset_id`, animation method/source route, target runtime, QA requirements | Return `UPSTREAM_DEFECT`. |
| Motion request | `animation_id`, `action_id`, `source_strategy`, `duration_seconds`, `target_fps`, `looping`, `view_mode`, `frame_size`, `anchor`, `output_usage` | Return `UPSTREAM_DEFECT`. |
| Style and identity context | art style, character/object refs, palette, camera/view, forbidden drift | Return `UPSTREAM_DEFECT` when strict style or identity is required. |
| Engine export profile | spritesheet/atlas format, pivot/anchor convention, import validation command when available | Return `blocked_by_missing_runtime_profile` for runtime-ready output. |
| `2d-animation-toolchain-env` report | video source, frame extractor, image processor, atlas, preview, runtime import capabilities | Return `blocked_by_missing_toolchain` if required capabilities are absent. |

Optional inputs:

- `.allforai/game-design/systems/motion-design.json`
- `.allforai/game-design/systems/frame-animation-spec.json`
- `.allforai/game-design/systems/animation-state-machine-spec.json`
- `.allforai/game-design/art/image-generation/accepted-image-manifest.json`
- `.allforai/game-design/art/asset-acceptance-criteria.json`
- local asset library indexes and user-provided motion references
- web/marketplace search candidates with license reports
- AI video generation provider/task descriptors
- Blender, engine, DragonBones, Spine, or browser preview capture outputs

## Output Contract

Writes under `.allforai/game-design/art/animations/video-to-sprite/`:

- `motion-video-source-plan.json`
- `motion-video-source-manifest.json`
- `video-frame-extraction-report.json`
- `video-to-sprite-frame-manifest.json`
- `video-to-sprite-animation-manifest.json`
- `video-to-sprite-preview-report.json`
- `video-to-sprite-qa-report.json`
- `video-to-sprite-repair-loop-report.json` when repair is needed
- generated frame files, spritesheets/atlases, and preview video/GIF files

`video-to-sprite-animation-manifest.json` entries must include:

```json
{
  "schema_version": "1.0",
  "asset_id": "player_cat",
  "animation_id": "player_cat_run_side",
  "action_id": "run",
  "source_strategy": "local_library | user_provided_video | web_or_marketplace_search | ai_video | 3d_render_capture | engine_capture | hybrid",
  "source_manifest_ref": ".allforai/game-design/art/animations/video-to-sprite/motion-video-source-manifest.json",
  "license_report_ref": null,
  "frame_count": 12,
  "fps": 12,
  "looping": true,
  "frame_size": {"width": 128, "height": 128},
  "anchor": {"x": 0.5, "y": 0.9},
  "event_frames": [],
  "frames_dir": ".allforai/game-design/art/animations/video-to-sprite/player_cat_run_side/frames",
  "sheet_path": ".allforai/game-design/art/animations/video-to-sprite/player_cat_run_side/player_cat_run_side.png",
  "metadata_path": ".allforai/game-design/art/animations/video-to-sprite/player_cat_run_side/player_cat_run_side.json",
  "preview_path": ".allforai/game-design/art/animations/video-to-sprite/player_cat_run_side/player_cat_run_side_preview.mp4",
  "accepted_image_manifest_ref": ".allforai/game-design/art/image-generation/accepted-image-manifest.json",
  "state": "generated | preview_ready | qa_passed | needs_revision | blocked",
  "validation": {
    "visual_evidence_inspected": true,
    "codex_visual_review_ref": ".allforai/game-design/art/qa/codex-visual-review.json",
    "runtime_import_ref": ".allforai/game-design/art/qa/runtime-import-check.json"
  },
  "consumers": ["frame-animation-generation", "animation-state-machine-spec", "runtime-import-check"]
}
```

Allowed states: `planned`, `source_selected`, `source_generated`,
`frames_extracted`, `normalized`, `preview_ready`, `qa_passed`,
`needs_revision`, `blocked`.

Every produced bitmap frame or sheet must be registered through
`game-art/30-generate/image-generation-contract/SKILL.md` so downstream skills
consume `.allforai/game-design/art/image-generation/accepted-image-manifest.json`
entries with `consumer_ready: true`, not raw PNG/JPG/WebP paths.

## Invocation Contract

```json
{
  "skill": "game-art/motion-video-to-sprite-animation",
  "mode": "source_extract_generate_validate",
  "input_paths": {
    "animation_production_plan": ".allforai/game-design/art/animation/2d-animation-production-plan.json",
    "motion_design": ".allforai/game-design/systems/motion-design.json",
    "engine_export_profile": ".allforai/game-design/art/export/engine-export-profile.json",
    "toolchain_report": ".allforai/game-design/art/env/2d-animation-toolchain-report.json",
    "image_generation_contract": "${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/image-generation-contract/SKILL.md",
    "visual_acceptance": "${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/visual-acceptance-review/SKILL.md"
  },
  "output_root": ".allforai/game-design/art/animations/video-to-sprite"
}
```

Supported modes: `source_plan_only`, `source_extract_generate_validate`,
`validate_existing`, `repair_existing`.

## Source Strategy

Choose the motion source in this order unless the production plan explicitly
forbids a source:

```text
local_library
-> user_provided_video
-> existing licensed motion/sprite/video asset
-> web_or_marketplace_search
-> 3d_render_capture
-> engine_capture
-> ai_video
-> hybrid
```

Record every attempted or skipped source in `motion-video-source-plan.json`.
Earlier sources may be skipped only when they are unavailable, fail license
policy, do not match the view/style/action, or cannot satisfy runtime frame
constraints.

Source rules:

- Local, user-provided, existing, web, and marketplace videos require provenance
  and license status before commercial use or adaptation.
- AI video is allowed only as a motion/image source and must be followed by
  frame extraction, visual QA, and downstream runtime validation.
- 3D render capture is preferred over AI video when camera angle, scale,
  turnarounds, or repeatable variants need high control.
- Engine capture is preferred when a rig, tween, or prototype animation already
  exists and can be rendered automatically.
- Do not accept a video because it looks plausible in playback; inspect the
  extracted runtime frames and preview at target size.

## Generation Workflow

1. Resolve `animation_id`, action intent, source route, target FPS, duration,
   loop policy, frame size, anchor, view mode, and runtime export profile.
2. Ensure toolchain capabilities: video sourcing/generation when needed, frame
   extraction such as `ffmpeg`, image processing, alpha/background removal or
   crop tools, atlas packing, preview rendering, Codex CLI visual review, and
   runtime import when available.
3. Acquire or generate the source video by the selected source strategy and
   write provenance in `motion-video-source-manifest.json`.
4. Extract frames at target cadence; discard duplicate/blurred frames only when
   the action still preserves timing and readable key poses.
5. Normalize frames: remove/flatten background as required, crop consistently,
   align subject anchors, resize to target frame size, and preserve silhouettes.
6. Pack frames into the requested sheet/atlas format and write frame metadata.
7. Render a preview at target in-game size and playback speed.
8. Run batch visual acceptance through
   `visual-qa/40-qa/batch-visual-acceptance/SKILL.md` or
   `game-art/40-qa/visual-acceptance-review/SKILL.md`; Codex CLI must inspect
   actual frame/contact-sheet/preview evidence.
9. Run runtime import validation when the engine profile provides an executable
   command. If it cannot run, return `blocked_by_runtime_import`; do not replace
   it with static inspection.
10. Register accepted frames/sheets through `image-generation-contract` and
    update the animation manifest.

## Automatic Validation

Deterministic checks:

- source video exists and provenance/license status is recorded
- extraction command exits `0`
- extracted frame count matches duration/FPS tolerance
- every referenced frame/sheet/preview path exists
- frame dimensions and atlas metadata match the engine export profile
- anchor/pivot stays within declared drift threshold
- loop first/last frame continuity meets the motion spec when `looping=true`
- manifest consumers and accepted-image refs are present

Visual checks:

- identity/style consistency across frames
- action readability at target size
- key pose coverage and timing
- no subject crop, unintended background, motion blur, duplicated frames, or
  incoherent morphing
- anchor/bounding-box stability and no frame-to-frame jitter
- silhouette and hit/readability constraints for gameplay use
- UI/game-layer contrast when the animation is screen-space or UI-facing

The QA report must classify failures as `source_gaps`, `video_generation_gaps`,
`frame_extraction_gaps`, `normalization_gaps`, `visual_gaps`, `contract_gaps`,
`runtime_import_gaps`, or `environment_blockers`.

## Repair Loop

Run up to `max_generation_attempts` from the motion request, default `3`:

- `source_gaps`: search/register another source, or route to AI video/3D
  capture only if the source strategy allows it.
- `video_generation_gaps`: regenerate AI video or rerender 3D/engine capture
  with stricter prompt/camera/action constraints.
- `frame_extraction_gaps`: adjust extraction cadence, de-duplicate policy, or
  source segment boundaries.
- `normalization_gaps`: repair crop, alpha, anchor, scale, or atlas metadata
  without regenerating the source video when content is valid.
- `visual_gaps`: repair with image edit mode for isolated frames only when the
  motion remains coherent; otherwise regenerate the source video.
- `runtime_import_gaps`: repair metadata/export format, then rerun the actual
  import validation.

After every repair, rerun preview generation and visual acceptance on the
changed animation. Do not mark completion from a manifest-only report.

## Completion Conditions

Return `COMPLETED` only when source provenance, extracted frames, normalized
sheet/atlas, preview, Codex CLI visual acceptance, image-generation registration,
and required runtime import validation all pass.

Return `COMPLETED_WITH_LIMITS` only for explicitly accepted reduced frame count,
non-looping, or lower-priority animations where runtime import and visual QA
still pass.

Return `UPSTREAM_DEFECT` when motion intent, style identity, source policy,
asset IDs, or runtime profile are insufficient.

Return `FAILED_VALIDATION` with `blocked_by_missing_toolchain`,
`blocked_by_missing_video_source`, `blocked_by_missing_visual_evidence`,
`blocked_by_runtime_import`, or the relevant gap class when required evidence
cannot be produced. Do not silently downgrade to static art or spec-only output.
