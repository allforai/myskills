# Game Content Skill Pack

> Internal bundled sub-skill pack for meta-skill. Status: bundled, inactive, not wired.

## Purpose

Game Content owns content planning: content IDs, roadmap, quest chains,
activities, content packs, pacing, and cross-discipline ownership.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `00-env` | `content-registry` | Content IDs, packs, cadence, owners, dependencies, and states. |
| `20-spec` | `content-roadmap-spec` | Content sequence, scope, release order, dependency, and coverage plan. |
| `20-spec` | `quest-chain-spec` | Quest chains, prerequisites, objectives, rewards, narrative and level refs. |
| `20-spec` | `activity-design-spec` | Repeatable activities, daily/weekly modes, rewards, and constraints. |
| `30-generate` | `content-pack-plan-generation` | Concrete content pack plans and manifests. |
| `40-qa` | `content-pacing-qa` | Cadence, repetition, coverage, dependency, and fatigue QA. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-content/00-env/content-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-content/20-spec/content-roadmap-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-content/20-spec/quest-chain-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-content/20-spec/activity-design-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-content/30-generate/content-pack-plan-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-content/40-qa/content-pacing-qa/SKILL.md
```

## Layering Rules

Content planning consumes game design and emits requirements for level,
narrative, UI, art, audio, balance, and runtime skills. It does not generate
final assets.
