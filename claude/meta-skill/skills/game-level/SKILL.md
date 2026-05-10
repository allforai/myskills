# Game Level Skill Pack

> Internal bundled sub-skill pack for meta-skill. Status: bundled, inactive, not wired.

## Purpose

Game Level owns level/map structure. It consumes game design, tilesets, props,
VFX, and runtime constraints, but it does not generate art assets directly.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `00-env` | `level-registry` | Level IDs, map IDs, paths, states, dependencies. |
| `10-design` | `level-flow-design` | Level pacing, sequence, objectives, difficulty beats. |
| `20-spec` | `level-layout-spec` | Layout grammar, rooms/lanes/grid/blockout rules, spawn/goal specs. |
| `20-spec` | `level-difficulty-budget-spec` | Per-level/region difficulty and psychological budgets: pressure, emotion, cognitive load, recovery, spike, reward, and validation probes. |
| `20-spec` | `teaching-beat-spec` | Mechanics teaching beats, safe practice, tests, and recovery. |
| `20-spec` | `encounter-placement-spec` | Encounter placement, enemy/hazard composition, difficulty, and counterplay. |
| `20-spec` | `reward-placement-spec` | Reward placement, risk/cost, visibility, reachability, and economy pacing. |
| `30-generate` | `level-blockout-generation` | Blockout maps, collision/walkability metadata, previews. |
| `40-qa` | `level-playability-qa` | Reachability, pacing, collision, objective, and preview checks. |
| `40-qa` | `level-pacing-qa` | Teaching, encounter, reward, rest, and difficulty pacing QA. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-level/00-env/level-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-level/10-design/level-flow-design/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-level/20-spec/level-layout-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-level/20-spec/level-difficulty-budget-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-level/20-spec/teaching-beat-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-level/20-spec/encounter-placement-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-level/20-spec/reward-placement-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-level/30-generate/level-blockout-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-level/40-qa/level-playability-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-level/40-qa/level-pacing-qa/SKILL.md
```

## Layering Rules

Dependencies flow from earlier numbered layers to later numbered layers only.
Every child skill must define input, output, invocation, automatic validation,
and completion conditions.
