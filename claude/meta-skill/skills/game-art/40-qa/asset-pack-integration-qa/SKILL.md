# Asset Pack Integration QA Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Validates whether searched, licensed, adapted, or user-provided asset packs are
actually usable as a coherent part of the game art pipeline. It checks pack
completeness, style fit, dimensions, animation completeness, tileability, UI
readability, metadata, atlas readiness, runtime import, license carry-through,
and handoff integrity.

## Input Contract

Required: adaptation manifest or registered existing asset manifest, license
provenance QA report, and artifact handoff entries.

Optional: visual style tokens, atlas manifests, runtime import report, UI
layout, tileset spec, animation state machine spec, and preview screenshots.

## Output Contract

Writes:

- `.allforai/game-design/art/sourcing/asset-pack-integration-qa-report.json`

Issues must include `issue_id`, `asset_id`, `candidate_id`, `severity`,
`qa_axis`, `expected`, `actual`, `evidence_paths`, `root_cause`,
`repair_target`, `blocks_runtime`, and `consumer_refs`.

Allowed root causes: `license_provenance`, `search_selection`,
`asset_adaptation`, `style_mismatch`, `metadata_missing`, `atlas_packaging`,
`runtime_import`, `handoff_contract`, `source_asset`, and `unknown`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_license`, `blocked_by_missing_assets`, `blocked_by_runtime_import`.

Downstream consumers: `artifact-handoff-contract`, `atlas-packaging`,
`2d-style-consistency-qa`, `runtime-import-check`,
`engine-ready-art-output-contract`, UI/level/runtime implementation, and
playtest QA.

## Invocation Contract

```json
{
  "skill": "game-art/asset-pack-integration-qa",
  "mode": "validate",
  "input_paths": {
    "adaptation_manifest": ".allforai/game-design/art/sourcing/existing-asset-adaptation-manifest.json",
    "license_report": ".allforai/game-design/art/sourcing/asset-license-provenance-qa-report.json",
    "handoff_contract": ".allforai/game-design/art/handoff/artifact-handoff-contract.json"
  },
  "output_root": ".allforai/game-design/art/sourcing"
}
```

Supported modes: `validate`, `validate_previews`, `validate_runtime_evidence`,
`repair_targets`.

## Automatic Validation

Check these axes when evidence exists:

- license/provenance still passes after adaptation,
- pack contains required asset categories,
- naming and IDs match `asset-registry`,
- dimensions, pivots, anchors, alpha, and atlas grouping are consistent,
- animation frames and state refs are complete,
- tiles repeat and include collision/walkability metadata,
- UI assets fit layout and remain readable,
- style matches visual tokens or differences are explicitly accepted,
- artifact handoff entries are ready for declared consumers,
- runtime import evidence exists for engine-facing assets.

State progression gates:

```text
passed
  no blocker/major issues and license/runtime evidence exists
passed_with_warnings
  only minor issues remain and limits are explicit
needs_revision
  style, metadata, pack completeness, or handoff issue remains
blocked_by_license
  license/provenance no longer passes
blocked_by_missing_assets
  required pack contents or source files are absent
blocked_by_runtime_import
  import validation failed or could not run
```

Repair routing: license failures route to `asset-license-provenance-qa`; bad
candidate choice routes to `asset-pack-search-spec`; adaptation defects route to
`existing-asset-adaptation-spec`; handoff gaps route to
`artifact-handoff-contract`; runtime failures route to `runtime-import-check`;
style mismatches route to `2d-style-consistency-qa`.

## Completion Conditions

Return `COMPLETED` when selected/adapted assets are licensed, coherent,
handoff-ready, and runtime-import validated. Return `FAILED_VALIDATION` when
license, pack completeness, handoff, or runtime import blocks use.
