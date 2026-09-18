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

## Detailed design

设计日期 2026-09-18，对照分支 `product-experience-overhaul` 上的真实文件核对过每一处引用。
下文路径若无前缀，均相对 `claude/meta-skill/`。验证器方案已在临时副本中做过原型验证
（见"原型证据"），未改动目标仓库的任何其它文件。

### Spec corrections（规格引用与现实不符之处，按现实设计）

1. **读取点是 13 处，不是 12 处。** 规格自己列出的清单加起来就是 13：
   `consumer-maturity-patterns.md:9,200`（2）、`experience-map-schema.md:371,455`（2）、
   `design-audit-dimensions.md:158,160,341`（3）、`capabilities/product-analysis.md:70,140,161`（3）、
   `generate-artifacts.md:28`、`translate.md:53`、`feature-gap.md:48`（各 1）。行号今日全部准确。
   其中 5 行（`cmp:9,200`、`ems:371,455`、`dad:158`）已含 `experience_priority.mode` 字面量，
   只需补"读自哪里"；其余 8 行必须改写。R-M1-02 按 13 处执行。
2. **游戏设计文档的规范路径是 `.allforai/game-design/game-design-doc.json`**（仓库内 68 处引用，
   生产者 `skills/game-design/00-env/game-design-registry/SKILL.md:49`、
   `capabilities/game-design.md:392,675`）。规格写的 `.allforai/game-design/design/game-design-doc.json`
   只出现在 `skills/game-creative/40-qa/creative-quality-critique/SKILL.md:26,141`（消费方，本轮不改）。
   设计：`data:experienceDesignArtifacts` 的游戏项**两条路径都接受**，规划文本以规范路径为主、
   注明 `design/` 变体同样有效。规格路径仍然满足校验，需求未被削弱。
3. **`structural_gate_blockers` 返回类型化 finding（dict），不是字符串。**
   （`validate_bootstrap.py:2101-2120`，由 `validate_unattended_readiness.py:591` 在 `/run` 边界调用。）
   因此 R-M1-07 需要一对函数：`experience_design_coverage_findings(bdir)`（类型化）与
   `validate_experience_design_coverage(bdir)`（`_rendered(...)` 包装），与
   `effect_stage_ownership_findings` / `validate_effect_stage_ownership`（`:1954`/`:2033`）同构。
   注册表接口名 `api:validateExperienceDesignCoverage` 不变，覆盖这一对函数与四个阻断码。
4. **`not_applicable` 位于 `workflow.json` 顶层**，是 `{"experience": "<理由>", "technical": "<理由>"}`
   形式的 dict（`product_intent.py:732-734`）。`experience_not_applicable_on_ui_product` 读这里。
5. **既有 `test_app_design_flow_*`（`:609-673`）根本不写 profile。** 新检查在 profile 缺失时直接返回空，
   所以这两个用例无需补 `experience_priority`。真正会被新检查误伤的是另一处，见下条。
6. **注册进 `main()` 与 `structural_gate_blockers` 会打断既有产品路线夹具。**
   `tests/unit/test_bootstrap_scope.py:57 project()` 是全部产品意图测试的共用夹具
   （`test_product_intent_session.py`、`test_acceptance_allocation.py`、`test_legacy_projection_authority.py`、
   `test_intent_review_corrections.py` 等经由 `draft` 把路线改成产品路线，并断言三个门返回 0）。
   原型实测：不改夹具时 `test_revised_baseline_generates_full_applicable_plan_and_gates_reject_drift`
   4 个参数全部失败（`missing_experience_priority`）。修法是给 `project()` 写出的 profile 加一行
   `experience_priority: {"mode": "none", ...}`（该夹具是无界面的订单服务，且其 `plan` 用了
   `not_applicable.experience`，`none` 是如实标注）；`product_intent.py:1356-1358` 用 `profile.update`
   保留该字段。原型实测改后 405 个相关用例全过。此文件计入 R-M1-09 的触碰清单。
7. **`test_validate_bootstrap.py` 目前没有任何 host 参数化。** host 参数化的既有先例是
   `test_bootstrap_scope.py:62-63`（按 host 取 `claude/…/scripts` 或 `codex/meta-skill/scripts`）。
   本设计沿用"按 host 路径取脚本"的做法，见 U9。
8. `tests/prompts/domain-codex.md:37` 的评审提示仍要求 app-design.md 有 "Human Gate Protocol 节"。
   R-M1-05 删除该节后这句提示会诱导评审者要求恢复它，故随 R-M1-05 同改一行。

### Architecture

M1 由三层构成，层间只靠两个数据契约耦合：

```
  生产（bootstrap 交互期）          消费（知识文本）                 强制（确定性）
  U1 profile.experience_priority ──► U2 13 处读取点统一读 .mode
        │                            U3 Step 2 强制加载设计知识
        │                            U4 规划法：设计产物路径契约 ──┐
        │                            U5 app-design 去 human_gate   │
        │                            U6 §3.5.0b 覆盖自检（LLM）    │
        └────────────────────────────────────────────────────────►U7 validate_bootstrap
                                                                   （bootstrap Step 5 + /run 边界）
                                     U8 validate_meta_contracts 钉住 U1/U3/U6 的措辞
                                     U9 单元测试钉住 U7 的行为
```

- `data:experiencePriority`：`bootstrap-profile.json.experience_priority = {mode, reason}`。唯一生产者 U1；
  读者 U2–U7 以及 M2/M3/M4。
- `data:experienceDesignArtifacts`：U4 文本与 U7 常量共同定义的产物路径集合。
- `api:validateExperienceDesignCoverage`：U7。

数据流：Step 1.6 写 profile → Step 2 依 `mode` 加载知识 → Step 3 依规划法产出含设计节点的图 →
§3.5.0b 语义自检（LLM，缺口即阻断并自修）→ Step 5 `validate_bootstrap.py` 确定性拒绝 →
`/run` 边界 `validate_unattended_readiness.py` 经 `structural_gate_blockers` 再次拒绝。

### Units

#### U1 体验优先级的 schema 与生产者（R-M1-01）

- 文件：`skills/bootstrap/SKILL.md`（编辑，Step 1.6 与 Step 1.2）。
- Step 1.6 的 JSON 块里，在 `"architecture_pattern"` 一行之后追加（沿用该块 `"a | b"` 的书写风格）：
  ```json
  "experience_priority": {"mode": "consumer | admin | mixed | none", "reason": "<one sentence: who the product serves and why this mode>"},
  ```
- JSON 块之后、`> **bootstrap-profile.json vs discovery source-summary.json` 引用块之前，新增一段
  `**experience_priority**`（约 8 行）：
  - bootstrap 是 `experience_priority` 的唯一生产者；下游一律读 `bootstrap-profile.json` 的
    `experience_priority.mode`，任何节点不得重新分类或改写。
  - 四个取值的判据：`consumer`（最终用户自愿使用、可随时离开的产品）、`admin`（内部/运营/后台工具，
    用户因职责使用）、`mixed`（两者并存，如消费端 + 商家后台）、`none`（没有最终用户界面）。
  - `none` 仅用于 `architecture_pattern` 为 `cli`、`library-sdk`、`embedded-firmware`，或纯后端/API 的项目。
  - 判定依据是产品面向谁，不是技术栈；游戏一律 `consumer`。
  - `reason` 必填，一句话。`local-change` 路线可省略整个字段。
- Step 1.2 末尾补一句：`Classify experience_priority (see 1.6) from task_goal, product_vision and who the product serves.`
- 不改 `product_intent.py`：它用 `profile.update(...)` 写 profile，保留既有字段（`:1356-1358`）。
- 依赖：无。被 U3、U7、U8 依赖（U8 钉住 `"mode": "consumer | admin | mixed | none"` 这一字面量）。

#### U2 读法统一（R-M1-02）

- 文件（全部编辑，逐行替换，不动其它内容）：

| 位置 | 现状 | 改为 |
|---|---|---|
| `knowledge/consumer-maturity-patterns.md:9` | `When \`experience_priority.mode = consumer\` or \`mixed\`, …` | 句首改为 `When \`bootstrap-profile.json\` \`experience_priority.mode = consumer\` or \`mixed\`, …` |
| `knowledge/consumer-maturity-patterns.md:200` | `(when \`experience_priority.mode = consumer\` or \`mixed\`)` | 不改字面量，保持（已合规） |
| `knowledge/experience-map-schema.md:371,455` | 已含 `.mode` | 保持；在 `:371` 行尾补 `, read from \`bootstrap-profile.json\`` |
| `knowledge/design-audit-dimensions.md:158` | 已含 `.mode` | 保持 |
| `knowledge/design-audit-dimensions.md:160` | `**Activation condition**: \`product-map.json\` contains \`experience_priority\` with mode …` | `**Activation condition**: \`bootstrap-profile.json\` \`experience_priority.mode\` is \`consumer\` or \`mixed\`.` |
| `knowledge/design-audit-dimensions.md:341` | `When experience_priority = consumer/mixed` | `When \`experience_priority.mode\` = consumer/mixed` |
| `knowledge/capabilities/product-analysis.md:70` | source-summary 字段表里的一行 `experience_priority` | **删除该行**（它不是 source-summary 字段）；在表后的 "Archetype fallback rule" 段之前加一句：`Experience classification is not a source-summary field: read \`experience_priority.mode\` from \`bootstrap-profile.json\`; never reclassify it here.` |
| `knowledge/capabilities/product-analysis.md:140` | `(experience_priority != admin)` | `(\`experience_priority.mode\` is \`consumer\` or \`mixed\`)` |
| `knowledge/capabilities/product-analysis.md:161` | `- \`experience_priority\` classified: consumer / admin / mixed` | `- \`experience_priority.mode\` read from \`bootstrap-profile.json\` and carried unchanged (never reclassified)` |
| `knowledge/capabilities/generate-artifacts.md:28` | `- \`experience_priority\`, \`protection_level\`, … fields generated` | `- \`protection_level\`, \`audience_type\`, \`render_as\` fields generated`（删除循环生产声明） |
| `knowledge/capabilities/translate.md:53` | `if experience_priority = consumer/mixed` | `if \`experience_priority.mode\` = consumer/mixed` |
| `knowledge/capabilities/feature-gap.md:48` | `experience_priority = consumer/mixed` | `\`experience_priority.mode\` = consumer/mixed` |

- 不变量（即验收第 4 条 grep）：`knowledge/` 下除文件名含 `bootstrap` 的文件外，任何提到
  `experience_priority` 的行都必须同行含字面量 `experience_priority.mode`。U4、U5 新写入
  `product-intent-confirmation.md`、`capabilities/app-design.md` 的句子同样受此约束。
- `codex/meta-skill/knowledge/` 下这些文件是符号链接，随之生效；无手工孪生需要改。
- 依赖：U1（字段名）。

#### U3 产品路线强制加载设计知识（R-M1-03）

- 文件：`skills/bootstrap/SKILL.md` Step 2（编辑）。
- 保留 `Capabilities are REFERENCE material, not a node menu.` 与第 1–8 条原文、原编号
  （`skills/bootstrap/SKILL.md` 是共享热点文件，不重排编号以免与 M2–M4 的串行编辑冲突）。
  第 1 条 `Do not read every file in \`knowledge/capabilities/\`.` 之后补一句指针：
  `Product routes with an interface also load item 9 regardless of goal names.`
  在第 8 条之后、`Proceed to planning with confirmed inputs.` 之前追加第 9 条：
  ```
  9. Product routes with an interface: when `task_route` is `new-product` or
     `product-reconstruction` and `experience_priority.mode != none`, always load
     `knowledge/capabilities/product-concept.md`, `knowledge/consumer-maturity-patterns.md`,
     `knowledge/journey-emotion-schema.md`, and `knowledge/capabilities/app-design.md`
     (`is_game_project = false`) or `knowledge/capabilities/game-design.md` (`is_game_project = true`),
     whether or not a goal name matches them (`create` has no capability file).
     This loads method, not a fixed node list.
  ```
  路径前缀写法与该节其它条目一致（`${CLAUDE_PLUGIN_ROOT}/knowledge/...`）。
- 依赖：U1。被 U8 钉住。

#### U4 规划法：体验设计责任不可省（R-M1-04）

- 文件：`knowledge/bootstrap-planning.md`（编辑，仅 `## Free planning` 段，追加一个列表项，不改既有 5 条，
  不触碰 Musts 编号——Must #9 属 M3）；`knowledge/product-intent-confirmation.md`（编辑，`plan` 操作段）。
- `## Free planning` 列表末尾追加：
  ```
  - "Smallest" never means omitting experience design. On a `new-product` or
    `product-reconstruction` route whose `experience_priority.mode` is `consumer` or `mixed`,
    the workflow contains node(s) whose `exit_artifacts` produce the experience design
    artifacts, and every node that implements an interface is (directly or transitively)
    `hard_blocked_by` them. Merge and name nodes freely; the contract is the artifact path,
    not the node name:
    - App: `.allforai/app-design/concept/job-story-spec.json`,
      `.allforai/app-design/spec/user-flow-spec.json`,
      `.allforai/app-design/spec/screen-requirements-spec.json`,
      `.allforai/app-design/spec/permissions-notifications-settings-spec.json`.
    - Game: `.allforai/game-design/game-design-doc.json`
      (`.allforai/game-design/design/game-design-doc.json` is accepted as the same artifact).
    `validate_bootstrap.py` refuses a graph that breaks this
    (`missing_experience_design_node`, `implementation_not_blocked_by_experience_design`).
  ```
- `product-intent-confirmation.md:122-123` 的句子
  "`not_applicable` may explain experience or technical omissions (for example a headless API has no UI experience work)."
  之后追加一句（同行含 `experience_priority.mode`，满足 U2 不变量）：
  ``` `not_applicable.experience` is legal only when `bootstrap-profile.json` `experience_priority.mode` is `none`; any other mode is refused as `experience_not_applicable_on_ui_product`. ```
  不改 `product_intent.py`（归 M2；确定性拒绝由 U7 承担）。
- 依赖：U1。与 U7 常量一一对应（`data:experienceDesignArtifacts`）。

#### U5 app-design 可无人值守运行（R-M1-05）

- 文件：`knowledge/capabilities/app-design.md`（编辑）、`tests/prompts/domain-codex.md`（编辑 1 行）。
- `app-design.md:5` 改为：
  `> Direction choices in this capability are Phase A decisions: a node whose direction is a human decision carries \`decision_mode: "brainstorm"\` and receives its answer as \`decision_inputs\` (see \`bootstrap-audits.md\` Phase A). No node carries \`human_gate: true\`; nothing here waits for approval at run time.`
- 删除 `## Human Gate Protocol` 整节（`:225-232`），原位替换为 `## Decision Inputs`：
  - 方向性选择（导航模型、主线、语气、变现）在交互式 `/bootstrap` 的 Phase A 收集，写成
    `.allforai/app-design/decision-<id>.json`，并接到消费节点的 `decision_inputs`。
  - `/run` 期间节点只读 `decision_inputs`，不发问、不等待审批。
  - 不写 `.allforai/app-design/approval-records.json`；不设 `approval_record_path`。
    已有项目里遗留的该文件仍被 `skills/bootstrap/SKILL.md` 的概念漂移检测读取（遗留读取，不改）。
- Canonical Node Registry 表的 `Discipline Owner` 列保留（`SKILL.md:618` 定义 `discipline_owner`
  为 Phase A 决定的归属角色，仍然有效）。`:182` "Merge all approved design JSONs" 改为
  "Merge all selected design JSONs"。
- `tests/prompts/domain-codex.md:37` 末句改为：
  `是否已无 Human Gate Protocol 节与 \`human_gate: true\`，方向决定是否经 \`decision_mode: "brainstorm"\` + \`decision_inputs\`？`
- 不改 `SKILL.md:93-99`、`validate_approval_records`、`validate_app_design_flow`、Step 6 对
  approval-records 的初始化（`SKILL.md:646-647` 已声明该链条留待后续退役）。
- 依赖：无。

#### U6 §3.5.0b App Design Coverage Check（R-M1-06）

- 文件：`knowledge/bootstrap-audits.md`（编辑）。
- `:33` 的 Trigger 句改为：
  `**Trigger**: for product-wide routes after product confirmation, \`has_product_concept\` is true (from Step 1.0). If false AND \`is_game_project\` is true, run **Game Design Coverage Check** (§3.5.0) instead. If false AND \`is_game_project\` is false AND \`experience_priority.mode != none\`, run **App Design Coverage Check** (§3.5.0b) instead. Otherwise skip to Step 3.4 (Confirm with User).`
- 在 §3.5.0 末句（`:50`）之后、`#### 3.5.1` 之前插入 `#### 3.5.0b App Design Coverage Check (interface products without product-concept.json)`：
  - 一段导语：适用条件；覆盖依据是 U4 的体验设计产物节点及其 node-spec，而不是功能清单。
  - 与 §3.5.0 同形的三列表（System Concern / Trigger Condition / Check），七行：

    | System Concern | Trigger Condition | Check |
    |---|---|---|
    | First entry & onboarding | always | 是否有节点设计首次打开到首次获得价值的路径（含无账号/无数据状态）？ |
    | Main line, not a feature grid | always | 用户流是否定义了一条主线（进入 → 核心动作 → 结果），首页不是功能入口网格？ |
    | In-progress feedback of the core loop | 产品有重复执行的核心动作 | 核心循环每一步是否定义了过程反馈（进度、正误、等待）？ |
    | What happens after completion | always | 每条主流程完成后是否定义了下一步（继续、复盘、离开），而非死路？ |
    | Empty / loading / error / success states | has UI screens | `screen-requirements-spec.json` 是否对每屏覆盖四态？ |
    | Reason to return | `experience_priority.mode` 为 `consumer`/`mixed` | 是否设计了回访理由（进度、节律、未完成事项），而非仅通知？ |
    | Settings audience | 产品有设置/配置界面 | `permissions-notifications-settings-spec.json` 是否只含最终用户该管的项，部署方配置不进入最终用户界面？ |

    （最后一行只要求"有此检查"；设置项受众的字段契约 `data:settingsAudience` 归 M4。）
  - 结尾段：**与 §3.5.0 不同，界面产品上的缺口是阻断，不是备注。** 修法：在既有体验设计节点的
    node-spec 中补齐范围，或新增设计节点并让界面实现节点 `hard_blocked_by` 它，然后重跑本检查；
    未清零不得进入 Step 3.4。节点集合因此变化时按 Phase A "Post-confirmation plan delta" 规则重新确认。
- 依赖：U1、U4。被 U8 钉住标题字面量 `3.5.0b App Design Coverage Check`。

#### U7 `validate_experience_design_coverage`（R-M1-07）

- 文件：`scripts/orchestrator/validate_bootstrap.py`（编辑；共享热点文件，改动限于：一个常量块、
  一组相邻新函数、`main()` 一行、`__all__` 两行、`structural_gate_blockers` 一处 return、模块 docstring 一行）。
- 常量（放在 `APP_DESIGN_FINALIZE_REQUIRED_ARTIFACTS` 之后）：
  ```python
  PRODUCT_ROUTES = ("new-product", "product-reconstruction")
  EXPERIENCE_PRIORITY_MODES = ("consumer", "admin", "mixed", "none")
  EXPERIENCE_DESIGN_MODES = ("consumer", "mixed")
  APP_EXPERIENCE_DESIGN_ARTIFACTS = (  # data:experienceDesignArtifacts，完整契约（4 条）
      ".allforai/app-design/concept/job-story-spec.json",
      ".allforai/app-design/spec/user-flow-spec.json",
      ".allforai/app-design/spec/screen-requirements-spec.json",
      ".allforai/app-design/spec/permissions-notifications-settings-spec.json",
  )
  APP_EXPERIENCE_DESIGN_REQUIRED = APP_EXPERIENCE_DESIGN_ARTIFACTS[1:3]   # 校验下限：user-flow + screen-requirements
  GAME_EXPERIENCE_DESIGN_DOC_PATHS = (
      ".allforai/game-design/game-design-doc.json",
      ".allforai/game-design/design/game-design-doc.json",
  )
  UI_MODULE_ROLES = ("frontend", "mobile")
  UI_IMPLEMENTATION_CAPABILITIES = ("implement", "translate", "ui-forge")
  UI_IMPLEMENTATION_TERMS = ("screen", "frontend", "front-end", "user interface", "界面", "页面",
                             "react native", "react-native", "flutter", "swiftui", "jetpack compose")
  GAME_UI_IMPLEMENTATION_TERMS = ("scene", "hud", "gameplay", "canvas", "sprite")
  ```
- 函数（放在 `_downstream_of`/`effect_stage_ownership_findings` 之后、`workflow_shape_findings` 之前，
  因为要用 `_structural`、`_rendered`、`_text`、`_downstream_of`、`_addressable_nodes`，它们都定义在
  `validate_app_design_flow` 之后；"放在 `validate_app_design_flow` 旁"落实为 `main()` 里的注册行紧随其后）：
  - `_produces(node, required) -> bool`：`_artifact_paths(node["exit_artifacts"])` 中有路径等于 `required`
    或以 `"/" + required` 结尾（兼容 monorepo 前缀，`SKILL.md:651-652`）。
  - `_ui_implementation_terms(profile) -> tuple`：`UI_IMPLEMENTATION_TERMS`，游戏再加
    `GAME_UI_IMPLEMENTATION_TERMS`，再加 profile 中 `role ∈ UI_MODULE_ROLES` 的模块路径 `"<path>/"`
    （与 `_profile_has_mobile_ui_module` `:626` 同样从 `profile.modules` 取证）。
  - `_is_implementation_node(node) -> bool`：`capability ∈ UI_IMPLEMENTATION_CAPABILITIES`，或
    `responsibilities` 含 `"implementation"`（产品路线 `plan` 操作写入的责任标签）。
  - `_ui_implementation_nodes(workflow, specs_dir, profile) -> list[dict]`（模块级私有函数，**界面实现节点的唯一识别入口**）：
    `_matching_nodes(workflow, specs_dir, _ui_implementation_terms(profile))`（`:766`，
    节点条目 + node-spec 正文的词项匹配，既有办法）再按 `_is_implementation_node` 过滤。
    刻意不用裸词 `"ui"`、`"expo"`（会命中 build/require/export）。
    M3 的 `experience_gate_flow_findings` 直接调用这个函数（闭环评审补充：M3 设计要求"与 M1 同源识别"，
    因此这里必须落成具名函数而不是内联在校验函数里，M3 无需再做抽取）。
  - `experience_design_coverage_findings(bdir) -> list[dict]`，判定顺序：
    1. `workflow.json` 或 `bootstrap-profile.json` 不存在、不可解析、根不是 dict → `[]`
       （与 `plan_confirmation_findings` `:1662-1672` 同样的让位方式；这些故障由 scope/shape 门负责）。
    2. `profile.task_route ∉ PRODUCT_ROUTES` → `[]`（`local-change` 与无路线的遗留 profile 均不触发）。
    3. `experience_priority` 不是 dict、`mode ∉ EXPERIENCE_PRIORITY_MODES` 或 `reason` 非非空字符串 →
       `missing_experience_priority`，**立即返回**（mode 未知时后续判定无依据）。
    4. `mode == "none"` → `[]`。
    5. `workflow.not_applicable` 是 dict 且含 `"experience"` → `experience_not_applicable_on_ui_product`（不返回，继续）。
    6. `mode ∉ EXPERIENCE_DESIGN_MODES`（即 `admin`）→ 返回当前 findings。
    7. 经 `_ui_implementation_nodes` 取界面实现节点；为空 → 返回（规格："且工作流含界面实现节点"）。
    8. 必需产物分组：应用 = `[(user-flow,), (screen-requirements,)]`；游戏（`profile.is_game_project is True`）=
       `[GAME_EXPERIENCE_DESIGN_DOC_PATHS]`。每组求生产者节点集；为空 → 每组一条
       `missing_experience_design_node`（消息含缺失路径）。
    9. 对每个界面实现节点、每个有生产者的分组：节点自身不是生产者，且
       `not any(_downstream_of(nodes, producer, ui_node))` → `implementation_not_blocked_by_experience_design`
       （`node_id=` 该实现节点，消息含产物路径与生产者 id）。
    节点一律经 `_addressable_nodes(workflow.get("nodes"))` 读取，畸形节点不会让本函数抛异常。
    每条消息以 `RETURN_TO_BOOTSTRAP`（`:1428`）收尾，因为四个码都只能在交互式 `/bootstrap` 修复。
  - `validate_experience_design_coverage(bdir) -> list[str]`：`return _rendered(experience_design_coverage_findings(bdir))`。
- 注册：
  - `main()`：`errors.extend(validate_app_design_flow(bdir))` 之后加
    `errors.extend(validate_experience_design_coverage(bdir))`。
  - `__all__`：加 `"validate_experience_design_coverage"`、`"experience_design_coverage_findings"`。
  - `structural_gate_blockers`：return 改为
    `repair_loop_declaration_findings(bdir) + effect_stage_ownership_findings(bdir) + experience_design_coverage_findings(bdir)`
    （追加在末尾，既有两项的相对顺序与 shape 优先规则不变；M3 的 `api:validateExperienceGateFlow` 之后同样追加一项即可，互不冲突）。
  - 模块 docstring 的 Checks 列表加一行。
- 不改复制清单（`SKILL.md` Step 6.2）：`validate_bootstrap.py` 已在其中。
- 接口（`api:validateExperienceDesignCoverage`）：上述两个函数签名 + 四个阻断码字符串。M3/M5 只依赖这些。

#### U8 契约措辞钉住（R-M1-08）

- 文件：`scripts/orchestrator/validate_meta_contracts.py`（编辑；共享热点，一个新函数 + `main()` 一行）。
- `validate_experience_routing_contract(errors: list[str]) -> None`，放在
  `validate_execution_repair_loop_contract` 之后，仿其结构，对 `_bootstrap_text()` 检查字面量：
  ```python
  "experience_priority",
  '"mode": "consumer | admin | mixed | none"',          # U1
  "experience_priority.mode != none",                   # U3 / U6 条件
  "knowledge/capabilities/product-concept.md",          # U3 加载条款
  "knowledge/consumer-maturity-patterns.md",
  "knowledge/journey-emotion-schema.md",
  "knowledge/capabilities/app-design.md",
  "knowledge/capabilities/game-design.md",
  "3.5.0b App Design Coverage Check",                   # U6 标题
  ```
  缺失时 `errors.append(f"bootstrap.md: missing experience routing term {term}")`。
- `main()`：在 `validate_execution_repair_loop_contract(errors)` 之后加一行调用。
- 不删除、不改动任何既有 pinned literal（U1/U3/U4/U6 的编辑均为追加或整句替换，已核对不触及
  `validate_implement_goal_contract` `:179-195` 等钉住的字符串）。
- 依赖：U1、U3、U6 的确切措辞——实现时先写文本再写钉子，字面量逐字一致。

#### U9 测试（R-M1-09）

- 文件：`tests/unit/test_validate_bootstrap.py`（编辑，追加在 `test_app_design_flow_passes_…` 之后）、
  `tests/unit/test_bootstrap_scope.py`（编辑 1 行，见 Spec corrections 6）。
- 风格：沿用本文件的 `_bootstrap_dir(tmp_path)`、`_base_node(**overrides)`、`_write`、直接
  `json.dumps` 写 `workflow.json` 的夹具写法与 `assert any("<code>" in e for e in errors)` 断言。
- host 参数化：新增本地助手
  ```python
  HOSTS = ["claude", "codex"]
  def _coverage_findings(host, bdir):   # 经 host 自己的脚本路径加载，codex 走符号链接
      scripts = Path(__file__).resolve().parents[4] / host / "meta-skill/scripts/orchestrator"
      out = subprocess.run([sys.executable, "-c", _COVERAGE_DRIVER, str(scripts), str(bdir)], ...)
      return json.loads(out.stdout)
  ```
  `_COVERAGE_DRIVER` 把 `scripts` 放上 `sys.path`、`import validate_bootstrap`、打印
  `experience_design_coverage_findings(bdir)` 的 JSON。用子进程而不是 `module_isolation.load`，
  因为后者按 realpath 缓存，两个 host 会拿到同一个模块对象，参数化形同虚设。
- 夹具助手 `_experience_project(tmp_path, *, route="new-product", priority=..., nodes, not_applicable=None, game=False)`：
  写 profile（含 `modules: [{"id": "app", "path": "mobile", "role": "mobile"}]`）与 workflow。
  基准通过图：`experience-design`（`exit_artifacts` = 4 条应用产物）→ `implement-mobile`
  （`capability="implement"`，goal 含 "screen"，`hard_blocked_by=["experience-design"]`）。
- 用例（全部 `@pytest.mark.parametrize("host", HOSTS)`）：

| 测试名 | 构造 | 期望 |
|---|---|---|
| `test_experience_coverage_passes_with_design_node_blocking_ui_implementation` | 基准图，`mode=consumer` | `[]` |
| `test_experience_coverage_rejects_missing_experience_priority` | 参数化 3 形：缺字段 / `mode="premium"` / 缺 `reason` | 仅 `missing_experience_priority` |
| `test_experience_coverage_rejects_workflow_without_design_node` | 去掉设计节点（ink-scent 形状） | `missing_experience_design_node`，消息含 user-flow 与 screen-requirements 路径 |
| `test_experience_coverage_rejects_ui_implementation_not_blocked_by_design` | 设计节点在，但 `implement-mobile.hard_blocked_by=[]`；另加经中间节点传递依赖的 `implement-web` | 仅 `implement-mobile` 被报，`node_id` 正确 |
| `test_experience_coverage_rejects_experience_not_applicable_on_ui_product` | 基准图 + `not_applicable={"experience": "skip"}`，`mode=admin` | `experience_not_applicable_on_ui_product` |
| `test_experience_coverage_ignores_local_change` | 无设计节点、无 `experience_priority`，`route="local-change"` | `[]` |
| `test_experience_coverage_ignores_mode_none` | 无设计节点，`mode=none`，`not_applicable.experience` 存在 | `[]` |
| `test_experience_coverage_game_accepts_either_design_doc_path` | `game=True`，参数化两条 game-design-doc 路径 | `[]`；去掉则 `missing_experience_design_node` |

  另加两条不带 host 的接线用例（进程内，用文件顶部 `load` 得到的模块）：
  - `test_experience_coverage_is_a_structural_gate_blocker`：`structural_gate_blockers(tmp_path)` 的 code 集含
    `missing_experience_design_node`（证明 `/run` 边界可达）。
  - `test_app_design_flow_fixtures_raise_no_experience_findings`：对既有两个 `test_app_design_flow_*`
    形状（无 profile）调用 `validate_experience_design_coverage`，断言 `[]`（证明不误报）。
- 文件顶部按既有写法绑定：`validate_experience_design_coverage = _validate_bootstrap.validate_experience_design_coverage`。
- `test_bootstrap_scope.py` `project()` 的 profile 字面量加：
  `"experience_priority": {"mode": "none", "reason": "Headless order-service fixture; no end-user interface"},`

### Error handling

- 校验器永不抛异常：文件缺失/不可解析/根类型错误 → 返回 `[]`，让位给已负责这些故障的 scope 门、
  `validate_workflow` 与 `workflow_shape_findings`；`structural_gate_blockers` 里 shape 故障仍先行独占返回。
- `missing_experience_priority` 先行短路，避免在未知 mode 上给出误导性的后续阻断。
- 误判方向的取舍：界面实现节点靠词项识别，可能把提到 "screen" 的后端实现节点算进来。后果是要求它
  也依赖设计节点——代价是一条 `hard_blocked_by` 边，方向安全。漏判的兜底是第 8 步：只要识别出任一
  界面实现节点，缺设计节点就被拒。
- 已 bootstrap 的旧产品路线项目（如 ink-scent）在下次 `/run` 会得到 `missing_experience_priority`，
  消息指向交互式 `/bootstrap`。这是需求的本意（R-M1-07 要求注册进 `structural_gate_blockers`），
  需在 M5 的发布说明里披露。
- 知识文本侧：§3.5.0b 缺口为阻断并就地自修；`validate_meta_contracts.py` 在措辞被后续模块改掉时失败。

### Testing

- 新增/修改的测试文件：`tests/unit/test_validate_bootstrap.py`、`tests/unit/test_bootstrap_scope.py`（夹具一行）。
- 验收命令（规格原文四条，从仓库根执行）：
  ```bash
  python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_bootstrap.py
  python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
  python3 claude/meta-skill/scripts/orchestrator/validate_skills.py claude/meta-skill/skills
  grep -rn "experience_priority" claude/meta-skill/knowledge | grep -v "experience_priority.mode" | grep -v bootstrap  # 期望为空
  ```
- 回归命令（因 Spec corrections 6 追加；逐个点名文件，不以目录方式跑 codex/pi）：
  ```bash
  python3 -m pytest -q claude/meta-skill/tests/unit/test_validate_unattended_readiness.py \
    claude/meta-skill/tests/unit/test_bootstrap_scope.py \
    claude/meta-skill/tests/unit/test_product_intent_session.py \
    claude/meta-skill/tests/unit/test_acceptance_allocation.py \
    claude/meta-skill/tests/unit/test_legacy_projection_authority.py \
    claude/meta-skill/tests/unit/test_legacy_profile_authority.py \
    claude/meta-skill/tests/unit/test_intent_review_corrections.py \
    claude/meta-skill/tests/unit/test_product_intent_resume.py \
    claude/meta-skill/tests/unit/test_product_retained_scope.py \
    claude/meta-skill/tests/unit/test_planning_audit_contracts.py
  ```
- 基线（2026-09-18 本分支实测）：`validate_meta_contracts.py` 与 `validate_skills.py` 均 exit 0；
  验收第 4 条 grep 当前输出 8 行（U2 要清零的那 8 行）。4 个已知既有失败不碰。
- TDD 次序：U9 先写红（四个拒绝用例 + 夹具一行）→ U7 转绿 → U1/U3/U6 文本 → U8 钉子 → U2/U4/U5 文本 → 四条验收 + 回归。

### 原型证据

在临时副本（已删除）里按 U7 写了原型并实测：

- 对真实的 `ink-scent/.allforai/bootstrap/`（13 节点、零设计节点）：原样 → `missing_experience_priority`；
  给 profile 补 `mode=consumer` 后 → 两条 `missing_experience_design_node`（user-flow、screen-requirements）。
  即本次改造的触发事故会被确定性拒绝。
- 原型 + `project()` 夹具一行：`test_validate_bootstrap`、`test_validate_unattended_readiness`、
  `test_bootstrap_scope`、`test_product_intent_session`、`test_acceptance_allocation`、
  `test_legacy_projection_authority`、`test_intent_review_corrections`、`test_product_intent_resume`、
  `test_product_retained_scope` 共 405 passed。去掉夹具那一行 → 4 failed（证明该行必要）。

### Assumptions

- A1 `reason` 缺失或为空也算 `missing_experience_priority`（规格写"缺该字段或 mode 非法"；schema 规定
  `reason` 为字段组成部分，缺它即字段不完整）。
- A2 `admin` 模式只受 `missing_experience_priority` 与 `experience_not_applicable_on_ui_product` 约束；
  设计节点强制只对 `consumer`/`mixed`（规格原文）。
- A3 同时产出设计产物的界面实现节点（设计与实现合并在一个节点）不被要求依赖自己；是否允许这种合并
  由 M3 的实现前评审门裁决，M1 不加码。
- A4 多个节点可分担产物；实现节点只需传递依赖每个必需产物的**某一个**生产者。
- A5 游戏判定用 `profile.is_game_project is True`，与 SKILL.md Step 2/§3.5.0 的判据一致。
- A6 产物路径匹配接受 monorepo 前缀（`endswith("/" + path)`）。
- A7 内部命名（常量名、`_produces`、`_ui_implementation_terms`、`_is_implementation_node`、测试助手名）
  为私有选择，非注册表接口。例外：`_ui_implementation_nodes` 与测试助手 `_experience_project` 的名字被 M3 的设计引用
  （同文件内复用），实现时不得改名。
- A8 Step 2 新条目作为第 9 条追加（不重排既有编号），第 1 条加一句指针；`experience_priority` 在 profile JSON 块中置于
  `architecture_pattern` 之后。
- A9 `local-change` 路线的 profile 可不带 `experience_priority`；无 `task_route` 的遗留 profile 不触发新检查。
- A10 `codex`/`pi` 的手工孪生（bootstrap 适配器等）不在本模块改动；符号链接文件自动同步。

### File touch list

| 路径（相对仓库根） | 动作 | 需求 |
|---|---|---|
| `claude/meta-skill/skills/bootstrap/SKILL.md` | edit（Step 1.2 一句、Step 1.6 schema + 说明段、Step 2 新条目） | R-M1-01、R-M1-03 |
| `claude/meta-skill/knowledge/consumer-maturity-patterns.md` | edit（`:9`） | R-M1-02 |
| `claude/meta-skill/knowledge/experience-map-schema.md` | edit（`:371`） | R-M1-02 |
| `claude/meta-skill/knowledge/design-audit-dimensions.md` | edit（`:160`、`:341`） | R-M1-02 |
| `claude/meta-skill/knowledge/capabilities/product-analysis.md` | edit（`:70`、`:140`、`:161`） | R-M1-02 |
| `claude/meta-skill/knowledge/capabilities/generate-artifacts.md` | edit（`:28`） | R-M1-02 |
| `claude/meta-skill/knowledge/capabilities/translate.md` | edit（`:53`） | R-M1-02 |
| `claude/meta-skill/knowledge/capabilities/feature-gap.md` | edit（`:48`） | R-M1-02 |
| `claude/meta-skill/knowledge/bootstrap-planning.md` | edit（`## Free planning` 追加一项；共享热点，纯追加） | R-M1-04 |
| `claude/meta-skill/knowledge/product-intent-confirmation.md` | edit（`plan` 段追加一句） | R-M1-04 |
| `claude/meta-skill/knowledge/capabilities/app-design.md` | edit（`:5`、`:182`、`:225-232` 整节替换） | R-M1-05 |
| `claude/meta-skill/tests/prompts/domain-codex.md` | edit（`:37` 一句） | R-M1-05 |
| `claude/meta-skill/knowledge/bootstrap-audits.md` | edit（`:33` Trigger、新增 §3.5.0b） | R-M1-06 |
| `claude/meta-skill/scripts/orchestrator/validate_bootstrap.py` | edit（常量块、新函数组、`main()`、`__all__`、`structural_gate_blockers`、docstring；共享热点，纯追加） | R-M1-07 |
| `claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py` | edit（新函数 + `main()` 一行；共享热点，纯追加） | R-M1-08 |
| `claude/meta-skill/tests/unit/test_validate_bootstrap.py` | edit（追加助手与用例；共享热点，纯追加） | R-M1-09 |
| `claude/meta-skill/tests/unit/test_bootstrap_scope.py` | edit（`project()` profile 加一行） | R-M1-09（R-M1-07 的回归保护） |

不创建新文件。不触碰 `codex/`、`pi/` 下任何实体文件，不触碰 `product_intent.py`、
`validate_unattended_readiness.py`、`validate_game_creative_pipeline.py`。
