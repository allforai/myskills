# 产品地图输出 Schema（product-map.json + 索引）

## `product-map.json` — 结构化汇总（供下游技能加载）

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "generated_at": "2026-02-24T10:00:00Z",
  "version": "2.4.0",
  "scope": "full",
  "scale": "large",
  "summary": {
    "role_count": 3,
    "task_count": 24,
    "flow_count": 2,
    "flow_gaps": 1,
    "orphan_task_count": 1,
    "independent_operation_count": 5,
    "conflict_count": 1,
    "constraint_count": 5,
    "validation_issues": 5,
    "competitor_gaps": 3
  },
  "experience_priority": {
    "mode": "consumer",
    "consumer_surface": true,
    "consumer_core": true,
    "primary_experience": "mobile",
    "reasoning": [
      "核心价值主要通过用户端持续使用获得",
      "后台主要承担配置、审核、运营支撑"
    ]
  },
  "roles": [...],        // 来自 role-profiles.json
  "tasks": [...],        // 来自 task-inventory.json
  "conflicts": [...],    // 来自 conflict-report.json（quick 模式为空数组）
  "constraints": [...]   // 来自 constraints.json（quick 模式为空数组）
  // flows 独立存储于 business-flows.json，此处不嵌入
}
```

`summary` 字段供下游技能（feature-gap、seed-forge）快速获取产品规模，无需遍历全部数组。

`experience_priority` 是用户端导向的全局契约字段，供 `experience-map`、`ui-design`、`design-to-spec`、`task-execute` 等下游技能切换评价标准：

- `mode = consumer`：用户端是主价值面，按成熟产品标准推进
- `mode = admin`：后台/专业端是主价值面，按效率与准确性优先
- `mode = mixed`：两端都重要，但用户端仍需通过成熟度检查

字段要求：

- `mode`：必填，枚举 `consumer | admin | mixed`
- `consumer_surface`：必填，布尔；是否存在用户端/移动端主界面
- `consumer_core`：必填，布尔；用户端是否承载核心价值而非仅承担辅助入口
- `primary_experience`：必填，枚举 `mobile | web-customer | admin | mixed`
- `reasoning`：必填，字符串数组；记录判定依据，供下游 explainability 使用

下游技能以此文件为主输入，同时按需加载 `business-flows.json`（业务流数据独立存储）。

## `product-map-report.md` — 可读摘要（给人看）

报告结构：

```
# 产品地图摘要

角色 X 个 · 任务 X 个 · 高频任务 X 个 · 冲突 X 个 · 约束 X 条

## 角色总览
| 角色 | 职责 | KPI |
|------|------|-----|
| （每角色一行） | | |

## 高频任务（Top 20%）
- T001 任务名（高频 / 高风险 / 跨部门）
- T005 任务名（高频 / 低风险）

## 冲突摘要
- C001 描述（高）

## 业务约束摘要
- CN001 描述（硬约束）

## 下一步建议
- 执行 experience-map 工作流 梳理界面、按钮和异常状态（必须，下游技能缺失时会自动运行）
- 执行 use-case 工作流 生成用例集（可选）
- 执行 feature-gap 工作流 检测功能缺口
- 执行 ui-design 工作流 生成 UI 设计规格

> 完整数据见 .allforai/product-map/product-map.json
```

## SVG 生成：product-map-visual.svg

`product-map-report.md` 写入磁盘后，生成 `.allforai/product-map/product-map-visual.svg`。

**生成方式**：使用 Python 脚本生成 SVG 文件。脚本读取 `role-profiles.json` 和 `task-inventory.json`，按以下设计意图生成角色-任务树状图：

**设计意图**：
- 左侧角色框，右侧任务框，折线连接
- 任务按 frequency 颜色区分：高频绿色、中频黄色、低频灰色
- 高风险任务标注红色徽章，跨部门任务标注紫色徽章，有冲突标记橙色三角
- 画布高度自适应任务数量

**颜色规范**：

| 元素 | 颜色 |
|------|------|
| 角色框 | fill `#3B82F6`，白色文字 |
| 任务框·frequency="高" | fill `#22C55E`，白色文字 |
| 任务框·frequency="中" | fill `#F59E0B`，白色文字 |
| 任务框·frequency="低" | fill `#9CA3AF`，白色文字 |
| 风险徽章（risk_level="高"） | fill `#EF4444` |
| 跨部门徽章（cross_dept=true） | fill `#8B5CF6` |
| 冲突标记（flags 不为空） | fill `#F97316` |
| 连线 | stroke `#CBD5E1` |

**图例**：画布顶部横向排列色块 + 说明文字：高频/中频/低频/高风险/跨部门/冲突

写入 `.allforai/product-map/product-map-visual.svg`

## 索引文件 Schema

`product-map-visual.svg` 写入后，立即生成两个轻量索引文件，供下游技能两阶段加载使用。

### `task-index.json`

从 `task-inventory.json` 提取关键字段，按模块分组。

```json
{
  "generated_at": "2026-02-25T10:00:00Z",
  "source": "task-inventory.json",
  "task_count": 24,
  "categories": [
    {"name": "basic", "label": "基本功能", "task_ids": ["T038","T039","T041"], "count": 3},
    {"name": "core", "label": "核心功能", "task_ids": ["T001","T002"], "count": 2}
  ],
  "modules": [
    {
      "name": "撤销管理",
      "task_ids": ["T001"],
      "tasks": [
        {
          "id": "T001",
          "name": "创建并提交撤销工单",
          "frequency": "高",
          "owner_role": "R001",
          "risk_level": "高",
          "category": "core"
        }
      ]
    }
  ]
}
```

### `flow-index.json`

从 `business-flows.json` 提取关键字段。

```json
{
  "generated_at": "2026-02-25T10:00:00Z",
  "source": "business-flows.json",
  "flow_count": 2,
  "flows": [
    {
      "id": "F001",
      "name": "异常处理全链路",
      "node_count": 4,
      "gap_count": 1,
      "roles": ["终端用户", "服务提供者"]
    }
  ]
}
```

**生成规则**：
- 索引随 Step 6 输出一起生成，时间戳与 `product-map.json` 的 `generated_at` 一致
- `scope` 模式下索引仍生成完整内容（不按 scope 过滤），确保下游技能自行筛选
- 下游技能加载索引时若发现索引不存在，回退到全量加载，行为与旧版完全一致
