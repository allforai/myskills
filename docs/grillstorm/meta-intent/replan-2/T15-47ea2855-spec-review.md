# T15 SPEC review — 47ea2855 (base 2cc347af)

SPEC axis. Diff `2cc347af...47ea2855`. Sources: `replan-2/issues/9.md`–`18.md`, `program-spec.md`.
Verdict: **reject** — stated scope delivered; two adapter-parity requirements only partly met.

## Delivered against spec

- Repair delivery is measured, not asserted: `measuredDelivery` (engine-core.js:355) requires every
  declared exit artifact present, a moved digest, one unchanged `binding_identity`, `readiness_status
  == "valid"`, withheld only by the loop's own QA node. Satisfies #13 "修复完成后，新证据绑定当前输入
  并恢复相关完成状态" and SG-01.
- Explicit planning confirmation (`plan-confirmation.json` + planning journal, provenance via
  `_journal_decision`) is enforced at bootstrap and re-checked at `/run` — #9 "遵守 ADR-0001 的…
  交互前置", program-spec I-scope.
- `_pending_decisions` blocks a wired-but-unmade choice on every route — #13 "未知产品决定不能由
  无人值守执行补造…交回交互阶段处理".
- Failing-QA → repair → fresh QA → closure runs against the real gate on both adapters
  (`declared-loop.test.js`; `test_real_routing_drives_the_declared_loop_to_closure`). Node 95/95,
  Codex 98/98, Claude unit 806/806 green here. 60 host cells stay `actual_host_passed: 0`:
  unexecuted, not a regression.

## Findings

1. **`/run` does not enforce the new structural gates on Claude (partial).** The commit's own
   `bootstrap-node-expansion-qa/SKILL.md` states these are decided by "the copied `validate_bootstrap.py`
   … at both the bootstrap and `/run` boundaries". But `validate_unattended_readiness.py:14,327`
   imports only `plan_confirmation_blockers`; `validate_repair_loop_declaration` and
   `validate_effect_stage_ownership` are reachable only from `validate_bootstrap.main()`
   (validate_bootstrap.py:1874–1876); Claude's `/run` runs readiness alone
   (`claude/.../orchestrator-template.md:36`) while Codex runs `validate_bootstrap.py`
   (flow-template.py:1042). A `downstream_effect_owner` naming a missing node, or a loop with no
   closure holder, executes unblocked on Claude. Breaks #13 "Claude 与 Codex 的实际入口和生成产物
   消费同一权威规则".

2. **Repair-budget accounting differs between adapters (wrong implementation).** Claude charges an
   attempt at route time — `loadDagPrompt` counts "transition_log entries for that QA node with status
   'failed'", and `repairRoutePrompt` writes that entry before the repair runs (engine-core.js:228,339).
   Codex counts only delivered repairs (`repair_progress` → `repair_delivered`, flow-template.py). From
   one `max_attempts`, an interruption between routing and execution, or a repair that delivers nothing,
   leaves the two hosts with different remaining budgets. The templates also diverge on an invalid
   budget: Claude "the QA failure goes to diagnosis", Codex "the QA node is re-run instead". Breaks
   program-spec O3 "identical authority/routing/readiness semantics".

3. **Candidate-freshness ledger contradicts itself (SG02).** `execution.json` flips
   `preparation_verification.candidate_refresh_required` true→false pinned to `"candidate":
   "e30ccc7c…"`, while the same file's `correction_verification_checkpoint.fresh_candidate_required`
   is `true` and each T15–T18 `results.json` records `candidate_refresh_required: true`. The candidate
   has since moved twice. #15–#18 SG02: "旧安装版本或候选改变后的旧证据不可充数".

## Scope

`check_codex_meta_skill_parity.py` / `smoke_codex_generated_run.py` were rewritten (install_bundle.py,
sandbox-policy assertions, `skills/bootstrap.md` → `skills/bootstrap/SKILL.md`) — unrelated to this
commit's subject, though it repairs guards that were false or vacuous. No product scope creep otherwise.
