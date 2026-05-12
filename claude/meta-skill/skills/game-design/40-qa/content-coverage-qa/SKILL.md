---
name: game-design-40-qa-content-coverage-qa
description: Internal bundled meta-skill module for game-design/40-qa/content-coverage-qa; use within generated bootstrap node-specs when this exact contract is selected.
---

# Content Coverage QA Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Validates that game design content requirements are covered by data, art, UI,
audio, level, narrative, and runtime ownership.

## Input Contract

Required: content taxonomy and game-design registry.

Optional: data table manifest, level blockout manifest, enemy roster, item/skill
set, art asset registry, UI registry, audio registry, and narrative specs.

## Output Contract

Writes `.allforai/game-design/content/content-coverage-qa-report.json`.

Issues must include `issue_id`, `content_id`, `severity`, `coverage_axis`,
`expected`, `actual`, `root_cause`, `repair_target`, `blocks_runtime`, and
`consumer_refs`.

Allowed root causes: `missing_data`, `missing_art`, `missing_ui`,
`missing_audio`, `missing_level`, `missing_narrative`, `missing_runtime_owner`,
`orphan_content`, `unknown`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_manifest`, `failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-design/content-coverage-qa",
  "mode": "validate",
  "input_paths": {
    "content_taxonomy": ".allforai/game-design/content/content-taxonomy-spec.json",
    "registry": ".allforai/game-design/design/game-design-registry.json"
  },
  "output_root": ".allforai/game-design/content"
}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Check that every required content item has source system refs, data refs, owner
skill refs, and downstream asset/UI/audio/runtime routes. Optional content must
be explicitly marked optional.

Repair routing: missing taxonomy routes to `content-taxonomy-spec`; missing data
routes to `design-data-table-generation`; missing art/UI/audio routes to the
corresponding downstream registry or generation skill.

## Completion Conditions

Return `COMPLETED` when required content is fully owned. Return
`FAILED_VALIDATION` when required content lacks a runtime-critical owner.
