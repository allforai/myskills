# Product Design Pattern Abstraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add functional abstraction detection to product-design at three injection points (事前/事中/事后), identifying shared UI templates, shared functional flows, and same-pattern features across the product map.

**Architecture:** A new `design-pattern` skill inserted between screen-map (Phase 3) and the parallel group (Phase 4-7) scans task-inventory + screen-map for 8 recurring pattern types, tags matching tasks/screens, and generates a `pattern-catalog.json` that downstream skills can reference. Mid-execution, ui-design checks pattern consistency. Post-execution, design-audit gains a 5th dimension verifying pattern compliance.

**Tech Stack:** Markdown skill files, JSON artifacts, `.allforai/design-pattern/` directory, AskUserQuestion for ONE-SHOT confirmation.

---

## Overview: Files to Modify

| Task | File | Action |
|------|------|--------|
| 1 | `product-design-skill/skills/design-pattern.md` | **CREATE** new Phase 3.5 skill |
| 2 | `product-design-skill/commands/product-design.md` | **MODIFY** — insert Phase 3.5 between Phase 3 and Phase 4-7 |
| 3 | `product-design-skill/skills/ui-design.md` | **MODIFY** — add mid-execution pattern consistency check |
| 4 | `product-design-skill/skills/design-audit.md` | **MODIFY** — add 5th audit dimension "模式一致性" |

---

### Task 1: Create `skills/design-pattern.md`

**Files:**
- Create: `product-design-skill/skills/design-pattern.md`

**Step 1: Write the file**

```markdown
---
name: design-pattern
description: >
  Use when "分析设计模式", "共享界面分析", "功能抽象", "模式识别", or automatically called by product-design Phase 3.5.
  Scans task-inventory and screen-map to identify recurring functional patterns (CRUD台、列表+详情、审批流、
  搜索分页、导出、通知触发、权限矩阵、状态机), presents ONE-SHOT confirmation, then tags tasks and screens
  with pattern references and writes pattern-catalog.json.
version: "1.0.0"
---

# Design Pattern — 产品功能模式抽象

> 扫描 task-inventory + screen-map → 识别重复设计模式 → 用户确认 → 标注 tasks/screens → 输出 pattern-catalog.json

## 目标

在并行设计开始前识别产品中的重复功能模式，通过统一模板避免"同模式多套路"：

1. **扫描** — 读取 task-inventory.json + screen-map.json，检测 8 类功能模式
2. **用户确认** — ONE-SHOT 展示分析结果（唯一停顿点）
3. **标注** — 为匹配任务和界面注入 `_Pattern_` 标签
4. **写入** — 生成 pattern-catalog.json

---

## 定位

```
Phase 3: screen-map → screen-map.json          ← 输入
Phase 3.5: design-pattern → pattern-catalog.json ← 本技能
Phase 4-7: 并行组（ui-design 消费 pattern-catalog） ← 下游
Phase 8: design-audit → Pattern Consistency 维度 ← 事后
```

**前提**：
- 必须有 `.allforai/product-map/task-inventory.json`（来自 product-map）
- 必须有 `.allforai/screen-map/screen-map.json`（来自 screen-map）

---

## 工作流

```
Preflight: 检查前置文件存在性
    ↓ 自动
Step 1: 模式扫描（扫描 task-inventory + screen-map，检测 8 类模式）
    ↓ 自动
Step 2: ONE-SHOT 用户确认（唯一停顿点）
    ↓ 用户确认后
Step 3: 注入标签 + 写入产物（自动，不停顿）
```

---

## Preflight: 前置检查

检查必需文件：
- `.allforai/product-map/task-inventory.json` — 不存在 → 输出「请先完成 Phase 2（product-map）」，终止
- `.allforai/screen-map/screen-map.json` — 不存在 → 输出「请先完成 Phase 3（screen-map）」，终止

---

## Step 1: 模式扫描

> 目标：检测 task-inventory + screen-map 中的 8 类功能模式。

**扫描维度**：task 标题、task type、task actions（screen-map 中的 actions 字段）、business-flows 节点序列、roles（涉及多角色的实体）。

### 8 类模式定义

| 模式 ID | 模式名 | 检测规则 | 阈值 |
|---------|--------|---------|------|
| `PT-CRUD` | CRUD 管理台 | 同实体 tasks 涵盖 create + list/query + edit/update + delete 四类动作 | 每组 ≥3 动作 |
| `PT-LIST-DETAIL` | 列表+详情对 | screen-map 中同模块存在 list 类型界面 + detail 类型界面 | 2+ 对 |
| `PT-APPROVAL` | 审批流 | business-flows 中出现 submit→review→approve/reject 节点序列 | 1+ 条流 |
| `PT-SEARCH` | 搜索+筛选+分页 | screen-map actions 同时含 search/filter/query + paginate/page | 2+ 界面 |
| `PT-EXPORT` | 导出/报表 | task 标题或 actions 含 export/report/download/导出/报表/下载 | 2+ 任务 |
| `PT-NOTIFY` | 通知触发 | business-flows 节点后紧跟 notify/send/push/通知/发送 节点 | 2+ 流节点 |
| `PT-PERMISSION` | 权限矩阵 | 同实体被 3+ 角色访问且每角色权限不同（CRUD 动作子集不同） | 1+ 实体 |
| `PT-STATE` | 状态机 | task 涉及 status/state 字段 + 明确状态转换动作（approve/reject/cancel/archive/activate） | 2+ 任务 |

对每类模式，记录：
- 匹配的 task_id 列表
- 匹配的 screen_id 列表（若适用）
- 实例数量
- 推荐设计模板（见下方参考表）

### 推荐设计模板参考

| 模式 | 推荐界面模板 | 推荐交互模板 |
|------|-----------|-----------|
| PT-CRUD | 顶部操作栏 + 数据表格 + 弹窗/侧边栏表单 | 行内编辑 or 详情页编辑 |
| PT-LIST-DETAIL | 主列表 + 右侧详情面板 or 跳转详情页 | 面包屑导航 |
| PT-APPROVAL | 流程时间轴 + 审批意见区 | 顶部状态标签 + 操作按钮组 |
| PT-SEARCH | 顶部筛选栏（折叠/展开）+ 分页器 | URL 参数持久化 |
| PT-EXPORT | 导出按钮（右上角）+ 导出配置弹窗 | 异步下载提示 |
| PT-NOTIFY | 系统级通知中心 or 消息列表 | 红点/角标 |
| PT-PERMISSION | 权限开关矩阵（角色×操作） | 灰化不可用项 |
| PT-STATE | 状态标签（颜色编码）+ 操作按钮根据状态动态显示 | 状态流转确认弹窗 |

---

## Step 2: ONE-SHOT 用户确认（唯一停顿点）

展示完整扫描结果，一次性收集用户决策。

**展示格式**：

```markdown
## Phase 3.5 — 设计模式分析

### 检测到的功能模式（{N} 类）

| 模式 | 实例数 | 涉及 Tasks | 涉及 Screens | 推荐模板 |
|------|--------|-----------|------------|--------|
| CRUD 管理台 | 3 个实体（订单、用户、商品） | T-12,T-13,T-14... | S-05,S-06,S-07... | 顶部操作栏+数据表格 |
| 列表+详情对 | 4 对 | T-08,T-09... | S-03,S-04... | 主列表+侧边详情 |
| 审批流 | 2 条流 | T-21,T-22... | — | 流程时间轴 |
| 搜索+筛选+分页 | 5 个界面 | — | S-01,S-03,S-05... | 顶部筛选栏 |

### 未检测到模式（跳过）
- PT-EXPORT（无导出相关任务）
- PT-NOTIFY（无通知触发流程）
```

用 **AskUserQuestion** 对模板选择有分歧的模式提问（一次性收集所有决策）：

```
对 CRUD 管理台，推荐「弹窗表单」还是「侧边栏表单」？
对 列表+详情，推荐「右侧面板」（不离开列表页）还是「跳转详情页」？
```

无分歧的模式（只有一种合理模板）→ 直接采用，无需确认。

---

## Step 3: 注入标签 + 写入产物（自动，不停顿）

用户确认后，自动执行以下操作，不再停顿。

### 3a. 更新 task-inventory.json

为每个匹配任务追加 `_pattern` 字段：

```json
{
  "task_id": "T-12",
  "title": "订单列表查询",
  "_pattern": ["PT-CRUD", "PT-SEARCH"],
  "_pattern_template": "顶部操作栏+数据表格+顶部筛选栏"
}
```

（原地更新，只追加字段，不修改已有字段）

### 3b. 更新 screen-map.json

为每个匹配界面追加 `_pattern` 字段：

```json
{
  "screen_id": "S-05",
  "name": "订单管理",
  "_pattern": ["PT-CRUD"],
  "_pattern_template": "顶部操作栏+数据表格",
  "_pattern_group": "orders-crud"
}
```

`_pattern_group` 用于将同模式的界面分组，便于 ui-design 阶段统一设计。

### 3c. 写入 `pattern-catalog.json`

```json
{
  "created_at": "ISO8601",
  "total_patterns_detected": 4,
  "patterns": [
    {
      "pattern_id": "PT-CRUD",
      "name": "CRUD 管理台",
      "instances": [
        {
          "group_id": "orders-crud",
          "entity": "订单",
          "task_ids": ["T-12", "T-13", "T-14"],
          "screen_ids": ["S-05", "S-06"],
          "template": "顶部操作栏+数据表格+弹窗表单",
          "user_decision": "modal-form"
        }
      ],
      "total_instances": 3
    },
    {
      "pattern_id": "PT-LIST-DETAIL",
      "name": "列表+详情对",
      "instances": [
        {
          "group_id": "orders-list-detail",
          "entity": "订单",
          "task_ids": ["T-08", "T-09"],
          "screen_ids": ["S-03", "S-04"],
          "template": "主列表+右侧详情面板",
          "user_decision": "side-panel"
        }
      ],
      "total_instances": 4
    }
  ],
  "tasks_tagged": 18,
  "screens_tagged": 12
}
```

**输出**：`Phase 3.5 ✓ {N} 类模式（{M} 个实例），标注 {P} 个 tasks、{Q} 个 screens`，自动继续。

---

## 输出文件

```
.allforai/design-pattern/
└── pattern-catalog.json          # 主产物，Phase 3.5 完成标志
.allforai/product-map/
└── task-inventory.json           # 原地追加 _pattern 字段
.allforai/screen-map/
└── screen-map.json               # 原地追加 _pattern 字段
```

---

## 3 条铁律

### 1. 用户只停顿一次

Step 2 是唯一的用户交互点。Step 1 全自动执行，Step 3 用户确认后全自动完成，不再询问。

### 2. 只追加，不覆盖

Step 3 更新 task-inventory.json 和 screen-map.json 时，只追加 `_pattern` 相关字段，不修改任何已有字段。

### 3. 无模式时优雅跳过

若扫描后所有 8 类模式均未达到阈值，直接输出「Phase 3.5 ✓ 未检测到重复功能模式，跳过」，不生成 pattern-catalog.json（下游技能将判断文件是否存在）。
```

**Step 2: Verify file content looks correct**

Read the created file and confirm:
- YAML frontmatter is valid
- 8 pattern types are listed with detection rules
- 3-step workflow matches the template
- JSON schemas are complete

**Step 3: No tests needed, no commit yet**

This task creates a documentation/skill file. Skip automated testing. Commit together with other tasks at the end.

---

### Task 2: Modify `commands/product-design.md` — Insert Phase 3.5

**Files:**
- Modify: `product-design-skill/commands/product-design.md`

**Step 1: Read the full file first**

```bash
# Read the file to understand current state
```

Use the Read tool on `product-design-skill/commands/product-design.md`.

**Step 2: Add Phase 3.5 to the Phase 0 artifact detection table**

Find the table in the "Phase 0：产物探测" section and add a new row:

```
| design-pattern | `.allforai/design-pattern/pattern-catalog.json` 存在 |
```

Insert after the `screen-map` row and before the `use-case` row.

**Step 3: Insert Phase 3.5 into the orchestration flow diagram**

Find the `## 编排流程` code block. Change:

```
Phase 3: screen-map
  加载并执行 skills/screen-map.md
  ↓ checkpoint + 轻量校验
Phase 4-7: 并行执行（4 个 Agent 同时启动）
```

To:

```
Phase 3: screen-map
  加载并执行 skills/screen-map.md
  ↓ checkpoint + 轻量校验
Phase 3.5: design-pattern（可选，有模式时执行）
  加载并执行 skills/design-pattern.md
  ↓ checkpoint
Phase 4-7: 并行执行（4 个 Agent 同时启动）
```

**Step 4: Add Phase 3.5 execution section**

After the "Phase 3" execution section and before the "Phase 4-7" section, insert:

```markdown
---

## Phase 3.5：设计模式分析（可选）

### 执行方式
用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/design-pattern.md`，按其工作流执行。

执行条件：
- 自动模式下，screen-map 完成后立即执行
- 若所有 8 类模式均未达阈值，技能自动输出跳过提示，无需用户操作

### 质量门禁（pattern-catalog.json 存在时）

| 条件 | 标准 |
|------|------|
| pattern-catalog.json | 存在（或明确跳过）|
| tasks_tagged | 所有 _pattern 匹配任务已标注 |
| screens_tagged | 所有 _pattern 匹配界面已标注 |

PASS → 进入 Phase 4-7 并行组

### resume 模式
- `pattern-catalog.json` 存在 → 跳过 Phase 3.5
- 文件不存在且 screen-map 已完成 → 补跑 Phase 3.5
```

**Step 5: Update Phase 0 detection table note**

Find the resume mode note for the parallel group. After mentioning screen-map completion prerequisite for Phase 4-7, add:

```
> **design-pattern**: 可选阶段，`pattern-catalog.json` 存在或 Phase 3.5 明确跳过，视为已完成。
```

**Step 6: Verify changes**

Read the modified section back and confirm:
- Phase 3.5 appears between Phase 3 and Phase 4-7 in the flow diagram
- Phase 3.5 section exists with quality gate table
- Phase 0 detection table has `design-pattern` row

---

### Task 3: Modify `skills/ui-design.md` — Add Pattern Consistency Check

**Files:**
- Modify: `product-design-skill/skills/ui-design.md`

**Step 1: Read the full file first**

Use Read tool on `product-design-skill/skills/ui-design.md`.

**Step 2: Understand where the mid-execution check should go**

Find the step in ui-design where screens are being designed/generated. The check should be inserted after the initial screen design step and before the final spec writing, as a quality check on the generated designs.

**Step 3: Add pattern-catalog awareness to the Preflight or initialization section**

At the beginning of the ui-design workflow (Preflight or Step 0), add a check:

```markdown
**Pattern Catalog（可选读取）**：
若 `.allforai/design-pattern/pattern-catalog.json` 存在，读取并作为设计约束使用：
- `_pattern_group` 相同的界面 → 必须使用相同的组件布局模板
- `_pattern_template` 字段 → 作为界面设计的首选方案参考
不存在 → 跳过，按标准流程设计
```

**Step 4: Add pattern consistency check step**

Find the step where individual screen specs are generated. After generating all screens (but before writing the final `ui-design-spec.md`), insert a pattern consistency check:

```markdown
**Pattern Consistency Check（仅当 pattern-catalog.json 存在时触发）**：

扫描本次已生成的所有界面设计：

检测 1: 同 `_pattern_group` 的界面是否使用了一致的主布局（顶部栏/侧边栏/主内容区比例相同）
  → 不一致 → 自动对齐到该 group 中最先生成的界面的布局
  → 记录调整: `pattern_alignment: [screen_id → aligned to screen_id]`

检测 2: 同一模式类型（如 PT-CRUD）的界面是否使用了相同的操作按钮位置（新建/编辑/删除）
  → 不一致 → 自动统一到推荐位置（右上角主操作 + 行内次操作）
  → 记录调整同上

检测 3: 同一审批流（PT-APPROVAL）的状态标签颜色体系是否统一（待审=黄/通过=绿/拒绝=红）
  → 不一致 → 标记为 WARNING，在 ui-design-spec.md 中备注「需统一颜色体系」

结果追加到 ui-design-spec.md 末尾的「模式一致性记录」章节：
```markdown
## 模式一致性记录

| Pattern Group | 对齐项目 | 调整说明 |
|--------------|---------|---------|
| orders-crud | 操作按钮位置 | 统一到右上角主操作 |
| approval-flows | 状态标签颜色 | ⚠ 需在组件库中统一 |
```

不阻塞，自动继续输出最终 ui-design-spec.md。
```

**Step 5: Verify changes**

Read the modified section and confirm:
- Pattern catalog loading is mentioned in Preflight/initialization
- Pattern consistency check step exists after screen generation
- Check includes 3 detection types
- Non-blocking behavior is explicit

---

### Task 4: Modify `skills/design-audit.md` — Add 5th Audit Dimension

**Files:**
- Modify: `product-design-skill/skills/design-audit.md`

**Step 1: Read the full file first**

Use Read tool on `product-design-skill/skills/design-audit.md` (full file).

**Step 2: Update the "目标" section to include the 5th dimension**

Find the current 4-dimension list in the `## 目标` section:

```markdown
1. **逆向追溯（Trace）** — 每个下游产物是否有上游源头？
2. **覆盖洪泛（Coverage）** — 每个上游节点是否被下游完整消费？
3. **横向一致性（Cross-check）** — 相邻层之间有无矛盾？
4. **信息保真（Fidelity）** — 关键对象是否可追溯且具备多视角覆盖？
```

Add after item 4:

```markdown
5. **模式一致性（Pattern Consistency）** — 相同功能模式是否使用了一致的设计套路？（仅当 pattern-catalog.json 存在时激活）
```

**Step 3: Update the 定位 diagram**

After the current three-axis structure in `## 定位`, add:

```
    ↓ 模式一致性（仅当 pattern-catalog.json 存在）
    pattern-catalog → ui-design-spec（_pattern_group 界面是否设计一致）
```

**Step 4: Add new Step 5 for Pattern Consistency**

Find the step structure in the file. After the existing Step 4 (Fidelity) and before the output/report section, insert:

```markdown
---

## Step 5: 模式一致性审计（Pattern Consistency）

> 目标：验证相同功能模式的界面/任务是否遵循了统一的设计套路。
> **前提**：`.allforai/design-pattern/pattern-catalog.json` 存在。不存在 → 跳过本步骤。

### 检测项

**5a. 界面模板一致性**

对 pattern-catalog.json 中每个 `_pattern_group`：
- 读取该 group 所有 screen_ids 在 ui-design-spec.md 中的设计描述
- 检测主布局模板是否一致（操作栏位置、列表样式、表单入口方式）
- 不一致 → `PATTERN_DRIFT`（模式漂移）

**5b. 跨实体 CRUD 一致性**

对所有 PT-CRUD 实例：
- 检查「新建」按钮位置是否一致（统一右上角或统一行内）
- 检查「删除」确认方式是否一致（统一弹窗确认或统一行内确认）
- 不一致 → `CRUD_INCONSISTENCY`

**5c. 审批流状态标签体系**

对所有 PT-APPROVAL 实例：
- 检查各流程的状态标签（待审/通过/拒绝）颜色语义是否统一
- 不一致 → `APPROVAL_COLOR_DRIFT`

**5d. 状态机操作按钮**

对所有 PT-STATE 实例：
- 检查状态转换操作按钮（如「通过」「拒绝」「归档」）的呈现位置是否一致（顶部操作栏/详情底部/行内）
- 不一致 → `STATE_ACTION_DRIFT`

### 输出格式

```json
{
  "pattern_consistency": {
    "status": "pass | issues_found | skipped",
    "issues": [
      {
        "type": "PATTERN_DRIFT | CRUD_INCONSISTENCY | APPROVAL_COLOR_DRIFT | STATE_ACTION_DRIFT",
        "pattern_id": "PT-CRUD",
        "pattern_group": "orders-crud",
        "description": "orders 管理台用弹窗表单，但 users 管理台用侧边栏",
        "affected_screens": ["S-05", "S-06", "S-11"],
        "severity": "MEDIUM",
        "recommendation": "统一使用弹窗表单（已在 Phase 3.5 确认选型）"
      }
    ],
    "total_patterns_checked": 4,
    "clean_patterns": 3,
    "drift_patterns": 1
  }
}
```

**严重度分级**：
- `HIGH`：核心路径（CRUD/审批流）出现漂移，用户认知成本高
- `MEDIUM`：次要路径（导出/状态机）漂移，影响一致性感知
- `LOW`：细节（按钮标签文本）差异，可接受

**输出处理**：
- 所有 issues 追加到 `audit-report.json` 的 `pattern_consistency` 字段
- issues_found → 在 audit-report.md 中新增「模式一致性」章节展示漂移列表
- 不阻塞流程，仅报告
```

**Step 5: Update audit-report schema**

Find where `audit-report.json` schema is defined in the file. Add `pattern_consistency` as a top-level field alongside the existing dimensions.

**Step 6: Update quick start commands**

Find the `## 快速开始` section. Add:

```markdown
/design-audit pattern   # 仅模式一致性检查（需 pattern-catalog.json 存在）
```

**Step 7: Verify changes**

Read modified sections and confirm:
- 5th dimension appears in 目标 list
- Step 5 section exists with 4 detection types
- JSON schema shows `pattern_consistency` field
- Quick start has `pattern` subcommand
- All detection types have severity levels

---

### Task 5: Commit

**Step 1: Stage all 4 files**

```bash
git add product-design-skill/skills/design-pattern.md
git add product-design-skill/commands/product-design.md
git add product-design-skill/skills/ui-design.md
git add product-design-skill/skills/design-audit.md
```

**Step 2: Commit**

```bash
git commit -m "feat: add design-pattern abstraction to product-design (三时机植入)

- New design-pattern.md skill: Phase 3.5, detects 8 recurring functional
  patterns (CRUD台/列表详情/审批流/搜索分页/导出/通知/权限矩阵/状态机)
- product-design.md: insert Phase 3.5 between screen-map and parallel group
- ui-design.md: mid-execution pattern consistency check across _pattern_group
- design-audit.md: 5th audit dimension for pattern consistency (PATTERN_DRIFT etc)

Mirrors the 3-point abstraction mechanism added to dev-forge."
```

**Step 3: Verify commit**

```bash
git log --oneline -3
git status
```

Expected: Clean working tree, new commit at top.

---

## Cross-Reference: Analogies with dev-forge

| dev-forge | product-design | Purpose |
|-----------|--------------|---------|
| `shared-utilities.md` (Phase 5) | `design-pattern.md` (Phase 3.5) | 事前扫描 + ONE-SHOT 确认 + 注入标签 |
| `_Leverage: SU-xxx_` in tasks.md | `_pattern`, `_pattern_group` in task-inventory/screen-map | 跨层引用标记 |
| abstraction_check in task-execute | pattern consistency in ui-design | 事中检测 |
| Phase 8 abstraction gate | design-audit Step 5 | 事后门禁 |
| `shared-utilities-plan.json` | `pattern-catalog.json` | 完成标志 artifact |

---

## Validation Checklist

After implementing:

1. `product-design-skill/skills/design-pattern.md` exists with valid YAML frontmatter
2. `product-design-skill/commands/product-design.md` Phase 0 table has `design-pattern` row
3. `product-design-skill/commands/product-design.md` flow diagram shows Phase 3.5 between Phase 3 and Phase 4-7
4. `product-design-skill/commands/product-design.md` has Phase 3.5 section with quality gate
5. `product-design-skill/skills/ui-design.md` references pattern-catalog.json in Preflight
6. `product-design-skill/skills/ui-design.md` has pattern consistency check step
7. `product-design-skill/skills/design-audit.md` 目标 list has 5th item
8. `product-design-skill/skills/design-audit.md` has Step 5 with 4 detection types
9. `product-design-skill/skills/design-audit.md` JSON schema includes `pattern_consistency`
10. All phase references are internally consistent (no stale "Phase 3.5" vs "Phase 4" confusion)
