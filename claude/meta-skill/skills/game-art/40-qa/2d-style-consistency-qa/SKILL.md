# 2D Style Consistency QA Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Validates that 2D game art reads as one coherent visual system across
characters, frame animations, skeletal animation previews, tiles, props,
backgrounds, UI icons, portraits, item art, and VFX.

This is a lightweight indie-game QA pass focused on practical consistency:
palette, outline, silhouette, scale, camera angle, resolution, lighting, UI/game
separation, small-size readability, and runtime import readiness.

## Input Contract

Required: visual style tokens and at least one asset manifest or preview set.

Optional: art-preview QA report, atlas manifest, animation previews, UI mockups,
tileset preview maps, runtime screenshots, image-generation reports, and engine
export profile, 2D view mode, and 2D layering spec.

## Output Contract

Writes:

- `.allforai/game-design/art/qa/2d-style-consistency-qa-report.json`

Issues must include `issue_id`, `asset_id`, `asset_path`, `surface`,
`severity`, `style_axis`, `expected`, `actual`, `evidence`,
`root_cause`, `repair_target`, `consumer_refs`, and `blocks_runtime`.

Evidence must include at least one of `preview_path`, `runtime_screenshot_path`,
`manifest_ref`, `atlas_ref`, `measured_value`, or `visual_observation`.

Allowed root causes: `visual_style_tokens`, `image_generation`,
`animation_generation`, `tileset_generation`, `prop_generation`,
`ui_generation`, `icon_generation`, `vfx_generation`, `atlas_packaging`,
`engine_export_profile`, `2d_view_mode`, `2d_layering`, `runtime_import`, and
`unknown`.

Allowed report states: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_evidence`, `blocked_by_style_contract`,
`blocked_by_runtime_import`.

Downstream consumers: `art-preview-qa`, `runtime-import-check`,
`atlas-packaging`, `game-ui` QA, level preview QA, playtest QA, and all
image-backed art producers.

## Invocation Contract

```json
{
  "skill": "game-art/2d-style-consistency-qa",
  "mode": "validate",
  "input_paths": {
    "visual_style_tokens": ".allforai/game-design/art/visual-style-tokens.json",
    "art_preview_report": ".allforai/game-design/art/qa/art-preview-qa-report.json",
    "atlas_manifest": ".allforai/game-design/art/atlases/atlas-manifest.json",
    "engine_export_profile": ".allforai/game-design/art/export/engine-export-profile.json"
  },
  "output_root": ".allforai/game-design/art/qa"
}
```

Supported modes: `validate`, `validate_previews`, `validate_runtime_screenshots`,
`repair_targets`.

## Automatic Validation

Check these axes when evidence exists:

- palette and saturation drift,
- outline width and edge treatment,
- pixel density or brush/detail density,
- camera angle and projection,
- character/background separation,
- prop/tile/player scale consistency,
- icon and item-art visual language,
- portrait/expression identity consistency,
- animation anchor jitter and silhouette stability,
- VFX intensity relative to gameplay importance,
- UI/game art contrast and safe separation,
- scene, character, outfit, UI, and VFX layer order,
- small-size readability,
- alpha/background correctness,
- atlas/runtime import mismatches.

Severity rules:

| Severity | Meaning |
|---|---|
| `blocker` | asset cannot ship or blocks runtime import/readability |
| `major` | visible inconsistency that affects gameplay readability or identity |
| `minor` | noticeable polish issue that does not block use |
| `warning` | risk or missing evidence, no confirmed defect |

Acceptance thresholds:

- Small gameplay sprites remain readable at target runtime scale.
- Player, enemy, hazard, pickup, and interactable silhouettes are distinguishable.
- UI icons do not look like world props unless intentionally shared.
- Foreground/occlusion layers do not hide critical gameplay without a cutaway or
  transparency rule.
- Animation previews do not show anchor jitter beyond the declared tolerance.
- VFX does not exceed its gameplay importance or obscure required state changes.

State progression gates:

```text
passed
  no blocker/major issues and required evidence exists
passed_with_warnings
  only minor/warning issues remain with repair targets documented
needs_revision
  blocker/major visual consistency issues exist
blocked_by_missing_evidence
  previews, screenshots, manifests, or measured values are insufficient
blocked_by_style_contract
  visual-style tokens are missing or contradictory
blocked_by_runtime_import
  runtime screenshot/import evidence cannot be produced or parsed
```

Every blocker or major issue must include one repair target. Do not report
generic "style mismatch" without naming the failed style axis and evidence.

Repair routing: unclear or contradictory style rules return to
`visual-style-tokens`; generated-image defects route through
`image-generation-contract` and the producing skill; animation jitter routes to
`frame-animation-generation` or `skeletal-animation`; atlas spacing or bleed
routes to `atlas-packaging`; view/projection defects route to
`2d-view-mode-spec`; layer ordering, outfit masking, or foreground occlusion
defects route to `2d-layering-spec`; runtime-only scale/pivot issues route to
`engine-export-profile` or `runtime-import-check`.

## Completion Conditions

Return `COMPLETED` when no blocker/major style consistency issues remain.
Return `COMPLETED_WITH_WARNINGS` when minor style drift is documented and does
not block runtime use. Return `FAILED_VALIDATION` when assets cannot be shipped
without repair.
