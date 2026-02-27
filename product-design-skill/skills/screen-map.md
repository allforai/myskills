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
version: "2.5.0"
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
功能语义层（必须）              界面交互层（必须）               基于 product-map + screen-map
```

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/task-inventory.json`。

---

## 快速开始

```
/screen-map              # 完整流程（Step 1-3）
/screen-map quick        # 跳过 Step 2（冲突检测），运行 Step 1 + Step 3。Step 3 报告中冲突相关部分显示为「未检测（quick 模式）」。
/screen-map scope 退款管理  # 只梳理指定模块的界面
```

## 增强协议（WebSearch + 4D+6V + XV）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：`”usability audit” + 场景词 + “real examples” + 2025`、`”WCAG 2.2” + 组件类型 + “accessibility”`

**4D+6V 重点**：异常与失败处理（`on_failure` / `exception_flows`）视为信息保真关键位，缺失时优先标红；每个关键界面补充 `source_refs`、`constraints`、`decision_rationale`。

**XV 交叉验证**（Step 2 界面级冲突+异常缺口检测后）：

| 验证点 | task_type | 发送内容 | 写入字段 |
|--------|-----------|----------|----------|
| UX 一致性审查 | `ux_review`→gpt | 界面清单 + 按钮列表 + 异常流覆盖情况 + 受众类型分布 | cross_model_review.ux_consistency_issues |
| 无障碍检查 | `accessibility_check`→gemini | 界面清单 + 操作频次 + 状态处理（空态/错误/加载） + 受众类型 | cross_model_review.accessibility_gaps |

自动写入：UX 一致性问题（跨界面交互模式不统一、反馈方式不一致）、无障碍缺陷（对比度不足、缺少键盘导航、状态变更无通知）。

## 中段经理理论支持（可选增强）

为让“功能点 → 交互设计”阶段具备统一的管理语言，可在现有 screen-map 规则上叠加：

| 理论/框架 | 对应步骤 | 落地方式 |
|-----------|----------|----------|
| 服务蓝图（Service Blueprint） | Step 1/2 | 将 `entry_point`、`handoff`、`exception_flows` 解释为前台触点与后台支撑链路 |
| Nielsen 可用性启发式 | Step 2 | 将 `SILENT_FAILURE`、`NO_EMPTY_STATE`、`MISSING_VALIDATION` 映射到可用性缺陷类型，便于评审 |
| 认知负荷管理（Cognitive Load） | Step 1 | 用 `OVERLOADED`、`HIGH_FREQ_BURIED` 控制信息密度和操作可达性 |
| 风险控制矩阵 | Step 2 | 将 `HIGH_RISK_NO_CONFIRM` 与受众类型联动，明确高风险操作的确认策略 |

> 本增强仅补充“为什么这样设计”的理论解释，不改变原有 flags 与输出结构。

**scope 模式**：运行与 full 相同的 Step 序列，但仅处理 `task-inventory.json` 中 `task_name` 包含指定关键词的任务及其关联界面。

**refresh 模式**：将 `screen-map-decisions.json` 重命名为 `.bak` 备份，从 Step 1 开始完整重新运行，忽略所有已有决策缓存。

---

## 规模适配

根据产品任务数量自动判定规模，采用不同交互策略。

### 规模判定

| 规模 | 任务数 | 说明 |
|------|--------|------|
| 小型 | ≤ 30 | 逐项确认，完整展示 |
| 中型 | 31 - 80 | 摘要确认，按模块聚合 |
| 大型 | > 80 | 统计+分组确认，仅展开有问题项 |

### 交互策略

| 环节 | 小型 | 中型 | 大型 |
|------|------|------|------|
| Step 1 确认 | 完整列表逐个确认 | 按模块摘要（界面数/操作数/覆盖率） | 统计总览 + 仅展开有 flag 的界面 |
| Step 2 问题展示 | 全部详细展示 | 高/中级详细展示，低级摘要 | 高级详细展示，中级摘要+示例，低/INFO 仅统计 |
| Step 2 确认 | 逐条确认 | 按类型分组确认 | 统计总览 + 仅高级逐条确认 |

### 脚本生成指南

当界面数 > 30 时，**必须使用 Python/Node 脚本**生成 `screen-map.json`，而非手动逐条构建：

1. 从路由配置 / 页面组件目录批量提取界面列表
2. 从组件代码批量提取按钮和操作
3. 关联 task-inventory.json 中的任务
4. 输出符合 Schema 的 JSON 文件
5. 用户仅需审核脚本输出，而非逐项构建

---

## 受众感知设计

检测阈值和严重度规则根据界面所服务的用户群体自动调整。

### 受众类型解析

每个界面的 `audience_type` 按以下规则解析：

1. 收集界面所有 `actions[].roles` 引用的角色 ID
2. 查找 `role-profiles.json` 中每个角色的 `audience_type`
3. 决定界面级受众类型：

| 角色组合 | 界面 audience_type | 理由 |
|---------|-------------------|------|
| 全部 consumer | `consumer` | 纯 C 端界面 |
| 全部 professional | `professional` | 纯 B 端界面 |
| 混合 | `consumer` | 取严格侧，保护普通用户 |
| 全部未标注 | `default` | 兼容 v2.3.0 |

### 受众设计档案

| 参数 | `default`（v2.3.0 兼容） | `consumer`（C端） | `professional`（B端） |
|------|--------------------------|--------------------|-----------------------|
| HIGH_FREQ_BURIED 阈值 | `click_depth >= 3` | `click_depth >= 3` | `click_depth >= 5` |
| OVERLOADED 任务数上限 | `5` | `3` | `8` |
| is_primary 推导 | frequency=高 且 depth ≤ 1 | frequency=高 且 depth ≤ 1 | frequency=高 且 depth ≤ 2 |
| HIGH_RISK_NO_CONFIRM | risk_level=高 | risk_level >= 中 | risk_level=高 |
| MISSING_VALIDATION | frequency=高 或 rules 匹配 | 所有 C/U 操作均触发 | frequency=高 或 rules 匹配 |
| NO_EMPTY_STATE severity | 中 | 高（需引导式空状态） | 低（简单提示即可） |
| SILENT_FAILURE severity | 高 | 高 | 中（专业用户可查日志） |

### 设计理念对照

| 维度 | Consumer（C端） | Professional（B端） |
|------|----------------|---------------------|
| 信息密度 | 低，每屏聚焦单一任务 | 高，仪表盘、多列表格 |
| 校验策略 | 严格、即时、防呆 | 批量操作，专家可跳过 |
| 空状态 | 必须有引导（情感化设计） | 简单提示即可 |
| 确认弹窗 | 中高风险均需确认 | 仅高风险需确认 |
| 错误恢复 | 撤销 > 确认弹窗 | 批量回滚、操作日志 |

---

## 全自动模式

**激活条件**（同时满足）：
1. `.allforai/product-concept/product-concept.json` 存在且含 `pipeline_preferences` 字段
2. 上下文含 `__orchestrator_auto: true`（由 `/product-design full` 编排器传入）

**未同时满足** → 保持标准交互模式（当前行为不变）。

**行为变化**：

| 步骤 | 标准模式 | 全自动模式 |
|------|----------|-----------|
| **Step 1 界面清单确认** | AskUserQuestion 确认 | 自动确认，记入 `pipeline-decisions.json`（`decision: "auto_confirmed"`） |
| **Step 2 冲突确认** | AskUserQuestion 确认 | 自动确认（所有检出的 REDUNDANT_ENTRY、HIGH_RISK_NO_CONFIRM、SILENT_FAILURE 等问题记录到 `pipeline-decisions.json`） |
| **Step 3 报告确认** | AskUserQuestion 确认 | 自动确认 |

**安全护栏**（自动模式下仍然停下来问用户）：
- ERROR 级验证失败（screen 数 = 0、task_refs 引用断裂）

---

## 工作流

```
前置：检查 .allforai/product-map/task-inventory.json 是否存在
      若不存在 → 提示用户先运行 /product-map，终止
      统计任务数 → 判定规模（小型/中型/大型）→ 告知用户交互模式
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
两阶段加载：
  Phase 1 — 加载索引：
    检查 .allforai/product-map/task-index.json
      存在 → 加载索引（< 5KB），获取任务 id/task_name/frequency/owner_role/risk_level + 模块分组
        scope 模式：从索引的 modules 中匹配指定模块名，仅加载该模块任务的完整数据
        其他模式：进入 Phase 2 加载完整数据
      不存在 → 回退到 Phase 2 全量加载

  Phase 2 — 加载完整数据：
    检查 .allforai/product-map/task-inventory.json：
      存在 → 加载任务列表，提取每个任务的 task_name、exceptions、risk_level、main_flow
      不存在 → 提示：「请先运行 /product-map 生成任务清单，再运行 /screen-map」，终止执行

  Phase 2.5 — 加载受众类型：
    检查 .allforai/product-map/role-profiles.json：
      存在且角色含 audience_type → 构建 role_id → audience_type 映射，标记 audience_mode = "typed"
      否则 → audience_mode = "default"（使用 v2.3.0 通用阈值）
    告知用户：「受众模式：typed — X 个 consumer 角色 + Y 个 professional 角色」或「default — 使用通用阈值」

  Phase 2.7 — 加载概念排除清单：
    检查 .allforai/product-concept/product-concept.json：
      存在 → 提取 competitive_position.errc.eliminate 列表，标记 concept_mode = "active"
      不存在 → concept_mode = "none"（不影响任何行为）
    过滤 task-inventory：排除 status = "user_removed" 的任务，记录排除数量
    告知用户：「概念感知：active — 已排除 X 个 user_removed 任务，ERRC.eliminate 共 Y 项」或「none — 处理全部任务」

  Phase 3 — 规模判定：
    统计过滤后的活跃任务总数 → 判定规模等级（小型/中型/大型）
    告知用户：「本产品共 X 个任务，判定为【大/中/小】型产品，将采用 {交互模式} 进行确认」
    记录 scale_level 供后续 Step 引用
```

---

### Step 1：界面与按钮梳理

**任务过滤**：仅对 `status` 不为 `user_removed` 的任务展开界面梳理。`user_removed` 任务已被产品概念层排除（ERRC.eliminate），不需要界面。前置检查 Phase 2.7 已完成过滤。

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

**校验规则提取方法**：

从代码中提取前端校验规则，转换为产品语言：
- **表单校验库**（Yup / Zod / Joi / Valibot 等）：提取 schema 定义中的 required、min/max、pattern 等规则
- **HTML5 表单属性**：提取 `required`、`minlength`、`maxlength`、`pattern`、`type="email"` 等原生校验
- **自定义校验函数**：识别 `validate`、`validator`、`check` 等函数中的校验逻辑
- **关联任务 rules 字段**：参照 `task-inventory.json` 中任务的 `rules` 字段，补充前端应校验但代码未实现的规则
- 所有提取结果统一转换为产品语言（如 `yup.string().required()` → `必填`，`yup.number().min(0)` → `金额 ≥ 0`）

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
      "audience_type": "professional",
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
| `audience_type` | 界面受众类型：`consumer` / `professional` / `default`，由关联角色自动推导 |

#### 按钮字段说明

| 字段 | 含义 |
|------|------|
| `label` | 按钮文字（界面上显示的） |
| `crud` | `C` 新增 / `R` 查看 / `U` 修改 / `D` 删除 |
| `frequency` | 操作频次：高 / 中 / 低 |
| `click_depth` | 触达该按钮需要几次点击（1=直接可见，2=需要展开，3+=深度隐藏） |
| `is_primary` | 由频次自动推导（frequency=高 且 click_depth 在受众档案范围内：consumer/default ≤ 1，professional ≤ 2），PM 可覆盖 |
| `roles` | 哪些角色可见/可操作此按钮 |
| `requires_confirm` | 是否需要二次确认弹窗 |
| `on_failure` | 操作失败时界面如何响应（提示文案、高亮字段、错误位置） |
| `validation_rules` | 前端校验规则列表（表单提交前执行） |
| `exception_flows` | 每条对应 task.exceptions 中一个异常的界面处理方式 |

**以下字段必须显式生成，不得省略**：
- `is_primary`: true/false（由频次自动推导，但必须显式写入）
- `on_failure`: string（无则 `""`）
- `on_success`: string（无则 `""`）
- `requires_confirm`: true/false
- `validation_rules`: []（无则空数组）
- `exception_flows`: []（无则空数组）

**字段名规范**：screen-map.json 中用 `tasks`（任务 ID 列表），screen-index.json 中用 `task_refs`。两处含义相同，名称不同是因为索引层简写。

#### task.exceptions 与 exception_flows 的衔接

梳理每个按钮时：

1. 读取关联任务（`tasks` 字段）的 `exceptions` 列表
2. 要求用户为每个异常标注对应的 `exception_flows`（界面如何响应）
3. 若某异常有 task 定义但没有界面响应 → 标记 `UNHANDLED_EXCEPTION` flag

**帕累托衍生检测**：

| 检测 | 逻辑 | 意义 |
|------|------|------|
| 高频操作可达性 | `frequency=高` + `click_depth >= 受众阈值`（consumer/default: 3, professional: 5）→ `HIGH_FREQ_BURIED` | 用户最常做的事不应被埋深 |
| 主操作频次一致性 | `primary_action` 不是频次最高的操作 → `PRIMARY_MISMATCH` | 主操作应由频次决定 |

**`flags` 取值（界面级）**：

| 标记 | 含义 |
|------|------|
| `OVERLOADED` | 单页任务数超过受众阈值（consumer: 3, professional: 8, default: 5），职责过重 |
| `HIGH_FREQ_BURIED` | 高频操作被埋在次级菜单 |
| `PRIMARY_MISMATCH` | `primary_action` 不是频次最高的操作 |
| `ORPHAN` | 没有任何任务关联，疑似废弃页面 |
| `CONCEPT_ELIMINATED` | 代码中存在的界面匹配 ERRC.eliminate 功能，属于概念层战略性排除的残留代码，建议清理 |
| `NO_ENTRY` | 没有任何其他页面指向此页（孤立入口） |

**ORPHAN 重分类**（concept_mode = "active" 时）：

检测到 `ORPHAN` 界面后，将其名称/描述与 `errc.eliminate` 列表进行语义匹配：
- 匹配成功 → 重分类为 `CONCEPT_ELIMINATED`，severity 降为 `INFO`（战略性排除，非意外）
- 匹配失败 → 保持 `ORPHAN`，severity 不变（真正的孤立页面）

匹配方式：AI 对比界面名称、描述与 ERRC.eliminate 条目的语义相关性。例如 ERRC.eliminate 含「实时协作」，代码中发现名为「协作编辑页」的界面 → 匹配成功。

**用户确认（按规模分级）**：

- **小型**（≤ 30 任务）：展示完整界面列表，逐个确认界面、按钮、异常响应
- **中型**（31-80 任务）：按模块展示摘要（界面数 / 操作数 / 异常覆盖率），用户确认模块级汇总，仅对有 flag 的界面展开详情
- **大型**（> 80 任务）：展示统计总览（总界面数、总操作数、覆盖率、flag 数），按模块分组仅展开有 flag 的界面，其余折叠为一行摘要

所有规模均需确认：界面和按钮梳理完整吗？频次评估准确吗？异常响应覆盖完整吗？

输出：`.allforai/screen-map/screen-map.json`

#### 索引文件生成

`screen-map.json` 写入后，立即生成轻量索引文件，供下游技能两阶段加载使用。

##### `screen-index.json`

从 `screen-map.json` 提取关键字段，按模块分组。模块归组：按关联任务的 `task_name` 语义聚类，与 `task-index.json` 的模块一致。

```json
{
  "generated_at": "2026-02-25T10:00:00Z",
  "source": "screen-map.json",
  "screen_count": 12,
  "concept_eliminated_count": 2,
  "modules": [
    {
      "name": "退款管理",
      "screens": [
        {
          "id": "S001",
          "name": "退款申请页",
          "task_refs": ["T001"],
          "action_count": 2,
          "audience_type": "professional",
          "has_gaps": false
        }
      ]
    }
  ]
}
```

`has_gaps` 判定：界面存在任一 flag（`OVERLOADED`、`HIGH_FREQ_BURIED`、`PRIMARY_MISMATCH`、`ORPHAN`、`CONCEPT_ELIMINATED`、`NO_ENTRY`）或任一按钮缺少 `on_failure` 定义时为 `true`。

**生成规则**：
- 索引随 Step 1 输出一起生成
- `scope` 模式下索引仍生成完整内容，确保下游技能自行筛选
- 下游技能加载索引时若发现索引不存在，回退到全量加载，行为与旧版完全一致

写入 `.allforai/screen-map/screen-index.json`

---

### Step 2：界面级冲突 + 异常缺口检测

基于已确认的 screen-map.json，检测两类问题：

#### 界面级冲突（从 product-map 迁入）

| 问题类型 | Flag | 检测逻辑 |
|----------|------|----------|
| 冗余入口 | `REDUNDANT_ENTRY` | 同一操作（相同 `crud` + 相同任务关联）在多个界面重复出现，且不属于已识别的标准模式 |
| 高风险无确认 | `HIGH_RISK_NO_CONFIRM` | 按钮 `requires_confirm=false` 且任务风险达到受众阈值（consumer: risk_level >= 中, professional/default: risk_level=高） |

**列表+详情页模式识别**（REDUNDANT_ENTRY 例外规则）：

若重复操作出现的两个界面恰好构成同一实体的列表页和详情页，属于标准产品模式，不应视为冗余。识别条件（满足任一）：
- 界面名称一个含「列表」/「list」，另一个含「详情」/「detail」/「编辑」/「edit」
- `click_depth` 差值为 1（列表页较浅，详情页较深）
- 两个界面关联的任务集合为包含关系（详情页任务 ⊆ 列表页任务）

匹配时：自动标记 `pattern: "list_detail_pair"`，severity 降级为 `INFO`，不计入问题总数。

#### 异常覆盖缺口

| 问题类型 | Flag | 检测逻辑 |
|----------|------|----------|
| 操作无失败反馈 | `SILENT_FAILURE` | 按钮 `crud` 为 C/U/D，但 `on_failure` 未定义或为空 |
| 表单缺少前端校验 | `MISSING_VALIDATION` | 按钮为表单提交（`crud=C` 或 `crud=U`），`validation_rules` 为空数组，且满足触发门槛（见下） |
| 列表无空状态处理 | `NO_EMPTY_STATE` | 列表/表格类界面，`states.empty` 未定义或为空 |
| 异常无界面响应 | `UNHANDLED_EXCEPTION` | task.exceptions 中有异常，但该界面对应按钮的 `exception_flows` 没有覆盖该异常 |

**MISSING_VALIDATION 触发门槛**：

- **consumer 界面**：所有 C/U 操作均触发（consumer 用户需要严格防呆校验）
- **professional/default 界面**：仅在满足以下任一条件时触发为中/高 severity：
  - 关联任务的 `rules` 字段包含前端应校验的规则（如必填、格式、范围限制）
  - 操作 `frequency=高`

不满足以上条件时（低频操作且无明确校验要求）→ 降级为 `INFO`，不计入问题总数。

**冲突报告 Schema**：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 screen-map 分析结果决定，不限行业。

```json
{
  "conflicts": [
    {
      "id": "SC001",
      "type": "REDUNDANT_ENTRY",
      "description": "「标记订单完成」按钮在订单列表页和订单详情页均出现，属于列表+详情页标准模式",
      "affected_screens": ["S005", "S009"],
      "pattern": "list_detail_pair",
      "audience_type": "professional",
      "severity": "INFO",
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
      "audience_type": "professional",
      "severity": "高",
      "confirmed": false
    },
    {
      "id": "EG002",
      "type": "UNHANDLED_EXCEPTION",
      "description": "T001 异常「审批超时 48h → 自动升级到上级」在退款申请页无对应 exception_flow",
      "affected_tasks": ["T001"],
      "affected_screens": ["S001"],
      "audience_type": "professional",
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
- `INFO`：已识别的标准模式（如 `list_detail_pair`）或降级项，不计入问题总数

**受众类型调整**（在基础规则之上）：

| Flag | Consumer 调整 | Professional 调整 |
|------|--------------|-------------------|
| SILENT_FAILURE | 高（不变） | 中（可查操作日志） |
| NO_EMPTY_STATE | 高（需引导设计） | 低（简单提示即可） |
| MISSING_VALIDATION | 所有 C/U 均为中（不降级 INFO） | 按基础规则 |
| HIGH_RISK_NO_CONFIRM | risk_level >= 中 即触发 | 仅 risk_level=高 |
| 其他 | 按基础规则 | 按基础规则 |

**大规模展示策略**：
- **高级问题**：所有规模均完整展示详情
- **中级问题**：小/中型完整展示；大型展示摘要+1个示例
- **低级问题**：小型完整展示；中型摘要；大型仅统计数量
- **INFO 级别**：小型展示列表；中/大型仅统计数量

**用户确认（按规模分级）**：
- **小型**：逐条确认每个问题
- **中型**：按问题类型分组确认
- **大型**：统计总览 + 仅高级问题逐条确认，其余按类型批量确认

输出：`.allforai/screen-map/screen-conflict.json`

---

### Step 3：输出报告

汇总 Step 1 和 Step 2 的所有已确认数据，生成可读报告。

#### `screen-map-report.md` — 可读摘要（给人看）

```
# 界面地图摘要

界面 X 个 · 操作 X 个 · 覆盖任务 X/X · 异常缺口 X 个 · 界面冲突 X 个
受众分布：consumer X 个界面 · professional X 个界面 · default X 个界面
概念排除：X 个任务已排除（user_removed）· X 个界面匹配 ERRC.eliminate（CONCEPT_ELIMINATED）

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

#### `screen-map-visual.svg` — 导航地图可视化

在生成 `screen-map-report.md` 后，使用 Python 脚本生成 SVG 导航地图：

**生成方法**：

```python
# 脚本逻辑概要（实际执行时生成完整脚本）
# 1. 读取 screen-map.json
# 2. 按模块分区布局
# 3. 每个模块一个分组框，内含界面节点
# 4. entry_point 关系用箭头连线（界面 → 子界面）
# 5. 颜色编码：
#    - 正常界面：蓝色边框 (#4A90D9)
#    - 有 flag 的界面：橙色边框 (#E8943A)
#    - 高频界面（含高频操作）：绿色边框 (#5CB85C)
# 6. 底部图例：正常界面 / 有问题界面 / 高频界面
```

**SVG 布局规则**：
- 按模块水平分区，每个模块纵向排列界面节点
- 节点显示：界面名称 + 操作数量
- entry_point 解析为有向箭头（来源界面 → 目标界面）
- 节点宽度固定 180px，高度按内容自适应
- 模块标题居中显示在分组框顶部

输出：`.allforai/screen-map/screen-map-visual.svg`

---

## 输出文件结构

```
.allforai/screen-map/
├── screen-map.json             # Step 1: 界面地图（含 states、on_failure、exception_flows）
├── screen-index.json           # Step 1: 界面索引（轻量，供下游两阶段加载）
├── screen-conflict.json        # Step 2: 界面级冲突 + 异常覆盖缺口
├── screen-map-report.md        # Step 3: 可读报告
├── screen-map-visual.svg       # Step 3: 导航地图可视化（按模块分区，颜色编码）
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

## 防御性规范

> 通用模式定义见 `docs/defensive-patterns.md`，以下为本技能的具体应用。

### 加载校验
- **`screen-map-decisions.json`**：加载时用 `python -m json.tool` 验证 JSON 合法性。解析失败 → 检查 `.bak` → 提示恢复或重新运行 `/screen-map refresh`。
- **`task-inventory.json`**：前置加载时验证 JSON 合法性。解析失败 → 提示用户「task-inventory.json 损坏，请重新运行 /product-map」，终止执行。

### 零结果处理
- **Step 1 提取 0 界面**：⚠ 警告「未从代码中识别到任何界面（路由/页面组件/菜单配置均为空）」+ 建议检查前端页面目录路径是否正确，或项目是否为纯后端服务。
- **Step 2 检测 0 问题**：✓ 明确告知「界面级冲突检测完毕，未发现异常缺口（共检查 {N} 个界面 {M} 个操作）」。

### 规模自适应
- 已有完整实现（见「规模适配」章节）。阈值：small ≤30 / medium 31–80 / large >80 任务。
- 界面数通常与任务数正相关，沿用任务数阈值。

### WebSearch 故障
- **趋势搜索**（动态趋势补充）：工具不可用或无有用结果 → 跳过趋势补充，标注「趋势搜索未执行（WebSearch 不可用）」，不影响主流程。

### 上游过期检测
- **`task-inventory.json`**：加载时比较 `generated_at` 与 `screen-map-decisions.json` 最新 `decided_at`。上游更新 → ⚠ 警告「task-inventory 在 screen-map 上次运行后被更新，界面梳理可能基于旧版任务数据，建议重新运行 /screen-map refresh」。仅警告不阻断。

---

## 4 条铁律

### 1. 以任务清单为唯一基准

只梳理 `task-inventory.json` 中 `status` 不为 `user_removed` 的任务对应的界面和按钮。`user_removed` 任务（概念层 ERRC.eliminate 排除）不生成界面。不引入任务之外的界面。发现代码中有但任务清单未覆盖的界面，标记为 `ORPHAN`；若 concept_mode = "active" 且匹配 ERRC.eliminate，重分类为 `CONCEPT_ELIMINATED`（INFO 级），由用户决定去留。

### 2. 异常覆盖是核心质量指标

task.exceptions 中每条异常都必须在对应界面的 exception_flows 中有响应。`UNHANDLED_EXCEPTION` 是高优先级问题，代表产品在异常情况下的设计缺失。每个 C/U/D 操作都应有 `on_failure` 定义，操作失败不能静默。

### 3. 只标不改，用户是权威

检测到任何 flag，只标记报告，不执行任何修改。用户说「这个异常不需要界面响应」，则标记为 `DEFERRED`，不进入缺口清单。PM 对 exception_flows 的补充无条件纳入。

### 4. screen-map 是必须层

screen-map 与 product-map 共同构成完整产品地图。product-map 提供功能语义（谁用、做什么），screen-map 提供界面交互（在哪做、怎么做、出错怎么办）。feature-gap、use-case、feature-prune、ui-design、design-audit 均依赖 screen-map 数据。当下游技能检测到 screen-map 不存在时，会自动触发 screen-map 运行，确保数据完整性。
