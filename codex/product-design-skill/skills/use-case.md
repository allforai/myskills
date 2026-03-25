---
name: use-case
description: >
  Use when the user asks to "generate use cases", "write test cases", "create use case document",
  "derive scenarios from product map", "verify e2e ordering", "用例", "生成用例", "用例集",
  "测试用例", "时序验证", "前置条件链", "从功能地图生成用例", "从体验地图推导用例",
  "场景覆盖", "用例树",
  or mentions generating Given/When/Then scenarios, deriving test cases from requirements,
  creating use case documents for QA or AI agent execution.
  Requires product-map to have been run first.
version: "2.5.0"
---

# Use Case — 用例集

> 以功能地图和体验地图为输入，推导完整用例：正常流、异常流、边界流

## 目标

以 `task-inventory.json`（必须）和 `experience-map.json`（必须，不存在则自动运行 experience-map）为输入，生成两份用例输出：

- **JSON 机器版**：完整字段，逐条可执行，供 AI agent 和自动化测试直接使用
- **Markdown 人类版**：摘要级，每条用例一行（ID + 标题 + 类型），供 PM / QA / 开发快速浏览

当 `product-map.json` 中的 `experience_priority.mode = consumer` 或 `mixed` 时，用例还必须覆盖成熟用户产品体验，不得只覆盖功能动作本身。

---

## 定位

```
product-map（功能地图）    experience-map（体验地图）    use-case（用例集）
谁用？做什么？有何异常？    在哪做？怎么做？出错怎么办？    推导完整用例，双格式输出
任务层语义                 界面层语义                    基于两者，机器可执行
```

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/task-inventory.json`。

若 `product-map.json` 含 `experience_priority`，use-case 必须继承该字段，切换不同的用例生成重心。

---

## 快速开始

```
/use-case              # 完整流程（Step 0-4）
/use-case quick        # 跳过异常流/边界流（Step 2）和 E2E 用例（Step 4），只生成正常流
/use-case scope 异常处理  # 只生成指定功能区的用例
```

## 增强协议（网络搜索 + 4D+6V + XV）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**搜索关键词**：`”risk based testing” + 产品类型 + “case study” + 2025`、`”INVEST user stories” + “real project”`

**4D+6V 重点**：`then` 覆盖三重成功定义（业务成功 + 技术成功 + 体验成功）；高频/高风险用例覆盖至少 4/6 视角，减少”可执行但不可解释”。

**XV 交叉验证**（Step 3 双格式输出后）：

| 验证点 | task_type | 发送内容 | 写入字段 |
|--------|-----------|----------|----------|
| 边界条件补充 | `edge_case_generation`→deepseek | 高频/高风险用例摘要（Given/When/Then） + 关联任务的 rules | cross_model_review.additional_edge_cases |
| 验收标准审查 | `acceptance_criteria_review`→gpt | 高频/高风险用例的 then 字段 + 任务的 acceptance_criteria | cross_model_review.acceptance_gaps |
| E2E 排序链路验证 | `e2e_ordering_validation`→gemini | E2E steps + ordering_issues + task main_flows | cross_model_review.ordering_gaps |
| **创新用例审查** | `innovation_use_case_review`→gpt | 创新用例列表 + adversarial-concepts.json 的创新方向 | cross_model_review.innovation_gaps |

自动写入：创新用例覆盖缺口（遗漏的创新机制验证、创新边界条件不足）。

自动写入：补充边界条件（被遗漏的极端场景、并发条件、时序依赖）、验收标准漏洞（then 条件不可测试、缺少否定断言、缺少数据完整性检查）。

## 中段经理理论支持（可选增强）

为让用例从“测试资产”升级为“需求质量资产”，可叠加以下产品管理框架：

| 理论/框架 | 对应步骤 | 落地方式 |
|-----------|----------|----------|
| INVEST（Independent/Negotiable/Valuable/Estimable/Small/Testable） | Step 1/2 | 对 `happy_path` 与异常用例做可测试性审查，减少空 `then` 与弱验收条件 |
| DoD（Definition of Done） | Step 3/4 | 将用例覆盖率（happy/exception/boundary/e2e）作为“需求完成”门禁 |
| 风险驱动测试（Risk-based Testing） | Step 2 | 高频/高风险任务优先补齐 exception + boundary，用例优先级更可解释 |
| 服务蓝图（Service Blueprint） | Step 4 | E2E 用例与跨角色/跨系统流一一对应，暴露前后台交接断点 |

> 默认流程不变；启用本增强后，use-case 可直接支撑评审会中的需求质量讨论。

**scope 模式**：scope 模式运行完整 Step 序列，但 Step 0 跳过 AI 分组，直接使用用户指定的功能区名称作为过滤条件，仅为匹配该功能区的任务生成用例。

**refresh 模式**：将 `use-case-decisions.json` 重命名为 `.bak` 备份，从 Step 0 开始完整重新运行，忽略所有已有决策缓存。

---

## 树结构（4 层）

```
角色 R001 运营专员
└── 功能区 FA001 异常处理
    └── 任务 T001 创建并提交工单
        ├── UC001  正常提交工单                [happy_path]
        ├── UC002  金额超限 → 拦截并提示        [exception]
        ├── UC003  重复提交 → 幂等去重          [exception]
        ├── UC004  权限不足 → 提示申请          [exception]
        ├── UC005  审批超时 48h → 自动升级      [exception]
        └── UC006  金额 ≥ 5000 → 触发复核流程   [boundary]
```

---

## 用例类型与来源

### 创新用例类型（新增，若 innovation_mode=active）

对 `innovation_task=true` 的任务，增加专用用例类型：

| 类型 | 用途 | 示例 |
|------|------|------|
| `innovation_mechanism` | 验证创新机制是否生效 | "场景流无限滚动"、"自动播放"、"3 秒启动" |
| `innovation_boundary` | 验证创新机制的边界条件 | "连续刷 10 个场景后的推荐准确性" |
| `state_transition` | 验证状态流转路径 | "工单提交 → 审核通过 → 工单完成" |
| `state_timeout` | 验证超时转换 | "审核超时后自动回退工单" |
| `state_compensation` | 验证补偿路径 | "工单撤销后配额恢复" |

**输出标记**：
- `innovation_use_case: true`
- `adversarial_concept_ref: IC001`

---

| 用例类型 | 来源字段 | 数量 |
|----------|----------|------|
| `happy_path` | `task.prerequisites` + `task.main_flow` + `task.outputs` | 每任务 1 条 |
| `exception` | `task.exceptions` 每条 + `screen.exception_flows`（若有） | 每异常 1 条 |
| `boundary` | `task.rules` 中含边界语义（≥ / ≤ / 幂等 / 超时）的条目 | 按规则提取 |
| `validation` | `screen.action.validation_rules`（需 experience-map） | 按校验规则提取 |

当 `experience_priority.mode = consumer` 或 `mixed` 时，还应额外补充以下用例倾向：

- `journey_guidance`：完成动作后是否知道下一步
- `result_visibility`：动作结果是否回流到列表/首页/历史
- `continuity`：提醒/通知/进度/最近活动等持续关系链路是否成立
- `entry_clarity`：首页主线是否可发现，而非入口拼盘

---

## 全自动模式

**激活条件**（同时满足）：
1. `.allforai/product-concept/product-concept.json` 存在且含 `pipeline_preferences` 字段
2. 上下文含 `__orchestrator_auto: true`（由 `/product-design full` 编排器传入）

**未同时满足** → 保持标准交互模式（当前行为不变）。

**行为变化**：

| 步骤 | 标准模式 | 全自动模式 |
|------|----------|-----------|
| **Step 0 功能区分组确认** | 向用户确认 | 自动确认，记入 `pipeline-decisions.json`（`decision: "auto_confirmed"`） |
| **Step 1 正常流确认** | 向用户确认 | 自动确认 |
| **Step 2 异常/边界确认** | 向用户确认 | 自动确认（所有用例自动生成，DEFERRED 标记不触发） |
| **Step 4 E2E 确认** | 向用户确认 | 自动确认 |

**安全护栏**（自动模式下仍然停下来问用户）：
- ERROR 级验证失败（use-case-tree.json 生成失败、task 引用断裂）

---

## 工作流

```
前置检查：
  .allforai/product-concept/concept-baseline.json  自动加载（推拉协议 §三.A）→ 不存在则 WARNING，不阻塞
  .allforai/product-map/task-inventory.json  必须存在，否则终止
  .allforai/experience-map/experience-map.json  必须（不存在则自动运行 experience-map 生成）
  .allforai/product-map/product-map.json  若存在且含 `experience_priority.mode = consumer|mixed` → 启用用户端成熟度用例补强
  .allforai/product-concept/product-mechanisms.json  可选（跨级拉取源）
  .allforai/use-case/use-case-decisions.json 若存在则加载，跳过已确认项

  跨级原始数据拉取（按需，推拉协议 §三.B）：
    product-concept.json:
      - roles[].jobs[].pain_relievers  → 生成 sad path 用例的来源
    product-mechanisms.json:
      - governance_styles（完整）       → 指导审核类用例生成（见下方消费规则）

  治理风格消费（governance_styles）：
    product-mechanisms.json 的 governance_styles 字段（由 concept Phase A.5 写入）：
    - 治理风格为"宽松高效"的业务流 → 不生成审核类 happy_path 用例，改为生成事后追究类用例（举报→处理→处罚）
    - 治理风格为"严格管控"的业务流 → 必须生成完整审核链用例（提交→审核→通过/拒绝→申诉）
    - system_boundary.external 中的功能 → 不生成 happy_path 用例，仅生成集成点 boundary 用例（外部服务超时/失败/不可用）
    - 无 governance_styles → 默认按任务内容推断（兼容旧版 concept）

Step 0: 功能区分组
      AI 按语义将任务分组为功能区（如「异常处理」「记录查询」）
      → 用户确认，可合并/拆分/重命名功能区
      ↓
Step 1: 正常流用例生成
      每个任务生成 1 条 happy_path 用例
      Given ← task.prerequisites
      When  ← task.main_flow（逐步展开）
      Then  ← task.outputs.states + outputs.messages + outputs.notifications + audit.recorded_actions
      若 `experience_priority.mode = consumer|mixed`：Then 还必须尽量包含“结果回流 / 下一步引导 / 用户可感知反馈”
      → 用户确认，可补充/修改
      ↓
Step 2: 异常流 + 边界用例生成（quick 模式跳过）
      每条 task.exceptions → 1 条 exception 用例
      task.rules 含边界语义 → boundary 用例
      screen.action.validation_rules → validation 用例（需 experience-map）
      screen.action.exception_flows 注入对应 exception 用例的 then 字段
      若 `experience_priority.mode = consumer|mixed`：额外补“完成后不知道下一步”“首页无主线”“持续关系断裂”“结果未回流”等体验型异常/边界用例
      → 用户确认，可标记 DEFERRED（不重要的异常暂不生成用例）
      ↓
Step 3: 双格式输出
      生成 use-case-tree.json（机器全量）
      生成 use-case-report.md（人类摘要）
      ↓
Step 4: 端到端用例生成（需 business-flows.json，quick 模式跳过）
      读取 business-flows.json，为每条完整流生成 E2E 用例
      有缺口的流标注待修复提示

模式路由：
  full 模式：Step 0 → Step 1 → Step 2 → Step 3 → Step 4
  quick 模式：Step 0 → Step 1 → Step 3（跳过 Step 2 异常流 + Step 4 E2E）；summary 中 e2e_count 设为 0
```

**核心原则：每个 Step 结束都有用户确认，用户是权威。**

---

### 前置检查

```
两阶段加载：
  Phase 1 — 加载索引：
    检查 .allforai/product-map/task-index.json
      存在 → 加载索引（< 5KB），获取任务 id/name/frequency/owner_role/risk_level + 模块分组
      不存在 → 回退到 Phase 2 全量加载

  Phase 2 — 按需加载完整数据：
    检查 .allforai/product-map/task-inventory.json
      存在 → 加载任务和角色数据
      不存在 → 提示：「请先执行 product-map 工作流生成功能地图，再执行 use-case 工作流」，终止

检查 .allforai/experience-map/experience-map.json：
  - 存在 → 加载界面数据（从 operation_lines[].nodes[].screens[] 提取），标注「已注入界面上下文」
  - 不存在 → 继续，标注「未注入界面上下文，exception_flows 和 validation_rules 将为空」
```

> **注意**：Step 0（功能区分组）是业务决策步骤，需用户确认，因此编为 Step 0 而非前置检查。前置检查只验证文件存在与否，不等待用户输入。

---

### Step 0：功能区分组

**数据加载**：若 `task-index.json` 存在，直接使用索引中的 `modules` 分组作为功能区初始分组（索引已按模块聚类），无需全量加载 `task-inventory.json`。`scope` 模式下，直接从索引的 `modules` 中匹配指定功能区名称进行过滤。若索引不存在，回退到读取完整 `task-inventory.json` 后 AI 语义归组。

读取任务数据，按语义归组：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "feature_areas": [
    {
      "id": "FA001",
      "name": "异常处理",
      "task_ids": ["T001", "T002", "T003"]
    },
    {
      "id": "FA002",
      "name": "记录查询",
      "task_ids": ["T004", "T005"]
    }
  ]
}
```

**用户确认**：功能区分组合理吗？有没有需要合并或拆分的？

---

### Step 1：正常流用例生成

**数据加载**：若前置使用了索引（Phase 1），此步按功能区分批加载完整任务数据 — 每个功能区从 `task-inventory.json` 中仅读取该区包含的任务 ID 对应条目，处理完一个功能区再加载下一个，避免一次性加载全量数据。

**用例字段全集**（不同类型字段的填写规则）：

| 字段 | happy_path | exception | boundary | validation |
|------|-----------|-----------|----------|------------|
| `id` | 必填 | 必填 | 必填 | 必填 |
| `title` | 必填 | 必填 | 必填 | 必填 |
| `type` | `"happy_path"` | `"exception"` | `"boundary"` | `"validation"` |
| `priority` | 必填 | 必填 | 必填 | 必填 |
| `given` | 必填 | 必填 | 必填 | 必填 |
| `when` | 必填 | 必填 | 必填 | 必填 |
| `then` | 必填 | 必填 | 必填 | 必填 |
| `screen_ref` | 选填 | 选填 | 选填 | 选填 |
| `action_ref` | 选填 | 选填 | 选填 | 选填 |
| `exception_source` | `null` | 必填（来自 `task.exceptions[N]`） | `null` | `null` |
| `rule_source` | 省略 | 省略 | 必填（来自 `task.rules[N]`） | 省略 |
| `validation_rule` | 省略 | 选填 | 省略 | 必填 |
| `flags` | 必填（默认 `[]`） | 必填（默认 `[]`） | 必填（默认 `[]`） | 必填（默认 `[]`） |

**priority 取值**：`高` / `中` / `低`。从任务的 `frequency`、`risk_level` 和 `category` 综合推导 — 高频或高风险任务的用例为高优先级；`category=core` 的任务优先级最低为「中」（核心功能即使低频也需覆盖）；低频且低风险且 basic 类为低优先级。

每个任务生成 1 条 happy_path 用例：

**机器版字段**：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "id": "UC001",
  "title": "正常提交工单",
  "type": "happy_path",
  "priority": "高",
  "given": [
    "已有关联记录",
    "有工单提交权限",
    "记录状态为已确认"
  ],
  "when": [
    "选择关联记录",
    "系统自动带出记录信息",
    "填写工单原因与金额",
    "金额校验通过（≤ 可调整金额）",
    "点击「提交工单」"
  ],
  "then": [
    "工单状态变为「主管待审」",
    "页面提示：工单已提交，主管将在 24h 内处理",
    "主管收到审核通知",
    "操作日志记录：创建、提交、操作人、时间"
  ],
  "screen_ref": "S001",
  "action_ref": "提交工单",
  "exception_source": null,
  "flags": []
}
```

**人类版（Markdown 摘要）**：

```markdown
| UC001 | 正常提交工单 | happy_path |
```

> **搜索驱动原则**：生成用例前，先 网络搜索「{产品类型} user scenario best practices」和「{产品类型} edge cases common mistakes」，用搜索结果补充容易遗漏的异常流和边界场景。

**用户确认**：正常流步骤完整吗？预期结果有没有遗漏？

---

### Step 2：异常流 + 边界用例生成

**exception 用例（来自 task.exceptions）机器版**：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "id": "UC002",
  "title": "金额超限拦截",
  "type": "exception",
  "priority": "高",
  "given": [
    "已有关联记录",
    "有工单提交权限",
    "填写调整金额 > 原始金额"
  ],
  "when": [
    "点击「提交工单」按钮（S001 / click_depth=1）"
  ],
  "then": [
    "工单未创建，数据库无新记录",
    "按钮保持可点击，不跳转",
    "金额字段边框变红，显示：调整金额不可超过原始金额，可调整 ¥{max_amount}",
    "顶部错误汇总出现：请检查调整金额"
  ],
  "screen_ref": "S001",
  "action_ref": "提交工单",
  "validation_rule": "金额 ≤ 原始金额",
  "exception_source": "task.exceptions[0]",
  "flags": []
}
```

**boundary 用例（来自 task.rules 边界语义）机器版**：

```json
{
  "id": "UC006",
  "title": "金额 ≥ 5000 触发复核流程",
  "type": "boundary",
  "priority": "高",
  "given": [
    "已有关联记录",
    "有工单提交权限",
    "填写调整金额 = 5000"
  ],
  "when": [
    "点击「提交工单」"
  ],
  "then": [
    "工单创建，状态为「主管待复核」而非「普通待审」",
    "主管收到复核通知",
    "普通审核流程不触发"
  ],
  "screen_ref": "S001",
  "action_ref": "提交工单",
  "rule_source": "task.rules[2]",
  "flags": []
}
```

**validation 用例（来自 screen.action.validation_rules）机器版**：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 experience-map 分析结果决定，不限行业。

```json
{
  "id": "UC007",
  "title": "处理原因为空 → 校验拦截",
  "type": "validation",
  "priority": "中",
  "given": [
    "已有关联记录",
    "有工单提交权限",
    "处理原因字段留空"
  ],
  "when": [
    "点击「提交工单」按钮（S001 / click_depth=1）"
  ],
  "then": [
    "工单未创建",
    "处理原因字段边框变红，显示：请填写处理原因",
    "按钮保持可点击，不跳转"
  ],
  "screen_ref": "S001",
  "action_ref": "提交工单",
  "validation_rule": "处理原因不能为空（screen.action.validation_rules[0]）",
  "flags": []
}
```

**用户确认**：异常场景覆盖完整吗？有没有需要标记 DEFERRED 的？

---

### Step 3：双格式输出

#### 机器版 `use-case-tree.json`（完整 4 层 JSON 树）

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "version": "2.5.0",
  "generated_at": "...",
  "summary": {
    "role_count": 3,
    "feature_area_count": 5,
    "task_count": 24,
    "use_case_count": 87,
    "happy_path_count": 24,
    "exception_count": 48,
    "boundary_count": 12,
    "validation_count": 3,
    "e2e_count": 2,
    "ordering_issue_count": 1,
    "e2e_flags": ["MISSING_HANDOFF_DATA"],
    "experience_map_injected": true
  },
  "roles": [
    {
      "id": "R001",
      "name": "运营专员",
      "feature_areas": [
        {
          "id": "FA001",
          "name": "异常处理",
          "tasks": [
            {
              "id": "T001",
              "name": "创建并提交工单",
              "use_cases": [
                { "id": "UC001", "type": "happy_path", "...": "见 Step 1 Schema" },
                { "id": "UC002", "type": "exception",  "...": "见 Step 2 Schema" }
              ]
            }
          ]
        }
      ],
      "e2e_cases": [
        { "id": "E2E-F001-01", "type": "e2e", "flow_ref": "F001", "...": "见 Step 4 Schema" }
      ]
    }
  ]
}
```

#### 人类版 `use-case-report.md`（摘要级，每条用例一行）

```markdown
# 用例集摘要

角色 X 个 · 功能区 X 个 · 任务 X 个 · 用例 X 条（正常流 X / 异常流 X / 边界 X）

## R001 运营专员

### 异常处理

**T001 创建并提交工单**（6 条用例）

| ID | 标题 | 类型 |
|----|------|------|
| UC001 | 正常提交工单 | happy_path |
| UC002 | 金额超限拦截 | exception |
| UC003 | 重复提交去重 | exception |
| UC004 | 权限不足提示 | exception |
| UC005 | 审批超时升级 | exception |
| UC006 | 金额 ≥ 5000 触发复核 | boundary |

> 完整字段见 .allforai/use-case/use-case-tree.json
```

---

### Step 4：端到端用例生成（需 business-flows.json，quick 模式跳过）

**前置检查：** 若 `.allforai/product-map/business-flows.json` 不存在，跳过此步骤。

读取 `business-flows.json`，为每条完整流（`gap_count == 0`）生成端到端用例：

**E2E 用例格式（JSON）：**

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "id": "E2E-F001-01",
  "type": "e2e",
  "flow_ref": "F001",
  "title": "异常处理全链路_正常流",
  "given": ["用户有已完成的记录", "服务提供者后台已登录"],
  "steps": [
    {
      "seq": 1,
      "actor": "终端用户",
      "system": "user-app",
      "task_ref": "user-app:T001",
      "action": "用户提交异常申请"
    },
    {
      "seq": 2,
      "actor": "服务提供者",
      "system": "provider-backend",
      "task_ref": "provider-backend:T015",
      "action": "服务提供者收到异常通知"
    },
    {
      "seq": 3,
      "actor": "服务提供者",
      "system": "provider-backend",
      "task_ref": "provider-backend:T016",
      "action": "服务提供者处理异常申请"
    },
    {
      "seq": 4,
      "actor": "终端用户",
      "system": "user-app",
      "task_ref": "user-app:T002",
      "action": "用户查看处理结果"
    }
  ],
  "then": ["用户看到异常申请状态为已处理", "服务提供者后台该申请标记为完结"]
}
```

**Markdown 格式（报告追加）：**

```
E2E-F001-01  异常处理全链路_正常流  [e2e]
```

E2E 用例写入 `use-case-tree.json`（追加到对应角色的 `cases` 数组）和 `use-case-report.md`（追加到末尾的「端到端用例」章节）。

有缺口的流（`gap_count > 0`）不生成 E2E 用例，在报告中标注：「F001 含 1 个缺口，待缺口修复后可生成 E2E 用例」。

#### E2E 排序验证（Step 4 子步骤）

对每条生成的 E2E 用例，执行以下链路验证：

| 检查 | Flag | 触发条件 | 严重级 |
|------|------|---------|--------|
| 前置条件链 | `BROKEN_PRECONDITION_CHAIN` | seq N 产出语义不覆盖 seq N+1 prerequisites | 高 |
| 前置条件不可验 | `UNVERIFIABLE_PRECONDITION` | 任一 step 对应 task 缺少 prerequisites 或 outputs | 低（WARNING） |
| 交接数据断裂 | `MISSING_HANDOFF_DATA` | handoff.data 中的项在上游 task 中无语义匹配 | 中 |
| 终止状态弱 | `WEAK_TERMINAL` | 最后节点 task 无 outputs.messages/states 且 main_flow 末步无感知语义 | 中 |

**检查逻辑**：
1. **前置条件链**：对连续的 seq N 和 seq N+1，检查 N 对应 task 的 `outputs`/`main_flow` 末步是否语义覆盖 N+1 对应 task 的 `prerequisites`。关键词匹配即可（不要求完全一致）。
2. **前置条件不可验**：若任一 step 对应的 task 缺少 `prerequisites` 或 `outputs` 字段，标记为 `UNVERIFIABLE_PRECONDITION`（WARNING 级，不阻断）。
3. **交接数据断裂**：若 flow node 有 `handoff.data`，检查其中每项在上游 task 的 `main_flow`/`outputs` 中是否有语义匹配。
4. **终止状态弱**：最后一个 step 对应的 task，检查是否有 `outputs.messages`、`outputs.states`、或 `main_flow` 末步含感知语义关键词（查/展示/通知/反馈/确认/完成）。

**E2E 用例追加 `ordering_issues` 字段**：

```json
"ordering_issues": [
  {
    "flag": "MISSING_HANDOFF_DATA",
    "seq_pair": [2, 3],
    "description": "seq 2 → seq 3 交接数据「异常申请ID」在上游 task main_flow 中无匹配",
    "severity": "中"
  }
]
```

**用户确认**：E2E 用例覆盖了所有关键业务流吗？排序验证发现的链路问题需要修复吗？

---

## 生成方式

LLM 直接分析 task-inventory + experience-map + business-flows，生成结构化用例树。用例生成需要理解业务语境来推导异常路径和边界条件。

可选辅助脚本：`../../shared/scripts/product-design/gen_use_cases.py`（用于骨架生成和 XV 交叉验证）。

**输出 schema 约束**：
- `use-case-tree.json` 必须是对象格式，包含 `roles`（数组）+ `summary`（统计）
- 每个 role 下的 use_cases 必须扁平可枚举（`roles[].feature_areas[].tasks[].use_cases[]`）
- 顶层 `summary` 必须包含 `total_use_cases` 计数，便于下游消费
- 每个 use_case 必须有 `id`、`title`、`type`（happy_path/exception/boundary/innovation/e2e）、`given`、`when`、`then`

**XV 交叉验证（v3.3.0+）**：辅助脚本或 LLM 可执行 XV 交叉验证（需 `OPENROUTER_API_KEY` 环境变量）。高严重度边界用例自动追加，弱验收标准自动标记 `xv_flag`。无 API Key 时静默跳过。

### 闭环审计

LLM 生成用例后，追问闭环完整性：

| 闭环类型 | 追问 |
|---------|------|
| **异常闭环** | 每个 happy_path 用例是否有对应的 exception 用例？核心任务的失败路径是否有恢复/重试用例？ |
| **映射闭环** | 每个涉及数据变更的用例（创建/删除/修改）是否有对应的验证用例（查看变更结果）？ |
| **生命周期闭环** | 创建类用例是否有对应的归档/删除/过期用例？ |

闭环缺失 → LLM 补充对应用例 → 重新验证。

---

## 输出文件结构

```
.allforai/use-case/
├── use-case-tree.json       # 机器可读：完整 4 层 JSON 树
├── use-case-tree-{RID}.json # 按角色拆分的用例子集（人类阅读用）
├── use-case-report.md       # 人类可读：摘要级 Markdown
└── use-case-decisions.json  # 用户决策日志（增量复用）
```

### decisions.json 通用格式

```json
[
  {
    "step": "Step 0",
    "item_id": "FA001",
    "item_name": "描述",
    "decision": "confirmed | modified | deferred",
    "reason": "用户备注（可选）",
    "decided_at": "2024-01-15T10:30:00Z"
  }
]
```

- `confirmed`：用户确认无修改
- `modified`：用户修改后确认
- `deferred`：暂不决定，下次运行时重新提问

**加载逻辑**：每个 Step 开始前检查 decisions.json，已 `confirmed` 的条目跳过确认直接沿用。

---

## Flags

| Flag | 含义 |
|------|------|
| `NO_EXCEPTION_CASES` | 任务有 exceptions 但全部被 DEFERRED，无异常用例 |
| `NO_SCREEN_REF` | 用例无界面引用（experience-map 未运行） |
| `INCOMPLETE_THEN` | then 条件为空（task.outputs 未定义） |
| `MISSING_BOUNDARY` | task.rules 存在但未提取出任何 boundary 用例 |
| `BROKEN_PRECONDITION_CHAIN` | E2E 排序：seq N 产出语义不覆盖 seq N+1 prerequisites |
| `UNVERIFIABLE_PRECONDITION` | E2E 排序：step 对应 task 缺少 prerequisites 或 outputs（WARNING） |
| `MISSING_HANDOFF_DATA` | E2E 排序：handoff.data 在上游 task 中无语义匹配 |
| `WEAK_TERMINAL` | E2E 排序：最后节点 task 无感知语义（无 outputs/messages/states） |

---

## 防御性规范

> 通用模式定义见 `docs/defensive-patterns.md`，以下为本技能的具体应用。

### 加载校验
- **`use-case-decisions.json`**：加载时用 `python -m json.tool` 验证 JSON 合法性。解析失败 → 检查 `.bak` → 提示恢复或重新执行 `use-case refresh`。
- **`task-inventory.json`**：前置加载时验证 JSON 合法性。解析失败 → 提示用户重新执行 `product-map` 工作流，终止执行。

### 零结果处理
- **某任务生成 0 用例**：⚠ 标注「任务 {task_id} ({name}) 的 main_flow 为空，无法生成用例，建议在 `product-map` 中补充该任务的 main_flow」，不静默跳过。
- **Step 2 某任务 0 异常用例**：若 task.exceptions 为空 → ⚠ 标注「任务 {task_id} 无异常定义，无法生成异常用例」；若全部被 DEFERRED → 标记 `NO_EXCEPTION_CASES` flag。
- **scope 模式匹配 0 任务**：明确告知「功能区 "{名称}" 未匹配任何任务」，列出现有功能区名称供参考。

### 规模自适应
- **阈值**：以任务数为计量对象。small ≤30 / medium 31–80 / large >80。
- **small**（≤30 任务）：逐任务展示用例，逐步确认。
- **medium**（31–80 任务）：按功能区分组展示摘要，确认功能区级。
- **large**（>80 任务）：脚本生成 `use-case-tree.json`，仅展示统计摘要 + 有 flag 的用例。

### 网络搜索不可用
- **趋势搜索**（动态趋势补充）：工具不可用或无有用结果 → 跳过趋势补充，不影响用例生成主流程。

### 上游过期检测
- **`task-inventory.json`**：加载时比较 `generated_at` 与 `use-case-decisions.json` 最新 `decided_at`。上游更新 → ⚠ 警告「task-inventory 在 use-case 上次运行后被更新，建议重新执行 use-case refresh」。
- **`experience-map.json`**（若存在）：同理比较时间戳。上游更新 → ⚠ 警告「experience-map 已更新，validation 和 exception_flows 数据可能过期」。
- 仅警告不阻断。

### 执行失败保护
- 任何步骤遇到不可恢复错误（JSON 解析失败、必须文件缺失、LLM 生成结果不合法）→ 写入 `.allforai/use-case/use-case-error.json`，包含 `{"error": "...", "step": "...", "timestamp": "..."}`，确保编排器能检测到失败而非静默空目录。

---

## 4 条铁律

### 1. 双格式原则：JSON 给机器，Markdown 给人类

JSON 完整字段，无省略，逐条可执行。Markdown 摘要级，每条用例一行（ID + 标题 + 类型），细节不在报告中重复——完整数据始终在 JSON 里。

### 2. 以功能地图为唯一数据源

只从 task-inventory.json 和 experience-map.json 推导用例，不引入两者之外的场景。发现遗漏场景，先更新 product-map，再重跑 use-case。

### 3. 每步确认，DEFERRED 可延后

异常用例不必一次全做。用户可标记 DEFERRED，不进入本次用例集，记录在 decisions.json 供后续补充。

用户确认结果写入 `use-case-decisions.json`：已确认的功能区分组（Step 0）、被标记为 DEFERRED 的用例（含 id 和原因）。下次运行自动加载，跳过已确认项，不重复询问。`use-case refresh` 可清空缓存并完整重跑。

### 4. 只生成不执行

use-case 只输出用例描述，不触发任何测试执行或代码生成。执行由 AI agent 或 QA 工程师负责。
