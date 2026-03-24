---
name: dev-forge-opencode
description: Use this skill when the user wants OpenCode to execute or adapt the dev-forge workflow from this repository. It provides a OpenCode wrapper around the existing dev-forge plugin structure.
---

# Dev Forge For OpenCode

Primary sources:

- `../../dev-forge-skill/SKILL.md`
- `../../dev-forge-skill/skills/`
- `../../dev-forge-skill/commands/`
- `../../dev-forge-skill/docs/`
- `./execution-playbook.md`

OpenCode operating rules:

- Treat `/project-forge`, `/design-to-spec`, `/task-execute`,
  `/product-verify`, `/deadhunt`, `/fieldcheck`, and `/testforge` as named
  workflows.
- Translate Claude-only orchestration syntax into normal OpenCode execution.
- Preserve the existing `.allforai/project-forge/`, `.allforai/product-verify/`
  and `.allforai/deadhunt/` contracts.
- Keep the original plugin directories unchanged while using this wrapper.
- Use `execution-playbook.md` as the OpenCode-friendly orchestration authority for
  `/project-forge`.

Suggested reading order:

1. `./execution-playbook.md`
2. `../../dev-forge-skill/SKILL.md`
3. The relevant file in `../../dev-forge-skill/skills/` or
   `../../dev-forge-skill/commands/`
4. Supporting docs in `../../dev-forge-skill/docs/`

