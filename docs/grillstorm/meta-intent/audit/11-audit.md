# #11 meta-skill：产品决定中断续接与旧基准安全接入 — audit 2026-09-11

Tree: main @ 3b195f19

| # | Criterion (verbatim) | Proof | Result |
|---|---|---|---|
| 1 | 在意图讨论中断后重新 bootstrap，已确认决定、理由、调整／删除历史和明确排除范围完整恢复，不重复完整访谈。 | `test_product_intent_resume.py::test_resume_restores_reasons_history_and_explicit_exclusions_without_reasking` | PASS (2 passed in 0.66s) |
| 2 | 未回答的问题保留待决状态；中断或旧文件存在不产生隐式确认。 | `test_product_intent_resume.py::test_resume_raises_legacy_inference_as_missing_confirmation` (as cited by the plan); `test_legacy_profile_authority.py::test_recording_legacy_confirmation_cannot_invent_a_new_consent_source` | UNPROVED → (no issue filed) — first cited test: `no tests ran in 0.05s` (0 collected; that test does not exist in `test_product_intent_resume.py` — it is defined in `test_product_intent_session.py`, where it passes: `2 passed in 0.42s`, but that file/command is not what this ticket's task cites). Second cited test: PASS (4 passed in 0.88s). The plan's proof citation for this criterion names the wrong file, so as commanded here it is not proven. |
| 3 | 旧 concept／baseline 有可信确认记录时按相关范围复用；没有确认来源时标为待核实，只询问本次任务所需缺口。 | `test_legacy_profile_authority.py::test_user_confirmation_recovers_legacy_profile_without_deleting_old_local_file`; `test_legacy_profile_authority.py::test_goal_only_journal_cannot_authorize_hand_projected_scope_and_acceptance` | PASS (2 passed in 2.04s); PASS (2 passed in 0.89s) |
| 4 | 旧基准接入不自动覆盖历史，不因为文档缺确认字段就把局部功能升级为全产品重塑。 | `test_legacy_profile_authority.py::test_mixed_legacy_history_enters_the_session_lifecycle_without_an_interview`; `test_legacy_profile_authority.py::test_legacy_removed_history_resumes_as_removed_not_as_new_work` | PASS (2 passed in 1.85s); PASS (6 passed in 2.87s) |
| 5 | 相关未决依赖保持不可执行，无关工作不会仅因这个问题被失效；显式范围排除与未回答严格区分。 | `test_local_reopen_scope.py::test_reopened_local_intent_blocks_only_its_consumers_until_reconfirm_refreeze_replan`; `test_product_intent_session.py::test_freeze_needs_explicit_scope_and_pending_exclusions` | PASS (4 passed in 4.28s); PASS (4 passed in 0.97s) |
| 6 | 确认在 bootstrap 交互阶段完成，并作为 decision inputs 交给执行；无人值守阶段不新增访谈、不捏造回答，不改造现有人审机制。 | `test_bootstrap_scope.py::test_unanswered_local_requirement_blocks_both_run_preflight_gates`; `test_validate_unattended_readiness.py -k "decision or pending or unanswered"` | PASS (1 passed in 0.24s); PASS (5 passed, 86 deselected in 0.11s) |
| 7 | 用户补齐相关决定后，依赖工作可恢复进入规划／执行，无需重做已完成确认。 | `test_local_reopen_scope.py::test_reopened_local_intent_blocks_only_its_consumers_until_reconfirm_refreeze_replan` (its recovery half) | PASS (4 passed in 4.28s) |
| 8 | 以中断—重入—补齐决定的端到端场景，以及有确认记录／无确认记录的旧基准场景验证；同时检查两端 readiness 结果和用户提问行为，不仅检查字段存在。 | `python3 -m pytest -q claude/meta-skill/tests/unit/test_product_intent_resume.py claude/meta-skill/tests/unit/test_legacy_profile_authority.py -k "claude or codex" -v` | PASS (42 passed in 18.76s) |

Verdict: KEEP OPEN (criterion 2)
