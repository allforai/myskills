# Independent review: repair-authorization evidence recovery and the safety helper

Read-only audit, worktree `grillstorm-meta-intent` at `47ea2855`. Scope as dispatched:
`claude/meta-skill/scripts/orchestrator/repair_authorization.py` (1111 lines) and
`claude/meta-skill/scripts/orchestrator/run_safety.py` (106 lines), judged against ADR
0005–0007 and `systematic-remediation-plan.md`. Nothing in the repository was modified
except this file. Every counterexample below was reproduced against the real helper via
its CLI, in throwaway fixture directories under the session scratchpad; no production
file, test, or host model was touched.

Both helpers are currently **untracked** (`git status` reports `??`) — themselves part of
in-flight work. `repair_authorization.py` held md5 `8740750ea0ee523e12aefbff29fd819d`
throughout. The Claude run-engine *did* change under me mid-audit; see finding 9, where an
earlier note of mine is retracted.

Baseline: `python3 -m pytest claude/meta-skill/tests/unit/test_repair_authorization.py
claude/meta-skill/tests/unit/test_run_safety.py -q` → **114 passed**. Every finding below
is therefore an *uncovered gap*, not a regression.

---

## Summary

| # | Severity | Where | Contract breached |
|---|---|---|---|
| 1 | **High** | `repair_authorization.py:440` `adopt_history` | ADR 0007 / plan §5 — a self-authored file adopts a zero-spend history over a run whose workflow shows execution |
| 2 | **High** | `repair_authorization.py:1004` `prove_absence` | ADR 0006 — `absence_of` names a caller-chosen field, so absence is proved from a field `attributes_to` cannot read |
| 3 | **High** | `repair_authorization.py:564` `attributes_to` | ADR 0006 — a record carrying a *different* `authorization_id` still attributes, via the node fallback |
| 4 | Medium | `repair_authorization.py:681` + `:580` | ADR 0007 — an adopted `started` grant may omit `started_at`, which silently disables the `predates` time gate |
| 5 | Medium | `repair_authorization.py:580` | ADR 0006 — a record with no timestamp at all is never "provably older", so any timeless same-node record proves execution |
| 6 | Medium | `repair_authorization.py:1057` `consumption` | ADR 0005 — an obligation with an unknown budget reports `exhausted: false`, a false negative |
| 7 | Medium | `validate_unattended_readiness.py:120` | ADR 0005 / plan §3 — the readiness gate fences the safety lock but not the ledger lock or a missing ledger |
| 8 | Low | `repair_authorization.py:123` `ledger_lock` | An abandoned lock is a permanent halt whose verdict carries no `untrusted` classifier |
| 9 | Info | both hosts | Plan §1 parity — **checked and now sound**; a mid-audit correction is recorded below |

Approved-by-design behaviour that I checked and did **not** count as a defect is listed at
the end, so the distinction the dispatch asked for is explicit.

---

## 1. `adopt_history` bypasses the prior-execution gate entirely (High)

`initialize` (`:365`) is careful: it reads the run's own `workflow.json`, computes
`execution_traces`, and refuses when any transition, repair route, or finished node
exists — "a missing ledger is not proof that it spent no repair budget."

`adopt_history` (`:440`) never calls `execution_traces`, and never requires the evidence
source to *be* the run's workflow. `verify_source` (`:415`) only proves that the named
file is the file whose digest is quoted (`:427–428`): any readable path inside the project
qualifies, and the digest is trivially satisfied by the caller that wrote the file.
`legacy_routes` (`:526`) then accepts `repair_routes: []`, and the completeness check
(`unclaimed = set(range(0)) - set()`) is vacuously satisfied.

Reproduction — same fixture, two calls:

```
workflow.json: 6 repair_routes for repair-1/qa-1, 1 completed node, 1 transition,
               required_repair_loops: [{repair-1, [qa-1], max_attempts: 3}]

initialize                                  -> blocked / prior_execution
                                               observed {"completed":1,"repair_routes":6,
                                                         "transition_log":1}

echo '{"repair_routes": []}' > legacy-evidence.json
adopt_history  source_path=legacy-evidence.json
               source_digest=<its own sha256>
               complete=true  authorizations=[]   -> ok, origin "adopted_history", adopted 0

consumption                                 -> obligations: []          (zero spend)
authorize repair-1/qa-1 budgets {qa-1: 99}  -> authorized, remaining 98
```

The run that `initialize` refuses as having a history is handed a clean zero-spend ledger
with `origin: adopted_history` and full provenance recorded — provenance pointing at a
file the caller wrote a second earlier. This is precisely the outcome ADR 0007 forbids
("absence of records is not proof of unused budget"; a reset "requires explicit user
confirmation"), and it is the outcome `initialize:396–402` refuses to grant even to a
caller who asks for it directly.

Every existing `adopt_history` test passes `source_path = WORKFLOW`, so the intended usage
is workflow-anchored — but nothing enforces it. `test_a_source_with_no_legacy_ledger_
offers_nothing_to_reconstruct` covers a source with *no* `repair_routes` key; the empty-
list case is uncovered.

Suggested contract (not applied): bind adoption the way `prove_absence:996` already binds
absence — require `source_path` to be the run's own workflow, or require the reconstructed
route set to account for `execution_traces(workflow)` — and refuse an adoption that leaves
a run with observed execution at zero spend.

## 2. `prove_absence` lets the caller pick a field that cannot contradict it (High)

`prove_absence` (`:985`) enforces two real guards: the document must be this run's own
execution record (`:996`, bound to `origin.proof.source_path`), and the log must be
asserted complete (`:1004–1008`). What it does not constrain is *which* list inside that
document is examined (`:1009`). `attributes_to` (`:556`) reads only `authorization_id`,
`node`, and `node_id` — so pointing `absence_of` at a list whose records use different key
names makes the absence unfalsifiable.

`repair_routes` is exactly such a list: its entries carry `repair_node_id` /`qa_node_id`,
never `node`. Reproduction against a workflow that records the attempt running:

```
workflow.json (one file, one digest, used for both calls):
  transition_log: [{node: repair-1, authorization_id: auth-A,
                    status: completed, at: 2030-01-01T00:00:00Z}]
  repair_routes : [{repair_node_id: repair-1, qa_node_id: qa-1, attempt: 1, ...}]

reconcile auth-A not_executed  absence_of=transition_log  complete=true
    -> blocked / unattributable_evidence  "transition_log records work for this attempt at [0]"

reconcile auth-A not_executed  absence_of=repair_routes   complete=true
    -> ok, outcome "aborted", attribution {"kind":"complete_log_absence",
                                           "records_examined": 1}
```

Same file, same digest, same `complete: true`, opposite verdict. The attempt whose
execution the very same document records as `completed` is settled `aborted` and its
unresolved-execution blocker is cleared. `records_examined: 1` is reported as if the one
record examined were reassuring.

Suggested contract: constrain `absence_of` to a declared execution log (the field
`origin.proof` names, or an allowlist), or make a field whose records cannot express node
identity an unverifiable-evidence refusal rather than a proof.

## 3. A conflicting `authorization_id` does not disqualify a record (High)

`attributes_to` (`:556–564`) returns True on `authorization_id` match, else falls through
to `node`/`node_id` match. An explicit *mismatch* on `authorization_id` is never a
disqualifier. So evidence that states, in the record itself, that it is about a different
grant is accepted as evidence about this one — as long as the repair node matches.

The dangerous shape is two grants of the same repair node that are unresolved at the same
time. `unresolved` (`:247`) blocks a second grant only for the *same obligation*, so a
shared repair node serving `qa-1` and `qa-2` legitimately holds two live grants at once
(that shape is required by ADR 0005 and asserted by
`test_an_unresolved_grant_blocks_only_its_own_obligations`).

```
initialize run-A; authorize+start auth-A (repair-1, qa-1); authorize+start auth-B (repair-1, qa-2)
consumption -> qa-1 unresolved [auth-A], qa-2 unresolved [auth-B]

workflow transition_log: [{node: repair-1, authorization_id: "auth-B",
                           status: completed, at: 2030-01-01T00:00:00Z}]

reconcile auth-A executed observation_ref=transition_log[0]
    -> ok, attribution.record.authorization_id == "auth-B"
consumption -> qa-1 unresolved []      (auth-A's blocker cleared by auth-B's evidence)
```

The stored provenance faithfully records `authorization_id: auth-B` inside the attribution
for `auth-A` — the ledger preserves the contradiction rather than refusing it.

`test_evidence_naming_another_authorization_is_refused` (test file `:385`) looks like it
covers this, but its fixture sets `node='elsewhere'` *and*
`authorization_id='a-different-grant'`, so it passes on the node mismatch. The test name
asserts a property the code does not have. Worth naming explicitly, because it is the kind
of coverage that makes a later reviewer stop looking.

Suggested contract: when a record carries an `authorization_id` at all, it must equal this
one — the node fallback should apply only to records with no identity of their own.

## 4. An adopted `started` grant may have no `started_at`, disabling the time gate (Medium)

`adopt_one` (`:681`) writes `'started_at': text(record.get('started_at')) or None`, and
`check_entry` (`:193`) does not require it even for `state: 'started'`. `prove_execution`
(`:976`) then calls `predates(observed, text(entry.get('started_at')))`, and `predates`
(`:580`) returns False whenever `moment` is empty. For an adopted `started` grant with no
`started_at`, the temporal attribution guard is a no-op.

```
adopt_history: one route (repair-1/qa-1), record state "started",
               start_ref transition_log[0] (dispatched 2020-01-01), NO started_at
    -> ok, adopted 1, ledger started_at == None

workflow transition_log: [{node: repair-1, status: completed, at: "2019-01-01T00:00:00Z"}]
reconcile old-1 executed observation_ref=transition_log[0]
    -> ok   (a record a full year BEFORE the dispatch "proves" the dispatch ran)
```

The mirror case fails closed rather than open — in `prove_absence:1015–1019` an empty
`claimed_at` makes every attributable record contradicting — so the exposure is one-sided,
on the `executed` path.

Suggested contract: `adopt_one` should refuse a `started` or `settled` record with no
usable timestamp, or derive `started_at` from the `start_ref` record's own time (which
`record_time` already knows how to read).

## 5. A record with no timestamp is never "provably older" (Medium)

Same root cause as 4, live rather than adopted. `predates` deliberately treats an
undated record as "possibly relevant rather than dismissed" (`:576–577`), which is the
right default for the *absence* direction. On the `executed` direction it inverts: an
undated record is admitted as proof.

```
initialize run-A; authorize+start auth-A (repair-1/qa-1)   # started_at = now
workflow transition_log: [{node: "repair-1", status: "completed"}]   # no time field
reconcile auth-A executed observation_ref=transition_log[0]  -> ok, outcome "unknown"
```

`test_evidence_predating_the_execution_claim_is_refused` covers the dated case only.
Since the workflow's own `transition_log` entries do carry `at`, this is reachable mainly
through a hand-edited or foreign-shaped log — but the evidence path exists precisely to be
used after a crash, when logs are most likely to be truncated or partly written.

Suggested contract: on the `executed` path require a readable timestamp and require it to
be at or after `started_at`, rather than requiring only that it not be provably earlier.

## 6. `exhausted: false` for an obligation whose budget is unknown (Medium)

`adopt_one` (`:679`) defaults `budgets` to `{}` when the historical record omits it;
`budget_of` (`:229`) then returns None, `recorded_budget` (`:784`) skips those entries, and
`consumption` (`:1055–1057`) computes `remaining = None` and `exhausted = False`.

```
adopt_history: 3 charges against repair-1/qa-1, records omit "budgets"
consumption -> {"qa_node_id": "qa-1", "spent": 3, "budget": null,
                "remaining": null, "exhausted": false}
   (the declared max_attempts in workflow.json is 3 — it is fully spent)
```

`exhausted: false` under an unknown budget is a false negative, not an unknown. It also
removes the only brake on caller-declared bounds: `recorded_budget` pins a bound only once
one has been recorded, so after such an adoption every later `authorize` may name its own
`budgets` and the conflict check at `authorize:743–751` has nothing to compare it against.

The Codex driver is not exposed — `eligible_obligations`
(`codex/meta-skill/knowledge/flow-template.py:560–581`) derives budgets from the workflow's
declared `max_attempts` and compares against `spent`, not `exhausted`. The exposure is to
any caller that reads the field the helper publishes.

Suggested contract: report `exhausted: null` (or a distinct `budget_unknown: true`) when
the bound is unknown, and refuse to adopt a record whose `budgets` do not cover its
obligations.

## 7. The readiness gate fences the safety lock but not the ledger (Medium)

`validate_unattended_readiness.py:120–169` is careful and, as far as I can tell, correct
for `run_safety`: it blocks on the marker, on an unreadable marker, and on the lock — with
the right reasoning ("an absent marker is not evidence that nothing needed quarantining").

The same reasoning is not applied to repair accounting. The readiness validator never
mentions `repair-authorizations.json` or `repair-authorizations.lock` (only
`SAFETY_MARKER`/`SAFETY_LOCK` at `:21–22`). A run can therefore pass readiness with no
ledger at all, or with an abandoned ledger lock; the untrusted state surfaces later, as a
mid-run `blocked` from the first `authorize`, rather than at the gate that exists to catch
it. Plan §3 asks that durable authorization be confirmed before execution; the gate that
would confirm it up front does not look.

## 8. An abandoned ledger lock is a permanent, unclassified halt (Low)

`ledger_lock` (`:123`) is a `mkdir` lock with no owner, pid, or timestamp, and no recovery
path. A writer killed while holding it fences every future write:

```
mkdir .allforai/bootstrap/repair-authorizations.lock     # simulate a crashed writer
authorize   -> after 12.3s: blocked "ledger is locked; ... an abandoned writer must be
                              reconciled"   —   no "untrusted" key on the verdict
consumption -> 0.0s: status "ok"            (reads do not take the lock)
```

Two observations. First, the refusal carries no `untrusted` classifier while every other
refusal in the module does, so a caller routing on `untrusted` sees an unclassified
blocker. `test_an_abandoned_lock_reports_a_blocker_instead_of_removing_it` asserts the
blocker but not a classifier. Second, `consumption` reads without the lock and returns
`status: ok` with a full budget report while writes are fenced — a driver polling
consumption is told everything is fine. The lock-free read is safe against tearing
(`write_json:93` is an fsync'd atomic replace), so this is a reporting inconsistency, not
a torn read. Fail-closed on the write path is the right default; the gap is that the halt
is invisible to readiness (finding 7) and unclassified here.

## 9. Parity: the Claude ledger integration landed mid-audit — earlier note retracted (Info)

Recorded because it changed under me. When I first read the tree, `engine-core.js` defined
`LEDGER_VERDICT_SCHEMA`, `authorizationPrompt`, `authorizationId` and `ledgerReceiptError`
and exported them, but no call site existed in either engine file, and repair accounting
still ran through a `repairChargePrompt` that appended `workflow.json` `repair_routes` by
agent prompt. I had written that up as a parity gap. Re-checking before finalising, it is
no longer true: `repairChargePrompt` is gone from the tree entirely, and both
`engine-core.js` and `run-engine.workflow.js` now drive the helper end to end —
`consumption` and a fallback `initialize` at `engine-core.js:630-645` /
`run-engine.workflow.js:640-655`, `authorize` at `:742` / `:752`, `start` at `:761` /
`:771`, `settle` at `:830` / `:840`, each guarded by `ledgerReceiptError`. **The gap was
closed by the worker who owns the Claude engine while this audit was running; the finding
is withdrawn, and I did not review the new integration.**

One durable consequence for the findings above: neither host ever calls `adopt_history`.
Codex calls `initialize` only (`flow-template.py:486`); the Claude engine calls
`consumption` and `initialize`. So finding 1 is not reachable from an engine — it is
reachable on the *operator recovery path*, which is exactly the path the module's own
refusal text sends people down ("Recover it with `adopt_history`",
`repair_authorization.py:396-401`). That makes it a hole in the interface a human reaches
for after a blocked run: the moment budget guarantees matter most, and the moment the
temptation to hand the tool an agreeable file is highest.

---

## Checked and judged sound (approved assumptions, not bypasses)

These are the places where the dispatch asked me to distinguish an accepted trade-off from
a real hole, and I concluded the former.

- **Caller-asserted `complete` is by design, and is not on its own the defect.** ADR 0007
  requires evidence "asserted complete"; `prove_absence:985–991` says as much in its
  docstring, and the module compensates with the source-path binding (`:996`) and the
  contradiction scan (`:1015–1019`). Finding 2 is not that `complete` is trusted — it is
  that the *field* the assertion ranges over is unconstrained, which makes the assertion
  vacuous rather than merely trusting.
- **`run_safety.py` lock and publication behaviour is correct.** Verified by fixture: on
  success the lock is released (`:83` releases only when `locked and persisted`); a
  crashed or failed publication leaves the lock as a permanent fence; a lock already held
  makes `lock.mkdir()` raise before `locked` is set, so a second process never removes a
  fence it does not own. `validate_unattended_readiness.py:164–169` refuses on the lock,
  which is what makes the fence meaningful. Two consequences that look alarming are the
  intended fail-closed behaviour: a second, independent halt is refused and not recorded
  while a fence stands, and a corrupt marker fences permanently. My only note is advisory:
  the returned reason is identical for "already fenced", "corrupt marker", and "unknown
  node" (`:72–73`), and the marker's own `recovery` text (`:55–58`) never mentions the
  lock, so an operator holding only the marker cannot tell which state they are in.
- **Charging at the grant and never refunding.** `authorize:771–772` charges before execution,
  `settle:834` and `reconcile:895` both return `refunded: False` on every path, and
  `SETTLEABLE` (`:46`) keeps `settle` from resolving an uncertainty. This matches ADR 0006
  and I found no path around it.
- **All-or-none multi-obligation charging.** `authorize:755–765` refuses the whole dispatch
  when any obligation is exhausted, so a sibling with budget is never charged on behalf of
  an exhausted one. Matches ADR 0005; covered by tests and by my own fixture.
- **Idempotence under a non-durable dispatch id.** Codex generates
  `authorization_id = uuid.uuid4().hex` in memory (`flow-template.py:601`), not persisted
  before the call, which at first looks like a double-charge risk on retry after a crash.
  It is not: the retry's new id is refused by the `unresolved` guard (`:736–741`), so the
  outcome is a blocker requiring reconciliation — exactly what ADR 0006 asks for.
- **The plan binding is recorded, not enforced — and that is deliberate.**
  `test_the_binding_covers_declared_loops_not_moving_execution_state` explicitly asserts
  that `consumption` keeps reporting the binding captured at `initialize` after the
  workflow's loops change, so that dynamic expansion does not invalidate the ledger. I
  confirmed the consequence by fixture (raising `max_attempts` 3→99 and adding an
  undeclared `repair-9`/`qa-9` loop is accepted by `authorize` without comment, and
  `consumption` still reports the stale digest), and I am *not* filing it as a defect: it
  is the recorded trade-off. It is worth stating in the report only because the residual
  risk it leaves — a first-ever bound for an obligation being whatever the caller names —
  is what finding 6 turns into a live hole after `adopt_history`.
- **`settle`, `reconcile` and `consumption` do not check `run_id`** (only `authorize:710`
  and `start:806` do). Not filed: the ledger is per-project-root, and both hosts' id
  schemes make a cross-run id collision unreachable (`engine-core.js:395` embeds the run
  id; Codex uses uuid4). Noting it as an asymmetry a future change could turn into a hole.

## Reproduction

Fixture scripts live in the session scratchpad
(`.../scratchpad/{harness,r1,r2,r3,r4,r5,r6,r6b,r7,r8}.py`) and are not part of the
repository. Each builds a temporary project with `.allforai/bootstrap/workflow.json` and
drives the helper through its CLI (`python3 repair_authorization.py <root>` with a JSON
request on stdin), which is the same entry point both hosts use. They can be recreated
from the transcripts above; none of them writes anywhere but its own tempdir.
