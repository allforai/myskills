# use-case 技能 + 双格式输出原则 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 新增 `use-case` 技能（从 product-map + screen-map 推导完整用例，JSON 机器全量 + Markdown 人类摘要），并将双格式输出原则同步更新到 product-map 和 screen-map 的报告规范。

**Architecture:** 三波并行执行。Wave 1 新建 use-case 技能文件，同时更新 product-map/screen-map 的报告规范；Wave 2 更新命令文件和 SKILL.md；Wave 3 更新 README 和 plugin.json。所有文件均在 `/home/hello/Documents/myskills/product-audit-skill/` 下操作。

**Tech Stack:** Markdown 技能文件，JSON Schema 示例，无代码依赖。

**Design doc:** `docs/plans/2026-02-24-use-case-skill-design.md`

---

## 执行顺序

```
Wave 1（并行）：Task 1 + Task 2 + Task 3 + Task 4
Wave 2（依赖 Wave 1）：Task 5 + Task 6 + Task 7
Wave 3（依赖 Wave 2）：Task 8 + Task 9
```

---

## Task 1：新建 `skills/use-case.md`

**Files:**
- Create: `skills/use-case.md`

**Step 1: 写入文件**

写入以下完整内容：

```markdown
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
- **Markdown 人类版**：摘要级，一条用例三行，供 PM / QA / 开发快速浏览

---

## 定位

```
product-map（功能地图）    screen-map（界面地图）    use-case（用例集）
谁用？做什么？有何异常？    在哪做？怎么做？出错怎么办？  推导完整用例，双格式输出
任务层语义                 界面层语义                基于两者，机器可执行
```

**前提**：必须先运行 `product-map`，生成 `.product-map/task-inventory.json`。

---

## 快速开始

```
/use-case              # 完整流程（Step 0-3）
/use-case quick        # 跳过异常流/边界流（Step 2），只生成正常流
/use-case scope 退款管理  # 只生成指定功能区的用例
```

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
  .product-map/task-inventory.json  必须存在，否则终止
  .screen-map/screen-map.json       可选，存在则注入 validation_rules + exception_flows
  .use-case/use-case-decisions.json 若存在则加载，跳过已确认项

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
```

**核心原则：每个 Step 结束都有用户确认，用户是权威。**

---

### 前置检查

```
检查 .product-map/task-inventory.json：
  - 存在 → 加载任务和角色数据
  - 不存在 → 提示：「请先运行 /product-map 生成功能地图，再运行 /use-case」，终止

检查 .screen-map/screen-map.json：
  - 存在 → 加载界面数据，标注「已注入界面上下文」
  - 不存在 → 继续，标注「未注入界面上下文，exception_flows 和 validation_rules 将为空」
```

---

### Step 0：功能区分组

读取 task-inventory.json 中所有任务，按语义归组：

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

每个任务生成 1 条 happy_path 用例，Given/When/Then 三段填充：

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

**用户确认**：正常流步骤完整吗？预期结果有没有遗漏？

---

### Step 2：异常流 + 边界用例生成

**exception 用例（来自 task.exceptions）**：

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

**boundary 用例（来自 task.rules 边界语义）**：

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

**用户确认**：异常场景覆盖完整吗？有没有需要标记 DEFERRED 的？

---

### Step 3：双格式输出

#### 机器版 `use-case-tree.json`

完整 4 层 JSON 树：

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
                { ...UC001... },
                { ...UC002... }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

#### 人类版 `use-case-report.md`

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

> 完整字段见 .use-case/use-case-tree.json
```

---

## 输出文件结构

```
.use-case/
├── use-case-tree.json       # 机器可读：完整 4 层 JSON 树
├── use-case-report.md       # 人类可读：摘要级 Markdown
└── use-case-decisions.json  # 用户决策日志（增量复用）
```

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

JSON 完整字段，无省略，逐条可执行。Markdown 摘要级，每条用例一行标题 + 类型，细节不重复。

### 2. 以功能地图为唯一数据源

只从 task-inventory.json 和 screen-map.json 推导用例，不引入两者之外的场景。发现遗漏场景，先更新 product-map，再重跑 use-case。

### 3. 每步确认，DEFERRED 可延后

异常用例不必一次全做。用户可标记 DEFERRED，不进入本次用例集，记录在 decisions.json 供后续补充。

### 4. 只生成不执行

use-case 只输出用例描述，不触发任何测试执行或代码生成。执行由 AI agent 或 QA 工程师负责。
```

**Step 2: 验证**

读取文件，确认：
- frontmatter 有 name/description/version
- 包含 Step 0-3 工作流
- 包含完整 JSON Schema 示例
- 包含双格式说明（JSON 机器版 + Markdown 人类版）
- 包含 4 条铁律

---

## Task 2：新建 `commands/use-case.md`

**Files:**
- Create: `commands/use-case.md`

**Step 1: 写入文件**

```markdown
---
description: "用例集：从功能地图和界面地图推导完整用例，输出 JSON 机器版和 Markdown 人类版。模式: full / quick / scope"
argument-hint: "[mode: full|quick|scope] [功能区名]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion"]
---

# Use Case — 用例集

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 前置检查

执行前必须检查：

1. `.product-map/task-inventory.json` 是否存在
   - 存在 → 加载任务和角色数据，继续执行
   - 不存在 → 输出提示并终止：
     ```
     ⚠️ 未找到 .product-map/task-inventory.json
     请先运行 /product-map 建立功能地图，再运行 /use-case。
     ```

2. `.screen-map/screen-map.json` 是否存在
   - 存在 → 标注「已注入界面上下文：validation_rules + exception_flows」
   - 不存在 → 标注「未注入界面上下文，exception_flows 将为空；建议先运行 /screen-map」

3. `.use-case/use-case-decisions.json` 若存在 → 自动加载，跳过已确认项

## 模式路由

- **无参数 或 `full`** → 完整流程：Step 0 → Step 1 → Step 2 → Step 3
- **`quick`** → 快速模式：Step 0 → Step 1 → Step 3（跳过 Step 2 异常流/边界用例）
- **`scope <功能区名>`** → 限定范围：全流程，但仅生成指定功能区的用例

## 执行流程

1. 参考已加载的 `skills/use-case.md` 中的目标定义、工作流和铁律
2. 根据模式按需执行对应步骤
3. 按工作流执行，**每个 Step 必须有用户确认环节**
4. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要**

## 详细文档（按需用 Read 工具加载）

- `${CLAUDE_PLUGIN_ROOT}/skills/use-case.md` — 完整工作流、Schema、铁律

## Step 执行要求

每个 Step 完成后：
1. 将结果写入 `.use-case/` 目录下对应文件
2. 向用户展示结果摘要
3. 等待用户确认后才进入下一个 Step

## 报告输出要求（强制执行）

执行完成后，必须在对话中直接输出以下报告摘要：

```
## 用例集报告摘要

> 执行时间: {时间}
> 执行模式: {full/quick/scope}
> 界面上下文: {已注入 / 未注入}

### 总览

| 维度 | 数量 |
|------|------|
| 角色 | X 个 |
| 功能区 | X 个 |
| 任务 | X 个 |
| 用例总数 | X 条 |
| 正常流 | X 条 |
| 异常流 | X 条 |
| 边界用例 | X 条 |

### 用例分布（按功能区）

（每行：功能区名 / 任务数 / 用例数 / 异常覆盖率）

### Flags 汇总

（逐条列出：flag 类型 / 涉及任务 / 说明）

### 下一步

1. 将 use-case-tree.json 交给 AI agent 执行自动化测试
2. 将 use-case-report.md 交给 QA 执行手工测试
3. 运行 /feature-gap 检测功能缺口（与用例集互补）

> 机器版: `.use-case/use-case-tree.json`
> 人类版: `.use-case/use-case-report.md`
> 决策日志: `.use-case/use-case-decisions.json`
```

## 铁律（强制执行）

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/use-case.md` 的「4 条铁律」章节。

1. **双格式原则** — JSON 完整字段给机器，Markdown 摘要级给人类
2. **以功能地图为唯一数据源** — 只从 task-inventory.json 和 screen-map.json 推导
3. **每步确认，DEFERRED 可延后** — 用户可标记任何用例为 DEFERRED
4. **只生成不执行** — 输出用例描述，不触发测试执行
```

**Step 2: 验证**

读取文件，确认：
- frontmatter 有 description/argument-hint/allowed-tools
- 前置检查包含 task-inventory.json + screen-map.json 两项
- 模式路由覆盖 full/quick/scope
- 报告摘要模板包含用例分布表

---

## Task 3：更新 `skills/product-map.md` — Step 6 报告规范改为摘要级

**Files:**
- Modify: `skills/product-map.md`

**Step 1: 定位并替换 Step 6 中的报告结构**

找到当前 `product-map-report.md` 的报告结构章节（包含 `## 概览` 到 `## 业务约束清单` 的部分），替换为以下摘要级规范：

```
#### `product-map-report.md` — 可读摘要（给人看）

报告结构（摘要级，细节留 JSON）：

\```
# 产品地图摘要

角色 X 个 · 任务 X 个 · 高频任务 X 个 · 冲突 X 个 · 约束 X 条

## 角色总览
| 角色 | 职责 | KPI |
|------|------|-----|
| 客服专员 | 处理退款、投诉 | 处理时效 < 2h |

## 高频任务（Top 20%）
- T001 创建退款单（高频 / 高风险 / 跨部门）
- T005 查询订单（高频 / 低风险）

## 冲突摘要
- C001 T001 与 T003 金额规则矛盾（高）

## 业务约束摘要
- CN001 退款金额不可超过原订单金额（硬约束）
- CN002 所有退款操作留存日志 3 年（合规）

> 完整数据见 .product-map/product-map.json
\```
```

**Step 2: 验证**

确认 Step 6 的报告结构部分已改为摘要级，不含逐字段枚举，末尾有 `> 完整数据见` 指引。

---

## Task 4：更新 `skills/screen-map.md` — Step 3 报告规范改为摘要级

**Files:**
- Modify: `skills/screen-map.md`

**Step 1: 定位并替换 Step 3 中的报告结构**

找到 `screen-map-report.md` 的报告结构章节，替换为以下摘要级规范：

```
#### `screen-map-report.md` — 可读摘要（给人看）

报告结构（摘要级，细节留 JSON）：

\```
# 界面地图摘要

界面 X 个 · 操作 X 个 · 覆盖任务 X/X · 异常缺口 X 个 · 界面冲突 X 个

## 高频操作（帕累托 Top 20%）
- 退款申请页 → 提交退款申请（click_depth=1）
- 订单列表页 → 搜索订单（click_depth=1）

## 问题清单
| 类型 | 界面 | 说明 |
|------|------|------|
| SILENT_FAILURE | S008 批量导出页 | 导出失败无提示 |
| UNHANDLED_EXCEPTION | S001 退款申请页 | 审批超时异常无响应 |

> 完整数据见 .screen-map/screen-map.json
\```
```

**Step 2: 验证**

确认 Step 3 的报告结构部分已改为摘要级，`screen-map-report.md` 的结构块内容不超过 20 行。

---

## Task 5：更新 `commands/product-map.md` — 报告模板简化

**Files:**
- Modify: `commands/product-map.md`

**Step 1: 定位并替换报告摘要模板**

找到 `## 报告输出要求` 中的报告摘要模板，将「界面」行和「高频操作清单」的逐字段描述，替换为：

```markdown
### 高频任务清单

（每行：任务名 / 角色 / 频次 / 风险等级）

### 冲突摘要（仅 full 模式）

（每行：冲突描述 / 严重度 / 涉及任务）
```

删除报告摘要中原有的「界面」行（`| 界面 | X 个 |`）和「高频操作（帕累托 Top 20%）」列表（已移至 screen-map）。

**Step 2: 验证**

确认报告摘要模板中不再有界面相关行，使用「任务清单」而非「高频操作清单」。

---

## Task 6：更新 `commands/screen-map.md` — 报告模板简化

**Files:**
- Modify: `commands/screen-map.md`

**Step 1: 定位并替换报告摘要模板**

找到 `## 报告输出要求` 中的报告摘要模板，将详细操作列表替换为：

```markdown
### 高频操作（帕累托 Top 20%）

（每行：界面名 → 操作按钮 / click_depth）

### 问题清单（仅 full 模式）

（每行：flag 类型 / 界面 / 一句话说明）
```

**Step 2: 验证**

确认摘要模板中「高频操作清单」和「异常覆盖缺口」两节已简化为每行一条格式。

---

## Task 7：更新 `SKILL.md` — 新增 use-case + 双格式铁律 + 版本 2.2.0

**Files:**
- Modify: `SKILL.md`

**Step 1: 更新 frontmatter 版本**

将 `version: "2.1.0"` 改为 `version: "2.2.0"`。

将 description 中的技能列表更新为包含 use-case：
```
five skills: product-map, screen-map, feature-gap, feature-prune, seed-forge
```
改为：
```
six skills: product-map, screen-map, use-case, feature-gap, feature-prune, seed-forge
```

**Step 2: 在 `### 2. screen-map` 之后新增 use-case 节**

```markdown
### 3. use-case — 用例集

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/use-case.md`

以功能地图和界面地图为输入，推导完整用例，双格式输出。

- 四层树结构：角色 → 功能区 → 任务 → 用例
- 每任务生成：1 条正常流 + N 条异常流 + M 条边界用例
- JSON 机器版：完整字段，可供 AI agent 和自动化测试执行
- Markdown 人类版：摘要级，供 PM / QA 快速浏览

\```
/use-case              # 完整流程
/use-case quick        # 只生成正常流，跳过异常流
/use-case scope 退款管理  # 只生成指定功能区的用例
\```
```

将原来的 `### 3. feature-gap` 改为 `### 4. feature-gap`，`### 4. feature-prune` 改为 `### 5. feature-prune`，`### 5. seed-forge` 改为 `### 6. seed-forge`。

**Step 3: 在定位图中新增 use-case 节点**

在 `screen-map` 行之后，`feature-gap` 行之前，新增：
```
├── use-case    推导完整用例，双格式输出（JSON 机器版 + Markdown 人类版）   基于 product-map + screen-map
```

**Step 4: 新增「输出规范」铁律节**

在推荐工作流之后新增：

```markdown
## 输出规范（全套件铁律）

**JSON 给机器，Markdown 给人类。**

| 文件类型 | 受众 | 密度 |
|----------|------|------|
| `*.json` | AI agent、自动化测试 | 完整字段，逐条可执行，无省略 |
| `*-report.md` | PM、QA、开发 | 摘要级，突出问题和结论，不列每条字段 |

所有技能的 Markdown 报告只呈现「有什么问题、结论是什么」，不重复 JSON 中已有的字段细节。完整数据始终在 JSON 文件中。
```

**Step 5: 更新推荐工作流图，加入 use-case**

```
product-map（必须先跑）
    ↓ 输出 .product-map/product-map.json + task-inventory.json
    │
    ├── screen-map（可选，推荐）
    │       ↓ 输出 .screen-map/screen-map.json
    │
    ├── use-case（可选，需 product-map；有 screen-map 时更完整）
    │       ↓ 输出 .use-case/use-case-tree.json + use-case-report.md
    │
    ├── feature-gap（Step 1 基于 product-map，Step 2/3 需要 screen-map）
    ├── feature-prune（Step 1 基于 product-map，Step 2 需要 screen-map）
    └── seed-forge（只需 product-map）
```

**Step 6: 验证**

确认版本为 2.2.0，SKILL.md 包含 6 个技能节，定位图有 use-case 行，有「输出规范」章节。

---

## Task 8：更新 `README.md`

**Files:**
- Modify: `README.md`

**Step 1: 更新工作流图**

将当前工作流图替换为：

```
product-map（建功能图）
    ↓ 输出 .product-map/product-map.json + task-inventory.json
    │
    ├── screen-map（可选，建界面图）
    │       ↓ 输出 .screen-map/screen-map.json
    │
    ├── use-case（可选，生成用例集）
    │       ↓ 输出 .use-case/use-case-tree.json（机器）+ use-case-report.md（人类）
    │
    ├── 功能查漏   — 地图说有的，现在有没有？
    ├── 功能剪枝   — 地图里有的，该不该留？
    └── seed-forge — 按地图生成真实感种子数据
```

**Step 2: 新增 use-case 技能说明**

在 `### screen-map` 之后，`### feature-gap` 之前，新增：

```markdown
### use-case — 用例集

> 以功能地图和界面地图为输入，推导完整用例，双格式输出。

- **树结构**：角色 → 功能区 → 任务 → 用例（4 层）
- **正常流**：从 main_flow 和 outputs 推导，每任务 1 条
- **异常流**：从 exceptions 推导，每条异常 1 条用例
- **边界用例**：从 rules 中提取边界语义
- **JSON 机器版**：完整 Given/When/Then，含 screen_ref、action_ref、逐条可验证的 then
- **Markdown 人类版**：每条用例三行（标题/类型/表格），不重复字段细节
```

**Step 3: 新增 use-case 输出表**

在 `### screen-map → `.screen-map/`` 之后新增：

```markdown
### use-case → `.use-case/`

| 文件 | 内容 |
|------|------|
| `use-case-tree.json` | 机器可读：完整 4 层 JSON 树（Given/When/Then 全量） |
| `use-case-report.md` | 人类可读：摘要级 Markdown（每条用例一行） |
| `use-case-decisions.json` | 用户决策日志 |
```

**Step 4: 更新使用说明，新增第三步**

在「第二步（可选）：建立界面地图」之后，新增：

```markdown
### 第三步（可选）：生成用例集

\```bash
/use-case              # 完整流程（正常流+异常流+边界用例）
/use-case quick        # 只生成正常流
/use-case scope 退款管理  # 只生成指定功能区
\```
```

**Step 5: 更新核心原则，新增双格式原则**

在核心原则列表中新增：

```
8. **JSON 给机器，Markdown 给人** — JSON 完整字段无省略，Markdown 摘要级突出结论，细节不重复
```

**Step 6: 验证**

确认 README 包含 use-case 技能说明、输出表、工作流图更新、第三步使用说明、第 8 条原则。

---

## Task 9：更新 `.claude-plugin/plugin.json`

**Files:**
- Modify: `.claude-plugin/plugin.json`

**Step 1: 写入更新内容**

```json
{
  "name": "product-audit",
  "description": "Product audit suite: product-map (build product map), screen-map (map screens and exception states), use-case (generate use case tree), feature-gap (detect feature gaps), feature-prune (prune over-design), seed-forge (generate realistic seed data). 产品审计套件：建立产品地图、界面与异常状态地图、用例集（双格式）、功能查漏、功能剪枝、种子数据锻造。",
  "version": "2.2.0",
  "author": { "name": "dv" }
}
```

**Step 2: 验证**

确认 version 为 `"2.2.0"`，description 中包含 use-case。

---

## 验证清单

完成所有 Task 后，逐项确认：

- [ ] `skills/use-case.md` 存在，含 Step 0-3、JSON Schema、双格式说明、4 条铁律
- [ ] `commands/use-case.md` 存在，含前置检查、模式路由、报告模板
- [ ] `skills/product-map.md` Step 6 报告结构为摘要级，有 `> 完整数据见` 指引
- [ ] `skills/screen-map.md` Step 3 报告结构为摘要级，有 `> 完整数据见` 指引
- [ ] `commands/product-map.md` 报告摘要无界面行，使用任务清单格式
- [ ] `commands/screen-map.md` 报告摘要简化为每行一条格式
- [ ] `SKILL.md` 版本 2.2.0，6 个技能节，有输出规范铁律章节
- [ ] `README.md` 包含 use-case 说明、工作流图更新、第 8 条原则
- [ ] `plugin.json` 版本 2.2.0
