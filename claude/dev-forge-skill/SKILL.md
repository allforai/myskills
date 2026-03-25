---
name: dev-forge
description: >
  Development forge: project-setup (interactive sub-project splitting + tech stack selection),
  design-to-spec (LLM-driven Forge-Verify-Loop (4D/6V/XV) -> requirements + design + tasks),
  task-execute (systematic task execution with progress tracking + Incremental XV + Task-Level verification loops),
  product-verify (static + dynamic acceptance),
  deadhunt (dead link hunting + CRUD completeness + ghost feature detection),
  fieldcheck (UI/API/Entity/DB field consistency),
  testforge (test-driven quality forging: full test pyramid — unit/component/integration/e2e-chain/mobile — audit + generate + fix → converge).
  Full pipeline: /project-forge. LLM-driven Forge-Verify-Loop (4D/6V/XV).
  开发锻造套件：项目引导、设计转规格、任务执行、产品验收、死链猎杀、字段一致性、测试锻造。
version: "6.0.0"
---

# Dev Forge — 开发锻造套件

> 从产品设计产物到可运行项目：AI 驱动的「锻造-验证-闭环」全流程自动化。

## 全局指导思想（新增）

当上游 `product-map` 判定 `experience_priority = consumer | mixed` 时，dev-forge 不再只以“功能实现完成”作为前端成功标准，而会自动切换到用户端优先标准：

- requirements / design / tasks 必须包含主线闭环、状态系统、反馈机制、回访理由
- task-execute 不能把“页面能打开 + API 通了”视为前端完成
- 用户端实现如果仍像概念 demo，需要在执行期继续修正，而不是等最终验收兜底

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

若项目为 `consumer` 或 `mixed`，会把“用户端成熟度要求”一起翻译为前端规格与任务，而不是只翻译成路由/接口/页面壳。

```
/design-to-spec             # 全量生成
/design-to-spec sp-001      # 仅指定子项目
```

### 3. task-execute — 任务执行

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/task-execute.md`

**R0 项目初始化**（Monorepo 配置 + 目录结构 + 依赖安装）→ **R1-R4 业务实现**（逐任务执行 + 增量 XV 审计 + 契约漂移同步 + DevSecOps 左移）。支持 build-log.json 进度追踪与断点续作。

若当前 Round 涉及用户端子项目，任务执行会额外检查主线是否顺、状态是否齐、是否具备持续关系，而不是只检查功能是否可点通。

```
/task-execute              # 从 Round 0 开始（或断点续作）
/task-execute round 2      # 仅执行指定 Round
/task-execute resume       # 从 build-log.json 断点续作
```

### 4. product-verify — 产品验收

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/product-verify.md`

静态扫描代码覆盖率 + 动态 Playwright 验证行为合规性，输出差异任务清单。

```
/product-verify             # 完整验收（静态+动态）
/product-verify static      # 只做静态扫描
/product-verify dynamic     # 只做动态验证
```

### 5. deadhunt — 死链猎杀 + 完整性验证

猎杀死链、幽灵功能、CRUD 缺口。6 Phase 流水线：项目分析→静态扫描→测试计划→深度测试→报告→补充测试。支持独立运行，不依赖 project-forge 流程。

```
/deadhunt                   # 完整验证（静态+深度）
/deadhunt static            # 仅静态分析
/deadhunt deep              # 仅深度测试（需 Playwright）
/deadhunt incremental       # 增量验证（仅 git 改动涉及的模块）
```

### 6. fieldcheck — 字段一致性检查

检查 UI↔API↔Entity↔DB 四层字段名一致性，发现幽灵字段、拼写错误、映射断裂。纯静态分析，不需要启动应用。

```
/fieldcheck                 # 全链路 L1↔L2↔L3↔L4
/fieldcheck frontend        # 仅前端 L1↔L2
/fieldcheck backend         # 仅后端 L2↔L3↔L4
/fieldcheck endtoend        # 端到端 L1↔L4
```

### 7. testforge — 测试锻造

审查项目自身测试代码的质量和覆盖率，用 FVL 三维验证（纵向审计 + 横向交叉 + 负空间推导）发现缺口。覆盖测试金字塔全层级：unit / component / integration / e2e-chain / mobile。从 business-flows 自动推导跨站 E2E 链并生成可执行测试脚本。补测试、修 bug，循环至全绿。

```
/testforge                  # 完整锻造（审计+补测试+修bug+报告）
/testforge analyze          # 仅审计（不补测试不修代码）
/testforge fix              # 仅锻造（用已有分析结果）
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
dev-forge（开发层）       引导→规格→执行→验收→猎杀→字段→测试锻造 ← 你在这里
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
| Test Pyramid / BDD | testforge：场景来自业务流，覆盖全测试金字塔 |
| **Understand-then-Scan** | fieldcheck/deadhunt/testforge：LLM 先理解项目规则（拦截器、ORM 模式、路由注册方式），再用理解扫描全项目。不硬编码 grep 模式。 |

### Understand-then-Scan 原则

> **LLM 驱动的检测 = 先理解项目的"规则"，再用理解去扫描。**

所有 skill 中涉及"检测项目特定模式"的逻辑，分两类执行方式：

| 执行方式 | 适用场景 | 做法 |
|---------|---------|------|
| **LLM 驱动** | 项目特定的逻辑模式（拦截器、ORM 查询、路由注册、响应格式） | LLM 先 Read 关键文件理解项目规则，推导出检测标准，再批量扫描 |
| **结构化比对** | 跨层标识符匹配（字段名、枚举值、URL 路径、i18n 键） | 提取两端数据集，diff 比对 |

**核心区别**：结构化比对只需要"提取 + 比较"，LLM 驱动需要"读代码 → 理解意图 → 推导规则 → 再扫描"。

**效率优化**：LLM 驱动的理解步骤每个项目只需做一次（Phase 0 / Step 0），理解结果缓存后，后续扫描步骤可以批量执行。

> 以上两类执行方式已涵盖 dev-forge 的核心检测原则。fieldcheck/deadhunt/testforge 各自在 skill 文件中定义具体检测规则。

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
    │   ├── forge-decisions.json        # 全程决策
    │   └── trend-sources.json          # 趋势搜索记录
    ├── demo-forge/              # → 独立插件 demo-forge-skill 管理
    ├── product-verify/
    │   ├── static-report.json          # 静态结果
    │   ├── dynamic-report.json         # 动态结果
    │   └── verify-report.md            # 可读报告
    ├── deadhunt/
    │   ├── deadhunt-decisions.json     # 决策日志
    │   ├── output/
    │   │   ├── validation-profile.json # 项目画像
    │   │   ├── static-analysis/        # 静态分析结果
    │   │   ├── validation-report-*.md  # 各端报告
    │   │   ├── fix-tasks.json          # 修复任务清单
    │   │   └── field-analysis/         # 字段一致性分析
    │   └── tests/                      # 生成的测试脚本
    └── testforge/
        ├── testforge-decisions.json    # 决策日志
        ├── test-profile.json           # 测试画像
        ├── testforge-analysis.json     # 审计分析（4D 缺口 + 横向 + 负空间）
        ├── testforge-fixes.json        # 修复记录
        └── testforge-report.md         # 可读报告
```
