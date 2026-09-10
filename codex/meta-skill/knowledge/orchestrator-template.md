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
continue/halt; needs_iteration (the concept-acceptance coverage gate names
behaviour mappings without evidence) halt_with_report/auto_fix_once/accept; safety
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

- **An attempt is spent when a repair dispatch is authorized, not when it succeeds.** The
  canonical ledger is `.allforai/bootstrap/repair-authorizations.json`, and the driver
  reaches it only through `repair_authorization.py` — never by reading or writing the file
  itself, because a second implementation of the accounting rules is a second set of bugs.
  It is a separate document from `workflow.json` so a concurrent workflow writer and the
  budget ledger can never lose each other's write.

  A dispatch is two durable steps, both before the executor: `authorize` records the
  charge against every eligible obligation all-or-none, and `start` claims the single
  execution that charge pays for. `authorize` is never permission to run, and only the
  first `start` returns `execution_allowed`; a replay, a resumed driver or a second worker
  is refused. When the attempt finishes under this driver's eye it is `settle`d, which
  records an outcome and returns no budget. An attempt that was interrupted, timed out, or
  quarantined is deliberately left unresolved: whether its execution occurred is a
  question for `reconcile` and evidence that can be checked, never an assumption. The
  helper then refuses a further grant for those obligations rather than replaying
  uncertain work or refunding an attempt that may already have edited the tree.

  Every one of those verdicts is checked for the request it answers: a receipt naming a
  different authorization or a different run is not an answer about this dispatch, and
  reading it as one would attribute a charge, a claim or an outcome to the wrong attempt.
  A settlement the ledger did not confirm is the same uncertainty as a crash — the node is
  **not** completed on it, and the run stops for reconciliation, because the ledger is the
  record of what a dispatch did and accepting work whose authorization stays open would
  make that record decorative.

  **Uncertain execution stops the whole run, up front.** An authorization with no recorded
  outcome may already have edited the tree; no branch may proceed on the assumption that
  it did not, including one that never failed. The run is refused before the first
  dispatch — not when the affected repair node happens to come up — and it is reported as
  `unresolved_repair_authorizations` with the ids, plus a note that reconciliation against
  attributable evidence is what releases it. That is deliberately not the same stop as an
  ordinary QA failure: report-backed QA blocking names `exhausted_obligations` or
  `unbounded_repair_loops`, where the evidence is complete and the answer is that an
  obligation was never satisfied. One list is a verdict, the other is a question, and they
  are never merged.

  Zero is a claim about history and is verified, never assumed: `initialize` is reached
  only when there is no ledger at all, and it refuses a workflow that already shows
  execution. A missing, unreadable or ambiguous ledger blocks every node — absence of
  records is not proof of unused budget. Two consequences follow, and the Claude engine
  shares both. A repair whose executor errors, or that writes nothing, costs the
  same one attempt as one that delivered and did not fix the finding: a budget that only
  charged for success would bound neither, and the loop could repeat without end. And an
  interruption between the authorization and the work leaves the attempt spent —
  over-counting the one attempt that was cut short is recoverable, re-granting it is not,
  because the work it authorized may already be in the tree. A route that opens and is
  interrupted before any dispatch costs nothing, on either host.

  Opening the route is not the charge. The QA node's failed `transition_log` entry records
  that this QA node failed; it is the QA node's history, never the budget. The ledger is
  durable, so a restarted driver resumes the spent budget instead of handing the same
  attempts out again.

- **A shared repair charges only the obligations that still have budget.** One repair node
  may answer several QA nodes, and each carries its own declared bound. The dispatch is
  authorized for the funded obligations alone: an exhausted sibling is never charged
  again, and it is never discharged by the attempt that answers another obligation. It
  still has to be satisfied.
- A loop that declares no `max_attempts` takes the documented default of three attempts
  per QA node. A declared `max_attempts` that is not a positive integer is unbounded, not
  a request for that default: nothing is routed, and a QA node that has already failed is
  **not re-run** — re-running it would reproduce the same failure with nothing able to fix
  it and bury the planning error in a busy run. The driver blocks that QA node and reports
  it, naming the loop under `unbounded_repair_loops`; the Claude engine stops with the same
  QA failure in `needs_diagnosis`. Both validators reject the shape before the run starts;
  this is only what happens if one ever gets past them.
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
- A repair dispatch that delivered nothing is bounded the same way: it spent its attempt,
  so the loop dispatches the next one and stops at the declared `max_attempts` rather than
  retrying a non-delivery until the generic consecutive-failure threshold catches it. The
  declared budget is therefore the single bound on every repair dispatch for that QA node,
  whatever the dispatch produced. The Claude engine applies the same bound.
- When the budget is spent and the QA node still fails, the obligation is **blocked and
  reported**, not re-run. No attempt is left that could fix it, so another rerun would
  reproduce the same failure; and the run may not finish around it either — an exhausted
  obligation is refused, never accepted. A repair that has already delivered is not
  exhausted: its QA rerun judges that delivery and is not another repair attempt. The
  Claude engine reaches the same verdict and ends in `needs_diagnosis`.

  What satisfies the obligation is its own QA attempt, and only the attempt the driver
  recorded says whether that happened. A ready exit artifact does not: the exit artifact
  of a QA node is a file, and anything dispatched for another reason can write it. So an
  obligation whose latest recorded attempt failed stays blocked however passed its report
  now reads. Its loop's repair node is blocked with it — nothing is left to pay for a
  dispatch, and a repair node run as an ordinary pending node is an unpaid attempt, not a
  free one.
- **A node's blockers hold in every role it plays.** A node may repair one loop and be a
  QA obligation of another; that shape stays supported, and `validate_bootstrap` refuses
  only a repair node that is its own loop's QA or closure node. So blocked-ness is
  decided before the repair role is: a node that is routed, awaiting its own repair,
  exhausted, or under an unbounded loop is not dispatched as a repairer for anything
  else. Otherwise the dispatch one loop authorized would put that node in front of the
  executor with its own QA report among its exit artifacts, and success in one role would
  cancel another role's blocker — which it never may (ADR 0006).
- **A declared `max_attempts` outranks the generic caps.** The consecutive-failure
  threshold and the stagnation cap are backstops for nodes nobody planned a bound for.
  They rise to what the plan declared — the budget plus the failure that opened the loop,
  and two transitions per authorized attempt — so a 6-attempt loop is never ended at the
  generic 3 while reporting a supervisor threshold instead of an exhausted budget. They
  stay finite, and a loop declaring fewer attempts never lowers them.
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
  `warnings` array of strings to `.allforai/bootstrap/run-warnings.json`. The supervisor
  reads it **immediately after the executor and before the node is recorded completed**,
  never only on the next iteration: by then the node would already have completed and
  released its successors. An unreadable warnings report is not an empty one and stops the
  run the same way. Hard safety blockers remain failures.
- **A halt is run-wide, and its outputs are quarantined rather than accepted.** Codex
  cannot cancel an executor that has already finished, so the attempt's outputs exist.
  The driver calls `run_safety.py . --nodes-json <ids> --reason <reason>`, which fences
  them behind `.allforai/bootstrap/safety-quarantine.json` without deleting or accepting
  anything, records the node `failed`, and stops. While that marker — or the
  `safety-quarantine.lock` left behind by a quarantine that could not be published —
  exists, **no node is dispatchable**, including branches that never failed, and no repair
  route opens: a safety halt is not an ordinary QA failure and a repair is not its answer.
  `validate_unattended_readiness.py` refuses both paths, so the halt survives a restart and
  is released only by independent revalidation.

  Persistence of the canonical marker is reported (`quarantine_persisted`), never assumed —
  and it is not what makes the halt durable. Whatever `run_safety.py` answers, and whether
  or not it is there to answer at all, the driver leaves the lock behind before it reports:
  a halt whose only record was the warnings file a worker writes and a Run Policy a user
  can edit would be released by editing either, and the quarantined outputs would read as a
  completed node on the next start. `halt_fenced` states whether that fence is in place.
- 5 iterations with no new artifacts: stop and output current best state plus TODOs
- Single node running too long: warn, do not silently discard work

## Termination

- All required exit artifacts are ready: report success
- `concept-acceptance` names missing behaviour mappings
  (`acceptance-report.json.missing_mappings` non-empty): read `--policy-event
  on_needs_iteration`. An empty list is the gate passing — proceed, ask nothing. A report
  that still carries a `verdict`, `overall_score` or `pass_threshold`, or no
  `missing_mappings` list, is refused by name; it is a scored report, not this gate's
  output (ADR-0008). halt_with_report writes the summary and stops. auto_fix_once makes the
  list one bounded QA repair request under the existing authorization path: the gate is a
  declared QA node whose current report is a positive verdict, `flow.py` routes it to its
  declared repair node, and the dispatch is charged to the ledger before it runs (ADR-0005,
  ADR-0006) — nothing is repaired by an executor of the policy's own. A gate no
  `required_repair_loops` entry names, or whose budget is spent or unknown, halts as an
  unauthorized repair (exit 6, reason named). After the one repair delivers the gate reruns;
  a list that still names mappings halts with its report (exit 5), whatever budget the loop
  has left. accept records accepted_with_gaps without claiming verified/completed work; the
  artifact gate treats an `accepted_with_gaps` report status as blocking. Never ask during
  execution.
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
