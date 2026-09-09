# T15 planning repairs — §5.1–§5.4 of the Codex/missing-product-docs evaluation

Scope: the four evidence-backed repairs named in
`T15-codex-missing-docs-evaluation.md` §5.1–§5.4, implemented in the candidate
source at HEAD `e30ccc7c`. No commit; root reviews. Campaign ledgers,
`test_results_pin.py`, candidate temp fixtures and the other evaluator's report
were not touched.

## What the evaluation asked for, and what the code actually did

The report proposed §5.1 as "two knowledge-file edits". That proposal was
checked against the real dispatch code before implementing, and it is not
sufficient on its own — **both** orchestrators drop the declared repair route in
code, in two different ways:

- **Claude** (`knowledge/run-engine/engine-core.js`, mirrored verbatim into
  `run-engine.workflow.js`): `computeReady` dispatched a node only when every
  `hard_blocked_by` id was in `done`, and a hard failure returned
  `needs_diagnosis` immediately. A failed QA node is never `done`, so the repair
  node was unreachable, exactly as the report predicted — but from
  `computeReady`, not from prose.
- **Codex** (`knowledge/flow-template.py`): `first_pending_node` ignored
  `hard_blocked_by` altogether and returned the first node in declaration order
  whose artifact gate failed. A failed QA node was therefore re-dispatched to
  itself forever until the 3-failure diagnosis cap halted the run; the repair
  node was never selected. The same omission meant a closure node could be
  dispatched on a failed QA dependency whenever declaration order allowed it.

So the repairs land in the consumed code paths first, with the prose updated to
match. `required_repair_loops` is consumed, not replaced: no new schema, no new
script, no change to `validate_unattended_readiness.py`'s existing shape rules.

## §5.1 — a failed QA node reaches its declared repair, bounded

Contract consumed as-is:
`.allforai/bootstrap/unattended-run-readiness-spec.json.required_repair_loops`
= `{scope, qa_node_ids, repair_node_id, closure_node_ids, max_attempts}`.

**Claude** — `claude/meta-skill/knowledge/run-engine/engine-core.js`
(+ the synced marker region in `run-engine.workflow.js`):

- `DAG_SCHEMA` gains `repair_loops[]`; `loadDagPrompt` now reads the readiness
  spec and returns `required_repair_loops` verbatim.
- `qaReportUsable(result)` — a failure opens a loop only when the QA node
  reached its own verdict **and published it** (`hard_fail`, non-empty
  `blocking_findings`, non-empty `artifacts_written`). Infrastructure failures
  (`invalid_artifact_gate`, `invalid_readiness_gate`, `deadlock`,
  `safety_warning`, `needs_iteration`, `exhausted_retries`) have no current
  report to repair against and stay diagnosis cases.
- `computeReady(nodes, done, repair)` — a failed dependency is satisfiable by
  **only** the `repair_node_id` declared for that QA node; every other successor
  still requires a completed dependency. The failed QA node itself is withheld
  while its repair is open, and every `closure_node_ids` entry is withheld while
  any `qa_node_ids` entry of its loop is not in `done`.
- `runEngine` — routes covered failures instead of stopping, records the routing
  through `repairRoutePrompt` (a *failed* transition, explicitly not a
  completion), re-dispatches the repair node for each attempt, closes the loop
  when the repair completes so the QA node reruns, and stops with
  `needs_diagnosis` when the budget is spent or when any failure in the wave is
  not a declared, budgeted, report-backed QA failure.

**Codex** — `codex/meta-skill/knowledge/flow-template.py`:

- `declared_repair_loops` / `open_repair_loops` read the same spec; unreadable
  or absent state declares nothing (fail-closed to today's behavior).
- `qa_report_usable` requires every declared exit artifact of the QA node to
  exist and, for JSON, to parse — a QA node that never published, or whose
  report is corrupt, is rerun rather than routed.
- Attempts are counted from `transition_log` completions of the repair node, so
  the budget survives driver restarts; `max_attempts` bounds it.
- `_pending_state` is now dependency-aware: an incomplete node is dispatchable
  only when its `hard_blocked_by` entries are complete, or when it is the
  declared repair node of an open loop. Declared closure nodes are withheld
  until their QA node itself completes.
- `blocked_pending_nodes` + a guard in `main`: "no dispatchable node while
  pending nodes remain" now exits 6 with the blocked ids. Previously that state
  could reach the success path.

**Prose, matching the code**: a "Declared cross-node repair loop" section in
both `orchestrator-template.md` files (Claude and Codex) and a Core Loop bullet
in the Codex template.

**Generation side**: `skills/bootstrap/SKILL.md` step 13 now requires every
QA → repair → closure loop to be declared in `required_repair_loops` when the
readiness spec is written, stating why the edge alone leaves the repair
unreachable.

**Planning gate**:
`skills/meta-orchestration/40-qa/bootstrap-node-expansion-qa/SKILL.md` now fails
a plan whose QA→repair→closure edges are not also declared in
`required_repair_loops` (new code `undeclared_repair_loop_routing`), with the
reachability reasoning in Guiding Philosophy and "What Every Production Node
Must Carry" so the auditor reasons about it rather than only matching a code.

## §5.2 — audit-induced plan deltas are re-confirmed before execution

- `knowledge/bootstrap-audits.md` Phase A: **any** node-set or `hard_blocked_by`
  change made after Step 3.4 — not only a G0 split/merge — enters the Phase A
  queue and is presented as a delta against the confirmed list (added / removed
  / re-wired, with the reason) before the three-lens gate, and is presented even
  when the queue is otherwise empty. `/run` is not offered until it is accepted.
- `skills/bootstrap/SKILL.md` Step 3.4 states that the confirmation is
  provisional until Phase A.
- `codex/meta-skill/skills/bootstrap.md`: the same delta is a real question on
  Codex; assume-and-declare cannot approve a plan the user never saw.

## §5.3 — effect proof is observable at its owning stage

`knowledge/node-spec-template.md` §Effect Verification: the required proof must
be observable at that node's own stage. When a deliverable is split so the full
effect first exists downstream, either merge the nodes or state the stage-local
effect here **and name the downstream node** that proves the full effect — and
that node's spec must carry it. The node-expansion audit enforces the second
half with a new `unowned_effect_stage` finding, so a deferral without a named
owner is rejected rather than silently accepted.

## §5.4 — promised fact documents are declared at planning

`bootstrap-node-expansion-qa/SKILL.md` gains `missing_document_contract`: a node
whose `responsibilities` include `documentation`, or whose Task promises a
document it will write, while carrying an empty `required_documents` (or a
required document with no `document_verification` argv), is a finding.
Deferring the declaration to run time is named as a planning gap: no gate can
demand a document nobody declared.

**Deliberately not done**: a hard `validate_bootstrap.py` rule of the form
"`documentation` responsibility ⇒ non-empty `required_documents`". That
predicate is not sound — several existing green tests legitimately carry a
documentation responsibility with no generated fact document — and forcing it
would have meant editing those tests to accept a new failure. The planning gate
that already caught §5.1 in this very run owns §5.4 instead. Recorded as
residual risk below.

## Tests

Red first, then green, for both executable changes.

New: `claude/meta-skill/knowledge/run-engine/tests/repair-loop.test.js`
(15 cases: schema + prompt wiring, `qaReportUsable` positive/negative,
`computeReady` admission/refusal/closure-hold/re-queue, and four `runEngine`
integration paths — route→repair→rerun→closure, no-report failure, undeclared
failure, budget exhaustion). 11 of 15 failed before the change.

New: 8 cases appended to `codex/meta-skill/test_flow.py` (routing on a usable
report; no routing without a report; no routing on an unreadable report;
budgeted re-attempt then QA re-queue; closure held until the QA rerun passes;
undeclared successor never runs on a failed dependency; blocked pending nodes
are not a finished workflow; unreadable spec keeps current selection). 3 failed
before the change, plus `blocked_pending_nodes` did not exist.

```
node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'   70/70 pass
python3 -m pytest codex/meta-skill/test_flow.py -q --tb=short              36/36 pass
python3 -m pytest claude/meta-skill/tests/unit -q --tb=short              647/647 pass
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py         exit 0
python3 claude/meta-skill/scripts/orchestrator/validate_generalization_boundaries.py exit 0
python3 claude/meta-skill/scripts/orchestrator/validate_skills.py                  exit 0
python3 claude/meta-skill/scripts/orchestrator/validate_specialization_contracts.py exit 0
```

No test was weakened, no expectation was relaxed, and no host-matrix pass is
claimed from these unit checks.

## Residual risk

1. **No host re-run.** These are unit and fake-agent level checks. The Claude
   path is exercised through `fake-agent`, not a real Workflow run; the Codex
   path is exercised through the driver's selection functions with the artifact
   gate stubbed to real artifact-status semantics, not through `codex exec`. The
   T15 cell was not re-run, so the scenario verdict stands unchanged.
2. **§5.2, §5.3 and the two new §5.1/§5.4 audit items are LLM-executed.** They
   are contracts the planner and the node-expansion audit must apply; no
   deterministic validator enforces them. §5.1's runtime half is deterministic,
   §5.1's declaration half is not.
3. **§5.4 has no deterministic planning check** (see above), so a planner that
   ignores the audit item can still promise a document in prose only.
4. **Codex second repair attempt regenerates a completed repair node.** With
   `max_attempts > 1`, `flow.py` re-dispatches the repair node even though its
   artifact gate passes, so its report is rewritten. That is intended (the loop
   must be able to try again), but it is a behavior change for any project whose
   repair node has non-idempotent exit artifacts.
5. **Engine resume semantics.** A repair node re-opened for a second attempt is
   removed from the in-memory `done` set, but its earlier `completed` transition
   stays in `workflow.json`. A cross-session resume therefore starts from
   "repair delivered, QA must rerun" — correct, but one attempt is not replayed.
6. **Codex selection is now dependency-aware, which is a behavior change beyond
   the repair loop.** `flow.py` previously ground forward on the first node with
   a failing gate, ignoring `hard_blocked_by` entirely. A project whose graph
   contains a dependency on a node that can never pass its gate (a retained or
   mis-wired node) now reports blocked and exits 6 instead of retrying an
   unrunnable node until the failure cap. That is the honest outcome and matches
   the Claude engine's deadlock detection, but it will surface plan defects that
   were previously hidden behind repeated retries.
7. **Concurrent accepted-with-gaps in a repaired wave.** If a wave contained
   both a routed QA failure and an `accepted_with_gaps` outcome, the accepted
   result is re-derived on the next wave rather than returned immediately. A
   declared closure node cannot be in such a wave, so this is an edge case, not
   a path the loop creates.
