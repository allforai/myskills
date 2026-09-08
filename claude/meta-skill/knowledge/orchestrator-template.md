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

## Preflight Gate

Before executing any workflow node, run unattended readiness:

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
Before stopping, record `preflight_blocked` with
`record_run_event.py`, then run `summarize_run_log.py --write-report`.

## Run Policy (the only questions `/run` asks, and only before the first node)

Everything a human could be asked mid-run is asked here instead, once, in one
`AskUserQuestion`, and written to `.allforai/bootstrap/run-policy.json` through
the shared copied CLI. First run `python3 .allforai/bootstrap/scripts/product_intent.py . --run-policy`.
If it returns `run_policy_ready`, reuse the validated policy without asking.
For `needs_run_policy`, collect the three answers and submit JSON operation
`run-policy` with `answers` and the actual `user_reference`. Invalid policy blocks
for interactive repair. Three decisions, each with a displayed default (never
submitted automatically):

| key | question | options (first = default) |
|---|---|---|
| `on_repeated_failure` | The same node fails 3 times, the diagnosis is neither out-of-scope nor converged. | `continue` (keep diagnosing until the caps below stop it) / `halt` (stop and report on the third failure) |
| `on_needs_iteration` | concept-acceptance returns `needs_iteration`. | `halt_with_report` (write acceptance-report.md, stop; the fix / re-bootstrap / accept choice is made by the human afterwards) / `auto_fix_once` (run one repair loop on the named gaps, re-verify, then stop either way) / `accept` (record `accepted_with_gaps` in assumed-decisions.json and finish the run) |
| `on_safety_warning` | A non-blocking safety warning fires (see safety.md). | `continue` (log the warning and go on) / `halt` (stop at the first warning) |

After this section there are no more questions: every later branch reads
`run-policy.json`, and a branch that would need a fourth answer halts with a report instead.
The Workflow engine checks this policy before loading the DAG and consumes
`product_intent.py . --policy-event on_needs_iteration` for durable one-repair
semantics. Run Policy is never a product decision: unresolved decision_inputs
return to interactive bootstrap and cannot be approved by continue/accept.

### Dynamic preflight reconciliation

Before every execution wave, run every idempotent expander declared by
`workflow.json.expanders`, including `expand_game_2d_production.py`. An expander may add or
repair nodes after an upstream node creates a trigger artifact. Re-read the changed DAG and
rerun `validate_unattended_readiness.py`; do not execute newly exposed work when readiness
is not `ready`.

### Generic QA repair loop

Every node follows `.allforai/bootstrap/protocols/input-freshness.md`: after its
implementation settles, observe current inputs, track newly consumed files with
the public `read` operation, refresh required documents and publish evidence with
its actual acceptance command. A stale publication requires re-observation and
reverification, never a success transition. Contract-only freshness permits work
but does not prove completion. The independent artifact gate consumes this state.
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
A node whose freshness is `undeclared` (missing `source_inputs`) or `invalid`
(malformed declaration) cannot start or be committed: return it to interactive
bootstrap to declare its product source (explicit `[]` only when none applies).
Never add a declaration inside `/run` to pass the gate. Retained legacy nodes
report `undeclared` as a warning only when dependency declarations and recorded
freshness state are readable and valid; no provenance is claimed for them.
Malformed declarations or unreadable freshness state block even retained nodes:
dependency impact is unknown, so legacy compatibility cannot waive that failure.

After a node reports success, independently run `check_artifacts.py --node <node_id> --json`.
Non-empty `code_gaps` or `test_gaps`, partial/conditional status, placeholders, failed
validation, or other blocking findings cannot be committed as complete. Invoke the
`execution-repair-loop`, repair within its three-attempt budget, and **Rerun affected QA evidence**
through the original node plus the independent artifact gate. Exhaustion is a hard failure;
never waive, downgrade, or hide a gap.

## Phase B execution (CC: Workflow engine)

`/run` is fully autonomous after the Run Policy section — no further questions, no human stops. Drive it as:

1. Invoke the Workflow engine script at
   `${CLAUDE_PLUGIN_ROOT}/knowledge/run-engine/run-engine.workflow.js`.
   It reads `workflow.json`, schedules ready nodes (alignment_refs run in parallel),
   self-heals soft failures, commits each node immediately, and returns one of:
   - `{ status: "complete" }`
   - `{ status: "needs_diagnosis", hardFailures: [...] }`

2. On `complete`: run the learning-protocol extraction, then produce the Phase C report:
   a. **Evidence-anchored completeness (verification honesty).** Run
      `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/compute_completeness.py <base>` — it derives each
      node's TRUE state from its recorded `verification` evidence and writes
      `.allforai/bootstrap/completeness-report.json`. **Report the two-column result as the
      headline: VERIFIED (真验过) % vs unverified (只生成没验) %.** Never present "completed
      node count" as completeness — a node without real evidence is `unverified`, never counted.
   b. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_evidence.py <base>` to list any
      false "verified" claims (evidence missing / self-graded) — these are downgraded.
   c. **Launch gate:** if `completeness-report.json.critical_unverified` is non-empty, the product
      is NOT launch-ready regardless of node count — surface those critical flows as needing real
      verification. Do not call the product complete on self-attestation.
   d. Read `.allforai/bootstrap/assumed-decisions.json` + any UNRESOLVED, then stop.

3. On `needs_diagnosis`:
   a. Read `hardFailures` (always non-empty — a stuck graph carries a synthesized `deadlock`
      finding) + `workflow.json` `diagnosis_history`.
   b. GLOBAL cap (fix L1): if total entries in `diagnosis_history` ≥ 5, mark UNRESOLVED and
      stop — this catches oscillating root causes the per-cause cap misses.
   c. Run `${CLAUDE_PLUGIN_ROOT}/knowledge/diagnosis.md`: locate the root-cause node
      (use `suspected_root_node` when present). This is autonomous — never ask the user.
   d. Per-cause cap (the policy unit-tested as engine-core `convergenceCheck`): if the same root
      cause already appears ≥2 times in `diagnosis_history`, mark it UNRESOLVED, write best-effort
      output + TODO, and stop.
   e. Otherwise apply the repair plan WITH CASCADE (fix C2):
      `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/compute_reset_closure.py .allforai/bootstrap/workflow.json <root_id...>`
      → remove the returned closure (root + transitive downstream) from the `transition_log`
      completed set, then RESUME the engine
      (same session: resumeFromRunId; cross-session: re-invoke — workflow.json idempotency
      skips already-completed nodes).

4. Repeat until `complete` or an UNRESOLVED stop.

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
2. Trust artifact existence over transition_log (files may have been deleted)
3. Continue from where things stand

## Safety (warnings, not blockers)

- Same node fails 3 times → **before warning**, check `workflow.json.diagnosis_history` for that node:
  - If any entry has `"out_of_scope": true` → mark workflow halted, output TODO list, do NOT retry or ask user
  - If 2+ entries share the same `root_cause.node` → convergence cap reached, mark UNRESOLVED, output TODO list, halt
  - Otherwise → apply `run-policy.json.on_repeated_failure`: `continue` keeps the diagnosis
    loop going (the global and per-cause caps still stop it); `halt` marks UNRESOLVED, outputs
    the TODO list, and stops. Never ask here.
- 5 iterations with no new artifacts → output current state + TODO list
- Single node running > 10 minutes → warn but don't kill

## Termination

- All nodes' exit_artifacts are ready → success report
- concept-acceptance verdict = needs_iteration → apply `run-policy.json.on_needs_iteration`:
  `halt_with_report` writes acceptance-report.md (with the fix / re-bootstrap / accept options
  listed for the human to pick afterwards) and stops; `auto_fix_once` runs one repair loop on
  the named gaps, re-runs concept-acceptance, then stops whatever the verdict; `accept` records
  `accepted_with_gaps` in assumed-decisions.json and returns a qualified outcome,
  without marking that node completed or verified; the artifact gate treats an
  `accepted_with_gaps` report status as blocking. Never ask here.
- User interrupts → transition_log is already saved, resume with /run
- Safety warning → apply `run-policy.json.on_safety_warning`: `continue` logs it and goes on,
  `halt` stops with the warning in the report. Never ask here.

## Post-Completion

**Run regardless of success or early stop:**

0. **Run log summary:**
   Run `python3 .allforai/bootstrap/scripts/summarize_run_log.py . --write-report`.
   Keep `.allforai/bootstrap/run-log.jsonl`, `.allforai/bootstrap/run-summary.json`,
   and `.allforai/bootstrap/run-summary.md` as the auditable production trace.

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
