---
name: game-art-30-generate-mesh-burst-generation
description: Retired. Remap mesh-burst VFX to sprite or particle generation; do not produce 3D mesh bursts.
---

# Mesh Burst Generation Skill

> Internal sub-skill for game-art pipelines. Status: bundled, retired.
> Kept as a tombstone so node-specs generated before retirement still resolve this path and get `NOT_APPLICABLE` instead of a missing file.

If this file is opened, do not generate mesh-burst specs, placeholders, or
previews. Remap the request to `sprite-vfx-generation` or `particle-system`
and return `NOT_APPLICABLE`.

Do not require `dimension=3d`. Do not write
`.allforai/game-design/art/vfx/mesh-bursts/`.
