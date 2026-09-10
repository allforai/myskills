# #10 meta-skill：产品意图初稿经用户重塑后驱动完整流程 — audit 2026-09-11

Tree: main @ 3b195f19

| # | Criterion (verbatim) | Proof | Result |
|---|---|---|---|
| 1 | 初稿包含目标用户、场景、核心问题、价值主张、业务闭环和取舍；代码事实、推断意图、未知项明确区分，推断附证据和不确定性。 | `test_product_intent_session.py::test_missing_dimensions_are_pending_gaps_and_bad_evidence_is_rejected` | PASS (2 passed in 0.39s) |
| 2 | 高置信度或充分代码证据不能替代用户确认；初稿和 product-summary 不自动升级为已批准产品基准。 | `test_product_intent_session.py::test_draft_is_provisional_and_resume_only_presents_pending_topics`; `test_bootstrap_scope.py::test_code_derived_confirmed_label_is_not_user_approval` | PASS (2 passed in 0.60s); PASS (1 passed in 0.22s) |
| 3 | 用户能确认、补充、调整、删除意图；新增意图可以没有代码实现依据，其依据是用户需求和决定。 | `test_product_intent_session.py::test_four_explicit_operations_preserve_history_and_user_additions` | PASS (2 passed in 0.51s) |
| 4 | 意图具有稳定身份、来源、决定理由及确认信息；调整保留前后关联，删除保留历史，不在讨论阶段删除或改动产品代码。 | `test_product_question_identity.py` (identity/provenance); `test_product_intent_session.py::test_four_explicit_operations_preserve_history_and_user_additions` (history); "不改动产品代码" — `test_intent_review_corrections.py` | PASS (14 passed in 3.75s); PASS (2 passed in 0.51s); PASS (30 passed in 10.97s) |
| 5 | 按主题讨论，主动指出矛盾和产品空白；不是仅询问是否认可现状，也不是固定长问卷。 | `test_product_intent_session.py::test_draft_is_provisional_and_resume_only_presents_pending_topics` (topics, not a questionnaire); `test_product_intent_session.py::test_missing_dimensions_are_pending_gaps_and_bad_evidence_is_rejected` (gaps surfaced) | PASS (2 passed in 0.60s); PASS (2 passed in 0.39s) |
| 6 | 明确确认基准的范围和版本；未决问题不能通过沉默自动确认，排除范围必须显式决定，依赖未决决定的工作不能被声明可执行。 | `test_product_intent_session.py::test_freeze_needs_explicit_scope_and_pending_exclusions`; `test_product_intent_session.py::test_pending_dependency_cannot_be_excluded_to_authorize_dependent_intent` | PASS (4 passed in 0.99s); PASS (2 passed in 0.39s) |
| 7 | 产品基准整合复用现有 product-concept 与 decision journal 责任，不另造并行事实源；新项目从用户意图出发并进入相同确认合同。 | `test_product_intent_session.py::test_existing_canonical_user_choice_is_reused_without_new_intent_decision`; `test_bootstrap_scope.py::test_new_and_reconstruction_routes_leave_product_confirmation_pending` | PASS (2 passed in 0.39s); PASS (1 passed in 0.39s) |
| 8 | 确认后，生成的 workflow、Node-spec 和验收条件体现新基准的增加、调整和删除，执行适用的完整流程；不以旧代码功能清单为验收真相，也不强制每个 Capability 都运行。 | `test_product_intent_session.py::test_revised_baseline_generates_full_applicable_plan_and_gates_reject_drift`; `test_freeze_idempotence.py::test_changed_product_selection_freezes_a_new_version_and_invalidates_the_plan` | PASS (4 passed in 2.69s); PASS (2 passed in 1.34s) |
| 9 | 通过脚本化用户响应的 bootstrap 场景验证四种操作、无代码依据的新增意图、未决阻塞、新产品路径和讨论不改代码；Claude、Codex 一致。 | `python3 -m pytest -q claude/meta-skill/tests/unit/test_product_intent_session.py -k "claude or codex" -v` | PASS (22 passed in 6.50s) |
| 10 | 与 #25 的主题内批量交互兼容：可整批明确确认，不要求逐项问答；推荐默认值、只展示例外或用户沉默均不自动批准新增产品意图。复用有来源的既有确认，例外进入待决。 | `claude/meta-skill/tests/unit/test_product_intent_session.py::test_invalid_batch_leaves_prior_authority_unchanged`; `::test_draft_is_provisional_and_resume_only_presents_pending_topics`; `::test_existing_canonical_user_choice_is_reused_without_new_intent_decision` | PASS (2 passed in 0.39s — first cited test; all cited tests run and passed) |
| 11 | 与 #24 的 Node-spec 按需读取兼容：输入声明是下限，不禁止读取额外资料；读取事实不增加产品授权。应用 main 的 2D/2.5D 能力限制披露，不恢复旧路线选择。 | `claude/meta-skill/tests/unit/test_evidence_freshness.py::test_baseline_and_additional_reads_invalidate_without_generated_self_loop` (additional reads become inputs, never authority) | PASS (2 passed — first cited test; all cited tests run and passed) |
| 12 | Claude 与 Codex 的实际入口和生成产物消费同一权威规则；脚本测试不冒充真实宿主测试。 | **none by pytest** — requires real Claude and Codex host runs from a clean context (same condition as #15–#18); pytest parity runs are regression reference only | AWAITS HOST RUN |
| 13 | 基于同步后的当前候选重新验证；历史通过报告仅供回归参考，不直接证明新版本完成。 | **none by pytest** — requires real Claude and Codex host runs from a clean context (same condition as #15–#18); pytest parity runs are regression reference only | AWAITS HOST RUN |

Note: `test_product_intent_session.py::test_invalid_batch_leaves_prior_authority_unchanged` was also run per the plan's Step 1 list — PASS (2 passed in 0.39s) — though it is not cited as a named proof in any row above; it corroborates row 3/6 (invalid batches cannot change authority).

Verdict: KEEP OPEN (criteria 12, 13 await real Claude + Codex host runs; all pytest-provable criteria PASS)
