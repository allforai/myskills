---
description: "项目锻造全流程：setup → spec → scaffold → build → verify。模式: full / existing / resume"
argument-hint: "[mode: full|resume] [existing]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion"]
---

# Project Forge — 项目锻造全流程编排

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

> **跨插件调用约定**：本命令是「导航员」。
> - Phase 1-3, 5 在本插件内执行，通过 `${CLAUDE_PLUGIN_ROOT}/skills/` 路径加载技能。
> - Phase 2.5（seed-forge）为本插件内已有命令。
> - Phase 4（任务执行）提示用户使用 superpowers 技能编排。
> - 各阶段产物通过 `.allforai/` 目录作为层间合约。

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 新项目，从头执行全流程
- **`full existing`** → 已有项目，gap 模式（扫描代码 → 仅补缺）
- **`resume`** → 检测已有产物，从第一个未完成阶段继续

## 六阶段架构

```
┌─────────────────────────────────────────────────────────────┐
│                  Project Forge (项目锻造)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Phase 0: 产物检测 + 模式路由                                │
│  ↓                                                          │
│  Phase 1: 项目引导 (project-setup)                          │
│    交互式: 拆子项目 + 选技术栈 + 分模块                     │
│    输出: project-manifest.json                               │
│  ↓ 质量门禁: ≥1 子项目，每个有技术栈                        │
│  Phase 2: 设计转规格 (design-to-spec)                       │
│    读产品设计产物 → 按子项目生成 spec                        │
│    输出: requirements.md + design.md + tasks.md              │
│  ↓ 质量门禁: 每子项目 3 份 spec 完整                        │
│  Phase 2.5: 种子数据方案                                     │
│    提示用户运行 /seed-forge plan                             │
│    输出: seed-plan.json                                      │
│  ↓ 质量门禁: seed-plan.json 存在                            │
│  Phase 3: 脚手架生成 (project-scaffold)                     │
│    按模板 + mock-server                                      │
│    输出: 项目骨架 + mock-server/                             │
│  ↓ 质量门禁: 脚手架存在 + mock 可启动                       │
│  Phase 4: 任务执行 (编排层)                                  │
│    按 Round 依赖顺序执行 batch                               │
│    Round 0→1→2→3→4                                          │
│  ↓ 质量门禁: CORE 任务完成，lint 通过                       │
│  Phase 5: 跨端验证 (e2e-verify)                             │
│    业务流 → 跨端场景 → Playwright                            │
│    输出: e2e-report                                          │
│  ↓                                                          │
│  Phase 6: 最终报告                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 0：产物检测 + 初始化

### 产物探测

扫描以下目录，判断进度：

| 阶段 | 完成标志 |
|------|----------|
| product-design | `.allforai/product-map/task-inventory.json` 存在且 task 数 > 0 |
| project-setup | `.allforai/project-forge/project-manifest.json` 存在 |
| design-to-spec | `.allforai/project-forge/sub-projects/*/tasks.md` 存在 |
| seed-forge plan | `.allforai/seed-forge/seed-plan.json` 存在 |
| project-scaffold | `.allforai/project-forge/sub-projects/*/scaffold-manifest.json` 存在 |
| task-execution | `.allforai/project-forge/sub-projects/*/build-log.json` 存在 |
| e2e-verify | `.allforai/project-forge/e2e-report.json` 存在 |

### 前置检查

**product-design 产物必须存在**：
- 检查 `.allforai/product-map/product-map.json`
- 不存在 → 输出「请先完成产品设计流程（/product-design full），再运行项目锻造」，终止

### 模式处理

**full 模式**：从 Phase 1 开始，逐阶段执行。
**full existing**：Phase 1 的 project-setup 以 existing 模式运行（扫描代码）。
**resume 模式**：从第一个未完成阶段开始。

### 初始化决策追踪

创建/更新 `.allforai/project-forge/forge-decisions.json`：

```json
{
  "forge_run": {
    "mode": "full | existing | resume",
    "started_at": "ISO8601",
    "product_source": ".allforai/product-map/product-map.json"
  },
  "phase_status": {
    "phase_1": "pending | completed | skipped",
    "phase_2": "pending | completed | skipped",
    "phase_2_5": "pending | completed | skipped",
    "phase_3": "pending | completed | skipped",
    "phase_4": "pending | in_progress | completed",
    "phase_5": "pending | completed | skipped",
    "phase_6": "pending | completed"
  },
  "decisions": []
}
```

向用户展示探测结果 + 执行计划，确认后开始。

---

## Phase 1：项目引导

### 执行方式

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/project-setup.md`，按其工作流执行。

- full 模式 → project-setup new
- existing 模式 → project-setup existing

### 质量门禁

| 条件 | 标准 |
|------|------|
| 子项目数量 | ≥ 1 |
| 每个子项目有技术栈 | template_id 非空 |
| 模块覆盖率 | 100%（所有模块已分配） |

**PASS** → 进入 Phase 2
**FAIL** → 向用户报告，AskUserQuestion：修复后继续 / 带问题继续 / 中止

---

## Phase 2：设计转规格

### 执行方式

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/design-to-spec.md`，按其工作流执行。

### 质量门禁

| 条件 | 标准 |
|------|------|
| 每子项目 3 份 spec | requirements.md + design.md + tasks.md 全部存在 |
| 任务覆盖 | 所有 CORE 任务都出现在 tasks.md 中 |
| 原子性 | tasks.md 中无宽泛任务（如"实现 XX 系统"） |

**PASS** → 进入 Phase 2.5
**FAIL** → 向用户报告问题

---

## Phase 2.5：种子数据方案

### 执行方式

提示用户执行种子方案生成：

```
Phase 2 完成。接下来需要种子数据方案作为 mock-server 数据蓝本。

请执行: /seed-forge plan

完成后请回到此处继续。如果不需要种子数据，可以跳过此步骤。
```

AskUserQuestion：
- 已完成 seed-forge plan → 验证 seed-plan.json 存在，继续
- 跳过 → 记录决策，mock-server 将使用最小占位数据
- 需要帮助 → 说明 seed-forge 的用途

### 质量门禁

| 条件 | 标准 |
|------|------|
| seed-plan.json | 存在（或用户选择跳过） |

---

## Phase 3：脚手架生成

### 执行方式

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffold.md`，按其工作流执行。

### New vs Existing 差异

- **new**：全量脚手架
- **existing**：仅补缺文件，绝不覆盖已有

### 质量门禁

| 条件 | 标准 |
|------|------|
| 脚手架文件 | scaffold-manifest.json 存在且文件数 > 0 |
| mock-server | apps/mock-server/server.js 存在 |
| 依赖安装 | 用户确认 pnpm install 成功 |
| mock 启动 | 用户确认 mock-server 可访问 |

**PASS** → 进入 Phase 4
**FAIL** → 向用户报告问题

---

## Phase 4：任务执行

### 执行计划展示

读取各子项目 tasks.md → 统计任务数 → 构建跨子项目依赖图：

```
Round 0: B0 Monorepo Setup
  - 0.1 配置 monorepo workspace
  - 0.2 创建 shared-types
  - 0.3 创建 mock-server

Round 1: 全部子项目 B1 (Foundation) 并行
  - [api-backend] B1 Foundation: X 个任务
  - [merchant-admin] B1 Foundation: X 个任务
  - [customer-web] B1 Foundation: X 个任务

Round 2: Backend B2 (API) ∥ Frontend B3 (UI)
  - [api-backend] B2 API: X 个任务
  - [merchant-admin] B3 UI: X 个任务（连 mock-server）
  - [customer-web] B3 UI: X 个任务（连 mock-server）

Round 3: api-client + Frontend B4 (Integration)
  - 生成 packages/api-client
  - [merchant-admin] B4 Integration: X 个任务（切换真实后端）
  - [customer-web] B4 Integration: X 个任务

Round 4: 全部子项目 B5 (Testing)
  - [api-backend] B5 Testing: X 个任务
  - [merchant-admin] B5 Testing: X 个任务
  - [customer-web] B5 Testing: X 个任务
```

### 执行方式选择

AskUserQuestion：选择执行方式

| 方式 | 说明 | 适合场景 |
|------|------|---------|
| **subagent-driven-development** | 逐任务执行 + 双审查，稳定但慢 | 首次使用、重要项目、不确定质量 |
| **dispatching-parallel-agents** | 按模块并行分发，快但需文件不冲突 | 模块独立性好、有经验的用户 |
| **手动执行** | 用户自己按 tasks.md 逐个执行 | 有特殊需求、想精细控制 |

### 逐 Round 执行

对每个 Round：

1. 展示本 Round 任务列表
2. 提示用户启动对应 superpowers 技能：
   ```
   Round {N} 就绪。请使用以下方式执行：

   方式 A（推荐）: 使用 /subagent-driven-development 逐任务执行
   方式 B: 使用 /dispatching-parallel-agents 并行执行

   执行范围: 以下任务列表
   {任务列表}

   完成后请回到此处继续。
   ```
3. 等待用户确认完成
4. 质量检查：
   - 提示用户运行 lint: `pnpm lint`
   - 提示用户运行 test: `pnpm test`
   - 有失败 → 记录，AskUserQuestion：修复后继续 / 跳过继续
5. 更新 build-log.json
6. 进入下一个 Round

### 并行度控制

- 同模块内任务：串行（防止文件冲突）
- 不同模块任务：可并行
- Round 内跨子项目：可并行（独立子项目无文件冲突）
- Round 间：串行（有依赖）

### 质量门禁

| 条件 | 标准 |
|------|------|
| CORE 任务 | 全部标记完成 |
| lint | 通过（或用户确认跳过） |
| test | 通过（或用户确认跳过） |

---

## Phase 5：跨端验证

### 执行方式

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/e2e-verify.md`，按其工作流执行。

### 前置

所有子项目应用必须正在运行。提示用户启动：
```
Phase 5 需要所有子项目应用正在运行。请确认以下服务已启动：

- api-backend: http://localhost:{port}
- merchant-admin: http://localhost:{port}
- customer-web: http://localhost:{port}
```

### 质量门禁

| 条件 | 标准 |
|------|------|
| E2E 通过率 | ≥ 80% 场景通过 |
| FIX_REQUIRED | 已全部分类 |

---

## Phase 6：最终报告

### 汇总所有阶段

读取全部阶段产出，生成最终报告：

**输出文件**：
- `.allforai/project-forge/forge-report.json` — 全量报告（机器版）
- `.allforai/project-forge/forge-report.md` — 人类版摘要

### forge-report.md 结构

```markdown
# 项目锻造报告

## 执行摘要

- 执行模式: {full/existing/resume}
- 子项目数: {N}
- 总任务数: {N} (CORE: {N}, DEFER: {N})

## 各阶段状态

| 阶段 | 状态 | 质量门禁 | 关键产出 |
|------|------|----------|----------|
| Phase 1: 项目引导 | 完成 | PASS | project-manifest.json |
| Phase 2: 设计转规格 | 完成 | PASS | {N} 子项目 × 3 份 spec |
| Phase 2.5: 种子方案 | 完成/跳过 | PASS/SKIP | seed-plan.json |
| Phase 3: 脚手架生成 | 完成 | PASS | {N} 文件 + mock-server |
| Phase 4: 任务执行 | 完成 | PASS | {N}/{M} 任务完成 |
| Phase 5: 跨端验证 | 完成 | PASS | {N}/{M} 场景通过 |

## 各子项目状态

| 子项目 | 类型 | 技术栈 | 任务 | 完成率 | E2E |
|--------|------|--------|------|--------|-----|
| api-backend | backend | NestJS | X/Y | 100% | N/A |
| merchant-admin | admin | Next.js | X/Y | 95% | 4/5 |
...

## 待处理项

### DEFER 任务（{N} 个）
{列表}

### E2E 失败项（{N} 个）
{列表}

## 下一步行动

1. [ ] 处理 DEFER 任务
2. [ ] 修复 E2E 失败项
3. [ ] 运行 /seed-forge fill 灌入真实数据
4. [ ] 运行 /product-verify full 完整验收
5. [ ] 运行 /deadhunt full 链路验证
6. [ ] 运行 /code-tuner full 架构分析

## 产出文件索引

> project-manifest: `.allforai/project-forge/project-manifest.json`
> 各子项目 spec: `.allforai/project-forge/sub-projects/{name}/`
> E2E 报告: `.allforai/project-forge/e2e-report.md`
> 全程决策: `.allforai/project-forge/forge-decisions.json`
```

---

## New vs Existing 模式差异

| Phase | New 模式 | Existing 模式 |
|-------|---------|--------------|
| Phase 1 | 从空白引导拆分 | 扫描已有代码，提议拆分，识别缺口 |
| Phase 2 | 全量 spec 生成 | 仅为缺失模块生成 spec |
| Phase 3 | 全量脚手架 | 仅补缺文件，绝不覆盖已有 |
| Phase 4 | 全量任务执行 | 仅执行缺口任务 |
| Phase 5 | 全量 E2E | 全量 E2E（无差异） |

---

## 铁律

### 1. 质量门禁不跳过

每阶段完成后必须通过质量门禁。失败时向用户报告，由用户决定是否带问题继续。

### 2. 用户可在任意阶段中止

保存已有产出，输出部分摘要。resume 模式可从中断处继续。

### 3. 编排命令是导航员

不直接实现功能，而是加载对应 skill 或提示用户执行对应命令。

### 4. .allforai/ 是层间合约

各阶段通过 `.allforai/project-forge/` 下的文件交换数据，不通过对话上下文传递大量数据。

### 5. 决策全程追踪

所有用户决策记录到 forge-decisions.json，可追溯、可审计。
