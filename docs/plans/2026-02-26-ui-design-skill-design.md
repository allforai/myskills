# Design Doc: `/ui-design` Skill

Date: 2026-02-26
Plugin: product-audit
Status: Approved

---

## 目标

以 `product-map`（以及可选的 `screen-map`、`product-concept`）为输入，结合用户选定的 UI 风格和 WebSearch 检索到的设计原则，输出高层 UI 设计规格文档 + 多界面按角色拆分的 HTML 预览文件。

---

## 定位

```
product-concept → product-map → screen-map → ui-design
（方向）          （任务）       （界面）       （视觉规格 + 预览）
```

---

## 命令入口

```
/ui-design              # 完整流程
/ui-design refresh      # 清除 ui-design-decisions.json，重新选风格 + 完整重跑
```

---

## 执行流程

### 前置检查

- `product-map.json` 必须存在，否则提示「请先运行 /product-map」并终止
- `screen-map.json` 可选：存在则按界面生成规格；不存在则从高频任务自动推导主要界面结构
- `product-concept.json` 可选：提取产品定位、价值主张用于配色和文案基调
- `ui-design-decisions.json` 存在则加载，风格选择等已决策项自动跳过

### Step 1：产品画像推导

从 `task-inventory.json` + `role-profiles.json` + `screen-map.json` 读取：
- 受众类型（consumer / professional / 混合）
- 角色列表及各角色的高频任务
- 界面总数（有 screen-map 时）

向用户展示推导结果，确认后进入 Step 2。

### Step 2：风格选择题（AskUserQuestion）

向用户展示 8 种主流风格，单选：

| 编号 | 风格 | 代表产品 | 特点 |
|------|------|---------|------|
| 1 | Material Design 3 | Google Workspace、Android | 动效、层级感、高色彩表现力 |
| 2 | Apple HIG | iOS 系统应用、Notion | 留白、极简、圆角、系统字体 |
| 3 | Fluent Design | Microsoft 365、VS Code | 亚克力毛玻璃、流动感、深浅模式 |
| 4 | Flat / Minimal | Linear、Vercel | 无阴影、高对比、信息密度高 |
| 5 | Glassmorphism | macOS widgets | 毛玻璃、渐变背景、模糊效果 |
| 6 | Ant Design 企业风 | 阿里系中后台 | 蓝灰色系、表格导向、高信息密度 |
| 7 | Shadcn / Tailwind 现代感 | Vercel、Raycast | 无障碍优先、深色模式、极简组件 |
| 8 | 品牌定制风 | Stripe、Airbnb | 强品牌色、独特字体、高辨识度 |

### Step 3：检索设计原则（WebSearch）

根据所选风格进行 WebSearch：
- 官方设计系统文档（如 Material Design guidelines、Apple HIG、Ant Design 官网）
- 核心设计原则文章

提取：配色逻辑、排版规范、组件偏好、交互原则。
摘要展示给用户确认后，才应用到后续生成。

### Step 4：生成设计规格（`ui-design-spec.md`）

逐界面（或逐高频任务推导的界面）输出高层规格：
- 界面目的与主视觉结构
- 布局模式（单列 / 双栏 / 仪表盘 / 侧边导航等）
- 配色语义（主色 / 辅色 / 功能色 — 成功/警告/错误）
- 主要组件库建议（如 shadcn/ui / Ant Design / Radix UI 等）
- 关键交互状态：空态 / 加载中 / 错误 / 成功反馈
- 受众设计提示（consumer 需要引导式空态、防呆校验；professional 支持高密度信息）

### Step 5：生成多角色 HTML 预览

生成方式：Python 脚本或直接写文件

**文件结构**：
```
.allforai/ui-design/preview/
├── index.html              # 总导航：角色卡片列表，显示界面数+高频任务，点击跳转
├── ui-role-{角色名}.html   # 每个角色一个文件，展示该角色可见的所有界面
└── ...
```

**index.html**：
- 每个角色一张卡片，显示：角色名、可见界面数、Top 3 高频任务
- 点击跳转对应角色 HTML
- 顶部显示产品名、选用风格

**每个 `ui-role-{角色名}.html`**：
- 纯 HTML + 内联 CSS，无外部依赖，直接浏览器打开
- 界面按模块分组，每个界面一个卡片
- 每张卡片展示：
  - 界面名 + 主要目的
  - 主操作区域骨架（主按钮、表单字段列表、关键数据展示区）
  - 三态骨架：正常 / 空态 / 错误
- 配色和字体风格匹配所选设计风格
- 顶部面包屑：产品名 > 角色名 > 模块名

---

## 输出文件

```
.allforai/ui-design/
├── ui-design-spec.md           # 高层设计规格（按界面/任务展开）
├── ui-design-decisions.json    # 用户决策日志（风格选择、确认记录）
└── preview/
    ├── index.html              # 总导航
    ├── ui-role-{角色1}.html
    ├── ui-role-{角色2}.html
    └── ...
```

---

## 3 条铁律

1. **只出规格不出代码** — 输出是设计语言描述，不是 React/Vue 组件代码
2. **screen-map 优先，缺席则推导** — 有 screen-map 按界面生成；没有则从高频任务自动推导主要界面
3. **WebSearch 摘要展示，用户确认后才应用** — 检索到的设计原则需摘要给用户确认，不自动静默应用

---

## 涉及文件（待实现）

| 文件 | 说明 |
|------|------|
| `product-audit-skill/commands/ui-design.md` | 命令文件 |
| `product-audit-skill/skills/ui-design.md` | 技能详情文件 |
| `.claude/plugins/cache/myskills/product-audit/2.6.0/commands/ui-design.md` | 运行时缓存 |
| `.claude/plugins/cache/myskills/product-audit/2.6.0/skills/ui-design.md` | 运行时缓存 |
| `product-audit-skill/.claude-plugin/plugin.json` | description 追加 ui-design |
| `.claude/plugins/cache/myskills/product-audit/2.6.0/.claude-plugin/plugin.json` | 同上 |
