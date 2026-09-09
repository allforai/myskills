# T14 spec review — #14 corrections @ 00b5caad (diff 5c02e24c…00b5caad, base 1ed30ee5)

Read-only; probes ran in `/tmp` fixtures with `GIT_*` stripped, checkout untouched.
`pytest tests/unit/test_external_change_recovery.py -q`: 26 passed. Both prior majors
close (see bottom). Both findings below are introduced by this correction: each probe
was rerun against a `git archive 5c02e24c` extraction and behaves correctly there.

## Finding 1 — a memoized classification is never re-verified (major)

AC: "经核实仅为实现层变化时增量更新事实文档；产品行为变化或语义影响不明确时展示冲突."
`resolve_external_changes` (evidence_freshness.py:520-527) reuses
`previous['classification']` whenever it is `fact-update`/`product-conflict`/`uncertain`.
The key is `change_identity(node_id, changed-file fingerprints)` (:412), which excludes
the acceptance argv and everything the acceptance depends on outside that file set —
including paths `inventory` skips (`node_modules`, `.venv`, :554).

Repro (`probe_cache.py`): benign drift → `fact-update`; then the acceptance's installed
dependency regresses so the recorded acceptance now fails. Same `change_id`; the
explicit `external-changes` op still reports `fact_update`, readiness shows only
`stale_evidence`, repair owner `deliver-export/implementation`. Clearing the memo and
rerunning on byte-identical source gives `product-conflict`, `unresolved_external_change`,
owner `interactive-bootstrap/product-decision`. At 5c02 step 2 already gave
`product-conflict`. So a live product conflict is reported as an implementation fact,
and the user has no way to force re-verification.

## Finding 2 — a gate executes acceptance and can mutate its own inputs (major)

AC: "无人值守执行遇到未决冲突时不发起产品访谈、不假定接受变化." `external_conflicts`
(:289) now runs classification, so `validate_unattended_readiness`, `evaluate`/`check`
and `check_artifacts.py` execute the project's recorded acceptance argv — the last of
these after every node (orchestrator-template.md:114).

Repro (`probe_mutation.py`): a self-healing acceptance (regenerate, then verify — a
codegen/format step). External edit leaks another account's orders; readiness alone
reverts `orders.py` to the recorded content, exits 0, `status: ready`, no blockers, and
records `fact-update`. At 5c02: file unchanged, `not_ready`, `stale_evidence`. A
validator destroyed an out-of-flow source edit and produced a false-valid classification.

## Verified closed / not proven

Prior Finding 1: identity drops `baseline_version` (:412); reject survives a v2 refreeze,
defer survives two refreezes with its reason, and revision supersedes (probe_defer,
tests:433/477). Prior Finding 2: readiness/artifacts/reconcile route drift to
`interactive-bootstrap` with no prior detection (tests:516); unrelated `warehouse`
stays valid; corrupt/unreadable stores fail closed. Docstring minor fixed.
Real Claude/Codex host dialogue proof remains pending; all evidence here is copied-CLI.
