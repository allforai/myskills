# M3 experience-gate — 体验质量门

总览：`2026-09-18-product-experience-overhaul-overview.md`。依赖 M1（`data:experiencePriority`、
`data:experienceDesignArtifacts`）、M2（`data:experienceDirectionIntent`）。

## 问题

- 应用没有质量门。`skills/app-design/40-qa/` 只有 `flow-coverage-qa`（路径是否存在）与
  `app-design-closure-qa`（追溯是否闭合），都判"有没有"，不判"好不好"。
- 游戏的 Must #8（`bootstrap-planning.md:162`）只是散文。`validate_game_creative_pipeline.py` 只检查
  插件源码里的措辞接线，且**无任何调用方**；生成的项目里没有任何检查要求评审节点存在，或要求
  `concept-acceptance` `hard_blocked_by` 它。`capabilities/concept-acceptance.md` 不提创意评审。
  应用与游戏是同一个漏洞。
- 好坏判断完全在事后（`user_steps: ["/cross-exam", "/product-review"]`），无人值守运行内部无自我纠正。

## 需求

- **R-M3-01 新子 skill：`skills/app-design/40-qa/experience-quality-critique/SKILL.md`。**
  结构对齐 `skills/game-creative/40-qa/creative-quality-critique/SKILL.md`。两个阶段，同一 skill：
  - `stage: "design"`（实现前）：输入 M1 的应用设计产物、M2 的体验方向意图及其 `acceptance`；
  - `stage: "runtime"`（实现后）：再加截图清单、`.allforai/verify/` 下的视觉评审与运行时报告。
  缺失的可选输入记为 `insufficient_evidence`，不得静默忽略。
- **R-M3-02 输出契约。** `.allforai/app-design/qa/experience-quality-critique-<stage>.json` 与同名
  `.html`（`review_language: "zh-CN"`）。finding 形状与游戏侧一致：`finding_id`、`dimension`、
  `judgment_type ∈ {contract_defect, evidence_based_critique, llm_judgment, insufficient_evidence}`、
  `severity ∈ {blocker, major, minor, note}`、`confidence`、`claim`、`reasoning`、`evidence_refs[]`、
  `counterexample_or_comparison`、`repair_route{owner_skill, owner_artifact, requested_change,
  rerun_from_node_id}`、`blocks[]`。阶段门：`must_fix_before_implementation`、
  `must_fix_before_release`、`recommended_iterations`。沿用游戏侧规则：纯 `llm_judgment` 不得成为硬阻断；
  硬阻断须是 `contract_defect` 或高置信、指到具体产物/界面/截图的 `evidence_based_critique`。
- **R-M3-03 判据（维度）。** 与 `/product-review` 同源的五个镜头：`onboarding`（引导）、
  `process_feedback`（过程反馈）、`next_step`（下一步）、`state_consistency`（状态一致）、
  `return_reason`（回来理由）；另加 `mainline`（主线不是功能入口网格）、
  `direction_fidelity`（是否兑现 M2 体验方向的 `acceptance`，是否把用户用语直译成功能）、
  `audience_leak`（部署方/开发者配置出现在最终用户界面，判据见 M4）。反面对照
  `consumer-maturity-patterns.md` §B 三个反模式。每条 finding 必须指到谁、什么情境、哪件事、
  观察到什么；指不出观察的只是口味，不写入。
- **R-M3-04 独立评审。** 评审必须由未编写被评产物的 fresh-context 评审方执行，语义沿用 ADR-0002/0003
  的独立视觉评审；node-spec 写明评审方不得读取作者节点的推理过程，只读产物与证据。
- **R-M3-05 登记。** `skills/app-design/PACK.md` 增加该子项与 canonical 路径，并加判定类型与输出根
  一节（对齐 `game-creative/PACK.md:40-81`）；`capabilities/app-design.md` 的 Canonical Node Registry
  与 Sub-Skill Mapping 增加该节点。满足 `validate_skills.py:166-167` 的孤儿检查。
- **R-M3-06 规划法 Must #9。** `bootstrap-planning.md` 新增 "Experience quality gate (products with UI)"：
  `experience_priority.mode ∈ {consumer, mixed}` 的非游戏产品路线，设计产物完成后、任何界面实现节点之前
  跑 `stage: "design"`；最后一个 UI/product-verify/visual QA 之后跑 `stage: "runtime"`；
  收尾/验收节点 `hard_blocked_by` runtime 评审；`must_fix_*` 走所属 pack 的修复回路。
  `suppress-rules.md` 增加一行：`experience_priority.mode = none` → 抑制体验质量门。
  `capabilities/concept-acceptance.md` 写明其受创意/体验评审阻断。
- **R-M3-07 无人值守修复路由。** 评审的 `must_fix_*` 非空即该产物不通过：
  `scripts/orchestrator/check_artifacts.py` 的硬失败子集（`:439-451`）纳入
  `must_fix_before_implementation`、`must_fix_before_release`。
  设计阶段的 must-fix 由产出该设计产物的节点修复并重跑设计评审；运行阶段的 must-fix 归入
  `experience_gaps`，由实现修复节点处理并重跑受影响的 QA 与 runtime 评审。两者都在
  `unattended-run-readiness-spec.json.required_repair_loops` 中声明，`max_attempts` 沿用既有预算规则。
  预算耗尽时按既有 Run Policy 处理，不新增询问。
- **R-M3-08 确定性校验：应用与游戏同时覆盖。** `validate_bootstrap.py` 新增
  `validate_experience_gate_flow(bdir)`，注册进 `main()`、`__all__`、`structural_gate_blockers`。
  触发：产品路线且 `experience_priority.mode ∈ {consumer, mixed}` 且工作流含实现节点。阻断码：
  - `missing_experience_gate`：应用无引用 `experience-quality-critique` 的节点 / 游戏无引用
    `creative-quality-critique` 的节点；
  - `implementation_not_blocked_by_design_critique`：（应用）界面实现节点不传递依赖设计阶段评审；
  - `closure_not_blocked_by_experience_gate`：收尾/`concept-acceptance`/`pipeline-closure-verify`
    节点不传递依赖运行阶段评审（游戏：实现后的那次创意评审）；
  - `experience_gate_without_repair_loop`：评审节点不在任何 `required_repair_loops.qa_node_ids` 内。
- **R-M3-09 源码接线校验。** 新增 `scripts/orchestrator/validate_app_experience_pipeline.py`
  （对齐 `validate_game_creative_pipeline.py`：PACK 列出每个子 skill、必备术语、bootstrap 语料提及）。
  两个 pipeline 校验器都加入 `.githooks/pre-commit` 的校验器清单，使其不再无人调用。
  `validate_meta_contracts.py` 新增 `validate_experience_gate_contract(errors)` 钉住 Must #9 与新术语。
- **R-M3-10 事后可采信的留痕。** 每次评审另写一份人读摘要到项目的
  `docs/experience-review/<stage>.md`（结论、must-fix、各镜头一行观察、证据限制、评审日期与被评提交）。
  这是 `/product-review` 能读到的位置（它不读 `.allforai/`）。
- **R-M3-11 测试。** `tests/unit/test_validate_bootstrap.py`：R-M3-08 四个码各一拒绝用例，应用与游戏各
  一通过用例，`mode == none` 与 `local-change` 不触发。新文件
  `tests/unit/test_validate_app_experience_pipeline.py`（接受最小夹具、拒绝未列出的子 skill、
  拒绝缺术语）。`tests/unit/test_check_artifacts_measurement.py` 或同类文件增加 must_fix 非空即失败的用例。
  `tests/unit/test_validate_unattended_readiness.py` 的回路夹具按需补新条目。

## 接口

- 暴露：`data:experienceCritiqueReport`（JSON 契约）、`data:experienceReviewDoc`（`docs/` 下的摘要）、
  `data:experienceLensVocabulary`（R-M3-03 的维度名单）、`api:validateExperienceGateFlow`（校验函数与四个码）。
- 消费：`data:experiencePriority`、`data:experienceDesignArtifacts`（M1）；
  `data:experienceDirectionIntent`（M2）；`data:settingsAudience`、`data:unspecifiedDecisionGap`（M4）。

## 不做

- 不改游戏创意评审 skill 的内容与输出 schema；只让它的存在与阻断关系被确定性校验。
- 不给评审打"客观分"冒充事实；分数仍带 `confidence`，硬阻断规则同游戏侧。
- 不在运行中向用户提问。

## 验收

```bash
python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_bootstrap.py \
  claude/meta-skill/tests/unit/test_validate_app_experience_pipeline.py \
  claude/meta-skill/tests/unit/test_validate_unattended_readiness.py
python3 claude/meta-skill/scripts/orchestrator/validate_app_experience_pipeline.py
python3 claude/meta-skill/scripts/orchestrator/validate_game_creative_pipeline.py
python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
```
