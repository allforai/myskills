# UI Design — Design Steps

> Steps that generate design tokens, component specs, and visual specs.
> Loaded by `skills/ui-design.md` orchestrator.

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

向用户展示 8 种风格，每种附带描述和代表产品：

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

### Variants 模式（--variants N）

当指定 `--variants N`（N ≥ 2）时，在 Step 2（风格选择）阶段生成 N 套不同的视觉方案：

**Step 2v: 多风格发散**
- 不再让用户选单一风格，而是自动选 N 种风格组合
- 使用 Agent 并发为每种风格生成：
  - tokens.json（设计令牌）
  - 2-3 个代表性界面的 hifi-preview HTML
- 输出到 `.allforai/ui-design/variants/variant-{n}/`

**Step 2v.1: 视觉对比**
- 生成对比导航页 `variants/comparison.html`
- 每个方案展示：风格名称 + 设计令牌摘要 + 2-3 个代表界面截图/链接
- 向用户提问 让用户选择风格方向

**Step 2v.2: 确认后执行**
- 选中风格后，按正常流程（Step 3-5）完成全套界面
- 记录选择到 ui-design-decisions.json

---

## Step 3：检索设计原则

**搜索策略**（按所选风格）：

| 风格 | 搜索关键词 |
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

> 注：v2 交互类型体系共 37 种（MG1-8、CT1-6、EC1-4、WK1-5、RT1-4、SB1-4、SY1-3、TU1-3），完整定义见 `./docs/interaction-types.md`。

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

图标库选型（根据当前端类型的 ui_styles 推断）：
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

**视图模式设计**（仅后台屏幕，有 view_modes 时）：
- 模式 1 — {label}：{布局描述，组件可见性，区域占比}
- 模式 2 — {label}：{布局变化，新增/隐藏的组件}
- 模式切换动效：{过渡动画描述}

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

直接逐文件写入完整 HTML 字符串。不使用 Python 脚本，避免执行环境依赖。

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
python3 ../../shared/scripts/product-design/gen_ui_components.py <BASE> --mode auto
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
   python3 ../../shared/scripts/product-design/gen_ui_stitch.py <BASE> --mode auto
   ```
   输出：`ui-design/stitch-prompts.json`（最多 10 个屏幕的结构化 prompt）

2. 检测 Stitch MCP 可用性：
   - 检查 MCP 工具 `mcp__stitch__create_project` 是否可用
   - **不可用 → 自动降级到 Step 5.6 LLM 高保真预览**（零外部依赖，Tailwind + tokens.json 驱动，跨屏一致性由代码保证）。同时输出提示：

     ```
     Stitch 未就绪，自动使用 LLM 高保真预览生成视觉稿。
     如需 Stitch 可交互原型，执行 setup 工作流 配置后重新执行 /ui-design。
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
   x.    **开启链接分享**：Stitch API 暂不支持程序化修改 visibility，输出提示：
         ```
         Stitch 视觉稿已生成: https://stitch.withgoogle.com/projects/{projectId}
         ⚠ 请手动开启分享：打开上方链接 → 点击右上角「Share」→ 选择「Anyone with the link」
         （Stitch API 暂不支持自动设置分享权限，待 API 更新后将自动化此步骤）
         ```
   xi.   **生成视觉约束截图**：对 Stitch 项目中的每个屏幕，获取截图保存到 `ui-design/screenshots/{screen_id}.png`。
         这些截图是 dev-forge 的视觉约束输入 — dev-forge 读取规格 JSON 生成代码，截图用于验证视觉还原度。
         Stitch/frontend-design 的视觉稿产出到此结束，不向下游传递任何代码。

3b. **用户已确认跳过** → 仅输出 prompts，展示手动使用说明：
   ```
   已跳过 Stitch 视觉稿生成（用户确认），已生成 stitch-prompts.json。
   后续使用：
   1. 执行 setup 工作流 配置 Stitch（一次性 Google OAuth）
   2. 重新执行 ui-design 工作流，将自动调用 Stitch 生成视觉稿
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

**生成方式**：并行生成（每屏一个子任务，同时执行所有子任务）。

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
   - **UI 标签语言**：从 product-concept.json 的 tagline/product_name 推断产品目标语言。中文产品（tagline 含中文）→ 所有产品界面文案（标签、按钮、导航、描述文本、推荐语、分类名、状态提示）均使用中文；英文产品 → 使用英文。仅学习内容本身（如对话原文、单词、例句）保持目标语言
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

**C3. 生成视觉约束截图**

对 hifi-preview 中每个屏幕 HTML 页面，使用 Playwright 打开并截图，保存到 `ui-design/screenshots/{screen_id}.png`。
这些截图与 Stitch 阶段 C 的截图写入同一目录，作为 dev-forge 的视觉约束输入。

**输出进度**：

```
Step 5.6 ✓ LLM 高保真预览
  设计系统参考: _design-system.html（{N} 个共享组件）
  屏幕页面: {N} 个（{role1}: {n1}, {role2}: {n2}）
  一致性校验: {pass/N 项已修正}
  预览入口: .allforai/ui-design/hifi-preview/index.html
```

---

## 生成方式

LLM 直接分析 experience-map + task-inventory + product-concept，理解产品定位和用户角色后生成 UI 设计规格和 HTML 预览。UI 设计高度依赖产品语义（目标用户、情绪状态、品牌调性），脚本无法理解这些上下文。

可选辅助脚本：`../../shared/scripts/product-design/gen_ui_design.py`（用于生成 tokens.json 骨架和文件结构，LLM 必须在其上补充设计决策和内容填充）。
