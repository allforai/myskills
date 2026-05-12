---
name: game-level-40-qa-level-playability-qa
description: Internal bundled meta-skill module for game-level/40-qa/level-playability-qa; use within generated bootstrap node-specs when this exact contract is selected.
---

# Level Playability QA Skill

> Internal sub-skill for game-level pipelines. Status: bundled, inactive, not wired.

## Overview

Validates level blockouts for reachability, pacing, collisions, objectives,
enemy/resource placement, camera bounds, and known failure cases.

## Input Contract

Required: level blockout or layout spec. Optional: runtime screenshots,
tileset/prop manifests, combat/progression specs, and level difficulty
validation QA report.

## Output Contract

Writes `.allforai/game-design/levels/level-playability-qa-report.json`.

Issues must include `level_id`, `severity`, `root_cause`, `evidence`,
`repair_target`, and `blocks_progression`.

Allowed root causes: `level_flow`, `level_layout`, `blockout_generation`,
`tileset_art`, `prop_art`, `systems_balance`, `runtime_tooling`, `unknown`.

Downstream consumers: `level-layout-spec`, `level-blockout-generation`,
`balance-sanity-qa`, art QA, runtime map import, and playtest QA.

## Invocation Contract

```json
{"skill":"game-level/level-playability-qa","mode":"validate","input_paths":{"level_layout_spec":".allforai/game-design/levels/level-layout-spec.json","blockout_manifest":".allforai/game-design/levels/blockouts/level-blockout-manifest.json","difficulty_validation":".allforai/game-design/levels/level-difficulty-validation-qa-report.json"},"output_root":".allforai/game-design/levels"}
```

Supported modes: `validate`, `validate_artifacts_only`, `validate_previews`.

## Automatic Validation

Check graph reachability, soft locks, invalid collisions, missing objectives,
unfair hazard placement, route readability, camera coverage, and repair target
classification.
If difficulty validation reports missing probes, unreadable danger, excessive
retry cost, or unverified execution windows, playability QA must keep the level
blocked until the relevant artifact/probe exists.

Repair routing: do not route visual tile/prop defects to level layout. Route them to
`art-preview-qa` or the relevant art producer; route structural dead ends to
`level-layout-spec`.

## Completion Conditions

Return `COMPLETED` when no blocker/major playability issues remain. Return
`FAILED_VALIDATION` with repair targets for blockers.
