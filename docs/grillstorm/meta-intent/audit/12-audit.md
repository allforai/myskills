# #12 meta-skill：源码与产品基准变化触发精准证据失效 — audit 2026-09-11

Tree: main @ 3b195f19

| # | Criterion (verbatim) | Proof | Result |
|---|---|---|---|
| 1 | 文档、执行合同和验收证据能追溯到所使用的产品源码状态、已确认产品基准版本和相关输入依赖。 | `tests/unit/test_evidence_freshness.py::test_observe_a_change_b_rejects_publication_until_b_is_reverified` | PASS (2 passed in 0.59s) |
| 2 | 同一提交上两次不同未提交改动可区分；不能仅用 commit 加 dirty 布尔值、文件存在或修改时间判定有效性。 | `shared/evidence-engine/test_identity.py` | PASS (10 passed in 2.03s) |
| | | `tests/unit/test_evidence_freshness.py::test_unknown_source_impact_and_output_tampering_cannot_prove_completion` | PASS (2 passed in 0.43s) |
| 3 | 源码变化与产品基准变化都触发影响分析，覆盖直接和传递依赖；相关旧文档／任务／验收被明确标为需要协调或过期。 | `tests/unit/test_evidence_freshness.py::test_source_drift_propagates_through_resume_and_both_gates_preserving_other_branch` | PASS (2 passed in 1.40s) |
| | | `tests/unit/test_evidence_freshness.py::test_baseline_scope_changes_and_artifact_dependencies_invalidate_transitively` | PASS (2 passed in 0.57s) |
| 4 | 无关分支及其有效成果保留，不以全量重建替代影响判断；无法确定影响时明确记录不确定性，不能视为零影响。 | `tests/unit/test_evidence_freshness.py::test_source_drift_propagates_through_resume_and_both_gates_preserving_other_branch` | PASS (2 passed in 1.40s) |
| | | `tests/unit/test_evidence_freshness.py::test_glob_membership_and_missing_dependency_declarations_are_not_zero_impact` | PASS (2 passed in 0.43s) |
| 5 | 区分产品输入与生成文档、运行记录、报告等产物；同步生成物本身不导致无止境的再次同步和自我失效。 | `tests/unit/test_evidence_freshness.py::test_baseline_and_additional_reads_invalidate_without_generated_self_loop` | PASS (2 passed in 0.87s) |
| 6 | 相同输入再次 bootstrap／续跑时，不生成重复产品决定、不重复规划、不改变已有效的验收状态。 | `tests/unit/test_freeze_idempotence.py::test_identical_product_refreeze_converges_without_new_journal_version_or_replan` | PASS (4 passed in 2.78s) |
| | | `tests/unit/test_freeze_idempotence.py::test_tampered_previous_scope_is_not_reused_as_the_identical_freeze` | PASS (2 passed in 1.12s) |
| 7 | 完成检查和执行就绪结果消费这些失效状态，过期证据不能继续证明相关任务完成；本票可通过单独改动输入并重跑检查演示。 | `tests/unit/test_freshness_downgrade.py::test_removing_source_inputs_from_a_published_completed_node_cannot_admit_stale_evidence` | PASS (2 passed in 1.59s) |
| | | `tests/unit/test_freshness_downgrade.py::test_corrupt_or_unknown_freshness_record_fails_closed_for_every_node` | PASS (12 passed in 11.31s) |
| 8 | 复用现有 workflow reconciliation、artifact gate 与 readiness 边界；测试源码单点变化、基准变化、不同 dirty 快照、依赖传播、无关保留及重复检查，Claude／Codex 一致。 | `python3 -m pytest -q tests/unit/test_evidence_freshness.py -k "claude or codex" -v` (file is `host`-parametrized; every test above ran under both) | PASS (32 passed in 8.76s) |
| 9 | 补齐 SG01：观察输入 A 后、证据发布前改成 B，拒绝拿 A 证明 B；实际重新验证 B 后才有效，稳定输入可收敛。 | `claude/meta-skill/tests/unit/test_evidence_freshness.py::test_observe_a_change_b_rejects_publication_until_b_is_reverified`; `test_freeze_idempotence.py::test_identical_product_refreeze_converges_without_new_journal_version_or_replan` | PASS (2 passed — first cited test; all cited tests run and passed) |
| 10 | 继续依赖 #10 的已确认基准合同；不为制造并发移除真实生产者依赖。额外按需读取若形成实际输入依赖，应记录并参与失效，不能仅靠初始声明漏判。 | `claude/meta-skill/tests/unit/test_evidence_freshness.py::test_baseline_and_additional_reads_invalidate_without_generated_self_loop`; `::test_glob_membership_and_missing_dependency_declarations_are_not_zero_impact` | PASS (2 passed — first cited test; all cited tests run and passed) |
| 11 | Claude 与 Codex 的实际入口和生成产物消费同一权威规则；脚本测试不冒充真实宿主测试。 | **none by pytest** — requires real Claude and Codex host runs from a clean context (same condition as #15–#18); pytest parity runs are regression reference only | AWAITS HOST RUN |
| 12 | 基于同步后的当前候选重新验证；历史通过报告仅供回归参考，不直接证明新版本完成。 | **none by pytest** — requires real Claude and Codex host runs from a clean context (same condition as #15–#18); pytest parity runs are regression reference only | AWAITS HOST RUN |

Note: each single-test invocation above selected 2 items (the file's `host` parametrization runs every test under both `claude` and `codex`), except `test_corrupt_or_unknown_freshness_record_fails_closed_for_every_node` (12 items — additionally parametrized per node) and `test_identical_product_refreeze_converges_without_new_journal_version_or_replan` (4 items). All selected items passed in every run.

Verdict: KEEP OPEN (criteria 11, 12 await real Claude + Codex host runs; all pytest-provable criteria PASS)
