---
name: experience-map
description: >
  Phase 4 — Experience Map Generation. Use when the user asks to "generate experience map",
  "map experience", "operation lines", "experience-map", "体验地图", "操作线",
  "体验线路", "节点屏幕", "operation line mapping",
  or mentions generating operation lines from journey emotions,
  mapping nodes to screens, building experience maps from journey-emotion-map.
  Replaces the former screen-map skill with a richer experience-oriented structure.
  Requires journey-emotion and product-map to have been run first.
version: "2.4.0"
---

# Experience Map — 体验地图

> LLM 理解产品语义后自由设计界面结构，再用验收规则 loop 修正

## 目标

以产品地图（任务 + 数据模型 + 业务流）和旅程情绪图为输入，LLM 自由设计体验地图：

- **设计阶段**：LLM 理解产品定位、用户角色、情绪弧线、数据结构后，自主决定每个界面的布局、组件、交互方式、状态流转
- **验收阶段**：LLM 自审设计质量（任务覆盖率、业务流连续性、平台差异、情绪匹配），不通过的界面重新设计
- **输出**：operation_lines > nodes > screens 三层结构 JSON + 人类可读报告

---

## 核心理念：LLM 设计 + 规则验收

```
旧模式（已废弃）：task → 匹配 37 种交互类型 → 填充模板
新模式：LLM 理解产品语义 → 自由设计界面 → LLM 验收 → loop 修正
```

**交互类型不是生成入口**。LLM 根据产品上下文自主决定界面结构，但 `interaction_type` 必须从渲染器支持列表中选择（影响线框渲染布局）。自由设计意图通过 `description`、`components`、`interaction_pattern` 表达。

---

## 定位

```
journey-emotion（旅程情绪图）    experience-map（体验地图）       ui-design（界面设计）
每个节点的情绪、风险、设计提示    操作线 > 节点 > 屏幕结构          基于体验地图生成设计规格
情绪层语义（人工确认）           交互层语义（LLM 自由设计）         视觉层语义
```

---

## 快速开始

```
/experience-map              # 完整流程（Step 1-4）
/experience-map refresh      # 清空缓存，从头重新运行
/experience-map --variants 3 # 生成 3 套信息架构方案，对比后选择
```

---

## 增强协议（WebSearch + 4D+6V + XV）

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/skill-commons.md`「统一验收方法论」。

**WebSearch**：Step 2 设计界面时，对创新功能（如 AI 生成、角色扮演、沉浸式学习）搜索同类产品的交互设计案例，作为设计参考和 D2 证据（如搜索「immersive language learning app UX」「AI content generation interface patterns」），写入 screen 的 `source_refs`。

**4D+6V 重点**：每个 screen 的 `description` 回答 D1（是什么设计）+ D4（为什么这样设计而非其他方案）；`emotion_design` 回答 D2（基于 journey-emotion 的什么证据）；核心界面（承载 core 任务的 screen）覆盖至少 4/6 视角审查——user: 能完成任务吗？business: 支撑核心指标吗？tech: 可实现吗？ux: 交互一致吗？data: 可观测吗？risk: 有安全风险吗？

**XV**（可选）：将体验地图摘要（操作线数、屏幕数、任务覆盖率、平台分布）发送给第二个模型独立评审，重点审查信息架构合理性和遗漏。

---

## 生成方式

LLM 直接分析全部上游产物，理解产品定位、用户角色、数据结构、业务流程、情绪弧线后，**自主设计**每个界面。

**LLM 的设计输入**（全部加载到上下文）：

| 输入 | 来源 | LLM 用途 |
|------|------|---------|
| 产品定位 | product-concept.json | 理解产品调性、创新概念、目标用户 |
| 治理风格 | product-mechanisms.json → `governance_styles` | 知道每条业务流的治理策略（事前审核/事后追究/分级/自动），决定是否需要审核屏幕、系统边界 |
| 操作频度 | role-value-map.json → `operation_profile` | 知道每个角色的操作频度和屏幕粒度指导（同页多功能 vs 单任务聚焦），指导屏幕合并/拆分决策 |
| 任务清单 | task-inventory.json | 知道每个角色要完成什么任务 |
| 数据模型 | entity-model.json | 知道每个实体有哪些字段、关系、状态机 |
| 业务流 | business-flows.json | 知道任务之间的流转顺序和交接关系 |
| 视图对象 | view-objects.json | 知道每个界面需要展示/操作哪些数据 |
| 旅程情绪 | journey-emotion-map.json | 知道用户在每个节点的情绪状态和设计提示 |
| 角色画像 | role-profiles.json | 知道每个角色的平台、受众类型、KPI |

**LLM 的设计自由度**：

LLM 可以自主决定以下所有方面（不受预定义交互类型限制）：

- **界面结构**：一个任务对应几个界面？是否需要分步向导？是否合并多个任务到一个界面？
- **布局方式**：卡片堆叠、瀑布流、时间线、看板、树形、地图、全屏沉浸... LLM 根据内容类型和用户场景选择
- **交互方式**：滑动翻页、拖拽排序、长按菜单、双击编辑、手势操作... LLM 根据平台和场景选择
- **组件选择**：不限于标准 CRUD 表单/列表，可以设计对话式界面、游戏化界面、AI 辅助界面等
- **状态设计**：空态、加载态、错误态、成功态的具体交互方式和文案
- **微动效**：翻转、弹性、渐显、粒子效果... LLM 根据情绪弧线选择

**唯一的硬约束**：

| 约束 | 规则 | 原因 |
|------|------|------|
| 平台 | consumer 角色 → mobile-ios 单列布局；professional 角色 → desktop-web 侧边栏布局 | 物理设备差异 |
| 应用归属 | 每个屏幕必须有 `app` 字段，标注属于哪个独立应用。跨角色业务流中的屏幕按 node role 归属对应应用（不是按操作线的主角色） | 同为 desktop-web 的 merchant 和 admin 是不同的应用 |
| 任务覆盖 | 每个任务至少出现在一个界面中 | 功能完整性 |
| 业务流连续 | 业务流中相邻任务的界面之间必须有导航路径 | 流程可达性 |

---

## 输出 schema

- 顶层 key 必须是 `operation_lines`（数组）+ `screen_index`（对象）
- 每个 operation_line 包含 `id`、`name`、`source_journey`、`role`、`nodes`
- 每个 node 包含 `seq`、`id`、`action`、`screens`（screen 对象数组）
- 每个 screen 必须包含：

| 字段 | 必须 | 说明 |
|------|------|------|
| `id` | 是 | S001 格式 |
| `name` | 是 | 界面名称（中文产品语言） |
| `description` | 是 | 界面用途和设计意图（2-3 句话，说明为什么这样设计） |
| `platform` | 是 | `mobile-ios` 或 `desktop-web` |
| `app` | 是 | 该屏幕所属的**独立应用**（如 `website`、`merchant`、`admin`）。由骨架生成器根据 node role 推导。`app` ≠ `platform`：merchant 和 admin 可能都是 desktop-web，但属于不同的可部署应用 |
| `layout_type` | 是 | LLM 从业务目的推导的语义化布局名称（如 `auth_card`、`priority_queue`、`structured_editor`、`visual_card_grid`、`status_timeline` 等）。**不能**是 interaction_type 的复制（如 "form"、"list"），也不能是通用描述（如 "sidebar-content"、"single-column"）。必须描述该屏幕的业务身份 |
| `layout_description` | 是 | 1-2 句话描述该屏幕的**具体空间布局**——各区域的位置、大小比例、视觉权重。每个屏幕的 layout_description 必须独特。下游线框渲染器可用此描述生成更精确的布局 |
| `tasks` | 是 | 引用的 task_id 数组 |
| `actions` | 是 | 用户在此界面可执行的操作列表 |
| `components` | 是 | **LLM 自由设计的组件清单**，每个组件包含 `type`（LLM 命名）、`purpose`、`behavior`、`data_source` |
| `interaction_pattern` | 是 | **LLM 自由描述的交互模式**（1-2 句话，如"卡片堆叠+左右滑动评分，翻转显示释义"） |
| `emotion_design` | 推荐 | 基于情绪弧线的设计决策，**必须是结构化对象**（见下方 emotion_design 格式说明） |
| `states` | 是 | 界面状态，**必须包含业务特定状态**（见下方 states 格式说明） |
| `flow_context` | 是 | 导航上下文（prev/next/entry_points/exit_points） |
| `vo_ref` | 推荐 | 关联的视图对象 |
| `api_ref` | 推荐 | 关联的 API 端点 |
| `data_fields` | 是 | 界面展示/操作的数据字段，每个元素为对象：`{name, label, type, input_widget, required}`（见下方 data_fields 格式说明） |
| `interaction_type` | 是 | **必须从下方渲染器支持列表中选择**（线框渲染器依赖此字段选择布局模板），选最接近的类型。自由设计意图写入 `description` 和 `interaction_pattern` |
| `view_modes` | 条件必须 | **屏幕内视图模式流转**（见下方 view_modes 格式说明）。当角色的 `operation_profile.screen_granularity` 为 `multi_function_per_page` 时必须填写；单任务聚焦的移动端屏幕可省略 |
| `_pattern` | 自动 | 功能模式 ID 数组（Step 3.6 写入） |
| `_pattern_group` 内的 `common_behavior` | 自动 | 同类功能模式的共性行为约束（Step 3.6 写入，仅约束行为一致性，不约束布局） |
| `_pattern_group` | 自动 | 模式分组 ID（Step 3.6 写入） |
| `_behavioral` | 自动 | 行为类别 ID 数组（Step 3.6 写入） |
| `_behavioral_standards` | 自动 | 行为标准映射对象（Step 3.6 写入） |

### data_fields 格式说明

每个 `data_fields` 元素必须是结构化对象（非字符串），下游线框渲染器依赖此格式：

```json
{
  "name": "scenario_title",
  "label": "场景标题",
  "type": "string",
  "input_widget": "text_input",
  "required": true
}
```

| 字段 | 说明 |
|------|------|
| `name` | 字段标识符（snake_case，对应 entity-model 中的字段名） |
| `label` | 用户可见标签（中文） |
| `type` | 数据类型：`string` / `number` / `boolean` / `date` / `enum` / `array` / `image` / `rich_text` |
| `input_widget` | 输入控件：`text_input` / `textarea` / `number_input` / `select` / `multi_select` / `toggle` / `date_picker` / `file_upload` / `rich_editor` / `readonly`（仅展示不可编辑） |
| `required` | 是否必填 |

LLM 根据 entity-model 和 view-objects 中的字段语义自主选择合适的 `type` 和 `input_widget`，不必穷举所有字段，只列出该界面核心展示/操作的字段。

### emotion_design 格式说明

`emotion_design` 必须是结构化对象，不能是纯字符串。LLM 需要将 `_emotion_ref` 中的情绪数据转化为具体的设计决策：

```json
{
  "source_emotion": "anxious",
  "source_hint": "用户首次支付，担心安全和金额",
  "design_response": "强调安全标识（锁图标+Stripe品牌），支付金额大字号确认，进度条清晰可见",
  "visual_tone": "calm_reassuring",
  "interaction_density": "low"
}
```

| 字段 | 说明 |
|------|------|
| `source_emotion` | 来自 `_emotion_ref.emotion` 的情绪标签（delighted/satisfied/neutral/anxious/frustrated/angry） |
| `source_hint` | 来自 `_emotion_ref.design_hint` 的设计提示（原样引用或摘要） |
| `design_response` | LLM 针对该情绪做出的具体设计决策（1-2 句话，必须是可操作的设计指令，不是抽象原则） |
| `visual_tone` | 视觉基调：`celebratory`（成就感）/ `calm_reassuring`（安心）/ `efficient_focused`（高效）/ `warm_friendly`（亲切）/ `neutral_professional`（中性专业） |
| `interaction_density` | 交互密度：`low`（少操作、大留白、突出核心 CTA）/ `medium`（标准密度）/ `high`（数据密集、批量操作） |

无 `_emotion_ref` 的屏幕（如独立操作线中的管理页面），`emotion_design` 可省略或填 `null`。

### states 格式说明

`states` 必须是对象（key=状态名, value=交互描述），且**除了 4 个基础状态外，必须包含该界面特有的业务状态**：

```json
{
  "empty": "空列表插画 + '去浏览'引导按钮",
  "loading": "骨架屏 + 下拉刷新",
  "error": "网络错误提示 + 重试按钮",
  "success": "操作成功 Toast 自动消失",
  "calculating": "配额实时计算中，数据区域显示加载动画",
  "resource_changed": "可用资源变化提醒横幅 + 自动更新数量",
  "expired": "超时未提交提醒 + 重新创建按钮"
}
```

**关键规则**：
- 4 个基础状态（empty/loading/error/success）是必须的，但 value 必须是针对该屏幕的具体交互描述，**不能所有屏幕都写一样的**
- **业务状态**（如 `calculating`、`stock_changed`、`processing_payment`、`pending_approval`、`connecting`、`disconnected`）必须根据该屏幕的业务场景添加，至少 1 个
- 包含审批/状态转换的屏幕（MG4/MG2-ST），必须包含流程状态（`pending`/`approved`/`rejected` 等）
- 包含支付的屏幕，必须包含支付状态（`processing_payment`/`payment_failed`/`payment_timeout`）
- 包含实时通讯的屏幕，必须包含连接状态（`connecting`/`connected`/`disconnected`）

### view_modes 格式说明

后台类型的"同页多功能"屏幕，同一个页面内包含多种视图模式，用户操作触发模式切换。`view_modes` 表达这种**屏幕内的交互编排**——不同于 `states`（静态状态枚举），`view_modes` 描述的是用户操作导致的**视图结构变化**（哪些组件显隐、布局如何切换）。

```json
"view_modes": [
  {
    "id": "full_list",
    "label": "全量列表",
    "trigger": "初始加载 / 清除筛选",
    "layout": "全部Tab高亮，表格显示所有记录，右侧无面板",
    "active_components": ["record-tabs", "search-bar", "record-table", "pagination"],
    "available_actions": ["搜索", "切换Tab", "点击行查看详情"]
  },
  {
    "id": "filtered_list",
    "label": "按状态筛选列表",
    "trigger": "点击状态Tab（待处理/处理中/已完成/已撤销）",
    "layout": "选中Tab高亮，表格仅显示该状态记录，批量操作按钮出现",
    "active_components": ["record-tabs", "search-bar", "filtered-table", "batch-action-bar"],
    "available_actions": ["批量处理", "批量打印", "导出", "搜索", "点击行"]
  },
  {
    "id": "detail_panel",
    "label": "记录详情侧边栏",
    "trigger": "点击列表中某一行",
    "layout": "列表缩窄至左侧60%，右侧40%滑出记录详情面板",
    "active_components": ["record-table-narrow", "record-detail-panel", "action-buttons"],
    "available_actions": ["处理", "取消记录", "查看进度", "关闭面板返回全宽列表"]
  }
]
```

| 字段 | 说明 |
|------|------|
| `id` | 视图模式标识符（snake_case） |
| `label` | 用户可理解的模式名称 |
| `trigger` | 什么用户操作触发进入此模式 |
| `layout` | 此模式下的布局描述（哪些区域可见、占比如何变化） |
| `active_components` | 此模式下可见/活跃的组件列表（引用 `components` 中的 type） |
| `available_actions` | 此模式下用户可执行的操作 |

**使用规则**：
- `operation_profile.screen_granularity = "multi_function_per_page"` 的角色（通常是 merchant/admin 后台），其屏幕**必须**定义 `view_modes`
- 第一个 view_mode 必须是默认/初始视图
- view_modes 之间形成有向图：每个 mode 的 `trigger` 说明从哪个 mode 可以到达此 mode
- 移动端单任务聚焦屏幕可省略（只有一种视图模式时不需要）
- `view_modes` 与 `states` 是互补关系：`states` 描述数据状态（空/加载/错误），`view_modes` 描述交互模式（列表/筛选/详情）。同一个 view_mode 内可以有不同 states

### 前后台交互指导思想（Interaction Design Principles by Audience）

前端（consumer）和后台（professional）的交互设计差异，不是"风格偏好"，而是由**用户特征**推导出的必然结论：

| 用户特征 | 前端（consumer） | 后台（professional） |
|---------|-----------------|-------------------|
| 用户规模 | 万~百万级 | 几人~几十人 |
| 使用频次 | 低频、碎片化、每次几分钟 | 高频、长时间连续操作、每天数小时 |
| 业务理解 | 不了解内部逻辑，需要引导 | 理解业务规则，追求效率 |

**推导出的设计指导思想**：

| 指导思想 | 前端 | 后台 | 推导逻辑 |
|---------|------|------|---------|
| **信息密度** | 低 — 大留白、一屏一焦点、重视觉层次 | 高 — 紧凑表格、多列信息、数据密集 | 人多但低频 → 每次都是"新手"，信息太多会迷失；人少但高频 → 熟练用户需要一眼看到全貌 |
| **引导程度** | 强 — 步骤引导、空状态提示、操作确认 | 弱 — 假设用户懂业务，减少确认弹窗 | 用户不看说明书 → 界面即说明；专业用户被反复确认会烦 |
| **页面粒度** | 细 — 单任务聚焦，每步一个全屏页面 | 粗 — 同页多功能，一个页面管理一个实体的全部操作 | 碎片化使用 → 每次进入只做一件事；长时间使用 → 频繁跳转浪费时间 |
| **操作方式** | 显式 — 大按钮、明确 CTA、手势导航 | 隐式 — 行内编辑、右键菜单、键盘快捷键、批量操作 | 手指触控 → 需要大触控区域；鼠标键盘 → 精确操作，追求速度 |
| **容错机制** | 严格 — 不可逆操作多重确认、自动保存 | 宽松 — 信任用户判断，快速撤销而非反复确认 | 用户犯错成本高且不可预期 → 防错优先；专业用户犯错少且能自行恢复 → 效率优先 |

**LLM 在设计每个屏幕时必须回答**：这个屏幕的用户是高频专业用户还是低频大众用户？据此选择信息密度和引导程度。不能用前端的低密度引导式设计套后台，也不能用后台的高密度效率式设计套前端。

---

### 后台屏幕范式（Backend Screen Archetype）

> 此范式是上述指导思想在后台（professional）角色上的具体落地，适用于所有 `screen_granularity = "multi_function_per_page"` 的角色，不绑定任何行业。

**核心原则**：后台用户高频长时间操作，典型操作单元是**一个实体的完整管理**，不是"查看列表"、"创建记录"、"编辑记录"等分步操作。因此，同一个实体的 CRUD 操作应合并为**一个屏幕**的不同 view_mode，而非拆成多个独立屏幕 — 减少页面跳转就是提升效率。

**标准后台管理页 = 列表主视图 + 同页创建/编辑 + 行内操作**：

```json
{
  "id": "S_EXAMPLE",
  "name": "邀请码管理",
  "interaction_type": "MG2-L",
  "tasks": ["T_list", "T_create", "T_invalidate", "T_delete"],
  "view_modes": [
    {
      "id": "list",
      "label": "列表视图",
      "trigger": "页面初始加载",
      "layout": "顶部操作栏（新建按钮+搜索框）+ 数据表格（列: 邀请码/使用状态/使用时间/操作）+ 分页",
      "active_components": ["action-bar", "search-bar", "data-table", "pagination"],
      "available_actions": ["新建", "搜索", "点击行查看", "行内作废", "行内删除"]
    },
    {
      "id": "create_modal",
      "label": "新建弹窗",
      "trigger": "点击「新建」按钮",
      "layout": "列表不变，弹出模态窗口/抽屉，包含创建表单",
      "active_components": ["data-table", "create-modal-form"],
      "available_actions": ["填写表单", "提交", "取消（关闭弹窗回到列表）"]
    },
    {
      "id": "detail_panel",
      "label": "详情侧边栏",
      "trigger": "点击表格某行",
      "layout": "列表缩窄至左侧60%，右侧40%滑出详情面板，展示使用情况",
      "active_components": ["data-table-narrow", "detail-panel", "action-buttons"],
      "available_actions": ["作废", "删除", "关闭面板"]
    }
  ]
}
```

**与前端（consumer）屏幕的对比**：

| 维度 | 后台（multi_function_per_page） | 前端（single_task_focus） |
|------|-------------------------------|-------------------------|
| 同实体 CRUD | **一个屏幕**：列表+创建弹窗+详情面板+行内操作 | **多个屏幕**：列表页→详情页→编辑页，页面间导航 |
| 创建操作 | 同页弹窗/抽屉，不离开列表上下文 | 独立全屏表单页 |
| 详情查看 | 侧边栏面板，列表仍可见 | 独立全屏详情页 |
| 批量操作 | 复选框+批量操作栏（批量删除/导出/状态变更） | 不常见，逐条操作 |
| 导航 | 侧边栏菜单，主区域内容切换，极少整页跳转 | 纵深导航（进入→返回），底部 Tab 切换 |
| 数据密度 | 高密度表格，多列信息，紧凑布局 | 低密度卡片，重视留白和视觉层次 |

**合并规则**：骨架生成器按 1 task = 1 screen 生成骨架后，LLM 在 Step 2 **必须**对后台角色执行合并：
1. 识别同一实体（entity-model 中的同一 entity）的所有屏幕
2. 将 list/create/edit/detail/status-change 合并为一个屏幕
3. 原来的多个 interaction_type 转换为 view_modes（列表=主视图，创建=弹窗/抽屉，详情=侧边栏面板）
4. 合并后的屏幕 interaction_type 取列表类型（MG2-L 或 MG3），tasks 合并所有原屏幕的 task_id

---

### 布局差异化设计原则（Layout Differentiation Principle）

> **核心洞察**：`interaction_type` 是渲染器的布局模板选择器，但**不是屏幕的设计身份**。同一个 `interaction_type`（如 MG2-C 创建表单）可以对应完全不同的业务场景——"注册账号"和"创建商品"虽然都是表单，但布局、组件、信息密度应该完全不同。LLM 必须从**业务目的**推导每个屏幕的独特布局，而非从 interaction_type 复制。

**为什么 LLM 会退化为模板？**

当 LLM 批量生成多个屏幕时，会无意识地复用上一个屏幕的结构（components 数组、layout_type、states），导致 30 个屏幕看起来像 5 个模板的复制品。这不是 LLM 的能力问题，而是**批量生成模式的心理陷阱**——写到第 15 个屏幕时，LLM 已经建立了"form 就是这样"的内隐模板。

**对抗退化的设计方法——「业务目的三问」**：

对每个屏幕，LLM 在设计前必须回答三个问题，答案直接决定布局：

| 问题 | 答案决定了什么 |
|------|-------------|
| 1. 用户来到这个屏幕的**核心目的**是什么？（完成交易/获取信息/管理数据/做决策/社交互动/创作内容） | 屏幕的主次区域划分 |
| 2. 这个目的需要什么样的**信息结构**？（线性流程/对比浏览/实时监控/层级导航/自由探索/聚焦输入） | components 的组织方式 |
| 3. 这个信息结构在**物理空间**中如何组织？（单列聚焦/左右分栏/上下分层/卡片矩阵/时间线/全屏沉浸） | layout_type 的选择 |

**示例——同样是"表单"（interaction_type = MG2-C），推导出完全不同的布局**：

| 屏幕 | 核心目的 | 信息结构 | 物理布局 | layout_type |
|------|---------|---------|---------|-------------|
| 注册 | 快速完成，建立信任 | 聚焦输入（最少字段） | 居中卡片+信任标识 | `auth_card` |
| 创建商品 | 填充完整商品信息 | 多区块（图片+规格+价格+描述） | 分区块长表单 | `structured_editor` |
| 提交工单 | 在上下文中描述问题 | 上下文+输入（引用订单/商品） | 上半展示+下半输入 | `contextual_form` |
| 充值 | 选择金额并支付 | 选择（预设金额）+输入（自定义） | 金额卡片+支付方式 | `amount_selector` |
| 创建广告 | 配置投放策略 | 向导（素材→定向→预算→预览） | 步骤条+预览面板 | `campaign_wizard` |

**示例——同样是"列表"（interaction_type = MG2-L），推导出完全不同的布局**：

| 屏幕 | 核心目的 | 信息结构 | 物理布局 | layout_type |
|------|---------|---------|---------|-------------|
| 商品列表（买家） | 发现感兴趣的商品 | 视觉浏览（图片为主） | 卡片网格+筛选侧栏 | `visual_card_grid` |
| 订单列表（买家） | 找到特定订单、跟踪状态 | 时间序列+状态标签 | 状态分Tab+时间线卡片 | `status_timeline` |
| 商品管理（商户） | 高效管理库存和上下架 | 数据密集表格+批量操作 | 紧凑表格+行内编辑 | `dense_data_table` |
| 工单列表（管理员） | 按优先级处理待办 | 优先级队列+详情预览 | 待办队列+侧边详情 | `priority_queue` |

**LLM 设计时的强制检查**：

完成一组屏幕设计后，LLM **必须**执行以下自检：
1. 列出所有 `layout_type` 的分布。如果任何单一 layout_type 占比 > 15%（即超过总屏幕数的 15%），必须逐个审查是否可以差异化
2. 取出所有同一 `interaction_type` 的屏幕，两两对比 `components` 数组。如果两个屏幕的 components 名称集合 jaccard 相似度 > 50%，必须说明为什么它们需要相同组件（同实体不同视角是合理的，复制粘贴不是）
3. `layout_type` **不能直接复用 interaction_type 的名称**（如不能把 layout_type 写成 "MG2-L"），必须是描述性的语义名称

---

### interaction_type 渲染器支持列表

线框渲染器根据 `interaction_type` 选择布局模板。**必须从以下列表中选择**，不可自创类型（自创类型会退化为无差别表格）。LLM 应选择最接近业务场景的类型，自由设计意图写入 `description` 和 `interaction_pattern`。

| 类型 | 名称 | 布局 slots | 适用场景 |
|------|------|-----------|---------|
| **MG1** | 只读列表 | header, filter-chips, read-only-list, pagination | 管理列表（只读浏览、搜索筛选） |
| **MG2-L** | CRUD列表 | header, search-bar, filter-chips, table, pagination, action-bar | 可增删改查的数据表格 |
| **MG2-C** | 创建表单 | header, form-body, field-group, action-bar | 新建实体的表单页 |
| **MG2-E** | 编辑表单 | header, form-body, field-group, action-bar | 编辑已有实体的表单页 |
| **MG2-D** | 详情页 | header, detail-fields, action-bar | 实体详情只读展示 |
| **MG2-ST** | 状态转换 | header, detail-fields, state-badge, action-bar | 触发状态迁移（如审核通过/拒绝） |
| **MG3** | 状态机列表 | header, state-tabs, table, action-bar | 按状态分 tab 的列表+行内状态操作 |
| **MG4** | 审批队列 | header, pending-badge, approval-cards, action-bar | 待审/已审队列，逐条审批 |
| **MG5** | 主从详情 | header, master-info, sub-tabs, sub-list | 主实体+多子实体 tab |
| **MG6** | 树形管理 | header, tree-toolbar, tree-view | 层级结构的增删移动 |
| **MG7** | 仪表盘 | header, kpi-cards, charts, date-filter | KPI 卡片+图表+日期筛选 |
| **MG8** | 配置页 | header, config-sections, save-bar | 分组设置项+保存 |
| **SY1** | 新手引导 | illustration, step-content, dots, action-bar | 步进式引导+插图 |
| **SY2** | 向导表单 | progress-steps, form-body, action-bar | 多步骤表单+进度条 |
| **CT1** | 内容 Feed | search-bar, filter-chips, feed-cards | 可搜索可筛选的卡片流 |
| **CT2** | 内容阅读 | cover-image, title, meta, body-content, action-bar | 全屏沉浸阅读+封面+操作栏 |
| **CT3** | 个人主页 | avatar-header, profile-fields, action-bar | 用户资料展示+编辑 |
| **CT4** | 卡片翻转 | progress, card-main, action-buttons | 滑动决策/翻转卡片/逐条审阅（适用于逐项处理、对比选择） |
| **CT5** | 媒体播放 | player-screen, progress-bar, controls | 音视频播放器 |
| **CT6** | 图库 | gallery-grid, action-bar | 图片网格+灯箱预览 |
| **CT7** | 搜索结果 | search-bar, filter-chips, results-list, pagination | 搜索+筛选+结果列表 |
| **EC1** | 条目详情 | product-image, title-price, specs, features, action-bar | 产品/定价页+操作 CTA |
| **EC2** | 结算 | item-list, total, payment-options, action-bar | 待处理列表+支付选择 |
| **WK3** | 文档编辑器 | editor-toolbar, editor-area, preview, status-bar | 双栏编辑器+工具栏+预览 |
| **SB1** | 提交表单 | form-body, action-bar | 反馈/举报/申请提交 |
| **RT4** | 通知中心 | notif-tabs, notif-list | 分类通知列表+已读未读 |

**选型指南**（常见业务场景→推荐类型）：
- 聊天/对话界面 → **CT2**（body-content 区域渲染对话气泡，description 说明聊天布局）
- 工作台/编辑器 → **WK3**（editor-area+preview 双栏）
- 仪表盘/监控 → **MG7**（KPI+图表）
- 图表/可视化 → **MG7**（charts slot）或 **CT2**（body-content 区域渲染可视化）
- AI 生成流程 → **SY2**（向导表单，多步骤）或 **SB1**（提交表单+结果）
- 审核工作台 → **MG4**（审批队列）或 **MG3**（状态机列表）
- 日志查看 → **MG1**（只读列表）
- 注册/登录 → **MG2-C**（创建表单）
- 订阅/付费 → **EC1**（产品定价）+ **EC2**（结账）

### node.screens 嵌入规则

每个 `node.screens` 数组中必须放入**完整的 screen 对象**（包含 id、name、description、platform、components 等全部字段），而非仅引用 `{screen_id: "S001"}`。下游工具（review_hub_server、_common.py）直接从 `node.screens[].id` 读取屏幕数据，不做二次查找。

`screen_index` 作为顶层快速索引同时存在（key = screen_id, value = 完整 screen 对象），与 node 内嵌的 screen 数据保持一致。

---

## 工作流

```
前置检查：
  .allforai/product-concept/concept-baseline.json      自动加载（推拉协议 §三.A）→ 不存在则 WARNING，不阻塞
  .allforai/experience-map/journey-emotion-map.json    必须存在
  .allforai/product-map/task-inventory.json             必须存在
  .allforai/product-map/role-profiles.json              可选
  .allforai/product-map/business-flows.json             可选
  .allforai/product-map/view-objects.json               可选
  .allforai/product-map/entity-model.json               可选
  .allforai/product-concept/product-concept.json        可选（跨级拉取源）

  跨级原始数据拉取（按需，推拉协议 §三.B）：
    product-mechanisms.json:
      - governance_styles[].downstream_implications  → 决定是否生成审核队列/状态屏幕
      - governance_styles[].rationale                → 验收时判断治理设计是否合理
    role-value-map.json:
      - roles[].operation_profile.density            → 决定后台屏幕的 view_modes 复杂度

Step 1: 加载全部上游数据
      读取 concept-baseline.json（产品定位、角色粒度、治理风格 — 背景知识）
      读取跨级拉取字段（downstream_implications, density）
      读取所有可用的前置数据到上下文
      ↓
Step 1.5: 生成骨架（自动）
      运行 gen_experience_map.py 生成 experience-map-skeleton.json
      确定性字段预填（operation_lines、nodes、screens 结构、data_fields、interaction_type、flow_context）
      ↓
Step 2: LLM 自由设计体验地图
      加载骨架，在此基础上填充 LLM 创意字段
      LLM 理解产品语义后，自主设计每个界面
      按角色分组，每个角色的界面独立设计
      ↓
Step 3: LLM 自审验收（loop）
      合格性验收：硬性规则 + 设计质量规则 + 上游基线验收
      不通过 → 修正 → 重新验收（最多 3 轮）
      ↓
Step 3.1: 质量提升 loop（设计精炼）
      5 维度评分 → 识别低分 screen → 提升 → 重新评分
      Round 1: 修补短板（低分 → 及格）
      Round 2: 提升核心（core 任务 screen 精打磨）
      Round 3: 统一风格（同类 screen 交互一致性）
      ↓
Step 3.5: Playwright 线框验证（loop，需 Playwright MCP）
      渲染验证 + 业务合理性判断
      不通过 → 修正 → 重新验证（最多 2 轮）
      ↓
Step 3.6: 模式扫描 + 行为规范（自动，不停顿）
      功能模式识别 + 行为规范检测
      标签写入 screen 节点
      ↓
Step 4: 输出
      写入 experience-map.json + report
```

---

### Step 1：加载全部上游数据

加载所有可用的前置数据。LLM 需要充分理解：

1. **产品是什么** — product-concept 的定位、创新概念、目标用户
2. **用户要做什么** — task-inventory 的全部任务（区分 basic/core）
3. **数据长什么样** — entity-model 的实体、字段、关系、状态机
4. **流程怎么走** — business-flows 的业务流节点和交接关系
5. **每步什么感受** — journey-emotion 的情绪弧线和设计提示
6. **界面需要什么数据** — view-objects 的字段和操作绑定

---

### Step 1.5：生成骨架（自动）

运行预构建脚本生成确定性骨架，减少 LLM token 消耗和幻觉：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_experience_map.py <BASE_PATH> --mode auto --shard experience-map
```

**脚本输出**：`experience-map-skeleton.json`，包含：

| 已填充（确定性） | LLM 待填充（占位空值） |
|-----------------|---------------------|
| operation_lines 结构（从 business-flows） | `name`（界面名称） |
| nodes（从 flow nodes） | `description`（设计意图） |
| screen.tasks（从 task_ref） | `components`（组件清单） |
| screen.platform（从 role audience_type） | `interaction_pattern`（交互模式） |
| screen.interaction_type（⚠️ 机械推断，仅供参考） | `emotion_design`（情绪设计） |
| screen.data_fields（从 entity-model + view-objects） | `states`（界面状态） |
| screen.vo_ref（从 view-objects 匹配） | `layout_type`（语义化布局名称） |
| screen.actions（从 CRUD 推断） | `layout_description`（空间布局描述） |
| screen.flow_context（从操作线顺序） | |
| screen 去重（同 task+role 复用） | |
| 独立/孤儿任务的额外操作线 | |
| _emotion_ref（从 journey-emotion 附加） | |
| _governance_hint（从 product-mechanisms 附加到 operation_line） | |

**骨架加载**：Step 2 中 LLM 读取骨架文件，在已有结构上填充创意字段。**重要**：骨架中的 `interaction_type` 是脚本的机械推断，LLM 在 Phase B 自由设计时应忽略它，设计完成后在 Phase C 最后一步才决定最终的 interaction_type。

---

### Step 2：LLM 自由设计体验地图

LLM 加载 `experience-map-skeleton.json`，在骨架基础上进行设计。骨架提供了 operation_lines > nodes > screens 结构、data_fields、flow_context 等确定性数据。

**⚠️ 关键设计顺序：先设计，后映射渲染器**

骨架中预填的 `interaction_type` 是脚本的机械推断，**LLM 必须忽略它，先完成自由设计，最后才回头选择最接近的渲染器类型**。这样做是为了防止 LLM 被 interaction_type 锚定，导致所有同类型屏幕长得一样。

```
错误顺序：看到 interaction_type=MG2-C → "这是表单" → 复制表单模板 → 所有表单一样
正确顺序：理解业务目的 → 自由设计布局和组件 → 最后选 interaction_type 给渲染器用
```

**LLM 在骨架上的工作**（按此顺序执行）：

**Phase A — 理解上下文**（每个屏幕都要做）：
1. **消费 `_governance_hint`**：骨架中每条 operation_line 可能携带 `_governance_hint` 字段（含 style/downstream_implications/system_boundary）。LLM **必须**阅读此字段并据此决定：该操作线中的屏幕是否需要审核/审批界面？注册/提交表单应包含哪些字段？哪些功能是外部系统不需要表单？`downstream_implications` 中声明的屏幕需求是否都有对应屏幕？
2. **合并/拆分 screens**：骨架按 1 task = 1 screen 生成，LLM **必须**根据角色的 screen_granularity 执行合并：
    - **后台角色**（`multi_function_per_page`）：同一实体的 list/create/edit/detail/status-change 任务 → 合并为一个屏幕，原操作变为 view_modes（见「后台屏幕范式」）。合并后 tasks 合并所有原屏幕的 task_id
    - **前端角色**（`single_task_focus`）：可拆分复杂任务为多步骤屏幕，每步独立全屏

**Phase B — 自由设计**（核心创意阶段，**不看 interaction_type**）：
3. 回答**「业务目的三问」**（见布局差异化设计原则）：核心目的 → 信息结构 → 物理布局
4. 填充 `layout_type` + `layout_description`：从三问答案推导。layout_type 必须是语义名称（如 `auth_card`、`priority_queue`），不能是通用标签
5. 填充 `name`：为每个界面命名（中文产品语言）
6. 填充 `description`：说明设计意图（2-3 句话，回答 D1+D4，包含三问推导过程）
7. 填充 `components`：设计组件清单（每个含 type/purpose/behavior/data_source）
8. 填充 `interaction_pattern`：描述交互模式（1-2 句话）
9. 填充 `emotion_design`：基于 `_emotion_ref` 的情绪设计决策
10. 填充 `states`：empty/loading/error/success + 业务特定状态
11. **填充 `view_modes`**：对 `multi_function_per_page` 角色的屏幕，设计屏幕内的视图模式流转

**Phase C — 审查与映射**（设计完成后回头修正）：
12. **审查 `data_fields`**：骨架从 entity-model 机械复制字段，LLM 必须以用户视角逐字段审查：
   - **该不该出现**：系统自动生成的字段（如主键、时间戳、外键）不应出现在创建/编辑表单中
   - **能不能编辑**：骨架的 `input_widget` 不区分界面语境，LLM 须根据业务语义判断可编辑性
13. **最后一步：选择 `interaction_type`**：根据已完成的设计，从渲染器支持列表中选择**最接近**的类型。这一步纯粹为了渲染器兼容，不影响已设计的 layout_type/components/layout_description

**额外的设计思考**（超越骨架）：

1. **理解数据结构**：entity-model 告诉你每个界面需要展示什么字段、有哪些状态转换
2. **匹配情绪弧线**：journey-emotion 告诉你用户在每个节点的情绪，指导交互密度和反馈方式
3. **尊重前后台交互指导思想差异**（见「前后台交互指导思想」section）：
   - consumer：人多低频 → 低信息密度、强引导、单任务聚焦、显式操作、严格容错
   - professional：人少高频 → 高信息密度、弱引导、同页多功能、隐式操作（行内编辑/批量/快捷键）、宽松容错
4. **组件语义前提验证**：每个组件/筛选/排序/分类方式都隐含了对底层数据的假设（作用域、基数、更新来源、统计基础等）。设计时必须验证这些假设是否被当前屏幕的数据模型支撑 — 如果数据模型不满足组件的语义前提，该组件就不应出现。具体执行：对每个组件回答三个问题——(a) 这个组件预设的数据来源是什么？（全局聚合 vs 用户私有 vs 实时流） (b) 当前屏幕的数据实际是什么？ (c) 两者是否匹配？不匹配则删除该组件
5. **创新界面**：product-concept 中的创新概念应该有独特的交互设计，不套用标准模板。创新功能的交互模式应从其业务本质推导，而非退化为通用表单
6. **治理风格驱动设计**：骨架中每条 operation_line 已注入 `_governance_hint`（来自 product-mechanisms.json），LLM **必须**阅读并遵循。如果骨架无此字段，从 concept-baseline.json 的 `governance_styles` 和 product-mechanisms.json 的完整数据中拉取。对每条业务流：
   - **严格管控**（strict）→ 必须有审核队列、状态跟踪、审核员工作台
   - **自动审核**（auto_review）→ 系统自动处理，只需异常队列和规则配置界面，**不需要**人工审核屏幕
   - **宽松高效**（lenient）→ **不生成审核屏幕**，改用举报/申诉通道、违规记录、事后追究
   - **`downstream_implications`** → 直接转化为屏幕需求（如"需要规则引擎配置界面"→ 必须有对应屏幕）
   - **`system_boundary.external`** → 该功能不在本系统屏幕中出现为可编辑表单（如"实名认证"是外部系统，注册表单只需最小信息+外部系统入口）
   - **`system_boundary.in_scope`** → 只有这些功能需要完整的表单/流程屏幕
7. **操作频度驱动粒度**：读取每个角色的 `operation_profile`，决定屏幕合并/拆分策略：
   - `screen_granularity: "multi_function_per_page"` → 相关任务优先合并为同一屏幕的不同 Tab/Section，减少跳转
   - `screen_granularity: "single_task_focus"` → 每个任务独立屏幕，纵深导航
   - `high_frequency_tasks` 中的任务 → 必须在 1-2 次点击内可达，不能藏在深层菜单

**屏幕合并原则**：搜索和列表通常是同一屏幕的两种状态（搜索是在现有列表上执行过滤，产生新的结果列表），不应拆为两个独立屏幕。类似地，同一实体的"查看全部"和"按条件筛选"也是同一屏幕的不同 view_mode。判断是否合并的标准：两个屏幕操作的是同一数据集合且交互模式可以用 Tab/筛选/搜索框切换 → 合并为一个屏幕的不同 view_mode。

**屏幕去重**：同一个任务可能出现在多条业务流中（如"下载场景包"同时出现在 F001/F002/F003/F004）。LLM 为该任务只设计一个屏幕（一个 screen_id），在不同操作线的节点中复用同一个 screen 对象。**同一个操作线内不应出现重复的 screen_id**。

**设计输出**：对每个界面写出 `description`（设计意图）、`components`（组件清单）、`interaction_pattern`（交互模式描述），而不仅仅是一个交互类型标签。

**大文件处理（分批设计）**：当 screen 数 > 30 时，**禁止**将全部设计决策压缩到一个 Python dict 中——这会导致模板化设计，丧失逐屏思考的质量。改用以下分批策略：

1. **按应用分批**：将所有屏幕按 `app` 字段分组（如 website 组、merchant 组、admin 组），每组作为一个批次。**注意**：跨角色操作线中的屏幕按各自的 `app` 归入不同批次（而非按操作线的主角色），确保每个屏幕从正确的应用视角设计
2. **每批次独立设计**：LLM 加载该批次涉及的上游数据子集（相关任务、实体、情绪节点），从该应用用户的视角对每个屏幕独立思考后输出设计
3. **使用 Python 脚本合并**：每批次的设计结果写入临时 JSON 文件，最终用 Python 脚本合并到骨架中
4. **逐屏质量保证**：每个屏幕的 `description` 必须 2-3 句话（≥ 40 字）、`states` 必须包含业务特定状态、`emotion_design` 必须回应 `_emotion_ref`

**批次脚本模板**（LLM 为每个批次生成一个这样的脚本）：

```python
# batch_fill_{app}.py — 按应用分批，每个屏幕独立设计，不共享模板函数
# 注意：该批次内所有屏幕属于同一个应用（如 merchant），从该应用用户的视角设计
#
# 设计流程：
# 1. 对每个屏幕，先回答「业务目的三问」（见布局差异化设计原则）
# 2. 从三问的答案推导 layout_type 和 components
# 3. 确保与前一个屏幕的布局不同（如果相同，重新审视三问的答案）

BATCH_DESIGNS = {
    "S001": {
        # ── 业务目的三问（指导设计，不写入 JSON） ──
        # Q1 核心目的: 用户快速完成注册，建立对平台的信任
        # Q2 信息结构: 聚焦输入，最少字段，信任标识前置
        # Q3 物理布局: 居中卡片，不需要侧边栏，背景留白
        # ── 从三问推导的设计 ──
        "name": "...",
        "description": "...(≥40字，回答 D1+D4，包含三问推导过程的设计理由)...",
        "components": [...],  # 每个含 type/purpose/behavior/data_source
        "interaction_pattern": "...",
        "layout_type": "auth_card",  # 从 Q3 推导，不是从 interaction_type 复制
        "layout_description": "居中登录卡片(480px宽)，上方 logo+品牌标语，卡片内邮箱/密码字段+登录按钮，下方注册链接和 OAuth 入口，背景为浅色品牌色渐变",
        "emotion_design": {    # 结构化对象，不是字符串
            "source_emotion": "...",
            "source_hint": "...",
            "design_response": "...",
            "visual_tone": "...",
            "interaction_density": "..."
        },
        "states": {            # 必须包含业务特定状态
            "empty": "...(该屏幕特有的空状态描述)...",
            "loading": "...",
            "error": "...",
            "success": "...",
            "business_state_1": "...(该屏幕特有的业务状态)..."
        }
    },
    # ...
}
```

**`layout_description` 字段**（新增必填）：用 1-2 句话描述该屏幕的**具体空间布局**——各区域的位置、大小、视觉权重。不同于 `interaction_pattern`（描述用户操作方式），`layout_description` 描述的是静态视觉结构。这个字段的目的是强迫 LLM 在脑中"画"出每个屏幕的样子，而非只贴标签。下游线框渲染器可以用这个描述生成更精确的布局。

**禁止的反模式**：
- ❌ `def get_states(platform, interaction_type)` — 模板函数，所有屏幕生成一样的状态
- ❌ `emotion_design = "简单的一句话"` — 字符串而非结构化对象
- ❌ 所有 desktop 屏幕都用 `sidebar-content`，所有 mobile 屏幕都用 `single-column`
- ❌ `description` 只有一句话重复屏幕名称
- ❌ `layout_type` 直接复用 interaction_type 名称（如 "MG2-L"、"form"、"list"）
- ❌ 多个屏幕共享相同的 `layout_description`（每个屏幕的空间布局描述必须独特）
- ❌ 跳过「业务目的三问」直接写 layout_type（三问注释是强制的思考过程）

---

### Step 3：LLM 自审验收（loop）

设计完成后，LLM 切换到验收者视角，检查以下规则：

**硬性规则（不通过 → 必须修正）**：

| 验收项 | 规则 | 检查方法 |
|--------|------|---------|
| 任务覆盖率 | 每个 task_id（含 independent_operations 和 orphan_tasks）至少出现在一个 screen 的 `tasks` 中 | 遍历 task-inventory 全部任务，检查未覆盖任务 |
| 屏幕归属 | 每个 screen 至少被一个 operation_line 的某个 node 引用 | 遍历所有 screen，检查是否在某个 node.screens 中 |
| 业务流连续性 | business-flows 中相邻节点对应的界面之间有 flow_context 连接 | 遍历每条流，检查 prev/next 链路 |
| 平台一致性 | consumer 角色的界面全部 mobile-ios，professional 全部 desktop-web | 按角色检查 platform 字段 |
| 界面非空 | 每个 screen 至少有 1 个 action 和 1 个 data_field | 遍历检查 |
| data_fields 格式 | 每个 data_field 必须是 `{name, label, type, input_widget, required}` 对象 | 遍历检查字段类型 |
| node.screens 完整性 | 每个 node.screens 元素必须是完整 screen 对象（含 id/name/platform 等），不能是引用 | 检查 node.screens[0] 是否有 id 和 name 字段 |
| 操作线内去重 | 同一个 operation_line 内不应有重复的 screen_id | 按操作线检查 screen_id 唯一性 |

**上游基线验收（硬性，LLM 判断）**：

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/skill-commons.md`「上游基线验收」。

LLM 同时加载 journey-emotion-map.json（情绪基线）和 experience-map.json（当前产出），逐条操作线对照审查：

| 审查视角 | LLM 判断什么 |
|---------|-------------|
| 情绪意图落地 | 每个 emotion_node 的 design_hint 是否在对应 screen 的 `emotion_design` 和 `interaction_pattern` 中有实质性体现？（不是照抄，而是判断设计是否回应了情绪需求） |
| 高风险保护 | risk=high/critical 的节点，对应 screen 的设计是否考虑了防错、确认、可逆性？ |
| 情绪弧线连贯 | 操作线中情绪从 anxious → delighted 的变化，在界面序列中有对应的体验递进吗？还是所有界面千篇一律？ |
| 旅程线完整 | 每条 journey_line 在 experience-map 中有对应的 operation_line |

**不通过 → 与硬性规则同等处理，LLM 修正对应 screen 后重新验收。**

**设计质量规则（硬性，不通过 → 必须修正）**：

| 验收项 | 规则 | 检查方法 |
|--------|------|---------|
| description 深度 | 每个 screen 的 `description` ≥ 40 字，且包含设计意图（不仅仅重复屏幕名称） | 遍历检查字符数，检查是否与 `name` 高度重复 |
| states 业务特定 | 每个 screen 的 `states` 除 4 个基础状态外，至少有 1 个业务特定状态 | 检查 states key 数量 > 4 |
| states 差异化 | 同类屏幕（相同 interaction_type）的 states 不能完全相同 | 按 interaction_type 分组，检查 states values 是否有差异 |
| emotion_design 结构 | 有 `_emotion_ref` 的 screen，`emotion_design` 必须是包含 `source_emotion` 和 `design_response` 的对象 | 检查类型和必填字段 |
| emotion_design 实质性 | `emotion_design.design_response` 必须是可操作的设计指令，不能是"保持简洁"等空泛描述 | LLM 判断是否可操作 |
| layout_type 多样性 | (a) 任何单一 layout_type 占比不超过全部屏幕的 15%（如 80 个屏幕中最多 12 个用同一 layout_type）；(b) layout_type 不能是 interaction_type 的简单复制（如 "form"、"list"、"MG2-L"）；(c) 每个 layout_type 必须是语义化名称，描述业务目的而非交互模式（如 `auth_card`、`priority_queue`、`structured_editor`） | 统计 layout_type 分布，检查占比超限的类型，检查是否与 interaction_type 重名 |
| layout_description 独特性 | 每个 screen 必须有 `layout_description` 字段（1-2 句话描述空间布局），且同一应用内不同 screen 的 layout_description 不能高度重复 | 按应用分组，检查 layout_description 是否存在且是否与其他 screen 的描述相似度 < 70% |
| interaction_type 准确性 | 创建操作不应是 CT2（内容阅读），删除操作不应是 MG1（只读），充值/提现等提交操作不应是 MG1（只读） | 交叉检查 actions 语义与 interaction_type 是否矛盾 |
| components 非空 | 每个 screen 至少 2 个 components，且每个 component 有 type/purpose/behavior | 遍历检查 |
| actions 语义匹配 | actions 中不应出现与屏幕无关的操作（如查看页面出现"保存"） | LLM 判断 actions 与 screen 业务场景是否匹配 |

**业务语义校验规则（硬性，不通过 → 必须修正）**：

> 这些规则检查 LLM 设计的业务合理性，防止"结构正确但业务错误"的屏幕通过验收。需要加载 `product-concept.json`（治理风格、角色操作频度）作为校验基准。

| 验收项 | 规则 | 检查方法 |
|--------|------|---------|
| **屏幕内容相似度** | 同一操作线内的屏幕，data_fields + components 的 jaccard 相似度不应 > 60% | 按操作线分组，计算每对屏幕的字段/组件名集合的 jaccard 系数。> 60% 的标记为"合并候选"，LLM 判断是否应合并为同一屏幕的不同状态/Tab |
| **功能-上下文适配** | 屏幕中的功能组件必须在该屏幕的业务上下文中合理 | LLM 逐屏审查：对每个 component/filter/sort/action 执行「数据语义三问」——(a) 这个组件预设的数据来源是什么？（全局聚合/用户私有/实时流/静态配置） (b) 当前屏幕的数据实际来源是什么？ (c) 两者是否匹配？**不匹配 → 删除该组件**。同时检查：发现型组件（筛选/排序/推荐）只出现在公共数据的浏览屏幕，不出现在用户私有数据的管理屏幕；注册/认证等流程的表单复杂度必须与 `_governance_hint` 匹配 |
| **概念治理规则回溯** | 屏幕设计必须符合 `_governance_hint`（骨架注入）或 `product-mechanisms.json` 中的 `governance_styles` | 对每个涉及审核/审批/注册的屏幕，检查对应业务流的治理风格：(a) 治理风格为 lenient → **不应有审核队列/审核状态屏幕** (b) 治理风格为 auto_review → 只需异常队列，**不需要人工审核工作台** (c) 治理风格为 strict → 必须有审核+状态跟踪+审核员工作台 (d) `system_boundary.external` 中的功能 → 不在本系统屏幕中出现为可编辑表单，只保留最小信息+外部系统入口 (e) `downstream_implications` 中声明的屏幕需求 → 必须有对应屏幕存在 |
| **孤立屏幕检测** | 每个屏幕应有概念层依据（对应的 task、business-flow 节点、或 governance 需求） | 如果一个屏幕的 `tasks` 引用为空且不在任何 business-flow 中，标记为"无概念依据"。LLM 判断是否应删除或补充对应的 task |
| **交互类型×应用适配** | 交互类型必须与应用类型匹配 | 检查规则：(a) app=website + platform=mobile-ios 的屏幕不应使用 MG2-L（重列表管理，应用 CT1 或简化列表） (b) app=admin/merchant + platform=desktop-web 的屏幕不应使用 CT1（休闲浏览 Feed，应用 MG1 或 MG2-L） (c) 参考 `operation_profile.screen_granularity`：merchant 角色的相关任务应优先合并为同页多功能（而非拆成多个独立屏幕） |
| **跨应用数据泄露** | 屏幕不应展示只属于其他应用的数据 | 检查规则：(a) app=provider 的屏幕不应包含"全平台统计"、"所有服务提供者"等平台级数据字段 (b) app=admin 的屏幕不应包含单个服务提供者的日常运营数据（如"我的工单"） (c) app=website 的屏幕不应包含后台管理字段（如"审核状态管理"） |

**软性规则（不通过 → 警告但不阻塞）**：

| 验收项 | 规则 |
|--------|------|
| 状态完整 | 每个界面应定义 empty/error 状态 |
| 导航可达 | 每个界面至少有一个 entry_point |
| 创新覆盖 | product-concept 中的创新概念应有对应的独特界面 |

**Loop 机制**：

```
生成体验地图 → 硬性规则检查 + 设计质量规则 + 上游基线验收（LLM 判断）
  全部通过 → Step 3.1 质量提升 loop
  不通过 →
    列出具体问题（哪些任务未覆盖、哪些情绪意图未落地、哪些高风险节点缺保护）
    LLM 修正对应界面
    → 重新验收（最多 3 轮）
  3 轮后仍不通过 → 记录剩余问题，WARNING 继续
```

---

### Step 3.1：质量提升 loop（设计精炼）

> Step 3 的合格性验收确保"没有错误"，Step 3.1 的质量提升确保"足够好"。这是两个不同的目标——合格性是底线，质量是天花板。

Step 3 通过后，进入质量提升 loop。该 loop 的目标不是修复错误，而是**持续提升设计质量**，因为 experience-map 的质量直接决定下游前端代码的质量。

#### 3.1.1 质量评分（每轮开始时执行）

LLM 对每个 screen 进行 5 维度打分（1-5 分），输出评分矩阵：

| 维度 | 1 分（差） | 3 分（及格） | 5 分（优秀） | 权重 |
|------|-----------|-------------|-------------|------|
| **D1 描述深度** | 重复屏幕名称，无设计意图 | 说明了用途但缺少"为什么"，< 60 字 | 清晰回答 D1+D4，≥ 80 字，包含设计权衡和替代方案理由 | 20% |
| **D2 状态完整性** | 只有 4 个基础状态 | 有 1-2 个业务状态但描述空泛 | ≥ 3 个业务特定状态，每个有具体交互描述，覆盖正常+异常+边界场景 | 25% |
| **D3 情绪落地** | emotion_design 为 null 或空泛字符串 | 有结构化对象但 design_response 是通用原则 | design_response 是该屏幕特有的可操作设计指令，与 source_emotion 强关联 | 15% |
| **D4 组件精确性** | 组件名通用（form, table），缺少 behavior | 有 purpose 但 behavior 空泛 | 每个组件的 behavior 描述了具体交互细节（触发条件、动画、反馈方式），data_source 指向正确实体 | 25% |
| **D5 交互适配** | interaction_type 与业务矛盾，layout_type 千篇一律 | interaction_type 基本正确，layout_type 合理 | interaction_type 精确匹配业务场景，layout_type 充分利用平台特性（mobile 手势、desktop 多列），interaction_pattern 描述独特交互 | 15% |

**加权总分** = D1×0.20 + D2×0.25 + D3×0.15 + D4×0.25 + D5×0.15

**质量阈值**：
- 每个 screen 加权总分 ≥ 3.5
- 全局平均分 ≥ 4.0
- 无任何 screen 在任何维度 ≤ 1

#### 3.1.2 识别提升目标

评分完成后，按优先级排序需要提升的 screen：

```
1. 任何维度 ≤ 1 的 screen → 最高优先级（质量缺陷）
2. 加权总分 < 3.5 的 screen → 高优先级（低于阈值）
3. 加权总分 3.5-4.0 且承载 core 任务的 screen → 中优先级（核心屏幕应更高）
4. 全局平均分 < 4.0 → 选取最低分的 20% screen 提升
```

对每个需要提升的 screen，生成**具体的提升指令**（不是"请改进"，而是"S020 的 states 缺少 payment_timeout 状态，需要添加超时后的用户引导交互"）。

#### 3.1.3 执行提升

按提升指令逐个 screen 重新设计。重新设计时 LLM 必须：

1. **重新阅读该 screen 的上游数据**（对应 task、entity 字段、emotion_node），不凭记忆
2. **参考同角色其他高分 screen 的设计模式**，保持一致性
3. **对比修改前后**，确认每个维度的分数确实提升了

**产品经理视角审查**（每个被修改的 screen 必须回答）：

| 审查问题 | 不合格信号 |
|---------|-----------|
| 用户在这个界面要完成什么任务？界面设计是否让任务路径最短？ | 操作步骤冗余、关键 CTA 不突出 |
| 用户从哪里来、到哪里去？前后界面的衔接是否自然？ | flow_context 断裂、缺少返回路径 |
| 用户在这一步的情绪是什么？设计是否回应了这个情绪？ | 焦虑场景缺少安全感设计、成就场景缺少正向反馈 |
| 如果操作失败了，用户能恢复吗？ | 缺少错误状态、没有重试/回退路径 |
| 这个界面的数据字段是用户需要看到/填写的吗？有没有系统字段泄露？ | 出现 id、created_at 等系统字段；缺少用户真正需要的字段 |
| 同类界面（如所有审批页）的交互模式是否一致？ | 同类型屏幕的组件布局/操作方式不统一 |

#### 3.1.4 Loop 控制

```
Step 3 合格性验收通过
  ↓
Round 1: 质量评分 → 识别低分 screen → 提升 → 重新评分
  全局平均 ≥ 4.0 且无 screen < 3.5 → Step 3.5
  ↓
Round 2: 聚焦 core 任务 screen → 对标竞品设计 → 提升 → 重新评分
  全局平均 ≥ 4.0 且无 screen < 3.5 → Step 3.5
  ↓
Round 3: 跨屏一致性审查 → 统一同类 screen 的交互模式 → 最终评分
  → Step 3.5（无论是否达标，记录最终评分到报告）
```

**每轮的侧重点不同**：
- **Round 1**：修补短板 — 把低分 screen 拉到及格线以上
- **Round 2**：提升核心 — 重点打磨承载 core 任务的 screen，可 WebSearch 参考竞品设计
- **Round 3**：统一风格 — 确保同类 screen（如所有 MG4 审批页、所有 CT2 详情页）的交互模式一致

**自动模式行为**：全自动模式下 3 轮全部自动执行，不停顿。每轮输出一行摘要：
```
Quality Round 1: avg 3.6→4.1, improved 12 screens, lowest S020(3.2→3.8)
Quality Round 2: avg 4.1→4.3, improved 5 core screens
Quality Round 3: avg 4.3→4.4, unified 3 pattern groups
```

**评分结果持久化**：最终评分写入 `experience-map-report.md` 的质量评分 section，每个 screen 的得分也写入 screen 对象的 `_quality_score` 字段（供下游 design-audit 参考）：

```json
{
  "id": "S020",
  "_quality_score": {
    "description_depth": 4,
    "states_completeness": 5,
    "emotion_alignment": 4,
    "component_precision": 4,
    "interaction_fit": 5,
    "weighted_total": 4.4,
    "round_improved": 2
  }
}
```

---

### Step 3.5：Playwright 线框验证（loop）

> 需要 Playwright MCP 可用（`mcp__playwright__browser_navigate` 或 `mcp__plugin_playwright_playwright__browser_navigate`）。不可用时跳过此步骤，在报告中标注 `playwright_verified: false`。

experience-map.json 写入后，使用 Playwright 自动化浏览器验证 Review Hub 线框渲染质量。此步骤分三轮检查：**结构验证 → 逐屏渲染验证 → 业务合理性判断**。

---

#### 3.5.1 启动与结构验证

```
1. 确保 Review Hub 服务器运行中（http://localhost:18900/）
   不可达 → 启动: python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review_hub_server.py <BASE> --port 18900
2. 导航到 /wireframe 页面
3. browser_snapshot 获取完整页面快照
4. 从快照中提取操作线树结构，执行结构验证
```

**结构验证规则**（从页面快照中检查）：

| 检查项 | 通过条件 | 自动修复 |
|--------|---------|---------|
| 操作线数量 | 页面操作线数 = JSON 中 operation_lines 数 | 若不一致，检查是否有空操作线（nodes=0）并移除 |
| 屏幕数量 | 每条操作线的屏幕数 = JSON 中对应 nodes 内屏幕总数 | 检查 node.screens 嵌入完整性 |
| 操作线内去重 | 同一操作线内无重复 screen_id | 自动删除重复引用，保留首次出现 |
| interaction_type 合法性 | 所有 screen 的 interaction_type 在渲染器支持列表中 | 替换为最接近的合法类型（见选型指南） |

**操作线内去重自动修复**：

```python
# 检查逻辑：遍历每条操作线的所有 nodes，收集 screen_id
# 同一操作线内出现重复 screen_id → 删除后续出现的重复引用
# 不同操作线之间共享同一 screen_id 是正常的（多条旅程经过同一界面）
for line in operation_lines:
    seen_ids = set()
    for node in line["nodes"]:
        node["screens"] = [s for s in node["screens"] if s["id"] not in seen_ids and not seen_ids.add(s["id"])]
```

**interaction_type 自动修复映射**：

```
自创类型 → 最接近的合法类型：
  WORKSPACE/EDITOR  → WK3（文档编辑器）
  DASHBOARD/MONITOR → MG7（仪表盘）
  ANALYTICS/VIZ     → MG7（图表）或 CT2（可视化内容）
  REVIEW/APPROVE    → MG4（审批队列）
  LOG/HISTORY       → MG1（只读列表）
  AI-GEN/WIZARD     → SY2（向导表单）
  CHAT/DIALOGUE     → CT2（对话内容）
  INBOX/NOTIFICATION → MG3（状态机列表）或 RT4（通知中心）
  PROFILE/SETTINGS  → CT3（个人主页）或 MG8（配置页）
```

若自动修复后文件有变更 → 重新写入 experience-map.json → 刷新 /wireframe 页面。

---

#### 3.5.2 批量渲染验证

优先使用 `browser_run_code` 批量提取验证数据（1 次导航 + 2 次 JS 执行），替代逐屏点击。

**Step A — 批量提取页面内嵌数据**：

```
1. browser_navigate 到 /wireframe
2. browser_run_code 提取结构数据：

(() => {
  const results = {};
  // ALL_SCREENS 是 {sid: screenObj} 的字典，TREE_DATA 是操作线树，SIXV 是 6V 标注
  const sids = Object.keys(ALL_SCREENS);
  for (const sid of sids) {
    const sc = ALL_SCREENS[sid] || {};
    const fc = sc.flow_context || {};
    results[sid] = {
      name: sc.name || '',
      interaction_type: sc.interaction_type || '',
      data_fields_count: Array.isArray(sc.data_fields) ? sc.data_fields.length : 0,
      data_fields_valid: Array.isArray(sc.data_fields) && sc.data_fields.length > 0
        && typeof sc.data_fields[0] === 'object',
      actions_count: Array.isArray(sc.actions) ? sc.actions.length : 0,
      flow_has_prev: Array.isArray(fc.prev) && fc.prev.length > 0,
      flow_has_next: Array.isArray(fc.next) && fc.next.length > 0,
    };
  }
  return {
    screen_count: sids.length,
    tree_op_line_count: TREE_DATA.length,
    screens: results,
  };
})()
```

**Step B — 批量 fetch 验证 iframe 渲染**：

```
3. browser_run_code 批量 fetch 所有 screen 的渲染 HTML：

(async () => {
  const sids = Object.keys(ALL_SCREENS);
  const results = {};
  // 并发 fetch，每个 screen 的独立渲染页
  const fetches = sids.map(async (sid) => {
    try {
      const resp = await fetch('/wireframe/screen/' + sid);
      const html = await resp.text();
      const name = (ALL_SCREENS[sid] || {}).name || '';
      results[sid] = {
        html_length: html.length,
        not_blank: html.length > 200,
        has_title: name ? html.includes(name) : null,
        has_button: /<button[\s>]/i.test(html) || /class="[^"]*btn[^"]*"/i.test(html),
      };
    } catch (e) {
      results[sid] = { error: e.message };
    }
  });
  await Promise.all(fetches);
  return results;
})()
```

**Step C — LLM 分析批量结果**：

将 Step A 和 Step B 的返回值合并，按以下检查规则逐屏判定 PASS / FAIL：

| 检查项 | 通过条件 | 数据来源 | 失败原因分析 |
|--------|---------|---------|-------------|
| iframe 加载 | `not_blank === true`（HTML > 200 字符） | Step B | node.screens 嵌入不完整，或 JSON 格式错误 |
| 标题渲染 | `has_title === true` | Step B | screen.name 字段缺失 |
| 布局匹配 | `interaction_type` 在 ZONE_MAP 26 种合法类型内 | Step A | interaction_type 不在 ZONE_MAP 中 |
| 数据字段 | `data_fields_count > 0` 且 `data_fields_valid === true` | Step A | data_fields 为空数组或格式错误（字符串而非对象） |
| 操作按钮 | `actions_count > 0` 且 `has_button === true` | Step A + B | actions 字段为空 |
| Flow 连接 | `flow_has_prev \|\| flow_has_next` 至少一个为 true（首屏可无 prev，末屏可无 next） | Step A | flow_context 字段缺失或值为 null |

**常见渲染故障的自动修复**：

| 故障现象 | 根因 | 自动修复 |
|---------|------|---------|
| 表单页（MG2-C/MG2-E）空白崩溃 | actions 是字符串数组，渲染器调用 `.get("label")` 报错 | 将字符串 action 转为 `{"label": action, "frequency": "中"}` |
| flow_context 面板报错 | prev/next/entry_points/exit_points 值为 null | 将 null 替换为空数组 `[]` |
| 数据字段表格无内容 | data_fields 元素是字符串而非对象 | 将字符串转为 `{"name": field, "label": field, "type": "string", "input_widget": "text_input", "required": false}` |
| 屏幕渲染为无差别表格 | interaction_type 不在 ZONE_MAP | 回到 3.5.1 的 interaction_type 自动修复 |

**修复 → 重验循环**：

```
批量验证 → 汇总失败项
  全部 PASS → 进入 3.5.3 业务合理性判断
  有 FAIL →
    按故障类型分组（格式/数据/类型）
    执行对应自动修复
    重新写入 experience-map.json
    刷新 /wireframe 页面
    → 重新执行 Step A + B + C 批量验证（最多 2 轮）
  2 轮后仍有 FAIL → 记录到报告，WARNING 继续
```

> **Fallback**：若 `browser_run_code` 不可用（返回错误或超时），退回逐屏点击方式：对 /wireframe 页面树中的每个操作线展开后，逐一点击屏幕条目 → 等待 iframe 加载 → `browser_snapshot` 获取内容 → 按上表检查规则判定 PASS/FAIL。如果屏幕数 > 20，可抽样验证（每条操作线首尾屏幕 + 随机 1-2 个中间屏幕），抽样失败的操作线再全量验证。

---

#### 3.5.3 业务合理性判断

渲染验证通过后，LLM 从 Playwright 获取的页面快照中审查业务合理性：

**操作线维度**：

| 检查项 | 合理标准 | 不合理信号 |
|--------|---------|-----------|
| 屏幕数量 | 核心业务流 ≥ 3 屏幕 | 仅 1 个屏幕的操作线（如"订阅流"只有方案页没有支付确认页） |
| 流程完整性 | 操作线覆盖从入口到出口的完整闭环 | 流程在中间断裂（缺少确认/结果页） |
| 角色匹配 | 操作线中的屏幕角色一致 | 消费者操作线中混入管理员界面 |

**屏幕维度**：

| 检查项 | 合理标准 | 不合理信号 |
|--------|---------|-----------|
| 功能密度 | 每屏 1-3 个核心任务 | 单屏 > 5 个任务（功能堆叠）或 0 个任务（空壳屏幕） |
| 差异化 | 创新功能有独特交互 | 产品核心创新功能用普通表单（MG2-C）而非专用类型 |
| 模板-组件一致性 | interaction_type 渲染模板与 components 描述的交互形态匹配 | components 描述了可视化/画布/图表，但 interaction_type 用了列表/详情/表格模板 |
| 平台交互适配 | mobile 用触摸原生组件，desktop 用鼠标原生组件 | mobile 界面出现分页器（应为无限滚动）、右键菜单；desktop 出现滑动手势 |
| 平台差异 | mobile 和 desktop 布局明显不同 | desktop 界面也是单列竖屏布局 |
| 组件语义前提 | 每个组件隐含的数据假设必须被当前屏幕的数据模型支撑 | 组件预设的数据特征（作用域、基数、统计来源、更新频率）与屏幕实际数据不匹配 — 如组件需要多用户聚合统计但屏幕数据是单用户私有的，或组件需要实时流但数据是静态快照 |
| actions 相关性 | 操作与屏幕业务场景匹配 | 屏幕 A 的 actions 引用了属于屏幕 B 业务域的不相关任务 |

**不合理项处理**：

```
业务合理性审查 → 汇总不合理项
  全部合理 → Step 4
  有不合理项 →
    LLM 修正对应屏幕/操作线：
      - 补充缺失屏幕（如订阅流添加支付确认页）
      - 拆分过度堆叠的屏幕
      - 修正错误的 actions/tasks 引用
      - 调整 interaction_type
    重新写入 experience-map.json
    → 回到 3.5.1 重新验证（最多 1 轮）
  修正后仍有问题 → 记录到报告，WARNING 继续
```

---

#### 3.5.4 验证报告输出

验证完成后，输出结构化验证结果（写入 experience-map-report.md）：

```
## Playwright 验证结果

验证轮次: N
总屏幕数: X
验证通过: Y / X

### 自动修复记录
| 屏幕 | 问题 | 修复动作 |
|------|------|---------|
| S006 | interaction_type 非最佳匹配 | → 调整为更合适的类型 |
| S019 | 操作线内重复出现 | 删除重复引用 |

### 业务合理性
| 操作线 | 屏幕数 | 判断 | 备注 |
|--------|--------|------|------|
| 核心业务流 | 7 | 合理 | 核心流程完整 |
| 支付链路 | 1 | ⚠ 不合理 | 缺少支付确认页 |

### 最终状态
playwright_verified: true / false
auto_fixes_applied: N
remaining_issues: M
```

---

### Step 3.6：模式扫描 + 行为规范（自动，不停顿）

验收和线框验证通过后，自动执行功能模式识别和行为规范检测，将标签直接写入 experience-map.json 的 screen 节点。

#### 3.6.1 功能模式识别

LLM 扫描 task-inventory.json + experience-map.json，检测 8 类功能模式：

| 模式 ID | 模式名 | 检测规则 |
|---------|--------|---------|
| `PT-CRUD` | CRUD 管理台 | 同实体 tasks 涵盖 create + list/query + edit/update + delete |
| `PT-LIST-DETAIL` | 列表+详情对 | 同模块存在 list 类型界面 + detail 类型界面 |
| `PT-APPROVAL` | 审批流 | business-flows 中出现 submit→review→approve/reject 序列 |
| `PT-SEARCH` | 搜索+筛选+分页 | actions 同时含 search/filter + paginate |
| `PT-EXPORT` | 导出/报表 | task 标题或 actions 含 export/report/download |
| `PT-NOTIFY` | 通知触发 | business-flows 节点后紧跟 notify/send/push 节点 |
| `PT-PERMISSION` | 权限矩阵 | 同实体被 3+ 角色访问且每角色权限不同 |
| `PT-STATE` | 状态机 | task 涉及 status/state 字段 + 状态转换动作 |

对匹配的 screen，写入 `_pattern` 和 `_pattern_group` 字段。**注意**：`_pattern` 只标识功能模式（如 CRUD、审批流），**不推荐具体布局**——布局由 LLM 在 Step 2 根据业务目的三问独立决定，不应被功能模式倒推。

```json
{
  "id": "S005",
  "name": "工单管理",
  "_pattern": ["PT-CRUD", "PT-SEARCH"],
  "_pattern_group": "records-crud",
  ...
}
```

#### 3.6.2 行为规范检测

LLM 扫描 experience-map.json 中所有 screen 的 states、actions、requires_confirm、on_failure、validation_rules 字段，检测 9 类行为不一致：

| ID | 名称 | 统一什么 |
|----|------|----------|
| `BC-DELETE-CONFIRM` | 破坏性操作确认 | 弹窗确认 vs 行内确认 vs 无确认 |
| `BC-EMPTY-STATE` | 空状态展示 | 图文引导 vs 纯文字 vs 空白 |
| `BC-LOADING` | 加载模式 | 骨架屏 vs 转圈 vs 渐进加载 |
| `BC-ERROR-DISPLAY` | 错误展示 | Toast vs 行内提示 vs 整页错误 |
| `BC-FORM-VALIDATION` | 表单校验反馈 | 实时校验 vs 提交时校验 |
| `BC-SUCCESS-FEEDBACK` | 成功反馈 | Toast vs 跳转 vs 行内反馈 |
| `BC-PERMISSION-DENIED` | 权限不足 | 重定向 vs 禁用/灰化 vs 隐藏 |
| `BC-PAGINATION` | 分页行为 | 无限滚动 vs 分页器 |
| `BC-UNSAVED-GUARD` | 未保存变更守卫 | 浏览器原生 vs 自定义弹窗 vs 无守卫 |

对有不一致的类别（影响 >= 3 个界面且分歧 > 30%），采用多数方案作为标准。对每个 screen 写入 `_behavioral` 和 `_behavioral_standards` 字段：

```json
{
  "id": "S001",
  "_behavioral": ["BC-DELETE-CONFIRM", "BC-EMPTY-STATE"],
  "_behavioral_standards": {
    "BC-DELETE-CONFIRM": "modal_confirm",
    "BC-EMPTY-STATE": "illustration_text"
  },
  ...
}
```

**跳过条件**：若所有 9 类行为均一致或影响界面 < 3 个，跳过行为标签写入。

#### 输出

Step 3.6 完成后，screen 节点已包含 `_pattern*` 和 `_behavioral*` 字段，不生成独立文件。下游 ui-design 和 design-audit 直接从 experience-map.json 读取这些字段。

---

### Step 4：输出

写入最终产物：

- `experience-map.json` — 机器可读完整结构
- `experience-map-report.md` — 人类可读报告（操作线总览 + 平台分布 + 高风险节点 + 验收结果 + Playwright 验证结果）
- `experience-map-decisions.json` — 决策记录

---

### Variants 模式（--variants N）

当指定 `--variants N`（N >= 2）时，生成 N 套不同的信息架构方案：

**Step 2v: 多方案发散**
- 每套方案采用不同的信息架构策略：
  - 方案 A：任务驱动型（按用户任务组织界面）
  - 方案 B：对象驱动型（按数据实体组织界面）
  - 方案 C：流程驱动型（按业务流程组织界面）
  - 方案 D：角色驱动型（按角色工作台组织界面）
  - 方案 E：混合型（高频任务前置 + 对象导航）
- 使用 Agent 并发生成 N 套 experience-map
- 每套方案输出到 `.allforai/experience-map/variants/variant-{n}/`

**Step 2v.1: 对抗式评审**
- 如果 OPENROUTER_API_KEY 可用，使用 ask_model 从 5 个视角评审每套方案
- 输出对比矩阵 + 推荐方案

**Step 2v.2: 用户选择**
- 展示对比矩阵，用户选择一个方案
- 选中方案复制到主目录

---

## 全自动模式

**激活条件**（同时满足）：
1. `.allforai/product-concept/product-concept.json` 存在且含 `pipeline_preferences` 字段
2. 上下文含 `__orchestrator_auto: true`

**行为变化**：

| 步骤 | 标准模式 | 全自动模式 |
|------|----------|-----------|
| **Step 3 验收** | 展示验收结果 → 用户确认 | 自动 loop 修正，仅 ERROR 级停 |
| **--variants** | 用户选择方案 | 自动选择推荐方案 |

**基础设施偏好消费**：

读取 `pipeline_preferences.infrastructure` 数组，若非空则在界面清单中体现对应的基础设施需求（如设置页面、语言切换入口、主题切换等）。具体界面设计由 LLM 根据产品上下文判定。

---

## 输出文件结构

```
.allforai/experience-map/
├── experience-map.json              # 机器可读：操作线 > 节点 > 屏幕完整结构
├── experience-map-report.md         # 人类可读：体验地图摘要报告
├── experience-map-decisions.json    # 决策记录
├── journey-emotion-map.json         # 上游输入（由 journey-emotion 生成）
├── journey-emotion-decisions.json   # 上游输入（由 journey-emotion 生成）
├── variants/                        # --variants 模式
│   ├── variant-1/
│   │   └── experience-map.json
│   └── comparison-matrix.json
```

---

## 防御性规范

### 加载校验
- `journey-emotion-map.json`：解析失败 → 终止
- `task-inventory.json`：解析失败 → 终止

### 零结果处理
- 生成 0 个操作线 → 终止
- 生成 0 个屏幕 → 终止

### 执行失败保护
- 任何步骤遇到不可恢复错误 → 写入 `.allforai/experience-map/experience-map-error.json`，包含 `{"error": "...", "step": "...", "timestamp": "..."}`

### 上游过期检测
- **`journey-emotion-map.json`**：加载时比较 `generated_at` 与已有 `experience-map.json` 的 `generated_at`。上游更新 → 警告「journey-emotion 在 experience-map 上次运行后被更新，建议重新运行 /experience-map」。
- **`task-inventory.json`**：加载时比较 `generated_at`。上游更新 → 警告「task-inventory 在 experience-map 上次运行后被更新」。
- **`business-flows.json`**：同上。
- 仅警告不阻断。

---

## 3 条铁律

### 1. LLM 自由设计，规则只做验收

LLM 根据产品语义自主设计界面结构、交互方式、组件选择。`interaction_type` 必须从渲染器支持列表中选择最接近的类型（影响线框布局），但实际设计意图通过 `description`、`components`、`interaction_pattern` 完整表达。验收规则检查硬性约束（覆盖率、连续性、平台），不评判设计风格。

### 2. 三层结构完整对齐

operation_lines > nodes > screens 三层结构必须完整。每个操作线至少一个节点，每个节点至少一个屏幕。

### 3. 前后台交互思想不可混用

consumer（人多低频）和 professional（人少高频）的界面必须在信息密度、引导程度、页面粒度、操作方式上有本质差异。不是换个宽度的同一套设计——用前端的低密度引导式设计套后台是浪费专业用户时间，用后台的高密度效率式设计套前端是劝退大众用户。

### 4. 业务正确性优先于结构完整性

结构正确（字段存在、状态数量够）但业务错误（收藏夹加了内容筛选、注册页加了不该有的认证表单）的屏幕比结构不完整更危险——因为后者容易被自动检测，前者只能被人工审核发现。LLM 设计每个屏幕时必须回答：「这个功能/组件/字段在这个业务场景下是否合理？」概念阶段收集的治理风格和操作频度是判断合理性的基准。
