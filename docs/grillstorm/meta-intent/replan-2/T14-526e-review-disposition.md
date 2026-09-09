# T14 — 526ef960 review in progress

Candidate: `526ef960e8c85fabbdf8862608a65c942413d1bb`.
Fixed point: `9bade2ffe869395b7b59e71080b5e17243985782`.

Implementation acceptance is supported by independent Standards and Spec reviews.
Real host proof remains 0/16 for #14 and 0/60 for T15–T18.
Neither main integration nor task-worktree cleanup has happened.

## Evidence precision correction

The committed `T14-resolution-sync-corrections.md` says the accept recovery reaches
ready without another `external-changes` call. Its committed regression does call
`external(tmp_path)` after document synchronization and before refreeze. That call
executes acceptance and writes classification state; this test therefore does not
isolate the entire no-reverification recovery claim. Its immediate post-document
readiness assertion does run before that call and observes no external blocker.

Builder completion message `msg_97896466f58f` explicitly acknowledges this gap. It
reports a separate scratch probe of the pinned archive with the intervening call
removed: both adapters reached ready after refreeze/replan, published valid evidence,
and stayed ready. This is builder-reported supplementary evidence, not independent
review or actual host dialogue proof. The independent Spec reviewer is assigned to
check the path separately. Preserve the original report and this qualification;
do not silently turn a stronger report statement into test coverage.

The builder reports 116 targeted, 647 full Python, 35 Codex adapter, 55 Node tests,
and three core mypy checks passing. Normal commit hook completed with exit 0.
The builder Dispatch `ctx_f392228d665f` completed and was released, with transcript
captured. The two read-only review Dispatches both completed and were released:

- Standards: `ctx_03da6a472fa3` / `task_01b653f5e870` — completed and released.
- Spec: `ctx_c3ff54dc22ab` / `task_f000567e39c5` — completed and released.

## Standards

# T14 standards review — `526ef960` (base `9bade2ff`)

Rules read: `CLAUDE.md`, `CONTEXT.md`, `codex/meta-skill/AGENTS.md`, ADR-0001–0003,
`input-freshness.md`, both `orchestrator-template.md`. Tooling-enforced items are excluded:
`.githooks/pre-commit` runs `py_compile`, the unit suite and the validators. No lint/format
config exists, so line width and layout are not documented rules.
Evidence: `pytest tests/unit/test_external_change_recovery.py -q --tb=short` → **42 passed**
(tmp_path fixtures). Copied-CLI only; real host proof stays 0/16 for #14, 0/60 overall.

## Documented-standard breaches (hard rules)

**None new.** The `9bade2ff` blocker is closed: `undetermined_external_change` is now named
in all three enumerations — `claude/…/orchestrator-template.md:98-108`,
`codex/…/orchestrator-template.md:150-160` ("All four"), and `input-freshness.md:137-140`.
`grep -rl external_change_repair_pending` finds no fourth enumeration, and the two templates
stay word-parallel per host parity.

**Docs match real blocking.** `validate_unattended_readiness.py:354-362` emits it from the
`except` around `routed_external_changes` with **no `node_id`** — project-wide, as documented
— for unreadable state / unparseable store, with "resolve it at the interactive bootstrap
entry". `test_unreadable_freshness_state_cannot_report_or_decide_external_changes:378-384`
asserts exactly `["undetermined_external_change"]` and `not_ready`. Verified.

## Heuristic smells (judgement, not blockers)

- **Mysterious Name / stale contract** — `routed_external_changes`'s docstring, one line above
  the changed hunk, still says the groups are "changes a standing verification classified as
  needing a decision, and changes no current verification covers". After
  `change['resolution'] or change['classification'] in (...)` (`:301-303`) group one also holds
  decision-routed changes with **no** standing verdict. Same in `external_conflicts:313`. The
  inline comment is correct; the docstrings above it are not.
- **Repeated Switches** — the classification-string cascade recurs: `:302` and `:582-583`
  (`in ('fact-update','product-conflict','uncertain')`). Two sites switching on one implicit
  type; `classification`/`resolution` remain **Primitive Obsession** (string + dict sentinels).
- **Duplicated Code** — the ~10-line undetermined paragraph is near-identical in both
  `orchestrator-template.md`; deliberate host parity, so heuristic only.

Not present in changed scope: Feature Envy, Data Clumps, Shotgun Surgery, Divergent Change,
Speculative Generality, Message Chains, Middle Man, Refused Bequest. `9bade2ff`'s dead
`workflow = read_json(...)` read is now used (`:571` feeds `inventory` at `:576`) — fixed incidentally.

## Spec

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

## Coordinator disposition

Standards: 0 new hard breaches, 3 advisory smell bullets. Spec: 0 product defects,
1 report/test-evidence qualification independently resolved by the no-extra-call probe.
Do not expand this correction into optional refactoring. The original test's coverage
claim remains qualified above; independent evidence, not the original assertion, supports
the complete recovery path.

Root preflight merged tree `0d3047999b46eef9b0f8ff89bc6bb42d248dd644`
(main `4e34c684` plus candidate `526ef960`) had no textual conflicts and passed
682 Python/Codex tests in 248.35 seconds and 55 Node tests. Test export:
`/private/tmp/meta-intent-526e-merge-check.MLCYes`; an enclosing fixture-only Git
context was supplied for snapshot-isolation tests. No actual main merge occurred.
This accepts the implementation slice, not the required real-host scenario matrix.
