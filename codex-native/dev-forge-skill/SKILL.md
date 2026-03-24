---
name: dev-forge-codex-native
description: Use this skill when the user wants dev-forge workflows in a Codex-native form, including deadhunt, fieldcheck, testforge, and the main forge pipeline.
---

# Dev Forge For Codex Native

Primary sources:

- `../../dev-forge-skill/SKILL.md`
- `../../dev-forge-skill/commands/`
- `../../dev-forge-skill/skills/`
- `./execution-playbook.md`
- `./commands/project-forge.md`
- `./commands/deadhunt.md`
- `./commands/fieldcheck.md`
- `./commands/testforge.md`

Codex-native rules:

- use `./execution-playbook.md` for `/project-forge`
- use the native command docs here for `deadhunt`, `fieldcheck`, and
  `testforge`
- keep `.allforai/project-forge/`, `.allforai/deadhunt/`,
  `.allforai/product-verify/`, and `.allforai/testforge/` unchanged
- treat source command files as domain references, not runtime requirements
