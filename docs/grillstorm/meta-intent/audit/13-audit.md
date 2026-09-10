# #13 meta-skill：流程内实现与文档同步后才能完成 — audit 2026-09-11

Tree: main @ 3b195f19

Ticket #13 was revised to v2 after this plan's Task 5 step was written: the current
`gh issue view 13` carries the original 8 "Acceptance criteria" plus two later sections,
"本次重生成的增量要求" (2 items) and "同步后共同验收约束" (2 items), for 12 criteria total.
Rows 1–8 use the plan's cited proofs verbatim; rows 9–12 (not in the plan's Task 5 table)
are proved from tests the plan's Step 1 already runs for this ticket, plus two additional
tests run here and named explicitly, applying the same "proved only by a test or artefact"
rule from Global Constraints.

| # | Criterion (verbatim) | Proof | Result |
|---|---|---|---|
| 1 | 规划阶段识别相关事实文档、产品决定、Node-spec／依赖和验证责任，局部改动不要求重新 bootstrap 整个产品。 | `test_bootstrap_scope.py::test_scoped_workflow_needs_documentation_as_well_as_code_and_verification`; `test_local_reopen_scope.py::test_reopened_local_intent_blocks_only_its_consumers_until_reconfirm_refreeze_replan` | PASS (1 passed in 0.25s); PASS (4 passed in 4.23s) |
| 2 | 实施后按实际代码更新接口、模块行为、实现状态等事实及其证据，协调受影响工作流和 Node-spec，保留历史。 | `test_external_change_recovery.py::test_a_verified_fact_update_survives_synchronizing_the_document_it_requires` | PASS (2 passed in 2.33s) |
| 3 | 已批准的产品变化按记录同步到基准；实现不能自行覆盖用户意图，也不重复询问已有且仍适用的决定。 | `test_external_change_recovery.py::test_a_revised_confirmed_intent_supersedes_the_earlier_decision`; `test_product_intent_session.py::test_existing_canonical_user_choice_is_reused_without_new_intent_decision` | PASS (2 passed in 2.05s); PASS (2 passed in 0.38s) |
| 4 | 产品源码、确认基准、必需文档或验收证据任一不一致时，相关任务不能标记完成，即使代码构建或测试局部通过。 | `test_delivery_closure.py::test_local_feature_closure_refuses_inconsistency_and_recovers`; `test_delivery_closure.py::test_required_document_without_verification_is_refused_at_every_gate` | PASS (2 passed in 9.49s); PASS (2 passed in 1.82s) |
| 5 | 不一致形成明确差异与修复责任，回到责任任务修复后重新同步并重验，不能只写一条警告便宣称闭环。 | `test_external_change_recovery.py::test_drift_reaches_the_gates_as_unverified_and_verification_routes_it_to_its_owner`; `test_delivery_closure.py::test_document_verification_must_match_the_node_spec` | PASS (2 passed in 2.80s); PASS (4 passed in 2.53s) |
| 6 | 未知产品决定不能由无人值守执行补造；相关工作报告受阻并交回交互阶段处理，遵守已有有限重试与失败报告机制。 | `test_run_policy_session.py -k "unattended or interview or decision"`; `test_bootstrap_scope.py::test_unanswered_local_requirement_blocks_both_run_preflight_gates` | PASS (6 passed, 15 deselected in 4.60s); PASS (1 passed in 0.24s) |
| 7 | 修复完成后，新证据绑定当前输入并恢复相关完成状态，无关工作保持有效。 | `test_delivery_closure.py::test_local_feature_closure_refuses_inconsistency_and_recovers` (recovery half, same run as row 4); `test_delivery_closure.py::test_document_check_that_changes_inputs_cannot_publish_proof_for_the_old_state` | PASS (2 passed in 9.49s); PASS (4 passed in 1.76s) |
| 8 | 用完整局部功能 fixture 验证文档遗漏拒绝完成、纠正后通过、已批准产品变化传播，以及受阻后恢复；两端使用相同产品权威规则和外部行为判据。 | `python3 -m pytest -q claude/meta-skill/tests/unit/test_delivery_closure.py -k "claude or codex" -v` | PASS (22 passed in 18.98s) |
| 9 | 与 main 的 accepted_with_gaps 区分：允许按 Run Policy 结束运行并报告缺口，不等于任务验收通过；过期文档、未决产品授权、失配证据不能转为 verified/completed。 | `test_delivery_closure.py::test_accepted_with_gaps_is_a_qualified_run_outcome_not_completion` (host-parametrized; asserts `checked["all_exist"] is False`, `status_error == "accepted_with_gaps"`, `artifact_readiness == "blocked"`, `plan["action"] == "invalidate"`) | PASS (2 passed in 0.75s) |
| 10 | 实现→同步→重新验收各环节复核当前输入，覆盖 SG01；本票复用运行策略合同，不复制另一套交互或重试机制。 | `test_delivery_closure.py::test_local_feature_closure_refuses_inconsistency_and_recovers` (its `# SG01 inside synchronization` block: observe A, mutate to B before publish → `stale`; re-observe and republish B → `valid`); `test_run_policy_session.py -k "unattended or interview or decision"` (same one-time Run Policy contract, no separate mechanism — same runs as rows 4/7 and row 6) | PASS (2 passed in 9.49s); PASS (6 passed, 15 deselected in 4.60s) |
| 11 | Claude 与 Codex 的实际入口和生成产物消费同一权威规则；脚本测试不冒充真实宿主测试。 | **none by pytest** — requires real Claude and Codex host runs from a clean context (same condition as #15–#18); a symlinked script or a pytest parity run is regression reference only, which is what this criterion says cannot count | AWAITS HOST RUN |
| 12 | 基于同步后的当前候选重新验证；历史通过报告仅供回归参考，不直接证明新版本完成。 | **none by pytest** — requires real Claude and Codex host runs from a clean context (same condition as #15–#18); a symlinked script or a pytest parity run is regression reference only, which is what this criterion says cannot count | AWAITS HOST RUN |

Verdict: KEEP OPEN (criteria 11, 12 await real Claude + Codex host runs; all pytest-provable criteria PASS)
