# Orchestrator Template (Codex)

> Template for generating `.codex/commands/run.md` inside target projects.
> Bootstrap reads this template and writes a project-local Codex run entry.

## Template: run.md

Below is the Codex-native content that bootstrap should render into `.codex/commands/run.md`.

~~~markdown
---
description: "Execute the generated project workflow toward a natural-language goal."
---

# Run — Workflow Orchestrator

User goal: `$ARGUMENTS`

## Ground Truth

Read `.allforai/bootstrap/workflow.json` at every iteration.
Trust project-local artifacts over conversation history.
If `.allforai/bootstrap/product-summary.json` exists, treat it as the current best product inference baseline.

## Core Loop

每轮：
1. Read `.allforai/bootstrap/workflow.json`
2. Run `python .allforai/bootstrap/scripts/check_artifacts.py .allforai/bootstrap/workflow.json --json`
3. Review which nodes are done and which are pending
4. Decide the next node:
   - prefer nodes whose upstream artifacts already exist
   - parallelize only when exit artifacts do not overlap
   - skip a node if its goal is already satisfied by current project state
   - re-run a failed node only after addressing the cause
5. Read `.allforai/bootstrap/node-specs/<node-id>.md`
6. Dispatch execution using that node-spec as the task contract
7. On success: append a completed transition entry to `workflow.json`
8. On failure: append a failed transition entry, then read `.allforai/bootstrap/protocols/diagnosis.md`
9. Repeat

## Recording Transitions

After each node completes or fails, append to `workflow.json`:

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

On the first iteration, if `transition_log` is non-empty:

1. run `check_artifacts.py` to inspect current state
2. trust artifact existence over the saved transition log
3. continue from the current project state

## Safety

- Same node fails 3 times: stop automatic retries, run diagnosis, and record `diagnosis_history`
- 5 iterations with no new artifacts: stop and output current best state plus TODOs
- Single node running too long: warn, do not silently discard work

## Termination

- All required exit artifacts exist: report success
- `concept-acceptance` verdict = `needs_iteration`: output acceptance summary, stop, and ask whether to fix, re-bootstrap, or accept
- User interrupts: the next run resumes from `workflow.json`

## Post-Completion

1. If `.allforai/bootstrap/product-summary.json` exists, run `python .allforai/bootstrap/scripts/check_product_summary.py .allforai/bootstrap/product-summary.json`
2. Read `.allforai/bootstrap/protocols/learning-protocol.md`
3. Read `.allforai/bootstrap/protocols/feedback-protocol.md`
4. Summarize reusable experience and proposed feedback

## Non-Stop Driver

If the workflow should keep moving until completion without stopping for "next step" confirmation, use:

`python .allforai/codex/flow.py`

This Codex-only outer driver repeatedly relaunches Codex against pending nodes until:

- all required exit artifacts exist
- the same node fails 3 times and a diagnosis record is written
- 5 consecutive transitions create no new artifacts
- or the driver's max-iteration safety limit is reached
~~~
