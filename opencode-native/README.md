# OpenCode Native Layer

This directory adds OpenCode-native entry points in parallel with the existing
Claude plugin layout.

Goals:

- keep the original `*-skill/` directories unchanged
- let OpenCode load `skills/` and `commands/` from a dedicated native layer
- reuse the original docs, scripts, and `.allforai/` contract as the source of
  truth
- adapt Claude-oriented workflow semantics into OpenCode operating rules

Primary entry points:

- `./SKILL.md`
- `./product-design-skill/SKILL.md`
- `./dev-forge-skill/SKILL.md`
- `./demo-forge-skill/SKILL.md`
- `./code-tuner-skill/SKILL.md`
- `./ui-forge-skill/SKILL.md`
- `./code-replicate-skill/SKILL.md`

Read this next:

1. `./SKILL.md`
2. `./inventory.md`
3. `./plugin-matrix.md`
4. `./runtime-gaps.md`
