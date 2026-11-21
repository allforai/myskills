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

## Active Supervision and Failure Notifications

Starting a process or dispatching a worker does not complete `/run`. Keep the
calling agent active until the independent final gate passes or a recorded policy
or concrete blocker requires stopping. Do not end the turn with a launch receipt.
Poll running work at intervals of at most 60 seconds and give the user a concise
progress update at least once per minute while work continues. Report a detected
failure promptly: the affected node, observed error, whether repair is underway,
and the next check. Logs alone are not a user notification.

A process heartbeat proves liveness only, not progress or successful verification.
If a worker exits, a tool session disappears, or a timeout fires, inspect its exit
status and persisted result immediately. Preserve failure history and follow the
recorded retry/diagnosis policy; do not wait indefinitely for an exited worker or
restart it blindly. If stopping is required, report the exact blocker and remaining
work in the final reply. Do not imply background execution will continue after the
turn ends unless a persistent supervised runner actually exists.

## Preflight Gate

<!-- clause-begin:run-preflight-readiness -->
Before executing any workflow node, run unattended readiness:

<!-- snippet:preflight-readiness -->
```bash
python3 .allforai/bootstrap/scripts/record_run_event.py . --event run_started --status started --message "run command invoked"
python3 .allforai/bootstrap/scripts/validate_unattended_readiness.py . --write-report
```

If it exits non-zero or `.allforai/bootstrap/unattended-run-readiness.json`
has `status != "ready"`, stop immediately. Do not start partial execution, do
not ask the user mid-run, and do not silently weaken validation. Report the
blockers from `.allforai/bootstrap/unattended-run-readiness.md` and ask the user
to resolve them through `/setup check`, `/bootstrap`, or the approval dashboard
before re-running `/run`.
<!-- clause-end:run-preflight-readiness -->

<!-- clause-begin:run-repair-ledger-origin -->
Then record the repair-ledger origin, still before the first node — this is the
only moment `initialize` can prove zero spend, because it refuses a workflow that
already shows execution:

<!-- snippet:repair-ledger-initialize -->
```bash
printf '{"operation":"initialize","run_id":"%s"}' "$(cat .allforai/bootstrap/run-id)" \
  | python3 .allforai/bootstrap/scripts/repair_authorization.py .
```

A `replayed: true` answer on a resumed run is the same statement, not a reset. If the
step was skipped and the workflow already ran nodes but never dispatched a declared
repair node, recover with `adopt_history` and evidence
`{"source_path": ".allforai/bootstrap/workflow.json", "source_digest": "<sha256>",
"absence_of": "repair_history", "complete": true}`; the helper verifies the absence
against the transition log. If declared repair nodes did run, the same `adopt_history`
takes `{"reconstruct_from": "transition_log", "complete": true}` and rebuilds one settled
attempt per repair transition, bounded by the declared loops. Any other history stays
blocked until reconstructed.
<!-- clause-end:run-repair-ledger-origin -->
Before stopping, record `preflight_blocked` with
`record_run_event.py`, then run `summarize_run_log.py --write-report`.

## Model tiers (the one question before the first node)

<!-- clause-begin:run-model-tiers -->
Every step runs on a tier, never on a model a skill names: `strong` for work that decides
or judges, `standard` for building to a settled spec, `light` for running a command and
reporting what it printed or writing a record. A node runs on the `model_tier` bootstrap
declared for it, `strong` when it declares none; the node gate, reviews, diagnosis and
repair are `strong` whatever the node declares (ADR-0021).

Before the first node, read `.allforai/bootstrap/model-tiers.json`. When it has no entry for
this host (`claude`, `codex` or `pi`), list the models this host can run now, recommend one
for each tier, and ask the user once to accept or change them. Write the answer under this
host's key as `{"strong": "<name>", "standard": "<name>", "light": "<name>"}`; a tier left
out runs on the session model. When nobody can answer, write the recommendation and list
it at completion as a choice the run made for the user. An entry that exists is used as it
is and is not asked again: the user edits the file to change it, or deletes this host's
entry to be asked at the next run. Never write a model name into a skill or a template.
<!-- clause-end:run-model-tiers -->

This is the only question a run asks (ADR-0021 narrows ADR-0018); everything below is
recorded, never asked.

## Run Policy (recorded, never asked)

Apart from the model tiers above, `/run` asks nothing — not before the first node and not after it. The user answers
questions at `/bootstrap`; a run goes from its first line to its report unattended
(ADR-0018). The three choices a run needs are read from
`.allforai/bootstrap/run-policy.json`: run
`python3 .allforai/bootstrap/scripts/product_intent.py . --run-policy` before the
first node. With no usable policy on record the script records the defaults itself and
marks them `chosen_by: default`, so completion can say they were nobody's choice; it
never returns a question.

| key | when it is read | options (first = default) |
|---|---|---|
| `on_repeated_failure` | The same node fails 3 times, the diagnosis is neither out-of-scope nor converged. | `continue` (keep diagnosing until the caps below stop it) / `halt` (stop and report on the third failure) |
| `on_needs_iteration` | The concept-acceptance coverage gate names behaviour mappings without evidence (`missing_mappings` non-empty; an empty list proceeds). | `halt_with_report` (write acceptance-report.md, stop; the fix / re-bootstrap / accept choice is made by the human afterwards) / `auto_fix_once` (the missing list becomes one bounded QA repair request through the gate's declared repair loop and the ledger; the gate reruns, then the run stops either way) / `accept` (record `accepted_with_gaps` in assumed-decisions.json and finish the run) |
| `on_safety_warning` | A non-blocking safety warning fires (see safety.md). | `continue` (log the warning and go on) / `halt` (stop at the first warning) |

A user who wants another choice says so outside a run — in the `/run` goal text or at
`/bootstrap` — and it is submitted as JSON operation `run-policy` with `answers` and the
actual `user_reference`; what it replaces is kept in `run-policy-repairs.json`. Every
later branch reads `run-policy.json`, and a branch that would need a fourth answer
halts with a report instead.
The Workflow engine checks this policy before loading the DAG and reads
`product_intent.py . --policy-event on_needs_iteration` when the gate fires; that
read charges nothing. The one repair `auto_fix_once` grants is an attempt the
repair-authorization ledger charges against the gate's declared loop, so no second
accounting of it exists. Run Policy is never a product decision: `continue` and
`accept` confirm no requirement.

### Dynamic preflight reconciliation

Before every execution wave, run every idempotent expander declared by
`workflow.json.expanders`, including `expand_game_2d_production.py`. An expander may add or
repair nodes after an upstream node creates a trigger artifact. Re-read the changed DAG and
rerun `validate_unattended_readiness.py`; do not execute newly exposed work when readiness
is not `ready`.

### Generic QA repair loop

<!-- clause-begin:run-freshness-publish -->
Every node follows `.allforai/bootstrap/protocols/input-freshness.md`: after its
implementation settles, observe current inputs, track newly consumed files with
the public `read` operation, refresh required documents and publish evidence with
its actual acceptance command. A stale publication requires re-observation and
reverification, never a success transition. Contract-only freshness permits work
but does not prove completion. The independent artifact gate consumes this state.
<!-- clause-end:run-freshness-publish -->
A withheld completion carries `freshness.diff` and `freshness.repair`: repair at
the named `owner` (the node, a stale producer, or `interactive-bootstrap` for a
pending or unreplanned product decision), then re-observe and republish. A
missing, drifted or outdated required document is a documentation inconsistency
of that node: publication executes each document's declared
`document_verification` against the current source, so a code-only acceptance
cannot complete a delivery whose facts are stale; rewriting a document without
correcting its facts fails the same check. A product-decision owner is a
preflight blocker for the next `/run`, never something to answer or invent
inside the run.
An `unresolved_external_change`, `unverified_external_change`,
`external_change_repair_pending` or `undetermined_external_change` readiness blocker
is source changed outside the delivery flow. All four are preflight blockers for the
next `/run`: report and refuse the affected work. An `unverified_external_change`
means no verification stands for the current source; the gates deliberately do not
run the project's acceptance to find out, so it is settled at the interactive
bootstrap entry, never by executing anything inside the run. An
`undetermined_external_change` is project-wide rather than node-scoped: the
comparison itself could not be completed, so no delivery can be shown to be free of a
waiting product conflict. Repair the unreadable state at the interactive bootstrap
entry; never read an undeterminable comparison as a clear one. Never interview the user
inside the run, never treat the changed code as the approved requirement, and never
let a Run Policy `accept` stand in for that decision. The user resolves it at the
interactive bootstrap entry; a rejected change leaves scoped implementation repair
whose confirmed acceptance must republish before the node completes.
A node whose freshness is `undeclared` (missing `source_inputs`) or `invalid`
(malformed declaration) cannot start or be committed: return it to interactive
bootstrap to declare its product source (explicit `[]` only when none applies).
Never add a declaration inside `/run` to pass the gate. Retained legacy nodes
report `undeclared` as a warning only when dependency declarations and recorded
freshness state are readable and valid; no provenance is claimed for them.
Malformed declarations or unreadable freshness state block even retained nodes:
dependency impact is unknown, so legacy compatibility cannot waive that failure.

### Declared cross-node repair loop

The in-node loop above repairs what a node owns. A QA node whose finding belongs to
another node cannot repair itself, and it never completes, so a repair successor wired
only through `hard_blocked_by` would be unreachable. The route is the declared one:
`unattended-run-readiness-spec.json.required_repair_loops` — `{scope, qa_node_ids,
repair_node_id, closure_node_ids, max_attempts}`. `validate_unattended_readiness.py`
checks that shape before the run: every QA, repair and closure node exists, the repair
node is `hard_blocked_by` each QA node, each closure node is `hard_blocked_by` the repair
node, and a declared `max_attempts` is a positive integer. It does not check that the
declared repair can actually fix the finding. The engine loads it as `repair_loops[]`
and applies it:

- A QA node that failed **with its own current report published** satisfies the declared
  `repair_node_id`'s dependency on it — for that repair node only, for at most
  `max_attempts` attempts **of its own**. The budget is per QA node, so one repair node
  serving several QA nodes owes each of them a full budget; attempts spent on one are
  never charged to a sibling. A QA node that never ran, published nothing, or failed on an
  environment, authority, readiness or gate error has no verdict to repair against: it is
  a diagnosis case, never a repair route.
- **An attempt is spent when a repair dispatch is authorized, not when it succeeds.** The
  canonical ledger is `.allforai/bootstrap/repair-authorizations.json`, its own document,
  and both hosts reach it only through `repair_authorization.py`. The engine has no
  filesystem: every ledger operation is a prompt that runs that CLI and returns its verdict
  verbatim, which is then checked against what was asked. A verdict that names another
  dispatch, another repair node, or an answer nobody asked for is a forged receipt and
  nothing executes on it — otherwise "the ledger said so" would mean only "the agent said
  so".

  A dispatch is two durable steps, both before the executor. `authorize` charges every
  eligible obligation atomically and is **never** permission to run; `start` claims the one
  execution that charge paid for, and only the first claim is granted. Two consequences
  follow, and the Codex driver shares both. A repair whose executor errors, or that writes
  nothing, costs the same one attempt as one that delivered and did not fix the finding: a
  budget that only charged for success would bound neither, and the loop could repeat
  without end. And an interruption between the charge and the work leaves the attempt
  spent — re-granting it would hand out an attempt whose work may already be in the tree.
  A route that opens and is interrupted before any dispatch costs nothing, on either host.

  Opening the route is not the charge. The QA node's failed `transition_log` entry records
  that this QA node failed and was routed; it is the QA node's history, never the budget.
- **Only an execution the engine watched end is settled.** Settling records an outcome and
  returns no budget. An attempt whose stage threw, whose host died, or whose wave was
  quarantined by a safety halt is deliberately left unresolved: whether it ran is then a
  question for `reconcile` and evidence that can be checked, not something to guess. The
  two guesses fail in opposite unsafe directions — assume it ran and a needed repair is
  skipped; assume it did not and duplicate side effects replay on a budget already spent.
- **Consumption first; initialize only a ledger that does not exist.** The spent budget is
  read from the ledger before any node runs, never summarized out of `workflow.json` by the
  agent that loads the DAG — a count inferred by reading a file is not accounting. A ledger
  that is unreadable, belongs to another run, or carries an ambiguous history is untrusted
  state and stops the run. Only `missing_ledger` may be initialized, and the helper itself
  reads `workflow.json` and refuses to record zero for a run that already shows execution.
  Because that origin is proved, an obligation the ledger does not list really has spent
  nothing — absence is trustworthy here only because the document is.
- **An unresolved grant at startup blocks.** A charge that never reached an outcome leaves
  it unknown whether that attempt ran, so a resumed run stops for reconciliation rather
  than replaying uncertain work or refunding an attempt that may already have been spent.
- A loop that declares no `max_attempts` takes the documented default of three attempts
  per QA node. A declared `max_attempts` that is not a positive integer is unbounded, not
  a request for that default: nothing is routed, and a QA node that has already failed is
  **not re-run** — re-running it would reproduce the same failure with nothing able to fix
  it and bury the planning error in a busy run. The engine stops with that QA failure in
  `needs_diagnosis`; the Codex driver blocks the node and reports it with
  `unbounded_repair_loops`. Both validators reject the shape before the run starts; this is
  only what happens if one ever gets past them.
- No other successor may proceed on a failed dependency. A failed node is never
  `completed`, and its report is never edited to make it look passed.
- A repair opened for one node never absorbs another node's verdict in the same wave. An
  `accepted_with_gaps` result or a stopped one-shot iteration repair still ends the run
  under the recorded Run Policy, and neither node is re-run into a passing verdict.
- When the repair node **delivers**, the QA node **reruns**. Delivery, not completion, is
  the signal, and the difference is structural. A declared repair node is
  `hard_blocked_by` the QA node it repairs, and `check_artifacts.py` folds the recorded
  freshness state into `all_exist`, so while that QA node is failing the repair node's own
  evidence is stale and its independent gate withholds it by construction. Retrying inside
  the node would burn the artifact repair budget against something no repair can fix, and
  the run would end `needs_diagnosis` with `exhausted_repair_loop` on the repair node.
  So for the declared repair node of an open loop, a **withheld** gate is a delivery: the
  engine records it and moves on. An environment, authority or cross-node blocker is still
  `hard_fail` — never a delivery, never an advance — and it stops the run once the loop's
  declared budget is spent, bounded like any other dispatch that produced nothing. The
  exception is a `NON_QA_FAILURE_TYPES` verdict (`invalid_artifact_gate`,
  `invalid_readiness_gate`, `deadlock`, `safety_warning`, `needs_iteration`,
  `exhausted_retries`): structural, environmental or policy answers are not attempts that
  fell short, so they stop the run immediately, on the same reasoning that keeps them from
  opening a repair route in the first place.

  A delivery is **measured, never asserted**. The engine holds no filesystem, so its only
  independent measurement is the gate step running `check_artifacts.py --json` and
  reporting what it printed; the node's own result is never the evidence. The same step
  runs once before the node and once after, and a delivery requires all of: every declared
  exit artifact present with no status error, the gate withheld only by this loop's own QA
  node, and at least one artifact whose content digest moved. Anything less — an absent
  measurement, a missing field, a touched or pre-existing artifact, a blocked report, a gate
  withheld by anything else — is `unmeasured_repair_delivery`, a hard failure, never a quiet
  advance.

  The repair node's own readiness and input binding are deliberately **not** part of that
  bar (ADR-0009). A repair edits the very source its QA node checks, so both move by doing
  the work; requiring them to stand still made every real repair unmeasurable and spent the
  loop's budget on a rule no repair could satisfy. A delivery therefore claims only that
  this attempt wrote its declared artifacts and that nothing but its own QA node withholds
  it. Whether the repair was *right* is not measured here and never was: the QA rerun that
  follows is the proof, and the declared budget bounds the attempts either way.

  Nothing is waived. A delivery never commits, so the repair node stays out of `done`; it
  is dispatched again once the QA node passes, and must pass this same independent gate on
  its own merits before anything commits it. Every `closure_node_ids` entry stays blocked
  until the QA node itself completes — a delivered repair is not a passing QA, and the
  rerun is the only way past the loop. The Codex driver applies the same lifecycle.
- A dispatch of the repair node that itself hard-fails inside its still-open loop — an
  `unmeasured_repair_delivery`, say — is not a terminal verdict while that loop has budget
  left. Its attempt is already charged, so the next one is dispatched; when the budget is
  gone the failure stops the run with its own findings. The declared `max_attempts` is
  therefore the single bound on every repair dispatch for that QA node, whatever the
  dispatch produced. The Codex driver applies the same bound.
- When the budget is spent and the QA node still fails, that is a hard failure with the
  original findings; report it, never waive it.

After a node reports success, independently run `check_artifacts.py --node <node_id> --json`.
Non-empty `code_gaps` or `test_gaps`, partial/conditional status, placeholders, failed
validation, or other blocking findings cannot be committed as complete. Invoke the
`execution-repair-loop`, repair within its three-attempt budget, and **Rerun affected QA evidence**
through the original node plus the independent artifact gate. Exhaustion is a hard failure;
never waive, downgrade, or hide a gap.

## Phase B execution (CC: Workflow engine)

`/run` is fully autonomous once the model tiers are settled — no further questions, no human stops. Drive it as:

1. Invoke the Workflow engine script at
   `.allforai/bootstrap/run-engine/run-engine.workflow.js`, passing the `claude` entry of
   `.allforai/bootstrap/model-tiers.json` (§ Model tiers) unchanged as `args.models`.
   It reads `workflow.json` plus `unattended-run-readiness-spec.json.required_repair_loops`,
   schedules ready nodes (alignment_refs run in parallel),
   self-heals soft failures, commits each node immediately, and returns one of:
   - `{ status: "complete" }`
   - `{ status: "needs_diagnosis", hardFailures: [...] }`
   - `{ status: "needs_product_decision", decisions: [...] }`

2. On `complete`: first send reported defects back (§ Reported defects go back to their owner);
   if any was routed, RESUME the engine and return to this step when it next reports. Otherwise
   run the learning-protocol extraction, then produce the Phase C report:
   a. **Evidence-anchored completeness (verification honesty).** Run
      `python3 .allforai/bootstrap/scripts/compute_completeness.py <base>` — it derives each
      node's TRUE state from its recorded `verification` evidence and writes
      `.allforai/bootstrap/completeness-report.json`. **Report the two-column result as the
      headline: VERIFIED (真验过) % vs unverified (只生成没验) %.** Never present "completed
      node count" as completeness — a node without real evidence is `unverified`, never counted.
      An entry served through a mock layer or answering with a canned fixture is refused in
      cross-exam's words (`refused[]` in the report) and read as `unverified`; whether a green
      feature is hollow beyond that is `/cross-exam`'s to judge, after the pipeline (ADR-0008).
   b. Run `python3 .allforai/bootstrap/scripts/check_evidence.py <base>` to list any
      false "verified" claims (evidence missing / self-graded) — these are downgraded.
   c. **Launch gate:** if `completeness-report.json.critical_unverified` is non-empty, the product
      is NOT launch-ready regardless of node count — surface those critical flows as needing real
      verification. Do not call the product complete on self-attestation.
   d. Read `.allforai/bootstrap/assumed-decisions.json` + any UNRESOLVED, then stop.

3. On `needs_diagnosis`:
   a. Read `hardFailures` (always non-empty — a stuck graph carries a synthesized `deadlock`
      finding) + `workflow.json` `diagnosis_history`.
   b. GLOBAL cap (fix L1): run `python3 .allforai/bootstrap/scripts/record_run_event.py . --diagnosis-budget`.
      It counts the diagnoses recorded in `diagnosis_history` since this invocation's
      `run_started` — entries that name a `root_cause`. The engine's own `kind: "failure"`
      records of the same failures do not count. If it prints `"capped": true` (5 or more),
      mark UNRESOLVED and stop — this catches oscillating root causes the per-cause cap
      misses. Entries of earlier invocations are history and never count.
   c. Run `.allforai/bootstrap/protocols/diagnosis.md`: locate the root-cause node
      (use `suspected_root_node` when present). This is autonomous — never ask the user.
   d. Per-cause cap (the policy unit-tested as engine-core `convergenceCheck`): if the same root
      cause already appears ≥2 times among this invocation's entries (`this_invocation` in the
      output above), mark it UNRESOLVED, write best-effort output + TODO, and stop.
   e. Otherwise apply the repair plan WITH CASCADE (fix C2). Append the diagnosis to
      `diagnosis_history` with its `root_cause` (the shape in `diagnosis.md`), then write each repair-plan step's action (and any prevention
      hint for that node) to `.allforai/bootstrap/diagnosis-corrections/<node_id>.json` as
      `{node_id, diagnosis, corrections: [...]}`. Do not edit node-specs during `/run`: a
      changed node-spec stales A0's decision coverage, and the next readiness check stops
      for a new rehearsal. The engine tells each dispatched node to read its corrections
      file and deletes it when the node completes. Then reset with the official operation:
      `python3 .allforai/bootstrap/scripts/compute_reset_closure.py .allforai/bootstrap/workflow.json --apply --diagnosis <timestamp> <root_id...>`
      — it marks the closure's (root + transitive downstream) completed transitions
      `superseded`, keeping them for audit. Never edit `transition_log` by hand. Then RESUME
      the engine (same session: resumeFromRunId; cross-session: re-invoke — workflow.json
      idempotency skips already-completed nodes).

3a. What a stop asks of the user:
   <!-- clause-begin:run-invocation-allowance -->
   A repair budget and a diagnosis cap bound one invocation of the run, not the life of
   the plan. A declared `max_attempts` counts repair attempts in a row that left the QA
   node with no fewer blocking findings: each failed QA verdict of a declared loop is
   recorded through `repair_authorization.py` as
   `{"operation":"verdict","repair_node_id":…,"qa_node_id":…,"blocking_count":…}` before
   it is routed, and a count lower than every earlier one of this invocation starts the
   count of attempts again. No invocation grants one obligation more than ten attempts
   (or its `max_attempts`, when that is higher). Attempts and diagnoses recorded before
   this invocation's `run_started` are history: the ledger leaves them out by itself.
   So a loop that stopped, or a cap that was reached, is reported with its open findings
   and the words "run again to continue" — it is never a reason to send the user to
   interactive bootstrap. Only three things go back there: a product decision nobody has
   answered, a plan change nobody has confirmed, and a defect in the plan itself (a
   deadlock, an undeclared loop, a node-spec that has to change).
   <!-- clause-end:run-invocation-allowance -->
   The engine records each verdict itself. In the halt report, list the stops that only
   need another `/run` separately from the ones that need `/bootstrap`.

   A node that declares `inline_review` is reviewed by the engine as soon as it passes:
   an independent reviewer writes its blocking findings to
   `.allforai/bootstrap/inline-review/<node_id>.json`, the node revises its own output
   from that file, and reviews continue while each finds fewer findings than the best so
   far. A review that stops converging lets the node through with the file as the record
   of what is still open — the QA node downstream judges it; it is not a failure to
   diagnose. In the final report, name every node whose review ended `open`.

3b. A product decision nobody settled:
   <!-- clause-begin:run-product-decision-gap -->
   `/run` never stops for a product decision (ADR-0018). A node that owns a user-visible
   rule the frozen intent does not settle weighs at least two options, builds with the one
   it recommends and records the choice in
   `.allforai/bootstrap/run-decisions/<node_id>.json`. It then passes or fails on its work
   like any other node, completion lists the choice, and the user overturns it at
   interactive `/bootstrap`, which asks it in Phase A. A node never takes a choice that
   contradicts a recorded decision. A workflow bootstrapped before this may still park a
   node with `.allforai/bootstrap/product-decision-gaps/<node_id>.json` and end
   `needs_product_decision`: record `run_halted` with that status, list every decision —
   node, question, options, recommendation — and say that rerunning `/bootstrap` answers
   them and brings the workflow to the unattended rule. Never ask here.
   <!-- clause-end:run-product-decision-gap -->

4. Repeat until `complete`, `needs_product_decision` or an UNRESOLVED stop.

This template is CC-only. Codex keeps its existing markdown loop (frozen).

## Recording Transitions

After each node completes or fails, append to workflow.json transition_log:

```json
{
  "node_id": "<node_id>",
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
2. Trust the gate over transition_log: a completion read from the log is a claim. The engine
   re-measures every inherited completion that a remaining node depends on (`inherit:<node_id>`,
   the same independent gate that follows a node's own run) and reruns one that no longer passes —
   a deleted file, a failed validation command and a stale input all count.
3. Continue from where things stand

The engine also starts by undoing a wave an earlier session never saw end (`recover-waves`):
the reads those nodes registered and the evidence they published return to what they were,
so an interrupted run needs no cleanup by hand.

## Safety (warnings, not blockers)

- Same node fails 3 times → **before warning**, check `workflow.json.diagnosis_history` for that node:
  - If any entry has `"out_of_scope": true` → mark workflow halted, output TODO list, do NOT retry or ask user
  - If 2+ entries share the same `root_cause.node` → convergence cap reached, mark UNRESOLVED, output TODO list, halt
  - Otherwise → apply `run-policy.json.on_repeated_failure`: `continue` keeps the diagnosis
    loop going (the global and per-cause caps still stop it); `halt` marks UNRESOLVED, outputs
    the TODO list, and stops. Never ask here.
- 5 iterations with no new artifacts → output current state + TODO list
- Single node running > 10 minutes → warn but don't kill

## Reported defects go back to their owner

A node that notices a defect in a file another node owns does not fail over it and does not
edit the file: it finishes and reports the warning `defect in <producing node>: <file> — <what
is wrong>` in `safety_warnings`, which the engine
appends to `.allforai/bootstrap/run-warnings.json`. When no node is left to run, and before the success report, run
`python3 .allforai/bootstrap/scripts/compute_reset_closure.py .allforai/bootstrap/workflow.json --route-defects`.
For each such warning not routed before, it writes the defect into
`diagnosis-corrections/<owner>.json`, resets the nodes the change reaches, and records the
routing in `routed-defects.json`. Those nodes are the owner, every node that recorded reading
the named file, and what depends on those; a node that only waits for the owner keeps its
completion. Where the reach cannot be told — the warning names no file, or no freshness record
exists — everything downstream of the owner is reset. If `routed` is not empty, RESUME the engine: the owner fixes
its own file under the correction, and the nodes that read it are judged again. If `routed` is empty
the run is finished. Run it once per completion, never per node: a file is changed, and its
consumers rerun, once for every defect reported so far. A defect is routed once and an owner
is sent back at most twice; what the command returns under `kept` stays a warning and is
listed in the final report with its reason. This is not a diagnosis and spends none of its
budget.

## Termination

  <!-- clause-begin:run-termination-user-steps -->
- All nodes' exit_artifacts are ready → success report. The report ends with
  `workflow.json.user_steps` in order (`/cross-exam`, then `/product-review`) as the steps
  the user types next; they are never dispatched, never started by a node, and never
  reported as done (ADR-0008). A list without `/product-review` means bootstrap suppressed it
  (CLI, library-sdk: no UI to critique); `/cross-exam` is never dropped.
  <!-- clause-end:run-termination-user-steps -->
- concept-acceptance names missing behaviour mappings (`acceptance-report.json.missing_mappings`
  non-empty; the node result carries the list verbatim) → apply
  `run-policy.json.on_needs_iteration`. An empty list is the gate passing: proceed, ask nothing.
  A report that still carries a `verdict`, `overall_score` or `pass_threshold`, or no
  `missing_mappings` list at all, is refused by name as `invalid_artifact_gate` — it is a
  scored report, not this gate's output (ADR-0008).
  `halt_with_report` writes acceptance-report.md (with the fix / re-bootstrap / accept options
  listed for the human to pick afterwards) and stops. `auto_fix_once` makes the missing list
  a QA failure like any other: it is routed to the gate's declared `required_repair_loops`
  entry and the repair node is dispatched under a ledger grant (authorize, start, settle —
  ADR-0005, ADR-0006), never repaired in-node. A gate no loop declares a repair for, or
  whose budget the ledger shows spent or unknown, halts as an unauthorized repair with
  `needs_diagnosis`. The recorded policy grants that route once: after the repair delivers
  the gate reruns, an empty list commits it and stops the run as `iteration_repair_stopped`,
  a list that still names mappings stops it as `needs_iteration` — whatever budget the loop
  has left. `accept` records `accepted_with_gaps` in assumed-decisions.json and returns a
  qualified outcome, without marking that node completed or verified; the artifact gate
  treats an `accepted_with_gaps` report status as blocking. Never ask here.
- User interrupts → transition_log is already saved, resume with /run
- Safety warning → apply `run-policy.json.on_safety_warning`: `continue` logs it and goes on,
  `halt` stops with the warning in the report. Never ask here.

## Post-Completion

**Run regardless of success or early stop:**

0. **Run log summary:**
   Run `python3 .allforai/bootstrap/scripts/summarize_run_log.py . --write-report`.
   Keep `.allforai/bootstrap/run-log.jsonl`, `.allforai/bootstrap/run-summary.json`,
   and `.allforai/bootstrap/run-summary.md` as the auditable production trace.

0b. **Disclose delegated decisions:**
   <!-- clause-begin:run-delegations-disclosure -->
   Run `python3 .allforai/bootstrap/scripts/product_intent.py . --delegations`.
   The completion text prints what it returns, each list under its own heading:
   - `Decisions you delegated to the model` — every `delegations` entry: its id, the
     proposal title, the user turn that handed the decision over, and the reason. If the
     list is empty, print `No delegated decisions.`
   - `Decisions this run took on its own recommendation` — every `run_decisions` entry:
     the node, the question, the options it weighed, the one it took and why. If the list
     is empty, print `No decisions taken by the run.`
   - `Run Policy left at its defaults` — every `run_policy_defaults` key with its value;
     leave the heading out when the object is empty.
   <!-- clause-end:run-delegations-disclosure -->
   The user must be able to see every decision that was made for them without opening a
   file. Do not ask the user anything here.

1. **Mark concept drift resolved (if applicable):**
   If `.allforai/product-concept/concept-drift.json` exists AND `resolved = false`
   AND all nodes completed successfully: set `"resolved": true` and write back.
   If /run stopped early or failed: leave `resolved = false` (drift still pending for next /bootstrap).

2. **Learning extraction:**
   Read `.allforai/bootstrap/protocols/learning-protocol.md`.
   Check `workflow.json.corrections_applied[]` and `diagnosis_history[]`:
   - If both empty: no learning to extract, skip.
   - For each entry in `corrections_applied[]`:
     * Extract: node, what_was_wrong (root_cause), fix_applied
     * Classify per learning-protocol.md type (mapping-gap / discovery-blind-spot / convergence / safety / other)
     * Write to `.allforai/bootstrap/learned/<category>.md` per learning-protocol.md File Naming Convention
   - For each entry in `diagnosis_history[]`:
     * Extract root_cause pattern and gaps_found domains
     * If the gap was not caught by the expected capability node → classify as "blind-spot"
     * Write to `.allforai/bootstrap/learned/blind-spots.md` (append, do not overwrite)

3. **Feedback proposal:**
   Read `.allforai/bootstrap/protocols/feedback-protocol.md`. If learning
   extraction found a universally useful meta-skill issue, run:
   `python3 .allforai/bootstrap/scripts/record_meta_skill_feedback.py . --category "<category>" --message "<deidentified failure pattern>"`
   This must not ask the user mid-run. Prefer a writable local `myskills`
   repository; only fall back to anonymous GitHub issue draft/auto mode when no
   local repo is available.
~~~
