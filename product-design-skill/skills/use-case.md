---
name: use-case
description: >
  Use when the user asks to "generate use cases", "write test cases", "create use case document",
  "derive scenarios from product map", "用例", "生成用例", "用例集", "测试用例",
  "从功能地图生成用例", "从界面地图推导用例", "场景覆盖", "用例树",
  or mentions generating Given/When/Then scenarios, deriving test cases from requirements,
  creating use case documents for QA or AI agent execution.
  Requires product-map to have been run first.
version: "2.3.0"
---

# Use Case — 用例集

> 以功能地图和界面地图为输入，推导完整用例：正常流、异常流、边界流

## 目标

以 `task-inventory.json`（必须）和 `screen-map.json`（必须，不存在则自动运行 screen-map）为输入，生成两份用例输出：

- **JSON 机器版**：完整字段，逐条可执行，供 AI agent 和自动化测试直接使用
- **Markdown 人类版**：摘要级，每条用例一行（ID + 标题 + 类型），供 PM / QA / 开发快速浏览

---

## 定位

```
product-map（功能地图）    screen-map（界面地图）    use-case（用例集）
谁用？做什么？有何异常？    在哪做？怎么做？出错怎么办？  推导完整用例，双格式输出
任务层语义                 界面层语义                基于两者，机器可执行
```

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/task-inventory.json`。

---

## 快速开始

```
/use-case              # 完整流程（Step 0-4）
/use-case quick        # 跳过异常流/边界流（Step 2）和 E2E 用例（Step 4），只生成正常流
/use-case scope 退款管理  # 只生成指定功能区的用例
```

## 增强协议（WebSearch + 4D+6V + XV）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：`”risk based testing” + 产品类型 + “case study” + 2025`、`”INVEST user stories” + “real project”`

**4D+6V 重点**：`then` 覆盖三重成功定义（业务成功 + 技术成功 + 体验成功）；高频/高风险用例覆盖至少 4/6 视角，减少”可执行但不可解释”。

**XV 交叉验证**（Step 3 双格式输出后）：

| 验证点 | task_type | 发送内容 | 写入字段 |
|--------|-----------|----------|----------|
| 边界条件补充 | `edge_case_generation`→deepseek | 高频/高风险用例摘要（Given/When/Then） + 关联任务的 rules | cross_model_review.additional_edge_cases |
| 验收标准审查 | `acceptance_criteria_review`→gpt | 高频/高风险用例的 then 字段 + 任务的 acceptance_criteria | cross_model_review.acceptance_gaps |

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
角色 R001 客服专员
└── 功能区 FA001 退款管理
    └── 任务 T001 创建并提交退款单
        ├── UC001  正常提交退款单              [happy_path]
        ├── UC002  金额超限 → 拦截并提示        [exception]
        ├── UC003  重复提交 → 幂等去重          [exception]
        ├── UC004  权限不足 → 提示申请          [exception]
        ├── UC005  审批超时 48h → 自动升级      [exception]
        └── UC006  金额 ≥ 5000 → 触发复核流程   [boundary]
```

---

## 用例类型与来源

| 用例类型 | 来源字段 | 数量 |
|----------|----------|------|
| `happy_path` | `task.prerequisites` + `task.main_flow` + `task.outputs` | 每任务 1 条 |
| `exception` | `task.exceptions` 每条 + `screen.exception_flows`（若有） | 每异常 1 条 |
| `boundary` | `task.rules` 中含边界语义（≥ / ≤ / 幂等 / 超时）的条目 | 按规则提取 |
| `validation` | `screen.action.validation_rules`（需 screen-map） | 按校验规则提取 |

---

## 全自动模式

**激活条件**（同时满足）：
1. `.allforai/product-concept/product-concept.json` 存在且含 `pipeline_preferences` 字段
2. 上下文含 `__orchestrator_auto: true`（由 `/product-design full` 编排器传入）

**未同时满足** → 保持标准交互模式（当前行为不变）。

**行为变化**：

| 步骤 | 标准模式 | 全自动模式 |
|------|----------|-----------|
| **Step 0 功能区分组确认** | AskUserQuestion 确认 | 自动确认，记入 `pipeline-decisions.json`（`decision: "auto_confirmed"`） |
| **Step 1 正常流确认** | AskUserQuestion 确认 | 自动确认 |
| **Step 2 异常/边界确认** | AskUserQuestion 确认 | 自动确认（所有用例自动生成，DEFERRED 标记不触发） |
| **Step 4 E2E 确认** | AskUserQuestion 确认 | 自动确认 |

**安全护栏**（自动模式下仍然停下来问用户）：
- ERROR 级验证失败（use-case-tree.json 生成失败、task 引用断裂）

---

## 工作流

```
前置检查：
  .allforai/product-map/task-inventory.json  必须存在，否则终止
  .allforai/screen-map/screen-map.json       必须（不存在则自动运行 screen-map 生成）
  .allforai/use-case/use-case-decisions.json 若存在则加载，跳过已确认项

Step 0: 功能区分组
      AI 按语义将任务分组为功能区（如「退款管理」「订单查询」）
      → 用户确认，可合并/拆分/重命名功能区
      ↓
Step 1: 正常流用例生成
      每个任务生成 1 条 happy_path 用例
      Given ← task.prerequisites
      When  ← task.main_flow（逐步展开）
      Then  ← task.outputs.states + outputs.messages + outputs.notifications + audit.recorded_actions
      → 用户确认，可补充/修改
      ↓
Step 2: 异常流 + 边界用例生成（quick 模式跳过）
      每条 task.exceptions → 1 条 exception 用例
      task.rules 含边界语义 → boundary 用例
      screen.action.validation_rules → validation 用例（需 screen-map）
      screen.action.exception_flows 注入对应 exception 用例的 then 字段
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
      存在 → 加载索引（< 5KB），获取任务 id/task_name/frequency/owner_role/risk_level + 模块分组
      不存在 → 回退到 Phase 2 全量加载

  Phase 2 — 按需加载完整数据：
    检查 .allforai/product-map/task-inventory.json
      存在 → 加载任务和角色数据
      不存在 → 提示：「请先运行 /product-map 生成功能地图，再运行 /use-case」，终止

检查 .allforai/screen-map/screen-map.json：
  - 存在 → 加载界面数据，标注「已注入界面上下文」
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
      "name": "退款管理",
      "task_ids": ["T001", "T002", "T003"]
    },
    {
      "id": "FA002",
      "name": "订单查询",
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
  "title": "正常提交退款单",
  "type": "happy_path",
  "priority": "高",
  "given": [
    "已有订单",
    "有退款申请权限",
    "订单状态为已支付"
  ],
  "when": [
    "选择订单",
    "系统自动带出支付信息",
    "填写退款原因与金额",
    "金额校验通过（≤ 可退金额）",
    "点击「提交退款申请」"
  ],
  "then": [
    "退款单状态变为「财务待审」",
    "页面提示：退款单已提交，财务将在 24h 内处理",
    "财务收到审核通知",
    "操作日志记录：创建、提交、操作人、时间"
  ],
  "screen_ref": "S001",
  "action_ref": "提交退款申请",
  "exception_source": null,
  "flags": []
}
```

**人类版（Markdown 摘要）**：

```markdown
| UC001 | 正常提交退款单 | happy_path |
```

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
    "已有订单",
    "有退款申请权限",
    "填写退款金额 > 原支付金额"
  ],
  "when": [
    "点击「提交退款申请」按钮（S001 / click_depth=1）"
  ],
  "then": [
    "退款单未创建，数据库无新记录",
    "按钮保持可点击，不跳转",
    "金额字段边框变红，显示：退款金额不可超过原订单金额，可退 ¥{max_amount}",
    "顶部错误汇总出现：请检查退款金额"
  ],
  "screen_ref": "S001",
  "action_ref": "提交退款申请",
  "validation_rule": "金额 ≤ 原订单金额",
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
    "已有订单",
    "有退款申请权限",
    "填写退款金额 = 5000"
  ],
  "when": [
    "点击「提交退款申请」"
  ],
  "then": [
    "退款单创建，状态为「主管待复核」而非「财务待审」",
    "主管收到复核通知",
    "普通财务审核流程不触发"
  ],
  "screen_ref": "S001",
  "action_ref": "提交退款申请",
  "rule_source": "task.rules[2]",
  "flags": []
}
```

**validation 用例（来自 screen.action.validation_rules）机器版**：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 screen-map 分析结果决定，不限行业。

```json
{
  "id": "UC007",
  "title": "退款原因为空 → 校验拦截",
  "type": "validation",
  "priority": "中",
  "given": [
    "已有订单",
    "有退款申请权限",
    "退款原因字段留空"
  ],
  "when": [
    "点击「提交退款申请」按钮（S001 / click_depth=1）"
  ],
  "then": [
    "退款单未创建",
    "退款原因字段边框变红，显示：请填写退款原因",
    "按钮保持可点击，不跳转"
  ],
  "screen_ref": "S001",
  "action_ref": "提交退款申请",
  "validation_rule": "退款原因不能为空（screen.action.validation_rules[0]）",
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
  "version": "2.3.0",
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
    "screen_map_injected": true
  },
  "roles": [
    {
      "id": "R001",
      "name": "客服专员",
      "feature_areas": [
        {
          "id": "FA001",
          "name": "退款管理",
          "tasks": [
            {
              "id": "T001",
              "task_name": "创建并提交退款单",
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

## R001 客服专员

### 退款管理

**T001 创建并提交退款单**（6 条用例）

| ID | 标题 | 类型 |
|----|------|------|
| UC001 | 正常提交退款单 | happy_path |
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
  "title": "售后全链路_正常流",
  "given": ["用户有已完成订单", "商户后台已登录"],
  "steps": [
    {
      "seq": 1,
      "actor": "买家",
      "system": "user-app",
      "task_ref": "user-app:T001",
      "action": "用户提交售后申请"
    },
    {
      "seq": 2,
      "actor": "商户",
      "system": "merchant-backend",
      "task_ref": "merchant-backend:T015",
      "action": "商户收到售后通知"
    },
    {
      "seq": 3,
      "actor": "商户",
      "system": "merchant-backend",
      "task_ref": "merchant-backend:T016",
      "action": "商户处理售后申请"
    },
    {
      "seq": 4,
      "actor": "买家",
      "system": "user-app",
      "task_ref": "user-app:T002",
      "action": "用户查看处理结果"
    }
  ],
  "then": ["用户看到售后申请状态为已处理", "商户后台该申请标记为完结"]
}
```

**Markdown 格式（报告追加）：**

```
E2E-F001-01  售后全链路_正常流  [e2e]
```

E2E 用例写入 `use-case-tree.json`（追加到对应角色的 `cases` 数组）和 `use-case-report.md`（追加到末尾的「端到端用例」章节）。

有缺口的流（`gap_count > 0`）不生成 E2E 用例，在报告中标注：「F001 含 1 个缺口，待缺口修复后可生成 E2E 用例」。

**用户确认**：E2E 用例覆盖了所有关键业务流吗？有需要补充的跨任务场景吗？

---

## 预置脚本（优先使用）

检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_use_cases.py` 是否存在：
- **存在** → `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_use_cases.py <BASE> --mode auto`
- **不存在** → 回退到 LLM 生成脚本（向后兼容）

预置脚本保证 schema 一致性和零语法错误。使用 `_common.get_screen_tasks()` 统一读取界面任务引用，使用 `_common.get_flow_nodes()` 读取业务流节点（`nodes` 字段，非 `steps`）。

---

## 输出文件结构

```
.allforai/use-case/
├── use-case-tree.json       # 机器可读：完整 4 层 JSON 树
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
| `NO_SCREEN_REF` | 用例无界面引用（screen-map 未运行） |
| `INCOMPLETE_THEN` | then 条件为空（task.outputs 未定义） |
| `MISSING_BOUNDARY` | task.rules 存在但未提取出任何 boundary 用例 |

---

## 防御性规范

> 通用模式定义见 `docs/defensive-patterns.md`，以下为本技能的具体应用。

### 加载校验
- **`use-case-decisions.json`**：加载时用 `python -m json.tool` 验证 JSON 合法性。解析失败 → 检查 `.bak` → 提示恢复或重新运行 `/use-case refresh`。
- **`task-inventory.json`**：前置加载时验证 JSON 合法性。解析失败 → 提示用户重新运行 `/product-map`，终止执行。

### 零结果处理
- **某任务生成 0 用例**：⚠ 标注「任务 {task_id} ({task_name}) 的 main_flow 为空，无法生成用例，建议补充 /product-map 中该任务的 main_flow」，不静默跳过。
- **Step 2 某任务 0 异常用例**：若 task.exceptions 为空 → ⚠ 标注「任务 {task_id} 无异常定义，无法生成异常用例」；若全部被 DEFERRED → 标记 `NO_EXCEPTION_CASES` flag。
- **scope 模式匹配 0 任务**：明确告知「功能区 "{名称}" 未匹配任何任务」，列出现有功能区名称供参考。

### 规模自适应
- **阈值**：以任务数为计量对象。small ≤30 / medium 31–80 / large >80。
- **small**（≤30 任务）：逐任务展示用例，逐步确认。
- **medium**（31–80 任务）：按功能区分组展示摘要，确认功能区级。
- **large**（>80 任务）：脚本生成 `use-case-tree.json`，仅展示统计摘要 + 有 flag 的用例。

### WebSearch 故障
- **趋势搜索**（动态趋势补充）：工具不可用或无有用结果 → 跳过趋势补充，不影响用例生成主流程。

### 上游过期检测
- **`task-inventory.json`**：加载时比较 `generated_at` 与 `use-case-decisions.json` 最新 `decided_at`。上游更新 → ⚠ 警告「task-inventory 在 use-case 上次运行后被更新，建议重新运行 /use-case refresh」。
- **`screen-map.json`**（若存在）：同理比较时间戳。上游更新 → ⚠ 警告「screen-map 已更新，validation 和 exception_flows 数据可能过期」。
- 仅警告不阻断。

---

## 4 条铁律

### 1. 双格式原则：JSON 给机器，Markdown 给人类

JSON 完整字段，无省略，逐条可执行。Markdown 摘要级，每条用例一行（ID + 标题 + 类型），细节不在报告中重复——完整数据始终在 JSON 里。

### 2. 以功能地图为唯一数据源

只从 task-inventory.json 和 screen-map.json 推导用例，不引入两者之外的场景。发现遗漏场景，先更新 product-map，再重跑 use-case。

### 3. 每步确认，DEFERRED 可延后

异常用例不必一次全做。用户可标记 DEFERRED，不进入本次用例集，记录在 decisions.json 供后续补充。

用户确认结果写入 `use-case-decisions.json`：已确认的功能区分组（Step 0）、被标记为 DEFERRED 的用例（含 id 和原因）。下次运行自动加载，跳过已确认项，不重复询问。`/use-case refresh` 清空缓存重跑。

### 4. 只生成不执行

use-case 只输出用例描述，不触发任何测试执行或代码生成。执行由 AI agent 或 QA 工程师负责。
