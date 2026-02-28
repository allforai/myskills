---
description: "产品验收：静态扫描代码覆盖率 + 动态 Playwright 验证行为合规性，输出差异任务清单。模式: static / dynamic / full / refresh"
argument-hint: "[mode: static|dynamic|full|refresh]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion"]
---

# Product Verify — 产品验收

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

- **无参数 或 `static`** → 静态验收：S1 → S2 → S3 → S4 → 报告
- **`dynamic`** → 动态验收：D0（应用可达性预检） → D1 → D2 → D3 → D4 → 报告
- **`full`** → 完整验收：static 全部步骤 + D0 → D1 → D2 → D3 → D4 → 合并报告
- **`refresh`** → 重新验收：将 verify-decisions.json 重命名为 .bak，清除缓存，完整重跑

## 前置检查

执行前必须检查：

1. **两阶段加载（索引优先）**：
   - 检查索引文件：
     - `.allforai/product-map/task-index.json` → 任务索引
     - `.allforai/screen-map/screen-index.json` → 界面索引（S2 用）
   - 任一索引存在 → 加载索引（< 5KB），按需决定是否加载完整数据
   - 所有索引不存在 → 回退到全量加载 `.allforai/product-map/product-map.json`
   - 若 `product-map.json` 也不存在 → 输出「请先运行 /product-map 建立产品地图」，**立即终止，不执行任何 Step**
2. `.allforai/screen-map/screen-map.json` 必须，不存在则自动运行 screen-map 生成界面地图，然后启用 S2
3. `.allforai/use-case/use-case-tree.json` 可选，dynamic 阶段优先使用；不存在则从 product-map 自动推导测试序列
4. **历史决策加载**：检查 `.allforai/product-verify/verify-decisions.json`，存在则加载，已决策项（S4 EXTRA 归属 + D4 失败分类）自动跳过，不重复询问

## 执行流程

1. 加载 `${CLAUDE_PLUGIN_ROOT}/skills/product-verify.md` 中的工作流和铁律
2. 根据模式执行对应步骤
3. 每个 Step 完成后输出摘要，自动进入下一个 Step
4. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要**

## 详细文档（按需用 Read 工具加载）

- `${CLAUDE_PLUGIN_ROOT}/skills/product-verify.md` — 完整工作流、Step 详述、铁律

## Step 执行要求

每个 Step 完成后：
1. 将结果写入 `.allforai/product-verify/` 目录下对应的 JSON 文件
2. 输出结果摘要
3. 自动进入下一个 Step（不停）

## 报告输出要求（强制执行）

执行完成后，必须在对话中直接输出以下报告摘要：

```
## 产品验收报告摘要

> 执行时间: {时间}
> 执行模式: {static/dynamic/full}

### 总览

| 维度 | 结果 |
|------|------|
| 静态覆盖率（任务） | X / X 个已覆盖 |
| 静态覆盖率（界面） | X / X 个已覆盖（仅 screen-map 存在时） |
| 静态覆盖率（约束） | X / X 条已覆盖 |
| 动态通过率 | X 通过 / X 失败 / X 跳过（仅 dynamic/full 模式） |
| 待处理任务 | IMPLEMENT X / REMOVE_EXTRA X / FIX_FAILING X |

### 静态缺口清单

（逐条：任务名/界面名 / 缺口类型 / 频次 / 严重度）

### 动态失败清单（仅 dynamic/full 模式）

（逐条：用例 ID / 任务名 / 失败步骤 / 失败原因）

### 验收任务清单

（逐条：类型 / 任务名 / 优先级 / 建议操作）

### 下一步

1. 优先实现 IMPLEMENT 中的高频任务
2. 确认 REMOVE_EXTRA 是否需要补充进产品地图
3. 修复 FIX_FAILING 后重跑 /product-verify dynamic

> 静态报告: `.allforai/product-verify/static-report.json`
> 动态报告: `.allforai/product-verify/dynamic-report.json`
> 验收任务: `.allforai/product-verify/verify-tasks.json`
> 可读报告: `.allforai/product-verify/verify-report.md`
> 决策日志: `.allforai/product-verify/verify-decisions.json`
```

---

## 铁律（强制执行）

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/product-verify.md` 的「5 条铁律」章节。

1. **product-map 是验收基准** — 静态验收以 product-map 为唯一真值，不引入额外需求来源
2. **只报告不修改代码** — 发现缺口只标记，不自动生成或修改任何实现代码
3. **频次决定优先级** — IMPLEMENT 任务按 frequency 排序，高频在前
4. **EXTRA 自动建议归属** — EXTRA 代码由系统自动建议 keep/remove，写入决策日志
5. **动态失败自动分类** — 基于错误特征自动建议分类（代码缺陷/ENV_ISSUE），写入决策日志
