# Failure Proportionality

Bound how far each failure mode expands into specs, tasks, code, and proof. Every mode is still
examined. This is an expansion budget, not permission to skip analysis.

## Classify before expanding

Record one entry per failure mode per outcome in `reviews/failure-classification.json`:

```json
{
  "schema_version": 1,
  "records": [
    {
      "mode": "timeout",
      "outcome": "requirement or global outcome ID",
      "damage": "reenterable|durable|unknown",
      "reentry_proof": "re-entry point and how state converges on re-run",
      "frequency": "routine|rare",
      "frequency_basis": "structural|external-sla|no-recorded-occurrence",
      "frequency_basis_evidence": "the constraint, declared SLA, or inspected history source",
      "expansion": "full|guard-only|none",
      "note": "one line; the whole record when expansion is none"
    }
  ]
}
```

`reenterable` means the failure leaves no durable trace and re-running restores a correct state.
`durable` means the failure can leave persistent wrong state: committed partial writes, an emitted
external side effect, moved money, a granted permission, a published message, or corrupt stored
rows.

`routine` means the mode is expected in normal operation. `rare` means it is credibly infrequent
for an evidenced reason.

## Expansion table

`expansion` is looked up, never chosen.

| | `reenterable` | `durable` |
|---|---|---|
| `routine` | `guard-only` | `full` |
| `rare` | `none` | `guard-only` |

- `full`: state transitions, rollback, recovery ordering, test seam, runtime observation, and
  completion evidence.
- `guard-only`: exactly one defense plus proof it holds. For `durable`, a transaction boundary,
  idempotency key, uniqueness constraint, or precondition check. For `reenterable routine`, proof
  that the re-entry path exists and is exercised. No branch tree, no recovery orchestration, no
  per-mode spec section.
- `none`: one ledger line. No requirement, spec section, task, test, or code branch.

`rare` with `reenterable` is the only exempt cell.

## Locks

1. Frequency never rewrites damage. `rare` does not convert `durable` into `reenterable`. Low
   probability does not undo an irreversible effect; it only shrinks the defense to one guard.
2. `rare` requires an admissible basis and its evidence: `structural` when a constraint, type, or
   invariant makes the mode unreachable; `external-sla` when an external dependency declares the
   guarantee; `no-recorded-occurrence` when named inspectable history shows none. A missing,
   unlisted, or unevidenced basis falls back to `routine`. "It basically never happens" is not a
   basis.
3. Re-entrancy is proved, not asserted. Missing or placeholder `reentry_proof` falls back to
   `durable`.

`damage: unknown` counts as `durable`. Investigate inside the same bounded gate; if it stays
unknown, defer that one mode without blocking the rest of the graph.

The orchestrator persists the reverse Grill's `failure_classification` array and the outcomes it
checked to `reviews/failure-classification.json`. The orchestrator, not the Grill subagent, runs
the validator before the closure gate:

```bash
python3 <skill>/scripts/validate_failure_classification.py reviews/failure-classification.json
```

It applies the fallbacks and the table deterministically, checks that every mode was classified
for every checked outcome, and rejects a self-reported `expansion` that disagrees with the
lookup. A failing run blocks the closure gate. A validator error is a Grill repair that reruns
the reverse Grill for the affected outcomes, not a prose override. The validator makes no
probability judgment of its own.

## Lens closure

A lens counts as applied to an outcome when every mode is classified, not when every mode is
designed. `expansion: none` and a proved `guard-only` are closed states.

## Issue ordering

Every issue from any lens carries `blast_radius`: `contract` when being wrong changes a
cross-module contract or acceptance, `module` when it changes one module's internals, `local`
when it changes a single call site. `local` requires naming that single call site; a `local`
claim that cannot name it falls back to `module`. Dependency order governs. Among ready issues,
order by `blast_radius` — `contract`, then `module`, then `local`. Record `local` issues in
`reviews/spec-grill.md` or `reviews/task-grill.md` without expanding them.

No lens outside exceptional behavior gains a skip permission. Ordering defers expansion, never
examination.
