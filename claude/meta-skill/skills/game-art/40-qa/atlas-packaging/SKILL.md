---
name: game-art-40-qa-atlas-packaging
description: Internal bundled meta-skill module for game-art/40-qa/atlas-packaging; use within generated bootstrap node-specs when this exact contract is selected.
---

# Atlas Packaging Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Validates and plans texture atlases for icons, tilesets, sprites, VFX sheets,
props, UI art, and other packed bitmap outputs.

## Input Contract

Required: source image manifest with paths and sizes. Optional:
`asset-registry.json`, `tileset-manifest.json`, sprite/VFX/icon manifests,
runtime constraints.

## Output Contract

Writes:
- `.allforai/game-design/art/atlases/atlas-packaging-spec.json`
- `.allforai/game-design/art/atlases/atlas-manifest.json`
- `.allforai/game-design/art/atlases/atlas-packaging-report.json`

Manifest entries must include `atlas_id`, `source_manifest`, `image_id`,
`asset_id`, `frame_id`, `x`, `y`, `w`, `h`, `margin`, `spacing`,
`bleed_policy`, `runtime_target`, `state`, and `validation`.

Allowed states: `planned`, `packed`, `validated`, `needs_revision`,
`automation_limited`.

## Invocation Contract

```json
{
  "skill": "game-art/atlas-packaging",
  "mode": "pack_validate",
  "input_paths": {
    "asset_registry": ".allforai/game-design/asset-registry.json"
  },
  "source_manifests": [],
  "output_root": ".allforai/game-design/art"
}
```

Supported modes: `plan_only`, `pack_validate`, `validate_existing`.

## Automatic Validation

Check image existence, duplicate IDs, spacing, margins, power-of-two policy when
required, UV/frame coordinates, alpha bleed, file prefixes, and runtime target
constraints.

When packing fails due to image dimensions or alpha bleed, classify whether the
root cause is image output, atlas settings, or runtime target. Only route to
`image-generation-contract` when the source image violates its output contract.

## Completion Conditions

Return `COMPLETED` when atlas manifests validate. Return
`COMPLETED_WITH_LIMITS` when packing is planned but not physically executed.
