# Corrections: repair-authorization evidence recovery

Answers the independently reproduced findings in
`systematic-ledger-independent-review.md`. Owned files, and the only ones touched:

- `claude/meta-skill/scripts/orchestrator/repair_authorization.py` (1111 → 1391 lines)
- `claude/meta-skill/tests/unit/test_repair_authorization.py` (1039 → 1374 lines)
- `claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py` (+18 lines)
- `claude/meta-skill/tests/unit/test_validate_unattended_readiness.py` (+31 lines)
- this report

Two passes: the first closed the seven reproduced recovery findings, the second (this
revision) closed residuals **R1** and **R3**.

`run_safety.py`, the Codex flow and the Claude run-engine were **not** modified. No operation name, verdict `status`, or existing verdict
field changed: every addition is a new key on a refusal (`untrusted`, `expected_source`,
`expected_absence_of`, `rivals`, `undeclared`, `declared`, `budgets`) or a new field
inside `origin.proof`. The new `untrusted` values are `ledger_locked`,
`undeclared_repair_plan`, `invalid_repair_declaration`, `ambiguous_repair_declaration`,
`undeclared_repair_pair` and `budget_not_declared`. The frozen surface
the concurrent Claude integration is building against — `initialize`, `adopt_history`,
`authorize`, `start`, `settle`, `reconcile`, `consumption`, and the `execution_allowed` /
`charged` / `remaining` / `refunded` receipt fields — is unchanged.

**Verification.** `python3 -m pytest test_repair_authorization.py
test_validate_unattended_readiness.py test_run_safety.py -q` → **219 passed** (138 + 75 +
6). Nothing pre-existing was dropped or relaxed.

Both passes were checked the same way — every new guard reverted in a scratch copy, the
suite re-run — so the tests are regressions rather than restatements:

| Pass | Guards reverted | Result |
|---|---|---|
| Recovery findings | 11 guards | **13 failed, 109 passed** |
| R1 + R3 | declaration enforcement in `authorize` and `adopt_one`, readiness ledger-lock fence | **15 failed, 198 passed** |

The six original reproduction scripts were re-run against the fixed module and all six now
refuse.

---

## What was fixed

### 1. Adoption is bound to the run's own workflow, and empty recoveries are refused

**Was:** `adopt_history` accepted any readable project file whose digest matched, never
called `execution_traces`, and accepted `repair_routes: []`. A run that `initialize`
refused as having six charged routes got a zero-spend ledger from a file the caller wrote
a second earlier.

**Now**, three guards:

- `:469` — the evidence `source_path` must be `.allforai/bootstrap/workflow.json`, the
  same document `prove_absence` already binds absence to. A digest proves a file is
  itself, which is free for a file you just authored; binding the path is what makes the
  provenance mean anything.
- `:568` — an empty `repair_routes` is refused outright (`incomplete_history`), pointing
  the caller at `initialize`. Adopting nothing only stamps a zero-spend origin with a
  provenance record attached; ADR 0007 is explicit that absence of records is not proof of
  unused budget.
- `:509` — the number of adopted authorizations must equal the charge count
  `execution_traces` reads off the workflow, and `origin.proof.observed` now records those
  traces. Given the path binding this is an invariant assertion rather than a new veto —
  `unclaimed` already forced the match — but it is what makes the origin auditable: the
  proof now states which execution the reconstruction accounts for, not only how many
  records it consumed.

Tests: `test_history_may_only_be_reconstructed_from_the_runs_own_workflow`,
`test_an_empty_legacy_ledger_reconstructs_nothing`,
`test_adoption_records_the_execution_it_accounts_for`.

### 2. Absence is measured against the execution log

**Was:** `absence_of` named any list in the bound document. `absence_of=repair_routes`
proved `not_executed` from the same digest-verified workflow whose `transition_log`
recorded that exact authorization completing — because `repair_routes` keys its entries by
`repair_node_id`, a shape `attributes_to` cannot read, so it is "absent" of every run that
ever happened.

**Now** `:55, :1147` — `absence_of` must name `transition_log`, the one log that records
what the run executed. Binding the document was never enough while the caller still chose
which list inside it was read.

Test: `test_absence_is_measured_against_the_execution_log_not_another_list` (which also
asserts that the honest field refutes the same claim).

### 3. A stated authorization id is answered on its own terms

**Was:** `attributes_to` matched on id, then fell through to the node — so an explicit
*mismatch* was never disqualifying, and a record labelled `auth-B` cleared `auth-A`'s
unresolved blocker on a shared repair node.

**Now** `:603, :620` — a record that names an authorization has already said which attempt
it is about; a mismatch ends the question. The node fallback is for records carrying no
identity of their own.

Test: `test_a_record_naming_another_authorization_never_falls_back_to_its_node`. The
pre-existing `test_evidence_naming_another_authorization_is_refused` asserted this property
but passed on its fixture's *node* mismatch; the new test pins the id path with the node
held equal.

### 4. Node-only records must pick out exactly one attempt, chronologically

A record naming only a node is evidence about a *node*, and one node legitimately holds
several unresolved attempts at once — the shared repair ADR 0005 requires. Two conditions
now make such a record identify one attempt:

- **Live reconciliation** (`:1047, :1101`) — `reconcile` computes the node's other
  unresolved grants and refuses a node-only record while any exists, naming them in
  `rivals`. Resolve the sibling and the same record attributes cleanly.
- **Legacy adoption** (`:682`) — no two adopted authorizations may cite the same node-only
  record. One run of a node is one attempt of it.
- **Datability** (`:690, :1109`) — the cited record must carry a readable time. An undated
  record was previously admitted on both paths, because `predates` correctly treats "no
  time" as "not provably older"; that default is right for absence and wrong for
  execution, so the requirement is now explicit on the execution side.
- **Chronology** (`:696`) — a legacy execution record may not predate the
  `repair_routes` entry it claims to end.

Tests: `test_a_node_only_record_cannot_pick_one_of_several_unresolved_attempts`,
`test_one_node_only_record_cannot_evidence_two_legacy_attempts`,
`test_an_undated_record_cannot_show_that_this_attempt_ran`,
`test_an_undated_legacy_execution_record_is_refused`,
`test_legacy_execution_evidence_predating_its_own_charge_is_refused`.

### 5. Adopted claims are dated from the record that evidences them

**Was:** `adopt_one` took `started_at` from the caller and left it `None` when absent, which
silently turned the `predates` gate into a no-op — a record from a year *before* the
dispatch proved that dispatch ran.

**Now** `:782` — dates are derived from the source wherever the record omits them:
`granted_at` from the route's `dispatched_at`, `started_at` from the record the `start_ref`
resolves to, `settled_at` from the settlement record. Combined with the datability
requirement above, an adopted `started` entry always carries a claim time, so the
chronology a later reconciliation is checked against is the evidence's rather than the
caller's.

Test: `test_an_adopted_claim_is_dated_from_the_record_that_evidences_it` — asserts both
derived values and then that a stale record is refused against the derived claim.

### 6. A spend with no bound is refused, not recorded

**Was:** an adopted record could omit `budgets`; `consumption` then reported
`budget: null, remaining: null, exhausted: false` for a fully spent obligation, and
`recorded_budget` had nothing to pin, so every later grant could name its own bound.

**Now**, refusing the incomplete adoption (the alternative the task allows):

- `:766` — `adopt_one` refuses a record that does not record a positive bound for every
  obligation it charges (`incomplete_history`).
- `:245` — `check_entry` refuses a ledger entry without one (`unreadable_ledger`), so a
  hand-edited ledger cannot reintroduce the state either.

Every entry this module writes carries its bound, so `budget: null` is now unreachable
through any operation. See residual **R2** for the part I deliberately did not change.

Tests: `test_an_adopted_charge_with_no_recorded_bound_is_refused`,
`test_a_ledger_entry_with_no_bound_cannot_be_read`.

### 7. A held lock is classified

`:144` — the lock refusal now carries `untrusted='ledger_locked'`, like every other
refusal in the module, so a caller or gate routing on `untrusted` can see a fenced ledger
instead of an unclassified blocker. Test: `test_a_held_lock_is_classified_as_untrusted_state`.

---

## Residual constraints

Stated against the ADRs and CONTEXT.md, not against what the tests happen to permit.

### R1. CLOSED — the declared repair loop now sets the bound

**Was:** the first grant for a (repair node, QA obligation) pair set the bound, so a
request could charge 99 attempts against a loop the plan bounded at 3, or charge a pair
the plan never declared at all.

**Now** the authority is `.allforai/bootstrap/unattended-run-readiness-spec.json` →
`required_repair_loops`, read fresh on every grant and every adoption:

- `declared_bounds` (`repair_authorization.py:407`) builds `{(repair node, QA node):
  bound}` from that spec. `declared_budget` (`:387`) mirrors what both hosts and
  `validate_unattended_readiness.py` already do — an omitted `max_attempts` takes the
  documented default of 3; one that is present but not a positive integer is a planning
  error, refused rather than read as a request for that default.
- `require_declared` (`:477`) refuses an undeclared pair (`undeclared_repair_pair`) and
  any stated bound that differs from the declared one (`budget_not_declared`). It refuses
  rather than silently substituting the declared value: a caller asking for 99 against a
  declared 3 is a defect in that caller, and answering with a quiet 3 hides the
  disagreement.
- `authorize` (`:830`) applies it before any question about ledger state — an undeclared
  charge has no budget to be within.
- `adopt_one` (`:800`) applies the same rule to history: a record stating no bound takes
  the declared one, a record stating a different one is refused. History the caller
  re-prices is not history.
- An unreadable, absent, malformed or self-contradictory plan blocks with something to fix
  (`undeclared_repair_plan`, `invalid_repair_declaration`, `ambiguous_repair_declaration`).
  No bound is ever invented.

**Dynamic expansion** is supported by construction rather than by exception: the spec is
re-read per grant, so a loop declared later becomes grantable immediately, and nothing in
that reading touches the ledger, so spend already charged is preserved. A bound that
*changes* for a pair that already has history is refused by the pre-existing
`recorded_budget` check — now with a message naming the real cause — and the ledger is
neither re-priced nor reset; the plan and the spend have to be reconciled by a person.

Tests: `test_a_request_may_not_inflate_the_declared_budget`,
`test_an_undeclared_pair_has_no_budget_to_be_within`,
`test_a_valid_expansion_is_grantable_and_keeps_what_was_spent`,
`test_a_redeclared_bound_for_a_charged_pair_stops_rather_than_repricing`,
`test_an_unusable_declaration_blocks_with_something_to_fix` (10 cases),
`test_an_omitted_max_attempts_takes_the_documented_default`,
`test_an_adopted_bound_comes_from_the_plan_not_from_the_record`,
`test_a_bound_that_moves_is_refused` (rewritten: the bound now moves in the plan, not in
the request).

**Fixtures**, not special cases: the suite gained a `plan()` helper that writes a realistic
`required_repair_loops` spec, and `started()` writes a default plan of three loops that
declare no `max_attempts` — the ordinary shape, taking the documented default. Tests
exercising a bound of 1 or 2 now declare a plan that says so. No check was weakened and no
test is exempted from the declaration rule.

### R2. CLOSED by construction — no reachable path leaves a bound unknown

The `exhausted` formula is unchanged, and deliberately so: with R1 closed there is no
reachable path to an unknown bound, so adding an explicit unknown state would add API
surface for a state that cannot occur. Every entry `authorize` or `adopt_one` writes now
carries a bound equal to a declared positive integer, `check_entry` refuses any entry
without one on every read, and `consumption` reads bounds only for the obligations
`check_entry` validated. `test_every_reported_obligation_has_a_known_bound` asserts the
property directly rather than trusting the argument.

### R3. CLOSED — the readiness gate fences a held ledger lock

`validate_unattended_readiness.py:164` now adds an `unreconciled_repair_accounting`
blocker when `.allforai/bootstrap/repair-authorizations.lock` exists, with the same
reasoning the safety lock already carries: the lock outlives a writer that died mid-update,
so what the ledger says about spent budget may be a read taken across an unfinished write.
It is refused, never removed — clearing it is a reconciliation decision about a specific
interrupted grant, which this gate cannot identify. The helper-side half landed earlier as
`untrusted='ledger_locked'`.

Deliberately **not** paired with a missing-ledger blocker. A run that has not yet recorded
its origin has no ledger, and that is the ordinary state of every new run before
`initialize` proves zero from the workflow; blocking on it would refuse every legitimate
run at its first readiness check. `test_a_missing_repair_ledger_does_not_block_readiness`
pins that, and `test_a_held_repair_ledger_lock_blocks_the_run` pins the fence and that the
gate does not delete it.

### R4. A historical run that executed but never repaired can no longer be adopted

New, and deliberate. Fix 1's empty-ledger refusal means a run whose workflow shows
completed nodes but an empty `repair_routes` is refused by `adopt_history` (no history to
reconstruct) *and* by `initialize` (it shows execution). Such a run cannot be resumed by
this module at all.

That is ADR 0007's stated trade-off made concrete — "Incomplete or ambiguous evidence
leaves the existing run blocked... Starting a separate new run requires explicit user
confirmation" — and an empty `repair_routes` is exactly absence of records. But it is a
real narrowing of what recovers, and the only route out is the user-confirmed separate
run. Operators should be told this rather than discovering it at a blocked resume.

### R5. `complete` is still a caller assertion — but it now ranges over evidence the caller did not author

`adopt_history` still requires `evidence.complete is True` on the caller's word, and
`prove_absence` still requires the caller to vouch for the log. That remains the accepted
design: ADR 0007 asks for evidence "asserted complete". What changed is that the
assertion is no longer vacuous — it now ranges over the run's own workflow (fix 1) and,
for absence, over the execution log specifically (fix 2), instead of over a document and a
field the caller chose. The residual is that a caller who can rewrite `workflow.json`
itself can still mislead the reconstruction; nothing in this module can detect that, and
no ADR claims otherwise.

---

## Remaining limits after this pass

Reported rather than fixed, because each is either outside my ownership or a change the
coordinator should sequence.

1. **`loop_binding` still reads `required_repair_loops` from `workflow.json`**, while
   `declared_bounds` reads it from the readiness spec. Only the spec now decides anything:
   the binding is informational provenance recorded in `origin.binding` and echoed by
   `consumption`. Pointing both at the spec would be more coherent, but `origin.binding`
   is recorded in existing ledgers and `consumption.binding` is consumer API, so it is a
   coordinated change, not a drive-by one.

2. **Cross-host divergence on an unreadable plan.** `flow-template.declared_repair_loops`
   swallows a parse error and returns `[]`, so `eligible_obligations` returns `{}` and
   Codex silently declines to dispatch; the helper now refuses actionably with
   `untrusted='undeclared_repair_plan'`. Same outcome (nothing runs), different
   diagnosability. Codex is not mine; root was notified.

3. **`ledger-double.js` has drifted further from the helper.** The engine's documented
   mock never consults the readiness spec and still reports `budget: null,
   exhausted: false`, so it now blesses grants the real helper refuses. Its own MOCK
   BOUNDARY comment already says `declared-loop.test.js` — which drives the real helper —
   wins on disagreement, and that test's fixture (`real-gate.js declaredLoopProject`)
   already writes a spec whose `max_attempts: 2` matches its loop, so nothing is broken.
   Root was notified so the double can be re-aligned deliberately.

4. **A plan that is itself wrong is still trusted.** The helper enforces that a charge
   matches the declared loop; it cannot tell whether the declaration is the one the user
   confirmed. `plan_confirmation_blockers` in the readiness gate is what covers that, and
   nothing here duplicates it.

5. **R4 stands unchanged** — a historical run that executed but never repaired still
   cannot be adopted, and the only route out is the user-confirmed separate run.
