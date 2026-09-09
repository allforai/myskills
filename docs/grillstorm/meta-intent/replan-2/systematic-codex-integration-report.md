# Codex host integration

Host-integration half of the systematic remediation plan for the Codex executor. Owned
files only: `codex/meta-skill/knowledge/flow-template.py`, `codex/meta-skill/test_flow.py`,
`codex/meta-skill/knowledge/orchestrator-template.md`. No production validator, no Claude
engine file, and no foundation helper was edited. `repair_authorization.py` and
`run_safety.py` are consumed exactly as shipped.

## Verification

```
python3 -m pytest codex/meta-skill/test_flow.py -q
```

→ **117 passed** (108 before this task; 9 new). Every repair-accounting fixture now drives
the real `repair_authorization.py` CLI in a temporary project, so these are driver tests
against the canonical helper, not stubs. No paid CLI call and no live model launch: the
executor is a local callable and `run_codex` is the only thing replaced.

## 1. Safety halt (independent branch, built first)

The driver read `run-warnings.json` only at the **top** of an iteration. A warning raised
by the node that had just run was therefore answered one iteration too late — after that
node had been recorded `completed` and had already released its successors.

Now, in `main()`:

- **After the executor, before the completion.** `read_safety_warnings` is re-read the
  moment `run_codex` returns. An unreadable or wrong-shaped report is not an empty one; it
  fails closed the same way a halt does.
- **Quarantine, never cancel.** No cancellation is assumed. The finished executor's outputs
  exist, so `quarantine_outputs` calls `run_safety.py . --nodes-json <ids> --reason <r>`
  and confirms the verdict names every node it asked for. The node is recorded `failed`
  with the quarantined artifact list; nothing is deleted and nothing is accepted. An
  unconfirmed persistence is reported as `quarantine_persisted: false`, never assumed.
- **Global, not next-loop.** `safety_halted()` treats the marker *and* the retained
  `safety-quarantine.lock` as a halt. `_pending_state` then returns no dispatchable node
  and blocks every pending node — including branches that never failed — and
  `open_repair_loops` returns nothing, so a halt is never answered by a repair route.
  `validate_unattended_readiness.py` already refuses both paths, so the halt survives a
  restart.
- **The in-flight authorization is left unresolved** and reported as
  `unresolved_repair_authorization`. Whether that quarantined attempt delivered is a
  question for `reconcile`, not for the driver that halted it.

## 2. Repair authorization through the canonical ledger

`workflow.json.repair_routes` is no longer read or written by this driver. Everything goes
through `.allforai/bootstrap/repair-authorizations.json` via `repair_authorization.py`:

| driver function | helper operation | rule it carries |
|---|---|---|
| `ledger_consumption` | `consumption`, then `initialize` only on `missing_ledger` | authoritative per-QA spend; unknown is not zero |
| `repair_attempts_spent` / `repair_progress` | `consumption` | budgets read from the ledger, never from legacy route counts |
| `eligible_obligations` | — | a shared repair charges only obligations with budget left |
| `authorize_repair_dispatch` | `authorize` then `start` | charge and launch claim, both durable before the executor |
| `settle_repair_dispatch` | `settle` | only for an attempt this driver watched finish |

Decisions confirmed by the coordinator before integration:

- **Run identity.** `consumption` is called first with no `run_id`. `initialize` is reached
  only when the helper reports `untrusted: missing_ledger`, with a freshly generated id. An
  existing ledger, an ambiguous history, or an unresolved `authorized`/`started` record
  yields `None` — the driver blocks and never resets. No new run-id state file was
  introduced.
- **`authorize` is not permission to run.** Execution proceeds only when `start` returns
  `execution_allowed: true`. Without a durable grant the driver stops with
  `"repair dispatch was not authorized"` rather than running an unpaid attempt.
- **Unknown never settles.** A return code of 124/130, or a safety halt, skips `settle`
  entirely, leaving the grant unresolved so the next dispatch is refused.
- **`initialize` / `adopt_history` / `reconcile` stay out of ordinary execution.** The
  driver calls `initialize` only for a provably new ledger and never calls the other two.
  Recovering a historical or crashed run is a deliberate, evidence-backed operation.
- A consumption verdict is memoised against the ledger's own digest, so an unchanged file
  is not re-read. Any write changes the digest and the next read goes back to the helper;
  the helper remains the only authority.

## 3. QA branch behaviour

- **An exhausted obligation is blocked, not re-run.** Previously the Codex driver released
  an exhausted QA node to run again and relied on the generic consecutive-failure cap to
  end the run. It now blocks the obligation and reports it, and the run cannot finish
  around it. This was a real cross-host divergence: `runEngine` already reaches
  `needs_diagnosis` through `blockedFailures`. Four existing tests asserted the old
  behaviour and were updated to the new contract with their coverage kept — see
  §5.
- **A delivered repair is not exhausted.** The `not answered` guard keeps the QA rerun that
  judges a delivery, which is not another repair attempt.
- **Ordinary QA failure blocks its chain only.** The failed QA node and its closure stay
  blocked; an independent branch keeps running; the run still cannot finish.

## 4. Declared budgets vs generic caps

`MAX_CONSECUTIVE_FAILURES_PER_NODE` (3) and `MAX_STAGNANT_ITERATIONS` (5) could end a
declared loop before its `max_attempts` was spent, and report a supervisor threshold
instead of an exhausted budget. `failure_threshold(project_root, node_id)` and
`stagnation_limit(project_root)` now raise those backstops to what the plan declared —
budget + 1 failures, and 2 × budget + 1 stagnant transitions — for nodes in a declared
loop only. Both stay finite, a node in no loop keeps the generic value, and a loop
declaring fewer attempts never lowers them.

## 5. Tests

New (9):

| test | contract |
|---|---|
| `test_a_safety_warning_raised_by_the_executor_stops_before_the_completion` | halt checked after the executor; node recorded `failed`; outputs quarantined and preserved; no further dispatch |
| `test_a_safety_halt_stops_every_branch_not_only_the_one_that_raised_it` | `late_wave_safety_halt`: run-wide stop reaches an untouched branch |
| `test_a_safety_halt_is_not_answered_by_a_repair_route` | `hard_qa_with_safety_warning`: routing and dispatch both refused |
| `test_an_ordinary_qa_failure_blocks_its_chain_but_not_an_independent_branch` | `ordinary_qa_failure_with_independent_branch` |
| `test_a_shared_repair_charges_only_the_obligations_that_still_have_budget` | `shared_repair_asymmetric_budget`, driven through the real ledger |
| `test_a_replayed_authorization_charges_nothing_and_never_re_executes` | `duplicate_authorization` + `conflicting_authorization_replay`; only the first `start` executes |
| `test_an_unresolved_authorization_blocks_the_next_dispatch_instead_of_replaying_it` | `unknown_execution_after_crash`: no refund, no re-execution, reconciliation required |
| `test_a_declared_per_qa_budget_is_not_curtailed_by_the_generic_caps` | explicit `max_attempts` outranks both caps |
| `test_a_smaller_declared_budget_never_raises_the_generic_backstop` | and never lowers them |

Retargeted at the canonical ledger, same contract: `test_an_unreadable_repair_ledger_dispatches_nothing`
(5 damaged-ledger shapes), plus two replacements — `test_a_missing_ledger_on_a_run_with_history_blocks_instead_of_starting_at_zero`
and `test_a_provably_new_run_starts_at_zero_and_is_recorded_as_such` — which together
replace the old `test_an_absent_repair_ledger_is_a_run_that_has_charged_nothing`. That old
test asserted absence meant zero, which ADR 0005 reverses.
`test_a_repair_dispatch_is_charged_before_its_executor_runs` now asserts against the ledger
the executor could actually read: charged *and* `started` while its own executor runs, and
`settled` afterwards.

Changed expectations (4), all the same defect: an exhausted obligation used to re-run.
`test_repair_delivery_requeues_qa_before_closure`,
`test_a_repair_attempt_that_delivers_nothing_never_releases_the_qa_rerun` (×4 modes),
`test_a_shared_repair_node_budgets_each_qa_node_separately` and
`test_a_spent_budget_survives_a_restart` now assert the obligation is blocked and reported.
Each kept its original coverage — attempts still spent on non-delivery, closure still
never reached, sibling budgets still independent, budget still resumed across a restart —
and each gained the blocked-obligation assertion. No assertion was weakened or deleted.

Scenario tests execute the behaviour and compare it to the fixture's `expect`; the fixture
is never asserted against itself.

## 6. Remaining limits

- **The Claude engine still charges `workflow.json.repair_routes`.** The Codex driver is
  now the only consumer of the canonical ledger. The coordinator recorded this as a
  temporary consumer gap, not accepted parity: root integrates Claude against the same
  ledger before acceptance, and the shared scenario tests must then prove equivalent
  business outcomes on both hosts.
- **No cross-host parity is demonstrated here.** These are Codex driver tests. Per ADR
  0004 both hosts must be checked against the same contract scenarios on the real hosts;
  simulated driver tests do not replace actual-host acceptance, and the 60-cell campaign
  is unaffected by this task.
- **Bootstrap must ship `repair_authorization.py` and `run_safety.py`** into
  `.allforai/bootstrap/scripts/`. `AGENTS.md` already lists both among the helpers the
  generated run consumes; `codex/meta-skill/skills/bootstrap.md` is not mine to edit, and
  whether the generator actually copies them was not verified by this task. If either is
  absent at runtime the driver fails closed — no ledger means no dispatch, and a missing
  `run_safety.py` means the halt is reported with `quarantine_persisted: false` — but that
  is a fail-closed run, not a working one.
- **`adopt_history` and `reconcile` have no driver path.** A run whose ledger is missing or
  whose authorization is unresolved blocks with an actionable message and is recovered by
  running the helper deliberately. That is the accepted trade-off in ADR 0007, not an
  oversight, but it means no automated recovery exists for legacy Codex runs that already
  spent `repair_routes` attempts.
- **`_LEDGER_READS` is unbounded** for the life of a driver process, keyed by
  `(project_root, ledger digest)`. One entry per distinct ledger state in a single run;
  not a leak worth managing at this size, but it is not evicted.
