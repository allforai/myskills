# T14 standards re-review — #14 correction (5c02e24c → 00b5caad)

Axis: documented hard breaches (`CLAUDE.md`, `CONTEXT.md`, `codex/meta-skill/AGENTS.md`,
ADR-0001–0003, `knowledge/input-freshness.md`) versus optional Fowler heuristics. No lint
or formatter config exists in the repo, so nothing is excluded as tooling-enforced. The
prior review's "Duplicated Code" was called a hard breach in error; every heuristic below
is optional. Evidence is copied-CLI in temporary projects (isolated `git archive`
extractions of both commits, `GIT_*` stripped, checkout untouched) — **not** real
Claude/Codex host dialogue proof, which #14 still owes.

Verified fixed: `owned_inputs` extracted (`evidence_freshness.py:379`);
`classify_external_change.__doc__` is no longer `None`.

## Hard breach (correction-introduced)

### 1. An unwritable store makes every gate lose the conflict silently

`external_conflicts` (`evidence_freshness.py:288-293`) now wraps `resolve_external_changes`,
which **writes** the store (`:532`), and still swallows `OSError` and returns `{}`. So a
non-writable `.allforai/bootstrap/` deletes the conflict from `check`, `check_artifacts.py`,
reconciliation and readiness — the exact routing loss this commit set out to fix.

Repro (`drift_project` + conflicting `orders.py`, then `chmod 555 .allforai/bootstrap`):

```
# 00b5caad
check_artifacts.py  rc=0  repair {'owner': 'interactive-bootstrap', ['product-decision']}  (writable)
check_artifacts.py  rc=0  repair {'owner': 'deliver-export',        ['implementation']}    (read-only)
readiness           blockers ['stale_evidence','unresolved_external_change'] → ['stale_evidence']
# 5c02e24c, same read-only state after an explicit external-changes refresh
check_artifacts.py  rc=0  repair {'owner': 'interactive-bootstrap', ['product-decision']}
```

Breaches `input-freshness.md:110-112` ("The affected node's repair owner is
`interactive-bootstrap` (`product-decision`) and readiness reports
`unresolved_external_change`") and `:146-147` ("Unattended execution reports unresolved
conflicts and refuses the affected work"). The comment's claim that "other gates already
fail closed on the same unreadable state" is false here: rc stays 0, no blocker is added.
The read path at 5c02 was resilient; the added write is the new fragility. Fix: let the
write fail soft (or run detection read-only) and never return `{}` for a detected conflict.

## Optional heuristic smells

- Duplicated Code — `product_intent.py:801` re-scans every node with a second
  `detect_external_changes` plus a `next(...)` fallback over the dict already built at `:739`.
- Mysterious Name — `validate_unattended_readiness.py:357` binds `state` to an English
  clause, colliding with node `state` at `:246`/`:404`.
- `input-freshness.md:144` is 93 cols against the file's ≤83 wrap (paragraph not re-wrapped).

`orchestrator-template.md`, `bootstrap.md` parity and ADR-0001–0003 alignment are clean.
