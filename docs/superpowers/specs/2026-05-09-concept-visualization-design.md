# Concept Visualization Design

## Overview

在所有概念阶段（产品概念、美术概念、游戏设计、App设计），CLI Q&A 进行的同时，Claude 生成并持续更新3个 HTML 可视化文件，通过 Playwright 在浏览器里实时展示进展。

**核心原则：**
- Q&A 交互**只在命令行**完成，HTML 是纯展示层
- 3个独立 HTML 文件，每个专注一件事
- Playwright 始终可用，无降级设计

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

```
阶段启动：
  browser_navigate → conclusion-kanban.html  (Tab 1)
  browser_navigate → mindmap.html            (Tab 2)
  browser_navigate → wireframes.html         (Tab 3)

每轮结论确认后：
  重写对应 HTML 文件
  browser_navigate 刷新对应 Tab（navigate to same path = refresh）

阶段完成：
  browser_close 关闭所有 Tab
  HTML 文件保留，供后续阶段 Context Pull
```

---

## HTML Files Specification

### 1. conclusion-kanban.html

**用途：** 收纳每个子阶段的确认结论，纯展示，无交互。

**视觉风格：** 深色主题，列宽自适应，卡片按时间序纵向堆叠。

**卡片结构：**
```
┌─────────────────────────┐
│ [子阶段标签]  [时间戳]   │
│ 结论标题（粗体）          │
│ ─────────────────────── │
│ · 关键数据点 1           │
│ · 关键数据点 2           │
│ [来源：搜索/用户确认]     │
└─────────────────────────┘
```

**各阶段列定义：**

| 阶段 | 列1 | 列2 | 列3 | 列4 | 列5 |
|------|-----|-----|-----|-----|-----|
| 产品概念 | 问题 | 用户 | 竞品洞察 | 核心功能 | 商业模式 |
| 美术概念 | 视觉方向 | 技术规格 | 资产清单 | 工具链 | — |
| 游戏设计 | 核心玩法 | 经济系统 | 成长系统 | 叙事 | 美术方向 |
| App设计 | 用户流程 | 页面结构 | 组件规范 | 设计Token | — |

**更新时机：** 每个子阶段 Q&A 结论确认后立即追加对应列的卡片，重写整个 HTML 文件。

---

### 2. mindmap.html

**用途：** 展示产品/游戏/设计的结构关系，随决策演化动态添加节点。

**视觉风格：** SVG 树状图，深色背景，节点用圆角矩形，边用曲线连接。

**节点类型：**
- **根节点**：产品/游戏名称（阶段开始时创建）
- **结构节点**：功能模块、页面、系统（蓝色，随决策添加）
- **结论节点**（游戏设计专用）：关键设计决策的具体内容（橙色，展开为子树）

**各阶段思维导图结构：**

**产品概念：**
```
产品名
  ├─ 核心用户
  │    └─ [用户画像结论]
  ├─ 解决的问题
  ├─ 核心功能模块
  │    ├─ 功能A
  │    └─ 功能B
  └─ 商业模式
```

**美术概念：**
```
游戏美术
  ├─ 维度（2D/3D/2.5D）
  ├─ 风格（cartoon/pixel/...）
  │    └─ 技术规格
  ├─ 动画系统
  └─ 工具链
```

**游戏设计（含结论节点）：**
```
游戏名
  ├─ 核心玩法环（结论节点：展开为具体机制）
  ├─ 经济系统
  │    ├─ 货币体系
  │    └─ Sink/Source
  ├─ 成长系统
  ├─ 叙事
  └─ 美术方向
```

**App设计：**
```
App名
  ├─ 核心流程
  │    └─ [页面序列]
  ├─ 页面层级
  ├─ 组件库
  └─ 设计规范
```

**更新时机：** 与 conclusion-kanban.html 同步，每轮结论确认后添加对应节点，重写整个 HTML 文件。

---

### 3. wireframes.html

**用途：** 阶段性注入线框草图，早期低保真激发想象，后期中保真验证概念。

**视觉风格：** 双区布局。
- 上方：当前最新线框（大图展示）
- 下方：历史版本缩略图时间轴

**保真度定义：**

| 阶段 | 触发时机 | 保真度 | 风格 |
|------|---------|--------|------|
| 早期（前3个子阶段结论后） | 首次触发 | 低保真 | SVG手绘感：粗线条、无填充、占位文字 |
| 后期（核心功能/玩法确认后） | 再次触发 | 中保真 | 灰度色块、组件名标注、尺寸标注 |

**各阶段线框内容：**

- **产品概念**：App主界面骨架 → 核心流程线框
- **美术概念**：风格参考布局 → 资产规格示意图
- **游戏设计**：HUD/UI 草图 + 关卡布局草图（两个独立区块）
- **App设计**：主屏幕线框 → 关键页面线框集

**更新时机：** 不是每轮更新，仅在关键节点触发（见触发时机列）。

---

## Shared Protocol

新增 `knowledge/capabilities/concept-visualization.md`，定义所有概念阶段 skill 共同遵守的协议。所有涉及的 skill/capability 文件在对应位置引用此协议。

### 启动序列

```
## Concept Visualization — 启动

1. 读取阶段配置（phase-id、列定义、思维导图根节点）
2. 创建目录：mkdir -p .allforai/concept-session/<phase-id>/
3. 生成三个初始 HTML（空壳：含阶段标题、列定义、根节点，无卡片/无线框）
4. Playwright 打开：
   browser_navigate(conclusion-kanban.html) → Tab 1
   browser_navigate(mindmap.html)            → Tab 2
   browser_navigate(wireframes.html)         → Tab 3
5. 开始 CLI Q&A
```

### 每轮结论更新序列

```
## Concept Visualization — 结论更新

触发：子阶段 Q&A 完成，结论确认

1. 生成结论卡片 HTML 片段（标题 + 数据点 + 来源）
2. 重写 conclusion-kanban.html（追加卡片到对应列）
3. 计算思维导图新增节点
4. 重写 mindmap.html（添加节点 + 连线）
5. browser_navigate 刷新 Tab 1（看板）
6. browser_navigate 刷新 Tab 2（思维导图）

[若到达线框触发节点]
7. 生成对应保真度的 SVG 线框
8. 重写 wireframes.html（追加到时间轴，更新主展示区）
9. browser_navigate 刷新 Tab 3（线框）
```

### 结束序列

```
## Concept Visualization — 结束

1. 最终 mindmap.html 写入完整结构（所有节点）
2. browser_close 所有 Tab
3. 在 CLI 输出文件路径，供用户事后查阅
4. HTML 文件保留在 .allforai/concept-session/<phase-id>/，
   供后续节点 Context Pull（如 art-spec-design 读取 art-concept 的结论看板）
```

---

## Files to Modify

| 文件 | 改动类型 | 改动内容 |
|------|---------|---------|
| `knowledge/capabilities/concept-visualization.md` | **新增** | 共享协议全文 + 各阶段配置表 + HTML模板 |
| `knowledge/capabilities/product-concept.md` | 修改 | 每个子阶段末尾添加「→ Concept Visualization 更新」调用 |
| `skills/art-concept.md` | 修改 | Step 0启动序列 + Step 1-4每步结论后添加更新调用 |
| `knowledge/capabilities/game-design.md` | 修改 | 每个game-design节点执行完成后添加更新调用 |
| `knowledge/capabilities/ui-design.md` | 修改 | 各子阶段末添加更新调用（App设计流程） |

---

## Data Flow

```
CLI Q&A 结论
    │
    ▼
concept-visualization.md 协议
    │
    ├──▶ conclusion-kanban.html  （Playwright Tab 1 刷新）
    ├──▶ mindmap.html            （Playwright Tab 2 刷新）
    └──▶ wireframes.html         （关键节点，Playwright Tab 3 刷新）
    
后续节点 Context Pull：
    art-spec-design ◀── art-concept/conclusion-kanban.html
    game-design-finalize ◀── game-design/mindmap.html
```

---

## Constraints

- Playwright MCP 始终可用（`mcp__plugin_playwright_playwright__*`），无降级
- HTML 文件每次整页重写（非 DOM patch），简化实现
- SVG 由 Claude 内联生成，无外部图表库依赖
- 线框保真度由 Claude 判断触发，不需要用户显式触发
