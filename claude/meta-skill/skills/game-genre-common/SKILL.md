# Game Genre Common Skill Pack

> Internal bundled sub-skill pack for meta-skill. Status: bundled, inactive, not wired.

## Purpose

Game Genre Common owns design patterns used by multiple genres but not by every
game. Concrete genre packs should compose these shared contracts instead of
duplicating them.

Use this layer between universal game design skills and concrete genre skills.

```text
Universal planning: game-design, game-balance, game-combat, game-level, game-content
Genre-common: run, deck, procedural, faction, collection, tech tree, relationship patterns
Genre-specific: game-roguelike, game-card, game-rpg, game-strategy, game-sim, etc.
```

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `20-spec` | `run-structure-spec` | Run/session branch structure for roguelike, dungeon, ladder, and challenge modes. |
| `20-spec` | `deck-building-spec` | Deck, hand, draw, discard, card pool, and build rules. |
| `20-spec` | `procedural-content-spec` | Seeded generation constraints, validation, distributions, and repair rules. |
| `20-spec` | `faction-system-spec` | Factions, relations, reputation, diplomacy, territory, and conflict rules. |
| `20-spec` | `collection-system-spec` | Collection catalogue, rarity, ownership, completion, display, and rewards. |
| `20-spec` | `tech-tree-spec` | Research tree, prerequisites, unlocks, pacing, and cost rules. |
| `20-spec` | `relationship-system-spec` | Relationship/affinity/trust systems, events, gifts, thresholds, and consequences. |
| `20-spec` | `quest-pattern-spec` | Reusable quest pattern grammar across RPG, sim, strategy, and narrative games. |
| `40-qa` | `genre-fit-qa` | Validate that selected genre-common contracts actually fit the selected genre. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-genre-common/20-spec/run-structure-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-genre-common/20-spec/deck-building-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-genre-common/20-spec/procedural-content-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-genre-common/20-spec/faction-system-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-genre-common/20-spec/collection-system-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-genre-common/20-spec/tech-tree-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-genre-common/20-spec/relationship-system-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-genre-common/20-spec/quest-pattern-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-genre-common/40-qa/genre-fit-qa/SKILL.md
```

## Layering Rules

Genre-common skills consume universal game design contracts and emit reusable
genre pattern contracts. Concrete genre packs may depend on these outputs, but
these skills must not depend on a single concrete genre pack.
