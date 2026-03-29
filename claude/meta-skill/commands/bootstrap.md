---
name: bootstrap
description: Analyze target project and generate project-specific skills, state machine, and orchestrator command.
arguments:
  - name: path
    description: Path to target project (default: current directory)
    required: false
---

Invoke the bootstrap skill to analyze this project and generate specialized configurations.

> Read ${CLAUDE_PLUGIN_ROOT}/skills/bootstrap.md and follow its protocol.
