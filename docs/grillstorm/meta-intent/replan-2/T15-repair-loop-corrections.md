# T15 — repair-loop corrections to 2cc347af

Scope: hard findings 1–3 of `T15-2cc347af-standards-review.md`, plus findings 1, 2, 5 and 6
of `T15-2cc347af-spec-review.md` (added by the coordinator in msg_ae969214f3a9). Implemented
on the current checkout (no new worktree, no commit). The decision-gate files
(`check_decision_inputs.py`, `product_intent.py`, `evidence_freshness.py`,
`validate_bootstrap.py`) belong to a separate editor and are untouched here; spec findings 3
and 4 are separately owned and not addressed.

Mapping: standards 1 = spec 5 (§1 below); standards 2 = spec 1 (§2); standards 3 (§3);
spec 2 (§4); spec 6 is the test gap, covered throughout and in Verification.

## 1. A routed repair swallowed another node's terminal verdict

`engine-core.js` ended a wave that opened any repair loop with `continue`, skipping the
`accepted` and `iteration_repair_stopped` checks below it.

- `iteration_repair_stopped` is committed into `done`, so the node never reappears and the
  run ended `{"status":"complete"}` — the review's scratch probe.
- `accepted_with_gaps` is *not* committed, so the node was re-dispatched in the next wave.
  A second run that happens to pass is committed and the recorded `accept` decision
  disappears; a node the Run Policy already accepted with gaps must never be re-run into a
  passing verdict.

Fix: the two terminal checks now run **after** routing rather than instead of it. Routing
still happens (the repair is recorded), but the wave's terminal verdict ends the run.
Precedence is unchanged: an unroutable hard failure still returns `needs_diagnosis` first.

## 2. Repair attempt identity

The declared contract in both `orchestrator-template.md` files is *at most `max_attempts`
attempts per failed QA node*. The two orchestrators implemented two different things:

| | before | after |
|---|---|---|
| `engine-core.js` | keyed `repair_node_id::qa_node_id`, in memory only — a restart handed the whole budget out again | same key, seeded from the durable record at load |
| `flow-template.py` | counted **completed transitions of the repair node**, so two QA nodes sharing one repair node shared one budget, and a repair *success* was the unit of accounting | counts, per QA node, the repair dispatches that answered *that* node's failure |

`flow-template.py` also re-dispatched the repair node on every iteration until the budget
was fully spent, so the QA node only re-ran after the last attempt — the declared "when the
repair node delivers, the QA node re-runs" never happened between attempts. `repair_progress`
now returns `(spent, answered)`; an answered failure is re-verified by the QA rerun, never by
another repair.

Both sides read attempts from durable state rather than inferring them:

- Codex walks `transition_log` directly (`repair_progress`).
- Claude asks the load-DAG step for `repair_attempts[] = {repair_node_id, qa_node_id, attempts}`
  — the count of that QA node's `failed` transitions, which is exactly one per grant because
  `repairRoutePrompt` writes one. Every declared QA node must state its attempts, explicit `0`
  included. A history that is absent, malformed, or missing a declared QA node stops the run
  with `invalid_repair_attempt_history`; a missing entry is missing history, not a fresh
  budget, so it never silently restores one. The review's probe (three resumes of a
  `max_attempts: 2` loop dispatching 2/2/2) now stops on the second resume.

## 3. Validation claims and invalid budgets

Both templates claimed the loop was "already shape-validated by
`validate_unattended_readiness.py`", which checked node membership and both edges but never
`max_attempts`. Corrected on both sides:

- The templates now state exactly what the validator checks and that it does not check
  whether the declared repair can fix the finding.
- `_validate_repair_loop_spec` now blocks `invalid_repair_loop_budget` when a declared
  `max_attempts` is not a positive integer (`bool` excluded), and warns
  `repair_loop_budget_defaulted` when the loop declares none.
- `repairBudget` / `repair_budget` return `null` / `None` for an explicitly invalid budget:
  the loop routes nothing and the QA failure goes to diagnosis. The documented default of 3
  is preserved for an omitted budget only, and Codex no longer borrows the unrelated
  `MAX_CONSECUTIVE_FAILURES_PER_NODE` for it (`DEFAULT_REPAIR_ATTEMPTS`).

## 4. Codex admitted stale and non-QA verdicts (spec finding 2)

`qa_report_usable` checked only that the QA node's exit artifacts existed and parsed. The
review's probe — an empty `transition_log` and a leftover `verify.json` — routed to repair
for `status: failed`, `failed_env` and `blocked` alike. Two rules now bind it, and neither
treats file existence or parseability as proof of a current report:

- **Run binding.** The report must have been written no earlier than the QA node's latest
  recorded dispatch (`transition_log.started_at`, one second of slack for timestamp
  resolution). A node with no recorded dispatch has no run to bind a leftover file to, so
  it is re-run rather than repaired against.
- **Non-QA exclusion.** A report whose status is `failed_env`, `blocked`, `not_ready`,
  `not_generated`, `existence_only` or `blocked_by_*` carries no QA verdict — the same
  admission rule `engine-core.js` applies through `NON_QA_FAILURE_TYPES`, which the Codex
  side previously had no analogue for. `NON_QA_REPORT_STATUSES` is the on-disk mirror of
  that set, and both templates now state the rule identically.

The legitimate recovery path is pinned by its own test: a QA node dispatched this run, whose
report was written after that dispatch and carries a real `failed` verdict with gaps, still
reaches its declared repair node.

## Verification

Each change was written test-first; the new tests were observed red against 2cc347af before
the fix and green after.

```
node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'   82/82 pass (was 70/70)
python3 -m pytest codex/meta-skill/test_flow.py -q --tb=short             49 passed (was 36)
python3 -m pytest claude/meta-skill/tests -q --tb=short                   653 passed, 2 failed*
python3 -m pytest codex/meta-skill/test_flow.py \
  claude/meta-skill/tests/unit/test_validate_unattended_readiness.py \
  claude/meta-skill/tests/unit/test_evidence_freshness.py -q --tb=short    94 passed (working tree)
```

\* Both failures are `test_evidence_freshness.py::test_same_commit_distinct_dirty_states_...`
and are an artifact of the isolation harness below (`git rev-parse` in a non-repo scratch
tree), not of any change here.

The working tree currently also fails
`test_run_policy_session.py::test_codex_driver_consumes_recorded_nonblocking_safety_warning`.
That failure is raised by `validate_bootstrap.py` (+399 lines from the concurrent
decision-gate editor) inside `publish_contract`; it does not reproduce in the isolated tree
below, which carries only this task's edits.

**Isolation.** Because another editor is changing `validate_bootstrap.py`,
`check_decision_inputs.py`, `product_intent.py` and `evidence_freshness.py` in the same
checkout, every suite above was re-run against a clean `git archive HEAD` tree with only this
task's files overlaid, so the results attribute to these changes alone.

Red observations before each fix (same tests, unchanged): 8 failures in `repair-loop.test.js`
for standards 1–3 and 2 more for the missing-history rule; 5 in `test_flow.py` for the
budget identity and 8 more for run binding and non-QA exclusion; 7 in
`test_validate_unattended_readiness.py`.

`run-engine.workflow.js` was re-synced from `engine-core.js`; the sync-check test passes.
`README.md`'s green count was updated to 80/80.

## Residual risk

- **No host proof.** Everything above is fake-agent (L2) and unit level. The Workflow shell
  was never executed on the real harness, and `flow.py` was never driven against a real
  Codex run. `tests/L3-runbook.md` remains the only real-agent path and was not run.
- **The Claude attempt history is agent-reported.** `repair_attempts[]` is produced by the
  load-DAG sub-agent counting `transition_log` entries, not read by the engine itself. A
  sub-agent that miscounts *downward* would hand out extra attempts; the engine can only
  reject a malformed shape, not a plausible wrong number. Codex reads the log directly and
  does not share this exposure.
- **A wave that both routes a repair and carries an unroutable hard failure** still returns
  `needs_diagnosis` and unwinds the routing, as before. That precedence was left as found.
- **The two admission rules are now equivalent, not shared.** `NON_QA_FAILURE_TYPES` (in-wave
  finding types) and `NON_QA_REPORT_STATUSES` (on-disk report statuses) are two lists in two
  languages that must be kept in step by hand; nothing fails if one drifts.
- **Run binding leans on `started_at` and mtime.** A workflow whose transition entries carry
  no `started_at`, or a filesystem with coarse timestamps, makes a current report look stale
  and sends a repairable failure to a re-run instead. That direction is fail-closed, but it
  can cost a legitimate repair.
- A repair node that never completes still re-queues forever in `engine-core.js`. The new
  `cappedPhase` helper makes that fail loudly in tests, but the engine itself has no wave cap.
