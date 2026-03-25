# Experience Map — Output Schema & Design Principles

> Loaded by the experience-map orchestrator during Step 2 (generation).
> Covers: output JSON schema, field format specs, interaction type registry, and design principles.

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
| `components` | 是 | **LLM 自由设计的组件清单**，每个组件包含 `type`（LLM 命名）、`purpose`、`behavior`、`data_source`、`render_as`（见下方 render_as 说明） |
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

### component render_as 说明

每个 component **必须**包含 `render_as` 字段，由 LLM 根据该组件的业务语义选择最合适的线框渲染形态。渲染器直接读取此字段，不做任何推断或模式匹配。

可选值：

| render_as | 线框表达 | 适用场景 | 常见误用（禁止） |
|-----------|---------|---------|----------------|
| `data_table` | 表头 + 多行数据行 + 分页 | 列表、表格、矩阵、队列 | 不要用于按钮组、标签页、单值展示 |
| `input_form` | 标签 + 输入框/选择器排列 | **多字段**表单、编辑器、配置页 | 不要用于单个选择器、排序切换、简单开关 |
| `key_value` | 标签-值横排对 | 详情面板、概览信息、摘要卡片 | 不要用于标签页切换、按钮组 |
| `bar_chart` | 柱状图占位 + 指标标签 | KPI、统计、图表、趋势、仪表盘 | 不要用于普通列表 |
| `search_filter` | 搜索框 + 筛选标签 | 搜索栏、过滤面板、侧边筛选 | — |
| `action_bar` | 按钮行（主操作 + 次操作） | 工具栏、操作区、提交栏、**单选择器、排序切换、步进器、按钮组** | — |
| `tab_nav` | 标签页切换条 | 标签导航、**状态标签页**、步骤条、分类切换 | 不要用 key_value 或 data_table 代替 |
| `media_grid` | 图片/视频占位网格 | 相册、图片上传、媒体展示 | — |
| `card_grid` | 卡片网格（图+文） | 商品卡片、推荐列表、内容流 | — |
| `tree_view` | 缩进层级节点 | 分类树、组织结构、文件夹 | — |
| `timeline` | 点-线时间轴 | **进度跟踪、物流跟踪、操作历史** | 不要用于数量步进器、按钮操作 |
| `text_block` | 纯文本段落 | 说明文字、空状态提示、通知内容 | 不要用于有操作性的组件 |

**选择原则**：LLM 必须根据**组件的实际业务用途**选择 render_as，而不是根据组件名称猜测。关键判断依据：

1. **组件的主要交互方式是什么？** — 点击按钮 → `action_bar`；填写多字段 → `input_form`；查看多行数据 → `data_table`
2. **单控件还是复合控件？** — 单个下拉/开关/按钮 → `action_bar`（不是 input_form）；多个输入字段 → `input_form`
3. **切换类组件一律用 `tab_nav`** — 状态标签页、步骤切换、分类 tab 都用 tab_nav，不用 key_value
4. **统计/图表类一律用 `bar_chart`** — 有"趋势/统计/分析/ROI/转化"的组件用 bar_chart，不用 input_form

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
| **信息密度** | 低~中 — 视觉层次清晰，但允许上下文聚合 | 高 — 紧凑表格、多列信息、数据密集 | 人多但低频 → 需要清晰视觉引导；人少但高频 → 需要一眼看到全貌 |
| **引导程度** | 强 — 步骤引导、空状态提示、操作确认 | 弱 — 假设用户懂业务，减少确认弹窗 | 用户不看说明书 → 界面即说明；专业用户被反复确认会烦 |
| **页面粒度** | 按用户意图聚合（见下方说明） | 粗 — 同页多功能，一个页面管理一个实体的全部操作 | 见下方「信息密度是连续光谱」 |
| **操作方式** | 显式 — 大按钮、明确 CTA、手势导航 | 隐式 — 行内编辑、右键菜单、键盘快捷键、批量操作 | 手指触控 → 需要大触控区域；鼠标键盘 → 精确操作，追求速度 |
| **容错机制** | 严格 — 不可逆操作多重确认、自动保存 | 宽松 — 信任用户判断，快速撤销而非反复确认 | 用户犯错成本高且不可预期 → 防错优先；专业用户犯错少且能自行恢复 → 效率优先 |

### 信息密度是连续光谱，不是二元开关

`screen_granularity` 不是"single_task_focus=永远不合并"和"multi_function_per_page=尽量合并"的二元选择。**信息密度是 0.0 到 1.0 的连续值**，LLM 必须对每个屏幕独立判断其合理密度。

**判断标准：用户在同一个意图下需要同时看到哪些信息？**

- 用户想"了解这个商品" → 商品图片 + 规格 + 价格 + 评价摘要 + 证据层 + 加购按钮 = **密度 0.6**，自然聚合在一个详情页
- 用户想"看我的订单怎么样了" → 订单信息 + 物流跟踪 + 退款入口 = **密度 0.5**
- 用户想"管理我的账号" → 头像 + 基本信息 + 订单快捷入口 + 宠物档案 + 积分 = **密度 0.4**
- 用户想"完成付款" → 极度聚焦，只有金额确认和支付按钮 = **密度 0.1**
- 后台管理员想"管理商品审核" → 异常队列 + 详情面板 + 规则配置 + 统计 = **密度 0.8**

**对 consumer 角色的合并规则**：不是"每个 task 独立一个屏幕"，而是"**同一用户意图**下的相关任务自然聚合"：
- 商品详情页聚合：查看商品 + 查看评价 + 查看问答 + 查看证据层 + 加入购物车 + 收藏 → 一个屏幕，用 Tab/折叠区域组织
- 个人中心聚合：个人信息 + 宠物档案入口 + 订单入口 + 积分 + 收货地址入口 → 一个枢纽页
- 但"浏览商品列表"和"搜索商品"仍然是同一屏幕的不同状态（搜索=在列表上执行过滤）

**LLM 对每个 consumer 屏幕必须判断**：这个屏幕的信息密度是多少（0.0-1.0）？密度 > 0.3 的屏幕允许聚合多个相关任务，用视觉层次（Tab/折叠/卡片）区分而非拆成独立页面。

**LLM 在设计每个屏幕时必须回答**：这个屏幕的用户是高频专业用户还是低频大众用户？据此选择信息密度和引导程度。不能用前端的低密度引导式设计套后台，也不能用后台的高密度效率式设计套前端。但也不能机械地把 consumer=低密度，因为"商品详情"天然就是中密度页面。

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
