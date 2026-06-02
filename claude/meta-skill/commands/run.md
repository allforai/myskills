---
name: run
description: Autonomously execute the bootstrapped workflow via the Workflow engine (Phase B). No human stops.
arguments:
  - name: path
    description: Path to target project (default: current directory)
    required: false
---

Execute the project's bootstrapped workflow autonomously.

> Precondition: `/bootstrap` has completed (workflow.json + all decision_inputs artifacts on disk).
> Follow the generated orchestrator protocol; for CC, invoke the Workflow engine at
> `${CLAUDE_PLUGIN_ROOT}/knowledge/run-engine/run-engine.workflow.js` and handle its
> `complete` / `needs_diagnosis` exits per `${CLAUDE_PLUGIN_ROOT}/knowledge/orchestrator-template.md`.

First verify the invariant:
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_decision_inputs.py <path>` (fallback to the
shared copy). If BLOCKED, tell the user bootstrap/Phase A is incomplete and stop.
