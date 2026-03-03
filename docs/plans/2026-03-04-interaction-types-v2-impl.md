# Interaction Types v2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 `interaction-types.md` 从 8 种类型（A-H）全量重写为三轴模型（37 种类型 + 平台矩阵 + 上下文预设），并同步更新引用它的三个下游技能文件。

**Architecture:** 三轴模型——第一轴：37 种交互类型（纯行为定义，无 UI 描述）；第二轴：每种类型内嵌 5 平台实现矩阵；第三轴：上下文预设（产品类型 × 用户属性）。设计文档见 `docs/plans/2026-03-04-interaction-types-v2-design.md`。

**Tech Stack:** Markdown 文档编写，无代码变更。所有变更仅限 `.md` 文件。

**关键约束：**
- 类型定义**不出现任何 UI 词汇**（布局、组件名、颜色等），只描述行为
- 不保留旧 A-H 别名，直接替换
- 每种类型的行为定义包含：用户意图 / 操作集合 / 数据状态 / 信息流向
- 平台矩阵覆盖 5 个平台：Web 桌面 / Mobile Web(H5) / iOS+Android 原生 / Windows 桌面 / TUI

---

## 受影响文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `product-design-skill/docs/interaction-types.md` | 全量重写 | 主文件，Tasks 1-9 |
| `product-design-skill/skills/screen-map.md` | 局部更新 | 枚举值 + 示例，Task 10 |
| `product-design-skill/skills/ui-design.md` | 局部更新 | 类型代号引用，Task 11 |
| `dev-forge-skill/skills/design-to-spec.md` | 局部更新 | 类型代号引用，Task 12 |

---

## Task 1: 重写文件头 + 设计原则 + 文档结构骨架

**文件：**
- 重写：`product-design-skill/docs/interaction-types.md`（清空重建）

**内容：** 写入以下完整内容作为骨架：

```markdown
# 页面交互类型体系 v2

> 本文档是页面交互类型的**单一事实来源**（Single Source of Truth）。
> 各阶段技能引用本文档，不重复定义类型。

## 引用关系

\`\`\`
docs/interaction-types.md（本文档 — 定义层）
  ↑ 引用
  ├── screen-map.md     → Step 1 推断 interaction_type，写入 screen-map.json
  ├── ui-design.md      → Step 4 按 interaction_type 生成视觉规格
  └── design-to-spec.md → Step 2 按 interaction_type 生成实现规格
\`\`\`

---

## 核心设计原则

### 原则一：行为层与表现层分离

**交互类型 = 行为契约**，只描述：
- 用户意图（用户想达成什么目标）
- 操作集合（用户能执行哪些操作）
- 数据状态（实体有哪些状态和流转规则）
- 信息流向（数据如何在用户和系统间流动）

**UI = 表现决策**，放在平台实现矩阵中，不属于类型定义。

> ❌ 错误：`布局：左侧树 + 右侧编辑区`（这是 UI）
> ✅ 正确：`实体有父子层级关系，操作需携带 parentId 上下文`（这是行为）

### 原则二：类型平台无关

同一交互类型在不同平台的 UI 实现可以完全不同，行为契约相同。

### 原则三：CRUD 的 U 有两种子形态

| 子形态 | 定义 | 典型操作 |
|--------|------|---------|
| 字段编辑（Edit） | 用户自由修改实体字段值 | 修改商品名称、价格、描述 |
| 状态流转（State Transition） | 触发预定义操作，实体状态跳转，无字段编辑 | 商品上架/下架、订单发货/取消 |

---

## 三轴模型总览

\`\`\`
第一轴：交互类型（行为定义层）
  37 种类型，8 个分类（MG/CT/EC/WK/RT/SB/SY/TU）
  每种类型：用户意图 + 操作集合 + 数据状态 + 信息流向

  ×

第二轴：平台实现矩阵（行为 → UI 映射）
  5 个平台：Web桌面 / Mobile Web / iOS+Android / Windows / TUI
  每种类型 × 每个平台：导航模式 / 内容展示 / 操作触发 / 写操作承载 / 平台特有能力

  ×

第三轴：上下文预设（影响类型分布与风格倾向）
  产品类型：电商 / 社交 / IM / 社区 / 工具 / 办公 / 金融 / 内容
  用户属性：C端消费者 / B端商户 / 内部办公
\`\`\`

### 类型代号体系

| 前缀 | 分类 | 数量 | 代号范围 |
|------|------|------|---------|
| MG | 管理/CRUD | 9 | MG1–MG8（含 MG2 子类型） |
| CT | 内容消费 | 8 | CT1–CT8 |
| EC | 电商交易 | 3 | EC1–EC3 |
| WK | 协作办公 | 7 | WK1–WK7 |
| RT | 通讯实时 | 4 | RT1–RT4 |
| SB | 审核提交 | 1 | SB1 |
| SY | 引导系统 | 2 | SY1–SY2 |
| TU | TUI/CLI | 4 | TU1–TU4 |

### screen-map 标注格式

单一类型：
\`\`\`json
{ "interaction_type": "MG3" }
\`\`\`

组合类型（用数组，首元素为主类型）：
\`\`\`json
{ "interaction_type": ["MG5", "MG3"] }
\`\`\`

---

## 第一轴 + 第二轴：交互类型定义与平台矩阵

[MG 类型内容 — Task 2]

[CT 类型内容 — Task 3]

[EC 类型内容 — Task 4]

[WK 类型内容 — Task 5]

[RT / SB / SY / TU 类型内容 — Task 6]

---

## 第三轴：上下文预设

[上下文预设内容 — Task 7]

---

## screen-map 推断规则

[推断规则内容 — Task 8]

---

## 跨端分布示例

[示例内容 — Task 9]

---

## 各阶段使用指南

[使用指南内容 — Task 9]
```

**验证：** 文件存在，骨架占位符完整，无旧 A-H 内容。

**提交：**
```bash
git add product-design-skill/docs/interaction-types.md
git commit -m "docs(interaction-types): v2 骨架 + 设计原则 + 三轴模型总览"
```

---

## Task 2: 写 MG 类型（管理/CRUD，9 种）

**文件：**
- 修改：`product-design-skill/docs/interaction-types.md`（替换 `[MG 类型内容 — Task 2]`）

**写入内容结构（每种类型格式）：**

```markdown
### MG1 只读列表 `readonly-list`

**用户意图：** 浏览、筛选、查找数据，无修改意图。

**操作集合：** 查询（分页/排序）、多维筛选、搜索、导出、点击进入详情。

**数据状态：** 无状态机，数据只读。

**信息流向：** `GET list(params)` → 展示 → 可选 `GET detail(id)` 跳转。

**平台矩阵：**

| 维度 | Web 桌面 | Mobile Web | iOS/Android | Windows | TUI |
|------|---------|------------|-------------|---------|-----|
| 进入方式 | 侧边栏菜单 | 底部 Tab / 顶部返回 | 底部 Tab / 导航栈 | 左侧导航树 | TU2 菜单选择 |
| 内容展示 | 多列数据表格 | 单列卡片列表（2-3 字段） | UITableView / RecyclerView | DataGrid 控件 | 格式化文本表格 |
| 筛选操作 | 顶部 Filter Bar 常驻 | 底部 Sheet 展开筛选 | SearchController + Sheet | 顶部筛选工具栏 | `--filter` 参数 |
| 分页方式 | 分页器（Pagination） | 上拉加载更多 | 下拉刷新 + 上拉加载 | 分页器 | 分批输出 / `--limit` |
| 导出 | 工具栏按钮 | 无 / 系统分享 | 系统分享 Sheet | 菜单栏 文件→导出 | `> output.csv` 重定向 |
| 平台特有 | 多列排序点击列头 | 触摸友好大行高 | 系统搜索集成 | 键盘快捷键导航 | ANSI 颜色高亮字段 |
```

**完整需覆盖的 9 种类型：**

```
MG1 只读列表
MG2 CRUD 实体集群（含子类型说明：MG2-L / MG2-D / MG2-C / MG2-E / MG2-ST）
MG3 状态机驱动
MG4 审批流
MG5 主从详情
MG6 树形管理
MG7 仪表盘
MG8 配置页
```

**MG2 子类型说明格式（写在 MG2 定义内）：**

```markdown
MG2 实体集群由以下子屏组成，screen-map 可精确标注子类型：

| 子屏 | 代号 | 行为摘要 |
|------|------|---------|
| 实体列表 | MG2-L | 可分页查询，提供操作入口 |
| 实体详情 | MG2-D | 只读展示完整字段，触发操作 |
| 新建表单 | MG2-C | 空表单 → 提交 → 创建实体 |
| 字段编辑 | MG2-E | 表单回填旧值 → 修改 → 提交更新 |
| 状态流转 | MG2-ST | 触发特定操作使实体状态跳转，无表单 |
```

**验证：** 9 种类型全部写完，每种包含四要素 + 平台矩阵，无 UI 描述混入行为定义。

**提交：**
```bash
git add product-design-skill/docs/interaction-types.md
git commit -m "docs(interaction-types): MG 类型完成（9 种管理/CRUD 类型 + 平台矩阵）"
```

---

## Task 3: 写 CT 类型（内容消费，8 种）

**文件：**
- 修改：`product-design-skill/docs/interaction-types.md`（替换 `[CT 类型内容 — Task 3]`）

**完整需覆盖的 8 种类型（每种格式同 Task 2）：**

```
CT1 Feed 流/信息流
CT2 内容阅读页
CT3 个人主页/Profile
CT4 卡片探索（Swipe 模式）
CT5 媒体播放器
CT6 相册/图库
CT7 搜索结果页
CT8 Story/短视频流
```

**平台矩阵特别注意：**
- CT1 Feed 流：TUI 平台 = `TU3 日志流`模式（文本 append，无图片）；Windows 桌面可能不适用（标注 N/A 并说明）
- CT4 卡片探索（Swipe）：TUI = N/A（手势无法映射到键盘，说明不适用）
- CT5 媒体播放器：TUI = 音频波形可视化（如 `cmus`），视频 = N/A
- CT8 Story/短视频：TUI = N/A

**验证：** 8 种类型全部写完，不适用平台明确标 N/A 并附原因。

**提交：**
```bash
git add product-design-skill/docs/interaction-types.md
git commit -m "docs(interaction-types): CT 类型完成（8 种内容消费类型 + 平台矩阵）"
```

---

## Task 4: 写 EC 类型（电商交易，3 种）

**文件：**
- 修改：`product-design-skill/docs/interaction-types.md`（替换 `[EC 类型内容 — Task 4]`）

**完整需覆盖的 3 种类型：**

```
EC1 商品详情页
EC2 购物车/结算清单
EC3 订单追踪时间线
```

**行为定义要点：**
- EC1：核心行为是"规格选择影响价格/库存"——这是独特的联动行为，不同于普通详情页
- EC2：本地状态（选中/数量）与服务端（库存/价格）的实时同步是关键行为
- EC3：纯只读时间线，与 MG3 状态机的区别是"无任何操作，只展示历史轨迹"

**平台矩阵特别注意：**
- EC1 商品详情：TUI = N/A（图片/规格选择无法在命令行呈现，明确标注）
- EC2 购物车：TUI = N/A
- EC3 订单追踪：TUI 可用（文本时间线）

**验证：** 3 种类型行为定义清晰，EC1 与 MG5 主从详情的区别在定义中体现。

**提交：**
```bash
git add product-design-skill/docs/interaction-types.md
git commit -m "docs(interaction-types): EC 类型完成（3 种电商交易类型 + 平台矩阵）"
```

---

## Task 5: 写 WK 类型（协作办公，7 种）

**文件：**
- 修改：`product-design-skill/docs/interaction-types.md`（替换 `[WK 类型内容 — Task 5]`）

**完整需覆盖的 7 种类型：**

```
WK1 对话/IM
WK2 频道/群组
WK3 文档编辑
WK4 画布/白板
WK5 看板（Kanban）
WK6 甘特图
WK7 文件管理器
```

**行为定义要点：**
- WK1 vs WK2：WK1 是点对点/小群实时通讯，WK2 有频道权限管理 + 固定消息 + 话题等频道特有概念
- WK3：关键行为是"OT/CRDT 实时协同 + conflict resolution"，这是与 MG8 配置页的本质区别
- WK4：坐标系操作（绝对定位）vs 文档流（WK3），这是行为层的核心差异
- WK5：拖拽跨列 = 状态变更，这是 Kanban 的核心行为
- WK6：时间段拖拽 = 任务时间字段变更，依赖关系约束是关键行为

**平台矩阵特别注意：**
- WK4 画布/白板：TUI = N/A（自由坐标无法在字符终端实现）
- WK6 甘特图：TUI 可用（字符甘特图，如 `gantt` 命令行工具）
- WK7 文件管理器：TUI 完全适用（如 `ranger`、`mc` 等 TUI 文件管理器是典型形态）

**验证：** 7 种类型写完，WK3 文档编辑行为定义中无"富文本"等 UI 词汇（富文本是实现方式，不是行为）。

**提交：**
```bash
git add product-design-skill/docs/interaction-types.md
git commit -m "docs(interaction-types): WK 类型完成（7 种协作办公类型 + 平台矩阵）"
```

---

## Task 6: 写 RT / SB / SY / TU 类型（共 11 种）

**文件：**
- 修改：`product-design-skill/docs/interaction-types.md`（替换 `[RT / SB / SY / TU 类型内容 — Task 6]`）

**完整需覆盖的 11 种类型：**

```
RT1 通话界面
RT2 直播间
RT3 邮件收发
RT4 通知中心

SB1 审核型提交（特别重要：需说明与 MG4 审批流的关系）

SY1 Onboarding/引导流程
SY2 向导/多步表单

TU1 命令行交互
TU2 交互式菜单（TUI）
TU3 日志流/监控
TU4 进度/任务流
```

**SB1 行为定义（需特别完整）：**

```markdown
### SB1 审核型提交

**用户意图：** 将自己创建的内容/实体提交给平台审核，不立即生效，等待审核结果后才能上线。

**操作集合：**
- 创建草稿（可保存不提交）
- 提交审核（进入待审队列）
- 查看审核状态（待审/审核中/通过/驳回）
- 驳回后查看驳回原因 + 修改内容 + 重新提交
- 撤回已提交申请（回到草稿状态）

**数据状态：**
`草稿 → 待审核 → 审核中 → 已通过 / 已驳回 → (修改) → 待审核`

**信息流向：** 提交操作 → 写入 MG4 审批队列；驳回通知 → 推送给提交方；通过 → 实体生效。

**与 MG4 的关系：** SB1（提交方视角）和 MG4（审核方视角）是同一个工作流的两端。同一个业务工作流在 screen-map 中会出现两种类型标注，分别在不同端的界面上。

**典型场景：** 商品上架、内容发布、广告投放、商家入驻、提现申请、KYC 认证
```

**TU 类型特别注意：**
- TU1-TU4 的"平台矩阵"格式特殊——TUI 类型本身就是平台，矩阵应改为"Shell 环境"维度：
  - Linux/macOS Terminal（bash/zsh）
  - Windows Terminal（PowerShell/cmd）
  - 嵌入式终端（VS Code Terminal / IDE）
  - SSH 远程终端

**验证：** 11 种类型写完，SB1 与 MG4 的关系说明清晰，TU 类型的平台矩阵维度调整合理。

**提交：**
```bash
git add product-design-skill/docs/interaction-types.md
git commit -m "docs(interaction-types): RT/SB/SY/TU 类型完成（11 种类型 + 平台矩阵）"
```

---

## Task 7: 写上下文预设（第三轴）

**文件：**
- 修改：`product-design-skill/docs/interaction-types.md`（替换 `[上下文预设内容 — Task 7]`）

**格式（每种产品类型）：**

```markdown
### 电商平台

| 端 | 用户属性 | 高频类型（占比 > 20%） | 中频类型（5–20%） | 低频类型（< 5%） |
|---|---------|----------------------|-----------------|----------------|
| 消费者 App | C端 | CT1(Feed) EC1(商品详情) | CT7(搜索) EC2(购物车) | EC3(追踪) CT3(Profile) |
| 消费者 Web | C端 | CT7(搜索结果) EC1(商品详情) | CT1(Feed) EC2(购物车) | MG1(订单) |
| 商家后台 | B端 | MG2(CRUD集群) SB1(审核提交) | MG3(状态机) SY2(向导) | MG4(审批) MG7(仪表盘) |
| 运营后台 | 内部 | MG4(审批) MG3(状态机) | MG1(只读列表) MG7(仪表盘) | MG2(CRUD) |

**导航结构：** 消费者端底部 Tab（首页/分类/购物车/我的）；后台侧边栏。
**信息密度：** 消费者端低密度大图；后台高密度数据表。
```

**需覆盖的产品类型（8 种）：**
```
电商平台 / 社交平台 / IM（即时通讯）/ 社区平台
工具类产品 / 办公类产品 / 金融平台 / 内容/媒体平台
```

**用户属性预设（3 种）：**

```markdown
## 用户属性预设

### C端消费者
- **信息密度：** 低（大图、大字号、留白充足）
- **错误容忍：** 高（友好提示，自动重试，避免技术词汇）
- **操作频率：** 低频偶发（每次操作间隔长）
- **学习成本：** 极低（无需培训即用）
- **UI 倾向：** 视觉引导为主，减少文字说明

### B端商户/企业
- **信息密度：** 中（数据可见但不拥挤）
- **错误容忍：** 中（有明确错误提示，允许重试）
- **操作频率：** 中频（每日使用，重复固定操作）
- **学习成本：** 中（可接受简短引导）
- **UI 倾向：** 效率优先，允许少量专业词汇

### 内部办公用户
- **信息密度：** 高（数据表格密集，多列多行）
- **错误容忍：** 低（精确错误码，技术细节可见）
- **操作频率：** 高频重复（批量操作、快捷键需求高）
- **学习成本：** 高（可接受系统培训）
- **UI 倾向：** 功能完整 > 视觉美观，键盘操作优先
```

**验证：** 8 种产品类型 × 3 种用户属性全部写完，频率标注使用高/中/低而非具体百分比。

**提交：**
```bash
git add product-design-skill/docs/interaction-types.md
git commit -m "docs(interaction-types): 上下文预设完成（8 种产品类型 + 3 种用户属性）"
```

---

## Task 8: 写 screen-map 推断规则

**文件：**
- 修改：`product-design-skill/docs/interaction-types.md`（替换 `[推断规则内容 — Task 8]`）

**格式：** 优先级从高到低的规则链，命中即停止。新规则需覆盖所有 37 种类型的推断入口。

```markdown
## screen-map 推断规则

> screen-map Step 1 梳理界面时，根据 screen 的 actions / name / entities 自动推断 interaction_type。
> 优先级从高到低，命中即停止。

### 规则链

**P1（最高优先级）— 特殊关键词匹配：**
- screen.name 含 `dashboard / overview / 报表 / 数据中心` → **MG7**
- screen.name 含 `onboarding / 引导 / 新手 / 欢迎` → **SY1**
- screen.name 含 `直播 / live / livestream` → **RT2**
- screen.name 含 `通话 / call / video-call` → **RT1**

**P2 — 实时通讯类型：**
- 有 `send-message / receive-message / typing-indicator` actions → **WK1**（对话/IM）
- 有 `send-message` + `manage-members / pin-message` → **WK2**（频道/群组）

**P3 — 审核相关：**
- 有 `approve / reject / audit / review` actions → **MG4**（审批流）
- 有 `submit-for-review / withdraw-submission` actions → **SB1**（审核型提交）

**P4 — 电商特有：**
- 有 `add-to-cart / select-sku / purchase` actions → **EC1**（商品详情页）
- 有 `update-quantity / apply-coupon / checkout` actions → **EC2**（购物车）
- screen.name 含 `order-tracking / 物流 / 快递` 且无写操作 → **EC3**（订单追踪）

**P5 — 状态机 / CRUD 区分：**
- 有状态操作（ship/cancel/freeze/activate/suspend）且**无** create/edit → **MG3**（状态机驱动）
- 有 `create + edit + delete` → **MG2**（CRUD 实体集群）
- 有 `parentId / children / treeData` 字段且有 CRUD → **MG6**（树形管理）

**P6 — 主从 / 配置 / 向导：**
- 有嵌套子实体列表（Tabs / 子表） → **MG5**（主从详情）
- screen.name 含 `settings / config / profile / 设置 / 配置` 且无列表 → **MG8**（配置页）
- 有 `next-step / prev-step / submit-wizard` actions → **SY2**（向导多步表单）

**P7 — 内容消费类：**
- 有 `swipe-left / swipe-right / like-or-skip` actions → **CT4**（卡片探索）
- 有 `play / pause / seek` actions → **CT5**（媒体播放器）
- 有 `view-story / next-story` actions → **CT8**（Story/短视频流）
- 有 `follow / like / share` actions 且数据为列表 → **CT1**（Feed 流）
- 有 `follow / share` 且数据为单一用户 → **CT3**（个人主页）
- 有 `search / filter` 且无写操作 → **CT7**（搜索结果页）
- screen 为文章/帖子详情，actions 仅有 `like / share / comment` → **CT2**（内容阅读）

**P8 — 协作办公类：**
- 有 `drag-card / move-column` actions → **WK5**（看板）
- 有 `drag-timeline / set-dependency` actions → **WK6**（甘特图）
- 有 `upload-file / move-file / rename-file` + 树形结构 → **WK7**（文件管理器）
- 有 `compose / reply / forward` actions → **RT3**（邮件收发）
- 有 `mark-read / dismiss-notification` actions → **RT4**（通知中心）
- 有 `rich-text-edit / insert-block / collaborative-cursor` → **WK3**（文档编辑）
- 有 `draw / connect-nodes / drag-canvas` → **WK4**（画布/白板）

**P9 — TUI 类（仅当 platform = tui）：**
- 有菜单导航交互 → **TU2**
- 有实时日志流输出 → **TU3**
- 有多步骤进度展示 → **TU4**
- 默认 → **TU1**

**P10（默认兜底）：**
- actions 仅有 `view / filter / search / export` → **MG1**（只读列表）
- 以上均不命中 → **MG1**（只读列表，兜底）
```

**验证：** 规则链能覆盖所有 37 种类型的入口，无死角；同一规则链不会同时命中两种类型（互斥）。

**提交：**
```bash
git add product-design-skill/docs/interaction-types.md
git commit -m "docs(interaction-types): screen-map 推断规则完成（37 种类型推断链）"
```

---

## Task 9: 写跨端分布示例 + 使用指南

**文件：**
- 修改：`product-design-skill/docs/interaction-types.md`（替换最后两个占位符）

**跨端分布示例（三个实体）：**

直接从设计文档 `docs/plans/2026-03-04-interaction-types-v2-design.md` 的"跨端分布示例"章节提取，整理成完整格式写入。包含：
- 操作日志（8 行矩阵）
- 商品（10 行矩阵）
- 订单（9 行矩阵）

**使用指南（三个阶段）：**

```markdown
## 各阶段使用指南

### screen-map 阶段

**输入：** task-inventory.json → screen.actions / screen.name / entities
**动作：** 按上方推断规则，为每个 screen 标注 `interaction_type`，写入 screen-map.json
**输出：** screen-map.json 中每个 screen 增加 `interaction_type` 字段

### ui-design 阶段

**输入：** screen-map.json（含 interaction_type）
**动作：** 按 interaction_type 选择推荐布局模式（各类型布局模式见 ui-design.md）
**注意：** interaction_type 决定行为框架，具体视觉细节由产品类型 + 用户属性预设决定

### design-to-spec 阶段

**输入：** screen-map.json（含 interaction_type）+ project-manifest.json（技术栈）
**动作：** 按 interaction_type × 技术栈，生成实现级规格（组件选型 / Service 签名）
**注意：** 技术栈映射表维护在 design-to-spec.md 中，本文档只定义行为契约
```

**验证：** 三个实体示例完整，使用指南三阶段清晰，占位符全部替换完毕，文档无 `[...内容 — Task N]` 字样残留。

**提交：**
```bash
git add product-design-skill/docs/interaction-types.md
git commit -m "docs(interaction-types): v2 完整版 — 示例 + 使用指南，全文档写完"
```

---

## Task 10: 更新 screen-map.md

**文件：**
- 修改：`product-design-skill/skills/screen-map.md`

**需要修改的位置（grep 确认行号后修改）：**

```bash
grep -n "interaction_type\|readonly-list\|full-crud\|state-machine\|approval\|master-detail\|tree-crud\|dashboard\|config-form" \
  product-design-skill/skills/screen-map.md
```

**修改内容：**

1. **Schema 文档中的枚举值**（原 line ~378）：
   - 旧：`readonly-list / full-crud / state-machine / approval / master-detail / tree-crud / dashboard / config-form`
   - 新：`MG1 / MG2(MG2-L/D/C/E/ST) / MG3 / MG4 / MG5 / MG6 / MG7 / MG8 / CT1-CT8 / EC1-EC3 / WK1-WK7 / RT1-RT4 / SB1 / SY1-SY2 / TU1-TU4`

2. **示例 JSON 中的值**（原 line ~315, ~491）：
   - `"interaction_type": "readonly-list"` → `"interaction_type": "MG1"`
   - `"interaction_type": "state-machine"` → `"interaction_type": "MG3"`

3. **推断规则描述文本**（原 line ~301, ~306）：
   - 保留引用说明，更新为新代号体系

**验证：** `grep "readonly-list\|full-crud\|state-machine\|approval\|master-detail\|tree-crud\|dashboard\|config-form" product-design-skill/skills/screen-map.md` 结果为空。

**提交：**
```bash
git add product-design-skill/skills/screen-map.md
git commit -m "fix(screen-map): 更新 interaction_type 为 v2 编码体系（MG/CT/EC/WK/RT/SB/SY/TU）"
```

---

## Task 11: 更新 ui-design.md

**文件：**
- 修改：`product-design-skill/skills/ui-design.md`

**需要修改的位置：**

```bash
grep -n "readonly-list\|full-crud\|state-machine\|approval\|master-detail\|tree-crud\|dashboard\|config-form" \
  product-design-skill/skills/ui-design.md
```

**修改内容：**

1. **布局模式对照表**（原 line ~249-258 的映射表）：
   - 将 8 行旧代号全部替换为新代号（MG1-MG8 + 新增类型各自的布局说明）
   - 新增类型的布局说明按照 interaction-types.md 平台矩阵中的"内容展示"和"写操作承载"维度填写

2. **一致性检测规则**（原 line ~363-367）：
   - 代号替换：`readonly-list` → `MG1`，`full-crud` → `MG2` 等

3. **示例 JSON**（原 line ~487）：
   - `"interaction_type": "state-machine"` → `"interaction_type": "MG3"`

**验证：** `grep "readonly-list\|full-crud" product-design-skill/skills/ui-design.md` 结果为空。

**提交：**
```bash
git add product-design-skill/skills/ui-design.md
git commit -m "fix(ui-design): 更新 interaction_type 为 v2 编码体系"
```

---

## Task 12: 更新 design-to-spec.md

**文件：**
- 修改：`dev-forge-skill/skills/design-to-spec.md`

**需要修改的位置：**

```bash
grep -n "readonly-list\|full-crud\|state-machine\|approval\|master-detail\|tree-crud\|dashboard\|config-form\|interaction_type" \
  dev-forge-skill/skills/design-to-spec.md
```

**修改内容：**

1. **类型引用文本**：将所有旧代号替换为新代号
2. **技术栈映射表的类型列**：更新为新代号（映射表结构不变，只改类型标识）
3. **兼容说明**（原 line ~227）：删除"若 screen-map.json 中无 interaction_type 字段（旧版兼容）"这段兼容逻辑，因为 v2 不保留兼容

**验证：** `grep "readonly-list\|full-crud\|旧版兼容" dev-forge-skill/skills/design-to-spec.md` 结果为空。

**提交：**
```bash
git add dev-forge-skill/skills/design-to-spec.md
git commit -m "fix(design-to-spec): 更新 interaction_type 为 v2 编码体系，移除旧版兼容逻辑"
```

---

## 完成验证

所有任务完成后执行：

```bash
# 确认旧代号在所有相关文件中已清除
grep -r "readonly-list\|full-crud\|state-machine\|tree-crud\|config-form\|master-detail" \
  product-design-skill/docs/ \
  product-design-skill/skills/screen-map.md \
  product-design-skill/skills/ui-design.md \
  dev-forge-skill/skills/design-to-spec.md

# 期望输出：空（无匹配）

# 确认新代号存在
grep -c "MG1\|MG2\|MG3\|CT1\|EC1\|WK1\|SB1\|TU1" \
  product-design-skill/docs/interaction-types.md

# 期望输出：数字 > 30
```
