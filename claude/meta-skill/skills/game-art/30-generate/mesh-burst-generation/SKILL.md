---
name: game-art-30-generate-mesh-burst-generation
description: Retired. Remap mesh-burst VFX to sprite or particle generation; do not produce 3D mesh bursts.
---

# Mesh Burst Generation Skill

> Retired. Not a production path.

If this file is opened, do not generate mesh-burst specs, placeholders, or
previews. Remap the request to `sprite-vfx-generation` or `particle-system`
and return `NOT_APPLICABLE`.

Do not require `dimension=3d`. Do not write
`.allforai/game-design/art/vfx/mesh-bursts/`.
