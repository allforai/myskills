# Implementation Feasibility QA Skill

> Internal sub-skill for game-product pipelines. Status: bundled, inactive, not wired.

## Overview

Validates whether the product design can be implemented with the declared
engine, tools, runtime constraints, data contracts, and verification paths.

## Input Contract

Required: game-design registry and all selected product/system/content specs.

Optional: target engine, runtime stack, tool capability reports, art/audio/UI
registries, data table manifest, build/test commands, and risk notes.

## Output Contract

Writes `.allforai/game-design/product/implementation-feasibility-qa-report.json`.

Issues must include `issue_id`, `requirement_id`, `severity`, `feasibility_axis`,
`expected`, `actual`, `evidence_paths`, `root_cause`, `repair_target`,
`blocks_runtime`, and `consumer_refs`.

Allowed root causes: `engine_gap`, `tool_missing`, `data_contract_gap`,
`runtime_complexity`, `asset_pipeline_gap`, `verification_unavailable`,
`scope_exceeds_budget`, `unknown`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_evidence`, `failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-product/implementation-feasibility-qa",
  "mode": "validate",
  "input_paths": {
    "registry": ".allforai/game-design/product/game-design-registry.json",
    "content_taxonomy": ".allforai/game-design/content/content-taxonomy-spec.json",
    "data_manifest": ".allforai/game-design/data/game-data-table-manifest.json"
  },
  "output_root": ".allforai/game-design/product"
}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Check engine/runtime ownership, tool availability, data importability,
implementation complexity, and executable verification paths. If a validation
cannot run, return `blocked_by_missing_evidence` or `FAILED_VALIDATION`; do not
use proxy evidence as a substitute.

Repair routing: engine gaps route to runtime architecture; tool gaps route to
capability registry; data gaps route to `game-data-table-generation`; product
scope gaps route to the owning spec.

## Completion Conditions

Return `COMPLETED` when implementation risks are either passed or explicitly
non-blocking. Return `FAILED_VALIDATION` when a required feature lacks an
implementable or verifiable path.
