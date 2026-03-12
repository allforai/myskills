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
version: "2.2.0"
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
| `layout_type` | 是 | LLM 自选布局（如 `single-column`、`sidebar-content`、`full-screen-immersive`、`card-stack`、`split-view`、`timeline` 等，不限于预定义列表） |
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
| `_pattern` | 自动 | 功能模式 ID 数组（Step 3.6 写入） |
| `_pattern_template` | 自动 | 推荐设计模板（Step 3.6 写入） |
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
  "empty": "空购物车插画 + '去逛逛'引导按钮",
  "loading": "骨架屏 + 下拉刷新",
  "error": "网络错误提示 + 重试按钮",
  "success": "操作成功 Toast 自动消失",
  "calculating": "积分抵扣实时计算中，金额区域显示加载动画",
  "stock_changed": "商品库存变化提醒横幅 + 自动更新数量",
  "expired": "超时未支付提醒 + 重新下单按钮"
}
```

**关键规则**：
- 4 个基础状态（empty/loading/error/success）是必须的，但 value 必须是针对该屏幕的具体交互描述，**不能所有屏幕都写一样的**
- **业务状态**（如 `calculating`、`stock_changed`、`processing_payment`、`pending_approval`、`connecting`、`disconnected`）必须根据该屏幕的业务场景添加，至少 1 个
- 包含审批/状态转换的屏幕（MG4/MG2-ST），必须包含流程状态（`pending`/`approved`/`rejected` 等）
- 包含支付的屏幕，必须包含支付状态（`processing_payment`/`payment_failed`/`payment_timeout`）
- 包含实时通讯的屏幕，必须包含连接状态（`connecting`/`connected`/`disconnected`）

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
| **CT4** | 卡片翻转 | progress, card-main, action-buttons | 闪卡/翻转/滑动决策（适用于复习、匹配） |
| **CT5** | 媒体播放 | player-screen, progress-bar, controls | 音视频播放器 |
| **CT6** | 图库 | gallery-grid, action-bar | 图片网格+灯箱预览 |
| **CT7** | 搜索结果 | search-bar, filter-chips, results-list, pagination | 搜索+筛选+结果列表 |
| **EC1** | 商品详情 | product-image, title-price, specs, features, action-bar | 产品/定价页+购买 CTA |
| **EC2** | 结账 | item-list, total, payment-options, action-bar | 购物车+支付选择 |
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
  .allforai/experience-map/journey-emotion-map.json   必须存在
  .allforai/product-map/task-inventory.json            必须存在
  .allforai/product-map/role-profiles.json             可选
  .allforai/product-map/business-flows.json            可选
  .allforai/product-map/view-objects.json              可选
  .allforai/product-map/entity-model.json              可选
  .allforai/product-concept/product-concept.json       可选

Step 1: 加载全部上游数据
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
| screen.interaction_type（从 infer_interaction_type） | `emotion_design`（情绪设计） |
| screen.data_fields（从 entity-model + view-objects） | `states`（界面状态） |
| screen.vo_ref（从 view-objects 匹配） | `layout_type`（布局类型） |
| screen.actions（从 CRUD 推断） | |
| screen.flow_context（从操作线顺序） | |
| screen 去重（同 task+role 复用） | |
| 独立/孤儿任务的额外操作线 | |
| _emotion_ref（从 journey-emotion 附加） | |

**骨架加载**：Step 2 中 LLM 读取骨架文件，在已有结构上填充创意字段，而非从零构建整个 JSON。

---

### Step 2：LLM 自由设计体验地图

LLM 加载 `experience-map-skeleton.json`，在骨架基础上填充创意字段。骨架已提供了完整的 operation_lines > nodes > screens 结构、data_fields、interaction_type、flow_context，LLM 聚焦于设计决策：

**LLM 在骨架上的工作**：
1. 填充 `name`：为每个界面命名（中文产品语言）
2. 填充 `description`：说明设计意图（2-3 句话，回答 D1+D4）
3. 填充 `components`：设计组件清单（每个含 type/purpose/behavior/data_source）
4. 填充 `interaction_pattern`：描述交互模式（1-2 句话）
5. 填充 `emotion_design`：基于 `_emotion_ref` 的情绪设计决策
6. 填充 `states`：empty/loading/error/success 状态设计
7. 填充 `layout_type`：选择布局方式
8. **审查并可调整** `interaction_type`：骨架的推断可能不是最优，LLM 可根据产品语义调整（但必须从渲染器支持列表选择）
9. **审查并可调整** `data_fields`：骨架从 entity-model 机械复制字段，LLM 必须以用户视角逐字段审查两个问题——**该不该出现**和**能不能编辑**：
   - **该不该出现**：该界面的用户需要看到/填写这个字段吗？系统自动生成的字段（如主键、时间戳、外键）不应出现在创建/编辑表单中；详情页也只保留对用户有意义的字段
   - **能不能编辑**：同一个字段在不同界面类型下可编辑性不同。骨架的 `input_widget` 是从字段元数据机械推断的，不区分界面语境。LLM 须根据业务语义判断：创建时可填但创建后不可改的字段（如订单类型、用户名）在编辑表单中应为 `readonly`；由系统计算/状态机驱动的字段（如状态、评分、进度）在任何表单中都不应让用户手动输入
10. **可合并/拆分 screens**：骨架按 1 task = 1 screen 生成，LLM 可根据设计判断合并多任务到一个界面或拆分复杂任务

**额外的设计思考**（超越骨架）：

1. **理解数据结构**：entity-model 告诉你每个界面需要展示什么字段、有哪些状态转换
2. **匹配情绪弧线**：journey-emotion 告诉你用户在每个节点的情绪，指导交互密度和反馈方式
3. **尊重平台差异**：
   - consumer (mobile-ios)：单手操作、竖屏、底部导航、手势交互、沉浸体验
   - professional (desktop-web)：大屏多列、鼠标键盘、侧边栏导航、批量操作、数据密集
4. **组件语义前提验证**：每个组件/筛选/排序/分类方式都隐含了对底层数据的假设（作用域、基数、更新来源、统计基础等）。设计时必须验证这些假设是否被当前屏幕的数据模型支撑 — 如果数据模型不满足组件的语义前提，该组件就不应出现
5. **创新界面**：product-concept 中的创新概念（如角色扮演、AI 即时生成）应该有独特的交互设计，不套用标准模板

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
BATCH_DESIGNS = {
    "S001": {
        "name": "...",
        "description": "...(≥40字，回答 D1+D4)...",
        "components": [...],  # 每个含 type/purpose/behavior/data_source
        "interaction_pattern": "...",
        "layout_type": "...",  # 根据该屏幕的业务场景选择，不默认 sidebar-content
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

**禁止的反模式**：
- ❌ `def get_states(platform, interaction_type)` — 模板函数，所有屏幕生成一样的状态
- ❌ `emotion_design = "简单的一句话"` — 字符串而非结构化对象
- ❌ 所有 desktop 屏幕都用 `sidebar-content`，所有 mobile 屏幕都用 `single-column`
- ❌ `description` 只有一句话重复屏幕名称

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
| layout_type 多样性 | 全部屏幕的 layout_type 不能只有 ≤ 3 种类型；dashboard 类（MG7）必须用 `dashboard` 而非 `sidebar-content` | 统计 layout_type 分布，检查特定类型匹配 |
| interaction_type 准确性 | 创建操作不应是 CT2（内容阅读），删除操作不应是 MG1（只读），充值/提现等提交操作不应是 MG1（只读） | 交叉检查 actions 语义与 interaction_type 是否矛盾 |
| components 非空 | 每个 screen 至少 2 个 components，且每个 component 有 type/purpose/behavior | 遍历检查 |
| actions 语义匹配 | actions 中不应出现与屏幕无关的操作（如查看页面出现"保存"） | LLM 判断 actions 与 screen 业务场景是否匹配 |

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
| 角色匹配 | 操作线中的屏幕角色一致 | 学习者操作线中混入管理员界面 |

**屏幕维度**：

| 检查项 | 合理标准 | 不合理信号 |
|--------|---------|-----------|
| 功能密度 | 每屏 1-3 个核心任务 | 单屏 > 5 个任务（功能堆叠）或 0 个任务（空壳屏幕） |
| 差异化 | 创新功能有独特交互 | AI 生成/角色扮演用普通表单（MG2-C）而非专用类型（SY2/CT2） |
| 模板-组件一致性 | interaction_type 渲染模板与 components 描述的交互形态匹配 | components 描述了图谱/可视化/画布，但 interaction_type 用了列表/详情/表格模板（如力导向图用 CT2 渲染成文章页） |
| 平台交互适配 | mobile 用触摸原生组件，desktop 用鼠标原生组件 | mobile 界面出现分页器（应为无限滚动）、右键菜单；desktop 出现滑动手势 |
| 平台差异 | mobile 和 desktop 布局明显不同 | desktop 界面也是单列竖屏布局 |
| 组件语义前提 | 每个组件隐含的数据假设必须被当前屏幕的数据模型支撑 | 组件预设的数据特征（作用域、基数、统计来源、更新频率）与屏幕实际数据不匹配 — 如组件需要多用户聚合统计但屏幕数据是单用户私有的，或组件需要实时流但数据是静态快照 |
| actions 相关性 | 操作与屏幕业务场景匹配 | "订阅方案"的 actions 引用"浏览场景包列表"等不相关任务 |

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
| S006 | interaction_type=CT3 非最佳匹配 | → CT2（对话内容） |
| S019 | 操作线 F001 内重复出现 | 删除重复引用 |

### 业务合理性
| 操作线 | 屏幕数 | 判断 | 备注 |
|--------|--------|------|------|
| 场景化学习链路 | 7 | 合理 | 核心流程完整 |
| 订阅付费链路 | 1 | ⚠ 不合理 | 缺少支付确认页 |

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

对匹配的 screen，写入 `_pattern` 和 `_pattern_template` 字段：

```json
{
  "id": "S005",
  "name": "订单管理",
  "_pattern": ["PT-CRUD", "PT-SEARCH"],
  "_pattern_template": "顶部操作栏+数据表格+顶部筛选栏",
  "_pattern_group": "orders-crud",
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

### 3. 平台差异不可忽略

consumer 角色和 professional 角色的界面必须在布局、导航、交互方式上有本质差异，不是换个宽度的同一套设计。
