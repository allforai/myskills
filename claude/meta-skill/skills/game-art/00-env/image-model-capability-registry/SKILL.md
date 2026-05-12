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
`blocked_by_policy`, `blocked_by_budget`.

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
