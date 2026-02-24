# 设计文档：use-case 技能 + 双格式输出原则

**日期**：2026-02-24
**版本**：2.2.0
**范围**：新增 use-case 技能，同步更新 product-map / screen-map 报告为摘要级

---

## 背景与动机

product-map 和 screen-map 已覆盖"功能层"和"界面层"，两者合并即可推导出完整用例：

- **谁**（角色）**在什么场景**（前置条件）**做什么**（操作步骤）**期望什么结果**（断言）
- 加上**异常场景**（task.exceptions → exception 用例）和**边界场景**（task.rules → boundary 用例）

同时发现现有报告对人类不够友好：详细 JSON 字段在 Markdown 中原样呈现，人读起来信息过载。

---

## 核心设计决策

### 决策 1：双格式输出原则（全套件统一）

| 文件类型 | 受众 | 密度原则 |
|----------|------|----------|
| `*.json` | 机器（AI agent、自动化测试） | 完整字段，逐条可执行，无省略 |
| `*-report.md` | 人类（PM、QA、开发） | 摘要级，突出问题和结论，字段细节不重复 |

适用范围：use-case（新建）、product-map（更新报告规范）、screen-map（更新报告规范）。

### 决策 2：use-case 树结构（4 层）

```
角色 (Role)
└── 功能区 (Feature Area)   — AI 语义分组，用户确认
    └── 任务 (Task)          — 来自 task-inventory.json
        └── 用例 (Use Case)  — 每任务生成 1..N 条
```

### 决策 3：用例类型与来源映射

| 用例类型 | 来源字段 | 数量 |
|----------|----------|------|
| `happy_path` | `task.prerequisites` + `task.main_flow` + `task.outputs` | 每任务 1 条 |
| `exception` | `task.exceptions` 每条 + `screen.exception_flows`（若有） | 每异常 1 条 |
| `boundary` | `task.rules` 中含边界语义的条目 | 按规则提取 |
| `validation` | `screen.action.validation_rules`（需 screen-map） | 按校验规则提取 |

### 决策 4：双格式密度对比

**人类版（Markdown）** — 一句话场景描述 + 3 行 Given/When/Then：

```markdown
#### UC002 金额超限拦截  `exception`
> 退款金额超过可退上限时，系统拦截并提示正确金额。

- **Given**：有效订单，金额填写超限
- **When**：点击提交
- **Then**：拦截 + 红色提示可退金额
```

**机器版（JSON）** — 完整字段，含 screen_ref、validation_rule、逐条可验证的 then：

```json
{
  "id": "UC002",
  "title": "金额超限拦截",
  "type": "exception",
  "priority": "高",
  "given": ["已有订单", "有退款申请权限", "订单状态为已支付", "填写退款金额 > 原支付金额"],
  "when": ["点击「提交退款申请」按钮（S001 / click_depth=1）"],
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

---

## use-case 工作流

```
前置检查：
  .product-map/task-inventory.json  必须存在，否则终止
  .screen-map/screen-map.json       可选，存在则注入 validation_rules + exception_flows

Step 0: 功能区分组
      AI 按语义将任务分组为功能区
      → 用户确认，可合并/拆分/重命名
      → 写入内存（不单独落盘）

Step 1: 正常流用例生成
      每任务 → 1 条 happy_path
      → 用户确认，可补充/修改

Step 2: 异常流 + 边界用例生成
      每条 task.exceptions → 1 条 exception
      task.rules 边界条目 → boundary
      screen.validation_rules → validation（需 screen-map）
      → 用户确认，可标记 DEFERRED

Step 3: 双格式输出
      use-case-tree.json（完整 JSON 树）
      use-case-report.md（人类摘要）
```

---

## 输出文件

### use-case → `.use-case/`

```
.use-case/
├── use-case-tree.json       # 机器可读：完整 4 层 JSON 树
├── use-case-report.md       # 人类可读：摘要级 Markdown
└── use-case-decisions.json  # 用户决策日志（增量复用）
```

### product-map-report.md 摘要级格式

```markdown
# 产品地图摘要

角色 X 个 · 任务 X 个 · 高频任务 X 个 · 冲突 X 个 · 约束 X 条

## 角色总览
| 角色 | 职责一句话 | KPI |

## 高频任务（Top 20%）
- T001 任务名（频次 / 风险 / 跨部门）

## 冲突摘要
- C001 描述（严重度）

> 完整数据见 .product-map/product-map.json
```

### screen-map-report.md 摘要级格式

```markdown
# 界面地图摘要

界面 X 个 · 操作 X 个 · 覆盖任务 X/X · 异常缺口 X 个 · 界面冲突 X 个

## 高频操作（帕累托 Top 20%）
- S001 退款申请页 → 提交退款申请（click_depth=1）

## 问题清单
| 类型 | 界面 | 描述 |
| SILENT_FAILURE | S008 | 批量导出无失败反馈 |

> 完整数据见 .screen-map/screen-map.json
```

---

## 受影响文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `skills/use-case.md` | 新建 | 完整技能定义 |
| `commands/use-case.md` | 新建 | `/use-case` 命令 |
| `skills/product-map.md` | 更新 | Step 6 报告规范改为摘要级 |
| `skills/screen-map.md` | 更新 | Step 3 报告规范改为摘要级 |
| `commands/product-map.md` | 更新 | 报告摘要模板简化 |
| `commands/screen-map.md` | 更新 | 报告摘要模板简化 |
| `SKILL.md` | 更新 | 新增 use-case，版本 2.2.0，写入双格式铁律 |
| `README.md` | 更新 | 新增 use-case，工作流图更新 |
| `.claude-plugin/plugin.json` | 更新 | 版本 2.2.0 |

---

## Flags（use-case 特有）

| Flag | 含义 |
|------|------|
| `NO_EXCEPTION_CASES` | 任务有 exceptions 但全部被 DEFERRED，无异常用例 |
| `NO_SCREEN_REF` | 用例无界面引用（screen-map 未运行） |
| `INCOMPLETE_THEN` | then 条件为空（task.outputs 未定义） |
| `MISSING_BOUNDARY` | task.rules 存在但未提取出任何 boundary 用例 |
