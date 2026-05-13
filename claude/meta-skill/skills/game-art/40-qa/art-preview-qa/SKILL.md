---
name: game-art-40-qa-art-preview-qa
description: Internal bundled meta-skill module for game-art/40-qa/art-preview-qa; use within generated bootstrap node-specs when this exact contract is selected.
---

# Art Preview QA Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Runs cross-asset visual QA over generated art, previews, screenshots, and
manifests. It classifies defects and routes repair to the correct upstream
skill, including `image-generation-contract` for generated-image defects.

## Input Contract

Required: accepted image manifest plus actual image evidence for generated or
adapted bitmap assets. Evidence may be per-asset PNG/JPG/WebP files, contact
sheets, preview maps, animation previews, UI mockup previews, or runtime
screenshots. Optional: `asset-registry.json`, `ui-registry.json`,
`image-generation-report.json`.

Manifest-only review is not allowed. If the QA agent did not inspect actual
images or generated previews, return `blocked_by_missing_visual_evidence`.

## Output Contract

Writes `.allforai/game-design/art/qa/art-preview-qa-report.json` with issues,
evidence, severity, root cause, and repair target.

Each issue must include `issue_id`, `asset_id`, `producer_skill`,
`consumer_skill`, `severity`, `root_cause`, `evidence`, `repair_target`,
`requested_action`, and `blocks_runtime`.

Allowed root causes: `image_generation`, `prompt_contract`, `asset_spec`,
`style_tokens`, `atlas_packaging`, `runtime_import`, `downstream_spec`, and
`unknown`.

## Invocation Contract

```json
{
  "skill": "game-art/art-preview-qa",
  "mode": "validate",
  "input_paths": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "ui_registry": ".allforai/game-design/ui/ui-registry.json",
    "image_generation_report": ".allforai/game-design/art/image-generation/image-generation-report.json"
  },
  "evidence": {
    "images": [],
    "contact_sheets": [],
    "previews": [],
    "screenshots": []
  },
  "output_root": ".allforai/game-design/art"
}
```

Supported modes: `validate`, `validate_artifacts_only`, `validate_visuals`.

## Automatic Validation

Check existence, naming, style, crop, alpha, small-size readability, playfield/UI
occlusion, manifest consistency, and downstream root-cause routing. For
generated or adapted bitmap assets, `validate_artifacts_only` may only report
schema/path defects; it cannot pass visual acceptance.

The report must include `visual_evidence_inspected: true`, a list of inspected
image/contact-sheet/preview paths, and a per-asset or per-task verdict. A report
that only verifies fields, paths, or semantic consistency must return
`blocked_by_missing_visual_evidence`.

For image-generation defects, emit feedback compatible with
`.allforai/game-design/art/image-generation/image-feedback-report.json`. For
atlas or runtime defects, route to `atlas-packaging` or `runtime-import-check`.
For semantic/spec defects, route to the producer skill without regenerating
images.

## Completion Conditions

Return `COMPLETED` when actual visual evidence was inspected and no
blocker/major issues remain. Return `FAILED_VALIDATION` for blocker defects and
include repair targets. Return `blocked_by_missing_visual_evidence` when images
or previews are missing, unreadable, stale, or not inspected.
