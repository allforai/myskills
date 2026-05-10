# Game Product Subskills

## Goal

Add a game-product skill pack that decomposes game planning and product design
into small Claude Code-readable sub-skills. The pack owns upstream product
contracts and hands structured requirements to systems, level, narrative, UI,
art, audio, data, and runtime implementation flows.

## Scope

- Product and player experience contracts.
- Core loop, pillars, mechanics, progression, economy, combat, levels,
  narrative/quest, and content taxonomy specs.
- Structured game data table, level blockout, enemy roster, and item/skill
  generation contracts.
- QA loops for core-loop closure, progression, economy, content coverage, and
  implementation feasibility.
- No bootstrap wiring in this task.

## Tasks

- [x] Add `game-product/SKILL.md` pack entry.
- [x] Add `00-env/game-design-registry`.
- [x] Add `10-concept` player experience, pillar, and core loop sub-skills.
- [x] Add `20-spec` mechanics, progression, economy, level, combat, taxonomy,
  and narrative/quest sub-skills.
- [x] Add `30-generate` data table, level blockout, enemy roster, and item/skill
  generation sub-skills.
- [x] Add `40-qa` loop, progression, economy, content coverage, and
  feasibility QA sub-skills.
- [x] Verify each sub-skill has input, output, invocation, automatic validation,
  repair routing, and completion conditions.
