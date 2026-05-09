# Art Preview QA Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Runs cross-asset visual QA over generated art, previews, screenshots, and
manifests. It classifies defects and routes repair to the correct upstream
skill, including `image-generation-contract` for generated-image defects.

## Input Contract

Required: at least one manifest or preview path. Optional:
`asset-registry.json`, `ui-registry.json`, `image-generation-report.json`,
screenshots/previews.

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
  "evidence": {"previews": [], "screenshots": []},
  "output_root": ".allforai/game-design/art"
}
```

Supported modes: `validate`, `validate_artifacts_only`, `validate_visuals`.

## Automatic Validation

Check existence, naming, style, crop, alpha, small-size readability, playfield/UI
occlusion, manifest consistency, and downstream root-cause routing.

For image-generation defects, emit feedback compatible with
`.allforai/game-design/art/image-generation/image-feedback-report.json`. For
atlas or runtime defects, route to `atlas-packaging` or `runtime-import-check`.
For semantic/spec defects, route to the producer skill without regenerating
images.

## Completion Conditions

Return `COMPLETED` when no blocker/major issues remain. Return
`FAILED_VALIDATION` for blocker defects and include repair targets.
