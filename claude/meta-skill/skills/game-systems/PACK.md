---
name: game-systems
description: Internal bundled meta-skill module for game-systems; use within generated bootstrap node-specs when this exact contract is selected.
---

# Game Systems Skill Pack

> Internal bundled sub-skill pack for meta-skill. Status: bundled, inactive, not wired.

## Purpose

Game Systems owns core loop, economy, progression, combat, and balance sanity
contracts. It does not generate art/audio/UI directly; it feeds those pipelines.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `10-design` | `core-loop-design` | Primary loop, session structure, goals, failure/retry. |
| `20-spec` | `economy-spec` | Resources, sinks, sources, prices, rewards, constraints. |
| `20-spec` | `progression-spec` | Unlocks, levels, XP, gates, pacing, difficulty schedule. |
| `20-spec` | `combat-spec` | Actors, stats, actions, damage, cooldowns, status effects. |
| `20-spec` | `inventory-system-spec` | Item storage, stack, slot, capacity, sorting, loss, UI, and data rules. |
| `20-spec` | `crafting-system-spec` | Recipes, inputs, outputs, stations, unlocks, failure, economy, and UI rules. |
| `20-spec` | `building-system-spec` | Placement, grid, snapping, costs, collisions, upgrades, permissions, and persistence rules. |
| `20-spec` | `social-system-spec` | Relationship, reputation, party, guild, gifting, dialogue, and reward rules. |
| `20-spec` | `achievement-system-spec` | Achievement triggers, progress tracking, rewards, visibility, and anti-cheese rules. |
| `40-qa` | `balance-sanity-qa` | Numeric sanity, exploit checks, pacing and difficulty warnings. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-systems/10-design/core-loop-design/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-systems/20-spec/economy-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-systems/20-spec/progression-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-systems/20-spec/combat-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-systems/20-spec/inventory-system-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-systems/20-spec/crafting-system-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-systems/20-spec/building-system-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-systems/20-spec/social-system-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-systems/20-spec/achievement-system-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-systems/40-qa/balance-sanity-qa/SKILL.md
```

## Layering Rules

Dependencies flow from earlier numbered layers to later numbered layers only.
