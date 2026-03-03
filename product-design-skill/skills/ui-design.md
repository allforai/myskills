---
name: ui-design
description: >
  Use when the user wants to "generate UI design", "create UI spec", "design screens",
  "what should the UI look like", "UI style guide", "UI from product map",
  "design system recommendation", "UI 设计", "界面设计", "生成UI", "UI 规格",
  "从产品地图生成UI", "设计风格", "UI 预览", "界面风格",
  or wants to turn product map and screen map into visual design specifications.
  Requires product-map to have been run first. Optionally uses screen-map and product-concept.
version: "1.0.0"
---

# UI Design — UI 设计规格生成

> 产品地图说应该有什么，设计应该长什么样？

## 目标

以 `product-map`（以及可选的 `screen-map`、`product-concept`）为输入，结合用户选定的 UI 风格和实时检索的设计原则，输出两类产物：

1. **`ui-design-spec.md`** — 高层 UI 设计规格：每个界面的布局模式、配色语义、组件建议、交互状态
2. **按角色拆分的 HTML 预览** — 每个角色一个 HTML 文件，展示该角色可见的所有界面卡片；`index.html` 做总导航

---

## 定位

```
product-concept → product-map → screen-map → ui-design
（方向）          （任务）       （界面结构）  （视觉规格 + 预览）
```

**前提**：必须先运行 `product-map`。`screen-map` 不存在时自动运行生成界面地图。

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

**安全护栏**（自动模式下仍然停下来问用户）：
- ERROR 级验证失败（无法推导任何界面、product-map 损坏）
- `ui_style = "undecided"` 时 Step 2 回退交互模式（风格选择不可自动推断）

---

## 工作流

```
前置检查：
  product-map.json 必须存在（否则终止）
  screen-map.json 必须（不存在则自动运行 screen-map 生成）
  product-concept.json 可选（提取定位/价值主张用于配色基调）
  ui-design-decisions.json 存在则加载历史决策

  Pattern Catalog（可选读取）：
    若 .allforai/design-pattern/pattern-catalog.json 存在，读取并作为设计约束使用：
    - _pattern_group 相同的界面 → 必须使用相同的组件布局模板
    - _pattern_template 字段 → 作为界面设计的首选方案参考
    不存在 → 跳过，按标准流程设计

  Phase 2.8 — 加载创新概念清单（新增）：
    检查 .allforai/product-concept/adversarial-concepts.json：
      存在 → 加载 `concepts[]` 数组，标记 innovation_mode = "active"
      不存在 → innovation_mode = "none"
    检查 task-inventory.json 的 `innovation_tasks` 字段：
      存在 → 告知用户：「创新感知：active — 检测到 X 个创新任务」
      不存在 → innovation_mode = "none"
  ↓
Step 1: 产品画像推导
  读取 task-inventory + role-profiles + screen-map + innovation_tasks（前置检查已保证存在）
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
Step 5: 生成多角色 HTML 预览
  index.html + 每角色一个 ui-role-{角色名}.html
```

> **强制规则**：Step 2「风格选择」不可跳过。即使存在历史决策，也必须向用户展示当前风格并请求确认（可沿用历史风格或改选），不得静默默认。

---

## Step 1：产品画像推导

**数据加载**：
- `task-inventory.json` — 获取所有任务、频次、角色归属
- `role-profiles.json` — 获取角色列表和 audience_type（consumer/professional）
- `screen-map.json`（前置检查已保证存在）— 获取界面列表和 audience_type
- `product-concept.json`（可选）— 提取 value_proposition 用于文案基调

**输出画像**：
- 受众类型：consumer / professional / 混合
- 角色列表：每个角色的名称、audience_type、高频任务 Top 3
- 界面数：来自 screen-map 或估算值（高频任务数 × 1.5，取整）

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

---

## 界面规格

（按角色分组，每个界面一节）

### {角色名} 的界面

#### {界面名}（{audience_type}）

**界面目的**：{一句话}

**布局模式**：{单列 / 双栏 / 侧边导航+内容区 / 仪表盘 / 表格页}

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

## 预置脚本（优先使用）

检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_ui_design.py` 是否存在：
- **存在** → `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_ui_design.py <BASE> --mode auto [--style material-design-3|ios-human-interface]`
- **不存在** → 回退到 LLM 生成脚本（向后兼容）

预置脚本保证 schema 一致性和零语法错误。支持 `--style` 参数指定风格（默认读取 `pipeline_preferences.ui_style`）。

---

## 输出文件结构

```
.allforai/ui-design/
├── ui-design-spec.md               # 高层设计规格
├── ui-design-decisions.json        # 用户决策日志（风格选择、Step 确认记录）
└── preview/
    ├── index.html                  # 总导航
    ├── ui-role-{角色1}.html
    ├── ui-role-{角色2}.html
    └── ...
```

---

## 防御性规范

> 通用模式定义见 `docs/defensive-patterns.md`，以下为本技能的具体应用。

### 加载校验
- **`ui-design-decisions.json`**：加载时用 `python -m json.tool` 验证 JSON 合法性。解析失败 → 检查 `.bak` → 提示恢复或重新运行 `/ui-design refresh`。
- **`product-map.json` / `task-inventory.json`**：前置加载时验证 JSON 合法性。解析失败 → 提示用户重新运行 `/product-map`，终止执行。

### 零结果处理
- **无 screen-map 且无高/中频任务**：⚠ 明确告知「无法推导界面列表 — screen-map 不存在，且 task-inventory 中无高/中频任务可用于推导界面。请先运行 /screen-map 或 /product-map 补充任务频次」，**终止执行**（不生成空规格）。
- **Step 1 推导 0 界面**：同上处理。
- **Step 3 搜索 0 设计原则**：若搜索正常但无有用结果 → 告知用户，提供选项：(a) 使用所选风格的默认 CSS 变量 (b) 用户手动提供设计参考。

### 规模自适应
- **阈值**：以界面数为计量对象（来自 screen-map 或推导数量）。small ≤15 / medium 16–40 / large >40。
- **small**（≤15 界面）：逐界面生成设计规格，逐步确认。
- **medium**（16–40 界面）：按模块分组生成规格，摘要确认。
- **large**（>40 界面）：脚本生成规格文件 + 仅展示高频界面预览。

### WebSearch 故障
- **Step 3 设计原则搜索**：
  - 工具不可用 → 告知用户「⚠ WebSearch 暂不可用」→ 提供选项：(a) 跳过搜索，使用风格默认 CSS 变量参数 (b) 用户手动提供设计参考 URL。
  - **品牌定制风（Brand Custom）+ 搜索无结果**：回退到 Flat/Minimal 风格的默认 CSS 变量 + ⚠ 警告「品牌定制风搜索无结果，已回退到 Flat/Minimal 默认参数，建议用户后续提供品牌设计规范」。

### 上游过期检测
- **`screen-map.json`**（若存在）：加载时比较 `generated_at` 与 `ui-design-decisions.json` 最新 `decided_at`。上游更新 → ⚠ 警告「screen-map 在 ui-design 上次运行后被更新，界面列表可能过期，建议重新运行 /ui-design refresh」。
- **`task-inventory.json`**：同理检查时间戳。
- 仅警告不阻断。

---

## 4 条铁律

1. **只出规格不出代码** — 输出是设计语言描述（布局/配色/组件建议），不生成任何 React、Vue、HTML 组件代码；HTML 预览是静态骨架展示，不是功能实现

2. **screen-map 优先，缺席则推导** — 有 screen-map 按界面生成规格（每个 screen-map 界面对应一节规格）；没有 screen-map 则从 task-inventory 中的高频任务自动推导主要界面结构（每个高/中频任务 → 一个推导界面）。界面规格标注其关联任务的 `category`（core/basic）+ `innovation_ui`（true/false），便于团队区分核心功能界面、基础设施界面和创新概念界面

3. **WebSearch 摘要展示，用户确认后才应用** — 检索到的设计原则必须以摘要形式展示给用户并等待确认，不自动静默应用；用户有权跳过检索（输入「跳过」）并手动指定设计参数

4. **风格选择不可省略** — 设计风格属于用户偏好决策，必须在 Step 2 由用户明确选择或确认沿用历史风格；未确认风格前不得生成规格和预览
