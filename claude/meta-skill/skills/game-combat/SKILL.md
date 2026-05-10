# Game Combat Skill Pack

> Internal bundled sub-skill pack for meta-skill. Status: bundled, inactive, not wired.

## Purpose

Game Combat owns combat designer contracts: player skills, enemy behaviors,
status effects, boss encounters, readability, and combat feedback requirements.
It consumes game design and balance specs and emits requirements for art, VFX,
animation, audio, UI, data, and runtime implementation.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `20-spec` | `skill-design-spec` | Player skills, activation, cost, cooldown, targeting, scaling, and feedback. |
| `20-spec` | `enemy-behavior-spec` | Enemy roles, state machines, telegraphs, counterplay, and AI requirements. |
| `20-spec` | `status-effect-spec` | Buffs, debuffs, DOT/HOT, crowd control, stacking, duration, and cleansing. |
| `20-spec` | `boss-encounter-spec` | Boss phases, mechanics, arena constraints, tells, rewards, and fail recovery. |
| `40-qa` | `combat-readability-qa` | Telegraph, feedback, state clarity, VFX/audio/UI readability, and fairness QA. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-combat/20-spec/skill-design-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-combat/20-spec/enemy-behavior-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-combat/20-spec/status-effect-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-combat/20-spec/boss-encounter-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-combat/40-qa/combat-readability-qa/SKILL.md
```

## Layering Rules

Combat planning consumes game design, systems, and balance contracts. It does
not generate final art or code; it emits combat requirements and QA reports.
