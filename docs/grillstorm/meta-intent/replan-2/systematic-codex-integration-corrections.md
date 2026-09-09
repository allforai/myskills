# Codex host integration — corrections after independent review

Answers `systematic-codex-independent-review.md`. Owned files only:
`codex/meta-skill/knowledge/flow-template.py`, `codex/meta-skill/test_flow.py`,
`codex/meta-skill/knowledge/orchestrator-template.md`, and this report. No production
validator, no Claude engine file, and no foundation helper was edited;
`repair_authorization.py` and `run_safety.py` are still consumed exactly as shipped.

## Verification

```
python3 -m pytest codex/meta-skill/test_flow.py -q
```

→ **124 passed** (117 before, 7 new). Every previously passing test still passes: no
existing expectation was changed, weakened, or deleted by these corrections. The new tests
drive the real selection or the real `main()` against the canonical ledger and the
canonical quarantine helper in a temporary project; no paid CLI call and no live model
launch. The review's own repro file was re-run against the fixed driver — findings 1, 2
and 3 now pass, finding 4 is unchanged on purpose (below), and its finding-5a probe now
fails because it asserted the discarded settle verdict this correction stopped discarding.

## 1. A node's blockers hold in every role it plays (review finding 1, High)

`_pending_state` tested repair-node membership before every blocker, so a node that
repairs loop A while being an obligation of loop B was dispatched as a repairer even when
the driver had already decided it was blocked. That dispatch puts the node in front of the
executor with its own QA report among its exit artifacts.

Blocked-ness is now decided first. A node that is routed to its own repair, waiting as a
closure, under an unbounded loop, or exhausted is not selected in any other role. The
repair role is reached only by a node nothing else blocks. Prior behaviour for graphs
without role overlap is unchanged, node for node: the blockers that used to be skipped for
a `complete` node are still skipped for it, with the one deliberate exception in §2.

## 2. Its own QA attempt is what satisfies an obligation (review finding 2, High)

The exhausted set skipped any obligation whose artifacts read ready
(`complete.get(qa_node_id)`). Completeness is measured from files on disk, so the dispatch
in §1 discharged the very obligation it was blocked for by writing that file, and the run
reached `done: true` with a spent, never-repaired obligation — and then dispatched that
loop's repair node again with no authorization, because by then it had no routed
obligation to charge.

Now, in `exhausted_obligation_pairs`, an obligation whose **latest recorded attempt
failed** and whose budget is spent stays exhausted however passed its report reads. The
exit artifact of a QA node is a file; the attempt the driver recorded is evidence. A
delivered repair is still not exhausted — its QA rerun judges the delivery and is not
another repair attempt — and an obligation whose latest attempt did not fail is still free
to run. The same pairs give `dead_loop_repairs`: a repair node with an exhausted
obligation and no funded routed obligation is blocked too, so no repair dispatch runs
unpaid after its budget is spent. A shared repair still runs for a sibling that has
budget, which the existing asymmetric-budget test continues to prove.

Residual, stated rather than hidden: the blocker keys on the node's latest transition, so a
`completed` entry forged directly into `workflow.json` for a node the driver never
dispatched would still clear it. The driver cannot produce that entry any more — it will
not dispatch the node — and defending the transition log against a hand-edited workflow is
the same trust boundary `_keep_last_transition` and the worker-evidence tests already own.

## 3. A halt is fenced whether or not the quarantine could be published (review finding 3, Medium)

`quarantine_outputs` returned `False` when `run_safety.py` was missing and the driver
reported it — but nothing durable recorded the halt, so the only fence was the warnings
file a worker writes and a Run Policy a user can edit. Clearing either read the quarantined
outputs back as a completed node on the next start.

`fence_safety_halt` now leaves `safety-quarantine.lock` before `quarantine_outputs`
returns, for exactly the meaning `run_safety.py` gives it: a quarantine was attempted and
the absence of a marker is not proof that none was required. `safety_halted` and
`validate_unattended_readiness.py` already refuse that path. The canonical marker is still
never invented, `quarantine_persisted` still reports only what the helper confirmed, and
the halt payload now also carries `halt_fenced`.

## 4. Uncertain execution stays a global refusal (review finding 4 — **not** adopted)

The review proposed demoting an unauthorizable repair dispatch to a blocked node so
independent branches could drain first. That is declined, per the coordinator's crash
policy: an authorization with no recorded outcome may already have edited the tree, and no
branch may proceed on the assumption that it did not.

What changed is *when* and *how* it is reported, not how much it stops. The refusal is now
raised in `_pending_state` from `unresolved_authorizations` before anything is dispatched,
rather than being discovered whenever the affected repair node happened to be selected, and
the two stops are no longer one list:

| stop | reported as | released by |
|---|---|---|
| report-backed QA blocking | `exhausted_obligations`, `unbounded_repair_loops` | nothing — the obligation was never satisfied and the run says so |
| uncertain execution | `unresolved_repair_authorizations` + `uncertain_execution` | `reconcile` against attributable evidence |

The first is a verdict this run recorded on complete evidence. The second is a question
about an execution nobody watched end. Merging them would let a reader answer a
reconciliation with more QA.

## 5. Receipts are checked, and an unsettled attempt is not a completion (review finding 5)

- `receipt_for` requires every `authorize` / `start` / `settle` verdict to name the
  authorization it was asked about (and the run, where the helper echoes it). A verdict is
  trusted for its accounting, not for its addressing; a receipt about another attempt is
  not an answer about this one. A mismatched `start` refuses execution and leaves the
  grant unresolved, which is the correct fail-closed end.
- `settle_repair_dispatch` returns whether the ledger confirmed the outcome, and the
  settlement now happens **before** the node can be recorded completed. An unconfirmed
  settlement records the attempt `failed` with the reason, prints
  `unresolved_repair_authorizations`, and stops the run: the ledger is the record of what a
  dispatch did, and accepting work whose authorization stays open would make that record
  decorative. The attempt is left unresolved for `reconcile`, exactly as a crash is.
- Not adopted from finding 5c: settling a 127 as `aborted`. The grant is already `started`
  by then, `SETTLEABLE` allows only `delivered`/`failed` from that state, and the charge is
  identical — changing it would mean re-ordering `start` around the executor for a
  distinction that buys no decision.
- Finding 5d (two artifact-gate passes per iteration) is left alone deliberately: it is a
  cost, not a wrong answer, and threading a precomputed `complete` map into
  `qa_nodes_routed_to` would make the charge depend on a map computed before the selection
  it charges for. Recorded as a known cost rather than hidden.

## 6. Tests (7 new, all behavioural)

| test | contract |
|---|---|
| `test_a_node_blocked_as_an_obligation_is_not_dispatched_in_its_repair_role` | §1: blocked in one role, blocked in all of them |
| `test_a_repair_role_dispatch_never_discharges_the_nodes_own_exhausted_obligation` | §2 end-to-end through `main()`: no `done: true`, no further dispatch, no further charge |
| `test_an_exhausted_obligation_stays_blocked_when_its_report_is_made_to_look_ready` | §2: a ready artifact is not a QA attempt; the dead loop's repair node is blocked with it |
| `test_a_halt_whose_quarantine_cannot_be_published_still_fences_the_next_start` | §3: no marker invented, lock left, next start refuses, clearing the warnings file releases nothing |
| `test_an_unresolved_authorization_refuses_the_whole_run_before_the_first_dispatch` | §4: nothing executes, an untouched branch is included, reported as reconciliation and not as a spent budget, no refund |
| `test_an_unconfirmed_settlement_stops_the_run_before_the_node_is_completed` | §5: recorded `failed` with the reason, grant left `started`, run stops |
| `test_a_receipt_for_another_authorization_is_not_permission_to_execute` | §5: a foreign receipt authorizes nothing and settles nothing |

`overlap_project` is the new fixture for the two-loop role overlap. It is the shape
`validate_bootstrap.py` permits — it refuses only a repair node that is its own loop's QA
or closure node — which is why the overlap has to be handled rather than banned.

## 7. Remaining limits

- **Cross-host parity is still not demonstrated here.** These are Codex driver tests. The
  six decisions above are the business decisions ADR 0004 requires both hosts to reach;
  they were sent to the coordinator for the Claude owner, and equivalence has to be proved
  on the real hosts against the shared contract scenarios, not by these tests.
- **The shared scenario fixtures do not yet carry the role-overlap case.**
  `claude/meta-skill/tests/fixtures/execution-contract-scenarios.json` is not mine to edit;
  until a scenario states the expected decision for a node that repairs one loop while
  owing another, the Codex and Claude tests for it are written independently rather than
  against one fixture.
- **`_LEDGER_READS` is still unbounded** for the life of a driver process, one entry per
  distinct ledger state. Unchanged and still not worth managing at this size.
- **The exhausted blocker trusts the transition log** (see §2 residual).
