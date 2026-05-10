# Game Art Skill Pack

> Internal bundled sub-skill pack for meta-skill.
> Status: bundled, inactive, not wired.
> This directory is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads a child skill path.
> These are Claude Code-readable sub-skills, not separately installed top-level
> skills.

## Purpose

Game Art is organized as a small set of composable sub-skills. Each sub-skill
owns one stable artifact contract and can be called by future bootstrap/run
nodes without relying on conversation state.

Do not organize by tool. Organize by production layer:

```text
00-env        What can the pipeline use? What are assets called?
10-design     What should the asset/motion communicate?
20-spec       How should the asset be decomposed or specified?
30-generate   How are concrete images, animations, previews, or data generated?
40-qa         Can the generated output be used downstream?
```

Layer numbers indicate directory organization and default execution order for new projects. Individual chains in node-specs may deviate from this order when the use case requires it (e.g., running a 40-qa license check before a 20-spec adaptation step). The node-spec is authoritative; chains shown below are illustrative.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `00-env` | `asset-registry` | Canonical asset IDs, file prefixes, paths, lifecycle states, validation report. |
| `00-env` | `production-tool-capability-registry` | Detect, auto-install, and validate Blender CLI/Python, image, atlas, importer, and probe tools before use. |
| `10-design` | `2d-animation-production-plan` | Light 2D animation method selection, fallback strategy, downstream routing, QA requirements. |
| `10-design` | `art-direction-input-contract` | Product concept, gameplay, runtime constraints, and human visual preferences as art input. |
| `10-design` | `asset-source-strategy-spec` | Decide per asset whether to use LLM generation, existing packs, existing 3D sources, user assets, adaptation, or hybrid production. |
| `10-design` | `motion-design` | Animation intent, key poses, timing, events, readability, fallback motion. |
| `20-spec` | `2-5d-production-mode-spec` | 3D-assisted production boundaries for games that render/bake to 2D runtime assets. |
| `20-spec` | `2-5d-lighting-shadow-spec` | Light direction, baked shadows, helper maps, and runtime lighting rules for 3D-assisted 2D output. |
| `20-spec` | `2d-layering-spec` | Unified scene, character, outfit, animation overlay, VFX, UI, helper, atlas, and runtime layer rules. |
| `20-spec` | `2d-view-mode-spec` | Side-view, top-down, isometric, fixed-room, board/grid, visual-novel, shooter, and hybrid spatial rules. |
| `20-spec` | `3d-source-asset-spec` | Production-only 3D source assets, cameras, materials, passes, output mapping, and runtime exclusion. |
| `20-spec` | `animation-state-machine-spec` | Runtime animation states, transitions, priorities, event frames, fallback states, import references. |
| `20-spec` | `asset-pack-search-spec` | Search and select existing 2D/3D asset packs with license, style, coverage, adaptation, and downstream fit constraints. |
| `20-spec` | `artifact-handoff-contract` | Shared cross-skill artifact handoff schema, downstream routes, QA/runtime status, and repair routes. |
| `20-spec` | `character-layer-sheet` | Character part decomposition, layer-sheet prompt/spec, pivots, validation. |
| `20-spec` | `engine-export-profile` | Engine/tool export contracts for atlases, pivots, clips, tilemaps, skeletons, and runtime import. |
| `20-spec` | `existing-asset-adaptation-spec` | Normalize, edit, recolor, resize, rerender, or route existing 2D/3D assets into project art contracts. |
| `20-spec` | `tileset-spec` | Tilemap mode selection, terrain vocabulary, tile rules, collision/walkability contracts. |
| `20-spec` | `vfx-spec` | VFX semantics, gameplay events, presentation layer, dimension, implementation mode, timing, readability budgets. |
| `20-spec` | `visual-style-tokens` | Shared palette, shape, line, material, camera, typography, and motion tokens. |
| `20-spec` | `frame-animation-spec` | Frame-animation vocabulary, frame counts, timing, anchors, loop rules, acceptance. |
| `30-generate` | `image-generation-contract` | Shared LLM image request, prompt, output, visual acceptance, repair, and fallback contract. |
| `30-generate` | `background-generation` | Background scene prompts, layers, parallax/depth, generated images, validation. |
| `30-generate` | `prop-generation` | Reusable prop specs, generated images/models/placeholders, variants, validation. |
| `30-generate` | `portrait-generation` | Character portraits, busts, dialogue/emotion variants, generated images, QA. |
| `30-generate` | `render-to-2d-asset-generation` | Render/bake/register 2D runtime assets from 3D-assisted production sources. |
| `30-generate` | `item-art-generation` | Item/equipment art specs, generated images, variants, inventory/shop validation. |
| `30-generate` | `frame-animation-generation` | Sprite-frame animation sheets, frame metadata, previews, repair loop. |
| `30-generate` | `expression-set-generation` | Character expression sheets, emotion states, portraits, validation, repair. |
| `30-generate` | `icon-generation` | Skill, item, currency, ability, status, and UI icon set generation with consistency QA. |
| `30-generate` | `tileset-generation` | Tileset prompts, generated tile sheets, atlas manifests, preview maps, repair loop. |
| `30-generate` | `particle-system` | Reusable particle emitter configs, textures, previews, validation, and repair. |
| `30-generate` | `sprite-vfx-generation` | Sprite-sheet VFX frame specs, generated sheets, frame metadata, previews, repair. |
| `30-generate` | `trail-generation` | Trail/ribbon specs, strip textures, timing, previews, validation, repair. |
| `30-generate` | `shader-vfx-generation` | Shader/material VFX parameter specs, placeholders, previews, reduced fallbacks. |
| `30-generate` | `decal-generation` | Impact marks, projected decals, scorch/blood/crack specs, textures, validation. |
| `30-generate` | `screen-effect-generation` | Flash, shake, vignette, radial burst, accessibility-safe screen-space effects. |
| `30-generate` | `mesh-burst-generation` | 3D shard/debris burst specs, placeholder meshes, timing, physics-lite validation. |
| `30-generate` | `light-pulse-generation` | 2.5D/3D light pulse specs, intensity curves, color timing, accessibility caps. |
| `30-generate` | `animation-event-fx` | Footstep, landing, weapon, cast, and hit FX bound to animation timeline events. |
| `30-generate` | `vfx-generation` | VFX orchestration across particle, sprite-sheet, trail, shader, decal, screen-effect, mesh-burst, light-pulse, and animation-event branches. |
| `30-generate` | `skeletal-animation` | Bone hierarchy, transform timelines, rendered preview loop, visual validation, repair. |
| `40-qa` | `art-preview-qa` | Cross-asset visual QA, downstream feedback, issue classification, repair routing. |
| `40-qa` | `atlas-packaging` | Atlas packing manifests, spacing/margin checks, references, and export validation. |
| `40-qa` | `2d-style-consistency-qa` | Palette, outline, scale, projection, readability, animation, UI/game, and runtime style QA. |
| `40-qa` | `3d-assisted-2d-qa` | Perspective, lighting, edge, pivot, style, helper-map, and runtime-exclusion QA for 3D-derived 2D assets. |
| `40-qa` | `asset-license-provenance-qa` | Hard-gate asset license, provenance, commercial/modification permission, attribution, and traceability. |
| `40-qa` | `asset-pack-integration-qa` | Validate existing/adapted asset packs against style, coverage, atlas, metadata, runtime import, and handoff contracts. |
| `40-qa` | `engine-ready-art-output-contract` | Final engine/runtime import contract and program-facing art manifest for assets, manifests, atlas, animation, VFX, UI, QA, and fallbacks. |
| `40-qa` | `runtime-import-check` | Runtime import validation for assets, manifests, previews, and fallback status. |

## Canonical Invocation Paths

Use these paths when a node-spec calls a child skill:

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-art/00-env/asset-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/00-env/production-tool-capability-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/2d-animation-production-plan/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/art-direction-input-contract/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/asset-source-strategy-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/motion-design/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/2-5d-production-mode-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/2-5d-lighting-shadow-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/2d-layering-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/2d-view-mode-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/3d-source-asset-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/animation-state-machine-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/asset-pack-search-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/artifact-handoff-contract/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/character-layer-sheet/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/engine-export-profile/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/existing-asset-adaptation-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/tileset-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/vfx-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/visual-style-tokens/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/frame-animation-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/image-generation-contract/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/background-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/prop-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/portrait-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/render-to-2d-asset-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/item-art-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/frame-animation-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/expression-set-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/icon-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/tileset-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/particle-system/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/sprite-vfx-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/trail-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/shader-vfx-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/decal-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/screen-effect-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/mesh-burst-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/light-pulse-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/animation-event-fx/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/vfx-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/skeletal-animation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/art-preview-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/atlas-packaging/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/2d-style-consistency-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/3d-assisted-2d-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/asset-license-provenance-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/asset-pack-integration-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/engine-ready-art-output-contract/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/runtime-import-check/SKILL.md
```

## Layering Rules

Allowed dependencies flow from earlier numbered layers to later numbered
layers only:

```text
00-env -> 10-design -> 20-spec -> 30-generate -> 40-qa
```

Rules:
- A later layer may read artifacts from earlier layers.
- An earlier layer must not depend on artifacts from later layers.
- A child skill must not invent asset IDs or file prefixes after
  `asset-registry` exists.
- Each child skill must define `Input Contract`, `Output Contract`,
  `Invocation Contract`, automatic validation, and completion conditions.
- If a required tool, image, source asset, preview, license, or runtime import
  check is unavailable, return `UPSTREAM_DEFECT`, `blocked_by_missing_evidence`,
  or `FAILED_VALIDATION`. Do not mark placeholder-only or spec-only output as
  accepted production art.

## Methodology Ownership

Each leaf child skill owns the method for its artifact. The parent pack only
defines layer order and common chains.

Art methods should be placed where they are executed:
- source choice and human preference collection: `10-design/art-direction-input-contract`
  and `10-design/asset-source-strategy-spec`;
- visual consistency rules: `20-spec/visual-style-tokens`;
- decomposition and runtime fit: `20-spec/2d-layering-spec`,
  `20-spec/engine-export-profile`, and asset-specific `20-spec/*` skills;
- LLM image prompt/repair/feedback loop: `30-generate/image-generation-contract`;
- concrete asset generation: asset-specific `30-generate/*` skills;
- preview, atlas, style, license, import, and engine handoff validation:
  `40-qa/*` skills.

Do not put concrete art generation, prompt, or QA procedures in
`knowledge/capabilities/game-design.md`; that file only wires game-design nodes
to these skills.

## Asset Lifecycle And Closure

`asset-registry` is the source of truth for asset IDs, file prefixes, lifecycle
state, and handoff paths. Child skills may only advance an asset state when the
required evidence for that state exists.

Recommended lifecycle:

```text
planned -> sourced | generated -> integrated -> qa_passed -> engine_ready -> locked
```

Rules:
- `planned` means the asset exists in the registry but has no accepted runtime
  artifact.
- `sourced` or `generated` requires provenance or generation records plus files.
- `integrated` requires manifest, atlas/layer metadata, and target engine
  export profile compatibility.
- `qa_passed` requires the relevant visual/style/license/preview QA report.
- `engine_ready` requires runtime import validation when an engine/importer is
  available; if it cannot run, report blocked validation instead of substituting
  a static inspection.
- `locked` assets must not be overwritten; create a new asset ID or versioned
  replacement.

Downstream implementation must reference assets through registry IDs and
manifests, not hardcoded paths. Hardcoded asset paths are a contract violation.

Program-facing exit artifacts:

```text
.allforai/game-design/art/export/engine-ready-art-output-contract.json
.allforai/game-runtime/art/engine-ready-art-manifest.json
.allforai/game-design/art/qa/runtime-import-check-report.json
```

`engine-ready-art-output-contract` is the authoritative art-side contract.
`engine-ready-art-manifest.json` is the runtime-side subset for program nodes.
Both must agree on `asset_id`, `runtime_id`, paths, atlas/frame metadata,
fallback status, and validation evidence.

`game-frontend` is the primary client-side consumer for this manifest. It owns
loader keys, scene binding, HUD binding, animation/VFX binding, playable smoke
tests, and visual runtime regression QA.

## Example Role Chains

Skeletal character animation:

```text
10-design/art-direction-input-contract
-> 00-env/asset-registry
-> 00-env/production-tool-capability-registry
-> 20-spec/visual-style-tokens
-> 20-spec/2d-view-mode-spec
-> 20-spec/2d-layering-spec
-> 20-spec/engine-export-profile
-> 10-design/2d-animation-production-plan
-> 10-design/motion-design
-> 20-spec/character-layer-sheet
-> 20-spec/animation-state-machine-spec
-> 30-generate/skeletal-animation
-> 40-qa/art-preview-qa
-> 40-qa/2d-style-consistency-qa
-> 40-qa/runtime-import-check
-> 40-qa/engine-ready-art-output-contract
```

Legacy skeletal character animation:

```text
00-env/asset-registry
-> 10-design/2d-animation-production-plan
-> 10-design/motion-design
-> 20-spec/2d-view-mode-spec
-> 20-spec/2d-layering-spec
-> 20-spec/engine-export-profile
-> 20-spec/character-layer-sheet
-> 20-spec/animation-state-machine-spec
-> 30-generate/skeletal-animation
-> 40-qa/art-preview-qa
-> 40-qa/2d-style-consistency-qa
-> 40-qa/runtime-import-check
-> 40-qa/engine-ready-art-output-contract
```

Light 2D indie character production:

```text
10-design/art-direction-input-contract
-> 00-env/asset-registry
-> 20-spec/visual-style-tokens
-> 20-spec/2d-view-mode-spec
-> 20-spec/2d-layering-spec
-> 20-spec/engine-export-profile
-> 10-design/2d-animation-production-plan
-> 10-design/motion-design
-> 20-spec/frame-animation-spec | 20-spec/character-layer-sheet
-> 20-spec/animation-state-machine-spec
-> 30-generate/frame-animation-generation | 30-generate/skeletal-animation
-> 40-qa/art-preview-qa
-> 40-qa/2d-style-consistency-qa
-> 40-qa/atlas-packaging
-> 40-qa/runtime-import-check
-> 40-qa/engine-ready-art-output-contract
```

2.5D assisted production for 2D runtime:

```text
10-design/art-direction-input-contract
-> 00-env/asset-registry
-> 20-spec/visual-style-tokens
-> 20-spec/2d-view-mode-spec
-> 20-spec/2d-layering-spec
-> 20-spec/engine-export-profile
-> 20-spec/2-5d-production-mode-spec
-> 20-spec/3d-source-asset-spec
-> 20-spec/2-5d-lighting-shadow-spec
-> 30-generate/render-to-2d-asset-generation
-> 20-spec/artifact-handoff-contract
-> 40-qa/art-preview-qa
-> 40-qa/2d-style-consistency-qa
-> 40-qa/3d-assisted-2d-qa
-> 40-qa/atlas-packaging
-> 40-qa/runtime-import-check
-> 40-qa/engine-ready-art-output-contract
```

Existing asset pack sourcing:

```text
10-design/art-direction-input-contract
-> 00-env/asset-registry
-> 20-spec/visual-style-tokens
-> 20-spec/2d-view-mode-spec
-> 20-spec/2d-layering-spec
-> 20-spec/engine-export-profile
-> 10-design/asset-source-strategy-spec
-> 20-spec/asset-pack-search-spec
-> 40-qa/asset-license-provenance-qa
-> 20-spec/existing-asset-adaptation-spec
-> 20-spec/artifact-handoff-contract
-> 40-qa/asset-pack-integration-qa
-> 40-qa/atlas-packaging
-> 40-qa/2d-style-consistency-qa
-> 40-qa/runtime-import-check
-> 40-qa/engine-ready-art-output-contract
```

Existing 3D source to 2D runtime:

```text
10-design/art-direction-input-contract
-> 00-env/asset-registry
-> 00-env/production-tool-capability-registry
-> 20-spec/visual-style-tokens
-> 20-spec/2d-view-mode-spec
-> 20-spec/2d-layering-spec
-> 20-spec/engine-export-profile
-> 10-design/asset-source-strategy-spec
-> 20-spec/asset-pack-search-spec
-> 40-qa/asset-license-provenance-qa
-> 20-spec/existing-asset-adaptation-spec
-> 20-spec/3d-source-asset-spec
-> 20-spec/2-5d-lighting-shadow-spec
-> 30-generate/render-to-2d-asset-generation
-> 20-spec/artifact-handoff-contract
-> 40-qa/3d-assisted-2d-qa
-> 40-qa/asset-pack-integration-qa
-> 40-qa/runtime-import-check
-> 40-qa/engine-ready-art-output-contract
```

Legacy light 2D indie character production:

```text
00-env/asset-registry
-> 20-spec/visual-style-tokens
-> 20-spec/2d-view-mode-spec
-> 20-spec/2d-layering-spec
-> 10-design/2d-animation-production-plan
-> 10-design/motion-design
-> 20-spec/engine-export-profile
-> 20-spec/frame-animation-spec | 20-spec/character-layer-sheet
-> 20-spec/animation-state-machine-spec
-> 30-generate/frame-animation-generation | 30-generate/skeletal-animation
-> 40-qa/art-preview-qa
-> 40-qa/2d-style-consistency-qa
-> 40-qa/atlas-packaging
-> 40-qa/runtime-import-check
-> 40-qa/engine-ready-art-output-contract
```

Tileset generation, future:

```text
00-env/asset-registry
-> 20-spec/visual-style-tokens
-> 20-spec/2d-view-mode-spec
-> 20-spec/2d-layering-spec
-> 20-spec/engine-export-profile
-> 20-spec/tileset-spec
-> 30-generate/tileset-generation
-> 40-qa/art-preview-qa
-> 40-qa/2d-style-consistency-qa
-> 40-qa/atlas-packaging
-> 40-qa/engine-ready-art-output-contract
```

VFX generation:

```text
00-env/asset-registry
-> 20-spec/2d-view-mode-spec
-> 20-spec/2d-layering-spec
-> 20-spec/vfx-spec
-> 30-generate/vfx-generation
   -> 30-generate/particle-system     (when implementation includes particle)
   -> 30-generate/sprite-vfx-generation
   -> 30-generate/trail-generation
   -> 30-generate/shader-vfx-generation
   -> 30-generate/decal-generation
   -> 30-generate/screen-effect-generation
   -> 30-generate/mesh-burst-generation
   -> 30-generate/light-pulse-generation
   -> 30-generate/animation-event-fx
-> 40-qa/art-preview-qa          (future)
-> game-ui/00-env/ui-registry    (consumer for UI-layer VFX)
```

Icon set generation:

```text
00-env/asset-registry
-> 30-generate/image-generation-contract
-> 30-generate/icon-generation
-> 40-qa/art-preview-qa          (future)
-> game-ui/00-env/ui-registry    (consumer)
```

Image-backed asset generation:

```text
00-env/asset-registry
-> 20-spec/visual-style-tokens
-> 20-spec/2d-layering-spec
-> 30-generate/image-generation-contract
-> 30-generate/icon-generation | tileset-generation | sprite-vfx-generation | decal-generation
-> 40-qa/art-preview-qa
-> 40-qa/2d-style-consistency-qa
-> 40-qa/runtime-import-check
-> 40-qa/engine-ready-art-output-contract
```

## Non-Goals

This pack does not install tools, mutate bootstrap behavior, or register each
child as a separate top-level Claude Code skill. It is an internal bundled
Claude Code-readable capability pack that future meta-skill nodes may
explicitly call by path.
