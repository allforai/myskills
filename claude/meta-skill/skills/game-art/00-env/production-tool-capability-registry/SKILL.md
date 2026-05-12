---
name: game-art-00-env-production-tool-capability-registry
description: Internal bundled meta-skill module for game-art/00-env/production-tool-capability-registry; use within generated bootstrap node-specs when this exact contract is selected.
---

# Production Tool Capability Registry Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Records which local production tools are available for game-art pipelines. It
is the tool gate for 3D-assisted 2D production, atlas packaging, image
processing, runtime import validation, and engine-ready output.

Blender CLI plus deterministic Blender Python scripts are the primary execution
path for 3D-assisted 2D production that renders or bakes from 3D sources. MCP
may be recorded as optional diagnostics, but it is not the production path. If
Blender CLI or an explicitly declared equivalent render tool is missing, attempt
automatic installation; if validation still fails, downstream render skills must
stop with `blocked_by_tooling`.

## Input Contract

Required: requested art pipeline capabilities and target runtime.

Optional: project root, configured MCP tools, expected command names, tool
version constraints, engine project paths, existing scripts, package manager,
and CI/runtime environment.

## Output Contract

Writes:

- `.allforai/game-design/art/tools/production-tool-capability-registry.json`
- `.allforai/game-design/art/tools/production-tool-capability-report.json`

Tool entries must include `tool_id`, `tool_kind`, `required_for`,
`preferred_access`, `cli_command`, `optional_mcp_tool`, `availability`,
`version`, `validation_command`, `install_policy`, `install_commands`,
`install_evidence`, `validation_evidence`, `project_paths`, `failure_status`,
`consumer_refs`, and `notes`.

Default required Blender entry:

```json
{
  "tool_id": "blender",
  "tool_kind": "3d_renderer",
  "required_for": ["3d_source_render", "sprite_turntable", "shadow_pass", "helper_maps"],
  "preferred_access": "cli",
  "cli_command": "blender",
  "optional_mcp_tool": "blender-mcp",
  "availability": "available | missing | installing | install_failed | version_mismatch | configured_but_unverified",
  "install_policy": "auto_install_if_missing",
  "install_commands": {
    "macos_brew": "brew install --cask blender",
    "linux_apt": "sudo apt-get update && sudo apt-get install -y blender",
    "linux_snap": "sudo snap install blender --classic",
    "windows_winget": "winget install BlenderFoundation.Blender"
  },
  "validation_command": "blender --version",
  "failure_status": "blocked_by_tooling"
}
```

Allowed `tool_kind` values: `3d_renderer`, `image_processor`,
`atlas_packer`, `runtime_importer`, `engine_editor`, `preview_renderer`,
`mesh_tool`, `texture_tool`, `script_runtime`, `mcp_tool`, `custom`.

Allowed availability values: `available`, `missing`, `installing`,
`install_failed`, `version_mismatch`, `configured_but_unverified`,
`project_missing`, `not_required`.

Allowed install policies: `auto_install_if_missing`, `manual_only`,
`provided_by_project`, `not_installable`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_tooling`.

Downstream consumers: `2-5d-production-mode-spec`, `3d-source-asset-spec`,
`2-5d-lighting-shadow-spec`, `render-to-2d-asset-generation`,
`atlas-packaging`, `runtime-import-check`, `3d-assisted-2d-qa`, and
`engine-ready-art-output-contract`.

## Invocation Contract

```json
{
  "skill": "game-art/production-tool-capability-registry",
  "mode": "detect_validate",
  "input_paths": {
    "engine_export_profile": ".allforai/game-design/art/export/engine-export-profile.json",
    "production_mode": ".allforai/game-design/art/2-5d/2-5d-production-mode-spec.json"
  },
  "output_root": ".allforai/game-design/art/tools"
}
```

Supported modes: `detect_validate`, `ensure_required_tools`,
`install_missing`, `validate_existing`, `register_declared`,
`repair_existing`.

## Automatic Validation

Check each required capability with an executable validation command. A declared
tool is not `available` until validation evidence exists. For required tools
with `install_policy=auto_install_if_missing`, run installation before returning
`blocked_by_tooling`.

Capability requirements:

| Capability | Typical tools | Required by |
|---|---|---|
| 3D render/bake | Blender or explicit equivalent renderer | `render-to-2d-asset-generation` |
| image processing | ImageMagick, sharp, canvas, custom script | alpha, crop, spritesheet, helper-map checks |
| atlas packing | TexturePacker, free-tex-packer, custom packer | `atlas-packaging` |
| runtime import | engine CLI/editor, runtime adapter, import script | `runtime-import-check` |
| screenshot/probe | Playwright, engine screenshot command, preview renderer | visual/runtime QA |
| script runtime | node, python, shell, package manager | generated validators/importers |

Installation flow:

```text
detect CLI command
-> if available: record version and validation evidence
-> if missing and install_policy=auto_install_if_missing: select install command
-> run install command
-> rerun validation command
-> if validation passes: availability=available
-> if install or validation fails: availability=install_failed, failure_status=blocked_by_tooling
```

Blender execution policy:

- Primary production path is `blender --background --python <generated_script.py>`.
- Blender Python scripts must be generated as deterministic artifacts and
  referenced by producing manifests.
- Optional MCP can inspect scenes or assist diagnostics, but completion must not
  depend on MCP.
- Install success alone is insufficient; rerun `blender --version`.
- If Blender CLI cannot be installed or verified, return `blocked_by_tooling`.

Fail-fast rules:

- If a required auto-installable tool is missing, attempt installation before
  returning `blocked_by_tooling`.
- If a tool cannot be verified, mark `configured_but_unverified` and block
  skills that require executable evidence.
- Do not downgrade to static checks for runtime import validation.
- Do not mark a 3D-assisted render path available without Blender or an
  explicitly declared equivalent render-capable tool.
- Every missing required tool must name the downstream skills it blocks.

State progression gates:

```text
draft
-> validated                    all required tools have executable evidence
-> needs_revision               optional tools or versions need adjustment
-> blocked_by_tooling           required tool missing, install failed, unverified, or wrong version
```

Repair routing: failed Blender install or validation repairs here before
`render-to-2d-asset-generation`; missing runtime importers route to
`engine-export-profile`; missing atlas tools route to `atlas-packaging`;
missing image processors route to the producing skill; optional MCP gaps are
diagnostics-only and must not block Blender CLI production.

## Completion Conditions

Return `COMPLETED` when every required capability for the selected art pipeline
has executable validation evidence. Return `FAILED_VALIDATION` when required
tools are missing, unverified, or incompatible.
