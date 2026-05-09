# Asset Pack Search Spec Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Defines how to search for existing 2D and 3D art assets or asset packs. It
captures search queries, target platforms, candidate result fields, ranking
criteria, budget, license requirements, style fit, and downstream adaptation
needs.

This skill specifies the search and result contract. It does not treat found
assets as usable until license/provenance QA passes.

## Input Contract

Required: asset source strategy spec and art direction input contract.

Optional: visual style tokens, target runtime, budget, preferred marketplaces,
forbidden sources, asset registry, existing local assets, and human references.

## Output Contract

Writes:

- `.allforai/game-design/art/sourcing/asset-pack-search-spec.json`
- `.allforai/game-design/art/sourcing/asset-pack-search-results.json`
- `.allforai/game-design/art/sourcing/asset-pack-search-report.json`

Search specs must include `search_id`, `asset_group`, `queries`, `platforms`,
`required_asset_types`, `source_dimension`, `style_constraints`,
`runtime_format_preferences`, `production_source_preferences`,
`license_requirements`, `budget`, `ranking_weights`, `rejection_rules`, `state`,
and `consumer_refs`.

Candidate results must include `candidate_id`, `title`, `source_url`,
`source_platform`, `author_or_publisher`, `license_claim`, `price`,
`formats`, `source_dimension`, `asset_count`, `preview_refs`, `style_match_score`,
`runtime_fit_score`, `adaptation_cost`, `license_risk`, `provenance_status`,
`selected`, and `next_skill`.

Allowed `source_dimension` values: `2d`, `3d`, `mixed`, `audio_visual`,
`unknown`.

3D candidate results must additionally include `source_3d_kind`,
`render_to_2d_purpose`, `tool_requirements`, `runtime_allowed`,
`runtime_exclusion_reason`, and `target_2d_outputs`.

Allowed states: `draft`, `searched`, `candidates_ranked`, `needs_revision`,
`blocked_by_no_candidates`, `blocked_by_search_access`.

Downstream consumers: `asset-license-provenance-qa`,
`existing-asset-adaptation-spec`, `asset-pack-integration-qa`,
`artifact-handoff-contract`, and `engine-ready-art-output-contract`.

## Invocation Contract

```json
{
  "skill": "game-art/asset-pack-search-spec",
  "mode": "search_spec_validate",
  "input_paths": {
    "source_strategy": ".allforai/game-design/art/sourcing/asset-source-strategy-spec.json",
    "art_direction": ".allforai/game-design/art/art-direction-input-contract.json",
    "visual_style_tokens": ".allforai/game-design/art/visual-style-tokens.json"
  },
  "output_root": ".allforai/game-design/art/sourcing"
}
```

Supported modes: `search_spec_validate`, `register_search_results`,
`validate_existing`, `repair_existing`.

## Automatic Validation

Check that each selected candidate has a source URL, publisher, license claim,
format list, preview evidence, price/budget fit, style fit, adaptation estimate,
and license QA route. No candidate may become selected for runtime integration
without `asset-license-provenance-qa`.

Common platforms may include official marketplaces, open asset libraries,
creator stores, project-local asset folders, and user-provided bundles. Search
results must record exact source and retrieval date if discovered online by a
caller with web access.

3D existing assets are valid search targets when they are used as production
sources for 2D output. Typical candidates include `.blend`, `.fbx`, `.glb`,
`.gltf`, `.obj`, texture folders, material libraries, animation clips, lighting
rigs, camera rigs, and scene/blockout files. These must route through
`existing-asset-adaptation-spec`, then `3d-source-asset-spec`, before
`render-to-2d-asset-generation`.

Ranking rules:

- Reject candidates with unclear license, missing source, or no modification
  right when adaptation is required.
- Prefer complete packs over loose assets when consistency matters.
- Prefer formats already compatible with target runtime/export profile.
- For 3D production sources, prefer formats Blender CLI can open or convert.
- Penalize style mismatch, missing animation metadata, and high adaptation cost.
- Do not scrape or ingest assets from sources that forbid reuse.

State progression gates:

```text
draft
-> searched                    queries/platforms/results recorded
-> candidates_ranked           candidates scored and selected/rejected with reasons
-> needs_revision              search spec too broad or candidates conflict with constraints
-> blocked_by_no_candidates    no candidate satisfies license/style/runtime gates
-> blocked_by_search_access    required search source is unavailable
```

Repair routing: bad queries repair here; no candidates route to
`asset-source-strategy-spec`; unclear license routes to
`asset-license-provenance-qa`; runtime format gaps route to
`engine-export-profile`.

## Completion Conditions

Return `COMPLETED` when ranked candidates and next routes are recorded. Return
`FAILED_VALIDATION` when no candidate can proceed to license/provenance QA.
