---
name: use-case
description: >
  Use when the user asks to "generate use cases", "write test cases", "create use case document",
  "derive scenarios from product map", "用例", "生成用例", "用例集", "测试用例",
  "从功能地图生成用例", "从界面地图推导用例", "场景覆盖", "用例树",
  or mentions generating Given/When/Then scenarios, deriving test cases from requirements,
  creating use case documents for QA or AI agent execution.
  Requires product-map to have been run first.
version: "2.2.0"
---

# Use Case — 用例集

> 以功能地图和界面地图为输入，推导完整用例：正常流、异常流、边界流

## 目标

以 `task-inventory.json`（必须）和 `screen-map.json`（可选）为输入，生成两份用例输出：

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

**scope 模式**：运行与 full 相同的 Step 序列，但跳过 Step 0 分组（直接使用用户指定的功能区名称作为过滤条件），仅为匹配该功能区的任务生成用例。

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

## 工作流

```
前置检查：
  .allforai/product-map/task-inventory.json  必须存在，否则终止
  .allforai/screen-map/screen-map.json       可选，存在则注入 validation_rules + exception_flows
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
  quick 模式：Step 0 → Step 1 → Step 3（跳过 Step 2 异常流 + Step 4 E2E）
```

**核心原则：每个 Step 结束都有用户确认，用户是权威。**

---

### 前置检查

```
检查 .allforai/product-map/task-inventory.json：
  - 存在 → 加载任务和角色数据
  - 不存在 → 提示：「请先运行 /product-map 生成功能地图，再运行 /use-case」，终止

检查 .allforai/screen-map/screen-map.json：
  - 存在 → 加载界面数据，标注「已注入界面上下文」
  - 不存在 → 继续，标注「未注入界面上下文，exception_flows 和 validation_rules 将为空」
```

> **注意**：Step 0（功能区分组）是业务决策步骤，需用户确认，因此编为 Step 0 而非前置检查。前置检查只验证文件存在与否，不等待用户输入。

---

### Step 0：功能区分组

读取 task-inventory.json 中所有任务，按语义归组：

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

**priority 取值**：`高` / `中` / `低`。从任务的 `frequency` 和 `risk_level` 综合推导 — 高频或高风险任务的用例为高优先级，低频且低风险为低优先级。

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
  "version": "2.2.0",
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
