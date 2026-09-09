# T14 spec review — `526ef960` (#14)

Base `9bade2ff`; candidate reviewed as committed, HEAD unchanged, read-only.
Evidence is copied-CLI pytest (`--tb=short`) on a full-repo clone carrying Git context,
both adapters (`HOSTS = ["claude", "codex"]`). **This is not host proof**: #14 stands at
0/16 and the #8 matrix at 0/60, unchanged by this commit.

## Verdict

No missing or partial requirement, no scope creep, no incorrect implementation found.

## Requirements served

- 「接受变化：记录用户决定及理由，更新产品基准版本，传播影响、协调任务和文档、重验并恢复相关执行」,
  「拒绝变化：保留确认基准，形成范围明确的实现修复任务」, 「暂不决定…保留冲突和上下文；无关工作不因而被全量重置」.
  At `9bade2ff` a decided change lost its verdict as soon as any project file moved — including
  the document the decision itself ordered written — and `routed_external_changes` regrouped it as
  unverified. Independently reproduced and confirmed fixed: accept reaches `ready` after document
  sync, refreeze, replan and republication; reject keeps `external_change_repair_pending` scoped to
  `orders.py` with the confirmed acceptance; defer keeps `unresolved_external_change` still reading
  "deferred (product-conflict)"; a verified `fact-update` survives writing its own required document.
- 「复用流程内同步／完成门槛，而不是另造外部修改专用验收体系」and 「Claude 与 Codex 的实际入口和生成产物消费同一权威规则」.
  `undetermined_external_change` was emitted by `validate_unattended_readiness.py:360` but absent from
  both `orchestrator-template.md` enumerations ("All three…") and from `input-freshness.md`. Both
  templates now carry it; Codex has no separate copy and takes the canonical `input-freshness.md`
  (`codex/meta-skill/skills/bootstrap.md:144`), so adapter parity holds.

## Guards independently verified (all hold)

Post-accept drift is not swallowed — a further external edit after a closed accept raises
`unverified_external_change`, because `change_identity` keys on file content. True source drift still
drops an undecided verdict (moving `warehouse.py` → `unverified_external_change` on both nodes).
Passive gates never execute acceptance: an instrumented acceptance command ran zero times across
readiness, artifact check and reconcile, and only under the bootstrap-entry `external-changes`
command. Unrelated `warehouse` results stay valid. Corrupt/unwritable-store blocking and
requirement-revision supersession keep their `9bade2ff` tests. `standing_changes`'s dropped third
return value has no other caller. The whole `claude/meta-skill/tests/unit` suite is green on the
candidate in that clone: **647 passed** (`pytest -q --tb=short`).

## Evidence note — not a product defect

`test_an_accepted_change_recovers_once_its_required_document_is_synchronized` calls
`external(tmp_path)` after the document sync and before refreeze; that command does run the
project's acceptance, so as written the test does not demonstrate its own "without another
verification step" claim. Deleting that line leaves the test green (2 passed), so the recovery does
not depend on it. Report/test-evidence gap, not a defect in the product.
