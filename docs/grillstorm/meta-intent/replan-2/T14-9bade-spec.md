# T14 spec review — #14 corrections @ 9bade2ff (diff 11f9a44c…9bade2ff, base 1ed30ee5)

Read-only. Probes ran in `git archive` extractions of both SHAs, `GIT_*` stripped; this
checkout was never a fixture. Every probe was rerun at `11f9a44c` to separate regression
from pre-existing behavior.


## Finding 1 — a decided change reappears as unverified drift (major, introduced)

AC: "接受变化：记录用户决定及理由，更新产品基准版本，传播影响、协调任务和文档、重验并恢复相关执行."

`classification_basis` (evidence_freshness.py:514) digests the **whole** `source_tree`, and
`source_tree` (:626) — unlike `inventory` — no longer excludes the flow's own
`exit_artifacts`/`required_documents`, so the "协调文档" step invalidates its own verdict.
`routed_external_changes` (:279) then groups on `classification` alone, never consulting
`change['resolution']`, so a settled change lands in the *unverified* group.

Repro (probe4): accept with an `adjust`, write `docs/orders-export.md`, refreeze v2,
replan, publish contract → readiness `not_ready`, sole blocker `unverified_external_change`.
At `11f9a44c` the same sequence is `ready`, exit 0. Recovery needs an extra
`external-changes` run no document lists in the accept loop, while
orchestrator-template.md:98 tells the run to refuse the affected work.

Same cause, two more regressions vs `11f9a44c`:

- Reject — AC "形成范围明确的实现修复任务": after `reject`, one unrelated file write drops
  `external_change_repair_pending` from readiness; the scoped repair is replaced by
  unverified drift routed back to the interactive entry (probe1).
- Fact update — AC "经核实仅为实现层变化时增量更新事实文档": after a verified `fact_update`,
  writing its fact document reintroduces `unverified_external_change` until republication
  (probe3).

Nothing bypasses product authority — every path fails closed toward blocking. The defect is
spurious blocking of decided or verified work and loss of the conflict/repair state the ACs
name. Defer keeps its hold but loses its "deferred" context.

## Verified closed / residual limits

Passive gates no longer execute project argv: a self-healing acceptance leaves the user's
bytes intact across readiness, `check_artifacts.py` and reconciliation (probe2), and drift
reaches them as `external: unverified` with node-owned repair — fact-only recovery still
needs no interview. Memoized verdicts are no longer replayed. An unwritable store keeps its
conflict and its `interactive-bootstrap` routing; a corrupt store or freshness state yields
`undetermined_external_change` (probe5). The builder's residuals hold as stated: explicit
verification of a self-healing acceptance returns rc 1 `invalid`, records nothing, leaves
the post-command source (no #14 AC requires restoration). "No `--reverify` needed" does not:
Finding 1 makes re-verification mandatory for reasons no doc states.

Unrelated #9–13 behavior holds: `claude/meta-skill/tests/unit` gives 637 passed plus 2 that
fail identically at `11f9a44c` for want of a `.git` in the extraction. Actual Claude/Codex
host proof remains 0/16 for #14 and 0/60 overall; all evidence here is copied-CLI.
