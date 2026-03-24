---
name: myskills-opencode-native
description: Use this skill when the user wants to access the OpenCode-native wrappers for the myskills repository, including product-design, dev-forge, demo-forge, code-tuner, ui-forge, and code-replicate.
---

# MySkills OpenCode Native Index

This is the top-level OpenCode entry point for the native layer in this
repository.

## Available native skills

| Skill | Path | Use when |
|---|---|---|
| `product-design` | `./product-design-skill/SKILL.md` | the user wants product concept, mapping, journey, experience, gap, or audit workflows |
| `dev-forge` | `./dev-forge-skill/SKILL.md` | the user wants project setup, design-to-spec, task execution, or verification loops |
| `demo-forge` | `./demo-forge-skill/SKILL.md` | the user wants demo data planning, media acquisition, execution, or verification |
| `code-tuner` | `./code-tuner-skill/SKILL.md` | the user wants architecture analysis, duplication checks, or abstraction recommendations |
| `ui-forge` | `./ui-forge-skill/SKILL.md` | the user wants UI generation or structured UI iteration with repository context |
| `code-replicate` | `./code-replicate-skill/SKILL.md` | the user wants code replication or fidelity-oriented adaptation |

## Operating rules

- Use the plugin-specific `SKILL.md` as the execution authority for that
  workflow.
- Prefer each plugin's `execution-playbook.md` when it exists.
- Keep the original source plugin directories unchanged.
- Preserve existing `.allforai/` contracts and file locations.

## Supporting docs

- `./README.md`
- `./compatibility-guide.md`
- `./plugin-matrix.md`
- `./runtime-gaps.md`
- `./native-roadmap.md`

