---
description: "功能查漏：基于 product-map 检测任务完整性、界面完整性和用户旅程缺口。模式: full / quick / journey / role / refresh"
argument-hint: "[mode: full|quick|journey|role|refresh] [角色名]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion"]
---

# Feature Gap — 功能查漏

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 完整查漏：Step 1 → Step 2 → Step 3 → Step 4 → Step 5
- **`quick`** → 快速查漏：Step 1 → Step 4（跳过 Step 2、3、5，这些需要 screen-map）
- **`journey`** → 仅旅程：Step 3 → Step 4（仅旅程验证 + 生成任务清单）
- **`role <角色名>`** → 限定角色：同 full 完整流程，但仅分析属于指定角色的任务和界面
- **`refresh`** → 重新分析：将 `gap-decisions.json` 重命名为 `.bak` 备份，忽略所有已有决策缓存，从 Step 1 开始完整重跑

## 前置检查

执行前必须检查：

1. **两阶段加载（索引优先）**：
   - 检查三个索引文件：
     - `.allforai/product-map/task-index.json` → 任务索引
     - `.allforai/screen-map/screen-index.json` → 界面索引
     - `.allforai/product-map/flow-index.json` → 业务流索引
   - 任一索引存在 → 加载索引（< 5KB），按需决定是否加载完整数据
   - 所有索引不存在 → 回退到全量加载 `.allforai/product-map/product-map.json`
   - 若 `product-map.json` 也不存在 → 输出「请先运行 /product-map 建立产品地图」，**立即终止，不执行任何 Step**

2. **历史决策自动加载（向后兼容）**：
   - 优先检查 `.allforai/feature-gap/gap-decisions.json`，存在则加载
   - 若不存在，检查 `.feature-audit/audit-decisions.json`（旧路径，仅读取，不写回旧路径）
   - 加载后，已决策的分类自动复用，不重复询问

## 执行流程

1. 参考已加载的 `skills/feature-gap.md` 中的目标定义、工作流和铁律
2. 从 `.allforai/product-map/product-map.json` 加载产品地图数据
3. 根据模式按需执行对应步骤
4. 按工作流执行，**每个 Step 必须有用户确认环节**
5. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要**

## 详细文档（按需用 Read 工具加载）

- `${CLAUDE_PLUGIN_ROOT}/skills/feature-gap.md` — 完整工作流、Step 详述、铁律

## Step 执行要求

每个 Step 完成后：
1. 将结果写入 `.allforai/feature-gap/` 目录下对应的 JSON 文件
2. 向用户展示结果摘要
3. 等待用户确认后才进入下一个 Step

不再支持的旧模式：`incremental`、`verify`（已移除，如用户输入这些模式，提示改用 `full`）

## 报告输出要求（强制执行）

执行完成后，必须在对话中直接输出以下报告摘要：

```
## 功能查漏报告摘要

> 执行时间: {时间}
> 执行模式: {full/quick/journey/role}
> 分析范围: {全产品 / 指定角色名}

### 总览

| 检测维度 | 缺口数 |
|----------|--------|
| 任务缺口（Step 1） | X 个 |
| 界面/按钮缺口（Step 2） | X 个 |
| 旅程缺口（Step 3） | X 个（仅 full/journey 模式）|

### Flag 统计

| Flag 类型 | 数量 |
|-----------|------|
| CRUD_INCOMPLETE | X |
| NO_SCREEN | X |
| HIGH_FREQ_BURIED | X |
| NO_PRIMARY | X |
| HIGH_RISK_NO_CONFIRM | X |
| ORPHAN_SCREEN | X |
| ENTRY_BROKEN | X |

### 用户旅程评分（仅 full/journey 模式）

（按角色列出：角色名 — 评分 X/4）

### 缺口任务清单（按频次排序，高频在前）

（逐条列出：任务名、频次、缺口类型、Flag、建议操作）

### 下一步

1. 优先修复高频任务的缺口
2. 修复 HIGH_FREQ_BURIED：将高频操作提升到更浅的层级
3. 补充 HIGH_RISK_NO_CONFIRM：为高风险操作添加二次确认

> 完整报告: `.allforai/feature-gap/gap-report.md`
> 缺口任务: `.allforai/feature-gap/gap-tasks.json`
> 决策日志: `.allforai/feature-gap/gap-decisions.json`
```

---

## 铁律（强制执行）

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/feature-gap.md` 的「铁律」章节。

1. **product-map 是唯一基准** — 所有缺口检测以 product-map.json 为准，不引入额外需求来源
2. **频次决定优先级** — 高频任务的缺口排在前面，低频缺口不主动建议补充
3. **用户确认分类** — 所有 Flag 的分类由用户最终确认
4. **只检测不建议** — 发现缺口只报告，不建议如何实现
5. **硬编码禁令** — 不建议添加功能、不做技术选型建议
