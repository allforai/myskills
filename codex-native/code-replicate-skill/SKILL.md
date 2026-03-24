---
name: code-replicate-codex-native
description: Use this skill when the user wants the code-replicate workflow in a Codex-native form for reverse engineering, fidelity extraction, or downstream artifact generation.
---

# Code Replicate For Codex Native

Primary sources:

- `../../code-replicate-skill/SKILL.md`
- `../../code-replicate-skill/skills/`
- `../../code-replicate-skill/docs/`
- `./execution-playbook.md`
- `./commands/code-replicate.md`
- `./skills/code-replicate-core.md`

Codex-native rules:

- use `./execution-playbook.md` as the execution authority
- use the native command and core-skill docs here as the primary entry points
- keep source code read-only unless the user explicitly broadens the task
- preserve `.allforai/code-replicate/` and downstream artifact contracts
