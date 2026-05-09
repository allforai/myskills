# Game Art Skill Pack

> Internal bundled sub-skill pack for meta-skill.
> Status: bundled, inactive, not wired.
> This directory is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads a child skill path.

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

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `00-env` | `asset-registry` | Canonical asset IDs, file prefixes, paths, lifecycle states, validation report. |
| `10-design` | `motion-design` | Animation intent, key poses, timing, events, readability, fallback motion. |
| `20-spec` | `character-layer-sheet` | Character part decomposition, layer-sheet prompt/spec, pivots, validation. |
| `20-spec` | `tileset-spec` | Tilemap mode selection, terrain vocabulary, tile rules, collision/walkability contracts. |
| `30-generate` | `icon-generation` | Skill, item, currency, ability, status, and UI icon set generation with consistency QA. |
| `30-generate` | `tileset-generation` | Tileset prompts, generated tile sheets, atlas manifests, preview maps, repair loop. |
| `30-generate` | `skeletal-animation` | Bone hierarchy, transform timelines, rendered preview loop, visual validation, repair. |

## Canonical Invocation Paths

Use these paths when a node-spec calls a child skill:

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-art/00-env/asset-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/motion-design/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/character-layer-sheet/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/tileset-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/icon-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/tileset-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/skeletal-animation/SKILL.md
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
- If a child skill cannot complete, it must return a structured status such as
  `UPSTREAM_DEFECT`, `FAILED_VALIDATION`, or `COMPLETED_WITH_LIMITS`.

## Example Role Chains

Skeletal character animation:

```text
00-env/asset-registry
-> 10-design/motion-design
-> 20-spec/character-layer-sheet
-> 30-generate/skeletal-animation
-> 40-qa/art-preview-qa          (future)
-> 40-qa/runtime-import-check    (future)
```

Tileset generation, future:

```text
00-env/asset-registry
-> 10-design/visual-style-tokens
-> 20-spec/tileset-spec
-> 30-generate/tileset-generation
-> 40-qa/art-preview-qa
-> 40-qa/atlas-packaging
```

VFX generation, future:

```text
00-env/asset-registry
-> 10-design/motion-design
-> 20-spec/vfx-beat-sheet
-> 30-generate/vfx-generation
-> 40-qa/art-preview-qa
```

Icon set generation:

```text
00-env/asset-registry
-> 30-generate/icon-generation
-> 40-qa/art-preview-qa          (future)
-> game-ui/00-env/ui-registry    (consumer)
```

## Non-Goals

This pack does not install tools, mutate bootstrap behavior, or register a
top-level Claude Code skill. It is an internal bundled capability pack that
future meta-skill nodes may explicitly call.
