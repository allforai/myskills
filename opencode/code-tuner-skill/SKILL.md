---
name: code-tuner
description: >
  This skill should be used when the user asks to "analyze server code quality",
  "check architecture compliance", "find duplicate code", "detect code duplication",
  "review backend architecture", "optimize server code", "code tuning",
  "refactor my backend", "audit code architecture", "code quality review",
  "assess technical debt", "check if code follows three-tier architecture",
  "check DDD compliance", "find abstraction opportunities", "analyze validation logic",
  or mentions server-side code optimization, backend refactoring,
  architectural violations, layered architecture review, or technical debt assessment.
  Supports three-tier, two-tier, and DDD architectures across any language.
  服务端代码调优，架构合规检查，重复代码检测，抽象机会分析，验证逻辑规范，技术债评估。
version: "2.0.0"
---

# Code-Tuner — 服务端代码调优

## 核心理念

相同功能，代码越少质量越高。通过五个维度衡量：

- **重复率** — 相似代码段的数量和分布
- **抽象层次** — 完成同一功能所需的函数/类/文件数量
- **跨层调用深度** — 一个请求穿越多少层才到达逻辑
- **文件分散度** — 相关逻辑分散在多少个文件中
- **验证规范度** — 验证逻辑是否在正确的层、是否统一

仅分析后端代码。覆盖入口层(Entry/API)、业务层(Business/Service)、数据层(Data/Repository)、工具层(Utility)。

## Overview

Code-tuner analyzes backend codebases across five quality dimensions:

- **Duplication rate** — similar code segments, their count and distribution
- **Abstraction level** — number of functions/classes/files needed to accomplish the same task
- **Cross-layer call depth** — how many layers a request traverses to reach logic
- **File scatter** — how many files related logic is spread across
- **Validation discipline** — whether validation logic is in the correct layer and unified

Covers Entry (API), Business (Service), Data (Repository), and Utility layers. Only analyzes server-side code.

---

## 两种运行模式

| | 未上线 (pre-launch) | 维护期 (maintenance) |
|---|---|---|
| 重构建议 | 激进：重写、合并、重新组织目录 | 保守：抽取公共方法、提取接口，不动现有结构 |
| 架构违规 | 标记为 `MUST-FIX` | 标记为 `TECH-DEBT`，附风险评估 |
| 重复代码 | 建议合并到一处 | 建议抽取共用方法，保留原调用点 |
| 任务排序 | 按代码质量影响（大的先做） | 按变更风险（安全的先做） |

## Lifecycle Modes

| Mode | Refactoring | Violations | Duplication | Task Ordering |
|------|-------------|------------|-------------|---------------|
| pre-launch (default) | Aggressive: rewrite, merge, reorganize | MUST-FIX | Merge into single location | By code quality impact (biggest first) |
| maintenance | Conservative: extract shared methods, keep structure | TECH-DEBT with risk assessment | Extract shared method, keep call sites | By change risk (safest first) |

Default to pre-launch unless the user clearly indicates a live production system.

---

## 工作流总览

```
Phase 0: 项目画像 ──→ 用户确认
     ↓
Phase 1: 架构合规检查
     ↓
Phase 2: 重复检测
     ↓
Phase 3: 抽象机会分析
     ↓
Phase 4: 综合评分 + 报告 + 重构任务清单
```

## Available Workflows

| Mode | Phases | Description |
|------|--------|-------------|
| full (default) | 0 → 1 → 2 → 3 → 4 | Complete analysis across all dimensions |
| compliance | 0 → 1 → 4 | Architecture compliance check only |
| duplication | 0 → 2 → 4 | Duplication detection only |
| abstraction | 0 → 3 → 4 | Abstraction opportunity analysis only |
| report | 4 only | Regenerate report from existing phase outputs |

---

### Phase 0: 项目画像

> 详见 `./references/phase0-profile.md`

识别技术栈、推断架构类型、映射层级、识别模块、扫描数据模型。

**关键原则**：层级映射基于逻辑角色（Entry / Business / Data / Utility），不依赖目录名。通过分析依赖方向和代码职责来判断每个目录属于哪一层。不同项目命名各不相同，名称不重要，职责和依赖方向才重要。

实体类和数据库表结构是服务端最重要的信息，扫描所有实体、关系、DTO/VO 分布。

输出 `tuner-profile.json`。架构类型 + 层级映射 + 模块列表 + 数据模型必须经用户确认。

> 跨语言目录映射速查见 `./references/layer-mapping.md`

### Phase 0: Project Profile

> Details: `./references/phase0-profile.md`

Identify tech stack, infer architecture type, map layers, identify modules, scan data model.

Key principle: layer mapping is based on logical roles (Entry / Business / Data / Utility), not directory names. Analyze dependency direction and code responsibilities to determine each directory's layer.

Entity classes and database table structures are the most important server-side information.

Output: `tuner-profile.json`. Architecture type + layer mapping + module list + data model must be confirmed by the user.

> Cross-language directory mapping reference: `./references/layer-mapping.md`

---

### Phase 1: 架构合规检查

> 详见 `./references/phase1-compliance.md`

按架构类型加载规则，检查依赖方向、层级职责、验证位置。

**规则类别：**
- **T-01~T-06** — 三层架构规则
- **W-01~W-03** — 两层架构规则
- **D-01~D-04** — DDD 规则
- **G-01~G-06** — 通用规则（所有架构）

**特殊规则：**
- **T-03**：入口层直接访问数据层时，判断是否合理。简单 CRUD（无业务判断、无组合调用、无事务要求）→ 合理，不报违规。包含业务逻辑 → 违规，应下沉到业务层。
- **G-04/G-05/G-06**：分层验证原则（宽进严出）。格式校验在入口层做掉（因为业务层可被多个入口组合调用）。业务规则验证在业务层。数据层不做业务验证。

输出 `phase1-compliance.json`。

### Phase 1: Architecture Compliance

> Details: `./references/phase1-compliance.md`

Load rules by architecture type, check dependency direction, layer responsibilities, validation placement.

Rule categories: T-01~T-06 (three-tier), W-01~W-03 (two-tier), D-01~D-04 (DDD), G-01~G-06 (universal).

Output: `phase1-compliance.json`.

---

### Phase 2: 重复检测

> 详见 `./references/phase2-duplicates.md`

四个扫描维度：

1. **API/入口层重复** — 多个端点做高度相似的事（导出、分页、CRUD）
2. **业务层重复** — Service 之间相似方法、复制粘贴后只改实体名
3. **数据层重复** — 相似查询、重复分页逻辑、DTO/VO 字段重叠 >70%
4. **工具类重复** — 功能相同的工具方法、重新实现已有库的功能

检测方法：提取方法的结构签名（参数类型 → 操作序列 → 返回类型），相似度 >70% 标记为候选重复。

如果 Service 方法只是透传到 Repository（无业务逻辑），建议删除该 Service 方法，让入口层直接调数据层。

输出 `phase2-duplicates.json`。

### Phase 2: Duplication Detection

> Details: `./references/phase2-duplicates.md`

Four scan dimensions: API/entry layer duplication, business layer duplication, data layer duplication, utility duplication.

Detection method: extract method structural signatures (parameter types → operation sequence → return type), mark as candidate duplicate when similarity > 70%.

Output: `phase2-duplicates.json`.

---

### Phase 3: 抽象机会分析

> 详见 `./references/phase3-abstractions.md`

五类分析：

1. **垂直抽象** — 多个类结构高度相似 → 抽取基类
2. **横向抽象** — 散落各处的相似代码片段 → 抽取公共方法
3. **接口合并** — 多个 API 逻辑相同只是实体不同 → 参数化
4. **验证逻辑** — 验证位置、验证重复、宽进严出、错误响应一致性
5. **过度抽象检测（反向检查）** — 只有 1 个实现的接口、只调用 1 次的工具方法、层层透传无增值、过深继承链

输出 `phase3-abstractions.json`。

### Phase 3: Abstraction Opportunity Analysis

> Details: `./references/phase3-abstractions.md`

Five analysis types: vertical abstraction, horizontal abstraction, interface consolidation, validation logic, over-abstraction detection (reverse check).

Output: `phase3-abstractions.json`.

---

### Phase 4: 综合评分 + 报告

> 详见 `./references/phase4-report.md`

**五维评分（各 0-100，加权总分）：**

| 维度 | 权重 |
|------|------|
| 架构合规度 | 25% |
| 代码重复率 | 25% |
| 抽象合理度 | 20% |
| 验证规范度 | 15% |
| 数据模型规范度 | 15% |

输出 `tuner-report.md`（摘要 + 问题列表 + 热力图 + 详细发现）和 `tuner-tasks.json`（可执行的重构任务清单）。

### Phase 4: Scoring + Report

> Details: `./references/phase4-report.md`

Five-dimension scoring (each 0-100, weighted total):

| Dimension | Weight |
|-----------|--------|
| Architecture compliance | 25% |
| Code duplication | 25% |
| Abstraction reasonableness | 20% |
| Validation discipline | 15% |
| Data model standards | 15% |

Output: `tuner-report.md` (summary + issue list + heatmap + detailed findings) and `tuner-tasks.json` (actionable refactoring task list).

---

## 关键原则

1. **仅分析服务端项目** — 非服务端项目（前端、Markdown、文档仓库等）直接告知用户不适用，不执行分析
2. **Phase 0 必须用户确认** — 架构类型判错，后续全错
3. **不自动重构** — 只输出报告和任务清单，由用户决定执行
4. **两种模式贯穿始终** — 每条发现都给出两种模式下的不同建议
5. **宽进严出** — 格式校验在入口层，业务校验在业务层，数据层不越界
6. **简单透传可跳层** — 纯 CRUD 无业务逻辑时，入口层可直接调数据层
7. **不过度抽象** — 同时检测"该抽象没抽象"和"不该抽象却抽象了"
8. **名称不重要，职责才重要** — 通过依赖模式识别层级，不靠目录名

## Key Principles

1. **Server-side projects only** — refuse non-backend projects (frontend, Markdown, documentation repos)
2. **Phase 0 requires user confirmation** — wrong architecture type leads to wrong analysis
3. **Read-only analysis** — only output reports and task lists; user decides what to execute
4. **Two modes throughout** — every finding includes different suggestions for both lifecycle modes
5. **Loose-in, strict-out** — format validation at entry layer, business validation at business layer, data layer stays in its lane
6. **Simple passthrough may skip layers** — pure CRUD with no business logic allows entry layer to call data layer directly
7. **No over-abstraction** — detect both "should abstract but didn't" and "shouldn't abstract but did"
8. **Names don't matter, responsibilities do** — identify layers by dependency patterns, not directory names

---

## 文件结构

```
your-project/
└── .allforai/code-tuner/
    ├── tuner-profile.json        # Phase 0: 项目画像
    ├── phase1-compliance.json    # Phase 1: 架构违规列表
    ├── phase2-duplicates.json    # Phase 2: 重复检测结果
    ├── phase3-abstractions.json  # Phase 3: 抽象机会
    ├── tuner-report.md           # Phase 4: 综合报告
    └── tuner-tasks.json          # Phase 4: 重构任务清单
```

## File Structure

```
your-project/
└── .allforai/code-tuner/
    ├── tuner-profile.json        # Phase 0: project profile
    ├── tuner-decisions.json      # Phase 0: decision log
    ├── phase1-compliance.json    # Phase 1: architecture violations
    ├── phase2-duplicates.json    # Phase 2: duplication detection results
    ├── phase3-abstractions.json  # Phase 3: abstraction opportunities
    ├── tuner-report.md           # Phase 4: comprehensive report
    └── tuner-tasks.json          # Phase 4: refactoring task list
```

---

## 使用方式

### 场景 1: 新项目完整分析

```
请用 code-tuner 技能分析我的项目。
项目路径是 /path/to/project。
项目状态是未上线。
```

### 场景 2: 维护期项目

```
请用 code-tuner 分析我的项目。
项目路径是 /path/to/project。
项目状态是维护期。
```

### 场景 3: 只跑单个阶段

```
请用 code-tuner 只做重复检测。
项目路径是 /path/to/project。
画像文件在 .allforai/code-tuner/tuner-profile.json。
```

### 场景 4: 指定模块分析

```
请用 code-tuner 分析订单模块。
项目路径是 /path/to/project。
只看 src/modules/order 目录。
```

## Usage

### Full analysis of a new project

```
Analyze my backend project's code quality. The project is at /path/to/project. It's pre-launch.
```

### Maintenance-mode project

```
Run code-tuner on my project at /path/to/project. It's in production maintenance mode.
```

### Single phase only

```
Just run duplication detection on my project. The profile is already at .allforai/code-tuner/tuner-profile.json.
```

### Specific module analysis

```
Analyze only the order module with code-tuner. Project is at /path/to/project, focus on src/modules/order.
```

---

## Orchestration

For detailed phase execution logic, transition rules, and resume handling, see `./execution-playbook.md`.
