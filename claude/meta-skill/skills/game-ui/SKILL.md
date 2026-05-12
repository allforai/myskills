---
name: game-ui
description: Internal bundled meta-skill module for game-ui; use within generated bootstrap node-specs when this exact contract is selected.
---

# Game UI Skill Pack

> Internal bundled sub-skill pack for meta-skill.
> Status: bundled, inactive, not wired.
> This directory is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads a child skill path.

## Purpose

Game UI is organized as composable sub-skills for player-facing interface
systems. It shares style, asset IDs, and visual tokens with `game-art`, but owns
screen flows, HUD information, layout specs, component states, UI mockups, and
readability QA.

Do not organize by tool. Organize by production layer:

```text
00-env        What UI assets, screens, and components exist?
10-design     What should the interface communicate and prioritize?
20-spec       How should screens and components be structured?
30-generate   How are mockups, UI assets, or implementation prompts produced?
40-qa         Can the UI be read, tapped, and used without harming gameplay?
```

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `00-env` | `ui-registry` | Canonical screen IDs, component IDs, UI asset IDs, paths, states, dependencies. |
| `10-design` | `ui-flow-design` | Screen graph, player journey, transitions, modal rules, recovery paths. |
| `10-design` | `hud-information-design` | HUD information priority, visibility rules, gameplay protection, fallback HUD. |
| `20-spec` | `screen-layout-spec` | Responsive screen layout, safe zones, regions, navigation, breakpoint rules. |
| `20-spec` | `component-state-spec` | Button, bar, card, icon, modal, list, and control states with validation. |
| `30-generate` | `ui-mockup-generation` | Mockup prompts/specs, generated previews, repair loop, export manifest. |
| `40-qa` | `ui-readability-qa` | Automated checks for readability, tap targets, contrast, overlap, and playfield protection. |

## Canonical Invocation Paths

Use these paths when a node-spec calls a child skill:

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-ui/00-env/ui-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-ui/10-design/ui-flow-design/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-ui/10-design/hud-information-design/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-ui/20-spec/screen-layout-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-ui/20-spec/component-state-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-ui/30-generate/ui-mockup-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-ui/40-qa/ui-readability-qa/SKILL.md
```

## Shared Contracts

Game UI must read shared visual contracts before inventing UI-specific style:

```text
.allforai/concept-contract.json
.allforai/game-design/art-style-guide.json
.allforai/game-design/asset-registry.json
```

Game UI writes UI-specific contracts under:

```text
.allforai/game-design/ui/
```

The pack must not regenerate world-art assets that already exist in
`asset-registry.json`. UI screens may reference icons, portraits, currencies,
items, and character art by asset ID.

## Layering Rules

Allowed dependencies flow from earlier numbered layers to later numbered layers
only:

```text
00-env -> 10-design -> 20-spec -> 30-generate -> 40-qa
```

Rules:
- A later layer may read artifacts from earlier layers.
- An earlier layer must not depend on artifacts from later layers.
- UI asset IDs, screen IDs, and component IDs must come from `ui-registry` once
  it exists.
- Each child skill must define `Input Contract`, `Output Contract`,
  `Invocation Contract`, automatic validation, and completion conditions.
- If a child skill cannot complete, it must return a structured status such as
  `UPSTREAM_DEFECT`, `FAILED_VALIDATION`, or `COMPLETED_WITH_LIMITS`.

## Example Role Chain

Full UI planning and mockup:

```text
00-env/ui-registry
-> 10-design/ui-flow-design
-> 10-design/hud-information-design
-> 20-spec/screen-layout-spec
-> 20-spec/component-state-spec
-> 30-generate/ui-mockup-generation
-> 40-qa/ui-readability-qa
```

HUD-only integration:

```text
00-env/ui-registry
-> 10-design/hud-information-design
-> 20-spec/screen-layout-spec
-> 20-spec/component-state-spec
-> 40-qa/ui-readability-qa
```

## Non-Goals

This pack does not install tools, mutate bootstrap behavior, register a
top-level Claude Code skill, or replace frontend implementation skills. It is an
internal bundled capability pack that future meta-skill nodes may explicitly
call.
