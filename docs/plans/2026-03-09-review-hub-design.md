# Review Hub — 统一审核站点设计

> Design approved 2026-03-09

## Problem

产品设计阶段有 5 个独立审核服务器（concept:18900, map:18901, wireframe:18902, ui:18903, data-model:18904），每个独占一个端口、自动弹浏览器。用户频繁切换窗口，无法回看之前阶段的产物。开发阶段的规格（design.md）没有可视化。

## Solution: Unified Review Hub

一个 Python HTTP 服务器（`review_hub_server.py`），一个端口（18900），6 个 tab。通过 `/review` 命令启动，打印 URL，不自动弹浏览器。

### 站点结构

```
http://localhost:18900/
├── /                    # 首页：6 个 tab 入口卡片 + 产物状态
├── /concept             # 概念脑图
├── /map                 # 产品地图脑图（含共性模式分支）
├── /data-model          # 数据模型脑图
├── /wireframe           # 线框：左树 + 右预览面板
├── /ui                  # UI：左树 + 右预览面板
├── /spec                # 开发规格脑图
└── /api/...             # 各 tab 的反馈 API
```

### 页面布局

**共享顶部导航栏：**
```
┌──────────────────────────────────────────────────────┐
│  Review Hub    [概念] [地图] [数据模型] [线框] [UI] [规格]  │
│                 ●      ●      ●         ●     ○    ○     │
└──────────────────────────────────────────────────────┘
```
- ● 有产物（可点击）
- ○ 无产物（灰显不可点击）
- 当前 tab 高亮

**脑图类 tab（概念/地图/数据模型/规格）：**
```
┌─────────────────────────────────────┐
│  [导航栏]                            │
├─────────────────────────────────────┤
│                                     │
│          脑图（径向/树形）            │
│                                     │
├─────────────────────────────────────┤
│  评论面板：节点评论 + 状态 + 提交     │
└─────────────────────────────────────┘
```

**预览类 tab（线框/UI）：**
```
┌─────────────────────────────────────┐
│  [导航栏]                            │
├──────────────────┬──────────────────┤
│                  │                  │
│  屏幕树（左）     │  预览+评论（右）  │
│  替代 dashboard  │  线框/UI iframe  │
│  卡片网格        │  + pin 评论      │
│                  │                  │
└──────────────────┴──────────────────┘
```

### 6 个 Tab 定义

#### Tab 1: 概念

```
产品概念
├── 定位：一句话描述
├── 目标用户
│   ├── 用户1：痛点 + 场景
│   └── 用户2：痛点 + 场景
├── 价值主张
│   └── 核心差异点
├── 商业模式
│   └── 收入来源 + 定价
└── 创新概念
    └── 关键机制
```

数据源：`product-concept/product-concept.json`
反馈存储：`concept-review/review-feedback.json`

#### Tab 2: 地图

```
产品地图
├── R001 商户 [primary]
│   ├── 核心任务
│   │   ├── T001 查看订单列表 [R·高频]
│   │   └── T002 创建订单 [C·高频·中风险]
│   └── 基本任务
│       └── T005 删除订单 [D·低频·高风险]
├── R002 运营管理员 [internal]
│   └── ...
├── 业务流
│   └── F001 订单处理流程
│       ├── ①创建(商户) → ②审核(运营) → ③发货(运营)
│       └── GAP 标记（如有）
└── 共性模式
    ├── CRUD 台（订单、商品）
    ├── 审批流（订单审核）
    └── 行为规范
        ├── 删除确认：二次确认弹窗
        ├── 空状态：引导文案 + 操作按钮
        └── 加载模式：骨架屏
```

数据源：`product-map/role-profiles.json` + `task-inventory.json` + `business-flows.json` + `pattern-catalog.json`（可选）+ `behavioral-standards.json`（可选）
反馈存储：`product-map-review/review-feedback.json`

#### Tab 3: 数据模型

```
数据模型
├── E001 订单
│   ├── 字段：id(PK) · order_no · status(enum) · amount ✱必填
│   ├── 状态机：pending → paid → shipped → completed
│   ├── API
│   │   ├── GET /orders (列表)
│   │   ├── POST /orders (创建)
│   │   └── PATCH /orders/:id/status (流转)
│   └── 视图
│       ├── VO001 订单列表 [MG2-L] → 5字段 · 3操作
│       └── VO002 订单详情 [MG2-D] → 8字段 · 2操作
├── E002 商品
│   └── ...
└── 关系
    └── 订单 1:N 商品项
```

数据源：`product-map/entity-model.json` + `api-contracts.json` + `view-objects.json`
反馈存储：`data-model-review/review-feedback.json`

#### Tab 4: 线框（树+预览）

左侧屏幕树（替代 dashboard 卡片网格），右侧预览面板（线框 iframe + pin 评论 + 6V tabs + 4D panel）。

```
线框                          │  预览区
├── J001 商户订单管理           │
│   ├── S001 订单列表 [MG2-L]  │  ← 点击显示线框 iframe
│   │   neutral · 5字段 · 3操作│     + pin 评论
│   ├── S002 创建订单 [MG2-C]  │     + 6V tabs
│   │   focused · 4字段        │     + 4D panel
│   └── S003 订单详情 [MG2-D]  │
│       neutral · 8字段 · 2操作│
└── J002 运营审核流程           │
    └── S004 审核队列 [MG4]    │
```

数据源：`experience-map/experience-map.json` + `journey-emotion-map.json`
反馈存储：`wireframe-review/review-feedback.json`

#### Tab 5: UI（树+预览）

左侧角色→屏幕树，右侧 HTML 预览 + pin 评论。

```
UI 设计                        │  预览区
├── R001 商户                   │
│   ├── 订单列表页              │  ← 点击显示 HTML 预览
│   ├── 创建订单页              │     + pin 评论
│   └── 订单详情页              │
└── R002 运营管理员             │
    └── 审核工作台              │
```

数据源：`ui-design/ui-design-spec.md` + `ui-design/preview/*.html`
反馈存储：`ui-review/review-feedback.json`

#### Tab 6: 规格

```
开发规格
├── 后端服务
│   ├── 数据模型
│   │   ├── orders 表
│   │   │   ├── 字段 + 类型 + 约束 + 索引
│   │   │   └── 状态机
│   │   └── products 表
│   │       └── ...
│   ├── API 接口
│   │   ├── GET /orders → 请求参数 · 响应结构 · 错误码
│   │   └── POST /orders → 请求体 · 响应 · 验证规则
│   ├── 中间件：认证 · 审计
│   └── 任务 (8)
│       ├── B1 初始化 [□]
│       └── B2 数据模型 [□]
├── 前端管理后台
│   ├── 页面路由
│   │   ├── /orders → 组件列表 · 四态 · 交互
│   │   └── /orders/new → 表单字段 · 验证
│   └── 任务 (6)
├── 共享基础
│   ├── 设计 Token（颜色、字号、间距）
│   ├── 共享类型定义（跨端复用的 DTO）
│   └── 基础中间件（认证、日志、错误处理）
└── 跨项目依赖
    └── 后端 B2 → 前端 B4
```

数据源：`project-forge/sub-projects/*/design.json`（dev-forge 新增输出）
反馈存储：`project-forge/spec-review-feedback.json`（新增）

### 命令变更

**新增：**
- `/review` — 启动统一审核站点，打印 URL，不自动弹浏览器
- `/review process` — 处理所有 tab 的反馈
- `/review process <tab>` — 处理指定 tab 的反馈（concept/map/wireframe/ui）

**废弃：**
- `/concept-review` → 删除
- `/map-review` → 删除
- `/wireframe-review` → 删除
- `/ui-review` → 删除
- `/data-model-review` → 删除

**废弃的旧服务器脚本：**
- `mindmap_review_server.py`
- `wireframe_review_server.py`
- `datamodel_review_server.py`
- `ui_review_server.py`

渲染逻辑从旧脚本提取到 `review_hub_server.py` 中，旧脚本删除。

### 反馈存储

各 tab 反馈写入路径不变（向后兼容），下游消费逻辑迁入 `/review process <tab>`：

| Tab | 反馈写入路径 |
|-----|------------|
| 概念 | `concept-review/review-feedback.json` |
| 地图 | `product-map-review/review-feedback.json` |
| 数据模型 | `data-model-review/review-feedback.json` |
| 线框 | `wireframe-review/review-feedback.json` |
| UI | `ui-review/review-feedback.json` |
| 规格 | `project-forge/spec-review-feedback.json` |

### Pipeline 自动化变更

完整自动化 pipeline（含本次变更）：

```
/product-concept → [review: 概念 tab]
→ market-validate (自动，Brave → WebSearch 降级，不需要验证时显示结论)
→ /product-map (Step 0-9，含数据建模 + VO)
→ [review: 地图 tab]
→ /journey-emotion
→ /experience-map
→ design-pattern (必须自动) + behavioral-standards (自动)
→ interaction-gate
→ [review: 线框 tab，数据模型 tab 可看]
→ [use-case ∥ feature-gap ∥ ui-design] (并行)
→ [review: UI tab]
→ design-audit
→ [feature-prune] (手动，用户按需)
```

review hub 在第一个审核节点启动，后续阶段只需通知用户刷新页面查看新 tab。

### dev-forge 变更

**design-to-spec Step 3 改为两阶段：**

Step 3a — 加载 product-design 数据模型（如果存在）：
- 读取 `entity-model.json` → ER 设计起点
- 读取 `api-contracts.json` → API 设计起点
- 读取 `view-objects.json` → 前端组件规格起点
- 不存在 → 回退到当前的从零推导（向后兼容）

Step 3b — 技术丰富（在 product-design 基础上补充）：
- 后端：+ 索引策略 + 中间件链 + 错误响应结构 + 分页约束
- 前端：+ 组件架构 + 状态管理 + 路由守卫

**新增输出 `design.json`：**

与 design.md 同时生成，结构化版本供规格 tab 渲染：

```json
{
  "sub_projects": [
    {
      "name": "backend-api",
      "type": "backend",
      "data_models": [
        {
          "table": "orders",
          "source_entity": "E001",
          "fields": [],
          "indexes": [],
          "state_machine": {}
        }
      ],
      "endpoints": [
        {
          "source_api": "API001",
          "method": "GET",
          "path": "/orders",
          "params": [],
          "response": {},
          "errors": []
        }
      ],
      "middleware": [],
      "tasks": []
    },
    {
      "name": "admin-frontend",
      "type": "frontend",
      "pages": [],
      "shared_components": [],
      "tasks": []
    }
  ],
  "shared": {
    "tokens": {},
    "types": [],
    "base_middleware": []
  },
  "cross_dependencies": []
}
```

每个节点保留 `source_*` 字段溯源到 product-design 的原始 ID。

### Code Changes

| File | Change |
|------|--------|
| `product-design-skill/scripts/review_hub_server.py` | **NEW** — 统一审核站点服务器 |
| `product-design-skill/commands/review.md` | **NEW** — `/review` 命令 |
| `product-design-skill/commands/concept-review.md` | **DELETE** |
| `product-design-skill/commands/map-review.md` | **DELETE** |
| `product-design-skill/commands/wireframe-review.md` | **DELETE** |
| `product-design-skill/commands/data-model-review.md` | **DELETE** |
| `product-design-skill/commands/ui-review.md` | **DELETE** — 如果存在 |
| `product-design-skill/scripts/mindmap_review_server.py` | **DELETE** — 逻辑迁入 hub |
| `product-design-skill/scripts/wireframe_review_server.py` | **DELETE** — 逻辑迁入 hub |
| `product-design-skill/scripts/datamodel_review_server.py` | **DELETE** — 逻辑迁入 hub |
| `product-design-skill/scripts/ui_review_server.py` | **DELETE** — 如果存在，逻辑迁入 hub |
| `product-design-skill/scripts/_common.py` | **MODIFY** — 更新 REVIEW_PORTS（只保留 18900） |
| `product-design-skill/skills/product-map.md` | **MODIFY** — 移除 /data-model-review 提示 |
| `product-design-skill/skills/experience-map.md` | **MODIFY** — 加入 design-pattern + behavioral-standards 自动触发 |
| `product-design-skill/SKILL.md` | **MODIFY** — 更新 pipeline、废弃旧命令、新增 /review |
| `product-design-skill/commands/product-design.md` | **MODIFY** — full 模式 pipeline 更新 |
| `dev-forge-skill/skills/design-to-spec.md` | **MODIFY** — Step 3a/3b + design.json 输出 |
| `dev-forge-skill/SKILL.md` | **MODIFY** — 文档更新 |
| `CLAUDE.md` | **MODIFY** — 更新推荐工作流 |
