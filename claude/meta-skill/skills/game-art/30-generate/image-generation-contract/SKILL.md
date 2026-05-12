---
name: game-art-30-generate-image-generation-contract
description: Internal bundled meta-skill module for game-art/30-generate/image-generation-contract; use within generated bootstrap node-specs when this exact contract is selected.
---

# Image Generation Contract Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill defines the shared contract for LLM image generation in game art
and game UI pipelines. It treats image generation as an unreliable upstream that
must be constrained, validated, repaired, and recorded before downstream skills
can consume the result.

It also defines the feedback loop from downstream skills back to image
generation. If a later skill fails because an image is cropped, merged,
misaligned, unreadable, wrong style, wrong scale, or otherwise unusable, the
later skill must report the defect against the original image request so the
image can be regenerated instead of forcing downstream workarounds.

This skill does not decide which asset should exist. Asset-specific skills such
as `icon-generation`, `tileset-generation`, `character-layer-sheet`,
`sprite-vfx-generation`, `decal-generation`, `particle-system`,
`trail-generation`, `skeletal-animation`, and `ui-mockup-generation` decide the
asset purpose and then use this contract for image requests and acceptance.

## Scope

Use this skill whenever a downstream skill needs AI-generated bitmap output:
- icons,
- tilesets,
- UI mockups,
- layer sheets,
- pose/keyframe reference sheets,
- sprite-sheet VFX,
- decal textures,
- particle textures,
- trail strip textures,
- preview or reference images.

Out of scope:
- choosing gameplay semantics,
- deciding asset inventory,
- final engine import,
- accepting images without validation,
- human review gates.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| Image generation request | `request_id`, `asset_id`, `purpose`, `output_path`, `prompt`, `acceptance` | Return `UPSTREAM_DEFECT`. |
| Generation profile | `task_type`, `model_class`, `prompt_template`, `output_constraints` | Derive from `purpose` once; if still ambiguous, return `UPSTREAM_DEFECT`. |
| Style context | art style, palette/material/tone, target view or UI context | Use `.allforai/game-design/art-style-guide.json` or return `UPSTREAM_DEFECT`. |

### Optional inputs

| Input | Fields used | Missing behavior |
|---|---|---|
| `.allforai/game-design/art-style-guide.json` | style, palette, line/rendering rules, camera | Return `UPSTREAM_DEFECT` when style lock is required. |
| `.allforai/game-design/asset-registry.json` | `asset_id`, `file_prefix`, paths, state | Use caller-provided naming. |
| `.allforai/game-design/ui/ui-registry.json` | UI screen/component refs | Use caller-provided UI context. |
| Existing generated images | validation and repair source | Register or validate existing image. |
| Caller generation capabilities | image model, transparent background support, vision validator | Return `FAILED_VALIDATION` if required generation or validation cannot run. |

## Request Schema

Every image-producing skill must normalize image requests to this shape:

```json
{
  "schema_version": "1.0",
  "request_id": "ico_fireball_primary",
  "asset_id": "fireball",
  "file_prefix": "ico_fireball",
  "purpose": "skill_icon | tileset | ui_mockup | layer_sheet | pose_reference | sprite_vfx | decal | particle_texture | trail_texture | background | prop | portrait | item_art | frame_animation | expression_set | preview",
  "generation_profile": {
    "task_type": "icon | tileset | ui_mockup | layer_sheet | pose_reference | sprite_vfx | decal | particle_texture | trail_texture | background | prop | portrait | item_art | frame_animation | expression_set | preview",
    "model_class": "image_generation | image_edit | multimodal_validate | spec_only",
    "recommended_model": "<runtime-selected model or capability alias>",
    "prompt_template": "icon_prompt | tileset_prompt | ui_mockup_prompt | layer_sheet_prompt | pose_reference_prompt | sprite_vfx_prompt | decal_prompt | particle_texture_prompt | trail_texture_prompt | background_prompt | prop_prompt | portrait_prompt | item_art_prompt | frame_animation_prompt | expression_set_prompt | preview_prompt",
    "output_constraints": {
      "alpha": false,
      "exact_size": true,
      "style_lock": true,
      "multi_frame_consistency": false,
      "small_size_readability": false,
      "seamless_edges": false,
      "layout_fidelity": false,
      "part_separation": false,
      "identity_consistency": false
    }
  },
  "style_context": {
    "source": ".allforai/game-design/art-style-guide.json",
    "dimension": "2d | 3d | screen_space",
    "render_style": "pixel | painted | vector | flat | hand_drawn | realistic | unknown",
    "palette": [],
    "camera_or_view": "front | side | top_down | isometric | screen | unknown"
  },
  "prompt_contract": {
    "positive_prompt": "<specific visual request>",
    "negative_prompt": "<forbidden content and failure modes>",
    "must_include": [],
    "must_not_include": [],
    "composition": "<framing/layout rules>",
    "background": "transparent | flat_neutral | scene | existing_context",
    "size": {"width": 1024, "height": 1024},
    "variants": []
  },
  "output_contract": {
    "path": ".allforai/game-design/art/icons/ico_fireball.png",
    "format": "png",
    "alpha_required": true,
    "file_prefix_required": "ico_fireball"
  },
  "acceptance": {
    "deterministic_checks": [],
    "visual_checks": [],
    "small_size_check": false,
    "transparent_background_check": false,
    "max_repair_attempts": 3,
    "downstream_feedback": {
      "enabled": true,
      "accepted_consumers": ["<skill name>"],
      "reopen_on": ["CROPPED_SUBJECT", "MISSING_REQUIRED_PART", "STYLE_DRIFT"]
    }
  }
}
```

## Generation Profile Selection

Every image request must declare a `generation_profile`. The caller may choose
the actual model at runtime, but it must choose a model whose capabilities match
the task profile. Do not use one generic prompt template for all image tasks.

| Task type | Model capability profile | Prompt template | Required output constraints |
|---|---|---|---|
| `icon` | high-silhouette image generation or edit | `icon_prompt` | alpha, exact size, style lock, small-size readability. |
| `tileset` | consistent texture/tile generation | `tileset_prompt` | exact size, seamless edges, style lock, atlas compatibility. |
| `ui_mockup` | layout-aware image generation/edit | `ui_mockup_prompt` | layout fidelity, text constraints, style lock. |
| `layer_sheet` | controlled character/component separation | `layer_sheet_prompt` | part separation, alpha/neutral background, exact size. |
| `pose_reference` | character-consistent pose/reference generation | `pose_reference_prompt` | identity consistency, pose readability, style lock. |
| `sprite_vfx` | frame-consistent effect generation | `sprite_vfx_prompt` | alpha, exact frame grid, multi-frame consistency. |
| `decal` | transparent texture generation | `decal_prompt` | alpha, blend edge quality, surface readability. |
| `particle_texture` | simple transparent sprite generation | `particle_texture_prompt` | alpha, small texture readability, blend suitability. |
| `trail_texture` | strip/gradient texture generation | `trail_texture_prompt` | alpha, stretch suitability, fade quality. |
| `background` | scene/background generation | `background_prompt` | camera/view, composition, style lock, UI-safe negative space. |
| `prop` | isolated object generation | `prop_prompt` | alpha, scale readability, style lock. |
| `portrait` | identity-consistent character portrait | `portrait_prompt` | identity consistency, crop policy, expression clarity. |
| `item_art` | isolated item/equipment generation | `item_art_prompt` | alpha, category readability, rarity/state clarity. |
| `frame_animation` | frame sheet generation/edit | `frame_animation_prompt` | exact frame grid, anchor consistency, multi-frame consistency. |
| `expression_set` | identity-consistent expression variants | `expression_set_prompt` | identity consistency, expression distinction, crop consistency. |
| `preview` | validation preview or reference image | `preview_prompt` | composition matches downstream validation need. |

If no available model supports the required profile, return `FAILED_VALIDATION`
with the missing capability and repair target. Do not produce spec-only or
placeholder output as accepted image-generation completion.

## Prompt Contract

Every request must include:
- asset purpose,
- generation profile and prompt template,
- exact subject,
- style source,
- target view/camera,
- composition and framing,
- background policy,
- size/aspect,
- output path,
- acceptance criteria.

Every request must include a negative prompt or equivalent constraint list.
Common negative constraints:
- no text or labels unless explicitly required,
- no cropping,
- no extra characters or objects,
- no merged parts when separation is required,
- no style drift from the art style guide,
- no busy background when transparency is required,
- no perspective mismatch for tiles/isometric/UI,
- no fake UI text beyond specified labels.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/art/image-generation/image-request-manifest.json` | yes | Normalized image requests, prompts, outputs, states. | image-producing skills, QA. |
| `.allforai/game-design/art/image-generation/image-generation-report.json` | yes | Validation, repair attempts, failures, fallbacks. | diagnostics and QA. |
| `.allforai/game-design/art/image-generation/image-feedback-report.json` | when downstream fails | Downstream defect reports mapped back to image requests. | image-producing skills and repair loops. |
| Requested image paths | when generated | Bitmap outputs owned by caller-specific skill. | downstream asset/UI/VFX pipelines. |

UI-producing callers may write UI-owned images under `.allforai/game-design/ui/`
but should still record the request in the shared manifest or an equivalent
caller-local manifest that follows this schema.

## Invocation Contract

```json
{
  "skill": "game-art/image-generation-contract",
  "mode": "normalize_generate_validate",
  "input_paths": {
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "ui_registry": ".allforai/game-design/ui/ui-registry.json"
  },
  "requests": [],
  "generation": {
    "image_generation_available": true,
    "vision_validation_available": true,
    "transparent_background_supported": true,
    "max_repair_attempts": 3
  },
  "output_root": ".allforai/game-design"
}
```

Supported modes:

| Mode | Behavior |
|---|---|
| `normalize_only` | Validate and normalize image requests without generation. |
| `normalize_generate_validate` | Normalize, generate/register, validate, repair, and report. |
| `validate_existing` | Validate existing image outputs against requests. |
| `repair_request` | Produce revised prompt constraints for failed requests. |
| `process_downstream_feedback` | Read downstream defects, classify root cause, reopen image requests when needed. |

## Automatic Validation

Run deterministic checks:
1. Every request has `request_id`, `asset_id`, purpose, prompt, output path, and
   acceptance rules.
2. Output path starts with the caller-approved root.
3. Output filename starts with the resolved `file_prefix`.
4. Size/aspect/background policy are declared.
5. `generation_profile.task_type`, `model_class`, `prompt_template`, and
   `output_constraints` are declared.
6. Negative prompt or `must_not_include` exists.
7. `max_repair_attempts` is finite.
8. Generated outputs are never marked `approved` without validation.

Run visual validation when images exist:
1. Subject matches the request purpose.
2. Required elements are present.
3. Forbidden elements are absent.
4. Style matches `art-style-guide.json`.
5. No important subject is cropped.
6. Background/alpha policy is satisfied.
7. Small-size readability passes when required.
8. Composition matches the downstream use case.

## Downstream Feedback Loop

Downstream skills must not silently compensate for unusable generated images.
If a consumer fails after using a generated image, it must write a feedback item
that identifies whether the root cause belongs to the image request, downstream
spec, runtime/tooling, or unavailable capability.

Feedback item shape:

```json
{
  "schema_version": "1.0",
  "request_id": "ico_fireball_primary",
  "asset_id": "fireball",
  "consumer_skill": "game-ui/ui-mockup-generation",
  "consumer_artifact": ".allforai/game-design/ui/ui-mockup-report.json",
  "defect": {
    "code": "STYLE_DRIFT | CROPPED_SUBJECT | MISSING_REQUIRED_PART | MERGED_PARTS | WRONG_VIEW | LOW_READABILITY | BAD_ALPHA | SEAM_FAILURE | TEXT_ARTIFACT | WRONG_SCALE | DOWNSTREAM_SPEC_ERROR | RUNTIME_IMPORT_ERROR",
    "severity": "blocker | major | minor",
    "evidence": ["<path or structured note>"]
  },
  "root_cause": "image_generation | prompt_contract | downstream_spec | runtime_tooling | unknown",
  "requested_action": "regenerate_image | revise_prompt | revise_downstream_spec | keep_with_warning"
}
```

Root-cause rules:
- `image_generation`: output violated the normalized request even though the
  request was sound. Regenerate with the same or slightly tightened prompt.
- `prompt_contract`: request was underspecified or missing a negative
  constraint. Revise prompt contract before regenerating.
- `downstream_spec`: image is valid but downstream expectations were wrong.
  Do not regenerate; repair the downstream spec.
- `runtime_tooling`: image is valid but import/render tooling failed. Do not
  regenerate; repair tooling or output format.
- `unknown`: run one repair pass only, then require a structured fallback.

When feedback root cause is `image_generation` or `prompt_contract`, reopen the
original request:
1. Set request state to `needs_revision`.
2. Copy downstream defect code into `acceptance.visual_checks`.
3. Add or tighten the corresponding negative prompt constraint.
4. Regenerate the image.
5. Re-run image validation.
6. Re-run the downstream consumer validation that originally failed.
7. Stop after the combined image/downstream repair budget is exhausted.

The repair budget is shared across the image request and its downstream
consumer. A default budget is 3 image attempts plus 2 downstream revalidation
attempts. If the defect still remains, return `FAILED_VALIDATION` with the
last evidence, failed checks, and upstream repair target.

## Repair Loop

If validation fails:
1. Write the failed check and evidence into the report.
2. Modify only the prompt constraints relevant to the failed check.
3. Regenerate or re-register the image.
4. Re-run deterministic and visual validation.
5. Stop after `max_repair_attempts`.

If still failing, return `FAILED_VALIDATION` with issue evidence and repair
targets. Spec-only or placeholder artifacts may be written for debugging, but
must not be reported as accepted generation output.

Do not ask for human reference images or human approval.

## Completion Conditions

Return `COMPLETED` only when normalized request manifests and reports validate,
and every required generated image passes acceptance.

Return `FAILED_VALIDATION` when image generation or vision validation is
unavailable for required output, or when generated images fail acceptance after
the repair budget. Return `UPSTREAM_DEFECT` when a request lacks required fields
and cannot be normalized.
