---
name: product-design-codex-native
description: Use this skill when the user wants the product-design workflow in a Codex-native form, including product setup, review handling, and the main artifact pipeline.
---

# Product Design For Codex Native

Primary sources:

- `../../product-design-skill/SKILL.md`
- `../../product-design-skill/skills/`
- `../../product-design-skill/commands/`
- `./execution-playbook.md`
- `./commands/product-design.md`
- `./commands/setup.md`
- `./commands/review.md`

Codex-native rules:

- use `./execution-playbook.md` for the main multi-phase workflow
- use the native `setup` and `review` documents in this directory instead of
  the thin compatibility wrappers
- keep `.allforai/` artifact paths unchanged
- treat source files as references for intent, not required runtime syntax

Suggested reading order:

1. `./execution-playbook.md`
2. `./commands/setup.md` when external capability setup is relevant
3. `./commands/review.md` when review hub or feedback processing is relevant
4. the relevant source skill in `../../product-design-skill/skills/`
