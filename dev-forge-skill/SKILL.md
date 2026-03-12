---
name: dev-forge
description: >
  Development forge: project-setup (interactive sub-project splitting + tech stack selection),
  design-to-spec (LLM-driven Forge-Verify-Loop (4D/6V/XV) -> requirements + design + tasks),
  task-execute (systematic task execution with progress tracking + Incremental XV + Task-Level verification loops),
  e2e-verify (cross-project Playwright/Patrol E2E),
  product-verify (static + dynamic acceptance),
  deadhunt (dead link hunting + CRUD completeness + ghost feature detection),
  fieldcheck (UI/API/Entity/DB field consistency).
  Full pipeline: /project-forge. LLM-driven Forge-Verify-Loop (4D/6V/XV).
  开发锻造套件：项目引导、设计转规格、任务执行、跨端验证、产品验收、死链猎杀、字段一致性。
version: "4.6.0"
---

# Dev Forge — 开发锻造套件

> 从产品设计产物到可运行项目：AI 驱动的「锻造-验证-闭环」全流程自动化。

## 前置依赖

本插件依赖 `product-design` 插件生成的 `.allforai/` 输出。请先运行 `/product-design full` 完成产品设计。

## 全流程编排

```
/project-forge full          # 新项目，开启 FVL 全流程
/project-forge existing      # 已有项目，gap 模式 + 6V 审计
/project-forge resume        # 从上次中断处继续
```

## 包含的技能（7 个 + 1 独立插件）

### 1. project-setup — 项目引导

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/project-setup.md`

交互式引导用户拆分子项目、选择技术栈、分配模块。LLM 验证架构合理性 (Conway's Law)。

```
/project-setup              # 新项目，从空白开始
/project-setup existing     # 已有项目，扫描代码 → 识别缺口
```

### 2. design-to-spec — 设计转规格

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/design-to-spec.md`

**Forge-Verify-Loop (FVL)**：LLM 生成初稿 → 4D/6V 审计 → XV 交叉验证 → 自动修正。API-First 策略，生成 requirements + design + events + tasks。

```
/design-to-spec             # 全量生成
/design-to-spec sp-001      # 仅指定子项目
```

### 3. task-execute — 任务执行

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/task-execute.md`

**R0 项目初始化**（Monorepo 配置 + 目录结构 + 依赖安装）→ **R1-R4 业务实现**（逐任务执行 + 增量 XV 审计 + 契约漂移同步 + DevSecOps 左移）。支持 build-log.json 进度追踪与断点续作。

```
/task-execute              # 从 Round 0 开始（或断点续作）
/task-execute round 2      # 仅执行指定 Round
/task-execute resume       # 从 build-log.json 断点续作
```

### 4. e2e-verify — 跨端验证

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/e2e-verify.md`

从 business-flows 推导跨端场景，Playwright（Web）/ XCUITest（iOS）/ Maestro（Flutter/RN）跨子项目执行。

```
/e2e-verify                 # 推导场景 + 执行全部
/e2e-verify plan            # 仅推导场景，不执行
/e2e-verify run             # 加载已有场景并执行
```

### 5. product-verify — 产品验收

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/product-verify.md`

静态扫描代码覆盖率 + 动态 Playwright 验证行为合规性，输出差异任务清单。

```
/product-verify             # 完整验收（静态+动态）
/product-verify static      # 只做静态扫描
/product-verify dynamic     # 只做动态验证
```

### 6. deadhunt — 死链猎杀 + 完整性验证

猎杀死链、幽灵功能、CRUD 缺口。6 Phase 流水线：项目分析→静态扫描→测试计划→深度测试→报告→补充测试。支持独立运行，不依赖 project-forge 流程。

```
/deadhunt                   # 完整验证（静态+深度）
/deadhunt static            # 仅静态分析
/deadhunt deep              # 仅深度测试（需 Playwright）
/deadhunt incremental       # 增量验证（仅 git 改动涉及的模块）
```

### 7. fieldcheck — 字段一致性检查

检查 UI↔API↔Entity↔DB 四层字段名一致性，发现幽灵字段、拼写错误、映射断裂。纯静态分析，不需要启动应用。

```
/fieldcheck                 # 全链路 L1↔L2↔L3↔L4
/fieldcheck frontend        # 仅前端 L1↔L2
/fieldcheck backend         # 仅后端 L2↔L3↔L4
/fieldcheck endtoend        # 端到端 L1↔L4
```

### 8. demo-forge — 演示锻造（独立插件）

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

## 定位

```
product-design（产品层）  概念→定义→交互→视觉→用例→查漏→剪枝
dev-forge（开发层）       引导→规格→执行→验证→验收→猎杀→字段 ← 你在这里
code-tuner（架构层）      合规→重复→抽象→评分
```

## 理论支撑

每个技能的决策都扎根于经典软件工程理论与 AI 闭环验证框架：

| 理论 / 框架 | 应用阶段 |
|------------|---------|
| Forge-Verify-Loop (4D/6V/XV) | 全流程：AI 生成与审计闭环 |
| Unix Philosophy | 贯穿全部：单一职责、组合、文本流 |
| Conway's Law | project-setup：架构映射组织 |
| Clean Architecture | design-to-spec：Batch 依赖方向 |
| Worse is Better / Tracer Bullet | task-execute R0：先能跑再完善 |
| Hexagonal Architecture | task-execute：mock↔真实后端只是换适配器 |
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
    ├── product-verify/
    │   ├── static-report.json          # 静态结果
    │   ├── dynamic-report.json         # 动态结果
    │   └── verify-report.md            # 可读报告
    └── deadhunt/
        ├── deadhunt-decisions.json     # 决策日志
        ├── output/
        │   ├── validation-profile.json # 项目画像
        │   ├── static-analysis/        # 静态分析结果
        │   ├── validation-report-*.md  # 各端报告
        │   ├── fix-tasks.json          # 修复任务清单
        │   └── field-analysis/         # 字段一致性分析
        └── tests/                      # 生成的测试脚本
```
