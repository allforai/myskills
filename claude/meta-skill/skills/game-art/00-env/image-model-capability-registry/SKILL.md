---
name: game-art-00-env-image-model-capability-registry
description: Internal bundled meta-skill module for game-art/00-env/image-model-capability-registry; use within generated bootstrap node-specs when image generation providers or MCP-backed image models must be detected, ranked, and validated.
---

# Image Model Capability Registry Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Detects image-generation providers, MCP tools, SDK/HTTP access paths, API key
availability, current model catalogs, model capabilities, pricing hints, and
routing suitability for game-art and game-UI image tasks.

This skill does not generate final art. It builds the model capability registry
that `image-generation-contract` must use before selecting any model.

Supported provider families:
- `google_gemini_image`
- `fal_ai`
- `openrouter_image`
- `mcp_image_batch`
- `project_local_mcp`
- `custom_http_provider`

The registry must prefer current provider discovery over hardcoded model names.
Provider model catalogs are time-sensitive and must be refreshed at execution
time when network/API access is available.

## Input Contract

Required: requested image generation profiles or art pipeline config.

Optional: configured MCP tools, environment variable names, project provider
preferences, budget/latency policy, allowed providers, forbidden providers,
cached model catalog, and previous validation history.

Expected environment variables:
- `GOOGLE_API_KEY` or project-specific Google key alias;
- `FAL_KEY` or `FAL_API_KEY`;
- `OPENROUTER_API_KEY`;
- provider-specific custom keys declared by the project.

## Output Contract

Writes:

- `.allforai/game-design/art/image-generation/image-model-capability-registry.json`
- `.allforai/game-design/art/image-generation/image-model-routing-report.json`

Registry entries must include `provider_id`, `provider_kind`, `access_path`,
`mcp_tool`, `api_key_env`, `availability`, `catalog_discovery`,
`model_id`, `model_display_name`, `model_version_or_created_at`,
`expiration_date`, `input_modalities`, `output_modalities`,
`supported_parameters`, `provider_schema_ref`, `pricing`, `rate_limits`,
`capability_tags`, `task_type_fit`, `quality_tier`, `latency_tier`,
`cost_tier`, `validation_evidence`, `failure_status`, and `notes`.

Routing report entries must include `request_id`, `asset_id`, `task_type`,
`required_capabilities`, `candidate_models`, `selected_provider`,
`selected_model`, `fallback_models`, `rejected_models`, `missing_capabilities`,
`selection_reason`, `routing_state`, and `consumer_refs`.

Allowed availability values: `available`, `missing_key`, `mcp_missing`,
`api_unreachable`, `catalog_unavailable`, `model_unavailable`,
`configured_but_unverified`, `not_allowed`, `not_required`.

Allowed routing states: `selected`, `selected_with_warning`,
`blocked_by_missing_model`, `blocked_by_provider_access`,
`blocked_by_policy`, `blocked_by_budget`, `blocked_by_missing_identity_lock`.

Allowed capability tags:
- `text_to_image`
- `image_edit`
- `image_to_image`
- `transparent_alpha`
- `aspect_ratio_control`
- `high_resolution`
- `text_rendering`
- `layout_fidelity`
- `identity_consistency`
- `identity_lock`
- `style_lora`
- `character_lora`
- `object_lora`
- `lora_adapter`
- `multi_frame_consistency`
- `frame_grid`
- `seamless_texture`
- `small_size_readability`
- `style_lock`
- `fast_iteration`
- `professional_quality`
- `schema_documented`

## Invocation Contract

```json
{
  "skill": "game-art/image-model-capability-registry",
  "mode": "detect_route_validate",
  "input_paths": {
    "image_requests": ".allforai/game-design/art/image-generation/image-request-manifest.json",
    "art_pipeline_config": ".allforai/game-design/art-pipeline-config.json"
  },
  "providers": {
    "google": {"enabled": true, "api_key_env": "GOOGLE_API_KEY"},
    "fal_ai": {"enabled": true, "api_key_env": "FAL_KEY"},
    "openrouter": {"enabled": true, "api_key_env": "OPENROUTER_API_KEY"}
  },
  "output_root": ".allforai/game-design/art/image-generation"
}
```

Supported modes: `detect_only`, `discover_catalog`, `route_only`,
`detect_route_validate`, `validate_existing`, `repair_existing`.

## Provider Discovery Method

Detection order:

```text
configured project MCP tools
-> provider API key environment variables
-> provider catalog API or documented model schema
-> cached catalog if live discovery is unavailable and cache age is acceptable
-> blocked status if no verified access exists
```

Provider rules:

- Google Gemini/Imagen access must be discovered from the configured Google API
  key and current Google model documentation/API availability. Use current model
  capabilities instead of assuming one permanent best model.
- fal.ai access must be discovered through `fal.ai` model metadata or model
  pages with input/output schemas. Each selected model must have a schema ref.
- OpenRouter access must use the Models API with
  `output_modalities=image` or equivalent image-output filtering when live API
  access is available. Record returned `architecture.output_modalities`,
  `supported_parameters`, pricing, and expiration metadata.
- Project MCP tools may wrap any provider, but MCP presence alone is not enough.
  The provider must still prove a callable image generation or image edit path.
- If MCP is absent but a provider SDK/HTTP path and API key are available, the
  registry may use SDK/HTTP access. Record `access_path=sdk_http`.

Do not hardcode a model as universally best. Hardcoded model names may appear
only as examples, cached observations, or provider-specific candidate entries
with discovery evidence.

## Routing Method

Translate each `generation_profile` into required capabilities:

| Task type | Required model capabilities |
|---|---|
| `icon` | `text_to_image`, `small_size_readability`, `style_lock`, `aspect_ratio_control`; prefer `transparent_alpha`. |
| `item_art` | `text_to_image`, `small_size_readability`, `style_lock`, `aspect_ratio_control`; prefer `transparent_alpha`. |
| `prop` | `text_to_image`, `style_lock`, `aspect_ratio_control`; prefer `transparent_alpha`. |
| `portrait` | `text_to_image`, `identity_consistency`, `style_lock`, `high_resolution`. |
| `expression_set` | `text_to_image` or `image_edit`, `identity_consistency`, `style_lock`, `multi_frame_consistency`. |
| `tileset` | `text_to_image` or `image_edit`, `seamless_texture`, `style_lock`, `aspect_ratio_control`. |
| `background` | `text_to_image`, `style_lock`, `aspect_ratio_control`, `high_resolution`. |
| `ui_mockup` | `text_to_image`, `layout_fidelity`, `text_rendering`, `aspect_ratio_control`. |
| `layer_sheet` | `text_to_image` or `image_edit`, `identity_consistency`, `style_lock`, `transparent_alpha`. |
| `pose_reference` | `text_to_image` or `image_edit`, `identity_consistency`, `style_lock`, `professional_quality`. |
| `sprite_vfx` | `text_to_image` or `image_edit`, `transparent_alpha`, `frame_grid`, `multi_frame_consistency`. |
| `frame_animation` | `text_to_image` or `image_edit`, `frame_grid`, `multi_frame_consistency`, `style_lock`. |
| `particle_texture` | `text_to_image`, `transparent_alpha`, `small_size_readability`, `fast_iteration`. |
| `trail_texture` | `text_to_image`, `transparent_alpha`, `aspect_ratio_control`, `style_lock`. |
| `decal` | `text_to_image`, `transparent_alpha`, `small_size_readability`, `style_lock`. |
| `preview` | match the downstream preview purpose; no generic model routing. |

Selection order:

```text
hard capability match
-> provider policy allowed
-> previous validation success for same task_type
-> quality tier
-> schema completeness
-> cost tier
-> latency tier
-> fallback availability
```

When no candidate satisfies hard capabilities, return
`blocked_by_missing_model` and list `missing_capabilities`. Do not select a
generic all-purpose model as a production model when it lacks required
capabilities.

## Identity And Style Locking

LoRA is optional globally but required for requests whose acceptance criteria
declare `identity_lock.required=true` and whose risk cannot be satisfied by
reference-image edit mode. Treat LoRA as one implementation of a broader
identity/style lock strategy.

Supported lock methods:
- `lora_adapter`: provider/model supports a project, style, character, or object
  LoRA adapter.
- `reference_edit_mode`: provider supports image edit / image-to-image with a
  context image and mask.
- `reference_image_only`: provider supports reference images but not true edit
  mode; this is lower confidence and cannot satisfy strict locks by itself.
- `prompt_only`: allowed only for low-risk assets.

Registry entries that support LoRA must record `lora_adapter_id`,
`lora_adapter_kind`, `lora_trigger_tokens`, `lora_weight_range`,
`lora_training_source_ref`, `lora_license_ref`, and `lora_validation_evidence`
when available.

Routing report entries must include `identity_lock_method`,
`identity_lock_strength`, `lora_adapter_id`, `requires_lora`, and
`identity_lock_fallbacks`. Allowed lock strengths: `strict`, `medium`, `low`,
`none`.

Use `requires_lora=true` for:
- recurring named characters across portraits, expression sets, animation frames,
  layer sheets, or outfit variants when edit mode cannot preserve identity;
- project-specific art style that must remain stable across many future batches;
- branded objects, puzzle pieces, tile families, icons, or mascots whose shape
  vocabulary must remain stable beyond one batch;
- any acceptance criteria that marks identity/style drift as a blocker and
  disallows reference-only fallback.

If `requires_lora=true` and no candidate exposes `lora_adapter` or an accepted
project LoRA profile, return `blocked_by_missing_identity_lock`. Do not silently
downgrade to prompt-only generation. If reference edit mode is allowed as a
fallback, set `selected_with_warning` and record the higher QA risk.

## MCP Image Batch Provider

When `mcp-image-batch` is configured, record it as provider kind
`mcp_image_batch` with `access_path=mcp_long_task` and `mcp_tool=mcp-image-batch`.
This provider is preferred for large batches of `llm_image_generation` or
`image_edit` requests when it satisfies the same hard capabilities as the routed
task profile.

The registry must verify:
- the MCP tool exists and can accept a file path input;
- the MCP can write a structured output file;
- long-task submission and polling are available;
- edit-mode tools or config are available when routing `image_edit` /
  image-to-image requests;
- selected model/profile information is returned or configured;
- missing tool support returns `blocked_by_missing_mcp_image_batch`, not a
  silent fallback to chat-based image generation.

For `mcp_image_batch`, the routing report must include
`batch_execution_skill=game-art/30-generate/batch-image-generation/SKILL.md`
and the selected model entry must state that file handoff is required. For edit
requests, the selected route must include `supports_edit_mode=true` or a
blocked state with the missing edit capability.

## Automatic Validation

Run these checks:
1. Every required provider entry records access path, API key environment
   status, and catalog discovery status.
2. Every selected model has image output capability.
3. Every selected model maps to the request `task_type`.
4. Required capability tags are present or explicitly justified as unavailable.
5. Provider-specific schema or supported parameters are recorded when available.
6. Pricing, rate limits, or unknown cost status are recorded.
7. Deprecated or expired models cannot be selected unless explicitly allowed
   for non-production experiments.
8. `selected_model` is absent when routing state is blocked.
9. Fallback models must satisfy the same hard capabilities, not just the same
   provider family.
10. Missing provider access returns a blocked state instead of a placeholder.
11. Strict identity/style lock requests are not routed to prompt-only models.
12. LoRA routes include adapter id, trigger tokens or profile ref, and license
    evidence when available.

## Repair Loop

If routing fails:
- missing API key routes to environment setup;
- missing MCP routes to provider SDK/HTTP fallback if available;
- unavailable provider catalog routes to live discovery repair or cache refresh;
- no model match routes to prompt/profile relaxation only if downstream
  constraints allow it;
- budget failure routes to provider preference or source strategy repair;
- repeated generation validation failure demotes the model for that `task_type`
  and re-routes to the next valid candidate.

## Completion Conditions

Return `COMPLETED` when all required image requests either have selected
models/fallbacks or have a blocked state with exact missing capabilities and
provider access evidence.

Return `FAILED_VALIDATION` when a selected model lacks image output, lacks a
required hard capability, has no callable access path, or cannot be verified.
