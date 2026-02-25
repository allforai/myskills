# `/ui-design` Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 product-audit 插件中新增 `/ui-design` 命令，从产品地图 + 界面地图推导 UI 设计规格，结合用户选定风格和 WebSearch 检索的设计原则，输出 `ui-design-spec.md` 和按角色拆分的 HTML 预览文件。

**Architecture:** 新增 `commands/ui-design.md`（命令入口）+ `skills/ui-design.md`（完整工作流文档），加入现有 product-audit 插件。执行时按 5 个 Step 推进：产品画像推导 → 风格选择 → WebSearch → 设计规格 → HTML 生成。

**Tech Stack:** 纯 Markdown skill 文件。HTML 预览由 skill 执行时生成（内联 CSS，无依赖）。缓存目录与源码目录保持同步。

---

## 涉及文件

**新建（4 个）：**
- `product-audit-skill/commands/ui-design.md`
- `product-audit-skill/skills/ui-design.md`
- `.claude/plugins/cache/myskills/product-audit/2.6.0/commands/ui-design.md`（内容同源码）
- `.claude/plugins/cache/myskills/product-audit/2.6.0/skills/ui-design.md`（内容同源码）

**修改（2 个）：**
- `product-audit-skill/.claude-plugin/plugin.json`
- `.claude/plugins/cache/myskills/product-audit/2.6.0/.claude-plugin/plugin.json`

---

## Task 1：创建 `commands/ui-design.md`（两处）

**Files:**
- Create: `product-audit-skill/commands/ui-design.md`
- Create: `.claude/plugins/cache/myskills/product-audit/2.6.0/commands/ui-design.md`

**Step 1：写入命令文件内容**

两处文件内容完全一致：

```markdown
---
description: "UI 设计规格：从产品地图 + 界面地图推导高层 UI 设计规格，结合风格选择和设计原则，输出设计规格文档 + 按角色拆分的 HTML 预览。模式: full / refresh"
argument-hint: "[mode: full|refresh]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "WebSearch"]
---

# UI Design — UI 设计规格生成

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

- **无参数 或 `full`** → 完整流程：Step 1 → Step 2 → Step 3 → Step 4 → Step 5
- **`refresh`** → 将 `ui-design-decisions.json` 重命名为 `.bak`，清除缓存，完整重跑

## 前置检查

执行前必须检查：

1. `.allforai/product-map/product-map.json` 必须存在，否则输出「请先运行 /product-map 建立产品地图」并**立即终止**
2. `.allforai/screen-map/screen-map.json` 可选，存在则按界面生成规格，不存在则从高频任务自动推导界面结构
3. `.allforai/product-concept/product-concept.json` 可选，存在则提取产品定位和价值主张用于配色基调
4. **历史决策加载**：检查 `.allforai/ui-design/ui-design-decisions.json`，存在则加载，已决策项（如风格选择）自动跳过

## 执行流程

1. 加载 `${CLAUDE_PLUGIN_ROOT}/skills/ui-design.md` 中的完整工作流和铁律
2. 根据模式执行对应步骤
3. 每个 Step 完成后展示摘要，等待用户确认
4. **【强制】执行完毕后，必须在对话中直接输出完整的报告摘要**

## 详细文档（按需用 Read 工具加载）

- `${CLAUDE_PLUGIN_ROOT}/skills/ui-design.md` — 完整工作流、Step 详述、风格列表、HTML 生成规则、铁律

## Step 执行要求

每个 Step 完成后：
1. 将结果写入 `.allforai/ui-design/` 目录下对应文件
2. 向用户展示结果摘要
3. 等待用户确认后才进入下一个 Step

## 报告输出要求（强制执行）

执行完成后，必须在对话中直接输出以下报告摘要：

```
## UI 设计规格报告摘要

> 执行时间: {时间}
> 选用风格: {风格名}
> 设计原则来源: {WebSearch 检索到的主要文档名/URL}

### 总览

| 维度 | 结果 |
|------|------|
| 覆盖角色 | X 个 |
| 覆盖界面 | X 个（来自 screen-map / 任务推导） |
| 生成 HTML 文件 | X 个（index + 各角色） |

### 设计规格要点

（每个角色/界面的布局模式、配色语义、组件库建议摘要）

### 输出文件

> 设计规格: `.allforai/ui-design/ui-design-spec.md`
> HTML 预览: `.allforai/ui-design/preview/index.html`
> 角色预览: `.allforai/ui-design/preview/ui-role-{角色名}.html`
> 决策日志: `.allforai/ui-design/ui-design-decisions.json`
```

---

## 铁律（强制执行）

> 完整定义见 `${CLAUDE_PLUGIN_ROOT}/skills/ui-design.md` 的「3 条铁律」章节。

1. **只出规格不出代码** — 输出是设计语言描述，不生成 React/Vue 组件代码
2. **screen-map 优先，缺席则推导** — 有 screen-map 按界面生成；没有则从高频任务自动推导主要界面
3. **WebSearch 摘要展示，用户确认后才应用** — 检索到的设计原则必须摘要给用户确认，不自动静默应用
```

**Step 2：验证两个文件内容一致**

```bash
diff product-audit-skill/commands/ui-design.md \
     .claude/plugins/cache/myskills/product-audit/2.6.0/commands/ui-design.md
```

期望输出：空（无差异）

**Step 3：commit**

```bash
git add product-audit-skill/commands/ui-design.md
git commit -m "feat(ui-design): 新增命令文件 commands/ui-design.md"
```

---

## Task 2：创建 `skills/ui-design.md`（两处）

**Files:**
- Create: `product-audit-skill/skills/ui-design.md`
- Create: `.claude/plugins/cache/myskills/product-audit/2.6.0/skills/ui-design.md`

**Step 1：写入技能详情文件内容**

两处文件内容完全一致：

```markdown
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

**前提**：必须先运行 `product-map`。`screen-map` 可选但推荐，存在时规格更精准。

---

## 快速开始

```
/ui-design            # 完整流程（风格选择 → 检索 → 生成规格 → 生成 HTML）
/ui-design refresh    # 清除决策缓存，重新选风格 + 完整重跑
```

---

## 工作流

```
前置检查：
  product-map.json 必须存在（否则终止）
  screen-map.json 可选（存在则按界面；否则从高频任务推导）
  product-concept.json 可选（提取定位/价值主张用于配色基调）
  ui-design-decisions.json 存在则加载历史决策
  ↓
Step 1: 产品画像推导
  读取 task-inventory + role-profiles + screen-map（可选）
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

---

## Step 1：产品画像推导

**数据加载**：
- `task-inventory.json` — 获取所有任务、频次、角色归属
- `role-profiles.json` — 获取角色列表和 audience_type（consumer/professional）
- `screen-map.json`（可选）— 获取界面列表和 audience_type
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

## 3 条铁律

1. **只出规格不出代码** — 输出是设计语言描述（布局/配色/组件建议），不生成任何 React、Vue、HTML 组件代码；HTML 预览是静态骨架展示，不是功能实现

2. **screen-map 优先，缺席则推导** — 有 screen-map 按界面生成规格（每个 screen-map 界面对应一节规格）；没有 screen-map 则从 task-inventory 中的高频任务自动推导主要界面结构（每个高/中频任务 → 一个推导界面）

3. **WebSearch 摘要展示，用户确认后才应用** — 检索到的设计原则必须以摘要形式展示给用户并等待确认，不自动静默应用；用户有权跳过检索（输入「跳过」）并手动指定设计参数
```

**Step 2：验证两处文件一致**

```bash
diff product-audit-skill/skills/ui-design.md \
     .claude/plugins/cache/myskills/product-audit/2.6.0/skills/ui-design.md
```

期望输出：空（无差异）

**Step 3：commit**

```bash
git add product-audit-skill/skills/ui-design.md
git commit -m "feat(ui-design): 新增技能详情文件 skills/ui-design.md"
```

---

## Task 3：更新 plugin.json description（两处）

**Files:**
- Modify: `product-audit-skill/.claude-plugin/plugin.json`
- Modify: `.claude/plugins/cache/myskills/product-audit/2.6.0/.claude-plugin/plugin.json`

**Step 1：追加 description**

在两处 plugin.json 的 `description` 字段末尾追加（紧接 product-verify 描述之后）：

```
ui-design (generate UI design spec and role-based HTML preview from product map and screen map).
UI设计规格生成（从产品地图推导高层UI规格 + 按角色拆分HTML预览）。
```

**Step 2：验证 JSON 格式合法**

```bash
cat product-audit-skill/.claude-plugin/plugin.json | python3 -m json.tool > /dev/null && echo "valid"
cat .claude/plugins/cache/myskills/product-audit/2.6.0/.claude-plugin/plugin.json | python3 -m json.tool > /dev/null && echo "valid"
```

期望输出：两行 `valid`

**Step 3：commit 所有改动**

```bash
git add product-audit-skill/commands/ui-design.md \
        product-audit-skill/skills/ui-design.md \
        product-audit-skill/.claude-plugin/plugin.json
git commit -m "feat(ui-design): v1.0.0 — 新增UI设计规格命令，风格选择+WebSearch+角色HTML预览"
```

---

## Task 4：commit & push

**Step 1：确认状态干净**

```bash
git status
```

期望：`nothing to commit, working tree clean`

**Step 2：push**

```bash
git push
```
