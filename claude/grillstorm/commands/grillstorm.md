---
name: grillstorm
description: Start, resume, or post-delivery audit an adaptive Grillstorm run.
arguments:
  - name: goal
    description: The goal to deliver, or a resume instruction
    required: true
---

Invoke the Grillstorm run mode for: $ARGUMENTS

> Read `${CLAUDE_PLUGIN_ROOT}/skills/grillstorm/SKILL.md` and follow its run or resume
> protocol. Do not enter handoff mode unless explicitly requested.
