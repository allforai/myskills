---
name: ui-design
description: >
  Use when the user wants to "generate UI design", "create UI spec", "design screens",
  "what should the UI look like", "UI style guide", "UI from product map",
  "design system recommendation", "UI 设计", "界面设计", "生成UI", "UI 规格",
  "从产品地图生成UI", "设计风格", "UI 预览", "界面风格",
  or wants to turn product map and screen map into visual design specifications.
  Requires product-map to have been run first. Optionally uses experience-map and product-concept.
version: "1.0.0"
---

# UI Design — UI 设计规格生成

> 产品地图说应该有什么，设计应该长什么样？

## 目标

以 `product-map`（以及可选的 `experience-map`、`product-concept`）为输入，结合用户选定的 UI 风格和实时检索的设计原则，输出两类产物：

1. **`ui-design-spec.md`** — 高层 UI 设计规格：每个界面的布局模式、配色语义、组件建议、交互状态
2. **按角色拆分的 HTML 预览** — 每个角色一个 HTML 文件，展示该角色可见的所有界面卡片；`index.html` 做总导航

---

## 定位

```
product-concept → product-map → experience-map → ui-design
（方向）          （任务）       （界面结构）  （视觉规格 + 预览）
```

**前提**：必须先运行 `product-map`。`experience-map` 不存在时自动运行生成体验地图。

### 新增输入通道（来自 experience-map）

| 输入 | 来源 | 用途 |
|------|------|------|
| `emotion_state` + `intensity` | experience-map 每个 node | 决定视觉层级、色彩情绪、动效强度 |
| `ux_intent` | experience-map 每个 node | 指导组件选择和布局策略 |
| `non_negotiable` | experience-map 每个 screen | 作为设计约束写入 spec |
| `continuity` | experience-map 每条 line | 指导转场动效和导航模式 |
| `quality_gate.issues` | interaction-gate.json | 标记需要特别处理的交互问题 |

---

## 快速开始

```
/ui-design            # 完整流程（风格选择 → 检索 → 生成规格 → 生成 HTML）
/ui-design refresh    # 清除决策缓存，重新选风格 + 完整重跑
```

## 增强协议（WebSearch + 4D+6V + XV）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：`”design system” + 行业词 + “case study” + 2025`、`”WCAG 2.2” + 组件类型 + “accessibility”`、`”dashboard UI” + “information density” + “best practices”`

**4D+6V 重点**：
- 读取 `task-inventory.json` 中的 `innovation_tasks` 字段，对 `innovation_task=true` 的界面标注 `innovation_ui: true`
- `source_refs` 指向 `adversarial-concepts.json` 的对应概念 ID（如 `IC001`）
- 规格附带设计决策理由；对高风险交互（删除、提交、权限）明确记录可访问性与失败反馈依据
- 创新概念 UI 规格必须体现跨领域参考（如"抖音无限滚动"、"游戏赛季制"）

**XV 交叉验证**（Step 4 生成设计规格后）：

| 验证点 | task_type | 发送内容 | 写入字段 |
|--------|-----------|----------|----------|
| 设计审查 | `design_review`→gpt | 设计规格摘要：配色系统 + 排版规范 + 关键界面布局 + 受众类型 | cross_model_review.design_issues |
| 视觉一致性 | `visual_consistency`→gemini | 设计规格摘要：各界面配色/圆角/间距参数 + 组件风格 + 状态设计 | cross_model_review.consistency_gaps |

自动写入：视觉层级问题（主操作不够突出、信息密度与受众不匹配、色彩语义冲突）、一致性缺陷（跨界面组件风格不统一、状态反馈模式不一致、间距/圆角参数偏差）。

## 尾段理论支持（可选增强）

为让 UI 产出从“风格偏好”升级为“可评审、可审计的设计决策”，可在现有流程叠加：

| 理论/框架 | 对应步骤 | 落地方式 |
|-----------|----------|----------|
| Design System / Design Tokens | Step 3/4 | 将配色、字号、间距、圆角参数化，保证多角色预览与后续实现一致 |
| Atomic Design | Step 4/5 | 将规格按原子-分子-组织拆分，避免界面规格仅停留在页面描述 |
| WCAG 可访问性（2.1/2.2） | Step 3/4 | 在颜色、排版、状态反馈中加入对比度与可达性约束 |
| Gestalt / 视觉层级原则 | Step 4 | 约束信息分组与主次层级，降低认知负荷，提升可扫读性 |

> 说明：此增强不替代用户风格选择；风格仍由 Step 2 明确决策。

---

## 全自动模式

**激活条件**（同时满足）：
1. `.allforai/product-concept/product-concept.json` 存在且含 `pipeline_preferences` 字段
2. 上下文含 `__orchestrator_auto: true`（由 `/product-design full` 编排器传入）

**未同时满足** → 保持标准交互模式（当前行为不变）。

**行为变化**：

| 步骤 | 标准模式 | 全自动模式 |
|------|----------|-----------|
| **Step 1 画像确认** | AskUserQuestion 确认 | 自动确认，记入 `pipeline-decisions.json`（`decision: "auto_confirmed"`） |
| **Step 2 风格选择** | AskUserQuestion 8 选 1 | 读 `pipeline_preferences.ui_style`：非 `"undecided"` → 直接使用预设风格，跳过 AskUserQuestion；`"undecided"` → **回退交互模式**（展示 8 种风格，用户选择） |
| **Step 3 设计原则确认** | AskUserQuestion 确认 | 自动确认（WebSearch 照常执行，搜索结果自动采纳） |
| **Step 4 规格确认** | AskUserQuestion 确认 | 自动确认 |
| **Step 5 预览确认** | AskUserQuestion 确认 | 自动确认 |
| **Step 5.5 Stitch 不可用** | AskUserQuestion 询问 | 自动降级到 Step 5.6（LLM 高保真预览） |

**安全护栏**（自动模式下仍然停下来问用户）：
- ERROR 级验证失败（无法推导任何界面、product-map 损坏）
- `ui_style = "undecided"` 时 Step 2 回退交互模式（风格选择不可自动推断）

---

## 工作流

```
前置检查：
  product-map.json 必须存在（否则终止）
  experience-map.json 必须（不存在则自动运行 experience-map 生成）
  product-concept.json 可选（提取定位/价值主张用于配色基调）
  ui-design-decisions.json 存在则加载历史决策

  Pattern Catalog（可选读取）：
    若 .allforai/design-pattern/pattern-catalog.json 存在，读取并作为设计约束使用：
    - _pattern_group 相同的界面 → 必须使用相同的组件布局模板
    - _pattern_template 字段 → 作为界面设计的首选方案参考
    不存在 → 跳过，按标准流程设计

  Behavioral Standards（可选读取）：
    若 .allforai/behavioral-standards/behavioral-standards.json 存在，读取并作为设计约束：
    - screen_behavioral_tags[screen_id]._behavioral_standards → 强制使用对应的标准方案
    - 例：BC-LOADING 标准为 skeleton → 所有界面的 loading 状态均使用骨架屏
    - 例：BC-DELETE-CONFIRM 标准为 modal_confirm → 所有 crud=D 操作使用模态弹窗确认
    不存在 → 跳过，各界面独立设计状态（向后兼容）

  Phase 2.8 — 加载创新概念清单（新增）：
    检查 .allforai/product-concept/adversarial-concepts.json：
      存在 → 加载 `concepts[]` 数组，标记 innovation_mode = "active"
      不存在 → innovation_mode = "none"
    检查 task-inventory.json 的 `innovation_tasks` 字段：
      存在 → 告知用户：「创新感知：active — 检测到 X 个创新任务」
      不存在 → innovation_mode = "none"
  ↓
Step 1: 产品画像推导
  读取 task-inventory + role-profiles + experience-map + innovation_tasks（前置检查已保证存在）
  推导：B端/C端、角色列表、各角色高频任务、界面总数
  向用户展示，确认
  ↓
Step 2: 风格选择（AskUserQuestion 单选）
  展示 8 种主流风格
  用户选定后，记录到 ui-design-decisions.json
  ↓
Step 3: 检索设计原则（WebSearch）
  根据所选风格搜索官方设计系统文档和核心原则文章
  提取：配色逻辑、排版规范、组件偏好、交互原则
  摘要展示，用户确认后才应用
  ↓
Step 4: 生成设计规格（ui-design-spec.md）
  逐界面/推导界面输出高层规格
  ↓
Step 5: 生成多角色 HTML 线框预览
  index.html + 每角色一个 ui-role-{角色名}.html
  ↓
Step 5.6: LLM 高保真 HTML 预览（Stitch 不可用时自动执行）
  tokens.json → CSS 变量 → Tailwind + 真实内容 → 高保真页面
```

> **强制规则**：Step 2「风格选择」不可跳过。即使存在历史决策，也必须向用户展示当前风格并请求确认（可沿用历史风格或改选），不得静默默认。

---

## Step 1：产品画像推导

**数据加载**：
- `task-inventory.json` — 获取所有任务、频次、角色归属
- `role-profiles.json` — 获取角色列表和 audience_type（consumer/professional）
- `experience-map.json`（前置检查已保证存在）— 获取界面列表和 audience_type
- `product-concept.json`（可选）— 提取 value_proposition 用于文案基调

**输出画像**：
- 受众类型：consumer / professional / 混合
- 角色列表：每个角色的名称、audience_type、高频任务 Top 3
- 界面数：来自 experience-map 或估算值（高频任务数 × 1.5，取整）

**用户确认**：展示推导结果，确认无误后进入 Step 2。

---

## Step 2：风格选择题

使用 AskUserQuestion 展示 8 种风格，每种附带描述和代表产品：

| 编号 | 风格名 | 代表产品 | 视觉特点 |
|------|--------|---------|---------|
| 1 | Material Design 3 | Google Workspace、Android | 动效丰富、层级感强、高饱和色彩、圆角卡片 |
| 2 | Apple HIG | iOS 系统、Notion、Linear | 大量留白、极简、系统字体、磨砂玻璃导航栏 |
| 3 | Fluent Design | Microsoft 365、VS Code | 亚克力毛玻璃、深色/浅色模式、流动感动效 |
| 4 | Flat / Minimal | Linear、Vercel、Loom | 无阴影、高对比度、单色调、信息密度高 |
| 5 | Glassmorphism | macOS widgets、部分仪表盘 | 毛玻璃背景、渐变叠加、半透明卡片 |
| 6 | Ant Design 企业风 | 阿里云、飞书后台、钉钉 | 蓝灰色系、表格/列表导向、高信息密度 |
| 7 | Shadcn / Tailwind 现代感 | Vercel、Raycast、Resend | 无障碍优先、深色模式原生支持、极简组件边框 |
| 8 | 品牌定制风 | Stripe、Airbnb、Figma | 强品牌主色、自定义字体、独特视觉语言 |

选定后记录：
```json
{ "step": "Step 2", "item_id": "style", "decision": "confirmed", "value": "Flat / Minimal", "decided_at": "..." }
```

**不可省略要求**：
- 不允许自动使用默认风格（例如固定 Flat / Minimal）
- 不允许因历史缓存而跳过用户确认
- 若用户未明确选择，本次流程停留在 Step 2，不进入 Step 3

---

## Step 3：检索设计原则

**搜索策略**（按所选风格）：

| 风格 | WebSearch 关键词 |
|------|----------------|
| Material Design 3 | "Material Design 3 guidelines color typography components 2025" |
| Apple HIG | "Apple Human Interface Guidelines iOS design principles 2025" |
| Fluent Design | "Microsoft Fluent Design System principles components 2025" |
| Flat / Minimal | "flat UI design principles minimalist web design best practices" |
| Glassmorphism | "glassmorphism design system CSS best practices accessibility" |
| Ant Design 企业风 | "Ant Design 5 design values enterprise UI guidelines" |
| Shadcn / Tailwind | "shadcn/ui design principles Tailwind CSS component patterns 2025" |
| 品牌定制风 | "brand-driven UI design system Stripe Airbnb design language" |

**提取内容**：
- 主色调推荐（色相范围、亮度规范）
- 排版规范（字号层级：标题/正文/辅助文字）
- 组件偏好（按钮风格、卡片风格、表单风格）
- 间距系统（4px / 8px grid）
- 核心设计原则（3-5 条）

**摘要展示格式**：
```
检索到的设计原则摘要：
来源：{URL}

配色：主色 {色相范围}，背景 {颜色}，功能色（成功/警告/错误）{举例}
排版：标题 {px}/正文 {px}/辅助 {px}，字体推荐 {字体名}
组件：{按钮风格描述}，{卡片风格描述}
间距：{间距系统说明}
原则：{3-5 条核心原则}

确认后将应用到 Step 4 规格生成。
```

---

## Step 4：生成设计规格

**输出文件**：`.allforai/ui-design/ui-design-spec.md`

**交互类型驱动**：读取 `experience-map.json` 中每个 screen 的 `interaction_type` 字段（由 experience-map Step 1 推断，类型定义见 `docs/interaction-types.md`），按类型选择推荐布局模式：

| 交互类型 | 推荐布局模式 | 关键区域 |
|---------|------------|---------|
| `MG1` (只读列表) | 侧边导航 + 表格区（筛选栏 + 数据表 + 分页） | 筛选条件区、数据表格、分页器 |
| `MG2` (全功能 CRUD) | 侧边导航 + 表格区 + 工具栏 | 新建按钮、操作列（编辑/删除）、表单弹窗或独立页 |
| `MG3` (状态机列表) | 侧边导航 + 表格区（状态筛选 Tab） | 状态 Tab、条件操作列、状态确认弹窗 |
| `MG4` (审批流) | 列表页 + 审核详情页 | 待审筛选、信息展示卡、审核操作面板 |
| `MG5` (主从详情) | 头部信息区 + Tab 切换子表 | 主实体信息、关键指标、子实体 Tab 列表 |
| `MG6` (树形 CRUD) | 左右分栏（左树右编辑） | 树形组件、编辑面板/弹窗 |
| `MG7` (仪表盘) | 网格布局（统计卡 + 图表区） | Statistic 卡片、图表、待办快捷入口 |
| `MG8` (配置表单) | 居中单列表单 | 分组表单区、固定底部保存按钮 |
| CT/EC/WK/RT/SB/SY/TU 类型 | 见 `docs/interaction-types.md` 平台矩阵 | 各类型布局指引详见该文档 |

> 注：v2 交互类型体系共 37 种（MG1-8、CT1-6、EC1-4、WK1-5、RT1-4、SB1-4、SY1-3、TU1-3），完整定义见 `${CLAUDE_PLUGIN_ROOT}/docs/interaction-types.md`。

**组合类型处理**：`interaction_type` 为数组时，主类型决定页面整体布局，次类型决定内嵌交互区域。如 `["MG5", "MG3"]` → 整体用 MG5 布局，操作区域按 MG3 模式设计。

**内容结构**：

```markdown
# UI 设计规格

> 风格：{风格名}
> 设计原则来源：{URL}
> 生成时间：{时间}

## 创新概念 UI 规格（若 innovation_mode=active）

（按创新概念分组，每个概念一节，通用描述不绑定特定行业）

### IC001: {创新概念名}

**创新方向**：{去课程化学习/赛季制/紧急速成等}

**跨领域参考**：
- {参考 1}：{如"抖音无限滚动"}
- {参考 2}：{如"游戏赛季制"}

**关键特性**：
- {特性 1}：{如"打开 APP 直接开始，无首页"}
- {特性 2}：{如"3 分钟微场景"}
- {特性 3}：{如"算法推荐下一个"}

**视觉设计要点**：
- 布局模式：{如"全屏沉浸式，隐藏导航栏"}
- 交互组件：{如"右侧滑动按钮，类似抖音点赞"}
- 状态反馈：{如"底部进度条显示完成度"}
- 配色语义：{如"动态配色匹配场景主题"}

**保护级别**：core/defensible

**设计来源**：adversarial-concepts.json → IC001

---

## 设计语言基础

### 配色系统
- 主色：{色值范围描述}
- 辅色：{色值范围描述}
- 功能色：成功 {描述} · 警告 {描述} · 错误 {描述}
- 背景：{描述}

### 排版
- 标题（H1/H2/H3）：{字号}/{字重}
- 正文：{字号}/{行高}
- 辅助文字：{字号}/{颜色说明}
- 字体推荐：{字体名}

### 推荐组件库
- 首选：{库名} — {理由}
- 备选：{库名} — {适用场景}

### 响应式策略

断点定义（从 product-concept 推断 platform_type）：
- mobile_app → 不需要断点（原生布局系统）
- web_app / responsive →
  | 断点 | 宽度 | 布局变化 |
  |------|------|----------|
  | sm   | <640px  | 单列，BottomNav，全宽卡片 |
  | md   | 640-1024px | 双列网格，侧边导航可折叠 |
  | lg   | >1024px | 三列网格，固定侧边栏 |

容器策略：max-width: 1280px, 居中
组件适配规则：
- Card grid: 1col(sm) → 2col(md) → 3-4col(lg)
- Navigation: BottomNav(sm) → SideNav(md+)
- Table: 横滚(sm) → 完整显示(md+)

### 间距标度

基础单位：4px
标度：
| token | 值 | 用途 |
|-------|-----|------|
| --space-1 | 4px | 图标与文字间距 |
| --space-2 | 8px | 组件内边距（紧凑） |
| --space-3 | 12px | 组件内边距（默认） |
| --space-4 | 16px | 卡片内边距、列表项间距 |
| --space-6 | 24px | 区块间距 |
| --space-8 | 32px | 页面区域间距 |
| --space-12 | 48px | 大区块分隔 |

### 排版标度

| token | 字号 | 行高 | 字重 | 字间距 | 用途 |
|-------|------|------|------|--------|------|
| --text-display | 36px | 1.2 | 700 | -0.5px | 首屏标题 |
| --text-h1 | 28px | 1.3 | 700 | -0.25px | 页面标题 |
| --text-h2 | 22px | 1.35 | 600 | 0 | 区块标题 |
| --text-h3 | 18px | 1.4 | 600 | 0 | 卡片标题 |
| --text-body | 16px | 1.5 | 400 | 0 | 正文 |
| --text-body-sm | 14px | 1.45 | 400 | 0.1px | 辅助文字 |
| --text-caption | 12px | 1.4 | 400 | 0.2px | 标注、时间戳 |

### 动效规范

| token | 值 | 用途 |
|-------|-----|------|
| --duration-fast | 150ms | 按钮反馈、开关切换 |
| --duration-normal | 250ms | 页面转场、模态弹出 |
| --duration-slow | 400ms | 复杂动画、展开收起 |
| --easing-standard | cubic-bezier(0.4, 0, 0.2, 1) | 大部分转场 |
| --easing-decelerate | cubic-bezier(0, 0, 0.2, 1) | 进入屏幕 |
| --easing-accelerate | cubic-bezier(0.4, 0, 1, 1) | 离开屏幕 |

原则：
- prefers-reduced-motion 时所有动画降为 0ms
- 交互反馈（按钮、开关）使用 fast
- 布局变化（展开、折叠、页面切换）使用 normal
- 首次加载动画使用 slow

### 图标规范

图标库选型（根据 ui_style 推断）：
| ui_style | 推荐图标库 | 备选 |
|----------|-----------|------|
| material-design-3 | Material Symbols | Phosphor |
| apple-hig | SF Symbols (iOS) / Lucide (Web) | Heroicons |
| fluent-design | Fluent UI Icons | — |
| ant-design | Ant Design Icons | — |
| shadcn-tailwind | Lucide | Radix Icons |
| 其他 | Lucide（通用性最好） | Phosphor |

尺寸标度：
| 用途 | 尺寸 | 示例 |
|------|------|------|
| 内联（按钮图标） | 16px / 20px | 编辑、删除按钮 |
| 标准（列表、导航） | 24px | 导航栏图标 |
| 特征（空状态、引导） | 48px / 64px | 空列表提示图 |

### 主题变体

默认生成 light theme token。dark theme 通过语义映射自动派生：
| 语义 token | light 值 | dark 值（自动派生规则） |
|------------|----------|------------------------|
| --surface | #FFFFFF | #1C1B1F |
| --on-surface | #1C1B1F | #E6E1E5 |
| --surface-container | #F3EDF7 | #2B2930 |
| --primary | 保持不变 | 保持不变 |
| --on-primary | 保持不变 | 保持不变 |
| --elevation-1 | shadow | lighter surface-container |

派生规则：
- 背景色：反转亮度（HSL L 通道取反）
- 前景色：反转亮度
- 品牌色（primary/secondary）：保持不变
- 阴影：dark 模式下用 surface 层级差异替代阴影

---

## 界面规格

（按角色分组，每个界面一节）

### {角色名} 的界面

#### {界面名}（{audience_type}）[类型: {interaction_type}]

**界面目的**：{一句话}

**交互类型**：{interaction_type}（布局模式由交互类型驱动，见上方对照表）

**布局模式**：{由 interaction_type 决定的推荐布局}

**主要区域划分**：
- 顶部：{导航栏/页头描述}
- 主体：{主要内容区描述}
- 操作区：{按钮/表单位置描述}

**关键状态设计**：
- 空态：{引导文案/插图建议}
- 加载中：{骨架屏/spinner 建议}
- 错误：{错误提示位置/样式建议}
- 成功反馈：{toast/inline/页面跳转}

**受众提示**：{针对 consumer/professional 的特殊设计要点}
```

每个界面 section 新增字段：
- **Emotion Context**: emotion_state (intensity/10) → 设计基调
- **Interaction Intent**: ux_intent → 交互意图
- **Non-negotiable**: 不可妥协设计约束
- **Quality Gate**: 质量门禁问题
- **Transition**: 转场方向和动效
- **Continuity Constraint**: 操作线连贯性约束

---

## Step 4.5：Pattern Consistency Check（仅当 pattern-catalog.json 存在时触发）

扫描本次已生成的所有界面设计：

**检测 1**: 同 `_pattern_group` 的界面是否使用了一致的主布局（顶部栏/侧边栏/主内容区比例相同）
  → 不一致 → 自动对齐到该 group 中最先生成的界面的布局
  → 记录调整: `pattern_alignment: [screen_id → aligned to screen_id]`

**检测 2**: 同一模式类型（如 PT-CRUD）的界面是否使用了相同的操作按钮位置（新建/编辑/删除）
  → 不一致 → 自动统一到推荐位置（右上角主操作 + 行内次操作）
  → 记录调整同上

**检测 3**: 同一审批流（PT-APPROVAL）的状态标签颜色体系是否统一（待审=黄/通过=绿/拒绝=红）
  → 不一致 → 标记为 WARNING，在 ui-design-spec.md 中备注「需统一颜色体系」

**检测 4**: 同一 `interaction_type` 的界面布局一致性检查
  检查所有 interaction_type 相同的界面：
    → 布局模式是否一致（如所有 `MG1` 都使用 侧边导航+表格区）
    → 关键区域划分是否一致（如所有 `MG2` 的新建按钮位置统一）
    → 不一致 → 自动对齐到该类型的推荐布局（见 `docs/interaction-types.md`）
    → 记录调整同上

**检测 5**: 行为规范合规检查（仅当 behavioral-standards.json 存在时触发）
  对每个有 `_behavioral_standards` 标签的界面：
    检查生成的设计是否匹配标准方案（如 BC-LOADING 标准为 skeleton，但设计中写了 spinner → 不匹配）
    不匹配 → `BEHAVIORAL_DRIFT` 告警，记录到模式一致性记录中
    匹配 → 无操作

结果追加到 ui-design-spec.md 末尾的「模式一致性记录」章节：

```markdown
## 模式一致性记录

| Pattern Group | 对齐项目 | 调整说明 |
|--------------|---------|---------|
| orders-crud | 操作按钮位置 | 统一到右上角主操作 |
| approval-flows | 状态标签颜色 | ⚠ 需在组件库中统一 |
```

不阻塞，自动继续输出最终 ui-design-spec.md。

---

## Step 5：生成多角色 HTML 预览

### 文件结构

```
.allforai/ui-design/preview/
├── index.html                   # 总导航
├── ui-role-{角色1名称}.html
├── ui-role-{角色2名称}.html
└── ...
```

### index.html 内容规范

- 纯 HTML + 内联 CSS，无外部依赖
- 顶部：产品名称 + 选用风格标签
- 主体：角色卡片列表（每张卡片：角色名、可见界面数、Top 3 高频任务）
- 点击卡片打开对应 `ui-role-{角色名}.html`（相对路径链接）
- 配色匹配所选风格

### `ui-role-{角色名}.html` 内容规范

- 纯 HTML + 内联 CSS，无外部依赖，直接浏览器打开
- 顶部：面包屑导航（产品名 > 角色名）+ 返回 index.html 链接
- 界面按模块分组，模块标题分隔
- 每个界面一张卡片，卡片包含：
  - 卡片头：界面名 + audience_type 标签（consumer/professional）
  - 主要操作区骨架：列出主要按钮标签（匹配风格配色）
  - 三态骨架行：「正常」「空态」「错误」状态简短描述
  - 底部：关联任务数量
- 配色和圆角、阴影匹配所选风格

### HTML 生成方法

直接用 Write 工具逐文件写入完整 HTML 字符串。不使用 Python 脚本，避免执行环境依赖。

风格对应 CSS 变量速查（Step 3 检索后确认）：

| 风格 | 主色 | 背景 | 圆角 | 阴影 |
|------|------|------|------|------|
| Material Design 3 | #6750A4 | #FFFBFE | 12px | elevation-2 |
| Apple HIG | #007AFF | #F5F5F7 | 10px | 0 1px 3px rgba(0,0,0,.1) |
| Fluent Design | #0078D4 | #F3F3F3 | 4px | 0 2px 8px rgba(0,0,0,.14) |
| Flat / Minimal | #111827 | #FFFFFF | 4px | none |
| Glassmorphism | #6366F1 | linear-gradient(135deg,#667eea,#764ba2) | 16px | glass |
| Ant Design 企业风 | #1677FF | #F0F2F5 | 6px | 0 1px 2px rgba(0,0,0,.08) |
| Shadcn / Tailwind | #18181B | #FAFAFA | 6px | 0 1px 3px rgba(0,0,0,.05) |
| 品牌定制风 | 由 Step 3 检索确定 | 同上 | 同上 | 同上 |

---

### Step 5.3：组件规格生成（始终执行）

运行组件分析脚本：
```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_ui_components.py <BASE> --mode auto
```

输出：`ui-design/component-spec.json`
- 共享组件识别（跨屏幕复用模式）
- 交互原语关联（interaction_type → behavioral primitives）
- 组件变体推断（size/state）
- a11y 规格标注（按组件类型自动注入）
- 屏幕→组件映射

**此步骤不依赖任何外部服务，始终执行。**
component-spec.json 是 dev-forge 的核心输入，用于生成共享组件规格、注入 a11y、关联交互原语实现方案。

---

### Step 5.5：Stitch 视觉生成（条件执行）

**跳过条件**：`pipeline_preferences.stitch_ui ≠ true`

**补充入口**：如果 `stitch_ui` 字段不存在（用户单独跑了 /product-concept）
且 Stitch MCP 工具可用 → 主动询问是否启用，写入 pipeline_preferences

**执行流程**：

1. 运行 prompt 构建脚本：
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_ui_stitch.py <BASE> --mode auto
   ```
   输出：`ui-design/stitch-prompts.json`（最多 10 个屏幕的结构化 prompt）

2. 检测 Stitch MCP 可用性：
   - 检查 MCP 工具 `mcp__plugin_product-design_stitch__create_project` 是否可用
   - **不可用 → 自动降级到 Step 5.6 LLM 高保真预览**（零外部依赖，Tailwind + tokens.json 驱动，跨屏一致性由代码保证）。同时输出提示：

     ```
     Stitch 未就绪，自动使用 LLM 高保真预览生成视觉稿。
     如需 Stitch 可交互原型，运行 /setup 配置后重新执行 /ui-design。
     ```

     → 跳转 Step 5.6

3a. **可用** → 执行 Stitch 两阶段生成流程：

   **阶段 A：锚点屏生成**
   i.    调用 `create_project(title="产品名-ui-design")` → 获得 projectId
   ii.   从 stitch-prompts.json 读取数据：
         - `anchor_screen_id` — 锚点屏 ID（如 `"S001"`）
         - `screens` 数组 — 每项含 `screen_id`、`screen_name`、`prompt`、`generation_order`
         - 锚点屏 = `screens` 中 `screen_id == anchor_screen_id` 的项
   iii.  调用 `generate_screen_from_text(projectId, anchor_prompt, deviceType)`
         - `deviceType` 取自 stitch-prompts.json 的 `device_type` 字段
         - 此屏幕建立整个项目的视觉语言
         - 注意：可能需要几分钟，不要重试
   iv.   获取锚点屏结果：
         - `get_screen_code(projectId, screenId)` → HTML
         - `get_screen_image(projectId, screenId)` → 截图
   v.    写入 `ui-design/stitch/{screen_id}.html` 并记录 stitch-index.json

   **阶段 B：后续屏幕生成（引用锚点）**
   vi.   对 stitch-prompts.json 的 `screens` 数组中 `screen_id != anchor_screen_id` 的项，按 `generation_order` 逐个生成：
         - 每个项的 `prompt` 已包含 component_vocabulary + 锚点屏引用指令
         - 调用 `generate_screen_from_text(projectId, prompt, deviceType)`
         - 同一 projectId 下生成，Stitch 自动维持项目级一致性
   vii.  逐个获取 HTML + 截图，写入 `ui-design/stitch/{screen_id}.html`

   **阶段 C：一致性检查与修正**
   viii. 对所有生成的 HTML 做快速一致性检查：
         - 比较各屏幕中 component_vocabulary 引用组件的 CSS 类名/结构
         - 如果发现明显偏差（如 ProductCard 在不同屏幕结构不同）：
           调用 `edit_screens(projectId, screenId, "Make the ProductCard
           component match the style from screen [锚点屏的 screen_name]:
           same border-radius, same shadow, same padding, same image ratio")`
         - 重新获取修正后的 HTML
   ix.   最终更新 `ui-design/stitch-index.json`，增加一致性检查结果：
         `consistency_check: { passed: true/false, corrections: [...] }`

3b. **用户已确认跳过** → 仅输出 prompts，展示手动使用说明：
   ```
   已跳过 Stitch 视觉稿生成（用户确认），已生成 stitch-prompts.json。
   后续使用：
   1. 运行 /setup 配置 Stitch（一次性 Google OAuth）
   2. 重新运行 /ui-design，将自动调用 Stitch 生成视觉稿
   3. 或手动访问 stitch.withgoogle.com 粘贴 prompt 生成
   ```

**输出文件**：
  - `ui-design/component-spec.json`（Step 5.3 始终生成，通用）
  - `ui-design/stitch-prompts.json`（Step 5.5 始终生成）
  - `ui-design/stitch/`（Stitch MCP 可用时）
  - `ui-design/stitch-index.json`（Stitch MCP 可用时）

---

### Step 5.6：LLM 高保真 HTML 预览（条件执行）

> 用 Claude 直接生成接近真实 UI 的 HTML 页面。与 Step 5 线框预览的区别：线框是固定模板拼接的骨架卡片；高保真预览是 LLM 按设计规格生成的完整页面布局，视觉效果接近成品 UI。

**触发条件**（满足任一）：
- Step 5.5 检测到 Stitch 不可用（自动降级，不停顿）
- Stitch 可用但用户额外要求也生成 LLM 预览（两者可并存）

**输出目录**：

```
.allforai/ui-design/hifi-preview/
├── _tokens.css              # 从 tokens.json 自动生成的 CSS 变量（所有页面共享）
├── _design-system.html      # 设计系统参考页（所有共享组件的样式定义）
├── {screen-id}.html         # 每个屏幕一个独立页面
└── index.html               # 导航页（链接到所有屏幕）
```

**执行流程**：

#### Phase A：生成共享设计基础

**A1. 生成 `_tokens.css`**（确定性，不需要 LLM）

从 `tokens.json` 机械转换为 CSS custom properties：

```css
:root {
  /* Color */
  --color-primary: #1976D2;
  --color-on-primary: #FFFFFF;
  --color-surface: #FFFFFF;
  --color-on-surface: #1C1B1F;
  --color-error: #B3261E;
  --color-success: #2E7D32;
  --color-warning: #ED6C02;
  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  /* Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 16px;
  /* Typography */
  --text-h1: 28px;
  --text-body: 16px;
  --text-caption: 12px;
  --font-family: 'Inter', system-ui, sans-serif;
  /* Shadow */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  /* Duration */
  --duration-fast: 150ms;
  --duration-normal: 250ms;
}
```

**A2. 生成 `_design-system.html`**（LLM 生成）

这是**锚点页面** — 定义所有共享组件的视觉样式。LLM 根据以下输入生成：

输入：
- `_tokens.css`（CSS 变量）
- `component-spec.json`（共享组件清单 + 变体）
- `ui-design-spec.md`「设计语言基础」章节（配色、排版、组件偏好）
- 所选风格名称

生成要求：
- 单文件 HTML，`<head>` 内引入 Tailwind CDN + `_tokens.css`
- 展示所有共享组件的实际渲染效果：Button（primary/secondary/danger × default/hover/disabled）、Card、Input、Table Row、Badge、Modal、Toast、Navigation 等
- **所有颜色/间距/圆角/字号必须引用 `var(--xxx)`，禁止硬编码值**
- 组件样式使用 Tailwind utility classes + CSS 变量覆盖
- 每个组件附标注：组件名 + 使用场景

此页面的双重作用：
1. 作为设计系统文档供团队参考
2. 作为后续屏幕生成的**视觉锚点**（LLM 生成后续屏幕时引用此页面的组件样式）

#### Phase B：逐屏生成高保真页面

**屏幕选择**：从 `component-spec.json` 或 `experience-map.json` 中选取屏幕，优先级：
1. `stitch-prompts.json` 存在 → 使用其 `screens` 列表（已排好优先级，最多 10 个）
2. 不存在 → 按 interaction_type 权重排序，取 Top 10

**生成方式**：使用 Agent 工具并行生成（每屏一个 Agent，单条消息发出所有 Agent 调用）。

每个 Agent 的 prompt 模板：

```
你是 UI 设计预览生成器。

任务：为屏幕「{screen_name}」生成一个高保真的单文件 HTML 预览页面。

## 设计系统（必须严格遵循）

{_tokens.css 内容}

## 屏幕规格

- 屏幕 ID: {screen_id}
- 屏幕名称: {screen_name}
- 交互类型: {interaction_type}
- 角色: {role}
- 受众类型: {audience_type}

### 布局规格（来自 ui-design-spec.md）
{该屏幕在 ui-design-spec.md 中的完整规格段落}

### 组件清单（来自 component-spec.json）
{该屏幕关联的组件列表 + 变体}

### 情绪上下文（来自 experience-map）
- emotion_state: {emotion_state}
- intensity: {intensity}/10
- ux_intent: {ux_intent}

### 内容填充（来自 task-inventory）
{该屏幕关联的任务名称列表，用作菜单项/表格行/卡片标题等真实内容}

## 设计系统参考

{_design-system.html 中该屏幕用到的组件的 HTML 片段}

## 生成规则

1. 单文件 HTML，<head> 引入：
   - <link href="https://cdn.jsdelivr.net/npm/tailwindcss@3/dist/tailwind.min.css" rel="stylesheet">
   - <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
   - <style> 块内嵌 _tokens.css 的全部 CSS 变量
2. 所有颜色/间距/圆角/字号使用 CSS 变量（var(--xxx)），禁止硬编码
3. 使用 Tailwind utility + style="xxx: var(--xxx)" 混合写法
4. 填充真实业务内容（从任务名称派生），不使用 Lorem ipsum
5. 包含关键状态：正常态为主，空态和加载态用注释标注
6. 响应式：适配桌面视口（>1024px），移动端合理降级
7. 顶部固定导航栏包含：返回 index.html 链接 + 屏幕名称 + 角色标签
8. 底部注脚：「设计预览 · {style_name} · 生成时间」

写入路径: .allforai/ui-design/hifi-preview/{screen_id}.html
```

#### Phase C：生成导航页 + 一致性校验

**C1. 生成 `index.html`**

导航页面，链接到所有已生成的屏幕页面。按角色分组，每组显示：角色名 + 屏幕缩略信息（名称 + interaction_type 标签）。

**C2. 一致性校验**（自动，不停顿）

Read 所有生成的 HTML 文件，检查：
- [ ] 所有文件是否引用了相同的 CSS 变量集（`_tokens.css` 内容一致）
- [ ] 导航栏结构是否统一（高度、布局、返回链接）
- [ ] 主色调是否一致（搜索 `var(--color-primary)` 出现次数，确认无硬编码替代）
- [ ] 字号层级是否一致（`var(--text-h1)` / `var(--text-body)` 使用正确）

不一致项 → 自动修正（Edit 替换硬编码值为 CSS 变量引用），记录修正日志。

**输出进度**：

```
Step 5.6 ✓ LLM 高保真预览
  设计系统参考: _design-system.html（{N} 个共享组件）
  屏幕页面: {N} 个（{role1}: {n1}, {role2}: {n2}）
  一致性校验: {pass/N 项已修正}
  预览入口: .allforai/ui-design/hifi-preview/index.html
```

---

## 预置脚本（优先使用）

检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_ui_design.py` 是否存在：
- **存在** → `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_ui_design.py <BASE> --mode auto [--style material-design-3|ios-human-interface]`
- **不存在** → 回退到 LLM 生成脚本（向后兼容）

预置脚本保证 schema 一致性和零语法错误。支持 `--style` 参数指定风格（默认读取 `pipeline_preferences.ui_style`）。

---

## 输出文件结构

```
.allforai/ui-design/
├── ui-design-spec.md               # 高层设计规格（含 micro-interaction 规格表）
├── ui-design-spec.json             # 设计规格（机器可读）
├── ui-design-decisions.json        # 用户决策日志
├── tokens.json                     # 设计令牌单一来源（配色、间距、圆角、排版）
├── micro-interactions.json         # 微交互规格（按屏幕，含情绪对齐）
├── preview/                        # 线框预览（Step 5，始终生成）
│   ├── index.html
│   ├── ui-role-{角色1}.html
│   └── ...
└── hifi-preview/                   # 高保真预览（Step 5.6，Stitch 不可用时自动生成）
    ├── _tokens.css                 # tokens.json → CSS 变量（所有页面共享）
    ├── _design-system.html         # 共享组件视觉参考（锚点页面）
    ├── {screen-id}.html            # 每屏一个高保真 HTML 页面
    └── index.html                  # 导航页
```

### tokens.json (Design Token Single Source)

从所选风格自动导出的设计令牌，供 dev-forge project-scaffold 消费：

- `color` — 配色系统（primary, secondary, surface, error 等）
- `spacing` — 间距系统（4px 基准 + 标度）
- `radius` — 圆角（sm/md/lg）
- `typography` — 排版（display/headline/title/body/label）
- `font`, `shadow`, `style_name`

下游 scaffold 读取 tokens.json 自动生成框架配置（Tailwind theme / CSS variables / Flutter theme），避免手动复制导致的令牌漂移。

### micro-interactions.json

基于 emotion_intensity 自动推导的微交互规格：

| 情绪强度 | 层级 | 动画 | 时长 | 触觉反馈 |
|---------|------|------|------|---------|
| 1-3 | calm | fade | 200ms | none |
| 4-6 | moderate | slide-fade | 250ms | light |
| 7-10 | intense | scale-bounce | 300ms | impact-medium |

特殊覆盖：CRUD "C" 成功 → scale-bounce + impact-medium；CRUD "D" 错误 → shake + notification-error；CUD 异步操作 → pulse loading 反馈。

### JSON 对应件

同步生成 `ui-design-spec.json`，供下游技能（design-audit、design-to-spec、product-verify）直接解析：

```json
{
  "generated_at": "ISO8601",
  "style": "Flat / Minimal",
  "style_source": "URL",
  "design_tokens": {
    "colors": { "primary": "#111827", "background": "#FFFFFF", "success": "...", "warning": "...", "error": "..." },
    "typography": { "h1": "28px/700", "h2": "22px/600", "body": "14px/400", "caption": "12px/400" },
    "spacing": "8px grid",
    "border_radius": "4px"
  },
  "screens": [
    {
      "id": "S-05",
      "name": "订单管理",
      "role": "管理员",
      "audience_type": "professional",
      "interaction_type": "MG3",
      "layout": "侧边导航+内容区",
      "sections": ["顶部操作栏", "数据表格", "分页器"],
      "states": { "empty": "引导文案", "loading": "骨架屏", "error": "toast 提示" },
      "task_refs": ["T-12", "T-13"],
      "innovation_ui": false,
      "_pattern": ["PT-CRUD"]
    }
  ],
  "pattern_alignment": []
}
```

---

## 防御性规范

> 通用模式定义见 `docs/defensive-patterns.md`，以下为本技能的具体应用。

### 加载校验
- **`ui-design-decisions.json`**：加载时用 `python -m json.tool` 验证 JSON 合法性。解析失败 → 检查 `.bak` → 提示恢复或重新运行 `/ui-design refresh`。
- **`product-map.json` / `task-inventory.json`**：前置加载时验证 JSON 合法性。解析失败 → 提示用户重新运行 `/product-map`，终止执行。

### 零结果处理
- **无 experience-map 且无高/中频任务**：⚠ 明确告知「无法推导界面列表 — experience-map 不存在，且 task-inventory 中无高/中频任务可用于推导界面。请先运行 /experience-map 或 /product-map 补充任务频次」，**终止执行**（不生成空规格）。
- **Step 1 推导 0 界面**：同上处理。
- **Step 3 搜索 0 设计原则**：若搜索正常但无有用结果 → 告知用户，提供选项：(a) 使用所选风格的默认 CSS 变量 (b) 用户手动提供设计参考。

### 规模自适应
- **阈值**：以界面数为计量对象（来自 experience-map 或推导数量）。small ≤15 / medium 16–40 / large >40。
- **small**（≤15 界面）：逐界面生成设计规格，逐步确认。
- **medium**（16–40 界面）：按模块分组生成规格，摘要确认。
- **large**（>40 界面）：脚本生成规格文件 + 仅展示高频界面预览。

### WebSearch 故障
- **Step 3 设计原则搜索**：
  - 工具不可用 → 告知用户「⚠ WebSearch 暂不可用」→ 提供选项：(a) 跳过搜索，使用风格默认 CSS 变量参数 (b) 用户手动提供设计参考 URL。
  - **品牌定制风（Brand Custom）+ 搜索无结果**：回退到 Flat/Minimal 风格的默认 CSS 变量 + ⚠ 警告「品牌定制风搜索无结果，已回退到 Flat/Minimal 默认参数，建议用户后续提供品牌设计规范」。

### 上游过期检测
- **`experience-map.json`**（若存在）：加载时比较 `generated_at` 与 `ui-design-decisions.json` 最新 `decided_at`。上游更新 → ⚠ 警告「experience-map 在 ui-design 上次运行后被更新，界面列表可能过期，建议重新运行 /ui-design refresh」。
- **`task-inventory.json`**：同理检查时间戳。
- 仅警告不阻断。

---

## 4 条铁律

1. **只出规格不出生产代码** — 输出是设计语言描述（布局/配色/组件建议），不生成任何 React、Vue 生产组件代码；Step 5 线框预览是静态骨架展示，Step 5.6 高保真预览是 Tailwind + CSS 变量驱动的视觉参考页面（供设计评审和开发参考，不是可部署的功能实现）

2. **experience-map 优先，缺席则推导** — 有 experience-map 按界面生成规格（每个 experience-map 界面对应一节规格）；没有 experience-map 则从 task-inventory 中的高频任务自动推导主要界面结构（每个高/中频任务 → 一个推导界面）。界面规格标注其关联任务的 `category`（core/basic）+ `innovation_ui`（true/false），便于团队区分核心功能界面、基础设施界面和创新概念界面

3. **WebSearch 摘要展示，用户确认后才应用** — 检索到的设计原则必须以摘要形式展示给用户并等待确认，不自动静默应用；用户有权跳过检索（输入「跳过」）并手动指定设计参数

4. **风格选择不可省略** — 设计风格属于用户偏好决策，必须在 Step 2 由用户明确选择或确认沿用历史风格；未确认风格前不得生成规格和预览
