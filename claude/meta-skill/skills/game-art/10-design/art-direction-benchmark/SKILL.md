---
name: game-art-10-design-art-direction-benchmark
description: Build the project-specific art direction benchmark that defines commercial visual appeal, reference targets, anti-targets, and scoring standards before bulk game art production.
---

# Art Direction Benchmark Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive,
> bootstrap-invoked when game art matters.

## Purpose

Turn art direction from a descriptive document into an auditable production
benchmark. This skill answers: "What does good art look like for this specific
game, and what must be rejected even if files exist?"

Use this before asset acceptance criteria, image generation, style consistency
QA, and runtime visual acceptance.

## Input Contract

Required:

```text
.allforai/product-concept/concept-baseline.json
.allforai/game-design/game-design-doc.json
.allforai/game-design/art-pipeline-config.json
.allforai/game-design/art/art-direction-input-contract.json
```

Optional:

```text
.allforai/game-design/art-style-guide.json
.allforai/game-design/art/visual-style-tokens.json
.allforai/game-design/art/human-visual-preferences.json
.allforai/game-design/art/sourcing/asset-pack-search-results.json
.allforai/bootstrap/specialized-skills/
```

If the required product/design/art inputs are missing, return
`UPSTREAM_DEFECT`. Do not invent a benchmark from generic taste.

## Output Contract

Writes:

```text
.allforai/game-design/art/art-direction-benchmark.json
.allforai/game-design/art/art-direction-benchmark.md
```

The JSON must include:

```json
{
  "status": "ready | blocked",
  "project_visual_promise": "",
  "commercial_appeal_hypothesis": "",
  "benchmark_references": [],
  "anti_references": [],
  "visual_quality_axes": [],
  "asset_family_standards": {},
  "runtime_screenshot_standards": {},
  "do_not_accept": [],
  "scoring_rubric": {
    "minimum_pass_score": 4,
    "axes": []
  },
  "repair_routes": []
}
```

## Method

1. Derive the `project_visual_promise` from the game concept, target audience,
   core loop, mood, platform, and monetization/retention surfaces.
2. Define `commercial_appeal_hypothesis`: why the first screenshot or store
   preview should make the target player want to try the game.
3. Create benchmark references as *criteria*, not copied assets. Each reference
   must state what quality it contributes: silhouette, palette, material,
   scene density, UI restraint, icon readability, animation feeling, or reward
   feedback.
4. Create anti-references: common outputs that must be rejected, such as
   generic AI gloss, inconsistent characters, muddy low-size icons, black
   prototype backgrounds, pure-color tiles, mismatched UI/game worlds, or
   screenshots that only prove rendering.
5. Define visual quality axes for this project. Recommended axes:
   concept fit, immediate appeal, readability at runtime size, family
   consistency, world/UI cohesion, animation/VFX delight, platform fit, and
   production feasibility.
6. Define asset-family standards for each family present in the registry:
   tiles, characters, environments, UI, icons, VFX, portraits, items, animation
   frames, and store-facing screenshots.
7. Define runtime screenshot standards for the player-facing screens that this
   project actually has. Do not hard-code a bundled screen type; use the
   project's scene flow and UI registry.

## Automatic Validation

Reject with `FAILED_VALIDATION` when:

- benchmark references are generic labels without visual quality criteria;
- anti-references are missing;
- scoring rubric asks only whether assets exist;
- asset family standards do not cover every active art family;
- runtime screenshot standards do not cover the project's player-facing
  screens;
- minimum pass score is below 4/5 for art-heavy games;
- the benchmark allows placeholder, prototype, or "acceptable for now" art to
  pass production.

## Completion Conditions

Return `COMPLETED` only when both output files exist, `status == "ready"`, every
active asset family has benchmark standards, runtime screenshot standards exist
for player-facing surfaces, and the scoring rubric can reject art that exists
but is not good enough. The benchmark must explicitly reject art that exists but is not good enough.
