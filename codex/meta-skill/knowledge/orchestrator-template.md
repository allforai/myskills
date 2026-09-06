# Orchestrator Template (Codex)

> Template for generating `.codex/commands/run.md` inside target projects.
> Bootstrap reads this template and writes a project-local Codex run entry.
> Codex keeps a markdown loop plus `.allforai/codex/flow.py`. It does not invoke
> the Claude Workflow JS engine. Shared contracts stay on `workflow.json` and
> the copied `scripts/orchestrator` helpers.

## Template: run.md

Below is the Codex-native content that bootstrap should render into `.codex/commands/run.md`.

~~~markdown
---
description: "Execute the generated project workflow toward a natural-language goal."
---

# Run — Workflow Orchestrator

User goal: `$ARGUMENTS`

If no goal argument is provided, reuse the task goal captured during `bootstrap` from `.allforai/bootstrap/bootstrap-profile.json`.

## Ground Truth

Read `.allforai/bootstrap/workflow.json` at every iteration.
Trust project-local artifacts over conversation history.
If `.allforai/bootstrap/product-summary.json` exists, treat it as the current best product inference baseline.

Treat `.allforai/bootstrap/*` artifacts as the canonical completion surface for workflow nodes.
Project docs under `docs/bootstrap/` may be updated, but they should not be the only completion signal for a node.

## Preflight Gate

Before executing any workflow node:

```bash
python3 .allforai/bootstrap/scripts/record_run_event.py . --event run_started --status started --message "codex run command invoked"
python3 .allforai/bootstrap/scripts/validate_unattended_readiness.py . --write-report
```

If the readiness command exits non-zero or `.allforai/bootstrap/unattended-run-readiness.json` has `status != "ready"`, stop immediately. Do not start partial execution and do not silently weaken validation. Report the blockers from `.allforai/bootstrap/unattended-run-readiness.md`.
Missing scripts, missing/invalid readiness reports, and failed expanders also block execution.
Before stopping, record `preflight_blocked` with `record_run_event.py`, then run `summarize_run_log.py --write-report`.

### Dynamic preflight reconciliation

Before every execution wave, run every idempotent expander declared by `workflow.json.expanders`, including `expand_game_2d_production.py` when that script was copied. An expander may add or repair nodes after an upstream node creates a trigger artifact. Re-read the changed DAG and rerun `validate_unattended_readiness.py`; do not execute newly exposed work when readiness is not `ready`.

## Core Loop

每轮：
1. Read `.allforai/bootstrap/workflow.json`
2. Run `python3 .allforai/bootstrap/scripts/check_artifacts.py .allforai/bootstrap/workflow.json --json`
3. Review which nodes are done and which are pending
4. Decide the next node:
   - prefer nodes whose `hard_blocked_by` nodes are complete
   - prefer nodes whose upstream artifacts already exist
   - parallelize only when exit artifacts do not overlap
   - skip a node only when the same independent artifact gate passes on current project state
   - re-run a failed node only after addressing the cause
5. Read `.allforai/bootstrap/node-specs/<node-id>.md`
6. Dispatch execution using that node-spec as the task contract
7. After the node reports success, independently run:
   `python3 .allforai/bootstrap/scripts/check_artifacts.py .allforai/bootstrap/workflow.json --node <node_id> --json`
   Non-empty production gaps, blocking status values, or `all_exist != true` cannot be recorded as complete.
   Missing checker, nonzero exit, empty/invalid JSON, mismatched node identity or non-boolean success are failures, never implicit passes. Final bootstrap validation must also succeed before reporting the workflow complete.
8. On success: append a completed transition entry to `workflow.json`
9. On failure: append a failed transition entry, then read `.allforai/bootstrap/protocols/diagnosis.md`
10. Repeat

## Recording Transitions

After each node completes or fails, append to `workflow.json` `transition_log`:

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

1. run `check_artifacts.py .allforai/bootstrap/workflow.json --json` to inspect current state
2. trust artifact readiness over the saved transition log; a JSON report with
   blocking status, fallback/placeholder/prototype gaps, or failed validation is
   not complete merely because the file exists. `conditional_pass`, `partial`,
   `accepted_with_warnings`, `passed_with_warnings`, `blocked_by_*`, or any
   non-empty `gaps`, `code_gaps`, `test_gaps`, `asset_gaps`, `audio_gaps`,
   `remaining_gaps`, `blockers`, `major_findings`, or `unresolved_findings`
   means the workflow must continue repair/revalidation.
3. continue from the current project state

## Safety

- Same node fails 3 times: stop automatic retries, run diagnosis, and record `diagnosis_history`
- 5 iterations with no new artifacts: stop and output current best state plus TODOs
- Single node running too long: warn, do not silently discard work

## Termination

- All required exit artifacts are ready: report success
- `concept-acceptance` verdict = `needs_iteration`: output acceptance summary, stop, and ask whether to fix, re-bootstrap, or accept
- for goal-based replication workflows, do not treat an accepted current slice as final success when the acceptance artifact says major requested fidelity surfaces remain open
- User interrupts: the next run resumes from `workflow.json`

## Post-Completion

1. Run `python3 .allforai/bootstrap/scripts/summarize_run_log.py . --write-report` when that script exists
2. If `.allforai/bootstrap/product-summary.json` exists, run `python3 .allforai/bootstrap/scripts/check_product_summary.py .allforai/bootstrap/product-summary.json`
3. Read `.allforai/bootstrap/protocols/learning-protocol.md`
4. Read `.allforai/bootstrap/protocols/feedback-protocol.md`
5. Summarize reusable experience and proposed feedback

## Non-Stop Driver

If the workflow should keep moving until completion without stopping for "next step" confirmation, use:

`python .allforai/codex/flow.py`

You may pass an explicit goal override, but the normal path is to let `flow.py` reuse the goal captured during `bootstrap`.

This Codex-only outer driver repeatedly relaunches Codex against pending nodes until:

- all required exit artifacts exist
- unattended readiness is not `ready`
- the same node fails 3 times and a diagnosis record is written
- 5 consecutive transitions create no new artifacts
- or the driver's max-iteration safety limit is reached
~~~
