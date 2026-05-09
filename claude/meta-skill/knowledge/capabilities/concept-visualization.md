# Concept Visualization Protocol

> 共享协议：由所有概念阶段（product-concept、art-concept、game-design、app-design）在对应位置引用。
> 在 Q&A 结论确认后调用此协议，将结论写入3个 HTML 可视化文件并通过 Playwright 展示。

## 阶段配置表

| phase-id | phase-label | 看板列（slug:名称，左→右） | 思维导图根节点来源 | 思维导图一级节点（初始） |
|---|---|---|---|---|
| `product-concept` | 产品概念 | wenti:问题 / yonghu:用户 / jingpin:竞品洞察 / gongneng:核心功能 / shangye:商业模式 | `product-concept.json → name` | 核心用户 / 解决问题 / 核心功能 / 商业模式 |
| `art-concept` | 美术概念 | shijue:视觉方向 / guige:技术规格 / qingdan:资产清单 / gongju:工具链 | `product-concept.json → name` + ` 美术概念` | 维度 / 风格 / 动画系统 / 工具链 |
| `game-design` | 游戏设计 | wanfa:核心玩法 / jingji:经济系统 / chengzhang:成长系统 / xushi:叙事 / meishu:美术方向 | `game-design-doc.json → name` | 核心玩法 / 经济 / 成长 / 叙事 / 美术 |
| `app-design` | App设计 | liucheng:用户流程 / jiegou:页面结构 / zujian:组件规范 / token:设计Token | `product-concept.json → name` | 核心流程 / 页面层级 / 组件库 / 设计规范 |

## 线框触发规则

| phase-id | 低保真触发条件 | 中保真触发条件 |
|---|---|---|
| `product-concept` | 「jingpin」列写入第1张卡片后 | 「gongneng」列写入第1张卡片后 |
| `art-concept` | 「shijue」列写入第1张卡片后（Q1答完） | 「guige」列写入第1张卡片后（Q3答完） |
| `game-design` | `core-loop-design` 节点完成后 | `art-direction` 节点完成后 |
| `app-design` | 「liucheng」列写入第1张卡片后 | 「jiegou」列写入第1张卡片后 |

## 线框内容规则（LLM特化层）

| phase-id | 低保真内容 | 中保真内容 |
|---|---|---|
| `product-concept` | App主界面骨架（导航栏+主要区块占位框） | 核心用户流程线框（含页面跳转箭头） |
| `art-concept` | 色盘+质感参考格（色块+文字标注风格关键词） | 资产规格示意图（各类资产尺寸比例对照表） |
| `game-design` | HUD草图（血量/分数/道具栏位置）+ 关卡布局草图（两块独立 SVG） | 完整游戏 UI 层级线框（主菜单→游戏中→结算） |
| `app-design` | 主屏幕骨架线框 | 核心页面线框集（3-5个关键页面） |

**保真度视觉规范：**
- 低保真：`stroke-width: 2`，`stroke: #666`，`fill: none`；文字用等宽字体+占位符（`X X X`）
- 中保真：`fill: #2a2a2a`；组件名文字标注（`font-size: 11px`）；尺寸标注用 dashed 线 + 数字

---

## 工具层：启动序列

调用时，将 `<phase-id>` 替换为实际阶段 ID（见阶段配置表）：

```
1. 确认目录存在：
   Bash: mkdir -p .allforai/concept-session/<phase-id>

2. 获取会话目录绝对路径：
   Read .allforai/bootstrap/bootstrap-profile.json → 读取 project_root 字段
   若字段不存在 → Bash: pwd 获取工作目录
   session_dir = <project_root>/.allforai/concept-session/<phase-id>

3. 判断首次/重复运行：
   尝试 Read .allforai/concept-session/<phase-id>/conclusion-kanban.html
   - 文件不存在（IOError）→ 首次：生成三个初始 HTML（见「HTML 初始模板」）
   - 文件存在 → 重复：
       读取 conclusion-kanban.html（保留已有卡片内容，后续追加）
       读取 mindmap.html（保留已有 SVG 节点树，后续追加）
       wireframes.html 总是重写为初始模板（重置）

4. 打开浏览器（严格顺序，非并行）：
   Step A: mcp__plugin_playwright_playwright__browser_navigate
           url = 'file://<session_dir>/conclusion-kanban.html'
   Step B: mcp__plugin_playwright_playwright__browser_evaluate
           script = "window.open('file://<session_dir>/mindmap.html','_blank')"
   Step C: mcp__plugin_playwright_playwright__browser_evaluate
           script = "window.open('file://<session_dir>/wireframes.html','_blank')"

5. 记录 pageId（全程使用）：
   mcp__plugin_playwright_playwright__browser_tabs
   → 按 URL 匹配 concept-session/<phase-id>/ 的3个页面（按打开顺序排列）：
     tab1_pageId = URL 含 conclusion-kanban.html 的页面
     tab2_pageId = URL 含 mindmap.html 的页面
     tab3_pageId = URL 含 wireframes.html 的页面
```

---

## LLM特化层：结论卡片内容生成

每次子阶段 Q&A 结论确认后，LLM 基于该轮实际结论生成如下 HTML（内容因项目而异）：

```
输入：
  - 本轮已确认的结论（用户选择 + 搜索证据）
  - 目标看板列的 slug（由各阶段 integration 段指定）

LLM 生成 <div class="card"> HTML：
  .card-meta：子阶段名称 + ISO 时间戳（e.g. "竞品调研 · 2026-05-09T10:30:00"）
  .card-title：一句话结论，≤20字，从本轮结论中提炼最关键结论
  .card-points：2-4条支撑数据点（来自搜索结果或用户确认，用 <br> 分隔）
  .card-source：搜索来源简写（如 "brave_web_search#3"）或 "用户确认"

示例输出（产品概念阶段，竞品调研列）：
<div class="card">
  <div class="card-meta">竞品调研 · 2026-05-09T10:30:00</div>
  <div class="card-title">竞品均缺乏情绪快速录入功能</div>
  <div class="card-points">· Day One 平均打开耗时 &gt;45s<br>· Notion 无移动端情绪标签<br>· 78% 用户睡前有记录意愿</div>
  <div class="card-source">brave_web_search#3 + 用户确认</div>
</div>
```

---

## LLM特化层：思维导图节点决策

每次结论确认后，LLM 决定新增节点的语义内容（不计算坐标，坐标由工具层算法承担）：

```
输入：
  - 本轮结论（关键词）
  - 当前思维导图已有节点树（从现有 mindmap.html 的 SVG <text> 标签中读取）

LLM 决策：
  1. 新节点标签文字：≤10字，来自结论最关键关键词
  2. 父节点选择：在已有节点树中选择语义最近的节点
  3. 节点类型：
     - 结构节点（fill: #2d3748，蓝灰）：默认，表示产品维度或模块
     - 结论节点（fill: #744210，橙色）：仅 game-design 阶段，表示关键设计决策

工具层坐标算法（LLM 不参与）：
  根节点 x=80，一级节点 x=320，二级节点 x=560，三级节点 x=800
  同级节点 y 均分，间距 80px；父节点中心 y = 其所有子节点 y 的均值
  节点尺寸：width=180，height=36，rx=6
  边：贝塞尔曲线，从父节点右边中点 → 子节点左边中点，控制点各偏移 60px
  SVG 总高度：max(400, 最深层子节点数 × 80 + 100)
```

---

## 工具层：结论更新序列

每次子阶段 Q&A 结论确认后执行（tab_pageId 来自启动序列 Step 5）：

```
1. 【LLM特化层】生成结论卡片 HTML（见「结论卡片内容生成」）
2. 读取现有 conclusion-kanban.html
   将新 <div class="card">...</div> 追加到 div#col-<slug> 内部
   若该列含 <p class="empty">—</p> 则先移除
   重写整个 conclusion-kanban.html

3. 【LLM特化层】决定思维导图新增节点（见「思维导图节点决策」）
4. 读取现有 mindmap.html，按坐标算法重新计算所有节点位置
   重写整个 mindmap.html（全量 SVG 重生成，不做增量 patch）

5. mcp__plugin_playwright_playwright__browser_navigate
   url = 'file://<session_dir>/conclusion-kanban.html'，page = tab1_pageId

6. mcp__plugin_playwright_playwright__browser_navigate
   url = 'file://<session_dir>/mindmap.html'，page = tab2_pageId

[仅当本次更新满足线框触发条件（见「线框触发规则」表）时，继续执行步骤 7-9]

7. 【LLM特化层】生成对应保真度内联 SVG 线框
   参考「线框内容规则」表中该阶段对应内容
   低保真视觉规范：stroke-width:2，stroke:#666，fill:none，文字用等宽字体
   中保真视觉规范：fill:#2a2a2a，组件名标注 font-size:11px，尺寸 dashed 线

8. 读取现有 wireframes.html：
   将当前 #main-content 的 SVG 提取并缩放为 200px 宽缩略图（保持宽高比，设置 SVG width="200" 并通过 viewBox 保持原始比例）
   追加到 #history div 内（包裹在 .history-item 中，添加时间戳文字）
   将新线框 SVG 写入 #main-content
   更新 .frame-label 文字为当前保真度 + 时间戳
   重写整个 wireframes.html

9. mcp__plugin_playwright_playwright__browser_navigate
   url = 'file://<session_dir>/wireframes.html'，page = tab3_pageId
```

---

## 工具层：结束序列

阶段所有 Q&A 完成后执行：

```
1. 确认 mindmap.html 已包含本阶段所有决策节点
2. mcp__plugin_playwright_playwright__browser_tabs → 确认3个 pageId 仍有效
3. mcp__plugin_playwright_playwright__browser_close  page = tab1_pageId
4. mcp__plugin_playwright_playwright__browser_close  page = tab2_pageId
5. mcp__plugin_playwright_playwright__browser_close  page = tab3_pageId
6. CLI 输出：
   "可视化文件已保存：
    看板：.allforai/concept-session/<phase-id>/conclusion-kanban.html
    导图：.allforai/concept-session/<phase-id>/mindmap.html
    线框：.allforai/concept-session/<phase-id>/wireframes.html"
```

---

## HTML 初始模板

### conclusion-kanban.html（首次运行时生成）

将 `{PHASE_LABEL}`、`{COL*}` 替换为阶段实际值（见阶段配置表）。
列数规则：art-concept 和 app-design 使用4列（省略第5列注释行）；product-concept 和 game-design 使用5列（保留第5列注释行并取消注释）：

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
    <div class="column"><div class="col-title">{COL1_NAME}</div><div id="col-{COL1_SLUG}"><p class="empty">—</p></div></div>
    <div class="column"><div class="col-title">{COL2_NAME}</div><div id="col-{COL2_SLUG}"><p class="empty">—</p></div></div>
    <div class="column"><div class="col-title">{COL3_NAME}</div><div id="col-{COL3_SLUG}"><p class="empty">—</p></div></div>
    <div class="column"><div class="col-title">{COL4_NAME}</div><div id="col-{COL4_SLUG}"><p class="empty">—</p></div></div>
    <!-- 5列阶段（product-concept / game-design）补充：
    <div class="column"><div class="col-title">{COL5_NAME}</div><div id="col-{COL5_SLUG}"><p class="empty">—</p></div></div>
    -->
  </div>
</body>
</html>
```

### mindmap.html（首次运行时生成）

`{ROOT_Y}` = `HEIGHT / 2 - 18`，`{ROOT_TEXT_Y}` = `HEIGHT / 2 + 6`。
初始 HEIGHT = 一级节点数 × 80 + 100（最小 400）。
`{L1_NODES_AND_EDGES}` 由 LLM 按算法生成，格式见注释：

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
    <!-- 根节点 -->
    <rect x="80" y="{ROOT_Y}" width="180" height="36" rx="6" fill="#3d5a80"/>
    <text x="170" y="{ROOT_TEXT_Y}" text-anchor="middle" fill="#e0e0e0" font-size="12" font-family="sans-serif">{ROOT_LABEL}</text>
    <!-- 一级节点示例（LLM 按坐标算法生成每个节点）：
    <path d="M 260,{ROOT_CY} C 320,{ROOT_CY} 320,{L1_CY} 320,{L1_CY}" stroke="#445566" fill="none"/>
    <rect x="320" y="{L1_Y}" width="180" height="36" rx="6" fill="#2d3748"/>
    <text x="410" y="{L1_TEXT_Y}" text-anchor="middle" fill="#e0e0e0" font-size="12" font-family="sans-serif">{L1_LABEL}</text>
    -->
    {L1_NODES_AND_EDGES}
  </svg>
</body>
</html>
```

### wireframes.html（每次运行时重置）

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
                    font-size: 10px; color: #555; text-align: center; }
    .history-item svg { display: block; margin: 0 auto 4px; }
    .placeholder { color: #333; text-align: center; padding: 40px; font-size: 13px; }
  </style>
</head>
<body>
  <h1>{PHASE_LABEL} · 线框图</h1>
  <div class="main-frame">
    <div class="frame-label">等待第一个线框生成...</div>
    <div id="main-content"><p class="placeholder">Q&amp;A 进行中，关键节点后自动生成</p></div>
  </div>
  <div id="history" class="history"></div>
</body>
</html>
```
