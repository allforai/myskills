---
description: "用例集：从功能地图和界面地图推导完整用例，输出 JSON 机器版和 Markdown 人类版。模式: full / quick / scope"
argument-hint: "[mode: full|quick|scope|refresh] [功能区名]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion"]
---

# Use Case — 用例集

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 前置检查

执行前必须检查：

1. `.allforai/product-map/task-inventory.json` 是否存在
   - 存在 → 加载任务和角色数据，继续执行
   - 不存在 → 输出提示并终止：
     ```
     ⚠️ 未找到 .allforai/product-map/task-inventory.json
     请先运行 /product-map 建立功能地图，再运行 /use-case。
     ```

2. `.allforai/screen-map/screen-map.json` 是否存在
   - 存在 → 标注「已注入界面上下文：validation_rules + exception_flows」
   - 不存在 → 标注「未注入界面上下文；建议先运行 /screen-map 以获得更完整的异常用例」

3. `.allforai/use-case/use-case-decisions.json` 若存在 → 自动加载，跳过已确认项

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 完整流程：Step 0 → Step 1 → Step 2 → Step 3 → Step 4
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
1. 将结果写入 `.allforai/use-case/` 目录下对应文件
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
| E2E 用例 | X 条 |

### 用例分布（按功能区）

| 功能区 | 任务数 | 用例数 | 异常覆盖率 |
|--------|--------|--------|-----------|
| 退款管理 | 3 | 18 | 100% |

### E2E 用例

| E2E ID | 标题 | 关联流 | 步骤数 |
|--------|------|--------|--------|
| E2E-F001-01 | 售后全链路_正常流 | F001 | 4 |

### Flags 汇总

（逐条列出：flag 类型 / 涉及任务 / 说明；无 flag 则写"无"）

### 下一步

1. 将 use-case-tree.json 交给 AI agent 执行自动化测试
2. 将 use-case-report.md 交给 QA 执行手工测试
3. 运行 /feature-gap 检测功能缺口（与用例集互补）

> 机器版: `.allforai/use-case/use-case-tree.json`
> 人类版: `.allforai/use-case/use-case-report.md`
> 决策日志: `.allforai/use-case/use-case-decisions.json`
```

**关键：摘要必须包含具体的用例分布表和 Flags 详情，不能只给统计数字。**

---

## 铁律（强制执行）

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/use-case.md` 的「4 条铁律」章节。

1. **双格式原则** — JSON 完整字段给机器，Markdown 摘要级给人类
2. **以功能地图为唯一数据源** — 只从 task-inventory.json 和 screen-map.json 推导
3. **每步确认，DEFERRED 可延后** — 用户可标记任何用例为 DEFERRED
4. **只生成不执行** — 输出用例描述，不触发测试执行
