# Game Art Asset Sourcing Pipeline

## Goal

Add a complete workflow for searching, selecting, licensing, adapting, and
integrating existing art assets or asset packs. Existing assets become a first
class source alongside image generation and 3D-assisted production.

## Scope

- Source strategy selection.
- Asset pack search requirements and result schema for 2D and 3D sources.
- License/provenance QA.
- Existing 2D asset and 3D production-source adaptation.
- Asset pack integration QA.
- Handoff into atlas/style/runtime/engine-ready contracts.

## Tasks

- [x] Define source strategy across generate, 3D render, existing pack,
  user-provided asset, and adapted asset.
- [x] Define asset pack search contract, result fields, source/platform metadata,
  and candidate ranking.
- [x] Support existing 3D models, scenes, materials, textures, camera rigs, and
  animation packs as production sources for Blender render-to-2D.
- [x] Define license/provenance QA with commercial/modification/attribution gates.
- [x] Define existing asset adaptation contract for renaming, sizing, slicing,
  metadata, style, atlas, pivots, animation, and tile data.
- [x] Define asset pack integration QA and repair routing.
- [x] Wire canonical invocation paths and role chain into `game-art/SKILL.md`.
- [x] Verify standard sections, status/root-cause fields, handoff, and runtime
  validation expectations.
