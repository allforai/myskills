# Input Compiler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Context Pull sections to meta-skill node-specs so subagents pull only relevant upstream fields, eliminating noisy context.

**Architecture:** Pull model — each node-spec gets a `Context Pull` section generated at bootstrap time. bootstrap.md reads the `Downstream Consumers` table from capability files, filters by project relevance, and generates natural-language pull instructions (required/optional) into every node-spec. No orchestrator changes.

**Tech Stack:** Markdown skill files only. No code.

**Spec:** `docs/superpowers/specs/2026-04-07-input-compiler-design.md`

---

### Task 1: Update architecture contract in meta-skill architecture design doc

**Files:**
- Modify: `docs/superpowers/specs/2026-03-29-meta-skill-architecture-design.md`

- [ ] **Step 1: Read Section 5 of the architecture doc**

Read lines 169–215 of `docs/superpowers/specs/2026-03-29-meta-skill-architecture-design.md`.
Find the sentence: "每个 node-spec 是一个完整的 subagent 指令，包含执行所需的全部上下文。subagent 不需要读别的文件。"

- [ ] **Step 2: Update the contract statement**

Replace that sentence with:

```
每个 node-spec 包含三类内容：任务指令、Context Pull 规则、以及必需的静态上下文。
subagent 在执行前按 Context Pull 规则主动拉取上游产物，这是 node-spec 执行的一部分，不是例外。
```

- [ ] **Step 3: Verify the change reads correctly in context**

Read the surrounding paragraph to confirm the updated contract statement is coherent.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-03-29-meta-skill-architecture-design.md
git commit -m "docs(meta-skill): update node-spec contract to allow Context Pull"
```

---

### Task 2: Add `capability` field to workflow.json schema in bootstrap.md

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md`

Context: The workflow.json schema (Step 3.2) currently has nodes with: id, goal, exit_artifacts, knowledge_refs, consumers. We need to add `capability` so bootstrap can look up the Downstream Consumers table when generating Context Pull.

- [ ] **Step 1: Read the workflow.json node schema in bootstrap.md**

Read lines 626–665 of `claude/meta-skill/skills/bootstrap.md`.
Find the `"nodes"` array in the workflow.json JSON block.

- [ ] **Step 2: Add `capability` field to the node schema**

In the node object, add `"capability"` after `"id"`:

```json
{
  "id": "<project-specific name>",
  "capability": "<name of the capability this node is based on, e.g. discovery, product-analysis, translate>",
  "goal": "<one sentence: what this node achieves>",
  "exit_artifacts": ["<file paths that prove this node is done>"],
  "knowledge_refs": ["<which knowledge files this node should reference>"],
  "consumers": ["<node IDs that read this node's exit_artifacts>"]
}
```

- [ ] **Step 3: Add `capability` field description to the Node fields section**

After the `consumers` field description, add:

```
- `capability`: Which capability this node is based on. Matches a file in
  `knowledge/capabilities/<capability>.md`. Used at Context Pull generation time
  to look up which upstream artifacts this node may consume.
```

- [ ] **Step 4: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(meta-skill): add capability field to workflow.json node schema"
```

---

### Task 3: Add Downstream Consumers table to discovery.md

**Files:**
- Modify: `claude/meta-skill/knowledge/capabilities/discovery.md`

Context: discovery.md currently has a `Required Outputs` table (3 columns: Output, What, Why downstream needs it). We add a new `Downstream Consumers` table after it using the 5-column model from the spec.

- [ ] **Step 1: Read discovery.md**

Read `claude/meta-skill/knowledge/capabilities/discovery.md` fully.
Note where `Required Outputs` section ends and `Methodology Guidance` begins.

- [ ] **Step 2: Add Downstream Consumers table**

After the `Required Outputs` table, add:

```markdown
### Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `source-summary.json` | `tech_stacks` | translate, compile-verify, quality-checks | required | 翻译策略和编译验收都依赖技术栈 |
| `source-summary.json` | `modules` | product-analysis, generate-artifacts | required | 模块边界是产物分析和代码生成的基础 |
| `source-summary.json` | `architecture_pattern` | product-analysis | optional | 有助于识别设计模式，缺失时用代码读取兜底 |
| `source-summary.json` | `detected_patterns` | product-analysis, translate | optional | 辅助推断业务意图和翻译复杂度 |
| `file-catalog.json` | `modules[].key_files` | translate, generate-artifacts | required | 代码生成需要知道读哪些源文件 |
| `infrastructure-profile.json` | `databases`, `caches`, `auth` | demo-forge, test-verify | required | demo 数据填充和测试都需要知道基础设施 |
| `reuse-assessment.json` | `per_component` | translate | optional | 缺失时按全量翻译降级 |
```

- [ ] **Step 3: Verify the table is well-formed**

Read the section back to confirm markdown table renders correctly (column count consistent, no broken pipes).

- [ ] **Step 4: Commit**

```bash
git add claude/meta-skill/knowledge/capabilities/discovery.md
git commit -m "feat(meta-skill): add Downstream Consumers table to discovery capability"
```

---

### Task 4: Add Downstream Consumers table to product-analysis.md

**Files:**
- Modify: `claude/meta-skill/knowledge/capabilities/product-analysis.md`

- [ ] **Step 1: Read product-analysis.md**

Read `claude/meta-skill/knowledge/capabilities/product-analysis.md`.
Note where the `Required Outputs` section ends.

- [ ] **Step 2: Add Downstream Consumers table**

After the `Optional Outputs` table and before `Required Quality`, add:

```markdown
### Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `role-profiles.json` | `roles` | feature-gap, feature-prune, ui-design, generate-artifacts | required | 角色定义是所有下游功能和 UI 设计的基础 |
| `task-inventory.json` | `tasks` | feature-gap, feature-prune, generate-artifacts | required | 任务清单是功能差距分析和代码生成的输入 |
| `task-inventory.json` | `tasks[].id`, `tasks[].role_ref` | feature-gap, feature-prune | required | 外键引用，下游必须用这些 ID 保持一致性 |
| `business-flows.json` | `flows` | ui-design, generate-artifacts | required | 用户旅程定义 UI 结构和功能实现顺序 |
| `experience-map.json` | `screens` | ui-design, generate-artifacts, product-verify | required | 屏幕契约是 UI 设计和验收的基础 |
| `use-case-tree.json` | `cases` | test-verify, product-verify | required | 验收用例来自 Given/When/Then |
| `journey-emotion-map.json` | `stages` | ui-design | optional | 仅 consumer 产品有此产物；缺失时跳过情感设计维度 |
```

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/knowledge/capabilities/product-analysis.md
git commit -m "feat(meta-skill): add Downstream Consumers table to product-analysis capability"
```

---

### Task 5: Add Downstream Consumers table to feature-prune.md and reverse-concept.md

**Files:**
- Modify: `claude/meta-skill/knowledge/capabilities/feature-prune.md`
- Modify: `claude/meta-skill/knowledge/capabilities/reverse-concept.md`

- [ ] **Step 1: Read feature-prune.md**

Read `claude/meta-skill/knowledge/capabilities/feature-prune.md`.

- [ ] **Step 2: Add Downstream Consumers table to feature-prune.md**

After the Required Outputs section, add:

```markdown
### Downstream Consumers

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `prune-decisions.json` | `decisions[].included` | translate, generate-artifacts | required | 只实现 included=true 的功能，必须在翻译前裁剪 |
| `prune-tasks.json` | `tasks` | generate-artifacts | required | 生成代码任务列表以剪枝后的功能为准 |
| `prune-report.md` | — | product-verify | optional | 验收时参考裁剪决策，了解哪些功能被排除 |
```

- [ ] **Step 3: Read reverse-concept.md**

Read `claude/meta-skill/knowledge/capabilities/reverse-concept.md`.

- [ ] **Step 4: Add Downstream Consumers table to reverse-concept.md**

After the Required Outputs section, add:

```markdown
### Downstream Consumers

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `concept-baseline.json` | `jobs`, `mission` | product-analysis | required | product-analysis 用 baseline 做一致性检查，避免循环分析 |
| `concept-baseline.json` | `jobs[].success_criteria` | product-verify | optional | 验收时检查实现是否满足 JTBD 成功条件 |
```

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/knowledge/capabilities/feature-prune.md
git add claude/meta-skill/knowledge/capabilities/reverse-concept.md
git commit -m "feat(meta-skill): add Downstream Consumers tables to feature-prune and reverse-concept"
```

---

### Task 6: Add Context Pull generation logic to bootstrap.md Step 3.3

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md`

Context: Step 3.3 "Pre-Generate Node-Specs" currently defines the node-spec sections as: Task, Project Context, Theory Anchors, Knowledge References, Guidance, Exit Artifacts, Downstream Contract, Integration Points. We add `Context Pull` as a new section, placed between `Project Context` and `Theory Anchors`.

- [ ] **Step 1: Read the node-spec format block in bootstrap.md**

Read lines 721–777 of `claude/meta-skill/skills/bootstrap.md`.
Find the `## Project Context` section in the node-spec template.

- [ ] **Step 2: Add Context Pull section to the node-spec template**

After `## Project Context` and before `## Theory Anchors`, insert:

```markdown
## Context Pull

<Generated by bootstrap. Lists upstream artifacts this node must read before executing.>
<Bootstrap generates this by:>
<  1. Finding this node's upstream nodes (those with this node in their consumers[])>
<  2. Reading each upstream node's capability → knowledge/capabilities/<capability>.md>
<  3. Filtering the Downstream Consumers table: keep rows where Consumer Capability matches this node's capability>
<  4. Further filtering by project relevance (bootstrap-profile.json): skip rows that don't apply>
<  5. Splitting into required (missing = error) and optional (missing = warning + continue)>

Example output:

**必需（缺失则报错返回，不要继续执行）：**
- 从 `.allforai/bootstrap/source-summary.json` 读取 `tech_stacks` 字段，
  用于了解当前项目的技术栈，作为翻译策略选择的依据。
- 从 `.allforai/bootstrap/file-catalog.json` 读取 `modules[].key_files` 字段，
  用于确定需要翻译的源文件列表。

**可选（缺失则输出 warning 后继续，使用降级策略）：**
- 从 `.allforai/bootstrap/reuse-assessment.json` 读取 `per_component` 字段，
  用于了解每个组件的复用评估结果。缺失时按全量翻译策略继续。
```

- [ ] **Step 3: Add Context Pull generation instructions to Step 3.3**

After the "Why pre-generate?" paragraph and before "Maximum Realism Principle", add:

```markdown
**Context Pull Generation (for each node-spec):**

For each node, generate a `Context Pull` section using this algorithm:

1. Find upstream nodes: scan workflow.json nodes[] for any node whose `consumers[]`
   includes the current node's id.
2. For each upstream node, read its `capability` field. Load
   `knowledge/capabilities/<capability>.md`.
3. In the Downstream Consumers table, keep rows where `Consumer Capability` contains
   the CURRENT node's capability name.
4. Filter by project relevance: skip rows where the artifact is produced by a
   capability path that wasn't included in this project's workflow (e.g., skip
   `reuse-assessment.json` if no reuse-assessment node exists).
5. Split remaining rows into two groups:
   - `required`: missing file → subagent must return error, list the missing file
   - `optional`: missing file → subagent logs warning and continues with fallback
6. Write the Context Pull section as natural-language instructions (see template above).
   Use the `Reason` column to explain why each field matters for this node's work.

If a node has no upstream nodes (it's the first in the graph), omit Context Pull entirely.
```

- [ ] **Step 4: Verify the section placement is correct**

Read the surrounding bootstrap.md content to confirm Context Pull generation instructions are placed logically (after "Why pre-generate?" and before "Maximum Realism Principle"), and the node-spec template section now includes `## Context Pull` between `## Project Context` and `## Theory Anchors`.

- [ ] **Step 5: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(meta-skill): add Context Pull generation logic to bootstrap Step 3.3"
```

---

### Task 7: Verify with test prompt

**Files:**
- Read: `claude/meta-skill/tests/prompts/specialization.md`

- [ ] **Step 1: Read the existing test prompt**

Read `claude/meta-skill/tests/prompts/specialization.md` to understand the test format.

- [ ] **Step 2: Check generated node-spec structure**

Mentally trace through the bootstrap logic for a simple case:
- Project with `discovery` → `product-analysis` → `generate-artifacts` nodes
- `product-analysis` node's upstream = `discovery` (capability: discovery)
- Open `discovery.md` Downstream Consumers table, filter rows where Consumer Capability contains `product-analysis`
- Result should include: `source-summary.json / tech_stacks` (optional), `source-summary.json / modules` (required), `source-summary.json / architecture_pattern` (optional)
- Confirm these match the discovery.md table we wrote in Task 3

- [ ] **Step 3: Verify required/optional split logic**

Check: does the generated Context Pull correctly separate required from optional?
From the discovery.md table: `modules` → required, `architecture_pattern` → optional.
The product-analysis node-spec should have `modules` under "必需" and `architecture_pattern` under "可选".

- [ ] **Step 4: Verify error behavior is specified**

Confirm the Context Pull template includes: "缺失则报错返回，不要继续执行" for required items.
Confirm optional items include a fallback description ("缺失时..." clause).

- [ ] **Step 5: Commit if any fixes were needed**

```bash
git add -p
git commit -m "fix(meta-skill): correct Context Pull generation based on trace verification"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Covered by |
|-----------------|------------|
| 架构契约变更（更新 node-spec 定义） | Task 1 |
| workflow.json 增加 capability 字段 | Task 2 |
| capabilities/*.md 增加 Downstream Consumers 表 | Tasks 3-5 |
| 字段模型：Artifact/Field Path/Consumer Capability/Required/Reason | Tasks 3-5 |
| Node→Capability 绑定规则（文件名由 capability 固定） | Task 2 (workflow schema) + Tasks 3-5 (fixed artifact names) |
| bootstrap.md 加入 Context Pull 生成逻辑 | Task 6 |
| 失败策略两级：required 报错 / optional warning | Task 6 (template) |
| 验收标准：结构验证 + 行为验证 | Task 7 |

**Gaps:** Tasks 3-5 cover 4 of 19 capability files. The remaining 15 (translate, compile-verify, generate-artifacts, demo-forge, test-verify, product-verify, feature-gap, ui-design, ui-forge, visual-verify, quality-checks, tune, concept-acceptance, launch-prep, product-concept) follow the same pattern. They can be added incrementally — the framework is established and each is a straightforward table addition.

**Placeholder scan:** No TBD or TODO in task steps. All table content is concrete.

**Type consistency:** `capability` field name used consistently across Task 2 and Task 6.
