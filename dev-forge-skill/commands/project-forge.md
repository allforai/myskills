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
> - Phase 4（任务执行）调用 `task-execute` skill，自动编排 superpowers 技能。
> - Phase 4.5（验证闭环）产品验收 + E2E 验证 → 修复任务 → 回归。
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
│  Phase 0: 产物检测 + 模式路由 + Preflight 偏好收集           │
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
│  Phase 4: 任务执行 (task-execute)                             │
│    自动编排: 策略推断 → 委托执行 → 进度追踪 → 增量验证      │
│    Round 0→1→2→3→4                                          │
│  ↓ 质量门禁: CORE 任务完成，lint 通过                       │
│  Phase 4.5: 验证闭环                                         │
│    product-verify + e2e-verify → 修复任务 → 回归验证         │
│  ↓ 质量门禁: 修复项 = 0 或用户确认跳过                      │
│  Phase 5: 跨端验证 (e2e-verify) — 条件执行                   │
│    仅当 Phase 4.5 被跳过时执行                                │
│    业务流 → 跨端场景 → Playwright                            │
│  ↓                                                          │
│  Phase 6: 最终报告                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 0：产物检测 + 初始化 + Preflight 偏好收集

### 产物探测

扫描以下目录，判断进度：

| 阶段 | 完成标志 |
|------|----------|
| product-design | `.allforai/product-map/task-inventory.json` 存在且 task 数 > 0 |
| project-setup | `.allforai/project-forge/project-manifest.json` 存在 |
| design-to-spec | `.allforai/project-forge/sub-projects/*/tasks.md` 存在 |
| seed-forge plan | `.allforai/seed-forge/seed-plan.json` 存在 |
| project-scaffold | `.allforai/project-forge/sub-projects/*/scaffold-manifest.json` 存在 |
| task-execution | `.allforai/project-forge/build-log.json` 存在 |
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
  "preflight": {
    "inferred_endpoints": ["backend", "admin", "web-customer", "mobile-native"],
    "tech_preferences": {
      "backend": {
        "template_id": "go-gin",
        "architecture": "three-layer",
        "cqrs": false
      },
      "admin": {
        "template_id": "nextjs",
        "state_management": "zustand",
        "server_cache": "tanstack-query"
      },
      "web-customer": {
        "template_id": "nextjs",
        "state_management": "zustand",
        "server_cache": "tanstack-query"
      },
      "mobile-native": {
        "template_id": "flutter"
      }
    },
    "monorepo_tool": "manual",
    "auth_strategy": "jwt",
    "confirmed_at": "ISO8601"
  },
  "phase_status": {
    "phase_1": "pending | completed | skipped",
    "phase_2": "pending | completed | skipped",
    "phase_2_5": "pending | completed | skipped",
    "phase_3": "pending | completed | skipped",
    "phase_4": "pending | in_progress | completed",
    "phase_4_5": "pending | in_progress | completed | skipped",
    "phase_5": "pending | completed | skipped",
    "phase_6": "pending | completed"
  },
  "decisions": []
}
```

### Preflight 技术偏好收集

> 目标：前置收集所有纯偏好问题，避免后续阶段中断。

**Step 2a: 推断端类型**

读取 `.allforai/product-map/role-profiles.json`：

| 条件 | 推断端类型 |
|------|-----------|
| 始终 | `backend` |
| 有 consumer 类角色 | `web-customer` |
| 有 producer / admin 类角色 | `admin` |
| 有 mobile 标记 或 screen-map 中有 mobile 界面 | `mobile-native` |

读取 `${CLAUDE_PLUGIN_ROOT}/templates/stacks.json`，按端类型过滤可选技术栈。

**Step 2b: 生成推荐配置**

基于以下规则生成推荐值（优先级：用户偏好 > 智能推断 > 默认值）：

| 配置项 | 推荐规则 |
|--------|---------|
| 后端技术栈 | 用户偏好（如 MEMORY 记录 Go+Gin → `go-gin`）> stacks.json 中 type=backend 第一个 |
| 后端架构 | product-map 聚合根 > 5 或跨域交互多 → DDD；否则 → 三层架构 |
| DDD 时 CQRS | 默认 false |
| 前端技术栈 (admin/consumer) | 后端选 Vue 系 → Nuxt；否则 → Next.js |
| 移动端技术栈 | 用户偏好（如 Flutter）> flutter（默认） |
| Monorepo 工具 | 全 TS → pnpm-workspace；混合语言 → manual；子项目 > 4 → turborepo |
| 状态管理 | React 系 → Zustand；Vue 系 → Pinia；Angular → 跳过 |
| 服务端缓存 | TanStack Query（React / Vue 通用） |
| 认证策略 | 多角色权限 → JWT；简单场景 → Session |

**Step 2c: 展示推荐配置 + 用户确认**

向用户展示推荐配置表：

~~~markdown
## Preflight — 技术偏好

从产品地图分析，你的产品需要 {N} 个端：

| 端 | 推荐技术栈 | 理由 |
|---|---|---|
| 后端 API | {stack} ({arch}) | {reason} |
| 管理后台 | {stack} | {reason} |
| 消费者 Web | {stack} | {reason} |
| 移动端 | {stack} | {reason} |

| 配置项 | 推荐值 |
|---|---|
| Monorepo | {tool} |
| 状态管理 | {lib} |
| 服务端缓存 | {lib} |
| 认证策略 | {strategy} |
~~~

AskUserQuestion：
- **全部确认** → 写入 forge-decisions.json，继续
- **逐项调整** → 对需要调整的项逐个 AskUserQuestion（仅展示 stacks.json 中该端类型的可选项），调整完后写入

**Step 2d: 写入 forge-decisions.json**

将确认后的配置写入 `forge-decisions.json` 的 `preflight` 字段（结构见「初始化决策追踪」中的 JSON schema）。

---

向用户展示探测结果 + 执行计划（含 preflight 结果摘要），确认后开始。

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

### 执行方式

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/task-execute.md`，按其工作流执行。

task-execute 自动完成：
- 加载各子项目 tasks.md + project-manifest.json
- 初始化/恢复 build-log.json
- 按 Round 结构分组，每 Round 自动推断执行策略（串行/并行）
- 逐任务委托 superpowers skill 执行
- 每 Round 结束后自动 lint/test + 增量 product-verify

### 质量门禁

| 条件 | 标准 |
|------|------|
| CORE 任务 | 全部标记 completed（build-log.json） |
| lint | 通过（或最后 Round 质量检查无 fail） |
| test | 通过（或用户确认跳过） |

**PASS** → 进入 Phase 4.5
**FAIL** → 向用户报告 build-log.json 中 failed/skipped 任务

---

## Phase 4.5：验证闭环

### 执行方式

Phase 4 完成后，运行完整验证并闭环修复：

```
Step 1: 完整产品验收
  用 Read 加载 ${CLAUDE_PLUGIN_ROOT}/skills/product-verify.md
  执行 /product-verify full（静态 + 动态）
  输出: verify-tasks.json（IMPLEMENT / REMOVE_EXTRA / FIX_FAILING）

Step 2: 跨端验证
  用 Read 加载 ${CLAUDE_PLUGIN_ROOT}/skills/e2e-verify.md
  执行 /e2e-verify full
  输出: e2e-report.json（FIX_REQUIRED 项）

Step 3: 判断是否需要修复
  汇总 verify-tasks.json 中 IMPLEMENT + FIX_FAILING 项
  汇总 e2e-report.json 中 FIX_REQUIRED 项
  无修复项 → PASS，进入 Phase 5
  有修复项 → Step 4

Step 4: 生成修复任务
  将验证发现转为原子任务，格式与 tasks.md 一致:
    - IMPLEMENT → 新增实现任务
    - FIX_FAILING → 修复任务（含失败截图/日志引用）
    - FIX_REQUIRED → 跨端修复任务
  追加到对应子项目 tasks.md 的 Fix Round（B-FIX）
  AskUserQuestion 确认修复任务列表

Step 5: 执行修复
  调用 /task-execute 执行 Fix Round
  build-log.json 追加 fix round 记录

Step 6: 回归验证
  重跑 Step 1-2（仅 scope 模式，覆盖修复涉及的 task_ids）
  仍有失败 → 记录到报告，AskUserQuestion:
    a. 再次修复（回到 Step 4）
    b. 记录为已知问题，继续
  全部通过 → PASS
```

### 质量门禁

| 条件 | 标准 |
|------|------|
| verify-tasks.json | IMPLEMENT + FIX_FAILING = 0（或用户确认跳过） |
| e2e-report.json | FIX_REQUIRED = 0（或用户确认跳过） |

**PASS** → 进入 Phase 5
**FAIL** → 用户决定继续修复 / 记录已知问题继续

---

## Phase 5：跨端验证（条件执行）

### 条件判断

检查 Phase 4.5 状态：
- Phase 4.5 **completed**（验证闭环已通过） → **跳过 Phase 5**，直接进入 Phase 6
- Phase 4.5 **skipped**（用户跳过验证闭环） → 执行 Phase 5
- Phase 4.5 中有 **DEFERRED** 项 → AskUserQuestion：执行完整 E2E / 跳过

### 执行方式（仅 Phase 4.5 被跳过时）

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
| Phase 4.5: 验证闭环 | 完成 | PASS | 修复 {N} 项，回归通过 |
| Phase 5: 跨端验证 | 完成/跳过 | PASS/SKIP | {N}/{M} 场景通过（4.5 已覆盖则跳过） |

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
