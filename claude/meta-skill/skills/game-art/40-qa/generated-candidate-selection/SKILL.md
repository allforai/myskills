---
name: game-art-40-qa-generated-candidate-selection
description: Select, reject, cluster, and register generated image candidates after batch generation so downstream consumers only see visually accepted, processing-ready images.
---

# Generated Candidate Selection Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive,
> image-generation downstream.

## Purpose

Raw LLM outputs are candidates, not assets. This skill filters generated or
edited images before they can enter `accepted-image-manifest.json`.

## Input Contract

Required:

```text
.allforai/game-design/art/image-generation/generated-image-files-manifest.json
.allforai/game-design/art/image-generation/image-batch-generation-plan.json
.allforai/game-design/art/image-generation/compiled-prompt-manifest.json
.allforai/game-design/art/asset-acceptance-criteria.json
.allforai/game-design/art/programmatic-art-processing-plan.json
```

Optional:

```text
.allforai/game-design/art/qa/visual-acceptance-batches/
.allforai/game-design/art/qa/codex-visual-review.json
.allforai/game-design/art/image-generation/image-feedback-report.json
.allforai/game-design/art/qa/contact-sheets/
```

If candidate files are missing or unreadable, return
`blocked_by_missing_visual_evidence`.

## Output Contract

Writes:

```text
.allforai/game-design/art/image-generation/generated-candidate-selection-report.json
.allforai/game-design/art/image-generation/generated-candidate-selection-report.md
.allforai/game-design/art/image-generation/accepted-image-manifest.json
```

The selection report must include:

```json
{
  "status": "passed | failed | blocked",
  "selected_candidates": [],
  "rejected_candidates": [],
  "cluster_summary": [],
  "coverage_shortage": [],
  "processing_readiness": [],
  "requires_additional_batch": [],
  "repair_routes": []
}
```

## Method

1. Load generated candidates and group by request id, asset family, task type,
   processing method, and acceptance target.
2. Reject obvious failures before downstream use:
   missing files, wrong dimensions, wrong alpha/background, crop, extra
   subjects, unreadable small icon/tile, merged separated parts, broken masks,
   wrong view, style drift, or direct final images where raw material was
   required.
3. Cluster similar candidates to avoid selecting multiple near-duplicates when
   variation is required.
4. Prefer candidates that are easiest for deterministic processing:
   clean layer boundaries, isolated parts, stable pivots, consistent palette,
   clear masks, simple alpha, no baked text, and correct framing.
5. Select best candidates per request/family and record why each was selected.
6. If accepted coverage is below target, set `coverage_shortage` and trigger
   another `mcp-image-batch` run through `image-batch-generation-plan`.
7. Write only accepted candidates to `accepted-image-manifest.json` with
   `consumer_ready: true` when deterministic, visual, provenance, processing,
   and downstream-readiness checks pass.

## Automatic Validation

Reject with `FAILED_VALIDATION` when:

- candidates are passed to downstream consumers without selection;
- generated files are registered as accepted only because paths exist;
- no candidate is checked against the programmatic processing plan;
- coverage shortage does not trigger another batch or remain blocking;
- rejected candidates lack rejection reasons;
- selected candidates lack processing readiness evidence;
- `accepted-image-manifest.json` contains `consumer_ready: true` for a candidate
  that has not passed selection.

## Completion Conditions

Return `COMPLETED` only when every required asset/request has enough selected
candidates or a blocking coverage shortage is reported, rejected candidates are
auditable, and accepted manifest entries are processing-ready and visually
accepted. This skill is the gate between raw LLM outputs and downstream art
consumers.
