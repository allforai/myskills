---
name: product-design-opencode
description: Use this skill when the user wants OpenCode to run or reason about the product-design workflow in this repository. It wraps the existing product-design plugin for OpenCode without changing the original Claude/OpenCode layout.
---

# Product Design For OpenCode

This wrapper adapts the existing product-design plugin to OpenCode.

Primary sources:

- `../../product-design-skill/SKILL.md`
- `../../product-design-skill/skills/`
- `../../product-design-skill/commands/`
- `../../product-design-skill/docs/`
- `../../product-design-skill/scripts/`
- `./execution-playbook.md`

OpenCode operating rules:

- Treat `/product-design full`, `/product-map`, `/review`, and related slash
  commands as workflow names, not literal terminal commands.
- Follow the OpenCode-friendly execution playbook in `./execution-playbook.md`.
- When the original workflow says `AskUserQuestion`, ask the user only if the
  missing choice would materially block progress.
- Reuse the `.allforai/` contract exactly as documented in the source plugin.
- Prefer reading the source plugin files directly rather than duplicating logic
  into this wrapper.

Suggested reading order:

1. `../../product-design-skill/SKILL.md`
2. The specific file in `../../product-design-skill/skills/` for the active
   phase
3. Any referenced docs in `../../product-design-skill/docs/`

Scope:

- This wrapper is intentionally thin.
- The original `product-design-skill/` directory remains the source of truth.

