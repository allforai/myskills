---
description: "产品地图：从代码读现状，用产品语言呈现角色、任务与约束。模式: full / quick / refresh / scope"
argument-hint: "[mode: full|quick|refresh|scope] [模块名]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion"]
---

# Product Map — 产品地图

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 完整流程：Step 0 → Step 1 → Step 2 → Step 4 → Step 5 → Step 6 → Step 7
- **`quick`** → 快速模式：Step 0 → Step 1 → Step 2 → Step 6 → Step 7（跳过 Step 4/5，Step 7 不可跳过）
- **`refresh`** → 重新分析：忽略所有缓存，从 Step 0 开始重跑
- **`scope <模块名>`** → 限定范围：全流程，但仅分析属于指定模块的任务

## 前置检查：已有数据检测

执行前先检查：
- 如果 `.allforai/product-map/product-map-decisions.json` 存在，自动加载历史决策，跳过已确认项的重复询问

## 执行流程

1. 参考已加载的 `skills/product-map.md` 中的目标定义、工作流和铁律
2. 根据模式按需执行对应步骤
3. 按工作流执行，**每个 Step 必须有用户确认环节**
4. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要**

## 详细文档（按需用 Read 工具加载）

- `${CLAUDE_PLUGIN_ROOT}/skills/product-map.md` — 完整工作流、Step 详述、铁律

## Step 执行要求

每个 Step 执行前，用 Read 工具加载 `skills/product-map.md` 中的对应章节。

每个 Step 完成后：
1. 将结果写入 `.allforai/product-map/` 目录下对应的 JSON 文件
2. 向用户展示结果摘要
3. 等待用户确认后才进入下一个 Step

## 报告输出要求（强制执行）

执行完成后，必须在对话中直接输出以下报告摘要：

```
## 产品地图报告摘要

> 执行时间: {时间}
> 执行模式: {full/quick/refresh/scope}
> 分析范围: {全产品 / 指定模块名}

### 总览

| 维度 | 数量 |
|------|------|
| 用户角色 | X 个 |
| 核心任务 | X 个 |
| 高频任务（帕累托 Top 20%） | X 个 |
| 冲突/CRUD 缺口（仅 full 模式） | X 个 |
| 业务约束（仅 full 模式） | X 条 |
| 校验问题 | X 个（完整性 X / 冲突 X） |
| 竞品差距 | 竞品有我没有 X 个 / 我有竞品没有 X 个 / 做法不同 X 个 |

### 高频任务清单

（每行：任务名 / 角色 / 频次 / 风险等级）

### 检测到的冲突（仅 full 模式）

（每行：冲突描述 / 严重度 / 涉及任务）

### 下一步

1. 运行 /screen-map 梳理界面、按钮和异常状态（可选，推荐）
2. 运行 /use-case 生成用例集（可选）
3. 根据产品地图，运行 /feature-gap 检测功能缺口
4. 根据产品地图，运行 /feature-prune 评估功能去留
5. 根据产品地图，运行 /seed-forge 生成种子数据

> 产品地图: `.allforai/product-map/product-map.json`
> 可读报告: `.allforai/product-map/product-map-report.md`
> 校验报告: `.allforai/product-map/validation-report.md`
> 竞品分析: `.allforai/product-map/competitor-profile.json`
> 决策日志: `.allforai/product-map/product-map-decisions.json`
```

**关键：摘要必须包含具体的高频任务清单和冲突详情，不能只给统计数字。**

---

## 铁律（强制执行）

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/product-map.md` 的「5 条铁律」章节。

1. **产品语言输出** — 输出全程使用业务语言，不出现接口地址、组件名等工程术语
2. **读代码不改代码** — 只分析提取，不执行任何代码修改
3. **用户是权威** — 所有确认以用户说的为准，PM 补充的业务视角无条件纳入
4. **每步确认后才继续** — 展示摘要，等待确认后才进入下一步
5. **product-map 是唯一数据源** — 输出的 product-map.json 供其他技能直接加载
