# Game Balance Skill Pack

> Internal bundled sub-skill pack for meta-skill. Status: bundled, inactive, not wired.

## Purpose

Game Balance owns numeric design contracts for progression, economy, drops,
rewards, prices, damage formulas, and balance validation. It consumes game
design intent and outputs structured numeric tables and QA reports.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `00-env` | `balance-registry` | Numeric IDs, curves, tables, formulas, owners, and states. |
| `10-design` | `balance-goal-spec` | Target pacing, difficulty, reward, fairness, and tuning goals. |
| `20-spec` | `progression-curve-spec` | XP, level, unlock, power, and session pacing curves. |
| `20-spec` | `economy-source-sink-spec` | Resource source/sink rates, caps, exchanges, and deadlock rules. |
| `20-spec` | `drop-table-spec` | Loot/drop probability, pity, rarity, and expected value rules. |
| `20-spec` | `reward-pricing-spec` | Prices, rewards, upgrade costs, affordability, and value anchors. |
| `20-spec` | `damage-formula-spec` | Damage, defense, scaling, crit, status, and TTK formulas. |
| `30-generate` | `balance-table-generation` | JSON/CSV numeric tables and manifests. |
| `40-qa` | `combat-balance-qa` | TTK, DPS, survivability, counterplay, and outlier QA. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-balance/00-env/balance-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-balance/10-design/balance-goal-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-balance/20-spec/progression-curve-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-balance/20-spec/economy-source-sink-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-balance/20-spec/drop-table-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-balance/20-spec/reward-pricing-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-balance/20-spec/damage-formula-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-balance/30-generate/balance-table-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-balance/40-qa/combat-balance-qa/SKILL.md
```

## Layering Rules

Dependencies flow `00-env -> 10-design -> 20-spec -> 30-generate -> 40-qa`.
Every child must define input, output, invocation, automatic validation, repair
routing, and completion conditions. Missing executable validation is a blocker,
not substitute evidence.
