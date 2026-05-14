---
name: game-art-10-design-asset-source-strategy-spec
description: Internal bundled meta-skill module for game-art/10-design/asset-source-strategy-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Asset Source Strategy Spec Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Chooses the source strategy for each art asset or asset group. It decides
whether to use local/project asset libraries, user-provided files, existing
asset packs, web or marketplace search, LLM image generation, motion-video
sourcing/capture, 3D-assisted rendering, adapted existing assets, or mixed
sourcing.

Use this after `art-direction-input-contract` and before asset search,
generation, or 3D-assisted production.

## Input Contract

Required: art direction input contract, asset registry or asset list, target
runtime, and production constraints.

Optional: human preferences, budget, license requirements, style tokens, view
mode, tool registry, existing local assets, search platforms, and schedule.

## Output Contract

Writes:

- `.allforai/game-design/art/sourcing/asset-source-strategy-spec.json`
- `.allforai/game-design/art/sourcing/asset-source-strategy-report.json`

Strategy entries must include `asset_id`, `asset_group`, `asset_kind`,
`source_strategy`, `source_priority_chain`, `selection_reason`,
`license_requirements`, `quality_requirements`, `adaptation_requirements`,
`fallback_strategy`, `downstream_skill_refs`, `handoff_requirements`, `state`,
and `consumer_refs`.

Allowed source strategies: `local_asset_library`, `user_provided_asset`,
`existing_asset_pack`, `web_or_marketplace_search`, `llm_image_generation`,
`motion_video_source`, `ai_video_source`, `3d_render_capture`,
`engine_capture`, `3d_assisted_render`, `existing_3d_source_asset`,
`adapt_existing_asset`, `hybrid`, `placeholder_only`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_preferences`, `blocked_by_license_policy`, `blocked_by_budget`.

Downstream consumers: `asset-pack-search-spec`, `asset-license-provenance-qa`,
`existing-asset-adaptation-spec`, `image-generation-contract`,
`render-to-2d-asset-generation`, `motion-video-to-sprite-animation`,
`artifact-handoff-contract`,
`asset-pack-integration-qa`, and `engine-ready-art-output-contract`.

## Invocation Contract

```json
{
  "skill": "game-art/asset-source-strategy-spec",
  "mode": "spec_validate",
  "input_paths": {
    "art_direction": ".allforai/game-design/art/art-direction-input-contract.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "visual_style_tokens": ".allforai/game-design/art/visual-style-tokens.json"
  },
  "output_root": ".allforai/game-design/art/sourcing"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every planned asset group has one primary strategy, one fallback
strategy, license requirements, quality gates, adaptation needs, and downstream
routes. Existing packs must route through license/provenance QA before
adaptation or runtime output.

Default priority chain:

```text
local_asset_library
-> user_provided_asset
-> existing_asset_pack
-> web_or_marketplace_search
-> llm_image_generation
-> motion_video_source | ai_video_source | 3d_render_capture | engine_capture
-> 3d_assisted_render | hybrid
```

Only skip an earlier step when the project explicitly forbids that source,
the required asset kind cannot be satisfied by that source, or the source is
unavailable. Record every skipped step and reason in `source_priority_chain`.

Strategy rules:

- Use `existing_asset_pack` for broad, coherent sets such as UI packs, tilesets,
  icons, VFX packs, or complete character packs when license and style fit.
- Use `local_asset_library` before web search or LLM generation when project
  files, shared studio libraries, or cached approved packs are available.
- Use `user_provided_asset` before web search or LLM generation when the user
  has provided reference or production-ready assets with usable rights.
- Use `web_or_marketplace_search` when no local/user asset satisfies the
  contract and the source policy allows online discovery.
- Use `existing_3d_source_asset` when a licensed model, scene, material, or
  animation pack can accelerate Blender-based render-to-2D production.
- Use `motion_video_source` when a local, user-provided, licensed web, or
  marketplace video/reference can become a frame animation through
  `motion-video-to-sprite-animation`.
- Use `ai_video_source` when no suitable licensed motion source exists and
  short organic motion can be generated, extracted, visually accepted, and
  imported as 2D frames.
- Use `3d_render_capture` or `engine_capture` when repeatable camera angle,
  scale, or action control is more important than AI-video variation.
- Use `adapt_existing_asset` when assets are available but need resizing,
  palette/style normalization, slicing, pivots, metadata, or atlas packing.
- Use `llm_image_generation` when no suitable licensed source exists or style
  specificity is high.
- Use `3d_assisted_render` when camera/angle consistency or many 2D renders are
  better produced from 3D.
- Use `placeholder_only` only when the caller explicitly accepts non-final art.

State progression gates:

```text
draft
-> validated                    every asset group has strategy, fallback, license gate, routes
-> needs_revision               strategy conflicts with style, runtime, budget, or license
-> blocked_by_preferences       human style/source preferences conflict or are missing in strict mode
-> blocked_by_license_policy    required license policy cannot be satisfied
-> blocked_by_budget            paid asset strategy exceeds declared budget
```

Repair routing: unclear style/source preference returns to
`art-direction-input-contract`; missing assets route to `asset-registry`;
license policy conflicts route to `asset-license-provenance-qa`; unavailable
tools route to `production-tool-capability-registry`.

All source paths that produce bitmap images must ultimately route through
`image-generation-contract` in registration mode so the downstream consumer
receives `.allforai/game-design/art/image-generation/accepted-image-manifest.json`
entries with `consumer_ready: true`, not raw file paths.

## Completion Conditions

Return `COMPLETED` when all assets have source strategy, fallback, license gate,
adaptation route, and handoff route. Return `FAILED_VALIDATION` when source
strategy cannot satisfy license/style/runtime constraints.
