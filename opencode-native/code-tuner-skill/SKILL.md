---
name: code-tuner-opencode
description: Use this skill when the user wants OpenCode to analyze backend architecture, duplication, abstraction opportunities, or technical debt using the code-tuner workflow from this repository.
---

# Code Tuner For OpenCode

Primary sources:

- `../../code-tuner-skill/SKILL.md`
- `../../code-tuner-skill/commands/code-tuner.md`
- `../../code-tuner-skill/references/`
- `./execution-playbook.md`

OpenCode operating rules:

- Treat `/code-tuner full`, `compliance`, `duplication`, `abstraction`, and
  `report` as workflow modes, not literal commands.
- Follow the OpenCode-friendly execution playbook in `./execution-playbook.md`.
- Run the same source phase sequence as the original plugin.
- Default lifecycle to `pre-launch` unless the user clearly indicates a live
  maintenance system.
- Refuse frontend-only or non-backend repositories.
- Keep analysis read-only unless the user explicitly asks for fixes.
- Reuse the `.allforai/code-tuner/` output contract when generating results.

This plugin is the best candidate for early OpenCode-friendly execution because it
depends more on repository analysis than on Claude-specific interactive command
routing.

