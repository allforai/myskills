---
name: game-art-00-env-asset-registry
description: Internal bundled meta-skill module for game-art/00-env/asset-registry; use within generated bootstrap node-specs when this exact contract is selected.
---

# Asset Registry Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill defines the canonical asset registry for game art workflows. It
turns art inventories, concept contracts, and generated asset outputs into a
single machine-readable source of truth for asset IDs, file prefixes, paths,
states, variants, dependencies, and validation status.

The registry is not just a filename list. It is the coordination layer that
allows granular art sub-skills such as skeletal animation, layer sheet
generation, sprite frame animation, tileset generation, VFX generation, icon
generation, and art QA to share stable asset references without inventing names.

## Scope

Use this skill whenever a game art flow needs to:
- assign deterministic `asset_id` and `file_prefix` values,
- map logical asset IDs to concrete output paths,
- track lifecycle state from placeholder to approved output,
- register variants such as skin, direction, rarity, animation, or resolution,
- prevent downstream skills from inventing alternate names,
- validate that generated files match the art inventory and naming rules.

Out of scope:
- Generating images.
- Designing animation timelines.
- Creating final art direction.
- Deciding gameplay balance or system design.

## Input Contract

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| `.allforai/game-design/art-asset-inventory.json` | `assets[].asset_id`, `assets[].type`, `assets[].name` | Return `UPSTREAM_DEFECT`; there is no asset set to register. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/concept-contract.json` | `canonical_registry.*[].asset_id`, `file_prefix` | Derive `file_prefix` from `asset_id` and `type`. |
| `.allforai/game-design/art-pipeline-config.json` | `active_nodes`, `dimension`, `style`, `character.rig`, `tileset.*`, `vfx.*` | Use generic type-based paths and mark config source missing. |
| Existing generated files | file paths under `.allforai/game-design/art/`, `previews/`, `atlases/` | Register missing files as `planned`. |
| Caller context | selected asset IDs, output root, target engine | Use all inventory assets and `.allforai/game-design` output root. |

### Normalized input

Before writing outputs, normalize all input into this internal shape:

```json
{
  "schema_version": "1.0",
  "output_root": ".allforai/game-design",
  "style_context": {
    "dimension": "2d | 3d | 2.5d | unknown",
    "style": "cartoon | pixel | realistic | hand_drawn | vector | unknown"
  },
  "assets": [
    {
      "asset_id": "<stable slug>",
      "type": "character | tile | environment | ui | vfx | icon | background | animation-frame | audio-cover | prop | actor_3d | other",
      "name": "<display name>",
      "file_prefix": "<resolved deterministic prefix>",
      "source": "concept_contract | derived",
      "requested_by_nodes": []
    }
  ]
}
```

If duplicate `asset_id` values appear, return `FAILED_VALIDATION` and write a
registry report explaining the collision. Do not silently rename assets.

## File Prefix Rules

Use concept-contract `file_prefix` when present. Otherwise derive prefixes by
asset type:

| Type | Prefix rule |
|---|---|
| `character` | `char_{asset_id}` |
| `actor_3d` | `actor_{asset_id}` |
| `tile` | `tile_{asset_id}` |
| `environment` | `env_{asset_id}` |
| `background` | `bg_{asset_id}` |
| `ui` | `ui_{asset_id}` |
| `icon` | `ico_{asset_id}` |
| `vfx` | `vfx_{asset_id}` |
| `animation-frame` | `anim_{asset_id}` |
| `audio-cover` | `aud_{asset_id}` |
| `prop` | `prop_{asset_id}` |
| `other` | `{asset_id}` |

Rules:
- `asset_id` must be lowercase snake/kebab-compatible slug text.
- `file_prefix` must be stable for the lifetime of the project.
- Never derive a new `file_prefix` downstream after this skill runs.
- If concept-contract and derived prefixes conflict, concept-contract wins and
  the conflict is recorded in `registry-report.json`.

## Lifecycle State Model

Each registered asset uses one lifecycle state:

| State | Meaning | Next action |
|---|---|---|
| `planned` | Asset is required but no output exists. | Downstream generation skill may create it. |
| `spec_ready` | Prompt/spec exists but no generated file yet. | Generate file or preview. |
| `generated` | File exists but QA has not passed. | Run art-preview-qa or asset-specific QA. |
| `preview_ready` | Preview or atlas test exists. | Run visual/deterministic validation. |
| `approved` | Asset passed validation and can be consumed by runtime. | Downstream can use it. |
| `needs_revision` | Asset failed validation but can be regenerated. | Re-run producing skill. |
| `automation_limited` | Automated asset is not final-quality and only usable as planning/prototype fallback. | Block launch/production; route repair or mark explicitly out of scope. |
| `not_applicable` | Asset does not apply to current pipeline branch. | Ignore in current flow. |

No downstream skill should treat `planned`, `spec_ready`, `generated`, or
`automation_limited` as final runtime-ready states. For launch, launch-prep,
production, or unattended run goals, placeholder/fallback/automation-limited
assets block completion unless the project production policy explicitly marks
the asset out of launch scope.

## Output Contract

The skill writes a canonical registry and a validation report.

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/asset-registry.json` | yes | Canonical mapping from asset IDs to paths, states, variants, and owners. | All game-art sub-skills, code generation, QA. |
| `.allforai/game-design/asset-registry-report.json` | yes | Validation results, collisions, missing files, and next actions. | Bootstrap/run diagnostics, QA. |

## Invocation Contract

Other flows call this sub-skill by reading this file and passing a node-spec
context. The caller must not rely on conversation state.

Minimal invocation context:

```json
{
  "skill": "game-art/asset-registry",
  "mode": "build_or_update",
  "input_paths": {
    "art_asset_inventory": ".allforai/game-design/art-asset-inventory.json",
    "concept_contract": ".allforai/concept-contract.json",
    "art_pipeline_config": ".allforai/game-design/art-pipeline-config.json"
  },
  "asset_filter": {
    "asset_ids": [],
    "asset_types": []
  },
  "output_root": ".allforai/game-design"
}
```

### Supported modes

| Mode | Behavior |
|---|---|
| `build_or_update` | Build registry from inventory and existing outputs; preserve stable prefixes. |
| `validate_existing` | Validate an existing registry against inventory and files. |
| `register_outputs` | Add outputs from a producing sub-skill without changing existing IDs. |
| `resolve_asset_ids` | Return resolved prefixes/paths for caller-selected assets. |

### Return protocol

| Status | Meaning | Caller action |
|---|---|---|
| `COMPLETED` | Registry exists and validates. | Continue downstream. |
| `COMPLETED_WITH_WARNINGS` | Registry validates but has missing optional files or automation-limited assets. | Continue with warnings. |
| `UPSTREAM_DEFECT` | Required inventory is missing or malformed. | Pause caller; fix upstream artifact. |
| `FAILED_VALIDATION` | Duplicate IDs, conflicting prefixes, invalid paths, or illegal states. | Do not continue downstream. |

## Registry Schema

Write `.allforai/game-design/asset-registry.json`:

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO timestamp>",
  "source": {
    "art_asset_inventory": ".allforai/game-design/art-asset-inventory.json",
    "concept_contract": ".allforai/concept-contract.json",
    "used_concept_contract": true
  },
  "output_root": ".allforai/game-design",
  "assets": [
    {
      "asset_id": "<stable id>",
      "type": "character | tile | environment | ui | vfx | icon | background | animation-frame | audio-cover | prop | actor_3d | other",
      "name": "<display name>",
      "file_prefix": "<stable prefix>",
      "state": "planned | spec_ready | generated | preview_ready | approved | needs_revision | automation_limited | not_applicable",
      "owner_node": "<node id that owns primary generation>",
      "consumers": ["<downstream node ids or skill names>"],
      "paths": {
        "spec": ".allforai/game-design/specs/<file_prefix>.json",
        "source": ".allforai/game-design/art/source/<file_prefix>.png",
        "output": ".allforai/game-design/art/<file_prefix>.png",
        "preview": ".allforai/game-design/previews/<file_prefix>.png",
        "atlas": ".allforai/game-design/atlases/<file_prefix>.json"
      },
      "variants": [
        {
          "variant_id": "<variant slug>",
          "kind": "skin | direction | rarity | resolution | animation | state",
          "file_prefix": "<file_prefix>_<variant_id>",
          "state": "planned | spec_ready | generated | preview_ready | approved | needs_revision | automation_limited | not_applicable",
          "paths": {}
        }
      ],
      "dependencies": ["<asset_id>"],
      "validation": {
        "last_checked_at": "<ISO timestamp>",
        "checks_passed": [],
        "checks_failed": [],
        "next_action": "<what should happen next>"
      }
    }
  ],
  "indexes": {
    "by_type": {},
    "by_state": {},
    "by_consumer": {}
  }
}
```

## Report Schema

Write `.allforai/game-design/asset-registry-report.json`:

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO timestamp>",
  "verdict": "pass | pass_with_warnings | fail",
  "summary": {
    "total_assets": 0,
    "approved": 0,
    "planned": 0,
    "needs_revision": 0,
    "automation_limited": 0
  },
  "collisions": [],
  "missing_required_fields": [],
  "missing_files": [],
  "prefix_conflicts": [],
  "invalid_states": [],
  "warnings": [],
  "next_actions": []
}
```

## Automatic Validation

Run these deterministic checks:

1. Every inventory asset has exactly one registry entry.
2. Every `asset_id` is unique.
3. Every `file_prefix` is unique.
4. Every path is project-relative and starts under `output_root`.
5. Every asset state is in the lifecycle enum.
6. Every variant prefix starts with the parent asset `file_prefix`.
7. Every dependency references an existing `asset_id`.
8. Every approved asset has at least one concrete output path.
9. No downstream consumer has invented an asset ID absent from the registry.
10. Concept-contract prefixes, when present, match registry prefixes.

If any check 1-7 fails, return `FAILED_VALIDATION`. Checks 8-10 may return
`COMPLETED_WITH_WARNINGS` if downstream can proceed safely.

## Update Rules

When updating an existing registry:
- Preserve existing `asset_id` and `file_prefix` values.
- Add new assets from inventory as `planned`.
- Mark removed inventory assets as `not_applicable` instead of deleting them
  unless the caller explicitly requests cleanup.
- Never overwrite an approved asset state with generated/spec_ready unless the
  caller passes an explicit revision context.
- Append validation history rather than replacing it when possible.

## Downstream Usage Rules

All game-art sub-skills must:
- read `asset-registry.json` before writing asset-specific outputs,
- use `file_prefix` for all filenames,
- update the registry through `register_outputs` after producing files,
- write validation state back to the corresponding asset or variant,
- refuse to invent unregistered asset IDs.

## Completion Conditions

This skill is complete only when:
- `asset-registry.json` exists and is valid JSON,
- `asset-registry-report.json` exists and is valid JSON,
- report verdict is `pass` or `pass_with_warnings`,
- no duplicate `asset_id` or `file_prefix` exists,
- every registered path is deterministic and project-relative,
- every failure has a concrete `next_action`.

Do not mark this skill complete if only one of the two output files exists.
