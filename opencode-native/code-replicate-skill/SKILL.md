---
name: code-replicate-opencode
description: Use this skill when the user wants OpenCode to apply the code-replicate workflows in this repository for reverse engineering, fidelity checking, or implementation replication.
---

# Code Replicate For OpenCode

Primary sources:

- `../../code-replicate-skill/SKILL.md`
- `../../code-replicate-skill/skills/`
- `../../code-replicate-skill/docs/`
- `./execution-playbook.md`

OpenCode operating rules:

- Use the original replication and fidelity documents as the canonical source.
- Follow the OpenCode-friendly execution playbook in `./execution-playbook.md`.
- Treat phase and slash-command references as labels for workflow routing.
- Keep the workflow artifact-oriented and read-only by default.
- Keep the OpenCode wrapper thin and non-invasive while compatibility is
  incremental.

