---
name: dev-forge
description: >
  Development forge: project-setup (interactive sub-project splitting + tech stack selection),
  design-to-spec (product-design artifacts → requirements + design + tasks),
  project-scaffold (template-based project skeleton + mock server),
  task-execute (systematic task execution with progress tracking + incremental verification),
  e2e-verify (cross-project Playwright/Patrol E2E),
  product-verify (static + dynamic acceptance).
  Full pipeline: /project-forge. Theory-backed decisions (Unix Philosophy, Clean Architecture, etc.).
  开发锻造套件：项目引导、设计转规格、脚手架生成、任务执行、跨端验证、产品验收。
version: "2.9.0"
---

# Dev Forge — 开发锻造套件

> 从产品设计产物到可运行项目：理论驱动的全流程自动化锻造。

## 前置依赖

本插件依赖 `product-design` 插件生成的 `.allforai/product-map/` 输出。请先运行 `/product-design full` 完成产品设计。

## 全流程编排

```
/project-forge full          # 新项目，从头执行
/project-forge existing      # 已有项目，gap 模式
/project-forge resume        # 从上次中断处继续
```

## 包含的技能（7 个）

### 1. project-setup — 项目引导

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/project-setup.md`

交互式引导用户拆分子项目、选择技术栈、分配模块。理论基础：Unix Philosophy（做一件事做好）、Conway's Law（架构映射组织）。

```
/project-setup              # 新项目，从空白开始
/project-setup existing     # 已有项目，扫描代码 → 识别缺口
```

### 2. design-to-spec — 设计转规格

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/design-to-spec.md`

从产品设计产物自动生成按子项目划分的 requirements + design + tasks。API-First 策略：先表结构和 API 端点，再展开前端。Step 3a 可选加载 product-design 数据模型（entity-model/api-contracts/view-objects）作为起点，Step 3b 在此基础上补充技术细节。同时输出 design.json 结构化版本供 Review Hub 渲染。

```
/design-to-spec             # 全量生成
/design-to-spec sp-001      # 仅指定子项目
```

### 3. project-scaffold — 脚手架生成

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffold.md`

按技术栈模板生成项目骨架 + Mock 后端。理论基础：Convention over Configuration、Tracer Bullet（先打通端到端最小路径）、Worse is Better（简单优先）。

支持 16 种技术栈模板：8 后端 + 6 Web + 2 移动端。

```
/project-scaffold           # 全量生成
/project-scaffold sp-001    # 仅指定子项目
```

### 4. task-execute — 任务执行

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/task-execute.md`

系统化执行 tasks.md 中的原子任务：自动推断执行策略（串行/并行）、委托 superpowers skill 编写代码、build-log.json 进度追踪、每 Round 增量验证。支持断点续作和修复轮次检测。

```
/task-execute              # 从 Round 0 开始（或断点续作）
/task-execute round 2      # 仅执行指定 Round
/task-execute resume       # 从 build-log.json 断点续作
```

### 5. e2e-verify — 跨端验证

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/e2e-verify.md`

从 business-flows 推导跨端场景，Playwright（Web）/ Patrol（Flutter）/ Detox（RN）跨子项目执行。

```
/e2e-verify                 # 推导场景 + 执行全部
/e2e-verify plan            # 仅推导场景，不执行
/e2e-verify run             # 加载已有场景并执行
```

### 6. demo-forge — 演示锻造（独立插件）

> 已独立为 `demo-forge-skill/` 插件。详见该插件文档。

按产品地图生成有业务逻辑、有人物关系、有时间分布的真实感演示数据，配合富媒体采集+加工+上传，Playwright 验证，多轮迭代打磨至演示级品质。

```
/demo-forge              # 全流程
/demo-forge design       # 只设计方案
/demo-forge media        # 富媒体采集+上传
/demo-forge execute      # 数据灌入
/demo-forge verify       # 验证
/demo-forge clean        # 清理
```

### 7. product-verify — 产品验收

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/product-verify.md`

静态扫描代码覆盖率 + 动态 Playwright 验证行为合规性，输出差异任务清单。

```
/product-verify             # 完整验收（静态+动态）
/product-verify static      # 只做静态扫描
/product-verify dynamic     # 只做动态验证
```

## 定位

```
product-design（产品层）  概念→定义→交互→视觉→用例→查漏→剪枝
dev-forge（开发层）       引导→规格→脚手架→执行→验证→验收 ← 你在这里
deadhunt（QA 层）         死链→CRUD完整性→幽灵功能→字段一致性
code-tuner（架构层）      合规→重复→抽象→评分
```

## 理论支撑

每个技能的决策都扎根于经典软件工程理论：

| 理论 | 应用阶段 |
|------|---------|
| Unix Philosophy | 贯穿全部：单一职责、组合、文本流 |
| Conway's Law | project-setup：架构映射组织 |
| Clean Architecture | design-to-spec：Batch 依赖方向 |
| Worse is Better / Tracer Bullet | project-scaffold：先能跑再完善 |
| Hexagonal Architecture | scaffold → verify：mock↔真实后端只是换适配器 |
| Test Pyramid / BDD | e2e-verify：场景来自业务流 |

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/dev-forge-principles.md`

## 输出

```
your-project/
└── .allforai/
    ├── project-forge/
    │   ├── project-manifest.json       # 总清单
    │   ├── sub-projects/{name}/
    │   │   ├── requirements.md         # 需求
    │   │   ├── design.md               # 设计（人类可读）
    │   │   ├── design.json             # 设计（机器可读，含 source_* 溯源）
    │   │   └── tasks.md                # 任务
    │   ├── build-log.json              # 任务执行进度
    │   ├── e2e-scenarios.json          # 跨端场景
    │   ├── e2e-report.md               # E2E 结果
    │   ├── forge-decisions.json        # 全程决策
    │   └── trend-sources.json          # 趋势搜索记录
    ├── demo-forge/              # → 独立插件 demo-forge-skill 管理
    └── product-verify/
        ├── static-report.json          # 静态结果
        ├── dynamic-report.json         # 动态结果
        └── verify-report.md            # 可读报告
```
