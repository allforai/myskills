---
name: game-frontend
description: Internal bundled meta-skill module for game-frontend; use within generated bootstrap node-specs when this exact contract is selected.
---

# Game Frontend Skill Pack

> Internal bundled sub-skill pack for meta-skill.
> Status: bundled, inactive, not wired.

## Purpose

Game Frontend owns the client-facing assembly layer for playable games. It
consumes approved design, art, UI, audio, level, and runtime contracts, binds
them into a visible client, runs it, and validates the result with logs,
screenshots, scene probes, and playability smoke tests.

Use this pack for browser/HTML5, Phaser, Pixi, Canvas/WebGL, Godot/Unity
client-frontends, and other client runtimes where the goal is to make a game
screen load, render, respond, and prove assets are connected.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `00-env` | `frontend-runtime-detection` | Detect client stack, engine/runtime commands, dev server, test tools, and runnable validation surface. |
| `20-spec` | `asset-import-binding-spec` | Bind engine-ready art manifest entries to loader keys, runtime IDs, atlas frames, fallbacks, and import checks. |
| `20-spec` | `game-data-binding-spec` | Bind design data tables and system specs into frontend-readable modules, schemas, loader keys, and probes. |
| `20-spec` | `scene-composition-spec` | Define scenes, layers, camera framing, level/art/UI/audio composition, and visible smoke targets. |
| `20-spec` | `input-camera-binding-spec` | Bind player input, camera follow/framing, viewport constraints, and device controls. |
| `20-spec` | `hud-ui-binding-spec` | Bind game UI/HUD contracts to frontend screens, states, safe areas, and runtime data. |
| `20-spec` | `animation-vfx-binding-spec` | Bind animation states, clips, events, VFX, particles, and fallback visuals to gameplay/front-end events. |
| `20-spec` | `audio-binding-spec` | Bind audio cues to frontend loader keys, scene/UI/animation triggers, volume groups, and runtime probes. |
| `20-spec` | `save-state-binding-spec` | Bind local/frontend persistence for progress, settings, checkpoints, reset, and save/load probes. |
| `30-generate` | `playable-client-assembly` | Apply the bindings in the target frontend codebase and produce a runnable client integration report. |
| `40-qa` | `playable-smoke-test` | Run the client and verify scene load, input, assets, HUD, animation/VFX, logs, and screenshots. |
| `40-qa` | `playability-probe-qa` | Drive a short automated gameplay loop and verify state/feedback changes. |
| `40-qa` | `visual-runtime-regression-qa` | Compare runtime screenshots/probes against expected scene/UI/art visibility and report regressions. |
| `40-qa` | `frontend-performance-budget-qa` | Validate load, frame, bundle, asset, and runtime performance budgets with evidence. |
| `40-qa` | `frontend-build-export-qa` | Validate production build/export output, asset references, launch, and release smoke evidence. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-frontend/00-env/frontend-runtime-detection/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-frontend/20-spec/asset-import-binding-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-frontend/20-spec/game-data-binding-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-frontend/20-spec/scene-composition-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-frontend/20-spec/input-camera-binding-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-frontend/20-spec/hud-ui-binding-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-frontend/20-spec/animation-vfx-binding-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-frontend/20-spec/audio-binding-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-frontend/20-spec/save-state-binding-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-frontend/30-generate/playable-client-assembly/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-frontend/40-qa/playable-smoke-test/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-frontend/40-qa/playability-probe-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-frontend/40-qa/visual-runtime-regression-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-frontend/40-qa/frontend-performance-budget-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-frontend/40-qa/frontend-build-export-qa/SKILL.md
```

## Required Inputs

Game Frontend should consume these artifacts when present:

```text
.allforai/game-design/game-design-doc.json
.allforai/game-design/design/program-development-node-handoff.json
.allforai/game-templates/template-registry.json
.allforai/game-templates/schemas/
.allforai/game-templates/instances/
.allforai/game-templates/template-reference-map.json
.allforai/game-runtime/art/engine-ready-art-manifest.json
.allforai/game-design/art/qa/runtime-import-check-report.json
.allforai/game-design/data/
.allforai/game-design/ui/ui-registry.json
.allforai/game-design/levels/
.allforai/game-design/audio/
```

## Outputs

Game Frontend writes contracts under:

```text
.allforai/game-frontend/env/
.allforai/game-frontend/bindings/
.allforai/game-frontend/assembly/
.allforai/game-frontend/qa/
```

## Boundary

Game Frontend is not a design, art, or backend/security pack. It may implement
client code and resource bindings in the target project, but it must not invent
missing design requirements, regenerate art, or accept unavailable validation.
If the client cannot run, return a blocking validation status and expose the
missing command, server, engine, or dependency.
