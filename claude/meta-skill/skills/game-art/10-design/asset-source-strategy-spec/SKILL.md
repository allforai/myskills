---
name: game-art-10-design-asset-source-strategy-spec
description: Internal bundled meta-skill module for game-art/10-design/asset-source-strategy-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Asset Source Strategy Spec Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Chooses the source strategy for each art asset or asset group. It decides
whether to use LLM image generation, 3D-assisted rendering, existing asset
packs, user-provided files, adapted existing assets, or mixed sourcing.

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
`source_strategy`, `selection_reason`, `license_requirements`,
`quality_requirements`, `adaptation_requirements`, `fallback_strategy`,
`downstream_skill_refs`, `handoff_requirements`, `state`, and `consumer_refs`.

Allowed source strategies: `llm_image_generation`, `3d_assisted_render`,
`existing_asset_pack`, `existing_3d_source_asset`, `user_provided_asset`,
`adapt_existing_asset`, `hybrid`, `placeholder_only`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_preferences`, `blocked_by_license_policy`, `blocked_by_budget`.

Downstream consumers: `asset-pack-search-spec`, `asset-license-provenance-qa`,
`existing-asset-adaptation-spec`, `image-generation-contract`,
`render-to-2d-asset-generation`, `artifact-handoff-contract`,
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

Strategy rules:

- Use `existing_asset_pack` for broad, coherent sets such as UI packs, tilesets,
  icons, VFX packs, or complete character packs when license and style fit.
- Use `existing_3d_source_asset` when a licensed model, scene, material, or
  animation pack can accelerate Blender-based render-to-2D production.
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

## Completion Conditions

Return `COMPLETED` when all assets have source strategy, fallback, license gate,
adaptation route, and handoff route. Return `FAILED_VALIDATION` when source
strategy cannot satisfy license/style/runtime constraints.
