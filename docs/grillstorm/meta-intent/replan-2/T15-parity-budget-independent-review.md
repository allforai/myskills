# T15 — Independent review: repair_routes durable budget semantics (parity lane)

Scope: `git diff 47ea2855` working tree — `engine-core.js` + workflow mirror, `flow-template.py`,
tests, both orchestrator templates. Read-only. Probes: `node --test` repair suites (36 pass),
`pytest -k "repair or ledger or budget"` (57 pass), two probes against real `runEngine`.

## Blocking defects

### B1 — A shared repair node charges a QA node past its declared `max_attempts` (Claude only)

`engine-core.js:611-621` charges **every** QA node in `openRepairNodes` unconditionally, while
`retained` (`:657-665`) keeps the loop alive if **any** sibling still has budget. A QA node already at
its budget is charged again.

Probe: resumed run, `max_attempts: 2`, loop `{qa:[verifyA,verifyB], repair}`, seeded `verifyA: 1`,
`verifyB: 0`, repair returns `unmeasured_repair_delivery`:

```
charges = repair:verifyA:2, repair:verifyB:1, repair:verifyA:3, repair:verifyB:2
```

`verifyA` gets a 3rd dispatch under a 2-attempt budget and the durable ledger records `"attempt": 3`.
This contradicts the invariant both templates now state verbatim ("the declared `max_attempts` is
therefore the single bound on every repair dispatch for that QA node"), and is an **adapter
divergence**: Codex `qa_nodes_routed_to` → `open_repair_loops` (`flow-template.py:846-848`) skips
`spent >= budget`. Fix: filter the charge loop by remaining per-QA budget. Bounded (≤ 2×budget).

### B2 — `routed.length + retained.length` double-counts, masking a terminal failure

`engine-core.js:684` compares counts, not a set. A node that is the repair node of one open loop **and**
a `qa_node_id` of another lands in both lists, so one failure fills two slots and an unrelated terminal
failure in the same wave is dropped.

Probe: loop1 `{qa:[verify1], repair:R}`, loop2 `{qa:[R], repair:R2}`, policy `on_safety_warning:
"halt"`, node `other` raising a safety warning in the wave where `R` fails → `other dispatches = 2`,
`safety-report:other` twice. A recorded safety halt is re-dispatched instead of stopping the run.
Neither `validate_bootstrap.py:1751` (self-reference within one loop only) nor
`validate_unattended_readiness.py:263-306` forbids the overlap. Fix: union the handled ids, compare
set size.

## Verified clean

Charge lands before the executor on both hosts — Codex proved at driver level, not helper-only, by
`test_a_repair_dispatch_is_charged_before_its_executor_runs`. An interrupted dispatch keeps its
attempt; a route interrupted before dispatch costs nothing; non-delivery, executor error and success
each cost one attempt; unreadable or missing ledger entries fail closed on both hosts;
`NON_QA_FAILURE_TYPES` stay out of `retained`, so structural and safety verdicts stop immediately;
closure still waits on the QA rerun; delivery is still measured; `sync-check.test.js` enforces the
mirror.

## Proof limits

No host scenario launched. B1's precondition (siblings diverging in spent budget) and B2's (cross-loop
node overlap) were hand-constructed; I did not confirm a generated plan produces either shape.
Unexamined: a run upgraded across this commit reads `repair_routes` as absent and restarts the budget
at 0 — no migration from the old `transition_log` count exists, but reaching it needs a mid-run
re-bootstrap.
