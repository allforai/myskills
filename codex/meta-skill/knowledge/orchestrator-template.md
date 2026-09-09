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
If `.allforai/bootstrap/product-summary.json` exists, treat it as provisional inference;
recorded user decision_inputs remain the product authority.

Treat `.allforai/bootstrap/*` artifacts as the canonical completion surface for workflow nodes.
Every scoped node declares `source_inputs` (project-relative product source; explicit `[]` only when
none applies) and follows `.allforai/bootstrap/protocols/input-freshness.md`. Readiness reports
`missing_source_inputs` / `invalid_source_inputs` as blockers and the artifact gate withholds
completion for such nodes; return them to `bootstrap` instead of declaring inside the run.
Retained legacy nodes without provenance are warning-only when dependency declarations
and recorded freshness state are valid. Malformed declarations or unreadable state block
even retained nodes because their dependency impact cannot be established.
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

## Run Policy — once before the first node

Run `python3 .allforai/bootstrap/scripts/product_intent.py . --run-policy`.
Reuse `run_policy_ready` with zero questions. On `needs_run_policy`, collect
the returned three choices together from the user: repeated failure
continue/halt; needs_iteration halt_with_report/auto_fix_once/accept; safety
warning continue/halt. First options are displayed defaults, never automatic
answers. Persist JSON `{operation: "run-policy", answers: {...}, user_reference}`
through that CLI. Invalid policy blocks for interactive repair. Both the markdown
loop and flow.py consume it; execution never opens another interview.
Continue/accept cannot confirm product intent. Missing product decisions return
to interactive bootstrap and block affected work regardless of Run Policy.

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
   - a failed QA node with a declared repair loop routes to that repair node first
     (see Declared cross-node repair loop below), then re-runs
5. Read `.allforai/bootstrap/node-specs/<node-id>.md`
6. Dispatch execution using that node-spec as the task contract
7. After the node reports success, independently run:
   `python3 .allforai/bootstrap/scripts/check_artifacts.py .allforai/bootstrap/workflow.json --node <node_id> --json`
   Non-empty production gaps, blocking status values, or `all_exist != true` cannot be recorded as complete.
   Missing checker, nonzero exit, empty/invalid JSON, mismatched node identity or non-boolean success are failures, never implicit passes. Final bootstrap validation must also succeed before reporting the workflow complete.
8. On success: append a completed transition entry to `workflow.json`
9. On failure: append a failed transition entry, then read `.allforai/bootstrap/protocols/diagnosis.md`
10. Repeat

## Declared cross-node repair loop

A QA node whose finding belongs to another node cannot repair itself, and a failed node
never completes, so a repair successor wired only through `hard_blocked_by` would be
unreachable exactly when it is needed. The route is the declared one:
`.allforai/bootstrap/unattended-run-readiness-spec.json.required_repair_loops` —
`{scope, qa_node_ids, repair_node_id, closure_node_ids, max_attempts}`.
`validate_unattended_readiness.py` checks that shape before the run: every QA, repair and
closure node exists, the repair node is `hard_blocked_by` each QA node, each closure node
is `hard_blocked_by` the repair node, and a declared `max_attempts` is a positive integer.
It does not check that the declared repair can actually fix the finding. `flow.py` and
this loop apply it:

- A QA node that failed **with its own current report published and readable** routes to
  its declared `repair_node_id`, for at most `max_attempts` attempts **of its own**. The
  budget is per QA node, so one repair node serving several QA nodes owes each of them a
  full budget; attempts spent on one are never charged to a sibling. A QA node that never
  ran, published nothing, or whose report cannot be read has no verdict to repair against:
  re-run it instead.
- "Current" is bound to the run being judged and to the inputs it judged, and existence
  plus parseability is proof of neither. Three things must hold together:
  - **A failed attempt on record.** This node's latest `transition_log` entry is `failed`,
    and the report was written no earlier than that entry's `started_at`. A node that never
    ran, or whose latest attempt completed, has no failure to repair.
  - **That attempt produced the report.** The driver records `qa_evidence` on every failed
    transition of a declared QA node: `produced`, the exit artifacts written while the
    attempt ran, each with its digest, and `binding`, the identity of the input snapshot
    the node was observed against. The route needs a non-empty `produced` whose digests
    still match what is on disk. An artifact counts as produced when its **content** changed
    between the two measurements the driver took around the attempt. A write time is not
    proof of execution: `touch` moves it without any report being generated, so it never
    admits anything on its own. A leftover report therefore cannot open a repair however
    recently it was touched, and a report edited after the attempt that wrote it no longer
    matches its digest.

    Only the driver writes this. It also keeps its own entry as the node's latest
    transition, dropping any the worker appended behind it: the process being judged does
    not get to file the evidence. A transition with no `qa_evidence` — an older log, or one
    written by something else — carries no proof and does not qualify.

    One case cannot be decided from outside: content that did not change while something
    did write the file. A node that re-ran and reached the same verdict looks exactly like a
    file nobody produced. The driver guesses neither way — it records `ambiguous` on the
    transition and says so in the error line, the repair route stays shut, and repeated
    failure is diagnosed. **A QA node that can repeat a verdict must say which attempt
    reached it**: put a run or attempt identifier in the report, so the same finding twice is
    two distinct verdicts and nothing has to be inferred from a timestamp.
  - **Inputs still current.** The recorded freshness state — the same one the independent
    artifact gate reads, through `check_artifacts.py --json`'s `freshness` — reports
    `readiness_status: valid` for the node. That field, not `status`, is the test: `status`
    tracks published *evidence*, which a failing QA node has none of and can never produce,
    so requiring it would refuse every repair the loop exists for. `readiness_status` is the
    contract-level answer — the node's most recent binding, contract preferred over older
    evidence, still matches its inputs, with no undecided external change. So a node that
    once delivered and published passing evidence, whose inputs have since moved, is not
    denied forever by that stale snapshot: observing its contract against the inputs as they
    are now restores the binding. Touching a file restores nothing — provenance is recorded
    at observation, not at mtime.

    `binding` names the snapshot, not the answer to a question about it. Two independent
    "the inputs are current" answers do not prove they describe the same inputs — a source
    can change and be re-observed between them, and both say yes. The driver records the
    identity at the start of the attempt and again at the end, keeps it only if it did not
    move, and admission requires the node to still be bound to that same identity. So a
    contract observation published after a report exists, or a source changed and
    republished either during or after the attempt, can never turn that report into a
    current verdict: it binds inputs, not history.

    A state that claims no provenance is not a pass here. `freshness: null` (a project with
    no freshness state), a `legacy` node's `undeclared`, a `missing` or `invalid`
    declaration, and an `uncertain` status all refuse the route. This does not change what
    completes: a legacy node still completes on the pre-freshness gate, exactly as before.
    It changes only what may be started automatically — an unattended repair is work this
    run begins on the strength of a report, so the absence of proof is not permission to
    begin it. Such a QA node is re-run, and repeated failure is diagnosed under the
    recorded Run Policy, the same route as any other unrepairable QA failure.

  - **A positive QA verdict.** The report states a failing outcome the node itself reached,
    or lists non-empty gaps or findings. An empty document, empty gap arrays, a report that
    states no outcome, or an environment, authority or never-ran status (`failed_env`,
    `blocked`, `not_ready`, `not_generated`, `existence_only`, `blocked_by_*`) carries
    nothing for a repair node to act on — the same exclusion the engine applies through
    `NON_QA_FAILURE_TYPES`.

  Anything short of all four is re-run or diagnosed, never repaired against.

- Attempts are counted from `transition_log`, which is durable: a restarted driver
  resumes the spent budget instead of handing the same attempts out again. An attempt is
  a repair dispatch that completed while that QA node was waiting on it.
- A loop that declares no `max_attempts` takes the documented default of three attempts
  per QA node. A declared `max_attempts` that is not a positive integer is unbounded, not
  a request for that default: the loop routes nothing and the QA node is re-run instead.
- Only the declared repair node may proceed on that failed QA node. No other successor
  advances on a failed dependency, a failed node is never recorded `completed`, and its
  report is never edited to look passed.
- When the repair node **delivers**, the QA node **re-runs**. Delivery, not completion, is
  the signal, and the difference is structural rather than a shortcut: a declared repair
  node is `hard_blocked_by` the QA node it repairs, so while that QA node is failing the
  repair node's own evidence is stale by definition and the freshness gate refuses it.
  Waiting for the repair node to complete first would invert the loop and hang it. A repair
  attempt has delivered when it wrote the repair node's declared exit artifacts, which the
  driver records the same way it records a QA attempt's.

  Nothing is waived by that. The repair transition stays `failed`, the node stays
  incomplete, the attempt still spends a budgeted attempt, and the QA rerun — never this
  record — decides whether the repair worked. Once the rerun passes, the repair node is
  dispatched again as an ordinary node, publishes its evidence with its upstream now valid,
  and completes on its own merits; only then does closure become reachable. Every
  `closure_node_ids` entry stays blocked until the QA node itself completes; a delivered
  repair is not a passing QA.
- When the budget is spent and the QA node still fails, it is a normal repeated failure:
  diagnose and stop under the recorded Run Policy. Never waive it.
- When no node is dispatchable but pending nodes remain, the graph is blocked. Report the
  blocked nodes; that state is never a completed workflow.

#### Recovering a legacy node's repair route

A legacy QA node that genuinely needs its declared repair loop is one declaration and one
observation away from it:

1. Add `source_inputs` to the node in `workflow.json` — the product sources it judges, or
   an explicit `[]` when none applies — and `input_dependencies` for the files it reads.
2. Observe and publish the node once through the generated helper:

   ```bash
   echo '{"operation":"observe","node_id":"<qa-node>","kind":"contract"}' \
     | python3 .allforai/bootstrap/scripts/evidence_freshness.py .
   echo '{"operation":"publish","observation":"<token>","verification_command":[...]}' \
     | python3 .allforai/bootstrap/scripts/evidence_freshness.py .
   ```

3. Let the QA node **run again**. The binding applies to attempts that start after it, so
   the route opens on the next attempt's own report — never on the one that was already on
   disk when you observed. If an input moves afterwards, the route closes again until the
   node is reobserved.

Declare the inputs at planning time rather than mid-run wherever the node still exists in
the plan; step 1 inside `/run` is a migration for retained history, not a way to open a
route for work that never declared what it judges.

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
   `accepted_with_gaps`, `accepted_with_warnings`, `passed_with_warnings`, `blocked_by_*`, or any
   non-empty `gaps`, `code_gaps`, `test_gaps`, `asset_gaps`, `audio_gaps`,
   `remaining_gaps`, `blockers`, `major_findings`, or `unresolved_findings`
   means the workflow must continue repair/revalidation.
3. continue from the current project state

## Safety

- Same node fails 3 times: diagnose and record `diagnosis_history`; consume
  `product_intent.py . --policy-event on_repeated_failure`. Continue retries only
  for recorded `continue`; out-of-scope, convergence and stagnation caps still halt.
- For non-blocking safety warnings, consume `--policy-event on_safety_warning`:
  continue logs, halt stops with a report. In native flow.py, nodes publish a
  `warnings` array of strings to `.allforai/bootstrap/run-warnings.json`; the
  supervisor consumes it before the next wave. Hard safety blockers remain failures.
- 5 iterations with no new artifacts: stop and output current best state plus TODOs
- Single node running too long: warn, do not silently discard work

## Termination

- All required exit artifacts are ready: report success
- `concept-acceptance` verdict = `needs_iteration`: consume `--policy-event on_needs_iteration`.
  halt_with_report writes the summary and stops; auto_fix_once durably consumes
  one repair, reruns acceptance, then stops; accept records accepted_with_gaps
  without claiming verified/completed work; the artifact gate treats an
  `accepted_with_gaps` report status as blocking. Never ask during execution.
- A node withheld by freshness carries `freshness.diff` and `freshness.repair`:
  repair at the named `owner` (the node, a stale producer, or `interactive-bootstrap`
  for a pending or unreplanned product decision), re-observe and republish. A
  missing, drifted or outdated required document is that node's documentation
  inconsistency: publication executes each document's declared `document_verification`
  against the current source, so a code-only acceptance cannot complete a delivery
  whose facts are stale, and rewriting a document without correcting its facts fails
  the same check. A product-decision owner returns to `bootstrap`, never to an in-run answer.
- An `unresolved_external_change`, `unverified_external_change`,
  `external_change_repair_pending` or `undetermined_external_change` readiness blocker
  is source changed outside the delivery flow. All four are preflight blockers: report
  and refuse the affected work. An `unverified_external_change` means no verification
  stands for the current source; the gates deliberately do not run the project's
  acceptance to find out, so it is settled at the interactive `bootstrap` entry, never
  by executing anything inside the run. An `undetermined_external_change` is
  project-wide rather than node-scoped: the comparison itself could not be completed,
  so no delivery can be shown to be free of a waiting product conflict. Repair the
  unreadable state at the interactive `bootstrap` entry; never read an undeterminable
  comparison as a clear one. Never interview during execution, never read
  the changed code as the approved requirement, and never let a Run Policy `accept`
  stand in for that decision. The user resolves it at the interactive `bootstrap`
  entry; a rejected change leaves scoped implementation repair whose confirmed
  acceptance must republish before the node completes.
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
- recorded failure policy or an existing convergence/stagnation cap stops retries
- 5 consecutive transitions create no new artifacts
- or the driver's max-iteration safety limit is reached
~~~
