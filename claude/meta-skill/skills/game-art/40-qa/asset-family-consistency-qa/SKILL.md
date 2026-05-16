---
name: game-art-40-qa-asset-family-consistency-qa
description: Validate that generated game art works as coherent asset families, not isolated accepted images, using benchmark-driven batch review and repair routing.
---

# Asset Family Consistency QA Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive,
> art-qa invoked.

## Purpose

Single images can pass while the game still looks cheap. This skill validates
whole asset families: tiles together, characters across expressions and poses,
UI/icons as one language, VFX with gameplay feedback, and environments with
runtime readability.

## Input Contract

Required:

```text
.allforai/game-design/art/art-direction-benchmark.json
.allforai/game-design/art/asset-acceptance-criteria.json
.allforai/game-design/art/image-generation/accepted-image-manifest.json
.allforai/game-design/asset-registry.json
.allforai/game-design/art/qa/codex-visual-review.json
```

Optional:

```text
.allforai/game-design/art/qa/visual-acceptance-batches/
.allforai/game-design/art/qa/contact-sheets/
.allforai/game-design/art-style-guide.json
.allforai/game-runtime/art/engine-ready-art-manifest.json
```

If image files or contact sheets are missing, return
`blocked_by_missing_visual_evidence`.

## Output Contract

Writes:

```text
.allforai/game-design/art/qa/asset-family-consistency-report.json
.allforai/game-design/art/qa/asset-family-consistency-report.md
```

The JSON must include:

```json
{
  "status": "passed | failed | blocked",
  "family_scores": {},
  "cross_family_scores": {},
  "failed_assets": [],
  "quality_gaps": [],
  "visual_quality_gaps": [],
  "repair_routes": [],
  "feedback_report_path": ".allforai/game-design/art/image-generation/image-feedback-report.json",
  "visual_repair_loop_refs": [],
  "requires_regeneration": []
}
```

## Method

1. Group accepted images by asset family, role, rarity, state, screen, and
   runtime size.
2. Build or read contact sheets for each family. Do not judge family coherence
   from manifest rows alone.
3. Compare each family against `art-direction-benchmark.json` and
   `asset-acceptance-criteria.json`.
4. Check within-family coherence:
   palette, outline/edge treatment, shape vocabulary, camera/projection,
   material language, lighting, scale, crop, transparent margins, pivot
   implication, and runtime-size readability.
5. Check cross-family cohesion:
   UI and game world belong together, VFX does not obscure important gameplay,
   icons match item/skill rarity, characters fit environments, and backgrounds
   do not overpower interactables.
6. For every failed family, classify the root cause:
   `prompt_problem`, `model_problem`, `missing_lora`, `source_asset_mismatch`,
   `asset_spec_problem`, `runtime_size_problem`, `palette_problem`,
   `crop_or_margin_problem`, or `engine_binding_problem`.
7. Route repairs to the smallest upstream step: prompt/model routing, LoRA,
   mcp-image-batch edit mode, source adaptation, atlas packaging, or runtime
   binding.

## Repair And Revalidation Loop

Family consistency failures must join the same visual repair loop used by
`visual-acceptance-review`; they must not stop at a report.

Loop:

1. For every failed asset or family, write feedback to
   `.allforai/game-design/art/image-generation/image-feedback-report.json`
   unless the root cause is not image-owned.
2. Route the failure to the smallest owner:
   - `prompt_problem`, `model_problem`, `missing_lora`, or
     `runtime_size_problem` -> `image-generation-contract` and
     `batch-image-generation` or LoRA repair;
   - `source_asset_mismatch` -> `asset-source-strategy-spec`,
     `asset-pack-search-spec`, or `existing-asset-adaptation-spec`;
   - `asset_spec_problem` -> the producing art spec/generation skill;
   - `palette_problem`, `crop_or_margin_problem` -> image edit or atlas repair;
   - `engine_binding_problem` -> `runtime-import-check` or frontend asset
     binding, not image regeneration by default.
3. Regenerate, edit, adapt, repack, or rebind only the affected family.
4. Rebuild the affected contact sheets or preview maps.
5. Rerun Codex CLI review for the affected visual batches.
6. Rerun this family consistency QA on the repaired evidence.
7. Append the iteration to
   `.allforai/game-design/art/qa/visual-repair-loop-report.json` and
   `.allforai/game-design/art/qa/visual-repair-loop-report.md`.

Default budget: 3 repair attempts per affected family. If the family still
fails after budget exhaustion, return `FAILED_VALIDATION` with the unresolved
`quality_gaps` or `visual_quality_gaps`. Do not return `passed` with repair
routes still open.
Do not return `passed` with repair routes still open.

## Automatic Validation

Reject with `FAILED_VALIDATION` when:

- a report passes using manifest-only or filename-only review;
- any active family has no contact sheet or equivalent visual evidence;
- average family score is used to hide failed critical assets;
- visual mismatch is reported as non-blocking for art-heavy games;
- repair routes do not identify the upstream node to rerun;
- failed assets do not include file paths and asset IDs.
- failed family findings were not written to
  `image-feedback-report.json` or another owner-specific feedback report;
- repaired families were not revalidated with fresh contact sheets, rerun
  Codex CLI review, and a new family consistency report.

## Completion Conditions

Return `COMPLETED` only when every active family has visual evidence, every
family scores at least 4/5 against benchmark criteria, no `quality_gaps` or
`visual_quality_gaps` remain, all failed candidates have either been repaired
and revalidated or remain `FAILED_VALIDATION`, and the visual repair loop report
records every repair attempt. Existing files are not sufficient.
