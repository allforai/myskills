# #14 meta-skill：外部代码漂移经用户决策恢复执行 — audit 2026-09-11

Tree: main @ 3b195f19

| # | Criterion (verbatim) | Proof | Result |
|---|---|---|---|
| 1 | 再次 bootstrap／续跑能发现外部源码变化并说明相关事实、产品决定、文档、任务与验收的影响，不要求后台持续监控。 | `tests/unit/test_external_change_recovery.py::test_external_implementation_change_is_reported_with_its_impact` | PASS (2 passed in 1.55s) |
| 2 | 经核实仅为实现层变化时增量更新事实文档；产品行为变化或语义影响不明确时展示冲突，不能自动把代码行为写成需求。 | `tests/unit/test_external_change_recovery.py::test_implementation_only_drift_keeps_its_node_owner_at_the_same_gates`; `::test_external_product_behavior_change_is_a_conflict_not_a_new_requirement`; `::test_unmapped_external_change_is_reported_as_uncertain_impact` | PASS (2 passed in 2.07s); PASS (2 passed in 2.04s); PASS (2 passed in 2.19s) |
| 3 | 接受变化：记录用户决定及理由，更新产品基准版本，传播影响、协调任务和文档、重验并恢复相关执行。 | `tests/unit/test_external_change_recovery.py::test_accepting_an_external_change_records_the_decision_and_recovers_execution`; `::test_an_accepted_change_recovers_once_its_required_document_is_synchronized` | PASS (2 passed in 3.19s); PASS (2 passed in 2.97s) |
| 4 | 拒绝变化：保留确认基准，形成范围明确的实现修复任务，修复后同步文档、重新验收并恢复执行。 | `tests/unit/test_external_change_recovery.py::test_rejecting_an_external_change_keeps_the_baseline_and_scopes_the_repair`; `::test_a_rejected_change_survives_the_next_baseline_freeze` | PASS (2 passed in 2.83s); PASS (2 passed in 2.60s) |
| 5 | 暂不决定或交互中断：保留冲突和上下文，使依赖该决定的工作受阻；无关工作不因而被全量重置。 | `tests/unit/test_external_change_recovery.py::test_deferred_conflict_holds_only_dependent_work_and_resumes_without_rebuilding`; `::test_a_deferred_change_keeps_its_hold_and_its_context_while_other_source_moves` | PASS (2 passed in 3.22s); PASS (2 passed in 1.89s) |
| 6 | 无人值守执行遇到未决冲突时不发起产品访谈、不假定接受变化；用户返回交互入口解决后能够接续，而非从头重建。 | `tests/unit/test_external_change_recovery.py::test_a_gate_never_runs_project_acceptance_over_an_out_of_flow_edit`; `::test_deferred_conflict_holds_only_dependent_work_and_resumes_without_rebuilding` (resumes-without-rebuilding half) | PASS (2 passed in 2.49s); PASS (2 passed in 3.22s) |
| 7 | 复用流程内同步／完成门槛，而不是另造外部修改专用验收体系；完成须同时满足可追溯决定、当前实现符合有效基准、相关文档同步、相关证据有效。 | `tests/unit/test_external_change_recovery.py::test_an_accepted_change_recovers_once_its_required_document_is_synchronized` (goes through the #13 document gate, no separate system); `::test_a_classification_is_not_reused_once_the_source_it_was_established_against_moves` | PASS (2 passed in 2.97s); PASS (2 passed in 2.43s) |
| 8 | 通过外部实现变化、接受产品变化、拒绝后修复、暂缓后恢复四类 bootstrap／续跑场景验证；相同输入重复运行稳定，Claude／Codex 一致。 | the four scenario tests in rows 1, 3, 4, 5 (all PASS above); parity: `python3 -m pytest -q claude/meta-skill/tests/unit/test_external_change_recovery.py -k "claude or codex" -v \| tail -3` | PASS (42 passed in 47.59s) |
| 9 | 使用现有测试 fixture 和校验边界完成集成验证，保留 ADR-0001 自由规划与交互前置、ADR-0002 的视觉评审及产物权威规则。 | artefact: `git log --oneline -- docs/adr/0001-bootstrap-free-planning.md docs/adr/0002-dual-independent-visual-review.md` — no commit under #14 touches either ADR | PASS — log shows only `42531648 Split bootstrap.md into planning protocols (ADR-0001).` and `06b2e036 Record ADR-0002: dual independent visual review.`; neither commit message references #14 (`grep -c "#14"` = 0) |

Note: every cited test in `test_external_change_recovery.py` is `host`-parametrized (claude/codex), so each single-test invocation above reports `2 passed` rather than `1 passed` — both host variants ran and passed, which is the same evidence the plan's "Expected: … each `1 passed`" line anticipated in unparametrized form, and it is what proves criterion 8's Claude/Codex-parity clause.

Verdict: CLOSE
