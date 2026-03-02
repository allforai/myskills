# Design-to-Spec Multi-Sub-Project Parallel Optimization — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert design-to-spec Step 1-3 from serial per-sub-project execution to backend-first + frontend-parallel Agent execution.

**Architecture:** Two-phase parallel: Phase A runs a single backend Agent (Step 1→2→2.5→3), then Phase B runs N frontend Agents in parallel (each Step 1→2→3). Orchestration logic added to `design-to-spec.md`; `project-forge.md` updated to allow Agent tool. Each Agent writes to its own isolated sub-project directory — no shard files needed.

**Tech Stack:** Claude Code Agent tool (barrier synchronization), Markdown skill file

---

### Task 1: project-forge.md — add Agent to allowed-tools and update Phase 2

**Files:**
- Modify: `dev-forge-skill/commands/project-forge.md:4` (allowed-tools)
- Modify: `dev-forge-skill/commands/project-forge.md:482-498` (Phase 2 section)

**Step 1: Add Agent to allowed-tools**

Change line 4 from:
```
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion"]
```
To:
```
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "Agent"]
```

**Step 2: Update Phase 2 execution description**

Find (lines 484-486):
```markdown
### 执行方式

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/design-to-spec.md`，按其工作流执行。
```

Replace with:
```markdown
### 执行方式

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/design-to-spec.md`，按其工作流执行。

design-to-spec 内部使用 Agent tool 并行加速：后端子项目先完成 spec，然后多个前端子项目并行生成 spec。详见 design-to-spec.md 的「并行执行编排」段落。
```

**Step 3: Commit**

```bash
git add dev-forge-skill/commands/project-forge.md
git commit -m "feat: add Agent to project-forge allowed-tools for parallel spec generation"
```

---

### Task 2: design-to-spec.md — update workflow code block with parallel flow

**Files:**
- Modify: `dev-forge-skill/skills/design-to-spec.md:199-354` (workflow code block)

This task updates the workflow code block to show the parallel structure and marks Step 1-3 as Agent-executed.

**Step 1: Insert parallel orchestration overview after Step 0**

Find (lines 219-221):
```
  → 更新 project-manifest.json
  ↓
Step 1: Requirements 生成（逐子项目）
```

Replace with:
```
  → 更新 project-manifest.json
  ↓
并行执行编排（详见「## 并行执行编排」段落）:
  子项目分类:
    后端组: type = "backend"（通常 1 个）
    前端组: 其余所有子项目（admin/web-customer/web-mobile/mobile-native）
  Phase A — 后端 Agent（1 个 Agent 调用）:
    Agent(backend): Step 1 → Step 2 → Step 2.5 → Step 3
    ↓ 完成后
  Phase B — 前端并行 Agent（单条消息发出 N 个 Agent 调用）:
    ┌── Agent(前端1): Step 1 → Step 2 → Step 3
    ├── Agent(前端2): Step 1 → Step 2 → Step 3
    └── Agent(前端N): Step 1 → Step 2 → Step 3
    全部完成 ↓
  以下 Step 1-3 描述每个 Agent 内部执行的步骤内容:
  ↓
Step 1: Requirements 生成
```

**Step 2: Update Step 1 body**

Find (line 222):
```
  对每个子项目:
```

Replace with:
```
  每个 Agent 对其负责的子项目:
```

**Step 3: Update Step 2 header**

Find (line 246):
```
Step 2: Design 生成（逐子项目，API-first 策略）
```

Replace with:
```
Step 2: Design 生成（API-first 策略）
```

**Step 4: Update Step 2 body**

Find (line 248):
```
  对每个子项目，基于 tech-profile 映射:
```

Replace with:
```
  每个 Agent 对其子项目，基于 tech-profile 映射:
```

**Step 5: Update Step 2 generation order note**

Find (line 297):
```
  **生成顺序**: 后端 design.md 先于前端，确保前端 design 可直接引用 API 端点定义
```

Replace with:
```
  **生成顺序**: 后端 Agent (Phase A) 先于前端 Agent (Phase B)，确保前端 design 可直接引用 API 端点定义
```

**Step 6: Update Step 2.5 header**

Find (line 299):
```
Step 2.5: Design 交叉审查（OpenRouter 可用时）
```

Replace with:
```
Step 2.5: Design 交叉审查（由后端 Agent 在 Phase A 内执行，OpenRouter 可用时）
```

**Step 7: Update Step 3 header**

Find (line 317):
```
Step 3: Tasks 生成（逐子项目）
```

Replace with:
```
Step 3: Tasks 生成
```

**Step 8: Commit**

```bash
git add dev-forge-skill/skills/design-to-spec.md
git commit -m "feat: update design-to-spec workflow to show parallel Phase A/B flow"
```

---

### Task 3: design-to-spec.md — add parallel execution orchestration section

**Files:**
- Modify: `dev-forge-skill/skills/design-to-spec.md` (insert after `## 工作流` section, before `## 任务 Batch 结构`)

This is the core addition. Insert a new top-level section between the workflow code block closing (line 354) and the `---` separator (line 356).

**Step 1: Insert the new section**

Find (lines 354-358):
```markdown
```

---

## 任务 Batch 结构
```

Replace with:
````markdown
```

---

## 并行执行编排

> Step 1-3 由 Agent 并行执行，编排器负责分类、调度和聚合。
> 本段描述 Agent 调度逻辑，Step 1-3 的具体内容见上方「工作流」段落。

### 子项目分类

编排器读取 `project-manifest.json`，将子项目分为两组：

| 组 | 条件 | 典型子项目 |
|----|------|-----------|
| 后端组 | `type = "backend"` | api-backend |
| 前端组 | 其余所有类型 | admin, web-customer, web-mobile, mobile-native |

### Phase A — 后端 Agent

启动 1 个 Agent 处理后端子项目，完整执行 Step 1 → Step 2 → Step 2.5 → Step 3。

Agent 产出：
```
.allforai/project-forge/sub-projects/{backend-name}/
├── requirements.md    # Step 1
├── design.md          # Step 2 + Step 2.5 审查结果
└── tasks.md           # Step 3
```

### Phase B — 前端并行 Agent

后端 Agent 完成后，用**单条消息发出 N 个 Agent tool 调用**并行执行。
Agent tool 的屏障同步机制保证所有前端 Agent 完成后才继续到 Step 4。

每个前端 Agent 完整执行 Step 1 → Step 2 → Step 3（不执行 Step 2.5）。

每个 Agent 产出：
```
.allforai/project-forge/sub-projects/{frontend-name}/
├── requirements.md    # Step 1
├── design.md          # Step 2
└── tasks.md           # Step 3
```

### Agent prompt 模板

~~~
你是 design-to-spec 的并行执行器。

任务: 为子项目 {sub-project-name} 生成完整的 spec 文档。

执行步骤:
1. 用 Read 工具加载 ${CLAUDE_PLUGIN_ROOT}/skills/design-to-spec.md（仅参考规则和模板，不重复全局步骤）
2. 按 Step 1 (requirements) → Step 2 (design) [→ Step 2.5 仅后端] → Step 3 (tasks) 执行
3. 产出写入 .allforai/project-forge/sub-projects/{sub-project-name}/

子项目信息:
- name: {name}
- type: {type}
- tech_stack: {tech_stack}
- assigned_modules: {modules}

上下文:
- project-manifest.json: .allforai/project-forge/project-manifest.json
- forge-decisions.json: .allforai/project-forge/forge-decisions.json（technical_spikes + coding_principles）
- 产品设计产物: .allforai/product-map/, .allforai/screen-map/ 等
- 后端 design.md: .allforai/project-forge/sub-projects/{backend-name}/design.md（仅前端 Agent 引用）
{自动模式标记: __orchestrator_auto: true（若自动模式激活）}

重要:
- 仅处理本子项目，不读写其他子项目的产出目录
- 按端差异化规则生成（参考 design-to-spec.md 的「各端差异化 Spec 生成」表格）
- 遵循两阶段加载（先 index 再 full data）
- 前端 Agent: API 调用必须引用后端 design.md 中已定义的端点 ID
- 预置脚本优先: 检查 ${CLAUDE_PLUGIN_ROOT}/scripts/ 是否有可用脚本
~~~

Agent 调用参数：

| Agent | Phase | 子项目类型 | 执行步骤 | 产出目录 |
|-------|-------|-----------|---------|---------|
| 后端 Agent | A | backend | Step 1→2→2.5→3 | `.allforai/project-forge/sub-projects/{backend}/` |
| 前端 Agent 1 | B | admin | Step 1→2→3 | `.allforai/project-forge/sub-projects/{admin}/` |
| 前端 Agent 2 | B | web-customer | Step 1→2→3 | `.allforai/project-forge/sub-projects/{web}/` |
| 前端 Agent N | B | mobile-native | Step 1→2→3 | `.allforai/project-forge/sub-projects/{mobile}/` |

### 错误处理

~~~
Phase A (后端 Agent):
  成功 → 进入 Phase B
  失败 →
    向用户报告错误原因
    询问: 重试 / 中止
    注: 后端失败不可跳过（前端依赖后端 design.md）

Phase B (前端 Agent 并行):
  全部成功 → 进入 Step 4
  部分失败 →
    成功的 Agent: 正常收集产出
    失败的 Agent: 记录错误信息
    向用户报告:
      "前端并行执行结果:
       ✓ admin: 完成 (requirements: N, design: N API, tasks: N)
       ✗ web-customer: 失败 — {错误原因}
       ✓ mobile: 完成 (requirements: N, design: N 页面, tasks: N)"
    询问:
      1. 重试失败的子项目（仅重跑失败的 Agent）
      2. 跳过继续到 Step 4（依赖分析标注缺失子项目）
      3. 中止流程
  全部失败 →
    向用户报告所有错误
    询问: 全部重试 / 中止

自动模式:
  后端 Agent 失败 → ERROR（停）
  前端 Agent 部分失败 → WARNING（记日志继续到 Step 4）
  前端 Agent 全部失败 → ERROR（停）
~~~

### resume 模式下的并行处理

~~~
resume 模式检测 Step 1-3 完成状态:
  检测方式: 检查 .allforai/project-forge/sub-projects/{name}/ 下三件套
    - requirements.md 存在
    - design.md 存在
    - tasks.md 存在
  三件全 → 该子项目已完成

  判定:
    后端 + 所有前端三件套全存在 → 跳过 Step 1-3，进入 Step 4
    后端三件套存在，部分前端缺失 → 跳过 Phase A，Phase B 仅启动缺失子项目的 Agent
    后端三件套缺失 → 从 Phase A 重新开始（全量执行）
~~~

### 单子项目退化

仅有 1 个后端子项目、无前端子项目时，Phase B 不启动任何 Agent，自动退化为纯串行执行。

---

## 任务 Batch 结构
````

**Step 2: Commit**

```bash
git add dev-forge-skill/skills/design-to-spec.md
git commit -m "feat: add parallel execution orchestration section to design-to-spec"
```

---

### Task 4: design-to-spec.md — update summary template and 铁律

**Files:**
- Modify: `dev-forge-skill/skills/design-to-spec.md` (Step 5 summary in workflow code block)
- Modify: `dev-forge-skill/skills/design-to-spec.md` (铁律 section)

**Step 1: Update Step 5 summary template**

Find the Step 5 summary table in the workflow code block (lines 341-353):
```
Step 5: 阶段末汇总确认
  展示全部生成结果摘要:

  | 子项目 | requirements | design | tasks |
  |--------|-------------|--------|-------|
  | {name} | {N} 需求项 | {N} API端点, {M} 页面 | {N} 任务 |
  | ... | ... | ... | ... |

  跨项目依赖: {N} 条
  执行顺序: B0 → B1(并行) → B2 → B3(并行) → B4 → B5
  总任务数: CORE {N} + DEFER {M}

  → 输出汇总进度「Phase 2 ✓ {N} 子项目 × 3 文档, CORE {M} 任务」（不停）
```

Replace with:
```
Step 5: 阶段末汇总确认
  展示全部生成结果摘要:

  Phase A (后端):
  | 子项目 | requirements | design | tasks | Step 2.5 审查 |
  |--------|-------------|--------|-------|--------------|
  | {backend} | {N} 需求项 | {N} API端点 | {N} 任务 | API {N} issues, Model {M} violations |

  Phase B (前端并行):
  | 子项目 | requirements | design | tasks | 状态 |
  |--------|-------------|--------|-------|------|
  | {admin} | {N} 需求项 | {N} 页面 | {N} 任务 | 完成/失败 |
  | {web} | {N} 需求项 | {N} 页面 | {N} 任务 | 完成/失败 |
  | {mobile} | {N} 需求项 | {N} 页面 | {N} 任务 | 完成/失败 |

  跨项目依赖: {N} 条
  执行顺序: B0 → B1(并行) → B2 → B3(并行) → B4 → B5
  总任务数: CORE {N} + DEFER {M}

  → 输出汇总进度「Phase 2 ✓ {N} 子项目 × 3 文档 (Phase A 串行 + Phase B 并行), CORE {M} 任务」（不停）
```

**Step 2: Add 铁律 rule 6**

Find the end of the 铁律 section (lines 508-510):
```markdown
### 5. 跨项目依赖显式声明

后端 B2 → 前端 B4 的依赖、共享类型的依赖，都在 Step 4 中显式声明并写入 execution_order。
```

After it, append:
```markdown

### 6. 并行 Agent 产出隔离

Phase A/B 的并行 Agent 各自写入独立子项目目录（`.allforai/project-forge/sub-projects/{name}/`），不读写其他 Agent 的产出。唯一跨 Agent 引用：前端 Agent 只读后端 design.md（API 端点定义），不修改。
```

**Step 3: Commit**

```bash
git add dev-forge-skill/skills/design-to-spec.md
git commit -m "docs: update summary template and add parallel isolation rule"
```

---

### Task 5: Final review — read both modified files and verify consistency

**Files:**
- Read: `dev-forge-skill/commands/project-forge.md` (full file)
- Read: `dev-forge-skill/skills/design-to-spec.md` (full file)

**Step 1: Read both files**

Verify:
- [ ] `project-forge.md` `allowed-tools` includes `"Agent"`
- [ ] `project-forge.md` Phase 2 mentions parallel execution
- [ ] `design-to-spec.md` workflow code block has parallel orchestration overview after Step 0
- [ ] `design-to-spec.md` Step 1 header no longer says "逐子项目"
- [ ] `design-to-spec.md` Step 2 header no longer says "逐子项目"
- [ ] `design-to-spec.md` Step 2.5 header mentions "后端 Agent 在 Phase A 内执行"
- [ ] `design-to-spec.md` Step 3 header no longer says "逐子项目"
- [ ] `design-to-spec.md` has `## 并行执行编排` section with: sub-project classification, Phase A, Phase B, Agent prompt template, error handling, resume mode
- [ ] `design-to-spec.md` Step 5 summary shows Phase A/B grouping
- [ ] `design-to-spec.md` 铁律 has rule 6 about parallel isolation
- [ ] No accidental deletions of Step 0, Step 4, Step 5, or any non-workflow content
- [ ] All existing sections (增强协议, 规格生成原则, 核心映射逻辑, 各端差异化, 任务 Batch 结构, 原子任务格式, 输出文件) remain intact

**Step 2: Commit (if any fixups needed)**

```bash
git add dev-forge-skill/skills/design-to-spec.md dev-forge-skill/commands/project-forge.md
git commit -m "fix: consistency fixes for design-to-spec parallel optimization"
```
