---
name: game-art-00-env-2d-animation-toolchain-env
description: Internal bundled meta-skill module for game-art/00-env/2d-animation-toolchain-env; use within generated bootstrap node-specs when 2D animation production needs DragonBones-compatible data generation, Spine/frame animation, atlas, preview, or runtime import tooling validation.
---

# 2D Animation Toolchain Env Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

This skill is the environment gate for 2D animation production. It determines
whether the local/project toolchain can actually generate, preview, import, and
validate frame animation, part tween animation, DragonBones-compatible skeletal
data, Spine-style skeletal data, UI tweens, or VFX-bound animation.

The goal is not to prefer a tool. The goal is to prevent downstream animation
skills from claiming completion when the required executable tools are missing.
If a required tool cannot be installed and verified automatically, this skill
must return a blocked status and name the blocked downstream skills.

For automated pipelines, require executable project adapters and runtime
validation, not GUI authoring tools. DragonBones Pro GUI and Spine Editor GUI
are optional human-facing editors; their absence must not block a pipeline that
can generate compatible JSON/atlas data and prove runtime import automatically.

## Input Contract

Required inputs:

| Input | Required fields | Missing behavior |
|---|---|---|
| `.allforai/game-design/art/animation/2d-animation-production-plan.json` | assets, `animation_method`, fallback method, downstream refs | Return `UPSTREAM_DEFECT`; cannot know which tools are required. |
| `.allforai/game-design/art/export/engine-export-profile.json` or equivalent runtime profile | target engine/runtime, import format, preview/import validation command when available | If missing, still validate authoring tools but mark runtime import tools `blocked_by_missing_runtime_profile`. |
| `.allforai/game-design/asset-registry.json` | animation asset ids and lifecycle state | Return `UPSTREAM_DEFECT` if animated asset ids cannot be resolved. |

Optional inputs:

- `.allforai/game-design/art-pipeline-config.json`
- `.allforai/game-design/systems/skeletal-animation-plan.json`
- `.allforai/game-design/systems/frame-animation-spec.json`
- project package files and editor config
- configured CLI command overrides
- CI/runtime environment constraints
- project-local scripts for preview, import, atlas, or screenshot validation
- project-local DragonBones-compatible JSON/atlas generator scripts

## Output Contract

Writes:

- `.allforai/game-design/art/env/2d-animation-toolchain-report.json`
- `.allforai/game-design/art/env/2d-animation-toolchain-registry.json`

The report must include:

```json
{
  "schema_version": "1.0",
  "status": "validated | validated_with_limits | blocked_by_missing_toolchain | blocked_by_missing_runtime_profile | failed_validation",
  "required_capabilities": [],
  "tools": [],
  "blocked_downstream_skills": [],
  "install_attempts": [],
  "validation_evidence": [],
  "repair_routing": [],
  "completion_verdict": "COMPLETED | COMPLETED_WITH_LIMITS | UPSTREAM_DEFECT | FAILED_VALIDATION"
}
```

Each `tools[]` entry must include `tool_id`, `tool_kind`, `required_for`,
`required`, `preferred_access`, `cli_command`, `availability`, `version`,
`install_policy`, `install_command`, `validation_command`,
`validation_evidence`, `failure_status`, and `consumer_refs`.

Allowed `tool_kind` values:

- `skeletal_editor`
- `skeletal_data_generator`
- `skeletal_runtime`
- `frame_editor`
- `atlas_packer`
- `image_processor`
- `preview_renderer`
- `runtime_importer`
- `script_runtime`
- `project_adapter`

Allowed `availability` values:

- `available`
- `missing`
- `installing`
- `install_failed`
- `configured_but_unverified`
- `version_mismatch`
- `not_required`

Allowed `failure_status` values:

- `blocked_by_missing_toolchain`
- `blocked_by_unverified_toolchain`
- `blocked_by_missing_runtime_profile`
- `blocked_by_runtime_import`
- `not_blocking_optional_tool`

## Invocation Contract

```json
{
  "skill": "game-art/2d-animation-toolchain-env",
  "mode": "detect_validate",
  "input_paths": {
    "animation_production_plan": ".allforai/game-design/art/animation/2d-animation-production-plan.json",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "engine_export_profile": ".allforai/game-design/art/export/engine-export-profile.json"
  },
  "output_root": ".allforai/game-design/art/env"
}
```

Supported modes:

- `detect_validate`
- `ensure_required_tools`
- `install_missing`
- `validate_existing`
- `register_declared`
- `repair_existing`

## Tool Requirement Rules

Select required capabilities from the animation production plan:

| Animation method | Required capabilities | Typical tools |
|---|---|---|
| `skeletal_animation` with `dragonbones` / `dragonbones_mesh` | DragonBones-compatible JSON/atlas generation, preview, runtime import | project generator/adapter, texture/atlas tool, Cocos/engine importer; DragonBones Pro GUI optional |
| `skeletal_animation` with `spine` | Spine-compatible data generation/export, atlas, preview, runtime import | project generator/adapter or licensed CLI where available; Spine GUI optional |
| `part_tween` | layer metadata, preview renderer, runtime import | project script, browser/canvas preview, engine importer |
| `frame_animation` | frame sheet production, atlas, preview, runtime import | Aseprite or image pipeline, atlas packer, engine importer |
| `pose_swap` / `ui_tween` | image processor, preview renderer, runtime import | project script, browser preview, engine importer |
| `vfx_only` | VFX preview and runtime import | VFX generation skill, engine importer |

DragonBones policy:

- DragonBones is allowed for 2D skeletal animation when the project or
  production plan requests DragonBones-compatible output.
- Do not require DragonBones Pro GUI for fully automated production.
- Prefer a project-local generator/adapter that writes DragonBones-compatible
  armature/skeleton JSON, texture atlas metadata, and runtime asset paths.
- Validate the automated path with executable evidence: generator fixture
  command exits `0`, atlas files exist, preview renders frames/screenshots, and
  engine import proves the DragonBones JSON/atlas can be loaded.
- If DragonBones Pro GUI is installed, record it as optional
  `tool_kind=skeletal_editor` with `required=false` unless the production plan
  explicitly declares a manual authoring path.
- If no generator, preview, or runtime import adapter exists, set
  `failure_status=blocked_by_missing_toolchain`. The missing capability is the
  compatible automated data pipeline, not the GUI app.
- Do not silently switch DragonBones to Spine, frame animation, or static
  output. Such switches must be declared by the upstream animation production
  plan and recorded as a fallback.

Spine policy:

- Spine may be recorded when the project has a valid Spine authoring/export
  path. Treat license or GUI-only constraints as optional editor capability
  unless a verifiable CLI/project adapter is required by the production plan.
- Do not replace DragonBones with Spine merely because Spine is installed.

Frame animation policy:

- If frame animation is selected, validate the actual frame-sheet/atlas/preview
  path. Aseprite, ImageMagick, sharp/canvas scripts, or engine importers are
  acceptable only when commands execute and evidence is recorded.

Runtime import policy:

- Import validation is separate from authoring validation.
- If the target engine cannot run or no import command exists, return
  `blocked_by_missing_runtime_profile` or `blocked_by_runtime_import`.
- Do not substitute static JSON inspection for runtime import validation.

## Automatic Validation

Validation flow:

```text
read animation production plan
-> derive required capabilities per asset/method
-> detect declared commands and project adapters
-> run validation commands for required tools
-> if missing and auto-install policy is declared: run install command
-> rerun validation commands
-> write registry/report with evidence
-> block downstream skills when required evidence is absent
```

Each required capability must have executable validation evidence before downstream
animation generation can claim `approved`, `engine_ready`, or `qa_passed`.

Required evidence examples:

- command exists and version command exits `0`
- DragonBones-compatible or Spine-compatible generator exits `0` on a minimal
  fixture and writes schema-valid JSON plus atlas metadata
- preview renderer outputs a screenshot or frame file
- engine importer loads a minimal animation asset and exits `0`
- atlas packer produces a manifest with expected image paths

Rejected evidence:

- tool name mentioned in a document only
- package installed but command cannot run
- generated JSON that was never imported or previewed
- screenshot path that does not exist
- manual editor instruction
- GUI app presence without an automated export/import adapter

## Repair Routing

When validation fails, route repair by root cause:

| Failure | Repair route |
|---|---|
| missing animation method | `2d-animation-production-plan` |
| DragonBones-compatible generator/preview/import adapter unavailable | this skill, then `skeletal-animation` if a generator can be created, otherwise `2d-animation-production-plan` only if a declared fallback exists |
| Spine-compatible generator/preview/import adapter unavailable | this skill, then `2d-animation-production-plan` only if a declared fallback exists |
| missing frame/atlas tool | this skill or `atlas-packaging` |
| missing preview renderer | this skill or the producing animation skill |
| missing runtime import profile | `engine-export-profile` |
| runtime import fails | `runtime-import-check` and engine frontend binding |

Downstream skills must read this report before generating or accepting output:

- `game-art/30-generate/skeletal-animation`
- `game-art/30-generate/frame-animation-generation`
- `game-art/20-spec/animation-state-machine-spec`
- `game-art/40-qa/runtime-import-check`
- `game-art/40-qa/engine-ready-art-output-contract`

## Completion Conditions

Return `COMPLETED` when every required 2D animation capability has executable
validation evidence and runtime import validation is either available or not
required for the current node.

Return `COMPLETED_WITH_LIMITS` when optional tools are missing but all required
tools for the selected plan have evidence.

Return `UPSTREAM_DEFECT` when the animation production plan, asset registry, or
runtime profile is missing required fields.

Return `FAILED_VALIDATION` with `status=blocked_by_missing_toolchain`,
`blocked_by_missing_runtime_profile`, or `blocked_by_runtime_import` when a
required tool cannot be verified. Do not emit fallback acceptance in this skill.
