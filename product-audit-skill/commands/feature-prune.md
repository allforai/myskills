---
description: "功能剪枝：基于 product-map 频次数据评估功能去留，输出 CORE / DEFER / CUT 分类清单。模式: full / quick / scope"
argument-hint: "[mode: full|quick|scope] [模块名]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "WebSearch", "WebFetch"]
---

# Feature Prune — 功能剪枝

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

- **无参数 或 `full`** → 完整剪枝：Step 1 → Step 2 → Step 3 → Step 4 → Step 5
- **`quick`** → 快速剪枝：Step 1 → Step 2 → Step 4 → Step 5（跳过 Step 3 竞品参考）
- **`scope <模块名>`** → 限定模块：完整流程，但仅分析指定模块的功能

## 前置检查

执行前必须检查：

1. **product-map 必须存在**：检查 `.allforai/product-map/product-map.json`
   - 若不存在 → 输出「请先运行 /product-map 建立产品地图」，**立即终止**

2. **scope 模式额外检查**：检查 `.allforai/feature-prune/frequency-tier.json`
   - 若不存在 → 输出「请先运行 /feature-prune full 生成频次分层数据」，终止

3. **历史决策自动加载**：检查 `.allforai/feature-prune/prune-decisions.json`，存在则加载，已决策项自动复用

## 执行流程

**重要**：Step 0（项目画像 + 功能收集）已由 `product-map` 承担，本命令**从 Step 1 开始**。

1. 参考已加载的 `skills/feature-prune.md` 中的目标定义和铁律
2. 从 `.allforai/product-map/task-inventory.json` 直接读取频次数据（无需重新收集）
3. 高频任务（frequency=高）自动受保护，不进入剪枝候选，除非用户主动发起
4. 按工作流执行，每个 Step 必须有用户确认环节
5. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要**

## 详细文档（按需用 Read 工具加载）

- `${CLAUDE_PLUGIN_ROOT}/skills/feature-prune.md` — 完整工作流、Step 详述、铁律

## Step 执行要求

每个 Step 完成后：
1. 将结果写入 `.allforai/feature-prune/` 目录下对应的 JSON 文件
2. 向用户展示结果摘要
3. 等待用户确认后才进入下一个 Step

输出文件：`frequency-tier.json`（Step 1）、`scenario-alignment.json`（Step 2）、`competitive-ref.json`（Step 3）、`prune-decisions.json`（Step 4）、`prune-tasks.json`（Step 5）、`prune-report.md`

## 报告输出要求（强制执行）

执行完成后，必须在对话中直接输出以下报告摘要：

```
## 功能剪枝报告摘要

> 执行时间: {时间}
> 执行模式: {full/quick/scope}
> 分析范围: {全产品 / 指定模块名}

### 总览

| 分类 | 数量 |
|------|------|
| CORE（必须保留） | X 个 |
| DEFER（推迟） | X 个 |
| CUT（移除） | X 个 |

### CUT 清单（含证据）

（逐条列出：功能名、频次、场景关联、竞品情况、决策理由）

### DEFER 清单（含时机建议）

（逐条列出：功能名、推迟原因、建议重新评估的时间点）

### 下一步

1. 将 DEFER 功能移出当前迭代，加入 backlog
2. 通知开发团队移除 CUT 功能
3. 修复后运行 /feature-gap 确认剩余功能的完整性

> 剪枝任务清单: `.allforai/feature-prune/prune-tasks.json`
> 完整报告: `.allforai/feature-prune/prune-report.md`
> 决策日志: `.allforai/feature-prune/prune-decisions.json`
```

---

## 铁律（强制执行）

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/feature-prune.md` 的「5 条铁律」章节。

1. **频次是客观依据** — 所有剪枝建议引用 product-map 中的 frequency 数据
2. **只剪不加** — 只讨论去留，不建议应该增加什么
3. **CUT 是建议不是执行** — 标记 CUT 不触发任何代码删除
4. **用户是最终决策者** — 用户可以推翻任何建议
5. **高频功能受保护** — frequency=高 的任务不进入剪枝候选，除非用户主动发起
