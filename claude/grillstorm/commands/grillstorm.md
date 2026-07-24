---
name: grillstorm
description: Start, resume, or post-delivery audit an adaptive Grillstorm run.
arguments:
  - name: goal
    description: The goal to deliver, or a resume instruction
    required: true
---

Invoke the Grillstorm mode selected by: $ARGUMENTS

> Read `${CLAUDE_PLUGIN_ROOT}/skills/grillstorm/SKILL.md` and follow its run, resume, or
> post-delivery audit protocol. Do not enter handoff mode unless explicitly requested.
