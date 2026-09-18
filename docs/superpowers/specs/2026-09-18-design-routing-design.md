# M1 design-routing — 设计环节必达

总览：`2026-09-18-product-experience-overhaul-overview.md`。canonical 树：`claude/meta-skill/`
（codex/pi 通过符号链接读取 `scripts/` 与大部分 `knowledge/`；手工孪生文件归 M5）。

## 问题

new-product 路线在有界面的产品上可以规划出零个体验设计节点，且没有任何确定性检查拒绝它。

- `skills/bootstrap/SKILL.md:364` 只加载"文件名与 goals 匹配的 capability"；new-product 以 `create`
  起步（`:256`），而 `knowledge/capabilities/` 下没有 `create.md`。
- `bootstrap-planning.md:9-12` 的"smallest node graph / prefer fewer nodes"使设计节点最先被省掉。
- `experience_priority` 有 12 处读取（`consumer-maturity-patterns.md:9,200`、
  `experience-map-schema.md:371,455`、`design-audit-dimensions.md:158,160,341`、
  `capabilities/product-analysis.md:70,140,161`、`generate-artifacts.md:28`、`translate.md:53`、
  `feature-gap.md:48`），没有生产者，没有 schema，平铺与 `.mode` 两种读法混用。
- `bootstrap-audits.md:33`：非游戏项目且无 `product-concept.json` 时跳过整个覆盖自检。
- `capabilities/app-design.md:5,225-232` 规定每个节点 `human_gate: true`，而
  `validate_unattended_readiness.py:748-768` 对未审批的 `human_gate` 节点报 `pending_human_gate`。
  ADR-0001 与 `skills/bootstrap/SKILL.md:643-647` 已声明 `human_gate` 不是运行时概念。
  按现行文本生成的 app-design 工作流**无法无人值守运行**。

## 需求

- **R-M1-01 体验优先级有生产者与 schema。** `bootstrap-profile.json` 新增
  `experience_priority: {"mode": "consumer" | "admin" | "mixed" | "none", "reason": "<一句依据>"}`，
  写入 `skills/bootstrap/SKILL.md` Step 1.6 的 profile schema。bootstrap 是唯一生产者。
  `none` 仅用于无最终用户界面的项目（`architecture_pattern` 为 `cli`、`library-sdk`、
  `embedded-firmware`，或纯后端/API）。判定依据是产品面向谁，不是技术栈。
- **R-M1-02 读法统一。** 上述 12 处读取点统一为 `bootstrap-profile.json` 的
  `experience_priority.mode`；删除"从 `source-summary.json` / `product-map.json` 读取"的说法与
  `generate-artifacts.md:28` 的循环生产声明。
- **R-M1-03 产品路线强制加载设计知识。** `skills/bootstrap/SKILL.md` Step 2 增加一条：
  `task_route` 为 `new-product` 或 `product-reconstruction` 且 `experience_priority.mode != none` 时，
  必须加载 `capabilities/product-concept.md`、`consumer-maturity-patterns.md`、
  `journey-emotion-schema.md`，以及 `capabilities/app-design.md`（非游戏）或
  `capabilities/game-design.md`（游戏）。"Capabilities are reference, not a node menu"保留：
  加载的是方法，不是固定节点清单。
- **R-M1-04 规划法：体验设计责任不可省。** `bootstrap-planning.md` "Free planning" 段补充：
  "smallest graph" 不包含省略体验设计；`experience_priority.mode` 为 `consumer`/`mixed` 的产品路线，
  工作流必须含产出体验设计产物的节点，且每个实现界面的节点（直接或传递）`hard_blocked_by` 它。
  节点可自由合并、命名；契约是产物路径，不是节点名：
  - 应用：`.allforai/app-design/concept/job-story-spec.json`、
    `.allforai/app-design/spec/user-flow-spec.json`、
    `.allforai/app-design/spec/screen-requirements-spec.json`、
    `.allforai/app-design/spec/permissions-notifications-settings-spec.json`；
  - 游戏：`.allforai/game-design/design/game-design-doc.json`。
  `product-intent-confirmation.md` 的 `plan` 操作里 `not_applicable.experience` 仅在 `mode == none` 时合法。
- **R-M1-05 app-design 可无人值守运行。** `capabilities/app-design.md` 删除
  `human_gate: true` 与 Human Gate Protocol 对新节点的要求，改为 `decision_mode: "brainstorm"` +
  `decision_inputs`（Phase A 前置决定，见 `bootstrap-audits.md:280-351`）。不为 app-design 新增
  `approval-records.json` 写入；既有读取方（`SKILL.md:93-99` 的概念漂移条件）保持为遗留读取，不改。
- **R-M1-06 覆盖自检的洞补上。** `bootstrap-audits.md` §3.5 触发条件改为：
  `has_product_concept` 为假且游戏 → §3.5.0；为假且 `experience_priority.mode != none` →
  新增 **§3.5.0b App Design Coverage Check**；两者皆否 → Step 3.4。§3.5.0b 沿用 §3.5.0 的
  三列表格（System Concern / Trigger Condition / Check），覆盖：首次进入与引导、主线（不是功能入口网格）、
  核心循环的过程反馈、完成后的下一步、空/加载/错误/成功状态体系、回访理由、设置项受众。
  与 §3.5.0 不同：界面产品上的缺口是**阻断**，不是备注。
- **R-M1-07 确定性校验：拒绝无体验设计覆盖的界面工作流。** 在
  `scripts/orchestrator/validate_bootstrap.py` 新增 `validate_experience_design_coverage(bdir)`，
  放在 `validate_app_design_flow` 旁，注册进 `main()`、`__all__` 与 `structural_gate_blockers`。
  读取 `bootstrap-profile.json` + `workflow.json` + node-specs。阻断码：
  - `missing_experience_priority`：产品路线的 profile 缺该字段或 `mode` 非法；
  - `missing_experience_design_node`：`mode ∈ {consumer, mixed}` 且工作流含界面实现节点，
    但没有节点的 `exit_artifacts` 覆盖 R-M1-04 的产物路径（应用至少 user-flow 与 screen-requirements；
    游戏至少 game-design-doc）；
  - `implementation_not_blocked_by_experience_design`：某界面实现节点不（传递）依赖该设计节点；
  - `experience_not_applicable_on_ui_product`：`mode != none` 而 `not_applicable` 含 `experience`。
  `task_route == local-change` 不触发。界面实现节点的识别复用 `validate_mobile_ui_coverage`
  （`:818-846`）与 `_matching_nodes`（`:766`）的既有办法，不新造启发式。
  因 `validate_bootstrap.py` 已在复制清单内并在 `/run` 边界重跑，不改复制清单。
- **R-M1-08 契约措辞钉住。** `validate_meta_contracts.py` 新增
  `validate_experience_routing_contract(errors)`（仿 `validate_execution_repair_loop_contract`，
  `:140-176`），钉住 bootstrap 语料中的 `experience_priority`、四个 mode 值、R-M1-03 的加载条款、
  §3.5.0b 标题；注册进 `main()`。
- **R-M1-09 测试。** `tests/unit/test_validate_bootstrap.py` 为 R-M1-07 的四个码各加拒绝用例与一个
  通过用例，并加 `local-change` 不触发、`mode == none` 不触发两例；host 参数化
  `["claude","codex"]`，夹具风格沿用该文件的 `test_app_design_flow_*`（`:609-671`）。既有
  `test_app_design_flow_*` 用例不得因新检查而误报（按需给其 profile 补 `experience_priority`）。

## 接口

- 暴露：`data:experiencePriority`（profile 字段）、`api:validateExperienceDesignCoverage`（校验函数及四个阻断码）、
  `data:experienceDesignArtifacts`（R-M1-04 的产物路径契约）。
- 消费：无。

## 不做

- 不新增固定节点清单或模板；不改游戏场景模板。
- 不修 `validate_game_creative_pipeline.py` 无人调用的问题（游戏与应用的质量门强制归 M3）。
- 不改 codex/pi 的手工孪生文件（归 M5）。

## 验收

```bash
python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_bootstrap.py
python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills
grep -rn "experience_priority" claude/meta-skill/knowledge | grep -v "experience_priority.mode" | grep -v bootstrap  # 期望为空
```
