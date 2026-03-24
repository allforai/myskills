---
name: myskills-codex-native
description: Use this skill when the user wants the Codex-native version of the myskills workflows without depending on Claude-specific runtime semantics.
---

# MySkills Codex Native Index

This is the top-level Codex-native entry point for this repository.

## Native workflow goals

- run without Claude slash-command semantics
- replace host-specific interaction rules with Codex operating rules
- preserve `.allforai/` artifact locations and report contracts
- keep original plugin directories as source references only

## Current native plugin status

| Plugin | Native path | Status |
|---|---|---|
| `product-design` | `./product-design-skill/SKILL.md` | pass |
| `dev-forge` | `./dev-forge-skill/SKILL.md` | pass |
| `demo-forge` | `./demo-forge-skill/SKILL.md` | pass |
| `code-tuner` | `./code-tuner-skill/SKILL.md` | pass |
| `ui-forge` | `./ui-forge-skill/SKILL.md` | pass |
| `code-replicate` | `./code-replicate-skill/SKILL.md` | pass |

## Read next

1. `./conventions.md`
2. `./migration-status.md`
3. `./completion-matrix.md`
4. `./retirement-criteria.md`
5. the plugin-specific native `SKILL.md` when present
