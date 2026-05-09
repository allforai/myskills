# 2.5D Assisted 2D Art Pipeline

## Goal

Add a complete contract path for games that use 3D as an art production aid but
ship a 2D runtime. The pipeline must keep 3D source assets out of runtime
delivery unless explicitly allowed, render or bake them into 2D assets, validate
style/readability, and prove the final 2D outputs import into the target engine.

## Scope

- Add 2.5D production mode selection.
- Add production tool capability registry for Blender CLI/Python render, image,
  atlas, runtime import, and screenshot/probe tools.
- Add 3D source asset specification.
- Add 2.5D lighting and shadow specification.
- Add render-to-2D asset generation.
- Add 3D-assisted 2D QA.
- Wire the chain into `game-art/SKILL.md`.
- Update output contracts so 3D production sources cannot silently enter the
  engine-ready 2D runtime bundle.

## Tasks

- [x] Define production-mode boundaries for 3D-assisted, 2D-runtime games.
- [x] Define tool capability registry, automatic installation, Blender
  CLI/Python primary path, and fail-fast tooling rules.
- [x] Define 3D source asset contracts and runtime exclusion rules.
- [x] Define lighting/shadow/bake consistency rules.
- [x] Define render-to-2D outputs, manifests, passes, and repair routing.
- [x] Define output-to-downstream routing for character sheets, tiles, props,
  backgrounds, helper maps, thumbnails, VFX, previews, QA, and runtime import.
- [x] Add shared artifact handoff contract so downstream skills can validate
  inputs without conversation memory.
- [x] Define QA for perspective, lighting, edge, scale, pivot, style, and runtime exclusion.
- [x] Wire canonical invocation paths and example role chain.
- [x] Verify standard sections, status/root-cause fields, routing, and import-validation expectations.
