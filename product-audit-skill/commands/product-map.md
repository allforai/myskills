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

- **无参数 或 `full`** → 完整流程：Step 0 → Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6 → Step 7
- **`quick`** → 快速模式：Step 0 → Step 1 → Step 2 → Step 3 → Step 6 → Step 7（跳过 Step 4/5，Step 3/7 不可跳过）
- **`refresh`** → 重新分析：忽略所有缓存，从 Step 0 开始重跑，完成后生成 refresh-diff.md
- **`scope <模块名>`** → 限定范围：全流程，但仅分析属于指定模块的任务

## 前置检查：已有数据检测

执行前先检查：
- 如果 `.allforai/product-concept/product-concept.json` 存在 → 进入**概念指导模式**（自主执行，仅 gap 处确认），加载产品概念作为战略指导
- 如果 `.allforai/product-map/product-map-decisions.json` 存在，自动加载历史决策，跳过已确认项的重复询问

**索引文件生成**：Step 6 完成后会自动生成 `task-index.json` 和 `flow-index.json` 索引文件，供下游技能（feature-gap、feature-prune、use-case、screen-map、seed-forge）两阶段加载使用，大幅减少 token 消耗。

## 执行流程

1. 参考已加载的 `skills/product-map.md` 中的目标定义、工作流和铁律
2. 根据模式按需执行对应步骤
3. **Step 0 完成后判定产品规模**（小型≤30 / 中型31-80 / 大型>80 任务），决定后续交互策略
4. 按工作流执行，**每个 Step 必须有用户确认环节**（概念指导模式下仅 gap 处确认）
5. **中型/大型产品**：Step 2 和 Step 3 完成后必须执行自审计子步骤（代码路由扫描 / handoff 验证）
6. **中型/大型产品**：大文件（task-inventory.json 等）必须使用 Python/Node 脚本生成，不可直接用 Write 工具
7. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要**

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
> 产品规模: {小型/中型/大型}（{任务数} 个任务）
> 分析范围: {全产品 / 指定模块名}

### 总览

| 维度 | 数量 |
|------|------|
| 用户角色 | X 个 |
| 核心任务 | X 个 |
| 业务流 | X 条（流缺口 X 个） |
| 高频任务（帕累托 Top 20%） | X 个 |
| 独立操作 | X 个 |
| 孤立任务 | X 个 |
| 冲突/CRUD 缺口（仅 full 模式） | X 个 |
| 业务约束（仅 full 模式） | X 条 |
| 校验问题 | ERROR X / WARNING X / INFO X |
| 竞品差距 | 竞品有我没有 X 个 / 我有竞品没有 X 个 / 做法不同 X 个 |

### 高频任务清单

（每行：任务名 / 角色 / 频次 / 风险等级）

### 检测到的冲突（仅 full 模式）

（每行：冲突描述 / 严重度 / 涉及任务）

### 自审计发现（中型/大型产品）

（Step 2 代码路由审计新增 X 个任务，Step 3 handoff 审计修复 X 个缺口）

### 下一步

1. 运行 /screen-map 梳理界面、按钮和异常状态（可选，推荐）
2. 运行 /use-case 生成用例集（可选）
3. 根据产品地图，运行 /feature-gap 检测功能缺口
4. 根据产品地图，运行 /feature-prune 评估功能去留
5. 根据产品地图，运行 /seed-forge 生成种子数据

> 产品地图: `.allforai/product-map/product-map.json`
> 可读报告: `.allforai/product-map/product-map-report.md`
> 业务流: `.allforai/product-map/business-flows-report.md`
> 校验报告: `.allforai/product-map/validation-report.md`
> 竞品分析: `.allforai/product-map/competitor-profile.json`
> 决策日志: `.allforai/product-map/product-map-decisions.json`
```

**关键：摘要必须包含具体的高频任务清单和冲突详情，不能只给统计数字。**

---

## 铁律（强制执行）

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/product-map.md` 的「10 条铁律」章节。

1. **产品语言输出** — 输出全程使用业务语言，不出现接口地址、组件名等工程术语
2. **角色为主线，任务必须完整** — 从"谁来用"出发，每个任务必须归属角色，required 字段必须完整
3. **频次决定主次** — 按 frequency 和 risk_level 分类，高频保完整性，高风险保约束覆盖
4. **只标不改，用户是权威** — 检测问题只标记不修改，最终决定由用户做出
5. **完整功能地图不依赖界面梳理** — 产品地图独立可运行，screen-map 是可选增强层
6. **Step 7 校验不可跳过** — 所有模式下必须执行校验，按 ERROR/WARNING/INFO 分级报告
7. **Step 3 业务流建模不可跳过** — 所有模式下必须执行，确保链路完整性
8. **每步确认，增量复用** — 每步展示摘要等待确认，决策写入 decisions.json 增量复用
9. **规模适配，量体裁衣** — 按产品规模自动调整交互策略和生成方式
10. **生成即审计，自查先于人查** — 中型/大型产品 Step 2/3 后强制自审计
