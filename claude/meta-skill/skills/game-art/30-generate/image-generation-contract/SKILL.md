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

This sub-skill defines the shared contract for LLM image generation and other
bitmap-image acquisition in game art and game UI pipelines. It treats every
image upstream as unreliable until it is constrained, validated, repaired, and
recorded before downstream skills can consume the result.

It also defines the feedback loop from downstream skills back to image
acquisition. If a later skill fails because an image is cropped, merged,
misaligned, unreadable, wrong style, wrong scale, or otherwise unusable, the
later skill must report the defect against the original image request so the
image can be regenerated, replaced, adapted, or rejected instead of forcing
downstream workarounds.

This skill does not decide which asset should exist. Asset-specific skills such
as `icon-generation`, `tileset-generation`, `character-layer-sheet`,
`sprite-vfx-generation`, `decal-generation`, `particle-system`,
`trail-generation`, `skeletal-animation`, and `ui-mockup-generation` decide the
asset purpose and then use this contract for image requests and acceptance.

For bulk LLM image production, this contract must delegate execution to
`game-art/30-generate/batch-image-generation/SKILL.md` when `mcp-image-batch` is
available and the routing report selects it. `mcp-image-batch` is a long-task
MCP, so batch prompts and results must be passed through files, not chat/tool
message payloads.

Preferred production chain:

```text
game-art/20-spec/programmatic-art-processing-plan/SKILL.md
-> game-art/20-spec/image-prompt-compiler/SKILL.md
-> game-art/20-spec/image-batch-generation-plan/SKILL.md
-> game-art/30-generate/batch-image-generation/SKILL.md
-> game-art/40-qa/generated-candidate-selection/SKILL.md
-> accepted-image-manifest.json
```

LLM outputs are candidates. They are not consumer-ready until candidate
selection, processing-readiness checks, and downstream validation pass.

## Scope

Use this skill whenever a downstream skill needs bitmap output from any
non-runtime source:
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

Allowed upstream image sources:
- `llm_image_generation`,
- `image_edit`,
- `web_or_marketplace_search`,
- `existing_asset_pack`,
- `user_provided_asset`,
- `3d_assisted_render`,
- `local_asset_library`,
- `local_existing_asset`,
- `hybrid`.

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
| Image model capability registry | selected provider/model, fallback models, missing capabilities | Call `game-art/00-env/image-model-capability-registry/SKILL.md`; return `FAILED_VALIDATION` if required generation cannot be routed. |
| Style context | art style, palette/material/tone, target view or UI context | Use `.allforai/game-design/art-style-guide.json` or return `UPSTREAM_DEFECT`. |
| Asset acceptance criteria | visual and technical standards per asset family | Use `.allforai/game-design/art/asset-acceptance-criteria.json`; return `UPSTREAM_DEFECT` when missing for production generation. |
| Programmatic processing plan | material-first policy, raw material requirements, assembly/preview outputs | Use `.allforai/game-design/art/programmatic-art-processing-plan.json`; return `UPSTREAM_DEFECT` when production 2D art can be assembled or processed deterministically but no plan exists. |
| Compiled prompt manifest | prompt file paths, negative prompt paths, material-first flags, LoRA/reference locks | Use `.allforai/game-design/art/image-generation/compiled-prompt-manifest.json`; return `UPSTREAM_DEFECT` before batch execution when missing. |
| Batch generation plan | batch groups, candidate coverage targets, retry budgets, model/profile grouping | Use `.allforai/game-design/art/image-generation/image-batch-generation-plan.json`; return `UPSTREAM_DEFECT` for bulk generation when missing. |

### Optional inputs

| Input | Fields used | Missing behavior |
|---|---|---|
| `.allforai/game-design/art-style-guide.json` | style, palette, line/rendering rules, camera | Return `UPSTREAM_DEFECT` when style lock is required. |
| `.allforai/game-design/art/asset-acceptance-criteria.json` | project/runtime-specific acceptance standards | Required before `consumer_ready: true`. |
| `.allforai/game-design/asset-registry.json` | `asset_id`, `file_prefix`, paths, state | Use caller-provided naming. |
| `.allforai/game-design/ui/ui-registry.json` | UI screen/component refs | Use caller-provided UI context. |
| `.allforai/game-design/art/image-generation/image-model-capability-registry.json` | provider/model capabilities | Required before selecting an AI image model. |
| `.allforai/game-design/art/image-generation/image-model-routing-report.json` | selected model and fallbacks | Required for `llm_image_generation` or `image_edit`. |
| `.allforai/game-design/art/2d-art-style-taxonomy.json` | selected 2D style family, avoid styles, LLM fit, processing fit | Use to keep prompts aligned with bootstrap-facing user choice. |
| `.allforai/game-design/art/image-generation/generated-candidate-selection-report.json` | selected/rejected candidates and coverage shortages | Required before marking raw generated outputs accepted. |
| Existing generated images | validation and repair source | Register or validate existing image. |
| Search/adaptation outputs | candidate image paths, license and adaptation reports | Validate as acquired images before downstream consumption. |
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
    "source_kind": "llm_image_generation | image_edit | web_or_marketplace_search | existing_asset_pack | user_provided_asset | 3d_assisted_render | local_asset_library | local_existing_asset | hybrid",
    "model_class": "image_generation | image_edit | multimodal_validate | search_register | render_register | spec_only",
    "recommended_model": "<selected provider/model from image-model-routing-report>",
    "fallback_models": [],
    "missing_capabilities": [],
    "identity_lock": {
      "required": false,
      "lock_scope": "none | project_style | character | object | tile_family | icon_family | ui_family",
      "preferred_method": "lora_adapter | reference_edit_mode | reference_image_only | prompt_only",
      "requires_lora": false,
      "lora_adapter_id": null,
      "lora_trigger_tokens": [],
      "fallback_allowed": true,
      "fallback_risk": "none"
    },
    "prompt_template": "icon_prompt | tileset_prompt | ui_mockup_prompt | layer_sheet_prompt | pose_reference_prompt | sprite_vfx_prompt | decal_prompt | particle_texture_prompt | trail_texture_prompt | background_prompt | prop_prompt | portrait_prompt | item_art_prompt | frame_animation_prompt | expression_set_prompt | preview_prompt",
    "material_first": {
      "enabled": true,
      "raw_material_kind": "layer | part | motif | plate | symbol | pose_reference | texture_source | vfx_source",
      "programmatic_consumer": "",
      "assembly_contract_ref": ".allforai/game-design/art/programmatic-art-processing-plan.json"
    },
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
      "consumer_input_contract": "<path or schema ref>",
      "consumer_required_checks": [],
      "consumer_ready_gate": true,
      "reopen_on": ["CROPPED_SUBJECT", "MISSING_REQUIRED_PART", "STYLE_DRIFT"]
    }
  },
  "provenance": {
    "source_kind": "llm_image_generation",
    "source_url": null,
    "source_candidate_id": null,
    "license_report_ref": null,
    "adaptation_manifest_ref": null,
    "generation_report_ref": ".allforai/game-design/art/image-generation/image-generation-report.json"
  }
}
```

## Generation Profile Selection

Every image request must declare a `generation_profile`. The caller may choose
the actual model at runtime, but it must choose a model whose capabilities match
the task profile. Do not use one generic prompt template for all image tasks.
For `llm_image_generation` and `image_edit`, model choice must come from
`game-art/00-env/image-model-capability-registry/SKILL.md`, not from a hardcoded
default model name.

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

Before selecting the final prompt/model path, read the programmatic processing
plan. If it says `material_first`, prompt for the raw materials required by the
plan rather than a flattened final in-game image. Ignore this only when the
processing plan records a justified exception and acceptance criteria allow the
risk.

Provider routing rules:
- Google, fal.ai, OpenRouter, project MCP tools, or custom HTTP providers may be
  selected only after the capability registry records callable access and model
  catalog evidence.
- MCP access is allowed as the provider access path, but MCP presence alone is
  not enough; the selected model must still satisfy the request profile.
- OpenRouter model discovery must use image-output model metadata when
  available.
- fal.ai model selection must record the model schema or model page reference.
- Google image model selection must record the current model id and capability
  evidence from the provider or documentation.
- A generic all-purpose model may be used for drafts, but it cannot produce
  `consumer_ready: true` unless it satisfies the hard capabilities and passes
  downstream validation.

## Identity / Style Lock Contract

Every image request must decide whether identity/style lock is required. This is
separate from normal `style_lock`: normal style lock can be prompt/reference
based, while strict identity lock may require LoRA or an equivalent adapter.

Use `identity_lock.required=true` when the asset must stay stable across many
outputs or future batches:
- recurring character portraits, expression sets, pose sheets, animation frames,
  layer sheets, or outfit variants;
- project-wide style that must survive model/provider changes;
- branded mascots, special objects, tile families, puzzle pieces, icon families,
  or UI visual systems with recognizable shape language.

Allowed methods:
- `lora_adapter`: use a provider/model LoRA, style LoRA, character LoRA, object
  LoRA, or project adapter profile.
- `reference_edit_mode`: use `mcp-image-batch` edit mode / image-to-image with
  context image and mask.
- `reference_image_only`: use reference images without edit masking; allowed only
  when acceptance criteria permit higher drift risk.
- `prompt_only`: allowed only for low-risk, one-off assets.

If `requires_lora=true`, requests must include `lora_adapter_id` or a
project-local LoRA profile ref from `image-model-routing-report.json`. If absent,
return `blocked_by_missing_identity_lock` unless the acceptance criteria
explicitly allow `reference_edit_mode` fallback. Fallbacks must set
`fallback_risk=higher_identity_drift` and trigger stricter visual QA.

Accepted manifest entries for locked assets must record the lock method,
adapter/profile id, trigger tokens when applicable, and whether a fallback was
used. Do not mark `consumer_ready: true` for strict locked assets generated with
prompt-only models.

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
| `.allforai/game-design/art/programmatic-art-processing-plan.json` | yes for 2D production art | Raw material and deterministic processing plan. | prompt compiler, candidate selection, QA. |
| `.allforai/game-design/art/image-generation/compiled-prompt-manifest.json` | when AI generation is used | Prompt files and lock/material-first metadata. | batch planning and generation. |
| `.allforai/game-design/art/image-generation/image-batch-generation-plan.json` | when batch generation is used | Candidate coverage, grouping, retry, and model policies. | batch-image-generation and repair loops. |
| `.allforai/game-design/art/image-generation/mcp-image-batch-input.json` | when using `mcp-image-batch` | File-based request handoff for long-task batch generation. | `batch-image-generation`. |
| `.allforai/game-design/art/image-generation/mcp-image-batch-task.json` | when using `mcp-image-batch` | Long-task id, polling policy, and final task state. | diagnostics and repair loops. |
| `.allforai/game-design/art/image-generation/mcp-image-batch-output.json` | when using `mcp-image-batch` | Structured MCP result mapped to request ids and generated files. | image validation. |
| `.allforai/game-design/art/image-generation/generated-image-files-manifest.json` | when generated | Raw generated file registry before acceptance. | image validation only. |
| `.allforai/game-design/art/image-generation/generated-candidate-selection-report.json` | when generated | Selected/rejected candidates, coverage shortage, processing readiness. | accepted manifest gate and repair loops. |
| `.allforai/game-design/art/image-generation/image-generation-report.json` | yes | Validation, repair attempts, failures, fallbacks. | diagnostics and QA. |
| `.allforai/game-design/art/image-generation/image-feedback-report.json` | when downstream fails | Downstream defect reports mapped back to image requests. | image-producing skills and repair loops. |
| `.allforai/game-design/art/image-generation/accepted-image-manifest.json` | yes when images are accepted | Only downstream-consumable manifest for generated, searched, user-provided, adapted, local, or 3D-rendered images. | downstream asset/UI/VFX pipelines. |
| Requested image paths | when generated or registered | Bitmap outputs owned by caller-specific skill. | accepted-image manifest only; downstream skills must not consume raw PNG paths directly. |

UI-producing callers may write UI-owned images under `.allforai/game-design/ui/`
but should still record the request in the shared manifest or an equivalent
caller-local manifest that follows this schema.

## Accepted Image Manifest Gate

`accepted-image-manifest.json` is the only allowed handoff from image upstreams
to downstream asset, UI, VFX, atlas, animation, and engine-export skills.
Downstream skills must not consume raw PNG paths directly.

Raw LLM/MCP files must pass
`game-art/40-qa/generated-candidate-selection/SKILL.md` before
`accepted-image-manifest.json` may contain `consumer_ready: true`. Selection
must inspect generated files against the compiled prompt manifest, batch plan,
asset acceptance criteria, and programmatic processing plan. Coverage shortage
must trigger another batch or remain blocking.

Every accepted manifest entry must include:

```json
{
  "schema_version": "1.0",
  "request_id": "ico_fireball_primary",
  "asset_id": "fireball",
  "file_prefix": "ico_fireball",
  "source_kind": "llm_image_generation | image_edit | web_or_marketplace_search | existing_asset_pack | user_provided_asset | 3d_assisted_render | local_asset_library | local_existing_asset | hybrid",
  "accepted_image_path": ".allforai/game-design/art/icons/ico_fireball.png",
  "accepted_manifest_path": ".allforai/game-design/art/image-generation/accepted-image-manifest.json",
  "consumer_skill": "game-art/icon-generation",
  "consumer_input_contract": "game-art/30-generate/icon-generation/SKILL.md#Input Contract",
  "consumer_ready": true,
  "acceptance_state": "accepted | needs_revision | rejected | blocked_by_license | blocked_by_validation | blocked_by_downstream_validation",
  "deterministic_checks": [],
  "visual_checks": [],
  "provenance": {
    "source_url": null,
    "source_candidate_id": null,
    "license_report_ref": null,
    "adaptation_manifest_ref": null,
    "generation_report_ref": ".allforai/game-design/art/image-generation/image-generation-report.json"
  },
  "repair_history": [],
  "downstream_revalidation": {
    "required": false,
    "consumer_report_path": null,
    "last_failed_defect": null,
    "rerun_status": "not_required | passed | failed | blocked"
  }
}
```

`consumer_ready` may be true only when all of the following are true:
- the accepted image path exists and matches the declared format/size/alpha
  policy;
- deterministic and visual validation pass for the declared purpose;
- the entry names the downstream consumer skill and its input contract;
- license/provenance status passes for searched, marketplace, pack,
  user-provided, or local-existing assets;
- adaptation or render reports pass when the image came from existing assets or
  3D-assisted production;
- after any downstream feedback, the pipeline must re-run the downstream
  consumer validation that originally failed and record the result here.

If any condition cannot be checked, set `consumer_ready: false` and return
`FAILED_VALIDATION`, `UPSTREAM_DEFECT`, or the specific blocked state. Do not
substitute a weaker static inspection for a required downstream validation.

## Invocation Contract

```json
{
  "skill": "game-art/image-generation-contract",
  "mode": "normalize_generate_validate",
  "input_paths": {
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "ui_registry": ".allforai/game-design/ui/ui-registry.json",
    "image_model_registry": ".allforai/game-design/art/image-generation/image-model-capability-registry.json",
    "image_model_routing": ".allforai/game-design/art/image-generation/image-model-routing-report.json",
    "asset_acceptance_criteria": ".allforai/game-design/art/asset-acceptance-criteria.json"
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
| `route_model` | Invoke or consume `image-model-capability-registry` routing for AI image requests. |
| `normalize_generate_validate` | Normalize, generate/register, validate, repair, and report. |
| `validate_existing` | Validate existing image outputs against requests. |
| `register_searched_or_existing` | Register searched, marketplace, user-provided, adapted, local, or 3D-rendered image outputs, then validate them into the accepted-image manifest. |
| `repair_request` | Produce revised prompt constraints for failed requests. |
| `process_downstream_feedback` | Read downstream defects, classify root cause, reopen image requests when needed. |
| `repair_coverage_shortage` | Generate more candidates or missing required variants after QA/downstream coverage failure. |

## Batch MCP Execution

When a batch contains multiple `llm_image_generation` or `image_edit` requests
and `image-model-routing-report.json` selects `mcp_image_batch`, invoke:

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/batch-image-generation/SKILL.md
```

Rules:
- use `mcp-image-batch` for the batch execution;
- write prompts, negative prompts, request arrays, reference paths, edit-mode
  fields, and output paths into
  `.allforai/game-design/art/image-generation/mcp-image-batch-input.json` or
  per-request prompt files;
- submit only file paths and long-task policy to the MCP;
- poll the long task and record
  `.allforai/game-design/art/image-generation/mcp-image-batch-task.json`;
- read results from
  `.allforai/game-design/art/image-generation/mcp-image-batch-output.json`;
- map generated files into
  `.allforai/game-design/art/image-generation/generated-image-files-manifest.json`;
- then run deterministic validation, visual validation, and downstream
  acceptance from this contract before writing `accepted-image-manifest.json`;
- generated candidates must be filtered by
  `game-art/40-qa/generated-candidate-selection/SKILL.md` before any entry is
  marked `consumer_ready: true`.

Do not mark MCP outputs `consumer_ready: true` directly. Do not hand raw
`generated-image-files-manifest.json` paths to downstream skills. If
`mcp-image-batch` is selected but unavailable, return
`blocked_by_missing_mcp_image_batch`.

For `image_edit`, `image_to_image`, in-painting, local repair, or
identity-preserving variation requests, include edit-mode fields for
`game-art/30-generate/batch-image-generation/SKILL.md`:

```json
{
  "operation": "edit",
  "contextImage": ".allforai/game-design/art/characters/umeko_default.png",
  "basePrompt": "Render the approved base image while preserving identity.",
  "maskRegion": [0.10, 0.30, 0.80, 0.45],
  "imageIndex": 0
}
```

Do not route edit requests through plain text-to-image generation when the
downstream requirement is to preserve identity, pose, clothing, layout, or
unmasked pixels. If the request lacks a context/base image or mask region,
return `UPSTREAM_DEFECT` and repair the request contract first.

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
9. Accepted entries are written only through `accepted-image-manifest.json`.
10. `consumer_ready` is false unless the declared downstream consumer and input
    contract are present.
11. Non-LLM sources include license/provenance and adaptation/render evidence.
12. LLM/image-edit requests include a selected provider/model from
    `image-model-routing-report.json`, or a blocked state with
    `missing_capabilities`.
13. Production requests reference matching asset-family criteria from
    `asset-acceptance-criteria.json`; otherwise `consumer_ready` remains false.
14. When `mcp_image_batch` is selected, the batch adapter wrote
    `mcp-image-batch-input.json`, `mcp-image-batch-task.json`,
    `mcp-image-batch-output.json`, and
    `generated-image-files-manifest.json`.
15. `mcp-image-batch` outputs are never accepted without this contract's
    deterministic and visual validation.
16. `image_edit` / image-to-image requests routed to `mcp_image_batch` include
    operation, context/base image, maskRegion, and preservation acceptance
    checks.
17. Strict identity/style lock requests include identity lock method, LoRA
    adapter/profile when required, and no prompt-only strict acceptance.

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

Downstream skills must not silently compensate for unusable upstream images.
If a consumer fails after using an accepted image, it must write a feedback item
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
  "requested_action": "regenerate_image | replace_source_candidate | adapt_existing_asset | revise_prompt | revise_downstream_spec | keep_with_warning"
}
```

Root-cause rules:
- `image_generation`: output violated the normalized request even though the
  request was sound. Regenerate with the same or slightly tightened prompt.
- `prompt_contract`: request was underspecified or missing a negative
  constraint. Revise prompt contract before regenerating.
- `source_selection`: searched, pack, user-provided, or local source cannot
  satisfy style/runtime/license/quality constraints. Return to
  `asset-pack-search-spec` or `asset-source-strategy-spec`.
- `asset_adaptation`: source image is usable but target slicing, scale, alpha,
  pivot, atlas, style normalization, or metadata is wrong. Return to
  `existing-asset-adaptation-spec`.
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

When feedback indicates coverage shortage, insufficient accepted images, missing
required variants, or not enough usable candidates, do not treat the previous
partial batch as complete. Add or reopen only the affected request ids and call
`game-art/30-generate/batch-image-generation/SKILL.md` again through
`mcp-image-batch` file handoff. Then re-run this contract's validation and the
downstream consumer validation. Examples include missing required tile states,
too few distinguishable tile variants, incomplete expression sets, insufficient
icon alternatives, failed contact-sheet coverage, and visual QA rejecting enough
images that the accepted count falls below the contract.

When feedback root cause is `source_selection`, `license_provenance`, or
`asset_adaptation`, do not call image generation by default. Reopen the selected
candidate or adaptation entry, repair through the owning source/adaptation skill,
then re-register the image here and re-run the downstream consumer validation
that originally failed.

The repair budget is shared across the image request and its downstream
consumer. A default budget is 3 image attempts plus 2 downstream revalidation
attempts. If the defect still remains, return `FAILED_VALIDATION` with the
last evidence, failed checks, and upstream repair target.

## Repair Loop

If validation fails:
1. Write the failed check and evidence into the report.
2. Modify only the prompt constraints relevant to the failed check.
3. Regenerate or re-register the image. For LLM/image-edit requests routed to
   `mcp_image_batch`, regenerate by submitting an affected-request repair batch
   to `mcp-image-batch`; do not switch to ad hoc single-image generation.
4. Re-run deterministic and visual validation.
5. Stop after `max_repair_attempts`.

If still failing, return `FAILED_VALIDATION` with issue evidence and repair
targets. Spec-only or placeholder artifacts may be written for debugging, but
must not be reported as accepted generation output or written with
`consumer_ready: true`.

Do not ask for human reference images or human approval.

## Completion Conditions

Return `COMPLETED` only when normalized request manifests, reports, and
`accepted-image-manifest.json` validate, and every required image is
`consumer_ready: true` for its declared downstream consumer.

Return `FAILED_VALIDATION` when image generation or vision validation is
unavailable for required generated output, when searched/existing assets lack
license/provenance or adaptation evidence, or when images fail acceptance after
the repair budget. Return `UPSTREAM_DEFECT` when a request lacks required fields
and cannot be normalized.
