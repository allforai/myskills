# meta-intent Ticket Audit (#9–#14) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close #9–#14 honestly — for every acceptance criterion on each ticket, name the test (or recorded evidence) on `main` that proves it, run that test, and either close the ticket with the proof or reopen the specific criterion as a defect.

**Architecture:** The six implementation tickets under #8 were merged by another session (ADR-0004..0007, `product_intent.py`, `evidence_freshness.py`, `repair_authorization.py`, …) but never closed against their criteria. This plan is an **audit, not implementation**: each task builds one criterion→proof map as a committed Markdown file, runs the cited tests, and closes the ticket. A criterion with no proving test becomes a new defect ticket, never a hand-wave. No product code changes; the only files created are the six audit records and, where a criterion is provable but untested, one added test.

**Tech Stack:** pytest (`claude/meta-skill/tests/unit`), `gh` CLI, Markdown.

**Spec:** GitHub issues #9, #10, #11, #12, #13, #14 (parent #8). Their "Acceptance criteria" sections are the spec; each task quotes them verbatim.

## Global Constraints

- **Out of scope:** #15–#18. Their closure conditions require real Claude and Codex host execution from a clean context with the evaluator holding criteria privately ("脚本测试不冒充真实宿主测试"; T15's own evaluation says "Not a host pass … stay `unverified`"). They are a separate plan needing the Codex CLI.
- Audit records live at `docs/grillstorm/meta-intent/audit/<ticket>-audit.md`, one per ticket, committed with the ticket's closure.
- A criterion is **proved** only by a test that fails when the behaviour is removed, or by a recorded artefact on `main`; "the prompt mentions it" or "the file exists" is not proof (the tickets say so).
- Each cited test must actually be run in the task (`python3 -m pytest -q <file>::<test> -v`) and PASS; paste the one-line result into the audit record.
- Suites run per directory. The meta-skill unit suite takes ~5 min; run only the named tests per task, and the whole `claude/meta-skill/tests/unit` once in Task 7.
- Never stage `docs/feedback/inbox/`.
- Commit messages: write to a file under the worktree and commit with `-F`. Trailer on every commit:
  ```
  Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
  ```
- Closing a ticket: `gh issue close <n> --comment-file <audit-record>` so the proof travels with the closure. A ticket with any **unproved** criterion is **not** closed; instead file one defect issue per unproved criterion (label `needs-triage`), comment the audit record on the ticket, and leave it open.

---

## File Structure

| File | Responsibility |
|---|---|
| `docs/grillstorm/meta-intent/audit/README.md` | The audit-record format (Task 1) |
| `docs/grillstorm/meta-intent/audit/09-audit.md` … `14-audit.md` | One criterion→proof table per ticket (Tasks 1–6) |
| `claude/meta-skill/tests/unit/test_*.py` | Existing proving tests; modified only if a provable criterion has no test (rare; say so in the record) |

Audit-record format (every record uses exactly this table):

```markdown
# #<n> <title> — audit <YYYY-MM-DD>

Tree: main @ <short-sha>

| # | Criterion (verbatim) | Proof | Result |
|---|---|---|---|
| 1 | <quoted criterion> | `tests/unit/<file>.py::<test>` | PASS (1 passed in 0.9s) |
| 2 | <quoted criterion> | artefact: `<path>` — <one line what it shows> | PASS |
| 3 | <quoted criterion> | **none** | UNPROVED → #<defect> |

Verdict: CLOSE | KEEP OPEN (criteria 3)
```

---

### Task 1: Audit-record format and #9 (局部需求确认后进入范围匹配的工作流)

**Files:**
- Create: `docs/grillstorm/meta-intent/audit/README.md`
- Create: `docs/grillstorm/meta-intent/audit/09-audit.md`
- Test (run only): `claude/meta-skill/tests/unit/test_bootstrap_scope.py`, `test_local_reopen_scope.py`, `test_product_retained_scope.py`

**Interfaces:**
- Produces: the record format above (README) and the convention every later task copies — `Tree: main @ <sha>` from `git rev-parse --short HEAD`, one pytest run per cited test, results pasted verbatim.

- [ ] **Step 1: Write the README**

`docs/grillstorm/meta-intent/audit/README.md`:

```markdown
# meta-intent ticket audits

One record per ticket under #8, produced when the ticket was closed against its acceptance
criteria on `main`. A criterion is proved only by a test that fails when the behaviour is
removed, or by a recorded artefact; a prompt sentence or a file's existence proves nothing.
Every cited test was run at the recorded tree and its one-line result pasted. A criterion with
no proof is UNPROVED and points at the defect issue filed for it; a ticket with any UNPROVED
criterion stays open.

Records: `09-audit.md` … `14-audit.md`. #15–#18 (thought tests) are not here: they need real
Claude and Codex host runs and have their own plan.
```

- [ ] **Step 2: Map #9's eight criteria to tests**

Run these, one at a time, and capture each one-line result:

```bash
T=claude/meta-skill/tests/unit
python3 -m pytest -q $T/test_bootstrap_scope.py::test_ambiguous_route_cannot_fall_back_from_existing_code -v
python3 -m pytest -q $T/test_bootstrap_scope.py::test_local_request_cannot_gain_whole_product_reverse_node -v
python3 -m pytest -q $T/test_bootstrap_scope.py::test_journal_backed_local_requirement_is_consumed_at_all_public_gates -v
python3 -m pytest -q $T/test_bootstrap_scope.py::test_unanswered_local_requirement_blocks_generated_bootstrap -v
python3 -m pytest -q $T/test_bootstrap_scope.py::test_confirmed_local_change_reuses_decision_and_preserves_unrelated_work -v
python3 -m pytest -q $T/test_bootstrap_scope.py::test_changed_requirement_requires_new_scoped_confirmation -v
python3 -m pytest -q $T/test_bootstrap_scope.py::test_scoped_workflow_needs_documentation_as_well_as_code_and_verification -v
python3 -m pytest -q $T/test_bootstrap_scope.py::test_requirement_is_an_actual_node_input_not_only_a_coverage_label -v
python3 -m pytest -q $T/test_bootstrap_scope.py::test_new_and_reconstruction_routes_leave_product_confirmation_pending -v
python3 -m pytest -q $T/test_bootstrap_scope.py::test_code_derived_confirmed_label_is_not_user_approval -v
```

Expected: every line ends `1 passed`. If one FAILS, that is a regression on `main`: stop, record it as UNPROVED with the failure text, and file the defect (Step 4).

- [ ] **Step 3: Write `09-audit.md`**

Fill the table with these rows (criterion text verbatim from the ticket; proof column as below; result column from Step 2):

| # | Criterion | Proof |
|---|---|---|
| 1 | 同一个 bootstrap 入口按用户目标区分产品重塑、局部需求、新建产品；含糊时仅澄清必要目标，不替用户扩展范围。 | `test_ambiguous_route_cannot_fall_back_from_existing_code`; `test_new_and_reconstruction_routes_leave_product_confirmation_pending` |
| 2 | 对于有代码但没有产品文档的局部功能请求，只分析与任务有关的代码和产品问题，不自动执行全量 reverse-concept。 | `test_local_request_cannot_gain_whole_product_reverse_node` |
| 3 | 局部需求的目标、业务规则、验收条件及必要用户决定被记录并可追溯；不全量逆推不等于不建立需求依据。 | `test_journal_backed_local_requirement_is_consumed_at_all_public_gates`; `test_requirement_is_an_actual_node_input_not_only_a_coverage_label` |
| 4 | 已有确认决定按适用范围复用；新增或变化的需求明确确认后进入已有产品基准或局部需求记录，不默认为用户接受。 | `test_confirmed_local_change_reuses_decision_and_preserves_unrelated_work`; `test_changed_requirement_requires_new_scoped_confirmation`; `test_code_derived_confirmed_label_is_not_user_approval` |
| 5 | 生成的 workflow 与 Node-spec 能表达相关实施、文档和验证责任，并保留无关产品方向和既有工作；不是只输出分类标签。 | `test_scoped_workflow_needs_documentation_as_well_as_code_and_verification`; `test_product_retained_scope.py::test_product_plan_preserves_unrelated_completed_work_and_provenance` |
| 6 | 产品重塑与新建产品被路由到各自流程而不冒充已经完成产品确认；本票不以局部路径替代完整产品发现。 | `test_new_and_reconstruction_routes_leave_product_confirmation_pending` |
| 7 | 遵守 ADR-0001 的自由规划、Suppress rule 和交互前置，不增加固定通用节点菜单或无人值守访谈。 | `test_unanswered_local_requirement_blocks_generated_bootstrap`; artefact: `docs/adr/0001-bootstrap-free-planning.md` (the rule) + `claude/meta-skill/knowledge/suppress-rules.md` (no fixed menu row added by the #9 commits — verify with `git log --oneline -- claude/meta-skill/knowledge/suppress-rules.md \| grep -c "#9"` = 0) |
| 8 | 通过 bootstrap 输入／输出行为场景覆盖有文档的局部需求、无文档的局部需求、产品重塑和新项目路由；Claude、Codex 语义一致。复用现有校验与 fixture，不仅断言提示词文本。 | the four `[claude]`/`[codex]` parametrized cases of `test_bootstrap_scope.py` — run `python3 -m pytest -q $T/test_bootstrap_scope.py -k "claude or codex" -v \| tail -3` and paste the count |

Criterion 8's Codex-parity proof is the parametrization itself; if `-k "claude or codex"` selects zero tests, the file is not host-parametrized and criterion 8 is UNPROVED (file a defect: "#9 criterion 8: bootstrap scope tests are not host-parametrized").

- [ ] **Step 4: Decide, close or file**

If every row is PASS: 

```bash
gh issue close 9 --comment-file docs/grillstorm/meta-intent/audit/09-audit.md
```

If any row is UNPROVED: for each, `gh issue create --title "#9 criterion <k>: <short>" --label needs-triage --body "<the row + failure text>"`, write its number into the row, then `gh issue comment 9 --body-file docs/grillstorm/meta-intent/audit/09-audit.md` and leave #9 open.

- [ ] **Step 5: Commit**

```bash
cat > /tmp/audit09.txt <<'EOF'
meta-intent audit: #9 局部需求路由 — criteria mapped to proving tests and closed

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add docs/grillstorm/meta-intent/audit/README.md docs/grillstorm/meta-intent/audit/09-audit.md
git commit -q -F /tmp/audit09.txt
```

---

### Task 2: #10 (产品意图初稿经用户重塑后驱动完整流程)

**Files:**
- Create: `docs/grillstorm/meta-intent/audit/10-audit.md`
- Test (run only): `test_product_intent_session.py`, `test_intent_review_corrections.py`, `test_product_question_identity.py`, `test_freeze_idempotence.py`

**Interfaces:**
- Consumes: the record format from Task 1.

- [ ] **Step 1: Run the proving tests**

```bash
T=claude/meta-skill/tests/unit
python3 -m pytest -q $T/test_product_intent_session.py::test_draft_is_provisional_and_resume_only_presents_pending_topics -v
python3 -m pytest -q $T/test_product_intent_session.py::test_four_explicit_operations_preserve_history_and_user_additions -v
python3 -m pytest -q $T/test_product_intent_session.py::test_missing_dimensions_are_pending_gaps_and_bad_evidence_is_rejected -v
python3 -m pytest -q $T/test_product_intent_session.py::test_pending_dependency_cannot_be_excluded_to_authorize_dependent_intent -v
python3 -m pytest -q $T/test_product_intent_session.py::test_freeze_needs_explicit_scope_and_pending_exclusions -v
python3 -m pytest -q $T/test_product_intent_session.py::test_existing_canonical_user_choice_is_reused_without_new_intent_decision -v
python3 -m pytest -q $T/test_product_intent_session.py::test_revised_baseline_generates_full_applicable_plan_and_gates_reject_drift -v
python3 -m pytest -q $T/test_product_intent_session.py::test_invalid_batch_leaves_prior_authority_unchanged -v
python3 -m pytest -q $T/test_freeze_idempotence.py::test_changed_product_selection_freezes_a_new_version_and_invalidates_the_plan -v
python3 -m pytest -q $T/test_intent_review_corrections.py -v | tail -2
python3 -m pytest -q $T/test_product_question_identity.py -v | tail -2
```

Expected: every single test `1 passed`; the two file runs end `5 passed` and `4 passed`.

- [ ] **Step 2: Write `10-audit.md`**

| # | Criterion | Proof |
|---|---|---|
| 1 | 初稿包含目标用户、场景、核心问题、价值主张、业务闭环和取舍；代码事实、推断意图、未知项明确区分，推断附证据和不确定性。 | `test_missing_dimensions_are_pending_gaps_and_bad_evidence_is_rejected` |
| 2 | 高置信度或充分代码证据不能替代用户确认；初稿和 product-summary 不自动升级为已批准产品基准。 | `test_draft_is_provisional_and_resume_only_presents_pending_topics`; `test_bootstrap_scope.py::test_code_derived_confirmed_label_is_not_user_approval` |
| 3 | 用户能确认、补充、调整、删除意图；新增意图可以没有代码实现依据，其依据是用户需求和决定。 | `test_four_explicit_operations_preserve_history_and_user_additions` |
| 4 | 意图具有稳定身份、来源、决定理由及确认信息；调整保留前后关联，删除保留历史，不在讨论阶段删除或改动产品代码。 | `test_product_question_identity.py` (4 tests); `test_four_explicit_operations_preserve_history_and_user_additions` (history); "不改动产品代码" — `test_intent_review_corrections.py` (5 tests) |
| 5 | 按主题讨论，主动指出矛盾和产品空白；不是仅询问是否认可现状，也不是固定长问卷。 | `test_draft_is_provisional_and_resume_only_presents_pending_topics` (topics, not a questionnaire); `test_missing_dimensions_are_pending_gaps_and_bad_evidence_is_rejected` (gaps surfaced) |
| 6 | 明确确认基准的范围和版本；未决问题不能通过沉默自动确认，排除范围必须显式决定，依赖未决决定的工作不能被声明可执行。 | `test_freeze_needs_explicit_scope_and_pending_exclusions`; `test_pending_dependency_cannot_be_excluded_to_authorize_dependent_intent` |
| 7 | 产品基准整合复用现有 product-concept 与 decision journal 责任，不另造并行事实源；新项目从用户意图出发并进入相同确认合同。 | `test_existing_canonical_user_choice_is_reused_without_new_intent_decision`; `test_bootstrap_scope.py::test_new_and_reconstruction_routes_leave_product_confirmation_pending` |
| 8 | 确认后，生成的 workflow、Node-spec 和验收条件体现新基准的增加、调整和删除，执行适用的完整流程；不以旧代码功能清单为验收真相，也不强制每个 Capability 都运行。 | `test_revised_baseline_generates_full_applicable_plan_and_gates_reject_drift`; `test_freeze_idempotence.py::test_changed_product_selection_freezes_a_new_version_and_invalidates_the_plan` |
| 9 | 通过脚本化用户响应的 bootstrap 场景验证四种操作、无代码依据的新增意图、未决阻塞、新产品路径和讨论不改代码；Claude、Codex 一致。 | `python3 -m pytest -q $T/test_product_intent_session.py -k "claude or codex" -v \| tail -3` — paste count; zero selected ⇒ UNPROVED |

- [ ] **Step 3: Decide, close or file** — same rule as Task 1 Step 4, ticket 10, record `10-audit.md`.

- [ ] **Step 4: Commit**

```bash
cat > /tmp/audit10.txt <<'EOF'
meta-intent audit: #10 产品意图重塑 — criteria mapped to proving tests and closed

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add docs/grillstorm/meta-intent/audit/10-audit.md
git commit -q -F /tmp/audit10.txt
```

---

### Task 3: #11 (产品决定中断续接与旧基准安全接入)

**Files:**
- Create: `docs/grillstorm/meta-intent/audit/11-audit.md`
- Test (run only): `test_product_intent_resume.py`, `test_legacy_profile_authority.py`, `test_validate_unattended_readiness.py`

- [ ] **Step 1: Run the proving tests**

```bash
T=claude/meta-skill/tests/unit
python3 -m pytest -q $T/test_product_intent_resume.py::test_resume_restores_reasons_history_and_explicit_exclusions_without_reasking -v
python3 -m pytest -q $T/test_product_intent_resume.py::test_resume_raises_legacy_inference_as_missing_confirmation -v
python3 -m pytest -q $T/test_legacy_profile_authority.py::test_goal_only_journal_cannot_authorize_hand_projected_scope_and_acceptance -v
python3 -m pytest -q $T/test_legacy_profile_authority.py::test_user_confirmation_recovers_legacy_profile_without_deleting_old_local_file -v
python3 -m pytest -q $T/test_legacy_profile_authority.py::test_mixed_legacy_history_enters_the_session_lifecycle_without_an_interview -v
python3 -m pytest -q $T/test_legacy_profile_authority.py::test_recording_legacy_confirmation_cannot_invent_a_new_consent_source -v
python3 -m pytest -q $T/test_legacy_profile_authority.py::test_legacy_removed_history_resumes_as_removed_not_as_new_work -v
python3 -m pytest -q $T/test_bootstrap_scope.py::test_unanswered_local_requirement_blocks_both_run_preflight_gates -v
python3 -m pytest -q $T/test_local_reopen_scope.py::test_reopened_local_intent_blocks_only_its_consumers_until_reconfirm_refreeze_replan -v
python3 -m pytest -q $T/test_validate_unattended_readiness.py -k "decision or pending or unanswered" -v | tail -3
```

Expected: single tests `1 passed`; the readiness `-k` run selects ≥1 and all pass.

- [ ] **Step 2: Write `11-audit.md`**

| # | Criterion | Proof |
|---|---|---|
| 1 | 在意图讨论中断后重新 bootstrap，已确认决定、理由、调整／删除历史和明确排除范围完整恢复，不重复完整访谈。 | `test_resume_restores_reasons_history_and_explicit_exclusions_without_reasking` |
| 2 | 未回答的问题保留待决状态；中断或旧文件存在不产生隐式确认。 | `test_resume_raises_legacy_inference_as_missing_confirmation`; `test_recording_legacy_confirmation_cannot_invent_a_new_consent_source` |
| 3 | 旧 concept／baseline 有可信确认记录时按相关范围复用；没有确认来源时标为待核实，只询问本次任务所需缺口。 | `test_user_confirmation_recovers_legacy_profile_without_deleting_old_local_file`; `test_goal_only_journal_cannot_authorize_hand_projected_scope_and_acceptance` |
| 4 | 旧基准接入不自动覆盖历史，不因为文档缺确认字段就把局部功能升级为全产品重塑。 | `test_mixed_legacy_history_enters_the_session_lifecycle_without_an_interview`; `test_legacy_removed_history_resumes_as_removed_not_as_new_work` |
| 5 | 相关未决依赖保持不可执行，无关工作不会仅因这个问题被失效；显式范围排除与未回答严格区分。 | `test_reopened_local_intent_blocks_only_its_consumers_until_reconfirm_refreeze_replan`; `test_product_intent_session.py::test_freeze_needs_explicit_scope_and_pending_exclusions` |
| 6 | 确认在 bootstrap 交互阶段完成，并作为 decision inputs 交给执行；无人值守阶段不新增访谈、不捏造回答，不改造现有人审机制。 | `test_unanswered_local_requirement_blocks_both_run_preflight_gates`; the readiness `-k` run |
| 7 | 用户补齐相关决定后，依赖工作可恢复进入规划／执行，无需重做已完成确认。 | `test_reopened_local_intent_blocks_only_its_consumers_until_reconfirm_refreeze_replan` (its recovery half) |
| 8 | 以中断—重入—补齐决定的端到端场景，以及有确认记录／无确认记录的旧基准场景验证；同时检查两端 readiness 结果和用户提问行为，不仅检查字段存在。 | `python3 -m pytest -q $T/test_product_intent_resume.py $T/test_legacy_profile_authority.py -k "claude or codex" -v \| tail -3` — paste count; zero ⇒ UNPROVED |

- [ ] **Step 3: Decide, close or file** — Task 1 Step 4 rule, ticket 11.

- [ ] **Step 4: Commit**

```bash
cat > /tmp/audit11.txt <<'EOF'
meta-intent audit: #11 中断续接与旧基准 — criteria mapped to proving tests and closed

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add docs/grillstorm/meta-intent/audit/11-audit.md
git commit -q -F /tmp/audit11.txt
```

---

### Task 4: #12 (源码与产品基准变化触发精准证据失效)

**Files:**
- Create: `docs/grillstorm/meta-intent/audit/12-audit.md`
- Test (run only): `test_evidence_freshness.py`, `test_freshness_downgrade.py`, `test_freeze_idempotence.py`, `test_check_artifacts.py`

- [ ] **Step 1: Run the proving tests**

```bash
T=claude/meta-skill/tests/unit
python3 -m pytest -q $T/test_evidence_freshness.py::test_observe_a_change_b_rejects_publication_until_b_is_reverified -v
python3 -m pytest -q $T/test_evidence_freshness.py::test_source_drift_propagates_through_resume_and_both_gates_preserving_other_branch -v
python3 -m pytest -q $T/test_evidence_freshness.py::test_unknown_source_impact_and_output_tampering_cannot_prove_completion -v
python3 -m pytest -q $T/test_evidence_freshness.py::test_baseline_and_additional_reads_invalidate_without_generated_self_loop -v
python3 -m pytest -q $T/test_evidence_freshness.py::test_baseline_scope_changes_and_artifact_dependencies_invalidate_transitively -v
python3 -m pytest -q $T/test_evidence_freshness.py::test_glob_membership_and_missing_dependency_declarations_are_not_zero_impact -v
python3 -m pytest -q $T/test_freshness_downgrade.py::test_removing_source_inputs_from_a_published_completed_node_cannot_admit_stale_evidence -v
python3 -m pytest -q $T/test_freshness_downgrade.py::test_corrupt_or_unknown_freshness_record_fails_closed_for_every_node -v
python3 -m pytest -q $T/test_freeze_idempotence.py::test_identical_product_refreeze_converges_without_new_journal_version_or_replan -v
python3 -m pytest -q $T/test_freeze_idempotence.py::test_tampered_previous_scope_is_not_reused_as_the_identical_freeze -v
python3 -m pytest -q shared/evidence-engine/test_identity.py -v | tail -2
```

Expected: single tests `1 passed`; engine identity file all pass (it holds "two different uncommitted states on one commit produce different builds").

- [ ] **Step 2: Write `12-audit.md`**

| # | Criterion | Proof |
|---|---|---|
| 1 | 文档、执行合同和验收证据能追溯到所使用的产品源码状态、已确认产品基准版本和相关输入依赖。 | `test_observe_a_change_b_rejects_publication_until_b_is_reverified` (`snapshot()` binds files, requirements, baseline_scope, upstream) |
| 2 | 同一提交上两次不同未提交改动可区分；不能仅用 commit 加 dirty 布尔值、文件存在或修改时间判定有效性。 | `shared/evidence-engine/test_identity.py` (whole-tree identity: commit + snapshot digest); `test_unknown_source_impact_and_output_tampering_cannot_prove_completion` (mtime / copy tampering refused) |
| 3 | 源码变化与产品基准变化都触发影响分析，覆盖直接和传递依赖；相关旧文档／任务／验收被明确标为需要协调或过期。 | `test_source_drift_propagates_through_resume_and_both_gates_preserving_other_branch`; `test_baseline_scope_changes_and_artifact_dependencies_invalidate_transitively` |
| 4 | 无关分支及其有效成果保留，不以全量重建替代影响判断；无法确定影响时明确记录不确定性，不能视为零影响。 | `…preserving_other_branch` (same test); `test_glob_membership_and_missing_dependency_declarations_are_not_zero_impact` |
| 5 | 区分产品输入与生成文档、运行记录、报告等产物；同步生成物本身不导致无止境的再次同步和自我失效。 | `test_baseline_and_additional_reads_invalidate_without_generated_self_loop` |
| 6 | 相同输入再次 bootstrap／续跑时，不生成重复产品决定、不重复规划、不改变已有效的验收状态。 | `test_identical_product_refreeze_converges_without_new_journal_version_or_replan`; `test_tampered_previous_scope_is_not_reused_as_the_identical_freeze` |
| 7 | 完成检查和执行就绪结果消费这些失效状态，过期证据不能继续证明相关任务完成；本票可通过单独改动输入并重跑检查演示。 | `test_removing_source_inputs_from_a_published_completed_node_cannot_admit_stale_evidence`; `test_corrupt_or_unknown_freshness_record_fails_closed_for_every_node` |
| 8 | 复用现有 workflow reconciliation、artifact gate 与 readiness 边界；测试源码单点变化、基准变化、不同 dirty 快照、依赖传播、无关保留及重复检查，Claude／Codex 一致。 | `python3 -m pytest -q $T/test_evidence_freshness.py -k "claude or codex" -v \| tail -3` (the file is `host`-parametrized — every test above ran under both) — paste count |

- [ ] **Step 3: Decide, close or file** — Task 1 Step 4 rule, ticket 12.

- [ ] **Step 4: Commit**

```bash
cat > /tmp/audit12.txt <<'EOF'
meta-intent audit: #12 精准证据失效 — criteria mapped to proving tests and closed

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add docs/grillstorm/meta-intent/audit/12-audit.md
git commit -q -F /tmp/audit12.txt
```

---

### Task 5: #13 (流程内实现与文档同步后才能完成)

**Files:**
- Create: `docs/grillstorm/meta-intent/audit/13-audit.md`
- Test (run only): `test_delivery_closure.py`, `test_external_change_recovery.py`, `test_run_policy_session.py`

- [ ] **Step 1: Run the proving tests**

```bash
T=claude/meta-skill/tests/unit
python3 -m pytest -q $T/test_delivery_closure.py::test_local_feature_closure_refuses_inconsistency_and_recovers -v
python3 -m pytest -q $T/test_delivery_closure.py::test_required_document_without_verification_is_refused_at_every_gate -v
python3 -m pytest -q $T/test_delivery_closure.py::test_document_verification_must_match_the_node_spec -v
python3 -m pytest -q $T/test_delivery_closure.py::test_document_check_that_changes_inputs_cannot_publish_proof_for_the_old_state -v
python3 -m pytest -q $T/test_delivery_closure.py::test_accepted_with_gaps_is_a_qualified_run_outcome_not_completion -v
python3 -m pytest -q $T/test_external_change_recovery.py::test_a_verified_fact_update_survives_synchronizing_the_document_it_requires -v
python3 -m pytest -q $T/test_external_change_recovery.py::test_a_revised_confirmed_intent_supersedes_the_earlier_decision -v
python3 -m pytest -q $T/test_external_change_recovery.py::test_drift_reaches_the_gates_as_unverified_and_verification_routes_it_to_its_owner -v
python3 -m pytest -q $T/test_run_policy_session.py -k "unattended or interview or decision" -v | tail -3
```

Expected: single tests `1 passed`; the run-policy `-k` run selects ≥1 and all pass.

- [ ] **Step 2: Write `13-audit.md`**

| # | Criterion | Proof |
|---|---|---|
| 1 | 规划阶段识别相关事实文档、产品决定、Node-spec／依赖和验证责任，局部改动不要求重新 bootstrap 整个产品。 | `test_bootstrap_scope.py::test_scoped_workflow_needs_documentation_as_well_as_code_and_verification`; `test_local_reopen_scope.py::test_reopened_local_intent_blocks_only_its_consumers_until_reconfirm_refreeze_replan` |
| 2 | 实施后按实际代码更新接口、模块行为、实现状态等事实及其证据，协调受影响工作流和 Node-spec，保留历史。 | `test_a_verified_fact_update_survives_synchronizing_the_document_it_requires` |
| 3 | 已批准的产品变化按记录同步到基准；实现不能自行覆盖用户意图，也不重复询问已有且仍适用的决定。 | `test_a_revised_confirmed_intent_supersedes_the_earlier_decision`; `test_product_intent_session.py::test_existing_canonical_user_choice_is_reused_without_new_intent_decision` |
| 4 | 产品源码、确认基准、必需文档或验收证据任一不一致时，相关任务不能标记完成，即使代码构建或测试局部通过。 | `test_local_feature_closure_refuses_inconsistency_and_recovers`; `test_required_document_without_verification_is_refused_at_every_gate` |
| 5 | 不一致形成明确差异与修复责任，回到责任任务修复后重新同步并重验，不能只写一条警告便宣称闭环。 | `test_drift_reaches_the_gates_as_unverified_and_verification_routes_it_to_its_owner`; `test_document_verification_must_match_the_node_spec` |
| 6 | 未知产品决定不能由无人值守执行补造；相关工作报告受阻并交回交互阶段处理，遵守已有有限重试与失败报告机制。 | the run-policy `-k` run; `test_bootstrap_scope.py::test_unanswered_local_requirement_blocks_both_run_preflight_gates` |
| 7 | 修复完成后，新证据绑定当前输入并恢复相关完成状态，无关工作保持有效。 | `test_local_feature_closure_refuses_inconsistency_and_recovers` (recovery half); `test_document_check_that_changes_inputs_cannot_publish_proof_for_the_old_state` |
| 8 | 用完整局部功能 fixture 验证文档遗漏拒绝完成、纠正后通过、已批准产品变化传播，以及受阻后恢复；两端使用相同产品权威规则和外部行为判据。 | `python3 -m pytest -q $T/test_delivery_closure.py -k "claude or codex" -v \| tail -3` — paste count; zero ⇒ UNPROVED |

- [ ] **Step 3: Decide, close or file** — Task 1 Step 4 rule, ticket 13.

- [ ] **Step 4: Commit**

```bash
cat > /tmp/audit13.txt <<'EOF'
meta-intent audit: #13 实现与文档同步 — criteria mapped to proving tests and closed

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add docs/grillstorm/meta-intent/audit/13-audit.md
git commit -q -F /tmp/audit13.txt
```

---

### Task 6: #14 (外部代码漂移经用户决策恢复执行)

**Files:**
- Create: `docs/grillstorm/meta-intent/audit/14-audit.md`
- Test (run only): `test_external_change_recovery.py`

- [ ] **Step 1: Run the proving tests**

```bash
T=claude/meta-skill/tests/unit
for t in test_external_implementation_change_is_reported_with_its_impact \
         test_external_product_behavior_change_is_a_conflict_not_a_new_requirement \
         test_accepting_an_external_change_records_the_decision_and_recovers_execution \
         test_rejecting_an_external_change_keeps_the_baseline_and_scopes_the_repair \
         test_deferred_conflict_holds_only_dependent_work_and_resumes_without_rebuilding \
         test_unmapped_external_change_is_reported_as_uncertain_impact \
         test_a_rejected_change_survives_the_next_baseline_freeze \
         test_implementation_only_drift_keeps_its_node_owner_at_the_same_gates \
         test_a_gate_never_runs_project_acceptance_over_an_out_of_flow_edit \
         test_an_accepted_change_recovers_once_its_required_document_is_synchronized \
         test_a_deferred_change_keeps_its_hold_and_its_context_while_other_source_moves \
         test_a_classification_is_not_reused_once_the_source_it_was_established_against_moves; do
  python3 -m pytest -q "$T/test_external_change_recovery.py::$t" -v | tail -1
done
```

Expected: twelve lines, each `1 passed`.

- [ ] **Step 2: Write `14-audit.md`**

| # | Criterion | Proof |
|---|---|---|
| 1 | 再次 bootstrap／续跑能发现外部源码变化并说明相关事实、产品决定、文档、任务与验收的影响，不要求后台持续监控。 | `test_external_implementation_change_is_reported_with_its_impact` |
| 2 | 经核实仅为实现层变化时增量更新事实文档；产品行为变化或语义影响不明确时展示冲突，不能自动把代码行为写成需求。 | `test_implementation_only_drift_keeps_its_node_owner_at_the_same_gates`; `test_external_product_behavior_change_is_a_conflict_not_a_new_requirement`; `test_unmapped_external_change_is_reported_as_uncertain_impact` |
| 3 | 接受变化：记录用户决定及理由，更新产品基准版本，传播影响、协调任务和文档、重验并恢复相关执行。 | `test_accepting_an_external_change_records_the_decision_and_recovers_execution`; `test_an_accepted_change_recovers_once_its_required_document_is_synchronized` |
| 4 | 拒绝变化：保留确认基准，形成范围明确的实现修复任务，修复后同步文档、重新验收并恢复执行。 | `test_rejecting_an_external_change_keeps_the_baseline_and_scopes_the_repair`; `test_a_rejected_change_survives_the_next_baseline_freeze` |
| 5 | 暂不决定或交互中断：保留冲突和上下文，使依赖该决定的工作受阻；无关工作不因而被全量重置。 | `test_deferred_conflict_holds_only_dependent_work_and_resumes_without_rebuilding`; `test_a_deferred_change_keeps_its_hold_and_its_context_while_other_source_moves` |
| 6 | 无人值守执行遇到未决冲突时不发起产品访谈、不假定接受变化；用户返回交互入口解决后能够接续，而非从头重建。 | `test_a_gate_never_runs_project_acceptance_over_an_out_of_flow_edit`; `…resumes_without_rebuilding` |
| 7 | 复用流程内同步／完成门槛，而不是另造外部修改专用验收体系；完成须同时满足可追溯决定、当前实现符合有效基准、相关文档同步、相关证据有效。 | `test_an_accepted_change_recovers_once_its_required_document_is_synchronized` (goes through the #13 document gate, no separate system); `test_a_classification_is_not_reused_once_the_source_it_was_established_against_moves` |
| 8 | 通过外部实现变化、接受产品变化、拒绝后修复、暂缓后恢复四类 bootstrap／续跑场景验证；相同输入重复运行稳定，Claude／Codex 一致。 | the four scenario tests in rows 1, 3, 4, 5; parity: `python3 -m pytest -q $T/test_external_change_recovery.py -k "claude or codex" -v \| tail -3` — paste count |
| 9 | 使用现有测试 fixture 和校验边界完成集成验证，保留 ADR-0001 自由规划与交互前置、ADR-0002 的视觉评审及产物权威规则。 | artefact: `git log --oneline -- docs/adr/0001-bootstrap-free-planning.md docs/adr/0002-dual-independent-visual-review.md \| head` shows no #14 commit touched either ADR |

- [ ] **Step 3: Decide, close or file** — Task 1 Step 4 rule, ticket 14.

- [ ] **Step 4: Commit**

```bash
cat > /tmp/audit14.txt <<'EOF'
meta-intent audit: #14 外部漂移恢复 — criteria mapped to proving tests and closed

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019P9YwUQfRBh2BhcLJGpXmo
EOF
git add docs/grillstorm/meta-intent/audit/14-audit.md
git commit -q -F /tmp/audit14.txt
```

---

### Task 7: Full suite, parent comment, push

**Files:** none new.

- [ ] **Step 1: Run the whole meta-skill suite once**

```bash
python3 -m pytest -q claude/meta-skill/tests/unit 2>&1 | tail -1
```

Expected: `… passed` with 0 failed (≈1,320). A failure here that none of the per-task runs showed means an audit task cited a test it did not actually run — go back and rerun that task's Step 1.

- [ ] **Step 2: Comment the parent and push**

```bash
gh issue comment 8 --body "$(cat <<'EOF'
Audit of #9–#14 against their acceptance criteria on main: records under docs/grillstorm/meta-intent/audit/. Tickets closed where every criterion has a proving test or artefact; any UNPROVED criterion was filed as its own needs-triage issue and its ticket left open (see each record's Verdict line).

#15–#18 are not in this audit: their closure conditions require real Claude and Codex host runs from a clean context with the evaluator holding criteria privately, and T15's own evaluation on disk says "Not a host pass … stay unverified". They need a separate plan once the Codex CLI is available.
EOF
)"
git fetch -q origin && test "$(git log --oneline HEAD..origin/main | wc -l)" = 0 && git push -q origin main
```

---

## Self-Review

**Spec coverage.** Every acceptance criterion of #9 (8), #10 (9), #11 (8), #12 (8), #13 (8), #14 (9) has a row with a named proof. The Claude/Codex-parity criterion on each ticket is proved by the `host` parametrization of the cited files, with an explicit UNPROVED path if a file turns out not to be parametrized — that is the one place the audit may legitimately fail, and the plan says what to do then rather than assuming. #15–#18 are excluded on the tickets' own closure conditions, stated in Global Constraints and the parent comment.

**Placeholder scan.** No TBD/TODO. Every "run the tests" step lists the exact `pytest` invocations. The "Decide, close or file" steps in Tasks 2–6 reference Task 1 Step 4 by name and that step spells out both branches with commands; that reference is deliberate (identical rule) and the commands are reproduced there, not omitted.

**Type consistency.** All test names were taken from `grep '^def test_'` on the current tree, not invented; record filenames `09-audit.md` … `14-audit.md` match between File Structure, each task and the Task 7 comment; the commit trailer is identical in all seven commit blocks.
