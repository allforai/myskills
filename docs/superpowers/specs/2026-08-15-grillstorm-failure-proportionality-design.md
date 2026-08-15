# Grillstorm Failure Proportionality And Issue Ordering

## Goal

Stop Grillstorm from expanding exceptional-behavior analysis without a bound.

The observed failure is a design that keeps growing: exception handling ends up larger than the
core behavior it protects, every low-probability scenario acquires its own branch, spec text, task,
and test, and the resulting artifact is too large to reason about. The cost is not source lines. It
is concepts, states, branches, and reviewer attention spent on scenarios that cannot damage
anything.

The fix is a proportionality rule with a hard admission test, not a general permission to skip
analysis. Every failure mode is still examined. What changes is how far each one is allowed to
expand into specs, tasks, code, and proof.

## Root Cause

Two mechanisms combine into a combinatorial explosion.

`prompts/spec-reverse-grill.md` and `prompts/task-reverse-grill.md` define the exceptional-behavior
lens as a fixed enumeration of roughly thirteen modes: invalid input, partial failure, timeout,
cancellation, retry, idempotency, concurrency/race, stale data, external outage, permission denial,
cleanup, degraded operation, and recovery.

`references/spec-closure-and-abstraction.md` and `references/task-documents.md` then close only when
every lens has been applied to every global outcome with no unresolved issue. Applied is currently
read as designed. Thirteen modes multiplied by every outcome, each demanding a resolution, produces
the unbounded expansion.

`references/orientation-and-intent.md` already defines purpose-complete minimalism, but it governs
concepts and abstractions, not failure-mode enumeration. It explicitly instructs preservation of
applicable failure, degraded, and recovery behavior. `applicable` is the only existing brake and it
carries no test.

Nothing in the current skill lets a reviewer conclude that a given failure mode does not deserve
expansion. That conclusion needs to exist, and it needs to be admissible at the closure gate.

## The Rule

Every failure mode is classified before it is expanded. The classification is the lens output.

```json
{
  "mode": "timeout|partial-failure|race|stale-data|invalid-input|...",
  "outcome": "global outcome or requirement ID this mode was examined against",
  "damage": "reenterable|durable|unknown",
  "reentry_proof": "entry point plus how state converges on re-run",
  "frequency": "routine|rare",
  "frequency_basis": "structural|external-sla|no-recorded-occurrence",
  "frequency_basis_evidence": "the constraint, declared SLA, or inspected history source",
  "expansion": "full|guard-only|none",
  "note": "one line; the whole record for expansion: none"
}
```

### Two axes, not equal in weight

`damage` decides whether a defense is required at all. `frequency` decides only how far that
defense expands. Frequency never decides whether damage exists.

- `reenterable`: a failure leaves no durable trace. Re-running restores a correct state.
- `durable`: a failure can leave persistent wrong state — partial writes committed, an external
  side effect already emitted, money moved, a permission granted, a message published, corrupt rows
  landed in storage.
- `routine`: the mode is expected in normal operation.
- `rare`: the mode is credibly infrequent, with an evidence-based reason.

### Expansion table

`expansion` is not chosen. It is looked up.

| | `reenterable` | `durable` |
|---|---|---|
| `routine` | `guard-only` | `full` |
| `rare` | `none` | `guard-only` |

- `full`: complete treatment — state transitions, rollback, recovery ordering, test seam, runtime
  observation, completion evidence.
- `guard-only`: exactly one defense, plus proof it holds. For `durable` this is a transaction
  boundary, idempotency key, uniqueness constraint, or precondition check. For `reenterable
  routine` it is proof that the re-entry path genuinely exists and is exercised. No branch tree, no
  recovery orchestration, no per-mode spec section.
- `none`: one line in the review ledger. No requirement, no spec section, no task, no test, no
  code branch.

`rare` × `reenterable` is the only cell exempt from expansion. That cell is the entire source of the
complexity being removed.

### The three locks

Without these the table is a rationalization device, because the cheapest cell is reachable by
assertion.

1. **Frequency cannot rewrite damage.** `rare` never converts `durable` into `reenterable`. The
   `rare durable` cell always carries a defense. Low probability does not undo an irreversible
   effect; it only means the defense can be one guard instead of a designed recovery path.
2. **`rare` requires an evidence-based basis.** Only three bases are admissible:
   - `structural`: a constraint, type, or invariant makes the mode unreachable;
   - `external-sla`: a declared guarantee from an external dependency;
   - `no-recorded-occurrence`: no occurrence in inspectable history, with the inspected source
     named.
   A missing basis, a basis outside the enumeration, or a basis with no
   `frequency_basis_evidence` falls back to `routine`. Intuition that something "basically never
   happens" is not a basis.
3. **Re-entrancy is proved, not asserted.** `reenterable` requires `reentry_proof` naming the
   re-entry point and how state converges after re-run. Empty or placeholder proof falls back to
   `durable`.

`damage: unknown` is treated as `durable`. Investigate inside the same bounded gate; if it remains
unknown, defer that single mode without blocking the rest of the graph.

## Closure Semantics

The load-bearing change: **a lens counts as applied to an outcome when every mode has been
classified, not when every mode has been designed.**

An `expansion: none` record is a valid closed state. So is `guard-only` with its single defense
proved. Closure gates must accept both.

## Issue Ordering Across All Lenses

The proportionality rule above is specific to exceptional behavior, where the discriminator is
evidence-based. Other lenses get ordering only, never a skip permission.

Every issue produced by any lens carries `blast_radius`, one of `contract`, `module`, or `local` —
whether being wrong changes a cross-module contract or acceptance, changes one module's internals,
or changes a single call site. The orchestrator consumes issues in that order. `local` issues are
recorded in the existing review ledger without expansion into specs or tasks.

No lens outside exceptional behavior gains permission to skip examination. A general "this is a
secondary concern, so I did not look" permission would immediately be used to skip primary
concerns, which is the same failure mode as an acceptance report claiming coverage it never
achieved.

## Enforcement

The three locks are checked by a program, not by prose the same agent grades itself against. Table
lookup and required-field checks are deterministic; judgment stays with the model, arithmetic goes
to code.

New `scripts/validate_failure_classification.py` reads `reviews/failure-classification.json` and
enforces:

1. `expansion` equals the table lookup of `(damage, frequency)` after all fallbacks are applied.
   A self-reported `expansion` that disagrees is an error, not a preference.
2. `frequency: rare` with a missing basis, or a basis outside the enumeration, falls back to
   `routine`; the record is then re-checked against the table.
3. `damage: reenterable` with empty, whitespace, or placeholder `reentry_proof` falls back to
   `durable`; the record is then re-checked against the table.
4. `damage: unknown` that is unresolved at gate time is counted as `durable`.
5. Every record names the `outcome` it was examined against.

The validator reports per-record errors with the record's `mode` and `outcome`. A failing run
blocks the closure gate. The validator makes no probability judgment of its own.

Tests cover: each table cell; each fallback path; placeholder-proof rejection; basis outside the
enumeration; unresolved `unknown`; and a self-reported `expansion` that contradicts the lookup.

## Files Changed

| File | Change |
|---|---|
| `references/failure-proportionality.md` | New. The rule, table, locks, closure semantics, ordering. |
| `prompts/spec-reverse-grill.md` | Exception lens classifies before expanding; issue schema gains the classification fields; `closed` redefined as classified. |
| `prompts/task-reverse-grill.md` | Same. |
| `prompts/spec-closure-critic.md` | Critic accepts the table; may challenge classification, locks, and proof quality only. |
| `prompts/task-closure-critic.md` | Same. |
| `references/spec-closure-and-abstraction.md` | The failure/degraded/rollback block accepts `none` and `guard-only` as closed; exit gate updated. |
| `references/task-documents.md` | Global reverse closure accepts the same. |
| `SKILL.md` | Wire the new reference; version bump. |
| `scripts/validate_failure_classification.py` | New validator. |
| `scripts/test_validate_failure_classification.py` | New tests. |

Critic prompts must change in the same revision. If a critic still demands per-mode treatment, it
re-raises every suppressed mode and the loop reopens, making the rest of the change inert.

No new persisted review artifact beyond `reviews/failure-classification.json`. Ordering ledgers
reuse the existing `reviews/spec-grill.md` and `reviews/task-grill.md`.

## Version And Mirror

Version `0.19.5` -> `0.20.0`, synchronized across `.claude-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, and `SKILL.md` frontmatter.

`codex/grillstorm/` is currently byte-identical to `claude/grillstorm/skills/grillstorm/` apart from
its `agents/` directory. Every change above is mirrored there.

## Non-Goals

- No cap on total findings, and no quota on exception findings.
- No probability estimation by the validator.
- No skip permission for any lens other than through the classification table.
- No change to review budgets in `references/review-budgets.md`.
