---
name: code-tuner-codex-native
description: Use this skill when the user wants backend architecture analysis, duplication review, abstraction recommendations, or code-tuner reporting in a Codex-native form.
---

# Code Tuner For Codex Native

Primary sources:

- `../../code-tuner-skill/SKILL.md`
- `../../code-tuner-skill/commands/code-tuner.md`
- `../../code-tuner-skill/references/`
- `./execution-playbook.md`

Codex-native rules:

- use `./execution-playbook.md` as the execution authority
- keep analysis read-only unless the user explicitly asks for fixes
- preserve `.allforai/code-tuner/` outputs and scoring contract
- refuse frontend-only or non-backend repositories
