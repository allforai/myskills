# Game LiveOps Skill Pack

> Internal bundled sub-skill pack for meta-skill. Status: bundled, inactive, not wired.

## Purpose

Game LiveOps owns monetization, retention, recurring tasks, events, and fairness
validation for games that need ongoing operation or revenue loops.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `20-spec` | `monetization-spec` | Revenue model, offers, SKUs, ads, battle pass, gacha, and constraints. |
| `20-spec` | `retention-loop-spec` | Daily/weekly/monthly hooks, reminders, streaks, and return motivation. |
| `20-spec` | `daily-weekly-task-spec` | Task cadence, objectives, rewards, reset rules, and fatigue limits. |
| `20-spec` | `event-operation-spec` | Time-limited events, season structure, content needs, rewards, and schedule. |
| `40-qa` | `monetization-fairness-qa` | P2W, pressure, value, disclosure, fairness, and regional risk QA. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-liveops/20-spec/monetization-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-liveops/20-spec/retention-loop-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-liveops/20-spec/daily-weekly-task-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-liveops/20-spec/event-operation-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-liveops/40-qa/monetization-fairness-qa/SKILL.md
```

## Layering Rules

LiveOps is optional and should be triggered only when the game has monetization,
recurring engagement, seasons, events, or service operation goals.
