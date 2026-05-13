---
name: game-art-20-spec-asset-acceptance-criteria
description: Internal bundled meta-skill module for game-art/20-spec/asset-acceptance-criteria; use before game art generation to define project-specific and runtime-specific acceptance standards for each asset family.
---

# Asset Acceptance Criteria Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the standards before production. This skill turns product concept,
gameplay, art direction, asset registry, project specialization, and target
runtime constraints into explicit acceptance criteria that downstream generation
and QA must use.

Do not let production define its own standard after the fact. Every generated,
searched, adapted, rendered, or user-provided art asset must have acceptance
criteria before it can be marked `consumer_ready`.

## Project And Technology Variation

Acceptance standards are not universal.

Project variation changes what "good" means:
- a puzzle board needs fast small-size distinction and low ambiguity;
- a platformer needs readable ground, hazard, silhouette, and motion timing;
- a visual novel needs portrait consistency, crop discipline, and emotion
  clarity;
- a 2.5D baked project needs consistent camera, lighting, shadows, and helper
  maps;
- a casual mobile project needs first-screenshot appeal and touch-size clarity.

Technology variation changes what "usable" means:
- Cocos, Phaser, Unity, Godot, web canvas, native mobile, and custom engines may
  require different atlas formats, pivots, alpha policy, texture compression,
  import manifests, animation formats, safe areas, DPI scales, and runtime
  preview evidence;
- generated sprites, DragonBones-compatible skeletons, frame animations,
  tilemaps, UI mockups, VFX sprite sheets, particle textures, and 3D-rendered
  2D assets each need different measurable acceptance checks.

Therefore this bundled skill defines the framework, while concrete criteria
must read project-local specialization when available:

```text
.allforai/bootstrap/specialized-skills/<specialization_id>-art-generation/SKILL.md
.allforai/game-design/art-pipeline-config.json
.allforai/game-design/art/visual-style-tokens.json
.allforai/game-design/art/engine-export-profile.json
```

If the project has clear genre, view-mode, platform, or engine-specific risks
but no specialization or runtime profile exists, return `UPSTREAM_DEFECT`
instead of applying generic criteria.

## Input Contract

Required:
- `.allforai/concept-contract.json`
- `.allforai/game-design/asset-registry.json`
- `.allforai/game-design/art-pipeline-config.json`
- `.allforai/game-design/art/visual-style-tokens.json` or equivalent style
  guide

Optional:
- `.allforai/bootstrap/specialized-skills/<specialization_id>-art-generation/SKILL.md`
- `.allforai/game-design/art/engine-export-profile.json`
- `.allforai/game-design/art/2d-view-mode-spec.json`
- `.allforai/game-design/art/2d-layering-spec.json`
- `.allforai/game-design/art/tilesets/tileset-spec.json`
- `.allforai/game-design/ui/component-state-spec.json`
- downstream runtime, importer, atlas, animation, or UI constraints

## Output Contract

Write:

```text
.allforai/game-design/art/asset-acceptance-criteria.json
.allforai/game-design/art/asset-acceptance-criteria.md
```

The JSON must contain:

```json
{
  "schema_version": "1.0",
  "project_profile": {
    "genre": "string",
    "view_mode": "string",
    "target_platforms": [],
    "runtime": "string",
    "specialization_ref": ".allforai/bootstrap/specialized-skills/<specialization_id>-art-generation/SKILL.md"
  },
  "asset_family_criteria": [
    {
      "asset_family": "tileset|character|portrait|icon|ui|background|prop|vfx|animation|particle|audio_visual_ref",
      "applies_to_asset_ids": [],
      "visual_acceptance": {
        "readability_scale_px": [],
        "distinguishability_rules": [],
        "style_lock_rules": [],
        "identity_lock": {
          "required": false,
          "lock_scope": "none|project_style|character|object|tile_family|icon_family|ui_family",
          "requires_lora": false,
          "allowed_methods": ["lora_adapter", "reference_edit_mode", "reference_image_only", "prompt_only"],
          "fallback_policy": "forbid|allow_with_warning|allow",
          "blocking_failure_codes": ["IDENTITY_DRIFT", "STYLE_DRIFT"]
        },
        "composition_rules": [],
        "forbidden_failure_modes": []
      },
      "technical_acceptance": {
        "format_rules": [],
        "atlas_rules": [],
        "pivot_anchor_rules": [],
        "alpha_rules": [],
        "runtime_import_rules": [],
        "performance_budget": []
      },
      "evidence_required": {
        "source_files": [],
        "contact_sheets": [],
        "preview_maps": [],
        "animation_previews": [],
        "runtime_screenshots": [],
        "import_reports": []
      },
      "blocking_failure_codes": [],
      "repair_routes": []
    }
  ]
}
```

The Markdown document is the human-readable standard. It must be concise,
Chinese by default for human-facing text, and organized by asset family so
Codex CLI visual review can read only the relevant batch standard.

## Invocation Contract

```json
{
  "skill": "game-art/asset-acceptance-criteria",
  "mode": "define_project_runtime_standards",
  "input_paths": {
    "concept_contract": ".allforai/concept-contract.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "art_pipeline_config": ".allforai/game-design/art-pipeline-config.json",
    "visual_style_tokens": ".allforai/game-design/art/visual-style-tokens.json",
    "engine_export_profile": ".allforai/game-design/art/engine-export-profile.json",
    "project_specialization": ".allforai/bootstrap/specialized-skills/<specialization_id>-art-generation/SKILL.md"
  },
  "output_root": ".allforai/game-design/art"
}
```

Supported modes: `define_project_runtime_standards`, `validate_existing`.

## Required Standard Dimensions

For each applicable asset family, define standards for:
- semantic fit: asset communicates the intended gameplay/UI/story meaning;
- family distinction: assets in the same family are distinguishable at runtime
  scale;
- style lock: palette, lighting, outline, material, camera, and tone match the
  project;
- identity/style lock strategy: whether recurring characters, project-wide
  styles, branded objects, tile families, icon families, or UI visual systems
  require LoRA, reference edit mode, reference-only fallback, or prompt-only
  generation;
- production fit: model/source/tool choices can realistically satisfy the
  standard;
- technical import: file format, alpha, atlas, pivot, animation, compression,
  and runtime import requirements;
- evidence: which previews, contact sheets, screenshots, samples, or reports are
  required to prove acceptance;
- blocking failures: concrete failure codes that prevent downstream use;
- repair routing: which skill owns each failure class.

## Automatic Validation

Before completion:
1. Confirm every asset family present in `asset-registry.json` has criteria or
   an explicit `not_applicable` reason.
2. Confirm every criterion is project/runtime-specific where the project has a
   known genre, view mode, platform, or engine.
3. Confirm each asset family has both visual acceptance and technical
   acceptance sections.
4. Confirm every asset family has required evidence paths or evidence types.
5. Confirm each blocking failure code has a repair route.
6. Confirm image-generation requests and visual-acceptance batches can reference
   this criteria document.
7. Confirm strict identity/style lock criteria declare whether LoRA is required,
   which fallback methods are allowed, and which drift failures are blockers.

## Completion Conditions

Return `COMPLETED` when JSON and Markdown criteria exist, cover all asset
families, and encode both project-specific and runtime-specific standards.

Return `UPSTREAM_DEFECT` when project type, view mode, runtime profile, asset
registry, or visual tokens are too incomplete to define standards.

Return `FAILED_VALIDATION` when criteria are generic, missing technical
acceptance, missing evidence requirements, or cannot route failures to an owner.
