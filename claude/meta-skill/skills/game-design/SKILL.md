# Game Design Skill Pack

> Internal bundled sub-skill pack for meta-skill.
> Status: bundled, inactive, not wired.
> This directory is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads a child skill path.

## Purpose

Game Design owns the game-design and game-planning decision chain before
asset, UI, level, systems, narrative, audio, and runtime implementation work. It
turns a game idea into stable, validated contracts that downstream skills can
read without relying on conversation state.

Do not organize by document type. Organize by production decision layer:

```text
00-env        What IDs and planning entities exist?
10-concept    What player experience and loop should the game deliver?
20-spec       How should systems, content, levels, and quests work?
30-generate   What concrete tables, rosters, blockouts, and content lists exist?
40-qa         Is the game design closed, balanced, covered, and feasible?
```

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `00-env` | `game-design-registry` | Canonical feature, system, loop, resource, level, enemy, item, quest, and content-pack IDs. |
| `10-concept` | `audience-positioning-spec` | Target audience, platform expectations, reference games, differentiation, preference, and market constraints. |
| `10-concept` | `genre-hybridization-spec` | Primary and secondary genre roles, cross-genre interfaces, hybrid risks, and downstream constraints. |
| `10-concept` | `player-experience-contract` | Target player, session, platform, motivation, emotion, complexity, monetization, and preference constraints. |
| `10-concept` | `game-pillar-spec` | Design pillars, tradeoff rules, design constraints, and acceptance signals. |
| `10-concept` | `core-game-loop-spec` | Session loop, action-feedback-reward chain, failure recovery, and loop consumers. |
| `20-spec` | `game-mode-spec` | Playable modes, entry/exit conditions, objectives, rewards, difficulty, UI, and runtime state. |
| `20-spec` | `objective-system-spec` | Goal taxonomy, tracking, completion, failure, rewards, UI display, save state, and softlock prevention. |
| `20-spec` | `difficulty-experience-spec` | Pressure curve, failure frequency, recovery, assist options, difficulty modes, and telemetry signals. |
| `20-spec` | `meta-game-spec` | Long-term game outside a single run/session: collection, daily/weekly loops, mastery, seasons, social surfaces, and re-entry motivation. |
| `20-spec` | `mechanics-spec` | Core interaction rules, inputs, risks, rewards, feedback, and runtime system refs. |
| `20-spec` | `progression-spec` | Unlocks, growth, chapters, mastery, meta progression, and motivation gates. |
| `20-spec` | `economy-spec` | Resource sources, sinks, prices, rewards, inventory, exploits, and balancing hooks. |
| `20-spec` | `level-design-spec` | Level grammar, objectives, pacing, encounter placement, rewards, and art/runtime requirements. |
| `20-spec` | `combat-spec` | Damage, hit rules, enemies, skills, statuses, encounter rhythm, readability, and recovery. |
| `20-spec` | `content-taxonomy-spec` | Characters, enemies, items, skills, levels, quests, events, UI, art, audio, and runtime requirement taxonomy. |
| `20-spec` | `narrative-quest-spec` | Story constraints, quest structure, dialogue needs, triggers, rewards, and branching rules. |
| `30-generate` | `design-data-table-generation` | Program-readable JSON/CSV tables for systems, items, enemies, skills, levels, quests, and economy. |
| `30-generate` | `level-plan-generation` | Playable blockout contracts, maps, encounter/reward placement, collision, and preview requirements. |
| `30-generate` | `enemy-design-list-generation` | Enemy set, behaviors, stats, spawn roles, drops, art/VFX/audio/runtime requirements. |
| `30-generate` | `item-skill-design-generation` | Item, equipment, skill, status, icon, VFX, animation event, and data-table entries. |
| `30-generate` | `art-input-handoff-generation` | Aggregate concept and planning outputs into art input, planning documentation, and program development node handoffs. |
| `40-qa` | `core-loop-closure-qa` | Validate goals, actions, feedback, reward, next-step motivation, failure, and session closure. |
| `40-qa` | `progression-balance-qa` | Validate pacing, unlocks, difficulty, grind, content gates, and dead-end risks. |
| `40-qa` | `economy-balance-qa` | Validate source/sink closure, inflation, exploit, affordability, and resource deadlocks. |
| `40-qa` | `content-coverage-qa` | Validate that every system/content requirement has data, art, UI, audio, level, and runtime ownership. |
| `40-qa` | `implementation-feasibility-qa` | Validate engine/tool feasibility, runtime complexity, unresolved risks, and non-substituted verification. |
| `40-qa` | `contract-wiring-qa` | Validate mapped sub-skill inputs, outputs, states, repair routes, final aggregation, and downstream handoff wiring. |
| `40-qa` | `game-design-final-closure-qa` | Validate final cross-skill product-design closure before downstream implementation and import work. |

## Canonical Invocation Paths

Use these paths when a node-spec calls a child skill:

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-design/00-env/game-design-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/10-concept/audience-positioning-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/10-concept/genre-hybridization-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/10-concept/player-experience-contract/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/10-concept/game-pillar-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/10-concept/core-game-loop-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/20-spec/game-mode-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/20-spec/objective-system-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/20-spec/difficulty-experience-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/20-spec/meta-game-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/20-spec/mechanics-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/20-spec/progression-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/20-spec/economy-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/20-spec/level-design-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/20-spec/combat-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/20-spec/content-taxonomy-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/20-spec/narrative-quest-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/30-generate/design-data-table-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/30-generate/level-plan-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/30-generate/enemy-design-list-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/30-generate/item-skill-design-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/30-generate/art-input-handoff-generation/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/40-qa/core-loop-closure-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/40-qa/progression-balance-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/40-qa/economy-balance-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/40-qa/content-coverage-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/40-qa/implementation-feasibility-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/40-qa/contract-wiring-qa/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-design/40-qa/game-design-final-closure-qa/SKILL.md
```

## Shared Contracts

Game Design writes planning contracts under:

```text
.allforai/game-design/design/
.allforai/game-design/systems/
.allforai/game-design/content/
```

Downstream consumers include:

```text
game-systems/*
game-level/*
game-narrative/*
game-ui/*
game-art/*
game-audio/*
runtime implementation
```

Every downstream requirement must preserve the originating `feature_id`,
`system_id`, or `content_id`.

## Methodology Ownership

Each leaf child skill owns its own design methodology. The parent pack only
defines routing, layer order, shared contract roots, and example chains.

Methodology belongs with the artifact it produces:
- audience, hybrid genre, player experience, pillars, core loop, modes,
  objectives, difficulty, mechanics, progression, economy, level, combat,
  content, narrative quest, generated tables, and closure QA live in this pack's
  leaf `SKILL.md` files.
- art-input handoff methodology lives in
  `30-generate/art-input-handoff-generation` and is the bridge from game
  concept/planning into `game-art` and downstream program development.
- numeric tuning methodology lives in `game-balance`.
- combat-specialist methodology lives in `game-combat`.
- runtime, server, simulation, and security implementation methodology lives in
  `game-runtime`.
- level craft methodology lives in `game-level`.
- story/dialogue methodology lives in `game-narrative`.
- content cadence, onboarding, and liveops methodology live in their own packs.
- reusable genre pattern methodology lives in `game-genre-common`.

If a child needs deeper process guidance, add it to that child skill or a
directly referenced one-level resource under that child. Do not move concrete
design procedures back into `knowledge/capabilities/game-design.md`.

## Layering Rules

Allowed dependencies flow from earlier numbered layers to later numbered
layers only:

```text
00-env -> 10-concept -> 20-spec -> 30-generate -> 40-qa
```

Rules:
- A later layer may read artifacts from earlier layers.
- An earlier layer must not depend on artifacts from later layers.
- IDs must come from `game-design-registry` once it exists.
- If a required input or executable validation path is missing, return
  `UPSTREAM_DEFECT` or `FAILED_VALIDATION`; do not invent substitute evidence.
- Each child skill must define input, output, invocation, automatic validation,
  repair routing, and completion conditions.

## Example Role Chain

Full game-design pass:

```text
00-env/game-design-registry
-> 10-concept/audience-positioning-spec
-> 10-concept/genre-hybridization-spec
-> 10-concept/player-experience-contract
-> 10-concept/game-pillar-spec
-> 10-concept/core-game-loop-spec
-> 20-spec/mechanics-spec
-> 20-spec/progression-spec
-> 20-spec/economy-spec
-> 20-spec/level-design-spec
-> 20-spec/combat-spec
-> 20-spec/content-taxonomy-spec
-> 20-spec/narrative-quest-spec
-> 20-spec/game-mode-spec
-> 20-spec/objective-system-spec
-> 20-spec/difficulty-experience-spec
-> 30-generate/design-data-table-generation
-> 30-generate/level-plan-generation
-> 30-generate/enemy-design-list-generation
-> 30-generate/item-skill-design-generation
-> 30-generate/art-input-handoff-generation
-> 40-qa/core-loop-closure-qa
-> 40-qa/progression-balance-qa
-> 40-qa/economy-balance-qa
-> 40-qa/content-coverage-qa
-> 40-qa/implementation-feasibility-qa
-> 40-qa/game-design-final-closure-qa
```

Downstream handoff examples:

```text
20-spec/content-taxonomy-spec -> game-art/00-env/asset-registry
30-generate/art-input-handoff-generation -> game-art/10-design/art-direction-input-contract
20-spec/level-design-spec -> game-level/20-spec/level-layout-spec
30-generate/item-skill-design-generation -> game-art/30-generate/icon-generation
20-spec/combat-spec -> game-art/10-design/motion-design
20-spec/narrative-quest-spec -> game-narrative/20-spec/quest-text-spec
```

## Non-Goals

This pack does not replace existing `game-systems`, `game-level`,
`game-narrative`, `game-ui`, `game-art`, or implementation skills. It defines
upstream game design contracts and validation gates that those packs can consume.
