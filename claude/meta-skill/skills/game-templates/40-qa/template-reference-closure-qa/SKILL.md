---
name: game-templates-40-qa-template-reference-closure-qa
description: Internal bundled meta-skill module for game-templates/40-qa/template-reference-closure-qa; use within generated bootstrap node-specs when this exact contract is selected.
---

# Template Reference Closure QA Skill

> Internal sub-skill for game-templates pipelines. Status: bundled, inactive, not wired.

## Overview

Validates that template schemas and instances are closed over source refs,
resource refs, consumers, inheritance, defaults, and repair targets.

## Input Contract

Required: template registry, schemas, inheritance spec, reference map, and
template instances.

Optional: design doc, balance/data manifests, art manifest, UI/audio manifests,
frontend/runtime contracts, and existing QA reports.

## Output Contract

Writes `.allforai/game-templates/qa/template-reference-closure-qa-report.json`.

Findings must include `finding_id`, `template_id`, `template_kind`,
`contract_axis`, `severity`, `expected`, `actual`, `evidence_paths`,
`repair_target`, `blocks_runtime`, and `state`.

Allowed axes: `schema_gap`, `missing_source_ref`, `missing_resource_ref`,
`missing_consumer`, `orphan_template`, `cycle`, `illegal_override`,
`default_gap`, `runtime_load_gap`.

Allowed states: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_artifacts`, `failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-templates/template-reference-closure-qa",
  "mode": "validate",
  "input_paths": {
    "registry": ".allforai/game-templates/template-registry.json",
    "schemas": ".allforai/game-templates/schemas",
    "instances": ".allforai/game-templates/instances",
    "reference_map": ".allforai/game-templates/template-reference-map.json"
  },
  "output_root": ".allforai/game-templates/qa"
}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Check schema compliance, source traceability, ref resolution, inheritance
cycles, illegal overrides, orphan instances, runtime consumers, and explicit
defaults. Do not mark closure passed if required upstream evidence is missing.

Repair routing: each finding must name the owning skill or artifact that can
repair it.

## Completion Conditions

Return `COMPLETED` when templates are closed and consumer-ready. Return
`FAILED_VALIDATION` when required refs, schemas, inheritance, or consumers are
not closed.
