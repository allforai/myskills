# Product Design Phase 4-7 Parallel Optimization — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert product-design Phase 4-7 from serial to parallel execution using Agent tool barrier synchronization.

**Architecture:** Single-file change to the orchestrator command. Phase 3 completion triggers 4 parallel Agent tool calls (use-case, feature-gap, feature-prune, ui-design). Each agent writes pipeline-decisions to a shard file; orchestrator merges shards before Phase 8.

**Tech Stack:** Claude Code Agent tool (parallel invocation), Markdown command file

---

### Task 1: Update frontmatter — add Agent to allowed-tools

**Files:**
- Modify: `product-design-skill/commands/product-design.md:1-4`

**Step 1: Add Agent tool to allowed-tools**

Change line 4 from:
```
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "WebSearch"]
```
To:
```
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "WebSearch", "Agent"]
```

**Step 2: Commit**

```bash
git add product-design-skill/commands/product-design.md
git commit -m "feat: add Agent to product-design allowed-tools for parallel execution"
```

---

### Task 2: Update overview flow diagram

**Files:**
- Modify: `product-design-skill/commands/product-design.md:31-63`

**Step 1: Replace the serial flow diagram**

Replace the `## 编排流程` code block (lines 33-63) with the parallel version:

```
Phase 0: 产物探测
  扫描 .allforai/，标记哪些阶段已完成
  full 模式 → 从头开始
  resume 模式 → 从第一个未完成阶段开始
  ↓
Phase 1: concept（可选）
  加载并执行 skills/product-concept.md
  ↓ checkpoint
Phase 2: product-map
  加载并执行 skills/product-map.md
  ↓ checkpoint
Phase 3: screen-map
  加载并执行 skills/screen-map.md
  ↓ checkpoint + 轻量校验
Phase 4-7: 并行执行（4 个 Agent 同时启动）
  ┌─ Agent: use-case      → .allforai/use-case/
  ├─ Agent: feature-gap   → .allforai/feature-gap/
  ├─ Agent: feature-prune → .allforai/feature-prune/
  └─ Agent: ui-design     → .allforai/ui-design/
  全部完成 ↓ 聚合 checkpoint + pipeline-decisions 合并 + 轻量校验
Phase 8: design-audit full（终审）
  加载并执行 skills/design-audit.md full
  ↓ 输出最终审计报告 + 全流程摘要
```

**Step 2: Commit**

```bash
git add product-design-skill/commands/product-design.md
git commit -m "docs: update flow diagram to show Phase 4-7 parallel execution"
```

---

### Task 3: Replace Phase 4-7 sections with parallel execution block

**Files:**
- Modify: `product-design-skill/commands/product-design.md:226-287`

This is the core change. Replace the 4 separate Phase sections (Phase 4, 5, 6, 7) with a single parallel execution section.

**Step 1: Replace Phase 4-7 content**

Delete the current Phase 4 (lines 226-240), Phase 5 (lines 243-253), Phase 6 (lines 256-269), Phase 7 (lines 273-287) sections. Replace with:

```markdown
## Phase 4-7：并行执行

> Phase 4 (use-case)、Phase 5 (feature-gap)、Phase 6 (feature-prune)、Phase 7 (ui-design)
> 之间无数据依赖（均仅依赖 product-map + screen-map），使用 Agent tool 并行执行。

### 执行方式

Phase 3 checkpoint 通过后，用**单条消息发出 4 个 Agent tool 调用**并行执行。
Agent tool 的屏障同步机制保证 4 个 Agent 全部完成后才继续到聚合 checkpoint。

每个 Agent 的 prompt 模板：

~~~
你是产品设计流水线的并行执行器。

任务: 执行 {skill-name} 技能的完整工作流。

执行步骤:
1. 用 Read 工具加载 ${CLAUDE_PLUGIN_ROOT}/skills/{skill-name}.md
2. 按该技能的完整工作流执行（不跳步骤、不简化）
3. 产出写入 .allforai/{skill-name}/ 目录
4. pipeline-decisions 写入分片文件 .allforai/pipeline-decisions-{skill-name}.json（不写 pipeline-decisions.json 主文件）

上下文:
- 产品地图: .allforai/product-map/
- 界面地图: .allforai/screen-map/
- 产品概念: .allforai/product-concept/（可选）
{自动模式标记: __orchestrator_auto: true（若自动模式激活）}

重要:
- pipeline-decisions 必须写入分片文件 .allforai/pipeline-decisions-{skill-name}.json
- 不要读写其他并行 Agent 的产出目录
- 预置脚本优先: 检查 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_{script}.py 是否存在，存在则优先使用
~~~

4 个 Agent 调用的具体参数：

| Agent | skill-name | 预置脚本 | 产出目录 | 分片文件 |
|-------|-----------|---------|---------|---------|
| Agent 1 | use-case | `gen_use_cases.py` | `.allforai/use-case/` | `pipeline-decisions-use-case.json` |
| Agent 2 | feature-gap | `gen_feature_gap.py` | `.allforai/feature-gap/` | `pipeline-decisions-feature-gap.json` |
| Agent 3 | feature-prune | `gen_feature_prune.py` | `.allforai/feature-prune/` | `pipeline-decisions-feature-prune.json` |
| Agent 4 | ui-design | `gen_ui_design.py` | `.allforai/ui-design/` | `pipeline-decisions-ui-design.json` |

### 聚合 checkpoint

4 个 Agent 全部返回后，编排器执行聚合 checkpoint：

**Step 1: 产出检查**

| 产出 | 检查 | 来源 Phase |
|------|------|-----------|
| `.allforai/use-case/use-case-tree.json` | 存在 | Phase 4 |
| `.allforai/feature-gap/gap-tasks.json` | 存在 | Phase 5 |
| `.allforai/feature-prune/prune-decisions.json` | 存在 | Phase 6 |
| `.allforai/ui-design/ui-design-spec.md` | 存在 | Phase 7 |

**Step 2: pipeline-decisions 合并**

1. 读取 4 个分片文件（`pipeline-decisions-{skill}.json`）
2. 读取已有的 `pipeline-decisions.json`（若存在）
3. 按 `phase` 字段去重合并所有条目
4. 写入 `pipeline-decisions.json`
5. 删除 4 个分片文件

**Step 3: 轻量校验（跨 skill 交叉检查）**

- **use-case 覆盖**: 每个 task 至少有 1 条用例。无用例的 task → 列出
- **gap×prune 矛盾**: feature-gap 报缺口的 task 被 feature-prune 标 CUT → 标记矛盾
- **UI 覆盖**: 每个 CORE 任务（prune-decisions 中标为 CORE）在 UI 设计中有体现。遗漏 → 列出

发现问题 → 向用户报告，询问是否继续（design-audit 终审会再次完整检查）。

**自动模式聚合 checkpoint**:
- 产出不存在 → ERROR（停）
- gap×prune 矛盾 → WARNING（记日志继续）
- 高频功能被 CUT 且被业务流引用 → ERROR（停，安全护栏）
- use-case 部分 task 无用例 → WARNING（记日志继续）
- CORE 任务 UI 覆盖率 < 50% → WARNING（记日志继续）

### 错误处理

~~~
4 个 Agent 返回后:
  检查每个 Agent 的返回结果:
    全部成功 → 执行聚合 checkpoint → 进入 Phase 8
    部分失败 →
      成功的 Agent: 正常收集产出
      失败的 Agent: 记录错误信息
      向用户报告:
        "Phase 4-7 并行执行结果:
         ✓ use-case: 完成
         ✓ feature-gap: 完成
         ✗ feature-prune: 失败 — {错误原因}
         ✓ ui-design: 完成"
      询问用户:
        1. 重试失败的 skill（仅重跑失败的 Agent）
        2. 跳过继续到 Phase 8（design-audit 对 use-case/gap/prune 标注为可选依赖）
        3. 中止流程
    全部失败 →
      向用户报告所有错误
      询问: 全部重试 / 中止
~~~

### resume 模式下的并行处理

~~~
resume 模式检测 Phase 4-7 完成状态:
  4 个产出全部存在 → 跳过 Phase 4-7，进入 Phase 8
  部分存在 → 仅启动缺失产出对应的 Agent（已有产出不重跑）
  全部不存在 → 正常启动 4 个并行 Agent
~~~
```

**Step 2: Commit**

```bash
git add product-design-skill/commands/product-design.md
git commit -m "feat: replace serial Phase 4-7 with parallel Agent execution"
```

---

### Task 4: Update Phase 0 exploration table for parallel awareness

**Files:**
- Modify: `product-design-skill/commands/product-design.md:67-85`

**Step 1: Add parallel group note to the exploration table**

After the existing table (line 80), add a note explaining that Phase 4-7 are a parallel group:

```markdown
> **并行组**: use-case / feature-gap / feature-prune / ui-design 为并行执行组。
> resume 模式下，仅当该组全部完成才视为"Phase 4-7 已完成"，否则补跑缺失的 skill。
```

**Step 2: Commit**

```bash
git add product-design-skill/commands/product-design.md
git commit -m "docs: add parallel group note to Phase 0 exploration"
```

---

### Task 5: Update execution summary template

**Files:**
- Modify: `product-design-skill/commands/product-design.md:302-335`

**Step 1: Update the summary table to reflect parallel execution**

In the summary template, replace the 4 separate rows for Phase 4-7 with a grouped row:

Change:
```
| use-case | 完成 | use-case 数: X | 校验: X task 有用例 |
| feature-gap | 完成 | gap 数: X | — |
| feature-prune | 完成 | CORE/DEFER/CUT: X/X/X | 校验: 无矛盾/X 处矛盾 |
| ui-design | 完成 | — | 校验: CORE 覆盖 XX% |
```

To:
```
| **Phase 4-7 并行** | | | |
| ├ use-case | 完成/失败 | use-case 数: X | 校验: X task 有用例 |
| ├ feature-gap | 完成/失败 | gap 数: X | — |
| ├ feature-prune | 完成/失败 | CORE/DEFER/CUT: X/X/X | — |
| └ ui-design | 完成/失败 | — | 校验: CORE 覆盖 XX% |
| 聚合校验 | PASS/FAIL | gap×prune 矛盾: X | UI CORE 覆盖: XX% |
```

**Step 2: Commit**

```bash
git add product-design-skill/commands/product-design.md
git commit -m "docs: update execution summary for parallel Phase 4-7"
```

---

### Task 6: Update 铁律 section

**Files:**
- Modify: `product-design-skill/commands/product-design.md:339-346`

**Step 1: Add parallel execution rule**

After existing rule 5 (line 345), add:

```markdown
6. **并行 Agent 产出隔离** — Phase 4-7 的 4 个并行 Agent 各自写入独立目录和分片 pipeline-decisions 文件，不读写其他 Agent 的产出。聚合由编排器在全部完成后统一执行
```

**Step 2: Commit**

```bash
git add product-design-skill/commands/product-design.md
git commit -m "docs: add parallel isolation rule to 铁律"
```

---

### Task 7: Final review — read modified file and verify consistency

**Files:**
- Read: `product-design-skill/commands/product-design.md` (full file)

**Step 1: Read the complete file**

Verify:
- [ ] `allowed-tools` includes `Agent`
- [ ] Flow diagram shows Phase 4-7 as parallel
- [ ] Phase 4-7 section has Agent prompt template, aggregation checkpoint, error handling, resume handling
- [ ] No references to old serial Phase 4, 5, 6, 7 remain
- [ ] Phase 0 table has parallel group note
- [ ] Summary template reflects parallel grouping
- [ ] 铁律 has rule 6 about parallel isolation
- [ ] No accidental deletions of Phase 0-3 or Phase 8 content

**Step 2: Commit (if any fixups needed)**

```bash
git add product-design-skill/commands/product-design.md
git commit -m "fix: consistency fixes for parallel Phase 4-7"
```
