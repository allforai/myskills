# Mesh Burst Generation Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill produces engine-neutral mesh-burst VFX specs for 3D or 2.5D
effects such as rock fragments, armor shards, crystal breaks, magic debris, and
object destruction bursts. It is called by `vfx-generation` when
`implementation_mode` includes `mesh_burst`.

## Scope

In scope:
- shard/debris vocabulary,
- placeholder mesh specs,
- burst timing, velocity, spread, gravity, drag, lifetime,
- material and color references,
- preview manifests,
- deterministic and visual validation,
- repair loops and particle/sprite fallback.

Out of scope:
- final authored 3D meshes,
- rigid-body simulation implementation,
- destruction gameplay logic,
- manual technical-artist cleanup.

## Input Contract

| Input | Required fields | Missing behavior |
|---|---|---|
| Mesh-burst VFX request | `vfx_id`, `file_prefix`, `presentation_layer`, `dimension=3d`, `anchor`, `lifecycle`, `mesh_burst` | Return `UPSTREAM_DEFECT`. |

Optional inputs: `vfx-spec.json`, `art-style-guide.json`, `asset-registry.json`,
existing mesh placeholders, and preview capabilities.

## Output Contract

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/art/vfx/mesh-bursts/mesh-burst-spec.json` | yes | Shard/debris specs, timing, material refs, fallback rules. | vfx-generation, runtime import, QA. |
| `.allforai/game-design/art/vfx/mesh-bursts/mesh-burst-manifest.json` | yes | Paths, placeholder refs, previews, states. | vfx-generation and registries. |
| `.allforai/game-design/art/vfx/mesh-bursts/mesh-burst-report.json` | yes | Validation and repair results. | diagnostics and QA. |

## Invocation Contract

```json
{
  "skill": "game-art/mesh-burst-generation",
  "mode": "spec_generate_validate",
  "input_paths": {
    "vfx_spec": ".allforai/game-design/art/vfx/vfx-spec.json",
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "asset_registry": ".allforai/game-design/asset-registry.json"
  },
  "generation": {
    "preview_renderer_available": true,
    "vision_validation_available": true,
    "max_repair_attempts": 3
  },
  "output_root": ".allforai/game-design"
}
```

Supported modes: `spec_only`, `spec_generate_validate`, `validate_existing`,
`register_existing`.

## Automatic Validation

Run deterministic checks:
1. Mesh burst has shard count, shape vocabulary, velocity, lifetime, material,
   gravity/drag, and fallback.
2. Paths route to `.allforai/game-design/art/vfx/mesh-bursts/` and start with
   `file_prefix`.
3. Lifetime and spread match `vfx-spec.json`.
4. Shard count stays inside the performance budget.
5. Fallback exists for non-3D runtimes.

Run visual validation when previews exist:
1. Burst origin and direction are readable.
2. Debris does not hide critical gameplay.
3. Shards match the source material style.
4. Motion dissipates cleanly.

Repair up to 3 times; otherwise downgrade to particle debris or sprite burst.

## Completion Conditions

Return `COMPLETED` only when specs, manifest, report, and available previews
validate. Return `COMPLETED_WITH_LIMITS` for placeholder or fallback-only output.
