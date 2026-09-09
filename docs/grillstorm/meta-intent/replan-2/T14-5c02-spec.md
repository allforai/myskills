# T14 spec review — #14 v2 @ 5c02e24c (base 1ed30ee5)

Read-only. Probes ran against the checkout; only `validate_unattended_readiness.py`
is dirty (a semantics-preserving type-narrowing edit, not mine, left in place), so
findings hold for the pinned commit. `pytest test_external_change_recovery.py -q`:
16 passed.

## Scope

No creep: the diff touches detection/decision/readiness, their docs, one test file
and a report. Nothing visual, so the ADR-0002/0003 constraint ("视觉文件迁移由
#27→#40→#41 负责，本票不重新实现") is met. Run Policy `accept` is proven distinct
from product acceptance (test line 289-296).

## Finding 1 — a rejected change is re-asked after the next freeze (major)

AC: "拒绝变化：保留确认基准，形成范围明确的实现修复任务，修复后同步文档、重新验收并恢复执行."
`change_id` digests `baseline_version` (evidence_freshness.py:434), and
`external_conflicts` keys on that id (:296). Recording a `reject` appends a journal
batch (product_intent.py:768-781), which makes the *next* `freeze` bump the baseline
to v2 — so the identity changes and the settled decision is unreachable.

Repro (`probe3.py`): drift → conflict `fdb47f296e7d` → reject → `_freeze("scope-9")`
→ version 2 → redetect yields `5855a7d4166d`, `resolution: None`. The user is asked
again about a change they already rejected; the repair task at product_intent.py:790
is orphaned. A `defer` loses its reason the same way once any other decision bumps
the baseline (probe3 keeps v1 only because nothing else was decided).

## Finding 2 — the outstanding decision is invisible between boundaries (major)

AC: "无人值守执行遇到未决冲突时…不假定接受变化." `external_conflicts` reads only the
store written by `external-changes`; an undetected/re-identified conflict is skipped
at :297. In the Finding-1 window (`probe4.py`) readiness drops to
`[('stale_evidence','deliver-export')]` and the repair owner flips from
`interactive-bootstrap/product-decision` to `deliver-export/implementation` — `/run`
is told to repair the node itself. Only the failing acceptance still prevents
closure; the "return to the interactive entry" routing is lost. `/run` never invokes
`external-changes` (SKILL.md:403 puts it at bootstrap/resume only).

## Finding 3 — dead docstring (minor)

evidence_freshness.py:449-452: the `record is None` return precedes the string, so
`classify_external_change.__doc__` is `None`.

## Not proven

Codex parity is a `scripts` symlink plus duplicated prose; host dialogue proof
remains pending, as the implementation report states.
