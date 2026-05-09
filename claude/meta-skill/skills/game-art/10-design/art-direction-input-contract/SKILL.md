# Art Direction Input Contract Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Normalizes all upstream information that can affect game art production before
any art sub-skill generates specs or assets. It turns product concept, gameplay,
audience, platform, narrative tone, technical constraints, and human visual
preferences into a stable art direction contract.

Use this as the entry boundary for `game-art` when a node-spec needs Claude Code
to route from product/game concept into visual style, view mode, asset planning,
generation, QA, and engine-ready output.

## Input Contract

Required: product/game concept, target game type, target platform, core gameplay
loop, and any available human preference notes.

Optional: reference images, negative references, genre competitors, narrative
tone, UI direction, monetization/business positioning, accessibility goals,
target runtime, production budget, image-generation capability, and existing
project art.

## Output Contract

Writes:

- `.allforai/game-design/art/art-direction-input-contract.json`
- `.allforai/game-design/art/art-direction-input-report.json`

The contract must include `contract_id`, `product_context`, `gameplay_context`,
`audience_context`, `emotional_targets`, `world_context`,
`human_preferences`, `reference_policy`, `style_constraints`,
`technical_constraints`, `production_constraints`, `accessibility_constraints`,
`acceptance_priorities`, `unknowns`, `state`, and `consumer_refs`.

Human preferences must be structured as:

```json
{
  "likes": [],
  "dislikes": [],
  "must_include": [],
  "must_avoid": [],
  "reference_images": [],
  "negative_references": [],
  "palette_preferences": [],
  "complexity_preference": "minimal | simple | medium | detailed | unknown",
  "style_risk_tolerance": "conservative | balanced | experimental"
}
```

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_product_concept`, `blocked_by_preference_conflict`,
`blocked_by_runtime_constraints`.

Downstream consumers: `asset-registry`, `visual-style-tokens`,
`2d-view-mode-spec`, `2d-layering-spec`, `2d-animation-production-plan`,
`motion-design`, `image-generation-contract`, `game-ui`, `game-audio`,
`game-narrative`, `2d-style-consistency-qa`, and
`engine-ready-art-output-contract`.

## Invocation Contract

```json
{
  "skill": "game-art/art-direction-input-contract",
  "mode": "normalize_validate",
  "input_paths": {
    "concept_contract": ".allforai/concept-contract.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "human_preferences": ".allforai/game-design/art/human-preferences.json"
  },
  "output_root": ".allforai/game-design/art"
}
```

Supported modes: `normalize_validate`, `validate_existing`, `repair_existing`,
`preference_merge`.

## Automatic Validation

Check that product context, gameplay context, visual preference, technical
constraint, and acceptance priority are explicit enough for downstream art
skills. A preference must be tagged as one of `hard_requirement`,
`soft_preference`, `negative_constraint`, or `unknown`.

Decision rules:

| Input signal | Required downstream impact |
|---|---|
| target game type or movement | view mode and animation production plan |
| human likes/dislikes | style tokens, image prompts, QA acceptance |
| target platform/runtime | export profile, atlas policy, performance budget |
| gameplay readability priority | silhouettes, VFX intensity, UI/game separation |
| monetization or item collection | icon/item art volume, rarity language |
| narrative/world tone | palette, materials, costumes, backgrounds, portraits |
| accessibility goal | contrast, motion intensity, flash limits, UI clarity |

Conflict handling:

- Hard requirements override soft preferences.
- Safety/accessibility constraints override style preferences.
- Runtime import constraints override visual complexity.
- If references conflict, preserve them as separate preference clusters and mark
  the contract `needs_revision`.
- Do not invent human preferences. If absent, set `unknowns` and use genre-safe
  defaults.

State progression gates:

```text
draft
-> validated                         product, gameplay, preferences, constraints usable
-> needs_revision                    conflicting preferences or unclear acceptance priorities
-> blocked_by_product_concept        no game/product context exists
-> blocked_by_preference_conflict    hard requirements contradict each other
-> blocked_by_runtime_constraints    required visual direction cannot fit target runtime
```

Repair routing: missing product or gameplay context returns to the product/game
concept node; conflicting human preferences repair here through
`preference_merge`; missing runtime constraints route to
`engine-export-profile`; style ambiguity routes to `visual-style-tokens` only
after this contract records the unknowns.

## Completion Conditions

Return `COMPLETED` when the contract gives downstream art skills enough
product, gameplay, preference, runtime, and acceptance context to proceed.
Return `COMPLETED_WITH_WARNINGS` when human preferences are sparse but safe
defaults are documented. Return `UPSTREAM_DEFECT` when product concept or hard
preference conflicts block art direction.
