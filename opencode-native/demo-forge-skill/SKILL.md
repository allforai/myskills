---
name: demo-forge-opencode
description: Use this skill when the user wants OpenCode to work with the demo-forge workflow from this repository. It adapts the existing demo-forge plugin to a OpenCode-friendly entry point.
---

# Demo Forge For OpenCode

Primary sources:

- `../../demo-forge-skill/SKILL.md`
- `../../demo-forge-skill/skills/`
- `../../demo-forge-skill/commands/`
- `../../demo-forge-skill/docs/`
- `./execution-playbook.md`

OpenCode operating rules:

- Treat `/demo-forge`, `design`, `media`, `execute`, `verify`, `clean`, and
  `status` as workflow names.
- Preserve the existing `.allforai/demo-forge/` artifact contract.
- When the source workflow references Playwright or media tooling, use OpenCode
  tools only when available and otherwise report the missing capability clearly.
- Use the existing plugin documentation as the canonical behavior definition.
- Use `execution-playbook.md` as the OpenCode-friendly orchestration authority for
  `/demo-forge`.

