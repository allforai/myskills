# #9 meta-skill：局部需求确认后进入范围匹配的工作流 — audit 2026-09-11

Tree: main @ 3b195f19

| # | Criterion (verbatim) | Proof | Result |
|---|---|---|---|
| 1 | 同一个 bootstrap 入口按用户目标区分产品重塑、局部需求、新建产品；含糊时仅澄清必要目标，不替用户扩展范围。 | `test_bootstrap_scope.py::test_ambiguous_route_cannot_fall_back_from_existing_code`; `test_bootstrap_scope.py::test_new_and_reconstruction_routes_leave_product_confirmation_pending` | PASS (1 passed in 0.31s); PASS (1 passed in 0.43s) |
| 2 | 对于有代码但没有产品文档的局部功能请求，只分析与任务有关的代码和产品问题，不自动执行全量 reverse-concept。 | `test_bootstrap_scope.py::test_local_request_cannot_gain_whole_product_reverse_node` | PASS (1 passed in 0.27s) |
| 3 | 局部需求的目标、业务规则、验收条件及必要用户决定被记录并可追溯；不全量逆推不等于不建立需求依据。 | `test_bootstrap_scope.py::test_journal_backed_local_requirement_is_consumed_at_all_public_gates`; `test_bootstrap_scope.py::test_requirement_is_an_actual_node_input_not_only_a_coverage_label` | PASS (2 passed in 0.93s); PASS (1 passed in 0.22s) |
| 4 | 已有确认决定按适用范围复用；新增或变化的需求明确确认后进入已有产品基准或局部需求记录，不默认为用户接受。 | `test_bootstrap_scope.py::test_confirmed_local_change_reuses_decision_and_preserves_unrelated_work`; `test_bootstrap_scope.py::test_changed_requirement_requires_new_scoped_confirmation`; `test_bootstrap_scope.py::test_code_derived_confirmed_label_is_not_user_approval` | PASS (12 passed in 3.44s); PASS (1 passed in 0.23s); PASS (1 passed in 0.22s) |
| 5 | 生成的 workflow 与 Node-spec 能表达相关实施、文档和验证责任，并保留无关产品方向和既有工作；不是只输出分类标签。 | `test_bootstrap_scope.py::test_scoped_workflow_needs_documentation_as_well_as_code_and_verification`; `test_product_retained_scope.py::test_product_plan_preserves_unrelated_completed_work_and_provenance` | PASS (1 passed in 0.27s); PASS (6 passed in 3.22s) |
| 6 | 产品重塑与新建产品被路由到各自流程而不冒充已经完成产品确认；本票不以局部路径替代完整产品发现。 | `test_bootstrap_scope.py::test_new_and_reconstruction_routes_leave_product_confirmation_pending` | PASS (1 passed in 0.43s) |
| 7 | 遵守 ADR-0001 的自由规划、Suppress rule 和交互前置，不增加固定通用节点菜单或无人值守访谈。 | `test_bootstrap_scope.py::test_unanswered_local_requirement_blocks_generated_bootstrap`; artefact: `docs/adr/0001-bootstrap-free-planning.md` (the rule) + `claude/meta-skill/knowledge/suppress-rules.md` (no fixed menu row added by the #9 commits — `git log --oneline -- claude/meta-skill/knowledge/suppress-rules.md \| grep -c "#9"` = 0) | PASS (1 passed in 0.21s); artefact count = 0 |
| 8 | 通过 bootstrap 输入／输出行为场景覆盖有文档的局部需求、无文档的局部需求、产品重塑和新项目路由；Claude、Codex 语义一致。复用现有校验与 fixture，不仅断言提示词文本。 | the four `[claude]`/`[codex]` parametrized cases of `test_bootstrap_scope.py` — `python3 -m pytest -q claude/meta-skill/tests/unit/test_bootstrap_scope.py -k "claude or codex" -v \| tail -3` | PASS (142 passed in 58.28s) |

Verdict: CLOSE
