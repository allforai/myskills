# Artifact Handoff Contract Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the shared artifact handoff schema used between game-art sub-skills.
It ensures generated, registered, QAed, packed, and runtime-bound art artifacts
carry enough structured data for downstream skills to validate inputs without
conversation memory.

Use this whenever one art sub-skill passes assets to another, especially across
3D-assisted rendering, frame animation, tilesets, atlases, UI, VFX, runtime
import, and engine-ready output.

## Input Contract

Required: producer skill name, artifact type, producer manifest path, asset IDs,
paths or explicit placeholder/disabled status, and intended downstream
consumers.

Optional: QA reports, runtime import reports, atlas refs, layer refs, frame
metadata, helper maps, source provenance, repair logs, and engine export
profile.

## Output Contract

Writes:

- `.allforai/game-design/art/handoff/artifact-handoff-contract.json`
- `.allforai/game-design/art/handoff/artifact-handoff-report.json`

Every handoff entry must include:

```json
{
  "artifact_id": "player_run_sheet",
  "artifact_type": "character_sprite_sheet",
  "producer_skill": "game-art/render-to-2d-asset-generation",
  "producer_manifest": ".allforai/game-design/art/2-5d/renders/render-to-2d-manifest.json",
  "asset_id": "player",
  "source_refs": [],
  "paths": [],
  "required_fields": {},
  "format_profile_ref": ".allforai/game-design/art/export/engine-export-profile.json",
  "qa_status": "not_run | passed | passed_with_warnings | failed | blocked",
  "runtime_status": "not_run | import_ready | import_ready_with_warnings | failed | engine_unavailable",
  "handoff_state": "draft | ready_for_consumer | blocked | consumed | deprecated",
  "downstream_routes": [],
  "repair_routes": [],
  "validation_evidence": []
}
```

Allowed artifact types include `character_sprite_sheet`,
`multi_direction_character_sheet`, `pose_sheet`, `character_part_render_set`,
`tileset_sheet`, `isometric_tile_render`, `prop_render`, `building_render`,
`background_plate`, `shadow_pass`, `normal_depth_height_map`,
`item_thumbnail_render`, `icon_set`, `vfx_sprite_render`, `particle_texture`,
`trail_texture`, `ui_mockup`, `atlas_manifest`, `runtime_import_manifest`,
`preview_contact_sheet`, and `preview_only`.

Downstream routes must include `consumer_skill`, `handoff_kind`,
`required_fields`, `accepted_artifact_types`, `qa_required`,
`runtime_import_required`, and `blocks_if_missing`.

Repair routes must include `failure_code`, `root_cause`, `repair_target`,
`repair_mode`, and `max_attempts`.

Allowed states: `draft`, `ready_for_consumer`, `blocked`, `consumed`,
`deprecated`.

Downstream consumers: every game-art producer, QA skill, atlas packaging,
runtime import check, engine-ready output contract, game UI, game level, and
runtime implementation nodes.

## Invocation Contract

```json
{
  "skill": "game-art/artifact-handoff-contract",
  "mode": "validate_handoff",
  "input_paths": {
    "producer_manifest": ".allforai/game-design/art/2-5d/renders/render-to-2d-manifest.json",
    "engine_export_profile": ".allforai/game-design/art/export/engine-export-profile.json"
  },
  "output_root": ".allforai/game-design/art/handoff"
}
```

Supported modes: `define_schema`, `validate_handoff`, `repair_handoff`,
`consumer_acceptance`.

## Automatic Validation

Validate that each handoff entry is self-contained:

- `artifact_id`, `artifact_type`, `producer_skill`, and `producer_manifest` are
  present.
- `paths` exist or the artifact is explicitly `preview_only`, `placeholder`,
  `disabled`, or `engine_unavailable`.
- `downstream_routes` cover at least one QA route and, for runtime assets, one
  runtime/export route.
- Each consumer route lists required fields and accepted artifact types.
- `qa_status=passed` requires evidence paths.
- `runtime_status=import_ready` requires executable import evidence.
- Raw 3D source paths may appear only in `source_refs`, not runtime `paths`.
- Repair routes point to specific skills, not vague categories.

Consumer acceptance rules:

| Consumer class | Required handoff fields |
|---|---|
| animation/frame skill | frame grid, FPS, pivot, anchor, alpha, action/state refs |
| skeletal/layer skill | part IDs, pivots, z-order, masks, source refs |
| tileset/level skill | tile size, projection, collision/walkability, preview map refs |
| atlas packaging | image paths, dimensions, padding/trim policy, atlas group |
| UI/icon skill | size, crop, alpha/background, UI consumer refs |
| VFX skill | frame timing, blend mode, anchor, event refs, intensity |
| runtime import | engine profile, runtime IDs, paths, executable validation plan |
| engine-ready output | QA status, runtime status, fallback status, consumer contracts |

State progression gates:

```text
draft
-> ready_for_consumer          required fields, paths/status, routes, repair targets valid
-> blocked                     missing required fields, QA, runtime evidence, or routes
-> consumed                    downstream consumer accepted the handoff
-> deprecated                  superseded by repaired artifact
```

Repair routing: missing producer fields route to the producer skill; invalid
consumer route repairs this contract; QA failures route to the named QA skill;
runtime import failures route to `runtime-import-check` or
`engine-export-profile`; raw 3D leakage routes to `3d-assisted-2d-qa` and
`engine-ready-art-output-contract`.

## Completion Conditions

Return `COMPLETED` when all handoff entries are self-contained and acceptable to
their declared consumers. Return `FAILED_VALIDATION` when required fields,
routes, repair targets, QA evidence, or runtime evidence are missing. Return
`UPSTREAM_DEFECT` when producer manifests cannot be resolved.
