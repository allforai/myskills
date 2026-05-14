---
name: execution-repair-loop
description: Generic repair-and-revalidation loop for QA-discovered implementation defects across app, game, backend, frontend, UI, and runtime workflows.
---

# Execution Repair Loop

## Purpose

This is the generic QA repair loop. It is domain-neutral and applies to app,
game, backend, frontend, mobile, UI, runtime, data, and asset-import execution
flows.

QA nodes must not turn repairable implementation defects into a successful
terminal state merely by writing a blocker report. A QA node may complete its
report, but any repairable `code_gaps` or equivalent implementation gaps must
flow into an execution repair loop before downstream closure can pass.

## Input Contract

Read one or more QA reports produced by upstream validation nodes. Reports must
classify findings into these buckets or equivalent names:

- `code_gaps`: implementation defects repairable in source code, configuration,
  integration wiring, data loaders, route handlers, UI state, or runtime logic.
- `test_gaps`: missing or weak tests required to prove the repair.
- `asset_gaps`: media/content defects routed to art/UI/audio/content repair.
- `contract_gaps`: missing or contradictory product/design/spec contracts.
- `environment_blockers`: unavailable runtime, simulator, service, key, tool,
  or external dependency.

Also read the target node-specs, workflow context, runtime profile, build/test
commands, and any project-local specialized skill referenced by the failed QA.

## Output Contract

Write under `.allforai/repair/` unless a domain-specific loop defines a stricter
path:

- `.allforai/repair/execution-repair-loop-report.json`
- `.allforai/repair/execution-repair-loop-report.md`
- `.allforai/repair/revalidation-report.json`

The JSON report must include:

- `repair_status`: `fixed | no_repairable_gaps | blocked_by_environment | blocked_by_contract | failed_validation`
- `attempts[]`
- `input_qa_reports[]`
- `code_gaps_fixed[]`
- `test_gaps_fixed[]`
- `changed_files[]`
- `commands_run[]`
- `qa_reports_rerun[]`
- `remaining_gaps[]`
- `rerun_required_nodes[]`

## Invocation Contract

Run this loop after QA nodes that can discover repairable implementation gaps
and before final closure/acceptance nodes. Do not ask the user during the loop.

```json
{
  "skill": "meta-orchestration/40-qa/execution-repair-loop",
  "mode": "repair_and_revalidate",
  "input_paths": [
    ".allforai/**/qa/*.json",
    ".allforai/bootstrap/workflow.json"
  ],
  "output_root": ".allforai/repair"
}
```

## Automatic Validation

1. Parse upstream QA reports.
2. If there are no `code_gaps` or `test_gaps`, write
   `repair_status: "no_repairable_gaps"` and preserve remaining non-code
   blockers for closure.
3. If `environment_blockers` prevent execution, return
   `blocked_by_environment`; do not substitute static review.
4. If `contract_gaps` prevent a correct repair, return `blocked_by_contract`.
5. Repair all feasible `code_gaps` and `test_gaps`.
6. Run relevant build/test/runtime commands.
7. Rerun the affected QA nodes or their equivalent validation commands.
8. Repeat up to 3 attempts.

## Completion Conditions

Return `COMPLETED` only when repairable implementation/test gaps are fixed and
affected QA evidence has been rerun. Return `FAILED_VALIDATION` when repairable
gaps remain after 3 attempts. Return a blocking status when the repair cannot be
validated because of environment, runtime, tool, or contract blockers.

Downstream closure nodes must read the repair loop report and must not pass when
repairable `code_gaps` remain.
