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
| `40-qa` | `balance-sanity-qa` | Numeric sanity, exploit checks, pacing and difficulty warnings. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-systems/10-design/core-loop-design/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-systems/20-spec/economy-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-systems/20-spec/progression-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-systems/20-spec/combat-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-systems/40-qa/balance-sanity-qa/SKILL.md
```

## Layering Rules

Dependencies flow from earlier numbered layers to later numbered layers only.
