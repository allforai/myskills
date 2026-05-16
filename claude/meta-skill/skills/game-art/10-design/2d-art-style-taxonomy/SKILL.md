---
name: game-art-10-design-2d-art-style-taxonomy
description: Present and select 2D game art style families during bootstrap so users understand style tradeoffs, production cost, LLM fit, programmatic processing fit, and project risks before art direction is frozen.
---

# 2D Art Style Taxonomy Skill

> Internal sub-skill for game-art pipelines. Status: bundled, bootstrap-facing.

## Purpose

Before a 2D game art pipeline starts, the user should understand the available
visual style families and their consequences. This skill produces a
project-facing style taxonomy and a selected style preference contract for
downstream art direction, prompt compilation, model routing, and programmatic
processing.

## Input Contract

Required:

```text
.allforai/product-concept/concept-baseline.json
.allforai/game-design/game-design-doc.json
```

Optional:

```text
.allforai/game-design/art/human-visual-preferences.json
.allforai/bootstrap/project-summary.json
.allforai/bootstrap/specialized-skills/
```

If product/game concept is missing, return `UPSTREAM_DEFECT`; do not ask the
user to choose art style without a product target.

## Output Contract

Writes:

```text
.allforai/game-design/art/2d-art-style-taxonomy.html
.allforai/game-design/art/2d-art-style-taxonomy.json
.allforai/game-design/art/human-visual-preferences.json
```

The JSON must include:

```json
{
  "status": "ready | pending_user_choice | blocked",
  "project_fit_summary": "",
  "style_families": [],
  "recommended_shortlist": [],
  "selected_preference": {
    "primary_style_family": "",
    "secondary_influences": [],
    "avoid_styles": [],
    "production_priority": "beauty | readability | speed | cost | consistency",
    "programmatic_processing_preference": "material_first"
  },
  "downstream_constraints": {}
}
```

## Style Families

Present only the relevant subset, but the taxonomy must be able to classify:

- `pixel_art`: low-res charm, strong grid readability, strict animation and
  palette discipline, good procedural variant fit.
- `hand_drawn_cartoon`: expressive, approachable, good for casual/character
  games, needs line consistency and cleanup.
- `flat_vector`: clean UI-like shapes, strong icon/UI cohesion, easy recolor,
  weaker organic atmosphere.
- `painted_illustration`: high appeal and mood, good for backgrounds/portraits,
  higher consistency and production cost.
- `anime_character`: strong character appeal, high identity drift risk, often
  needs reference/LoRA and strict face/outfit locks.
- `storybook_watercolor`: soft emotional tone, good for cozy/narrative games,
  risk of low small-size contrast.
- `cutout_paper`: layered craft look, excellent programmatic composition and
  parallax fit.
- `low_poly_rendered_2d`: 3D-assisted source rendered to 2D, good consistency,
  requires Blender/camera/material pipeline.
- `clay_or_toy_like`: tactile, commercial appeal for casual games, strong
  lighting/material demands.
- `minimal_geometric`: fast, readable, low asset cost, can look generic if
  visual hooks are weak.
- `comic_ink`: high contrast and action readability, line quality matters.
- `ui_first_casual`: polished panels/icons/effects dominate, suitable for
  puzzle/merge/idler games where UX surfaces carry the appeal.

## User-Facing Explanation Requirements

The HTML must be in Chinese and explain for each shortlisted style:

- player first-impression promise;
- suitable game genres and screens;
- asset workload and iteration cost;
- LLM generation difficulty;
- whether LoRA/reference/edit mode is likely required;
- best programmatic processing methods;
- runtime readability risks;
- what the style should avoid.

Do not present style as abstract art history. Present it as production choices
for this project.

## Automatic Validation

Reject with `FAILED_VALIDATION` when:

- the taxonomy does not map style choices to project genre/core loop;
- style options omit production cost, LLM fit, and programmatic processing fit;
- selected preference is missing or ambiguous;
- avoid styles are missing;
- downstream constraints do not mention prompt/model/processing implications;
- HTML is not Chinese.

## Completion Conditions

Return `COMPLETED` when the taxonomy HTML/JSON exist, the selected preference is
ready or explicitly pending user choice, and downstream art direction can read
the selected style family, avoid list, and processing preference.
