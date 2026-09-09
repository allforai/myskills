# T14 candidate 9bade2ff — independent review and disposition

Candidate: `9bade2ffe869395b7b59e71080b5e17243985782`; correction base: `11f9a44cf712fad200c99fe4ee402dc05a5d5a9f`.

The two independent reports below retain their separate axes. Original reports remain beside this file.

## Standards

Axis: documented rules (`CLAUDE.md`, `CONTEXT.md`, `codex/meta-skill/AGENTS.md`, ADR-0001–0003,
`knowledge/input-freshness.md`, both `orchestrator-template.md`) versus optional Fowler
heuristics. No lint/format config exists in the repo, so nothing is excluded as
tooling-enforced and line width is not a documented rule. Evidence is copied-CLI in a
temporary `git archive` extraction (`GIT_*` stripped, checkout untouched) — **not** real
Claude/Codex host dialogue proof, which stays 0/16 for #14 and 0/60 overall.

**Prior blocker closed.** The 00b5 breach (an unwritable store deleting the conflict from
every gate) is fixed at the seam, not papered over: the gates now route through the
read-only `standing_changes`, and `cache_classifications` (`evidence_freshness.py:532-547`)
fails soft instead of raising or returning `{}`. `test_an_unwritable_store_keeps_the_conflict_it_could_not_record`
covers it; 108/108 pass in the three touched unit files.

## Documented-standard violation

**1. `orchestrator-template.md` enumerates the external-change blockers exhaustively and
this commit made that enumeration false.** `claude/…/orchestrator-template.md:98-101` and
`codex/…/orchestrator-template.md:150-153` say "`unresolved_external_change`,
`unverified_external_change` or `external_change_repair_pending` … **All three** are
preflight blockers". The same commit adds a fourth external-change readiness code,
`undetermined_external_change` (`validate_unattended_readiness.py:360`), documented in
neither template nor `input-freshness.md`'s outcome list. Behaviour still fails closed via
the template's generic "do not execute newly exposed work when readiness is not `ready`"
(`:76-78`), so this is doc-vs-code, not an open gate — but the generated run meets a
blocker code its own instructions do not name.

## Heuristic smells (judgement calls, not blockers)

- **Speculative Generality / dead read** — `standing_changes` opens the workflow and never
  uses it: `workflow = read_json(root, WORKFLOW, {})` (`:561`); one extra JSON read on
  every gate call.
- **Speculative Generality** — `cache_classifications`' docstring promises to "report
  whether the cache was written"; the sole caller discards it: `cache_classifications(root, changes)` (`:611`).
- **Middle Man** — `external_conflicts` is now `return routed_external_changes(root)[0]`
  (`:308-310`), a positional-index passthrough.
- **Duplicated Code** — `state['nodes'].get(change['node_id']) if change['node_id'] else None`
  at `:568` and `:600`, each after its own `state = read_json(root, STATE, …)` (`:562`, `:595`).
- **Docstring drift** — `routed_external_changes` claims "It raises, so every gate fails
  closed"; the function contains no `raise` (it inherits one from `standing_changes`).

Carried over from 00b5, untouched here: `product_intent.py:801` duplicate
`detect_external_changes` rescan; `validate_unattended_readiness.py:375` binds `state` to an
English clause. Host parity (both templates, both bootstrap entries) is word-identical;
ADR-0001–0003 and `AGENTS.md` contract notes are unaffected.

## Spec

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

## Coordinator disposition

- Standards: 1 documented instruction mismatch; worst within this axis is the missing `undetermined_external_change` guidance. Add the missing outcome to both host templates and the freshness reference. The 5 heuristic smells and 2 carried-over observations are not acceptance blockers and are not grounds for unrelated refactoring. A function can propagate an exception without a local `raise`; that docstring observation alone does not prove a defect.
- Spec: 1 new major; worst within this axis is already-decided work becoming unverified again during its own document synchronization. This is an acceptance blocker. Fix the public recovery paths without dropping freshness or asking again for recorded user consent.
- All three prior 00b5 blockers are confirmed closed by the two axes. Their regression tests must remain effective.
- Fix ownership: task `task_8d906f40b0df`, dispatch `ctx_f392228d665f`, same Opus terminal reused under a fresh assignment. Standards terminal released. Source remains on 9bade2ff until that correction is committed; no main merge authorized by this review result.
- Root verification at 9bade2ff: 108 targeted copied-CLI tests passed (65.50 s), 55 Node tests passed. The main/9bade preflight tree `ac07050f414ff2171dc989b8841f159d9a88ac40` has no textual conflicts. An initial full test of its archive passed 672 cases and failed 2 because the archive had no enclosing Git context; after adding a temporary fixture Git context, those 2 passed without a source change. The complete rerun then passed all 674 Python/Codex cases (230.56 s); 55 Node cases also passed. This is preflight evidence for that tree, not an applied merge or proof of future corrections.
- Actual host proof is still 0/16 for #14 and 0/60 for T15–T18. Implementation acceptance, real host proof, main integration and worktree cleanup remain incomplete.

Summary: Standards — 1 documented mismatch plus 5 optional heuristics; Spec — 1 new major recovery regression. Candidate is not accepted.
