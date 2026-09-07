# Bounded Design Review

Use this contract for the adversarial review loops in specification design, task design, and
workflow/DAG design. Implementation review, diagnosis, test repair, and post-delivery probing keep
their own budgets and do not consume these rounds.

| Layer | Minimum rounds | Soft limit | Hard limit |
| --- | ---: | ---: | ---: |
| Specification design | 1 | 5 | 6 |
| Task design | 1 | 3 | 5 |
| Workflow/DAG design | 1 | 3 | 4 |

One complete, valid round whose critics cover every material claim with supported evidence and
raise no material finding closes the layer. More rounds are bought only by findings, never by a
count: a minimum above one would spend critics confirming a result the first round already
proved. The hard limit is the anti-thrash guard and never moves.

A round starts when the first required critic is dispatched and increments exactly once. All
required critics for that layer belong to the same round. A failed, timed-out, cancelled,
malformed, or incomplete critic consumes the round and cannot establish closure. One
infrastructure retry may complete the same round; it does not rerun critics that already returned
a valid verdict.

Track findings by stable failure-family ID, not wording. Rephrasing or rediscovering the same root
cause is a recheck, not a new family. A material classification is sticky; downgrade to residual
requires evidence and an independent critic. Internal repairs do not reset the counter. Only an
explicit user instruction that changes the goal, scope, public interface, or acceptance criteria
starts a new epoch and fresh budget.

## Stop policy

- Run the first round in full.
- Before the soft limit, continue when a material finding is new, remains open, or a material
  repair still needs confirmation.
- At or after the soft limit, continue only for an open material blocker, a new material family,
  or the single independent confirmation round required by the latest material repair.
- Close only after a complete valid round independently confirms every material family
  `verified_resolved`, with zero open material blockers. Residual-only findings do not block.
- If a known material blocker has no concrete repair or new evidence, stop immediately as
  `blocked_unrepaired`; do not spend rounds on cosmetic reruns.
- At the hard limit, never dispatch another round. If confirmation is incomplete, a critic result
  is invalid, or a material blocker remains, stop as `budget_exhausted_blocked`, not closed.
- No design-review layer may set a hard limit above 6.

Repairs occur between rounds: `round N verdicts -> repairs -> round N+1 confirmation`. The last
material repair may close only after that confirmation when budget remains. If it occurs at the
hard limit, report `budget_exhausted_blocked`.

Persist a round ledger containing layer, epoch, round, limits, new/rechecked/verified/open/residual
family IDs, repairs, whether confirmation is required, status, and stop reason. Status is one of
`continue`, `closed`, `blocked_unrepaired`, or `budget_exhausted_blocked`. The final report must
disclose the ledger, autonomous repairs and classifications, and every unresolved blocker.

Do not skip a layer merely because its artifact is absent. Skip only when the route makes the
layer genuinely inapplicable; a missing, stale, or invalid required artifact is a blocker.
