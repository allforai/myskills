---
name: game-art-20-spec-character-layer-sheet
description: Internal bundled meta-skill module for game-art/20-spec/character-layer-sheet; use within generated bootstrap node-specs when this exact contract is selected.
---

# Character Layer Sheet Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill converts a character asset into a layer-sheet specification for
rigging, skeletal animation, frame animation, expression sets, and outfit/skin
variants. It decides which body and accessory parts must be separated, how they
should be named, where pivots can be placed, and how generated layer-sheet
images are validated and repaired.

This is not a simple character image generator. It is a structured
decomposition workflow:

```text
asset registry + character context + motion needs
→ part decomposition plan
→ layer sheet image spec/prompt
→ generated or referenced layer sheet
→ deterministic + visual validation
→ repair loop
→ stable layer contract for downstream animation
```

## Scope

Use this skill when a downstream art flow needs separated character parts.

In scope:
- character part decomposition,
- layer naming and z-order,
- pivot hint placement,
- layer sheet prompt/spec generation,
- optional generated image validation,
- repair instructions for missing, merged, or unusable parts,
- automated fallback when full separation is not feasible.

Out of scope:
- final polished character art,
- skeletal hierarchy or animation timelines,
- frame animation generation,
- manual paint cleanup,
- human approval.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| Asset registry or asset list | `asset_id`, `name`, `file_prefix`, `type` | Return `UPSTREAM_DEFECT`; no target character exists. |
| Character context | gameplay role, target view, art style | Infer safe defaults if possible; otherwise use generic character defaults. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/game-design/asset-registry.json` | `assets[].asset_id`, `file_prefix`, `type`, `paths` | Use caller-provided asset list. |
| `.allforai/game-design/systems/motion-design.json` | animations, key poses, body focus | Use role-based default part list. |
| `.allforai/game-design/art-style-guide.json` | style, dimension, proportions, visual tone | Use neutral 2D character assumptions. |
| Existing character reference image | silhouette, costume, proportions | Generate prompt/spec without relying on external reference. |
| Existing layer sheet image | part layout | Validate and repair if usable. |

### Normalized input

```json
{
  "schema_version": "1.0",
  "assets": [
    {
      "asset_id": "<stable id>",
      "name": "<display name>",
      "file_prefix": "<stable prefix>",
      "gameplay_role": "player | enemy | boss | npc | mascot | prop_character | generic_character",
      "target_view": "front | side | three_quarter | top_down | isometric",
      "style": "cartoon | realistic | hand_drawn | vector | unknown",
      "scale_class": "small | normal | boss | ui"
    }
  ],
  "motion_focus": [
    {
      "asset_id": "<asset id>",
      "required_body_focus": ["weapon_arm", "head", "torso"]
    }
  ],
  "output_root": ".allforai/game-design"
}
```

## Decomposition Rules

Layer decomposition must serve animation and downstream editing, not anatomy for
its own sake.

### Baseline humanoid part list

Use this list for player, enemy, boss, NPC, and mascot characters unless the
design makes a part irrelevant:

```json
[
  "head",
  "neck",
  "torso",
  "pelvis",
  "upper_arm_l",
  "forearm_l",
  "hand_l",
  "upper_arm_r",
  "forearm_r",
  "hand_r",
  "upper_leg_l",
  "lower_leg_l",
  "foot_l",
  "upper_leg_r",
  "lower_leg_r",
  "foot_r",
  "hair_front",
  "hair_back",
  "weapon",
  "accessory"
]
```

### Add parts when needed

Add optional parts when the character design or motion plan requires them:
- `tail`,
- `wing_l`, `wing_r`,
- `cape`,
- `shield`,
- `hat`,
- `horn_l`, `horn_r`,
- `ear_l`, `ear_r`,
- `eye_l`, `eye_r`,
- `mouth`,
- `fx_anchor`.

### Merge parts when safe

Merge parts when they never move independently:
- merge `neck` into `torso` for very small characters,
- merge hands into forearms for tiny sprites,
- merge legs for static NPC busts,
- merge hair into head if there is no secondary motion.

Every merge must be recorded in `merged_parts[]` with a reason.

## Creative Workflow

| Stage | Purpose | Main output |
|---|---|---|
| 1. Select characters | Choose assets that need layer sheets. | `selected_assets[]` |
| 2. Read motion needs | Identify which body parts must move. | `motion_requirements[]` |
| 3. Decompose parts | Create part list, z-order, pivot hints. | `parts[]` |
| 4. Write layer sheet spec | Produce prompt and layout rules. | `layer_sheet_prompt` |
| 5. Generate or register image | Use available image tool or existing file. | `layer_sheet.path` |
| 6. Validate image | Check separation, completeness, naming, usability. | `visual_validation` |
| 7. Repair | Modify prompt/spec and regenerate or mark fallback. | `repair_log[]` |
| 8. Accept | Write final layer contract. | `acceptance` |

## Layer Sheet Image Specification

Filename:

```text
.allforai/game-design/art/layers/{file_prefix}_layer_sheet.png
```

Image requirements:
- transparent or flat neutral background,
- one character per sheet,
- body parts separated with clear whitespace,
- consistent scale across all parts,
- no labels baked into the image,
- no shadows connecting separate parts,
- no overlapping parts unless explicitly marked as a stack,
- costume details stay attached to the correct body part,
- hands/feet/weapon parts are large enough for pivot placement,
- generated at 2048x2048 minimum for normal characters.

Prompt requirements:
- state the exact part list,
- request separated components arranged in rows,
- request consistent lighting and style,
- forbid text, labels, motion blur, cropped limbs, and merged hands/weapons,
- include target view and style.

## Image Generation Upstream Contract

When generating a layer sheet image, follow
`game-art/30-generate/image-generation-contract/SKILL.md`.

Use normalized image requests with `purpose=layer_sheet` and
`generation_profile.task_type=layer_sheet`. The request must use
`prompt_template=layer_sheet_prompt` and a model profile that supports controlled
component separation. It must include exact part list, target view, style source,
output path, positive prompt, negative prompt, part-separation acceptance checks,
crop checks, pivot feasibility checks, and `downstream_feedback.enabled=true`.

If skeletal animation, image slicing, rig planning, or visual QA reports
`MISSING_REQUIRED_PART`, `MERGED_PARTS`, `CROPPED_SUBJECT`, `WRONG_VIEW`,
`WRONG_SCALE`, or `STYLE_DRIFT`, process the downstream feedback through
`image-generation-contract`. Regenerate the layer sheet when the root cause is
`image_generation` or `prompt_contract`.

## Automatic Validation

Run deterministic checks:

1. Every selected asset has `asset_id`, `file_prefix`, and part list.
2. Every `part_id` is unique per asset.
3. Every part has `z_order`, `pivot_hint`, and `required` flag.
4. Every required motion focus maps to at least one part.
5. Every layer sheet path starts with `file_prefix`.
6. Every merged part has a reason.
7. Every optional missing part is either not needed or has a fallback.

Run visual validation when a layer sheet image exists:

1. Required major body parts are visible.
2. Parts are separated and not fused.
3. No important part is cropped.
4. Background does not interfere with transparency extraction.
5. Left/right mirrored parts are distinguishable.
6. Weapon/accessory parts are not merged into hands unless intentionally merged.
7. Part sizes are plausible relative to the character.
8. Pivot placement appears feasible.

If visual validation fails, repair the prompt/spec and regenerate up to 3 times.
If it still fails, mark the asset `automation_limited` and provide a simplified
part list that downstream animation can still consume.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/systems/layer-sheet-plan.json` | yes | Canonical part list, pivots, image paths, validation. | skeletal-animation, sprite-frame-animation, expression-set. |
| `.allforai/game-design/systems/layer-sheet-report.json` | yes | Acceptance verdict, issues, repair log, next actions. | QA, diagnostics. |
| `.allforai/game-design/art/layers/*_layer_sheet.png` | when generated | Visual layer sheet. | image slicing, rig planning, visual QA. |

## Invocation Contract

Minimal invocation context:

```json
{
  "skill": "game-art/character-layer-sheet",
  "mode": "plan_generate_validate",
  "input_paths": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "motion_design": ".allforai/game-design/systems/motion-design.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json"
  },
  "asset_filter": {
    "asset_ids": [],
    "asset_types": ["character", "actor_3d"]
  },
  "generation": {
    "image_generation_available": true,
    "vision_validation_available": true,
    "max_repair_attempts": 3
  },
  "output_root": ".allforai/game-design"
}
```

Supported modes:

| Mode | Behavior |
|---|---|
| `plan_only` | Produce decomposition and image spec only. |
| `plan_generate_validate` | Produce plan, generate/register image, validate, repair, and write verdict. |
| `validate_existing` | Validate an existing layer sheet against the plan. |

Return statuses:

| Status | Meaning | Caller action |
|---|---|---|
| `COMPLETED` | Layer sheet plan and validation pass. | Continue downstream. |
| `COMPLETED_WITH_LIMITS` | Simplified or automation-limited sheet exists. | Continue with limits. |
| `UPSTREAM_DEFECT` | Missing asset registry or character target. | Pause caller; fix upstream input. |
| `FAILED_VALIDATION` | Repair loop exhausted without usable fallback. | Do not continue downstream. |

## Layer Sheet Plan Schema

Write `.allforai/game-design/systems/layer-sheet-plan.json`:

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO timestamp>",
  "source": {
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "motion_design": ".allforai/game-design/systems/motion-design.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json"
  },
  "characters": [
    {
      "asset_id": "<asset id>",
      "file_prefix": "<file prefix>",
      "state": "planned | spec_ready | generated | approved | needs_revision | automation_limited",
      "target_view": "front | side | three_quarter | top_down | isometric",
      "layer_sheet": {
        "path": ".allforai/game-design/art/layers/<file_prefix>_layer_sheet.png",
        "prompt": "<image generation prompt>",
        "status": "spec_only | generated | approved | automation_limited"
      },
      "parts": [
        {
          "part_id": "upper_arm_l",
          "display_name": "left upper arm",
          "z_order": 20,
          "pivot_hint": "shoulder joint center",
          "required": true,
          "required_for_animations": ["walk", "attack"],
          "mirrored_from": null
        }
      ],
      "merged_parts": [
        {
          "parts": ["neck", "torso"],
          "merged_into": "torso",
          "reason": "small sprite; neck does not move independently"
        }
      ],
      "visual_validation": {
        "validator": "llm_vision | deterministic_only | not_run",
        "verdict": "pass | fail | partial",
        "issues": [],
        "repair_attempts": 0
      }
    }
  ],
  "acceptance": {
    "verdict": "pass | pass_with_limits | fail",
    "checked_at": "<ISO timestamp>",
    "passed_checks": [],
    "failed_checks": [],
    "next_action": "<what happens next>"
  }
}
```

## Report Schema

Write `.allforai/game-design/systems/layer-sheet-report.json`:

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO timestamp>",
  "verdict": "pass | pass_with_limits | fail",
  "summary": {
    "character_count": 0,
    "generated_count": 0,
    "approved_count": 0,
    "automation_limited_count": 0
  },
  "failed_checks": [],
  "visual_issues": [],
  "repair_log": [],
  "next_actions": []
}
```

## Downstream Usage

Downstream skills must consume this output as follows:
- `skeletal-animation` uses `parts[]`, `pivot_hint`, and `layer_sheet.path`.
- `sprite-frame-animation` uses `parts[]` only when frame animation is built
  from separated layers.
- `character-expression-set` uses face-related parts such as eyes, brows, mouth.
- `art-preview-qa` uses `visual_validation` and `layer_sheet.path`.

Downstream skills must not rename parts. If a different part split is required,
they must request a new layer-sheet revision.

## Completion Conditions

This skill is complete only when:
- `layer-sheet-plan.json` exists and is valid JSON,
- `layer-sheet-report.json` exists and is valid JSON,
- report verdict is `pass` or `pass_with_limits`,
- every selected character has a part list,
- every required part has a pivot hint,
- every generated sheet has visual validation or an explicit reason validation
  was unavailable,
- every failed check has a next action.
