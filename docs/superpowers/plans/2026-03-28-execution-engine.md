# Execution Engine Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the execution engine protocol (subagent isolation + upstream feedback loop) to all 6 skills across 3 platforms, so every skill's "full" mode uses subagent dispatch with clean context per phase and downstream-to-upstream defect feedback.

**Architecture:** Write one canonical protocol doc per skill (in `docs/execution-engine.md`), add phase declarations to each SKILL.md, and rewrite orchestration commands to use the dispatch + feedback pattern. Codex/opencode sync via parallel agents at the end.

**Tech Stack:** Markdown skill files (LLM-interpreted, no code runtime)

---

### Task 1: Write the canonical execution engine protocol document

This is the shared reference doc that every skill's main flow and subagents will read. It lives inside each skill's `docs/` directory (because `${CLAUDE_PLUGIN_ROOT}` is per-plugin). We write one canonical version first, then copy it into each skill.

**Files:**
- Create: `claude/product-design-skill/docs/execution-engine.md`

- [ ] **Step 1: Write the protocol document**

```markdown
# Execution Engine Protocol

> 本文件定义所有 skill 通用的执行引擎协议。主流程（调度器）和 subagent（执行者）都必须遵守。

## 1. 主流程角色：纯调度器

主流程**不执行任何业务逻辑**。职责仅有三项：

1. **读状态**：当前阶段、上一个 subagent 返回结果
2. **决策路由**：正常 → 下一阶段；UPSTREAM_DEFECT → 回退到目标阶段
3. **Dispatch subagent**：按任务模板组装 prompt → Agent tool 发出

### 主流程 context 只包含

- 本 skill 的 phase 声明（SKILL.md 中的 YAML）
- 当前进度（哪些阶段已完成、当前在哪）
- 最近阶段的摘要（≤500 字/阶段）
- 累积的 UPSTREAM_DEFECT 记录（如有）

### 不在主流程 context 里

- 铁律/规则全文 → subagent 自己 Read
- 源代码 → subagent 自己 Read
- 中间产物详情 → 写入 .allforai/，subagent 自己 Read

## 2. Subagent 任务模板

每个 subagent 被 dispatch 时，主流程用以下模板组装 prompt：

```
## 任务
{phase.id}：{phase.subagent_task}

## 输入
- 读取以下产物文件：{phase.input 列表，每行一个路径}
- 上游摘要：{主流程选择性注入的前序阶段摘要，仅注入与当前阶段相关的}
{仅回退时}
- 修复上下文：{UPSTREAM_DEFECT 信号全文，含 evidence 和 suggested_fix}

## 规则
读取以下规则文件后执行（按顺序读取，全部读完再开始执行）：
{phase.rules 列表，每行一个路径}

## 输出要求
1. 产物文件：写入 {phase.output}
2. 阶段摘要：任务完成后返回 ≤500 字摘要，包含：
   - 关键决策（做了什么、为什么这么做）
   - 发现的异常/风险
   - 下游需要注意的事项
3. 缺陷信号：若发现上游产物有问题（缺失、矛盾、不完整），按以下格式返回：
   {"signal":"UPSTREAM_DEFECT","source_phase":"当前阶段","target_phase":"应该修的阶段","defect_type":"LLM自行描述","evidence":"具体证据","severity":"blocker|warning","suggested_fix":"建议修复方向"}
   无上游问题则不返回此字段。
```

## 3. 信息共享机制

### 3.1 产物文件（主通道）

每个阶段的 subagent 将产出写入 `.allforai/` 目录。下游 subagent 通过 Read 工具按需读取。

### 3.2 阶段摘要（辅助通道）

每个 subagent 完成时返回 ≤500 字摘要。主流程判断哪些摘要与下一阶段相关，选择性注入。

**选择性注入原则**：
- 直接前置阶段的摘要：默认注入
- 非直接前置阶段：仅当其摘要中提到与当前阶段相关的风险/注意事项时注入
- 摘要总量控制：注入给单个 subagent 的摘要总计不超过 1500 字

## 4. 下游回退协议

### 4.1 回退决策

```
severity = blocker → 立即暂停当前阶段，dispatch 目标阶段 subagent 修复
severity = warning → 记录，继续当前阶段，当前阶段完成后再 dispatch 修复
```

### 4.2 回退执行

1. 主流程解析 target_phase → 找到对应阶段声明
2. Dispatch 修复 subagent：注入 UPSTREAM_DEFECT 信号作为修复任务（不重跑整个阶段）
3. 修复 subagent 更新产物文件 → 返回修复摘要
4. 主流程把修复摘要注入当前阶段 subagent → 从断点继续

### 4.3 防无限回退

- 同一 {source_phase, target_phase} 对最多回退 2 次
- 第 3 次 → 标记 UNRESOLVED_DEFECT，继续执行，最终报告标红
- 此约束协议级，与具体 skill 无关

### 4.4 跨 skill 回退

协议不区分 skill 内和跨 skill。target_phase 格式为 `{skill}.{phase}`（如 `product-design.use-case`）。主流程加载目标 skill 的阶段声明，dispatch 修复 subagent。

## 5. Phase 声明格式

每个 skill 在 SKILL.md 中用 YAML 声明阶段结构：

```yaml
phases:
  - id: <阶段ID>
    subagent_task: "<一句话任务描述>"
    input: [<产物文件路径>]
    output: "<输出路径>"
    rules: ["${PLUGIN_ROOT}/<规则文件路径>"]
    depends_on: [<前置阶段ID>]
```

- depends_on 为空的阶段可并行 dispatch
- 主流程（LLM）直接理解 YAML，无需 parser
```

- [ ] **Step 2: Verify the document is self-contained**

Read through the written file. Confirm: no TBD, no references to external docs that don't exist, all sections complete.

- [ ] **Step 3: Commit**

```bash
git add claude/product-design-skill/docs/execution-engine.md
git commit -m "docs: execution engine protocol — subagent isolation + upstream feedback"
```

---

### Task 2: Add phase declarations to product-design-skill

**Files:**
- Modify: `claude/product-design-skill/SKILL.md`
- Copy: `claude/product-design-skill/docs/execution-engine.md` (from Task 1)

- [ ] **Step 1: Read current SKILL.md**

Read the full file to understand current structure.

- [ ] **Step 2: Add execution engine reference and phase declarations**

Add to the top of the orchestration section in SKILL.md:

```yaml
# execution-engine: ${CLAUDE_PLUGIN_ROOT}/docs/execution-engine.md

phases:
  - id: product-concept
    subagent_task: "发现产品愿景：分析用户需求，输出产品概念"
    input: []
    output: ".allforai/product-concept.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/product-concept.md"]

  - id: product-map
    subagent_task: "构建产品地图：角色、任务、约束、业务流、数据模型"
    input: [".allforai/product-concept.json", "项目代码库"]
    output: ".allforai/product-map/"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/product-map.md"]
    depends_on: [product-concept]

  - id: journey-emotion
    subagent_task: "绘制情感旅程：识别用户在每个任务中的情感波动和决策点"
    input: [".allforai/product-map/"]
    output: ".allforai/experience-map/journey-emotion-map.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/journey-emotion.md"]
    depends_on: [product-map]

  - id: experience-map
    subagent_task: "构建体验地图：将情感旅程转化为界面体验设计"
    input: [".allforai/product-map/", ".allforai/experience-map/journey-emotion-map.json"]
    output: ".allforai/experience-map/experience-map.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/experience-map.md"]
    depends_on: [journey-emotion]

  - id: interaction-gate
    subagent_task: "交互质量门禁：评估体验地图的交互成熟度"
    input: [".allforai/experience-map/experience-map.json"]
    output: ".allforai/experience-map/interaction-gate.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/interaction-gate.md"]
    depends_on: [experience-map]

  - id: use-case
    subagent_task: "生成用例树：从产品地图和体验地图推导完整用例"
    input: [".allforai/product-map/", ".allforai/experience-map/"]
    output: ".allforai/use-case/"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/use-case.md"]
    depends_on: [interaction-gate]

  - id: feature-gap
    subagent_task: "分析功能缺口：对比用例树和现有实现，识别缺失功能"
    input: [".allforai/product-map/", ".allforai/experience-map/", ".allforai/use-case/"]
    output: ".allforai/feature-gap/"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/feature-gap.md"]
    depends_on: [interaction-gate]

  - id: ui-design
    subagent_task: "生成 UI 设计规格：基于体验地图输出界面设计"
    input: [".allforai/product-map/", ".allforai/experience-map/"]
    output: ".allforai/ui-design/"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/ui-design.md"]
    depends_on: [interaction-gate]

  - id: design-audit
    subagent_task: "设计审计：跨层一致性检查（追溯、覆盖、交叉一致性）"
    input: [".allforai/product-map/", ".allforai/experience-map/", ".allforai/use-case/", ".allforai/feature-gap/", ".allforai/ui-design/"]
    output: ".allforai/design-audit/"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/design-audit.md"]
    depends_on: [use-case, feature-gap, ui-design]
```

Note: `use-case`, `feature-gap`, `ui-design` share the same `depends_on: [interaction-gate]` — they can be dispatched in parallel.

- [ ] **Step 3: Rewrite the `full` mode orchestration section**

Replace the current sequential phase list with dispatcher instructions:

```markdown
## full 模式执行

读取 `${CLAUDE_PLUGIN_ROOT}/docs/execution-engine.md` 获取调度协议。

主流程作为纯调度器执行：
1. 按 phases 声明的 depends_on 拓扑排序
2. 逐阶段（或并行）dispatch subagent，使用协议中的任务模板
3. 收集阶段摘要，选择性注入给下一阶段
4. 收到 UPSTREAM_DEFECT 时按协议回退
5. 所有阶段完成后输出最终报告
```

- [ ] **Step 4: Run a consistency check**

Verify: every phase.id matches a real skill file, every input/output path matches the existing `.allforai/` data contract in CLAUDE.md.

- [ ] **Step 5: Commit**

```bash
git add claude/product-design-skill/SKILL.md
git commit -m "feat(product-design): add execution engine phase declarations + dispatcher orchestration"
```

---

### Task 3: Add phase declarations to dev-forge-skill

**Files:**
- Modify: `claude/dev-forge-skill/SKILL.md`
- Copy: `claude/dev-forge-skill/docs/execution-engine.md` (from Task 1)

- [ ] **Step 1: Read current SKILL.md**

- [ ] **Step 2: Copy execution-engine.md into docs/**

```bash
cp claude/product-design-skill/docs/execution-engine.md claude/dev-forge-skill/docs/execution-engine.md
```

- [ ] **Step 3: Add phase declarations to SKILL.md**

```yaml
# execution-engine: ${CLAUDE_PLUGIN_ROOT}/docs/execution-engine.md

phases:
  - id: project-setup
    subagent_task: "项目初始化：探测技术栈、生成项目清单、配置开发环境"
    input: ["项目代码库"]
    output: ".allforai/project-manifest.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/project-setup.md"]

  - id: design-to-spec
    subagent_task: "设计转规格：FVL 闭环（4D 分解 → 6V 审计 → XV 交叉验证）"
    input: [".allforai/product-map/", ".allforai/experience-map/", ".allforai/use-case/", ".allforai/ui-design/", ".allforai/project-manifest.json"]
    output: ".allforai/dev-forge/requirements.md, .allforai/dev-forge/design.json, .allforai/dev-forge/tasks.md"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/design-to-spec.md"]
    depends_on: [project-setup]

  - id: task-execute
    subagent_task: "执行开发任务：按 tasks.md 逐任务实现，含增量 XV 验证"
    input: [".allforai/dev-forge/requirements.md", ".allforai/dev-forge/design.json", ".allforai/dev-forge/tasks.md"]
    output: "代码变更 + .allforai/dev-forge/build-log.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/task-execute.md", "${CLAUDE_PLUGIN_ROOT}/docs/skill-commons.md"]
    depends_on: [design-to-spec]

  - id: product-verify
    subagent_task: "产品验收：静态分析 + Playwright 动态验证"
    input: ["项目代码库", ".allforai/dev-forge/design.json"]
    output: ".allforai/product-verify/"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/product-verify.md"]
    depends_on: [task-execute]

  - id: deadhunt
    subagent_task: "死链猎杀：死链 + CRUD 缺口 + 幽灵功能 + 接缝检查"
    input: ["项目代码库"]
    output: ".allforai/deadhunt/"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/deadhunt.md"]
    depends_on: [task-execute]

  - id: fieldcheck
    subagent_task: "字段一致性：UI↔API↔Entity↔DB 四层字段检查"
    input: ["项目代码库"]
    output: ".allforai/fieldcheck/"
    rules: ["${CLAUDE_PLUGIN_ROOT}/commands/fieldcheck.md"]
    depends_on: [task-execute]

  - id: testforge
    subagent_task: "测试锻造：审计测试缺口 → 补测试 → 修 bug → 收敛"
    input: ["项目代码库", ".allforai/dev-forge/design.json", ".allforai/dev-forge/tasks.md"]
    output: ".allforai/testforge/"
    rules: ["${CLAUDE_PLUGIN_ROOT}/commands/testforge.md"]
    depends_on: [task-execute]
```

Note: `product-verify`, `deadhunt`, `fieldcheck` all depend only on `task-execute` — they can be dispatched in parallel. `testforge` also depends on `task-execute` and can run in parallel with the above three.

- [ ] **Step 4: Rewrite the `full` mode orchestration section**

Same dispatcher pattern as Task 2 Step 3.

- [ ] **Step 5: Commit**

```bash
git add claude/dev-forge-skill/SKILL.md claude/dev-forge-skill/docs/execution-engine.md
git commit -m "feat(dev-forge): add execution engine phase declarations + dispatcher orchestration"
```

---

### Task 4: Add phase declarations to demo-forge-skill

**Files:**
- Modify: `claude/demo-forge-skill/SKILL.md`
- Copy: `claude/demo-forge-skill/docs/execution-engine.md` (from Task 1)

- [ ] **Step 1: Read current SKILL.md**

- [ ] **Step 2: Copy execution-engine.md into docs/**

```bash
cp claude/product-design-skill/docs/execution-engine.md claude/demo-forge-skill/docs/execution-engine.md
```

- [ ] **Step 3: Add phase declarations to SKILL.md**

```yaml
# execution-engine: ${CLAUDE_PLUGIN_ROOT}/docs/execution-engine.md

phases:
  - id: design
    subagent_task: "设计 demo 数据方案：实体清单、场景链路、API 端点映射"
    input: [".allforai/product-map/", ".allforai/experience-map/"]
    output: ".allforai/demo-forge/demo-plan.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/demo-design.md"]

  - id: media
    subagent_task: "获取/生成 demo 媒体素材并上传"
    input: [".allforai/demo-forge/demo-plan.json"]
    output: ".allforai/demo-forge/upload-mapping.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/media-forge.md"]
    depends_on: [design]

  - id: execute
    subagent_task: "通过 API 灌入全部 demo 数据（灌入即集成测试）"
    input: [".allforai/demo-forge/demo-plan.json", ".allforai/demo-forge/upload-mapping.json"]
    output: ".allforai/demo-forge/forge-data.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/demo-execute.md"]
    depends_on: [design, media]

  - id: verify
    subagent_task: "验证 demo 数据的视觉完整性（V1-V7 层 + V8 路由）"
    input: [".allforai/demo-forge/forge-data.json"]
    output: ".allforai/demo-forge/verify-report.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/demo-verify.md"]
    depends_on: [execute]
```

Note: verify failures that route back to `design`, `execute`, or `dev_task` now use the UPSTREAM_DEFECT protocol instead of the custom V8 routing table. The V8 routing logic in demo-verify.md should be updated to emit UPSTREAM_DEFECT signals.

- [ ] **Step 4: Update demo-verify.md V8 routing to emit UPSTREAM_DEFECT**

Read `claude/demo-forge-skill/skills/demo-verify.md`. Find the V8 routing table. Rewrite it so that:
- `route: design` → emit `UPSTREAM_DEFECT` with `target_phase: "demo-forge.design"`
- `route: media` → emit `UPSTREAM_DEFECT` with `target_phase: "demo-forge.media"`
- `route: execute` → emit `UPSTREAM_DEFECT` with `target_phase: "demo-forge.execute"`
- `route: dev_task` → emit `UPSTREAM_DEFECT` with `target_phase: "dev-forge.task-execute"`
- `route: skip` → no signal, just log

- [ ] **Step 5: Rewrite the `full` mode orchestration**

Same dispatcher pattern. The existing "max 3 repair rounds" becomes the protocol's "max 2 retries per {source, target} pair".

- [ ] **Step 6: Commit**

```bash
git add claude/demo-forge-skill/
git commit -m "feat(demo-forge): add execution engine phase declarations + UPSTREAM_DEFECT routing"
```

---

### Task 5: Add phase declarations to code-tuner-skill

**Files:**
- Modify: `claude/code-tuner-skill/SKILL.md`
- Copy: `claude/code-tuner-skill/docs/execution-engine.md` (from Task 1)

- [ ] **Step 1: Read current SKILL.md**

- [ ] **Step 2: Copy execution-engine.md and add phase declarations**

```yaml
# execution-engine: ${CLAUDE_PLUGIN_ROOT}/docs/execution-engine.md

phases:
  - id: profile
    subagent_task: "项目画像：探测技术栈、架构类型、分层结构、模块划分"
    input: ["项目代码库"]
    output: ".allforai/code-tuner/tuner-profile.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/references/phase0-profile.md", "${CLAUDE_PLUGIN_ROOT}/references/layer-mapping.md"]

  - id: compliance
    subagent_task: "架构合规检查：依赖方向、分层规则、跨架构通用规则"
    input: [".allforai/code-tuner/tuner-profile.json", "项目代码库"]
    output: ".allforai/code-tuner/phase1-compliance.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/references/phase1-compliance.md"]
    depends_on: [profile]

  - id: duplicates
    subagent_task: "重复检测：API/Service/Data/Utility 四层扫描"
    input: [".allforai/code-tuner/tuner-profile.json", "项目代码库"]
    output: ".allforai/code-tuner/phase2-duplicates.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/references/phase2-duplicates.md"]
    depends_on: [profile]

  - id: abstractions
    subagent_task: "抽象分析：垂直/水平/接口合并/验证逻辑/过度抽象"
    input: [".allforai/code-tuner/tuner-profile.json", "项目代码库"]
    output: ".allforai/code-tuner/phase3-abstractions.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/references/phase3-abstractions.md"]
    depends_on: [profile]

  - id: report
    subagent_task: "综合报告：5维评分 + 热力图 + 重构任务清单"
    input: [".allforai/code-tuner/phase1-compliance.json", ".allforai/code-tuner/phase2-duplicates.json", ".allforai/code-tuner/phase3-abstractions.json"]
    output: ".allforai/code-tuner/tuner-report.md, .allforai/code-tuner/tuner-tasks.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/references/phase4-report.md"]
    depends_on: [compliance, duplicates, abstractions]
```

Note: `compliance`, `duplicates`, `abstractions` all depend only on `profile` — dispatch in parallel.

- [ ] **Step 3: Rewrite orchestration section**

- [ ] **Step 4: Commit**

```bash
git add claude/code-tuner-skill/
git commit -m "feat(code-tuner): add execution engine phase declarations + parallel analysis dispatch"
```

---

### Task 6: Add phase declarations to code-replicate-skill

**Files:**
- Modify: `claude/code-replicate-skill/SKILL.md`
- Copy: `claude/code-replicate-skill/docs/execution-engine.md` (from Task 1)

- [ ] **Step 1: Read current SKILL.md**

- [ ] **Step 2: Copy execution-engine.md and add phase declarations**

```yaml
# execution-engine: ${CLAUDE_PLUGIN_ROOT}/docs/execution-engine.md

phases:
  - id: preflight
    subagent_task: "预检：收集参数、克隆源码、确认复刻范围"
    input: ["用户输入"]
    output: ".allforai/code-replicate/replicate-config.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md"]

  - id: discovery
    subagent_task: "发现：扫描源码结构、模块摘要、基础设施清单、抽象提取"
    input: [".allforai/code-replicate/replicate-config.json", "源代码库"]
    output: ".allforai/code-replicate/discovery-profile.json, .allforai/code-replicate/extraction-plan.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/docs/analysis-principles.md"]
    depends_on: [preflight]

  - id: generate
    subagent_task: "生成：按模块 LLM 生成 → 脚本合并 → 标准产物"
    input: [".allforai/code-replicate/extraction-plan.json", "源代码库"]
    output: ".allforai/product-map/, .allforai/experience-map/"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md"]
    depends_on: [discovery]

  - id: verify
    subagent_task: "验证：schema 校验 + XV 交叉验证 + 还原度报告"
    input: [".allforai/product-map/", ".allforai/experience-map/", ".allforai/code-replicate/extraction-plan.json"]
    output: ".allforai/code-replicate/replicate-report.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/cr-fidelity.md"]
    depends_on: [generate]
```

- [ ] **Step 3: Rewrite orchestration section**

- [ ] **Step 4: Commit**

```bash
git add claude/code-replicate-skill/
git commit -m "feat(code-replicate): add execution engine phase declarations"
```

---

### Task 7: Add phase declarations to ui-forge-skill

**Files:**
- Modify: `claude/ui-forge-skill/SKILL.md`
- Copy: `claude/ui-forge-skill/docs/execution-engine.md` (from Task 1)

- [ ] **Step 1: Read current SKILL.md**

- [ ] **Step 2: Copy execution-engine.md and add phase declarations**

```yaml
# execution-engine: ${CLAUDE_PLUGIN_ROOT}/docs/execution-engine.md

phases:
  - id: fidelity-check
    subagent_task: "还原度检测：对比设计规格与当前实现的偏差"
    input: [".allforai/ui-design/", "前端代码库"]
    output: ".allforai/ui-forge/fidelity-assessment.json"
    rules: ["${CLAUDE_PLUGIN_ROOT}/docs/fidelity-checklist.md"]

  - id: restore
    subagent_task: "还原修复：按设计规格修复实现偏差"
    input: [".allforai/ui-forge/fidelity-assessment.json", ".allforai/ui-design/"]
    output: "代码变更"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/ui-forge.md"]
    depends_on: [fidelity-check]

  - id: polish
    subagent_task: "视觉打磨：层次、响应式、状态设计、微交互增强"
    input: [".allforai/ui-design/", "前端代码库"]
    output: "代码变更"
    rules: ["${CLAUDE_PLUGIN_ROOT}/skills/ui-forge.md"]
    depends_on: [restore]
```

- [ ] **Step 3: Rewrite orchestration section**

- [ ] **Step 4: Commit**

```bash
git add claude/ui-forge-skill/
git commit -m "feat(ui-forge): add execution engine phase declarations"
```

---

### Task 8: Sync to codex and opencode platforms

Each platform has its own entry point convention (codex: AGENTS.md + execution-playbook.md, opencode: SKILL.md + skills.json). The phase declarations need to be adapted to each platform's format.

**Files:**
- Modify: `codex/{each-skill}/SKILL.md` or `AGENTS.md` + `execution-playbook.md`
- Modify: `opencode/{each-skill}/SKILL.md`
- Copy: `execution-engine.md` into each skill's docs/

- [ ] **Step 1: Copy execution-engine.md to all codex skills**

```bash
for skill in product-design-skill dev-forge-skill demo-forge-skill code-tuner-skill code-replicate-skill ui-forge-skill; do
  cp claude/product-design-skill/docs/execution-engine.md codex/$skill/docs/execution-engine.md
done
```

- [ ] **Step 2: Copy execution-engine.md to all opencode skills**

```bash
for skill in product-design-skill dev-forge-skill demo-forge-skill code-tuner-skill code-replicate-skill ui-forge-skill; do
  cp claude/product-design-skill/docs/execution-engine.md opencode/$skill/docs/execution-engine.md
done
```

- [ ] **Step 3: Add phase declarations to each codex skill**

For each codex skill, read its SKILL.md (or AGENTS.md + execution-playbook.md), then add the same phase YAML from the corresponding claude skill Task (2-7). Adapt tool references if needed (codex uses relative paths instead of `${CLAUDE_PLUGIN_ROOT}`).

- [ ] **Step 4: Add phase declarations to each opencode skill**

Same as Step 3 but for opencode platform. Adapt to opencode conventions.

- [ ] **Step 5: Commit**

```bash
git add codex/ opencode/
git commit -m "feat: sync execution engine protocol to codex and opencode platforms"
```

---

### Task 9: Final verification

- [ ] **Step 1: Verify protocol doc exists in all 18 skill directories**

```bash
for platform in claude codex opencode; do
  for skill in product-design-skill dev-forge-skill demo-forge-skill code-tuner-skill code-replicate-skill ui-forge-skill; do
    test -f $platform/$skill/docs/execution-engine.md && echo "OK: $platform/$skill" || echo "MISSING: $platform/$skill"
  done
done
```

Expected: 18 lines of "OK".

- [ ] **Step 2: Verify all claude SKILL.md files contain phase declarations**

```bash
for skill in product-design-skill dev-forge-skill demo-forge-skill code-tuner-skill code-replicate-skill ui-forge-skill; do
  grep -l "phases:" claude/$skill/SKILL.md && echo "OK" || echo "MISSING: $skill"
done
```

Expected: 6 lines of OK.

- [ ] **Step 3: Push**

```bash
git push
```
