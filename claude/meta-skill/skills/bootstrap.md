---
name: bootstrap
description: >
  Internal skill for /bootstrap command. Performs lightweight project analysis,
  generates project-specific node-specs and state-machine.json, validates products,
  and writes to target project.
---

# Bootstrap Protocol v0.1.0

> Full implementation in Plan 3. This is the skeleton.

## Steps

1. Lightweight analysis -> bootstrap-profile.json
2. Select relevant knowledge (node templates + mappings + domains)
3. LLM generates node-specs
4. Generate state-machine.json
5. Generate .claude/commands/run.md
5.5. Validate products (structure + graph + safety + user confirmation)
6. Write files to target project
