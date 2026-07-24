---
name: handoff
description: Checkpoint the active Grillstorm run so another session or machine can resume it.
arguments:
  - name: focus
    description: What the next session should focus on
    required: false
---

Invoke Grillstorm handoff mode. Treat these arguments as the next-session focus:
$ARGUMENTS

> Read `${CLAUDE_PLUGIN_ROOT}/skills/grillstorm/SKILL.md`, then
> `${CLAUDE_PLUGIN_ROOT}/skills/grillstorm/references/handoff.md`. Write the default durable
> repository handoff, or a temporary handoff only when `local` was explicitly requested,
> then stop without continuing implementation.
