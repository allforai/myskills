# Orchestrator Template

> Template for generating .claude/commands/run.md in target projects.
> Bootstrap reads this and writes a customized version.

## Template: run.md

Below is the complete content that bootstrap writes to `.claude/commands/run.md`.

---

~~~markdown
---
name: run
description: Execute the project workflow. Specify a goal.
arguments:
  - name: goal
    description: What you want to achieve (natural language)
    required: true
---

# Workflow Orchestrator

You are the workflow orchestrator. Execute nodes to achieve the goal.

## Ground Truth

Read `.allforai/bootstrap/workflow.json` at every iteration. Trust it over conversation history.

## Core Loop

```
每轮：
  1. Read workflow.json (nodes + transition_log)
  2. Run: python .allforai/bootstrap/scripts/check_artifacts.py .allforai/bootstrap/workflow.json --json
  3. Review which nodes are done (exit_artifacts exist) and which are pending
  4. Decide next node:
     - What's done? What's pending? What makes sense next?
     - Can run multiple nodes in parallel if their exit_artifacts don't overlap
     - Can skip a node if its goal is already satisfied
     - Can re-run a failed node after fixing the issue
  5. Read the node-spec: .allforai/bootstrap/node-specs/<node-id>.md
  6. Dispatch subagent with node-spec as prompt
  7. On success: record transition (status=completed, artifacts_created)
  8. On failure: record transition (status=failed, error=<one line>),
     then read .allforai/bootstrap/protocols/diagnosis.md and diagnose
  9. Back to 1
```

## Recording Transitions

After each node completes or fails, append to workflow.json transition_log:

```json
{
  "node": "<id>",
  "status": "completed | failed",
  "started_at": "<ISO timestamp>",
  "completed_at": "<ISO timestamp>",
  "artifacts_created": ["<file paths>"],
  "error": "<one line, only if failed>"
}
```

## Session Resume

On first iteration if transition_log is non-empty:
1. Run check_artifacts.py to see current state
2. Trust artifact existence over transition_log (files may have been deleted)
3. Continue from where things stand

## Safety (warnings, not blockers)

- Same node fails 3 times → warn user, ask if they want to continue
- 5 iterations with no new artifacts → output current state + TODO list
- Single node running > 10 minutes → warn but don't kill

## Termination

- All nodes' exit_artifacts exist → success report
- User interrupts → transition_log is already saved, resume with /run
- Safety warning acknowledged → continue or stop per user choice

## Post-Completion

1. Read `.allforai/bootstrap/protocols/learning-protocol.md` — extract experience
2. Read `.allforai/bootstrap/protocols/feedback-protocol.md` — propose feedback
~~~
