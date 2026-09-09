# T14 standards review — #14 v2 (1ed30ee5 → 5c02e24c)

Scope: pinned diff only. Documented rules (`CLAUDE.md`, `CONTEXT.md`, `codex/meta-skill/AGENTS.md`,
ADR-0001–0003, `knowledge/input-freshness.md`) override heuristic smells. No tooling config exists in
the repo, so no findings are excluded as tooling-enforced.

## Hard breaches

### 1. A recorded external-change resolution is silently dropped by an unrelated refreeze

`claude/meta-skill/scripts/orchestrator/evidence_freshness.py:429` binds `change_id` to
`baseline_version`, and `external_conflicts` (`:295-297`) matches a stored resolution by `change_id`
alone. Any unrelated `freeze` bumps that version (`product_intent.py:947`), so the identity of an
*unchanged* conflicting file changes and the recorded decision is orphaned.

Reproduction (isolated copy of `claude/meta-skill`, `GIT_*` stripped, worktree untouched); reject a
conflict, then refreeze an unrelated scope:

```
BEFORE ['external_change_repair_pending', 'stale_evidence']
AFTER  ['stale_evidence']
# re-detection then reports the same orders.py as a fresh product-conflict, resolution: null
```

This breaks two documented invariants in `knowledge/input-freshness.md` (added by this diff): "The
next boundary reports the same change identity with its resolution intact" and "Detection never
invents, reopens or recomputes a recorded resolution." Consequence: the rejected change's scoped
implementation repair stops blocking unattended readiness, and the user is re-interviewed on a
decision they already made. `defer` is lost the same way. Fix: key the stored resolution on node +
file content and carry it across baseline versions, rather than on a baseline-scoped digest.

### 2. Duplicated Code — the unmapped-source computation is copied verbatim

`evidence_freshness.py:388-394` and `399` reproduce `517-523` and `561` line for line (the `owned`
set built from `source_inputs`/`input_dependencies`, `extra`, `inputs.files`, `observed_reads`, and
the `previous`/`current` symmetric diff minus `owned`). Extract one helper and call it from
`unmapped_changes` and `evaluate`.

### 3. Dead docstring in `classify_external_change`

`evidence_freshness.py:448-456`: the `record is None` early return precedes the string literal, so it
is a no-op expression. Verified: `classify_external_change.__doc__` is `None`. Move it above the
guard.

## Optional judgment calls

- `external_conflicts:286-292` swallows six exception classes and returns `{}`. The comment asserts
  other gates fail closed on the same state; that claim is not asserted anywhere in this diff.
- `product_intent.py:713-714` leaves three blank lines before `_external_change`.

Docs, Codex adapter parity (`orchestrator-template.md`, `bootstrap.md`) and ADR-0001–0003 alignment
are clean.
