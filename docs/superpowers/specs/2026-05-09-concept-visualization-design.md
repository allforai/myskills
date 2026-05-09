# Concept Visualization Design

## Overview

在所有概念阶段（产品概念、美术概念、游戏设计、App设计），CLI Q&A 进行的同时，Claude 生成并持续更新3个 HTML 可视化文件，通过 Playwright 在浏览器里实时展示进展。

**核心原则：**
- Q&A 交互**只在命令行**完成，HTML 是纯展示层
- 3个独立 HTML 文件，每个专注一件事
- Playwright 始终可用（`mcp__plugin_playwright_playwright__*`），无降级设计
- game-design 跨多次 `/run` 执行，HTML 文件跨 session 累积，不重置

---

## Architecture

### 文件结构

每次概念阶段在 `.allforai/concept-session/<phase-id>/` 下生成：

```
.allforai/concept-session/<phase-id>/
  ├── conclusion-kanban.html   # 结论看板
  ├── mindmap.html             # 思维导图
  └── wireframes.html          # 线框图
```

`<phase-id>` 取值：`product-concept` | `art-concept` | `game-design` | `app-design`

### Playwright 会话管理

**打开3个页面（三步序列，非并行）：**

```
步骤1：browser_navigate → file:///abs/path/conclusion-kanban.html
        （在当前页打开 Tab 1）

步骤2：browser_evaluate → window.open('file:///abs/path/mindmap.html', '_blank')
        （浏览器新标签页打开 Tab 2）

步骤3：browser_evaluate → window.open('file:///abs/path/wireframes.html', '_blank')
        （浏览器新标签页打开 Tab 3）
```

绝对路径通过 `pwd` 或 bootstrap-profile.json 中的项目根目录拼接得到。

**刷新已打开的页面：**

```
browser_tabs → 列出所有已打开页面，找到对应 pageId
browser_navigate(url=same_file_url, page=pageId) → 重新导航触发刷新
```

**关闭本次会话页面（阶段结束时）：**

```
browser_tabs → 列出所有页面
# 只关闭本次打开的3个页面（匹配 concept-session/<phase-id>/ 路径）
# 不关闭其他已有页面
browser_close(pageId=tab1_id)
browser_close(pageId=tab2_id)
browser_close(pageId=tab3_id)
```

**重复运行处理（phase 被再次执行时）：**

- `conclusion-kanban.html` / `mindmap.html`：检查文件是否已存在
  - 已存在 → 读取现有内容，在已有状态基础上继续追加（跨 session 累积）
  - 不存在 → 创建新文件
- `wireframes.html`：每次覆盖重写（线框是阶段性快照，不需要累积）
- game-design 专项：每个节点执行时读取已有 HTML 文件，在已有卡片/节点基础上追加新内容

---

## HTML Files Specification

### 1. conclusion-kanban.html

**用途：** 收纳每个子阶段的确认结论，纯展示，无交互。

**视觉风格：** 深色主题（`#1a1a2e` 背景），列宽等分，卡片按时间序纵向堆叠，列标题固定在顶部。

**卡片结构：**
```
┌─────────────────────────┐
│ [子阶段标签]  [时间戳]   │  ← 灰色小字
│ 结论标题（粗体白字）       │
│ ─────────────────────── │
│ · 关键数据点 1           │
│ · 关键数据点 2           │
│ ─────────────────────── │
│ 来源：[搜索证据/用户确认] │  ← 浅色斜体
└─────────────────────────┘
```

**HTML 初始模板结构：**

```html
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>{PHASE_LABEL} — 结论看板</title>
  <style>
    body { background: #1a1a2e; color: #e0e0e0; font-family: sans-serif; margin: 0; padding: 16px; }
    h1 { font-size: 16px; color: #8888aa; margin-bottom: 16px; }
    .board { display: flex; gap: 16px; align-items: flex-start; }
    .column { flex: 1; min-width: 0; }
    .col-title { font-size: 12px; font-weight: bold; color: #8888ff; text-transform: uppercase;
                 padding: 8px 0; border-bottom: 1px solid #333; margin-bottom: 12px; }
    .card { background: #252540; border-radius: 8px; padding: 12px; margin-bottom: 10px;
            border-left: 3px solid #5555ff; }
    .card-meta { font-size: 10px; color: #666; margin-bottom: 6px; }
    .card-title { font-weight: bold; margin-bottom: 8px; font-size: 14px; }
    .card-points { font-size: 12px; color: #bbb; margin-bottom: 8px; }
    .card-source { font-size: 10px; color: #777; font-style: italic; }
    .empty { font-size: 12px; color: #444; text-align: center; padding: 20px 0; }
  </style>
</head>
<body>
  <h1>{PHASE_LABEL} · 结论看板</h1>
  <div class="board">
    {COLUMNS_HTML}  <!-- 每列: <div class="column"><div class="col-title">列名</div><div id="col-{slug}"></div></div> -->
  </div>
</body>
</html>
```

追加卡片时，向对应列的 `div#col-{slug}` 内插入卡片 HTML，重写整个文件。

**各阶段列定义：**

| 阶段 | 列1 | 列2 | 列3 | 列4 | 列5 |
|------|-----|-----|-----|-----|-----|
| 产品概念 | 问题 | 用户 | 竞品洞察 | 核心功能 | 商业模式 |
| 美术概念 | 视觉方向 | 技术规格 | 资产清单 | 工具链 | — |
| 游戏设计 | 核心玩法 | 经济系统 | 成长系统 | 叙事 | 美术方向 |
| App设计 | 用户流程 | 页面结构 | 组件规范 | 设计Token | — |

**更新时机：** 每个子阶段 Q&A 结论确认后立即追加卡片到对应列，重写整个 HTML 文件。

---

### 2. mindmap.html

**用途：** 展示产品/游戏/设计的结构关系，随决策演化动态添加节点。

**视觉风格：** 内联 SVG，深色背景（`#0d1117`），左根右叶水平树，节点圆角矩形，边用贝塞尔曲线。

**SVG 布局算法（固定规则，Claude 遵守）：**

```
坐标系：左上角 (0,0)，SVG 宽度 = 1200px，高度随节点数自动扩展
根节点：固定在 (80, 中心Y)
一级节点：x = 320，y 均分分布（间距 80px）
二级节点：x = 560，y 跟随父节点均分
三级节点：x = 800，y 跟随父节点均分

节点尺寸：宽 180px，高 36px，圆角 6px
边：从父节点右边中点 → 子节点左边中点，贝塞尔曲线（控制点 x 各偏移 60px）

节点颜色：
  根节点    → fill: #3d5a80
  结构节点  → fill: #2d3748（蓝灰）
  结论节点（游戏设计专用）→ fill: #744210（橙）
  文字      → fill: #e0e0e0，font-size: 12px
```

**HTML 初始模板结构：**

```html
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>{PHASE_LABEL} — 思维导图</title>
  <style>
    body { background: #0d1117; margin: 0; padding: 16px; }
    h1 { color: #8888aa; font-size: 16px; font-family: sans-serif; margin-bottom: 12px; }
    svg { width: 100%; overflow: auto; display: block; }
  </style>
</head>
<body>
  <h1>{PHASE_LABEL} · 思维导图</h1>
  <svg id="mindmap" viewBox="0 0 1200 {HEIGHT}" xmlns="http://www.w3.org/2000/svg">
    {NODES_AND_EDGES_SVG}
  </svg>
</body>
</html>
```

每次更新重写整个 SVG 内容（重新计算所有节点坐标）。

**各阶段思维导图初始根结构：**

| 阶段 | 根节点标题 | 一级节点（初始） |
|------|-----------|----------------|
| 产品概念 | 产品名（来自 product-concept.json） | 核心用户 / 解决问题 / 核心功能 / 商业模式 |
| 美术概念 | `{产品名}` + 美术概念 | 维度 / 风格 / 动画系统 / 工具链 |
| 游戏设计 | 游戏名（来自 game-design-doc.json） | 核心玩法 / 经济 / 成长 / 叙事 / 美术 |
| App设计 | App名 | 核心流程 / 页面层级 / 组件库 / 设计规范 |

> 注：美术概念根节点不写死"游戏美术"，从上游产品名派生，适用于游戏和非游戏产品。

**更新时机：** 与 conclusion-kanban.html 同步，每轮结论确认后添加对应节点，重写整个 HTML 文件。

---

### 3. wireframes.html

**用途：** 阶段性注入线框草图，早期低保真激发想象，后期中保真验证概念。

**视觉风格：**
- 上区：当前最新线框（全宽大图展示）
- 下区：历史版本缩略图时间轴（小图 + 时间戳标注）
- 每次更新：将旧版本移至历史区，新版本展示在主区

**各阶段线框触发规则：**

| 阶段 | 低保真触发时机 | 中保真触发时机 |
|------|-------------|-------------|
| 产品概念 | 「竞品洞察」列第1张卡片出现后 | 「核心功能」列第1张卡片出现后 |
| 美术概念 | 「视觉方向」列第1张卡片出现后（Q1答完） | 「技术规格」列第1张卡片出现后（Q3答完） |
| 游戏设计 | `core-loop-design` 节点完成后 | `art-direction` 节点完成后 |
| App设计 | 「用户流程」列第1张卡片出现后 | 「页面结构」列第1张卡片出现后 |

**各阶段线框内容定义：**

| 阶段 | 低保真内容 | 中保真内容 |
|------|----------|----------|
| 产品概念 | App主界面骨架（导航栏+主要区块占位框） | 核心用户流程线框（含页面跳转箭头） |
| 美术概念 | 色盘+质感参考格（色块+文字标注风格关键词） | 资产规格示意图（各类资产尺寸比例对照表） |
| 游戏设计 | HUD草图（血量/分数/道具栏位置）+ 关卡布局草图（独立两块） | 完整游戏 UI 层级线框（主菜单→游戏中→结算） |
| App设计 | 主屏幕骨架线框 | 核心页面线框集（3-5个关键页面） |

**保真度视觉规范：**

低保真：SVG 粗线条（stroke-width: 2, stroke: #666），矩形无填充（fill: none），文字用等宽字体占位（`X X X X`）。

中保真：SVG 灰度色块填充（fill: #2a2a2a），组件名文字标注（font-size: 11px），尺寸标注箭头（dashed line + 数字）。

**HTML 初始模板结构：**

```html
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>{PHASE_LABEL} — 线框图</title>
  <style>
    body { background: #1a1a2e; color: #e0e0e0; font-family: sans-serif; margin: 0; padding: 16px; }
    h1 { font-size: 16px; color: #8888aa; }
    .main-frame { border: 1px solid #333; border-radius: 8px; padding: 16px; margin-bottom: 24px; background: #111; }
    .frame-label { font-size: 11px; color: #666; margin-bottom: 8px; }
    .history { display: flex; gap: 12px; flex-wrap: wrap; }
    .history-item { border: 1px solid #2a2a2a; border-radius: 4px; padding: 8px;
                    font-size: 10px; color: #555; text-align: center; cursor: default; }
    .history-item svg { display: block; margin: 0 auto 4px; }
    .placeholder { color: #333; text-align: center; padding: 40px; font-size: 13px; }
  </style>
</head>
<body>
  <h1>{PHASE_LABEL} · 线框图</h1>
  <div class="main-frame">
    <div class="frame-label" id="main-label">等待第一个线框生成...</div>
    <div id="main-content"><p class="placeholder">Q&A 进行中，关键节点后自动生成</p></div>
  </div>
  <div id="history" class="history"></div>
</body>
</html>
```

---

## Shared Protocol

新增 `knowledge/capabilities/concept-visualization.md`，各概念阶段 skill/capability 文件在对应位置引用此协议。

### 启动序列

```
## Concept Visualization — 启动

前置：确认 .allforai/concept-session/<phase-id>/ 目录存在
      （mkdir -p 若不存在）

判断是否首次运行（文件是否存在）：
  首次：生成三个初始 HTML（含阶段标题、列定义/根节点、空内容区）
  重复：读取现有 conclusion-kanban.html 和 mindmap.html 的已有内容，
        继续累积（wireframes.html 总是重置）

打开浏览器页面（顺序执行）：
  1. browser_navigate(url='file:///abs/path/conclusion-kanban.html')
  2. browser_evaluate(script="window.open('file:///abs/path/mindmap.html','_blank')")
  3. browser_evaluate(script="window.open('file:///abs/path/wireframes.html','_blank')")
  4. browser_tabs → 记录三个页面的 pageId，用于后续刷新和关闭

开始 CLI Q&A
```

### 每轮结论更新序列

```
## Concept Visualization — 结论更新

触发：子阶段 Q&A 完成，结论确认

1. 生成结论卡片内容（标题 + 数据点列表 + 来源标注）
2. 将卡片插入对应列，重写 conclusion-kanban.html
3. 计算思维导图新增节点及坐标（按布局算法）
4. 重写 mindmap.html（全量 SVG 重新生成）
5. browser_navigate(url=kanban_url, page=tab1_pageId)   → 刷新看板
6. browser_navigate(url=mindmap_url, page=tab2_pageId)  → 刷新思维导图

[若到达线框触发节点（见各阶段触发规则）]
7. 生成对应保真度的内联 SVG 线框
8. 将旧主区内容移入历史区，新线框写入主区，重写 wireframes.html
9. browser_navigate(url=wireframes_url, page=tab3_pageId) → 刷新线框
```

### 结束序列

```
## Concept Visualization — 结束

1. 最终 mindmap.html 写入完整结构（确认所有节点都已添加）
2. 记录 session 中打开的 pageId 列表
3. 逐一关闭本次开启的3个页面（仅关闭这3个，不影响其他页面）：
   browser_close(page=tab1_pageId)
   browser_close(page=tab2_pageId)
   browser_close(page=tab3_pageId)
4. CLI 输出文件路径：
   "可视化文件已保存：
    看板：.allforai/concept-session/<phase-id>/conclusion-kanban.html
    导图：.allforai/concept-session/<phase-id>/mindmap.html
    线框：.allforai/concept-session/<phase-id>/wireframes.html"
```

---

## Files to Modify

| 文件 | 改动类型 | 改动内容 |
|------|---------|---------|
| `knowledge/capabilities/concept-visualization.md` | **新增** | 共享协议全文 + 各阶段配置表 + HTML模板 |
| `knowledge/capabilities/product-concept.md` | 修改 | 启动序列写入 Overview；每个子阶段末尾添加「→ 更新看板+思维导图」；竞品洞察/核心功能完成时触发线框 |
| `skills/art-concept.md` | 修改 | Step 0 添加启动序列；Step 1 每问答完后更新；Q1答完触发低保真线框；Q3答完触发中保真线框 |
| `knowledge/capabilities/game-design.md` | 修改 | 每个节点执行末添加更新调用；跨 session 累积模式说明；core-loop-design 完成触发低保真；art-direction 完成触发中保真 |
| `knowledge/capabilities/ui-design.md` | 修改 | 各子阶段末添加更新调用（App设计流程） |

---

## Data Flow

```
CLI Q&A 结论
    │
    ▼
concept-visualization.md 协议
    │
    ├──▶ conclusion-kanban.html  （Playwright 刷新 Tab 1）
    ├──▶ mindmap.html            （Playwright 刷新 Tab 2）
    └──▶ wireframes.html         （关键节点，Playwright 刷新 Tab 3）

后续节点 Context Pull（可选读取，作为可视化参考）：
  art-spec-design      ◀── art-concept/conclusion-kanban.html
  game-design-finalize ◀── game-design/mindmap.html
  implement-ui-systems ◀── app-design/conclusion-kanban.html
  product-analysis     ◀── product-concept/mindmap.html
```

---

## 工具层 vs LLM特化层

本协议的执行分为两个层次，职责严格分离：

### 工具层（机械执行层）

**定义：** 与项目内容无关的固定动作序列，任何阶段、任何产品执行方式完全相同。

| 操作 | 调用形式 | 说明 |
|------|---------|------|
| 打开浏览器标签页 | `browser_navigate(url='file:///...')` | 固定调用顺序：先 Tab1，再 window.open Tab2、Tab3 |
| 打开追加标签页 | `browser_evaluate(script="window.open('file:///...','_blank')")` | Tab2/Tab3 专用，脚本内容固定 |
| 记录标签 pageId | `browser_tabs` | 记录结果供后续刷新/关闭使用 |
| 刷新指定页面 | `browser_navigate(url=same_url, page=pageId)` | 固定模式，重导航触发刷新 |
| 关闭指定页面 | `browser_close(page=pageId)` | 仅关闭本次打开的3个，不影响其他 |
| 写入 HTML 文件 | `Write(file_path=..., content=...)` | 整页覆盖，写完才刷新 |
| 检测文件是否存在 | `Read(file_path=...)` | 判断首次/重复运行 |

工具层不感知产品内容，只负责「在正确时机调用正确工具」。

### LLM特化层（内容生成层）

**定义：** 需要 LLM 基于本次概念阶段 Q&A 实际结果进行推理和生成的内容。每个项目不同，每次执行不同。

**看板卡片内容（conclusion-kanban.html）：**

```
LLM 任务：给定已确认的 Q&A 结论，生成卡片 HTML 内容：
  - 结论标题：一句话总结本轮结论（不超过20字）
  - 关键数据点：2-4条支撑性事实或数据（来自搜索证据或用户选择）
  - 来源标注：搜索来源URL简写 或 "用户确认"

示例输出（产品概念"问题"列卡片）：
  标题：「年轻用户缺乏快速记录情绪的工具」
  数据点：
    · 78% 受访者在睡前有情绪记录意愿（BehaviorSurvey 2024）
    · 现有日记App平均打开到记录耗时 >45秒
  来源：brave_web_search#3 + 用户确认

LLM 生成 <div class="card">...</div> 的完整 HTML，工具层负责写入文件。
```

**思维导图 SVG 内容（mindmap.html）：**

```
LLM 任务：给定本次新增结论，确定以下内容：
  1. 新节点标签文字（来自结论关键词，≤10字）
  2. 新节点挂载的父节点（在已有树结构中选择最合适的）
  3. 节点类型（结构节点 or 结论节点—仅游戏设计阶段）

LLM 不负责计算坐标 — 坐标由固定布局算法（x=80/320/560/800 分层，80px间距）机械计算。
LLM 负责：节点语义内容 + 树挂载位置。
工具层（算法）负责：坐标计算 + 贝塞尔曲线路径 + SVG代码输出。
```

**线框 SVG（wireframes.html）：**

```
LLM 任务：给定当前阶段已确认的结构信息，生成内联 SVG 线框内容：
  低保真：从产品方向生成主界面骨架轮廓（SVG 粗线条矩形 + 文字占位）
  中保真：从核心功能列表生成关键流程线框（灰度色块 + 组件标注）

SVG 内容的布局和元素选择由 LLM 根据产品特点决定：
  - 哪些区块放在顶部、中部、底部
  - 哪些关键交互元素需要标注
  - 流程步骤如何用箭头连接

LLM 生成完整内联 SVG 代码，工具层负责写入 main-content div 并刷新浏览器。
```

**边界原则：**
- 凡是「内容写什么」→ LLM特化层（需理解当前项目上下文）
- 凡是「如何呈现到浏览器」→ 工具层（固定调用序列）
- 坐标计算、HTML结构、CSS样式 → 工具层（固定模板，不因项目而变）

---

## Constraints

- Playwright MCP 始终可用（`mcp__plugin_playwright_playwright__*`），无降级
- Tab 管理：第1个用 `browser_navigate`，第2、3个用 `browser_evaluate` 执行 `window.open`；`browser_tabs` 记录 pageId 用于后续刷新和精准关闭
- HTML 文件整页重写（非 DOM patch），每次写完再刷新
- SVG 由 Claude 按固定布局算法内联生成，无外部图表库依赖
- 线框保真度由各阶段明确的触发规则决定，不由 Claude 自由判断
- game-design HTML 文件跨 `/run` session 累积，不重置
