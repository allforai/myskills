---
name: screen-map
description: >
  Use when the user asks to "map screens", "list buttons", "analyze UI", "map navigation",
  "check error states", "map exception flows", "analyze form validation",
  "界面梳理", "按钮梳理", "界面地图", "异常状态映射", "导航路径", "错误状态",
  "表单校验", "操作失败流程", "空状态处理", "界面交互地图",
  or mentions mapping screens to tasks, button-level CRUD analysis, UI navigation paths,
  error/empty state design, form validation rules, or exception flow coverage.
  Requires product-map to have been run first.
version: "2.1.0"
---

# Screen Map — 界面与异常状态地图

> 以产品地图为基础，梳理每个任务对应的界面、按钮和异常状态

## 目标

以 `.allforai/product-map/task-inventory.json` 为输入，系统化梳理产品的界面层：

1. **在哪做** — 每个任务对应哪些界面，每个界面的核心目的是什么
2. **怎么做** — 每个界面上的操作按钮，CRUD 分类、频次、层级
3. **出了问题怎么办** — 界面异常状态、表单校验、操作失败流程、空状态处理
4. **有没有界面级问题** — 检测冗余入口、高风险无确认、异常覆盖缺口

---

## 定位

```
product-map（功能地图）         screen-map（界面地图）          feature-gap（缺口检测）
谁用？做什么？有何异常？         在哪做？怎么做？出错怎么办？      地图说有的，现在有没有？
task-inventory.json 为基础      以 task-inventory 为输入        读 screen-map 做 Step 2/3
功能语义层（必须）              界面交互层（可选增强）           基于 product-map + screen-map
```

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/task-inventory.json`。

---

## 快速开始

```
/screen-map              # 完整流程（Step 1-3）
/screen-map quick        # 跳过 Step 2（冲突检测），运行 Step 1 + Step 3。Step 3 报告中冲突相关部分显示为「未检测（quick 模式）」。
/screen-map scope 退款管理  # 只梳理指定模块的界面
```

**scope 模式**：运行与 full 相同的 Step 序列，但仅处理 `task-inventory.json` 中 `task_name` 包含指定关键词的任务及其关联界面。

**refresh 模式**：将 `screen-map-decisions.json` 重命名为 `.bak` 备份，从 Step 1 开始完整重新运行，忽略所有已有决策缓存。

---

## 工作流

```
前置：检查 .allforai/product-map/task-inventory.json 是否存在
      若不存在 → 提示用户先运行 /product-map，终止
      ↓
Step 1: 界面与按钮梳理
      按任务展开，梳理每个任务的界面和操作按钮
      包含 states（界面状态）、on_failure（失败反馈）、
           validation_rules（校验规则）、exception_flows（异常流程）
      参照 task.exceptions 标注每个异常的界面响应方式
      → 用户确认，生成 screen-map.json
      ↓
Step 2: 界面级冲突 + 异常缺口检测（quick 模式跳过）
      检测 REDUNDANT_ENTRY、HIGH_RISK_NO_CONFIRM
      检测 SILENT_FAILURE、MISSING_VALIDATION、NO_EMPTY_STATE、UNHANDLED_EXCEPTION
      → 用户确认，排除误报，生成 screen-conflict.json
      ↓
Step 3: 输出报告
      汇总 screen-map.json 和 screen-conflict.json
      生成 screen-map-report.md
```

**核心原则：每个 Step 结束都有用户确认，用户是权威。**

---

### 前置检查

```
检查 .allforai/product-map/task-inventory.json：
  - 存在 → 加载任务列表，提取每个任务的 task_name、exceptions、risk_level、main_flow
  - 不存在 → 提示：「请先运行 /product-map 生成任务清单，再运行 /screen-map」，终止执行
```

---

### Step 1：界面与按钮梳理

按任务展开，从代码提取页面和操作按钮，转换为产品语言描述。

**界面提取方法**：

从代码中识别界面的常见模式：
- **路由文件**（route config / router）：每个路由路径对应一个界面
- **页面组件**（Page / View / Screen 命名的组件文件）：每个页面组件 = 一个界面
- **菜单配置**（sidebar / nav 配置文件）：菜单项与界面一一对应
- 若以上模式均不存在，询问用户描述产品的主要页面

**按钮提取方法**：

从界面组件代码中识别操作：
- 表单提交（form submit / onSubmit）
- 按钮点击（Button / onClick / handleXxx）
- 链接跳转（Link / navigate / router.push）
- 批量操作（batch / bulk action）
- 每个操作标注 CRUD 类型（Create / Read / Update / Delete）

**click_depth 推导**：从角色的主入口页面开始计算到达该操作需要的最少点击次数（主导航 = 0，列表页按钮 = 1，详情页按钮 = 2，弹窗内按钮 = 3）。

**frequency 推导**：继承关联任务在 `task-inventory.json` 中的 `frequency` 值。同一界面有多个任务关联时，取最高频次。

**关键要求**：梳理每个界面时，读取对应任务的 `exceptions` 字段，要求用户为每个异常标注对应的界面处理方式（`exception_flows`）。

#### 界面 Schema

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 screen-map 分析结果决定，不限行业。

```json
{
  "screens": [
    {
      "id": "S001",
      "name": "退款申请页",
      "description": "客服填写退款原因、金额，提交退款申请",
      "primary_purpose": "让客服快速、准确地提交退款申请",
      "primary_action": "提交退款申请",
      "entry_point": "订单详情页 → 申请退款按钮",
      "tasks": ["T001"],
      "states": {
        "empty": "暂无退款申请，提示用户新建",
        "loading": "表单加载中，显示骨架屏",
        "error": "网络错误，显示重试按钮",
        "permission_denied": "权限不足，跳转到错误页"
      },
      "actions": [
        {
          "label": "提交退款申请",
          "crud": "C",
          "frequency": "高",
          "click_depth": 1,
          "is_primary": true,
          "roles": ["R001"],
          "requires_confirm": false,
          "on_failure": "高亮必填字段，顶部显示错误汇总",
          "validation_rules": ["金额 > 0", "金额 ≤ 原订单金额", "退款原因必填"],
          "exception_flows": [
            "订单已全额退款 → 顶部红色提示「该订单已全额退款，不可重复申请」",
            "支付信息缺失 → 弹窗提示「支付信息异常，请联系技术支持」附工单入口",
            "权限不足 → 按钮置灰，hover 显示「请申请退款权限」"
          ]
        },
        {
          "label": "撤回退款",
          "crud": "D",
          "frequency": "低",
          "click_depth": 2,
          "is_primary": false,
          "roles": ["R001", "R002"],
          "requires_confirm": true,
          "on_failure": "提示撤回失败原因（如：审批已完成，无法撤回）",
          "validation_rules": [],
          "exception_flows": []
        }
      ],
      "pareto": {
        "high_freq_actions": ["提交退款申请"],
        "low_freq_buried": [],
        "high_freq_buried": []
      },

**帕累托计算方法**：将该界面内所有按钮按 `frequency` 降序排列，累计占比达到 80% 的按钮标记为 `high_freq_actions`。`click_depth ≥ 3` 的高频按钮标记为 `high_freq_buried`；`click_depth ≤ 1` 的低频按钮标记为 `low_freq_buried`（疑似冗余快捷入口）。

      "flags": []
    }
  ]
}
```

#### 界面字段说明

| 字段 | 含义 |
|------|------|
| `primary_purpose` | 这个页面最重要的目标（用户视角一句话） |
| `primary_action` | 频次最高的操作，由帕累托分析自动推导，PM 可调整 |
| `states` | 界面的各类状态：`empty`（空数据）/ `loading`（加载中）/ `error`（错误）/ `permission_denied`（无权限）等 |

#### 按钮字段说明

| 字段 | 含义 |
|------|------|
| `label` | 按钮文字（界面上显示的） |
| `crud` | `C` 新增 / `R` 查看 / `U` 修改 / `D` 删除 |
| `frequency` | 操作频次：高 / 中 / 低 |
| `click_depth` | 触达该按钮需要几次点击（1=直接可见，2=需要展开，3+=深度隐藏） |
| `is_primary` | 由频次自动推导（`frequency=高` 且 `click_depth=1`），PM 可覆盖 |
| `roles` | 哪些角色可见/可操作此按钮 |
| `requires_confirm` | 是否需要二次确认弹窗 |
| `on_failure` | 操作失败时界面如何响应（提示文案、高亮字段、错误位置） |
| `validation_rules` | 前端校验规则列表（表单提交前执行） |
| `exception_flows` | 每条对应 task.exceptions 中一个异常的界面处理方式 |

#### task.exceptions 与 exception_flows 的衔接

梳理每个按钮时：

1. 读取关联任务（`tasks` 字段）的 `exceptions` 列表
2. 要求用户为每个异常标注对应的 `exception_flows`（界面如何响应）
3. 若某异常有 task 定义但没有界面响应 → 标记 `UNHANDLED_EXCEPTION` flag

**帕累托衍生检测**：

| 检测 | 逻辑 | 意义 |
|------|------|------|
| 高频操作可达性 | `frequency=高` + `click_depth >= 3` → `HIGH_FREQ_BURIED` | 用户最常做的事不应被埋深 |
| 主操作频次一致性 | `primary_action` 不是频次最高的操作 → `PRIMARY_MISMATCH` | 主操作应由频次决定 |

**`flags` 取值（界面级）**：

| 标记 | 含义 |
|------|------|
| `OVERLOADED` | 单页任务数超过阈值（默认 5），职责过重 |
| `HIGH_FREQ_BURIED` | 高频操作被埋在次级菜单 |
| `PRIMARY_MISMATCH` | `primary_action` 不是频次最高的操作 |
| `ORPHAN` | 没有任何任务关联，疑似废弃页面 |
| `NO_ENTRY` | 没有任何其他页面指向此页（孤立入口） |

**用户确认**：界面和按钮梳理完整吗？频次评估准确吗？异常响应覆盖完整吗？

输出：`.allforai/screen-map/screen-map.json`

---

### Step 2：界面级冲突 + 异常缺口检测

基于已确认的 screen-map.json，检测两类问题：

#### 界面级冲突（从 product-map 迁入）

| 问题类型 | Flag | 检测逻辑 |
|----------|------|----------|
| 冗余入口 | `REDUNDANT_ENTRY` | 同一操作（相同 `crud` + 相同任务关联）在多个界面重复出现 |
| 高风险无确认 | `HIGH_RISK_NO_CONFIRM` | 对应任务 `risk_level=高` 且按钮 `requires_confirm=false` |

#### 异常覆盖缺口

| 问题类型 | Flag | 检测逻辑 |
|----------|------|----------|
| 操作无失败反馈 | `SILENT_FAILURE` | 按钮 `crud` 为 C/U/D，但 `on_failure` 未定义或为空 |
| 表单缺少前端校验 | `MISSING_VALIDATION` | 按钮为表单提交（`crud=C` 或 `crud=U`），`validation_rules` 为空数组 |
| 列表无空状态处理 | `NO_EMPTY_STATE` | 列表/表格类界面，`states.empty` 未定义或为空 |
| 异常无界面响应 | `UNHANDLED_EXCEPTION` | task.exceptions 中有异常，但该界面对应按钮的 `exception_flows` 没有覆盖该异常 |

**冲突报告 Schema**：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 screen-map 分析结果决定，不限行业。

```json
{
  "conflicts": [
    {
      "id": "SC001",
      "type": "REDUNDANT_ENTRY",
      "description": "「标记订单完成」按钮在订单列表页和订单详情页均出现，业务逻辑相同，入口重复",
      "affected_screens": ["S005", "S009"],
      "severity": "中",
      "confirmed": false
    }
  ],
  "exception_gaps": [
    {
      "id": "EG001",
      "type": "SILENT_FAILURE",
      "description": "「批量导出」按钮（S008）无 on_failure 定义，导出失败时用户无任何反馈",
      "affected_screens": ["S008"],
      "affected_actions": ["批量导出"],
      "severity": "高",
      "confirmed": false
    },
    {
      "id": "EG002",
      "type": "UNHANDLED_EXCEPTION",
      "description": "T001 异常「审批超时 48h → 自动升级到上级」在退款申请页无对应 exception_flow",
      "affected_tasks": ["T001"],
      "affected_screens": ["S001"],
      "severity": "中",
      "confirmed": false
    }
  ]
}
```

**severity 判定规则**：
- `高`：影响高频操作（frequency = 高）或涉及数据丢失风险（SILENT_FAILURE）
- `中`：影响中频操作，或用户体验问题但不影响数据完整性
- `低`：影响低频操作，或纯粹的优化建议

**用户确认**：检测结果有没有误报？哪些问题需要处理？

输出：`.allforai/screen-map/screen-conflict.json`

---

### Step 3：输出报告

汇总 Step 1 和 Step 2 的所有已确认数据，生成可读报告。

#### `screen-map-report.md` — 可读摘要（给人看）

```
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

> 完整数据见 .allforai/screen-map/screen-map.json
```

输出：`.allforai/screen-map/screen-map-report.md`

---

## 输出文件结构

```
.allforai/screen-map/
├── screen-map.json             # Step 1: 界面地图（含 states、on_failure、exception_flows）
├── screen-conflict.json        # Step 2: 界面级冲突 + 异常覆盖缺口
├── screen-map-report.md        # Step 3: 可读报告
└── screen-map-decisions.json   # 用户决策日志（增量复用）
```

### decisions.json 通用格式

```json
[
  {
    "step": "Step 1",
    "item_id": "S001",
    "item_name": "描述",
    "decision": "confirmed | modified | deferred",
    "reason": "用户备注（可选）",
    "decided_at": "2024-01-15T10:30:00Z"
  }
]
```

- `confirmed`：确认无修改
- `modified`：修改后确认
- `deferred`：暂不决定，下次重新提问

**加载逻辑**：每个 Step 开始前检查 decisions.json，已 `confirmed` 的条目跳过确认直接沿用。

---

## 4 条铁律

### 1. 以任务清单为唯一基准

只梳理 `task-inventory.json` 中已定义任务对应的界面和按钮。不引入任务之外的界面。发现代码中有但任务清单未覆盖的界面，标记为 `ORPHAN`，由用户决定去留。

### 2. 异常覆盖是核心质量指标

task.exceptions 中每条异常都必须在对应界面的 exception_flows 中有响应。`UNHANDLED_EXCEPTION` 是高优先级问题，代表产品在异常情况下的设计缺失。每个 C/U/D 操作都应有 `on_failure` 定义，操作失败不能静默。

### 3. 只标不改，用户是权威

检测到任何 flag，只标记报告，不执行任何修改。用户说「这个异常不需要界面响应」，则标记为 `DEFERRED`，不进入缺口清单。PM 对 exception_flows 的补充无条件纳入。

### 4. screen-map 是增强层，不是必须层

product-map 可独立运行并提供完整功能语义。screen-map 专注界面交互层，为 feature-gap Step 2/3 提供数据支撑。若用户不需要界面级分析，可跳过 screen-map 直接运行 feature-gap Step 1 或 feature-prune。
