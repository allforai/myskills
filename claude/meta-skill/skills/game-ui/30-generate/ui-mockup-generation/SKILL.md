# UI Mockup Generation Skill

> Internal sub-skill for game UI pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill produces UI mockup specifications, image prompts, generated
mockup references, and export manifests from the UI registry, layout specs, and
component state specs. It is a structured mockup pipeline, not a generic image
generation request.

## Scope

In scope:
- mockup prompt/spec generation,
- UI style token derivation from shared art direction,
- screen preview image registration,
- component sheet prompt/spec generation,
- visual repair loops,
- export manifest for downstream frontend or QA.

Out of scope:
- final frontend code,
- game-world art generation,
- gameplay implementation,
- human approval.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| `.allforai/game-design/ui/ui-registry.json` | screens, components, file prefixes | Return `UPSTREAM_DEFECT`. |
| `.allforai/game-design/ui/screen-layout-spec.json` | screen regions and breakpoints | Return `UPSTREAM_DEFECT`. |
| `.allforai/game-design/ui/component-state-spec.json` | components and required states | Return `UPSTREAM_DEFECT`. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/game-design/art-style-guide.json` | style, palette, material, typography mood | Use neutral readable game UI. |
| `.allforai/concept-contract.json` | product identity and visual promise | Use game design tone. |
| `.allforai/game-design/asset-registry.json` | icon, portrait, item refs | Use placeholder refs. |
| Existing generated mockups | screen previews | Validate and register. |
| Caller context | image generation and vision availability | Produce specs only if unavailable. |

## Generation Workflow

| Stage | Purpose | Main output |
|---|---|---|
| 1. Derive UI tokens | Palette, typography, borders, panels, icon tone. | `ui-style-tokens.json` |
| 2. Select mockup targets | Screens, states, breakpoints. | `mockup_targets[]` |
| 3. Write prompt/spec | One prompt/spec per target. | `mockup_specs[]` |
| 4. Generate or register images | Use available image tool or existing files. | `mockups/*.png` |
| 5. Validate previews | Layout fidelity, style consistency, text fit. | `visual_validation` |
| 6. Repair | Update spec/prompt and regenerate up to capped attempts. | `repair_log[]` |
| 7. Export manifest | Stable list of specs and images. | `ui-mockup-manifest.json` |

## Mockup Rules

- Mockups must respect `screen-layout-spec.json`; do not invent screen regions.
- Component visuals must respect `component-state-spec.json`.
- Shared game-art assets must be referenced by ID and path when available.
- Do not generate duplicate icon/portrait art if `asset-registry.json` already
  provides it.
- Text in generated mockups is allowed only for UI labels from specs; avoid
  decorative fake paragraphs.
- If image generation is unavailable, produce complete prompt/spec artifacts and
  mark image outputs `not_generated`.

## Image Generation Upstream Contract

Every generated UI mockup must follow
`game-art/30-generate/image-generation-contract/SKILL.md`.

Use normalized image requests with `purpose=ui_mockup`. The request must include
screen/component id, breakpoint, layout spec reference, component state
reference, style token source, output path, positive prompt, negative prompt,
layout fidelity checks, text-fit checks, playfield protection checks, and
`downstream_feedback.enabled=true`.

If UI readability QA, frontend implementation, or browser screenshot validation
reports `LOW_READABILITY`, `TEXT_ARTIFACT`, `CROPPED_SUBJECT`, `WRONG_SCALE`,
`STYLE_DRIFT`, or layout drift caused by the mockup image, process the defect
through `image-generation-contract`. Regenerate the mockup when root cause is
`image_generation` or `prompt_contract`; otherwise repair layout/component specs.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/ui/ui-style-tokens.json` | yes | UI-specific tokens derived from shared art style. | mockups, frontend, QA. |
| `.allforai/game-design/ui/ui-mockup-spec.json` | yes | Mockup targets, prompts, expected composition, validation rules. | image generation, QA. |
| `.allforai/game-design/ui/ui-mockup-manifest.json` | yes | Generated/registered image paths and statuses. | frontend, QA. |
| `.allforai/game-design/ui/mockups/*.png` | when generated | Screen or component preview. | QA and product review. |
| `.allforai/game-design/ui/ui-mockup-report.json` | yes | Validation, repair attempts, unresolved issues. | Diagnostics and QA. |

## Invocation Contract

```json
{
  "skill": "game-ui/ui-mockup-generation",
  "mode": "spec_generate_validate",
  "input_paths": {
    "ui_registry": ".allforai/game-design/ui/ui-registry.json",
    "screen_layout": ".allforai/game-design/ui/screen-layout-spec.json",
    "component_state": ".allforai/game-design/ui/component-state-spec.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "concept_contract": ".allforai/concept-contract.json",
    "asset_registry": ".allforai/game-design/asset-registry.json"
  },
  "generation": {
    "image_generation_available": true,
    "vision_validation_available": true,
    "max_repair_attempts": 3
  },
  "output_root": ".allforai/game-design/ui"
}
```

Supported modes:

| Mode | Behavior |
|---|---|
| `spec_only` | Write tokens, mockup specs, and manifest placeholders. |
| `spec_generate_validate` | Write specs, generate/register images, validate, repair, and report. |
| `validate_existing` | Validate existing mockups against specs. |

## Automatic Validation

Run deterministic checks:
1. Every mockup target references a registered screen or component.
2. Every mockup path starts with the target file prefix.
3. Every screen mockup references a layout breakpoint.
4. Every component mockup references a state from `component-state-spec.json`.
5. Every referenced shared asset exists or is marked placeholder.
6. UI tokens include color, typography, spacing, border, panel, and feedback
   categories.

Run visual validation when images exist:
1. Required regions appear in the expected relative order.
2. Critical HUD elements are visible.
3. Text is not cropped or unreadably small.
4. Buttons and controls are visually distinct from panels.
5. UI style matches shared art direction.
6. Gameplay playfield is not covered beyond the layout rule.

If validation fails, repair the prompt/spec and regenerate up to 3 times. If it
still fails, mark `automation_limited` and keep the best validated spec.

## Completion Conditions

Return `COMPLETED` only when required specs and manifests validate, and generated
images pass QA when generation is available. Return `COMPLETED_WITH_LIMITS` when
only spec artifacts can be produced.
