---
description: "界面地图：梳理界面、按钮、导航路径和异常状态，输出界面交互地图。模式: full / quick / scope"
argument-hint: "[mode: full|quick|scope|refresh] [模块名]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "WebSearch"]
---

# Screen Map — 界面与异常状态地图

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 前置检查

执行前必须检查：

1. **两阶段加载（索引优先）**：
   - 检查 `.allforai/product-map/task-index.json`
     - 存在 → 加载索引（< 5KB）
       - `scope` 模式：从索引的 `modules` 中匹配指定模块名，仅加载该模块任务的完整数据
       - 其他模式：进入全量加载 `task-inventory.json`
     - 不存在 → 回退到全量加载 `.allforai/product-map/task-inventory.json`
   - 若 `task-inventory.json` 也不存在 → 输出提示并终止：
     ```
     ⚠️ 未找到 .allforai/product-map/task-inventory.json
     请先运行 /product-map 建立产品地图，再运行 /screen-map。
     ```

2. 如果 `.allforai/screen-map/screen-map-decisions.json` 存在，自动加载历史决策，跳过已确认项的重复询问

3. **加载受众类型**：检查 `.allforai/product-map/role-profiles.json` 中角色是否含 `audience_type` 字段。存在 → 构建角色-受众映射（audience_mode = "typed"）；否则 → audience_mode = "default"（使用 v2.3.0 通用阈值）

4. **加载概念排除清单**：检查 `.allforai/product-concept/product-concept.json`。存在 → 提取 ERRC.eliminate，过滤 user_removed 任务（concept_mode = "active"）；否则 → concept_mode = "none"

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 完整流程：Step 1 → Step 2 → Step 3
- **`quick`** → 快速模式：Step 1 → Step 3（跳过 Step 2 冲突与缺口检测）
- **`scope <模块名>`** → 限定范围：全流程，但仅梳理属于指定模块的任务对应界面

## 执行流程

1. 参考已加载的 `skills/screen-map.md` 中的目标定义、工作流和铁律
2. **规模判定**：统计任务数 → 判定规模等级（小型 ≤30 / 中型 31-80 / 大型 >80）→ 告知用户采用的交互模式
3. 根据模式按需执行对应步骤
4. **大型产品**（界面 >30）：必须使用 Python/Node 脚本批量生成 `screen-map.json`，用户审核脚本输出
5. 按工作流执行，**每个 Step 必须有用户确认环节**（确认方式按规模分级）
6. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要**

## 详细文档（按需用 Read 工具加载）

- `${CLAUDE_PLUGIN_ROOT}/skills/screen-map.md` — 完整工作流、Schema、铁律

## Step 执行要求

每个 Step 执行前，用 Read 工具加载 `skills/screen-map.md` 中的对应章节。

每个 Step 完成后：
1. 将结果写入 `.allforai/screen-map/` 目录下对应的 JSON 文件
2. 向用户展示结果摘要
3. 等待用户确认后才进入下一个 Step

## 报告输出要求（强制执行）

执行完成后，必须在对话中直接输出以下报告摘要：

```
## 界面地图报告摘要

> 执行时间: {时间}
> 执行模式: {full/quick/scope}
> 产品规模: {小型/中型/大型}（{X} 个任务）
> 分析范围: {全产品 / 指定模块名}
> 受众模式: {typed / default}
> 概念感知: {active（已排除 X 个任务）/ none}

### 总览

| 维度 | 数量 |
|------|------|
| 界面总数 | X 个 |
| 按钮/操作总数 | X 个 |
| 已覆盖任务 | X / 总任务数 |
| 异常覆盖缺口（仅 full 模式） | X 个 |
| 界面级冲突（仅 full 模式） | X 个 |
| 受众分布 | consumer X · professional X · default X |
| 概念排除任务 | X 个（user_removed） |
| CONCEPT_ELIMINATED 界面 | X 个 |

### 高频操作（帕累托 Top 20%）

（每行：界面名 → 操作按钮 / click_depth）

### 问题清单（仅 full 模式）

（每行：flag 类型 / 界面 / 一句话说明）

### 下一步

1. 修复高优先级异常缺口（SILENT_FAILURE 优先）
2. 运行 /use-case 生成用例集（可选，以本报告为输入）
3. 根据界面地图，运行 /feature-gap 检测功能缺口（Step 2/3 需要本报告）
4. 根据界面地图，运行 /feature-prune 评估功能去留（Step 2 需要本报告）

> 界面地图: `.allforai/screen-map/screen-map.json`
> 冲突报告: `.allforai/screen-map/screen-conflict.json`
> 可读报告: `.allforai/screen-map/screen-map-report.md`
> 导航地图: `.allforai/screen-map/screen-map-visual.svg`
> 决策日志: `.allforai/screen-map/screen-map-decisions.json`
```

**关键：摘要必须包含具体的高频操作清单和异常缺口详情，不能只给统计数字。**

---

## 铁律（强制执行）

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/screen-map.md` 的「4 条铁律」章节。

1. **以任务清单为唯一基准** — 只梳理 task-inventory.json 中已定义任务对应的界面
2. **异常覆盖是核心质量指标** — 每条 task.exception 都必须有对应的界面响应
3. **只标不改，用户是权威** — 所有 flag 只报告，不执行修改
4. **screen-map 是必须层** — 与 product-map 共同构成完整产品地图，feature-gap/use-case/feature-prune/ui-design 均依赖其数据
