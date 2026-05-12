---
name: game-design-40-qa-game-design-final-closure-qa
description: Internal bundled meta-skill module for game-design/40-qa/game-design-final-closure-qa; use within generated bootstrap node-specs when this exact contract is selected.
---

# Game Design Final Closure QA Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Validates whether a complete game product design is closed enough for art,
audio, UI, engine import, implementation, and testing work to proceed without
relying on conversation state or unstated assumptions.

## Input Contract

Required: game-design registry, player experience contract, pillars, core loop,
mechanics, progression, economy, level, combat, content, narrative, generated
tables, generated level plans, enemy list, item/skill list, and all selected QA
reports.

Optional: game-systems, game-balance, game-combat, game-level, game-narrative,
game-content, game-onboarding, game-liveops, game-ui, game-art, game-audio, and
engine-import handoff artifacts.

## Output Contract

Writes `.allforai/game-design/design/game-design-final-closure-qa-report.json`.

The report includes `status`, `validated_at`, `input_paths`,
`closed_contracts`, `open_contracts`, `cross_skill_traceability`,
`blocking_issues`, `non_blocking_warnings`, `repair_plan`, and
`handoff_readiness`.

Each issue includes `issue_id`, `severity`, `source_skill`, `source_artifact`,
`requirement_id`, `expected`, `actual`, `evidence_paths`, `root_cause`,
`repair_target`, `blocks_downstream`, and `consumer_refs`.

Allowed root causes: `missing_contract`, `incomplete_traceability`,
`conflicting_design_rule`, `unvalidated_balance`, `missing_content_ownership`,
`missing_asset_requirement`, `missing_ui_requirement`, `missing_audio_requirement`,
`missing_engine_import_requirement`, `verification_unavailable`, `unknown`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_evidence`, `failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-design/game-design-final-closure-qa",
  "mode": "validate",
  "input_paths": {
    "registry": ".allforai/game-design/design/game-design-registry.json",
    "core_loop": ".allforai/game-design/design/core-game-loop-spec.json",
    "content_taxonomy": ".allforai/game-design/content/content-taxonomy-spec.json",
    "data_manifest": ".allforai/game-design/data/game-data-table-manifest.json",
    "qa_reports": ".allforai/game-design/design/*-qa-report.json"
  },
  "output_root": ".allforai/game-design/design"
}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Check that every registry entity has ownership across design, data, art, UI,
audio, level/content placement, runtime import, and verification where relevant.
Check that each player-facing loop has a goal, action, feedback, reward,
failure/retry path, and next-step motivation. Check that all blocking findings
from upstream QA reports are resolved or routed to a concrete repair target.

If required evidence or an executable validation path is unavailable, return
`blocked_by_missing_evidence` or `FAILED_VALIDATION`; do not use substitute
evidence or mark closure based on plausibility.

Repair routing: missing design rules route to the owning `game-design` child;
numeric issues route to `game-balance`; combat issues route to `game-combat`;
level/content placement issues route to `game-level` or `game-content`; story
issues route to `game-narrative`; player learning issues route to
`game-onboarding`; asset issues route to `game-art`; UI issues route to
`game-ui`; audio issues route to `game-audio`; import/runtime gaps route to the
target engine handoff skill.

## Completion Conditions

Return `COMPLETED` when all required contracts are traceable, validated, and
handoff-ready with no blocking issue. Return `FAILED_VALIDATION` when any
required contract is missing, contradictory, unverified, or lacks a repair
target.
