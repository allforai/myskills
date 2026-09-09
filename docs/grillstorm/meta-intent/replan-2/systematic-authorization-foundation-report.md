# Repair-authorization foundation

Workstream 3 of the systematic remediation plan, foundation only: the canonical
repair-authorization API and its focused tests. No host engine, validator, gate, or
orchestrator template was edited, and nothing here is integrated into either host.

Incorporates all nine coordinator refinements received before API freeze, and a
follow-up **evidence-trust audit** that found and fixed three ways trust could be
asserted rather than proved. See "Evidence-trust audit" below for what was wrong, what
changed, and the precise consumer impact. The call-level API is unchanged; the evidence
payloads `reconcile` and `adopt_history` accept are strictly narrower.

## Deliverables

| File | Status |
|---|---|
| `claude/meta-skill/scripts/orchestrator/repair_authorization.py` | new |
| `claude/meta-skill/tests/unit/test_repair_authorization.py` | new, 108 tests |

## What it is

A repair authorization is a uniquely identified grant to perform one repair attempt
against named QA obligations. It is charged when the grant is durably recorded — not
when the repair succeeds — and recording the same grant again is not another attempt
(CONTEXT.md, ADR 0006).

The ledger is its own document, `.allforai/bootstrap/repair-authorizations.json`,
guarded by a `repair-authorizations.lock` mkdir lock. This module never writes
`workflow.json`. Today's Codex path (`charge_repair_attempts` in
`codex/meta-skill/knowledge/flow-template.py`) read-modify-writes the whole workflow
document to append a `repair_routes` entry, so an unrelated concurrent workflow writer
and the budget ledger race for the same file and either can lose the other's write.
Separating the ledger removes that race by construction; a test asserts the workflow
document is byte-identical after a grant, a start, a settlement, and a read.

## State machine

```
authorize ──► authorized ──► start ──► started ──► settle ──► settled
              (charged,              (the one-time          (outcome
               no execution)          launch claim)          recorded)
                                            └── reconcile (evidence) ──► settled
```

`authorize` is a charge, never permission to run: every authorize verdict carries
`execution_allowed: false`. Only the **first** successful `start` returns
`execution_allowed: true`; a replayed start, a resumed driver, and a second worker all
get `false`. A settled attempt is never restartable — re-execution needs a new
authorization and a new charge.

`unresolved` = state in `{authorized, started}`. An unresolved grant blocks a further
grant **for its own obligations only**; independent repair loops grant and start in
parallel unaffected, and reading the ledger while another repair is in flight is normal,
not an error.

## API

```python
new_authorization_id() -> str                       # durable unique dispatch id (uuid4 hex)
initialize(root, run_id) -> verdict                 # verifies the workflow on disk itself
adopt_history(root, run_id, evidence) -> verdict    # verified, attributable recovery
authorize(root, request) -> verdict                 # atomic, locked, all-or-none
start(root, run_id, authorization_id) -> verdict    # one-time durable launch claim
settle(root, authorization_id, outcome, evidence=None) -> verdict
reconcile(root, authorization_id, determination, evidence) -> verdict
consumption(root, repair_node_id=None) -> verdict
session(root, request) -> verdict                   # operation dispatch; the CLI entry
```

Ledger entry:

```json
{"authorization_id": "...", "repair_node_id": "...",
 "obligations": ["qa-a", "qa-b"], "charged": {"qa-a": 1, "qa-b": 2},
 "budgets": {"qa-a": 3, "qa-b": 3}, "state": "authorized|started|settled",
 "outcome": null, "granted_at": "...", "started_at": null, "settled_at": null,
 "request_digest": "sha256(...)", "provenance": {}}
```

### Verdict vocabulary

Every verdict carries `status` and `reason`; every refusal also carries `untrusted`.

| status | meaning |
|---|---|
| `authorized` | charge durably recorded; `execution_allowed: false` |
| `started` | launch claim; `execution_allowed` true only on the first |
| `replayed` | same id, identical payload — the same attempt, nothing further charged |
| `payload_conflict` | same id, different obligations or bounds; nothing charged |
| `budget_exhausted` | at least one obligation is at its bound; nothing charged |
| `blocked` | untrusted state |
| `settled` / `ok` | bookkeeping success |
| `invalid` | malformed request |

`untrusted` values: `missing_workflow`, `unreadable_workflow`, `prior_execution`,
`existing_run`, `missing_ledger`, `unreadable_ledger`, `run_identity_mismatch`,
`unresolved_authorization`, `unknown_authorization`, `already_settled`,
`budget_conflict`, `unverifiable_evidence`, `incomplete_history`, `ambiguous_history`,
and — added by the audit — `unclaimed_execution`, `undetermined_execution`,
`unattributable_evidence`.

## CLI

Same contract for both hosts — Codex calls it directly, Claude runs it as an
agent-executed command through its delegated filesystem:

```
python3 claude/meta-skill/scripts/orchestrator/repair_authorization.py <project_root> < request.json
```

Verdict JSON on stdout. Exit 0 for `ok | authorized | replayed | started | settled`;
exit 1 for `blocked | budget_exhausted | payload_conflict | invalid`. A test asserts the
CLI and the Python API reach the same verdict for the same state, and that every refusal
exits non-zero carrying a typed `untrusted` reason.

## Contracts enforced

1. **Charge on grant, never on success.** `settle` and `reconcile` both report
   `refunded: false`; a failed or aborted attempt is still an attempt.
   `settle` may only assert what the ledger already proves: a never-claimed grant can
   only be `aborted`, a claimed one only `delivered`/`failed`. `unknown` is not
   settleable at all — it is what `reconcile` records against evidence.
2. **Grant and launch are separate, and the launch is claimed once.** Nothing executes
   on an authorize verdict. A crash between charge and claim leaves an `authorized`
   grant that blocks rather than silently re-running.
3. **Per-obligation budgets, all-or-none.** One dispatch answering several obligations
   charges one attempt of each under a single lock. If any obligation is at its bound
   the whole grant is refused and nothing is charged; the driver re-requests with only
   the eligible obligations. An exhausted obligation is refused, never accepted.
4. **Idempotent replay with payload consistency.** The digest covers `run_id`,
   `repair_node_id`, sorted obligations and budgets — not provenance or timestamps, so
   an ordinary retry is recognised as the same dispatch. A reused id with a changed
   payload is `payload_conflict`, not a replay.
5. **Durable writes.** The temporary file is fsync'd before the atomic replace and the
   parent directory is fsync'd after; an atomic replace alone orders renames but does
   not get bytes to disk. A held or stale lock returns an actionable `blocked` and is
   **never removed on the owner's behalf**.
6. **A new run is verified, not asserted.** `initialize` takes no caller proof. It reads
   `.allforai/bootstrap/workflow.json` and records
   `{transition_log, repair_routes, completed}`; any non-zero count is `prior_execution`
   and must go through `adopt_history`. The recorded proof is
   `{kind: verified_untouched_workflow, source_path, source_digest, observed,
   verified_at}`. A different `run_id` over an existing ledger is refused outright —
   a caller boolean is not user-confirmation evidence, and no proof format was invented
   for a confirmation nothing currently records.
7. **Run binding covers declared loops only.** `loop_binding` digests
   `(repair_node_id, qa_node_ids, max_attempts)` — not completion or transition state,
   which move every wave. Dynamic expansion that adds a loop changes the digest without
   invalidating the ledger: a newly declared obligation simply has no history to lose,
   and it is never a reason to reset.
8. **Historical recovery is verified against the real document.** `adopt_history`
   requires `source_path` + `source_digest` that match the file on disk, `complete:
   true`, and per record a `source_ref` of the form `repair_routes[i]` resolving to a
   real entry whose `repair_node_id`/`qa_node_id` match the record. Every entry must be
   claimed exactly once — an unclaimed index is `incomplete_history`. A source with no
   readable `repair_routes` is `unverifiable_evidence`.
   **A repair_routes entry proves a charge and nothing else**, so a `started` claim needs
   a `start_ref` and a `settled` claim a `settlement_ref`, each resolving to a record of
   the same verified source that is attributable to that repair node; a settled one must
   be terminal, and the outcome is **derived** from its status
   (`completed`→`delivered`, `failed`→`failed`), never caller-declared. A declared
   outcome contradicting the evidence is refused. Provenance is preserved; nothing is
   refunded.
9. **Reconciliation needs evidence about *this* attempt.** A matching digest proves only
   that a file is the file it claims to be. `executed` additionally requires an
   `observation_ref` resolving to a record attributable to this authorization (its
   `authorization_id`, or its repair node) and not predating the execution claim.
   `not_executed` requires `absence_of` naming a log asserted `complete: true`, in **this
   run's own bound execution record**, containing nothing attributable to the attempt at
   or after the claim — any contradicting record refuses. Both determinations settle
   without refund and record the determination, basis, path, digest and attribution.
10. **`consumption` is the canonical read.** Per obligation: `spent`, `budget`,
    `remaining`, `exhausted`, and the unresolved authorization ids; plus a run-level
    `unresolved` list carrying each id's `state`.

## Evidence-trust audit

A follow-up audit asked whether this module *validates* evidence or merely *accepts* it.
Three places asserted trust rather than proving it. All three are fixed, with executable
negative tests for each. None of the fixes refunds anything.

### D1 — `settle` was `reconcile` with the evidence gate removed

`settle(id, "unknown")` on a `started` entry set `state: settled` with **no evidence at
all**. That cleared the `unresolved_authorization` blocker and let the next authorization
run work that may already have run — precisely the outcome ADR 0006 forbids. The entire
`reconcile` evidence path was optional; a caller could route around it with one call.

**Fix.** The outcome a settlement may assert is now bounded by the state the ledger
itself proves:

| state | what the ledger proves | settleable outcomes |
|---|---|---|
| `authorized` | execution was never claimed | `aborted` only |
| `started` | execution was claimed | `delivered`, `failed` only |

`unknown` is refused as `invalid` from every state — it is a reconciliation result, not a
settlement. `aborted` on a `started` entry is an assertion about work that may already
have happened, so it is refused as `undetermined_execution` and must go through
`reconcile`. A definite outcome on a never-started grant is refused as
`unclaimed_execution`.

### D2 — `adopt_history` read execution out of a charge

A legacy `repair_routes` entry records exactly one fact: an attempt was charged. It has
no settlement field. Yet a caller-declared `state: "settled"` was accepted and the
outcome silently defaulted to `unknown`, turning an unknown legacy execution into a
resolved, non-blocking entry. A legacy run resumed as though its attempts were known to
be finished.

**Fix.** A claimed state must itself be attributable to the verified source.
`authorized` is always allowed — the route does prove the charge. `started` requires a
`start_ref`, `settled` a `settlement_ref`, each resolving to a record of the same
verified source attributable to that repair node; a settled one must be terminal, and its
status **derives** the outcome. A declared outcome that contradicts the evidence is
refused. Unreferenced claims are refused actionably, telling the caller to supply the
reference or adopt the record as `authorized` — which is accepted, and blocks until
reconciled.

### D3 — `reconcile` proved neither identity nor determination

`source_path` + a matching digest + a freeform `basis` accepted **any** project file and
**any** prose. Nothing tied the evidence to the authorization, and nothing distinguished
`executed` from `not_executed`. A genuine, correctly hashed report about entirely
different work reconciled an attempt.

**Fix.** The two determinations need opposite proofs, and both are now checked:

- `executed` — `observation_ref` must resolve to a record of the verified source that is
  attributable to this authorization (matching `authorization_id`, or the entry's
  `repair_node_id`) and does not predate the execution claim.
- `not_executed` — an absence is only meaningful against a log known to be whole *and*
  known to be the right log. It requires `absence_of` naming a field, `complete: true`,
  and the source to be **this run's own bound execution record** (from the ledger's
  `origin.proof.source_path`). Any record attributable to the attempt at or after the
  claim contradicts the determination and refuses.

The second condition matters as much as the first: without it, the emptiest unrelated
file would "prove" that nothing happened, since no unrelated document contains a trace of
this attempt either way.

### Consumer impact (call-level API unchanged)

No operation name, function signature, status value, or ledger field changed. What
narrowed is which evidence payloads are accepted:

| consumer behavior | before | now |
|---|---|---|
| `settle(id, "unknown")` after a crash | resolved it | `invalid` — call `reconcile` |
| `settle(id, "aborted")` on a started grant | resolved it | `blocked: undetermined_execution` |
| `settle(id, "delivered")` before `start` | resolved it | `blocked: unclaimed_execution` |
| `reconcile` with path + digest + basis | accepted | needs `observation_ref` or `absence_of`+`complete` |
| `adopt_history` record `state: "settled"` | accepted, outcome `unknown` | needs `settlement_ref`; outcome derived |
| adopting a bare `repair_routes` ledger | resolved entries | `authorized` entries that block until reconciled |

Three new `untrusted` values: `unclaimed_execution`, `undetermined_execution`,
`unattributable_evidence`.

## Verification

```
python3 -m pytest claude/meta-skill/tests/unit/test_repair_authorization.py -q
```

→ **108 passed**.

Isolation (both collection orders, per the coordinator's "focused tests only"):

```
python3 -m pytest claude/meta-skill/tests/unit/test_repair_authorization.py \
                 claude/meta-skill/tests/unit/test_validate_bootstrap.py \
                 claude/meta-skill/tests/unit/test_check_artifacts.py -q
```

→ **200 passed**, and **200 passed** with the order reversed.

The suite loads the module through `..module_isolation.load`, the repo's authoritative
isolation loader (owned by `shared/scripts/orchestrator/_module_isolation.py`), so a
combined collection cannot bind another tree's same-named module here. This is a
dependency on the parallel test-isolation workstream's helper.

A combined `claude/meta-skill/tests/unit` run was **999 passed** at 01:12, before this
refinement round. Combined suites are the coordinator's to run once sources settle.

### Common contract scenarios covered

From `claude/meta-skill/tests/fixtures/execution-contract-scenarios.json`, the six
scenarios that are this helper's business (the rest — safety halt, closure, admission,
overlapping roles, same-named modules — belong to the engines and validators):

| scenario | test |
|---|---|
| `shared_repair_asymmetric_budget` | `test_shared_repair_asymmetric_budget` |
| `duplicate_authorization` | `test_duplicate_authorization` |
| `conflicting_authorization_replay` | `test_conflicting_authorization_replay` |
| `partial_shared_charge_crash` | `test_partial_shared_charge_crash` |
| `unknown_execution_after_crash` | `test_unknown_execution_after_crash` |
| `missing_historical_ledger` | `test_missing_historical_ledger` |

Each **drives the implementation and compares the observed behavior** to the fixture's
`expect` values. The earlier version of these tests asserted fixture values against
themselves (`assert expect['automatic_refund'] is False`), which tested the JSON file
rather than the module; those tautologies are gone. Where the fixture says
`automatic_refund: false`, the test now re-reads the spend after the crash path and
asserts the observed refund flag equals it; where it says `final_acceptance: false`, the
test observes whether the helper actually issues the grant.

### Fault and concurrency coverage

- Concurrent distinct dispatches against a budget of 1 across 8 processes: exactly one
  `authorized`.
- Concurrent replays of one dispatch id across 8 processes: exactly one `authorized`,
  the rest `replayed`, all `execution_allowed: false`, spend exactly 1.
- Concurrent `start` of one authorization across 8 processes: `execution_allowed` true
  exactly once.
- 8 concurrent multi-obligation grants: ledger stays readable, every entry complete.
- Truncated, wrong-shape, wrong-version ledgers; entries with a bad or missing `state`,
  `charged`, `obligations`, or identity; duplicated entries — all blocked.
- Abandoned lock: actionable blocker, and the lock is still there afterwards.
- Missing / unreadable / already-executed workflow at `initialize`.
- Evidence with a wrong digest, a missing digest, a path escaping the project, an
  unresolvable `source_ref`, a doubly-claimed index, a mismatched node, a dropped record.
- `workflow.json` byte-identical across a grant, a start, a settlement, and a read.
- fsync is exercised (temp file + parent directory) on every ledger write.
- **Evidence-trust negatives**: `settle(unknown)` refused and the blocker still standing
  afterwards; every refused shortcut (`unknown`, `aborted`, evidence-less reconcile,
  reference-less reconcile) leaving reauthorization blocked and the spend unchanged; a
  forged adopted outcome contradicting its own cited record; a non-terminal
  `settlement_ref`; execution evidence about another node; an unrelated file with a
  genuine digest failing both the `executed` and the `not_executed` direction; evidence
  predating the execution claim; a log that records the run failing to prove it did not
  run; and no path through `settle` ever producing outcome `unknown`.

### Mutation check

Three defects were injected to confirm the suite is not vacuous; each was caught, then
reverted:

| injected defect | tests failed |
|---|---|
| replayed `start` returns `execution_allowed: true` | 2 |
| missing ledger read as zero consumption | 19 |
| `reconcile not_executed` refunds the attempt | 1 |
| `settle` accepts any outcome in any state (the D1 bypass) | 6 |
| `adopt_history` infers `settled`/`unknown` from a bare charge (D2) | 8 |
| `reconcile` skips the attribution check (D3) | 3 |
| `not_executed` ignores contradicting records | 1 |
| absence accepted from any document | 2 |

## Boundaries

- This is API scope, not integration. No host consumes this ledger yet; the Claude
  engine still reads `repair_attempts` and Codex still appends `repair_routes`.
- **No cross-host parity is claimed or demonstrated.** These are single-module contract
  tests, not host acceptance. Per ADR 0004 both hosts must be checked against the same
  contract scenarios on the real hosts; simulated tests do not replace that.
- `initialize` proves a new run from the workflow document only. A run whose history
  lives somewhere this module cannot read is `prior_execution`, and recovering it is the
  caller's evidence to produce.
- No mechanism exists here for user-confirmed replacement of an existing run's ledger.
  That was deliberately not invented: it is refused with an actionable blocker until a
  real recorded user-decision source exists to verify against.
- Completeness of an absence log remains the **caller's assertion** (`complete: true`),
  recorded as provenance. The module cannot prove a log is whole; what it does guarantee
  is that the log is this run's own, and that no record contradicting the determination
  is ignored. A caller that asserts completeness falsely is making a false statement of
  record, not exploiting a gap in a check.
