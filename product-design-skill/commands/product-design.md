---
description: "产品设计全流程编排：按阶段串联 concept → map → screen → use-case → gap → prune → ui-design → audit，每阶段间插入检查点。模式: full / resume"
argument-hint: "[mode: full|resume] [skip: concept]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "WebSearch", "Agent"]
---

# Product Design Full — 产品设计全流程编排

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 设计思想入口（建议先读）

执行全流程前，建议先阅读：

- `${CLAUDE_PLUGIN_ROOT}/docs/product-design-principles.md`

该文档汇总前段/中段/尾段的经典理论支持（如第一性原理、JTBD、Kano、Nielsen、ISO 9241-11、WCAG）及参考文献。

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 从头执行全流程（已有产物作为参考但会重新生成）
- **`full skip: concept`** → 从头执行，但跳过 Phase 1 概念发现
- **`resume`** → 检测已有产物，从第一个未完成阶段开始

## 编排流程

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

---

## Phase 0：产物探测

扫描以下目录，判断每个阶段的完成状态：

| 阶段 | 完成标志 |
|------|----------|
| concept | `.allforai/product-concept/` 目录存在 |
| product-map | `.allforai/product-map/task-inventory.json` 存在且 task 数 > 0 |
| screen-map | `.allforai/screen-map/screen-map.json` 存在且 screen 数 > 0 |
| use-case | `.allforai/use-case/use-case-tree.json` 存在 |
| feature-gap | `.allforai/feature-gap/gap-tasks.json` 存在 |
| feature-prune | `.allforai/feature-prune/prune-decisions.json` 存在 |
| ui-design | `.allforai/ui-design/ui-design-spec.md` 存在 |
| design-audit | `.allforai/design-audit/audit-report.json` 存在 |

**full 模式**：从 Phase 1（或 Phase 2 如果 skip concept）开始，逐阶段执行。
**resume 模式**：从第一个未完成阶段开始。

向用户展示探测结果，确认执行计划后开始。

---

## Phase 1：concept（可选）

**跳过条件**：用户指定 `skip: concept`，或 resume 模式下已完成。

**执行**：
1. 用 Read 工具加载 `${CLAUDE_PLUGIN_ROOT}/skills/product-concept.md`
2. 按 product-concept 技能的完整工作流执行

**检查点**：concept 产出目录存在。

---

## 自动模式检测

Phase 1（product-concept）执行完毕后，检测自动模式条件：

1. 读取 `.allforai/product-concept/product-concept.json`
2. 检查 `pipeline_preferences` 字段是否存在
3. **存在** → 启用自动模式：
   - 后续 Phase 2-8 每个技能调用时携带上下文标记 `__orchestrator_auto: true`
   - 检查点策略切换为三级评估（见下方）
   - 向用户展示：「检测到流水线偏好，启用全自动模式 — ERROR 级问题才停，WARNING 记日志继续」
4. **不存在** → 交互模式（当前行为不变）

### 检查点三级评估（自动模式）

自动模式下，Phase 2-8 的每个检查点行为变更：

| 级别 | 条件 | 行为 |
|------|------|------|
| **ERROR** | 必填字段缺失、引用断裂、task 数 = 0、必须文件不存在 | **停下来问用户**，展示错误详情，等待用户决策 |
| **WARNING** | 推荐字段缺失、覆盖率低于预期、轻微不一致 | 记入 `.allforai/pipeline-decisions.json`（`decision: "auto_continued"`），展示日志行后自动继续 |
| **PASS** | 检查全部通过 | 自动继续，展示一行摘要 |

### `pipeline-decisions.json`（自动模式决策日志）

自动模式下所有自动确认和自动跳过的决策记录在此文件，用户事后可审查：

```json
[
  {
    "phase": "Phase 2",
    "skill": "product-map",
    "step": "Step 1",
    "decision": "auto_confirmed",
    "severity": "PASS",
    "summary": "角色列表 3 个，无差异",
    "decided_at": "ISO timestamp"
  },
  {
    "phase": "Phase 3",
    "skill": "screen-map",
    "step": "Step 2",
    "decision": "auto_continued",
    "severity": "WARNING",
    "summary": "2 个 SILENT_FAILURE 检出，已记录",
    "details": ["S008 批量导出无 on_failure", "S012 删除操作无确认弹窗"],
    "decided_at": "ISO timestamp"
  }
]
```

---

## Phase 1-2 pipeline-decisions 写入

concept 和 product-map 完成后，追加记录到 `.allforai/pipeline-decisions.json`：

```json
{"phase": "Phase 1 — concept", "decision": "auto_confirmed", "detail": "concept generated", "decided_at": "..."}
{"phase": "Phase 2 — product-map", "decision": "auto_confirmed", "detail": "tasks=N, roles=M, flows=K", "decided_at": "..."}
```

按 `phase` 字段去重 — 重跑时替换已有条目，不产生重复。

---

## Phase 2：product-map

**执行**：
1. 用 Read 工具加载 `${CLAUDE_PLUGIN_ROOT}/skills/product-map.md`
2. 按 product-map 技能的完整工作流执行
3. 完成后追加 pipeline-decisions 记录（自动模式下）

**检查点**：
- `task-inventory.json` 存在
- task 数量 > 0
- `task-inventory-basic.json` 和 `task-inventory-core.json` 存在
- 每个 task 有 `category` 字段（basic 或 core）

检查点失败 → 向用户报告，询问是否继续（product-map 是后续所有阶段的基础，强烈建议修复）。

**自动模式检查点**：task 数 = 0 → ERROR（停）；category 字段缺失 → WARNING（记日志继续）；task 数 > 0 且分类完整 → PASS。

---

## Phase 3：screen-map

**执行**：
1. 用 Read 工具加载 `${CLAUDE_PLUGIN_ROOT}/skills/screen-map.md`
2. 按 screen-map 技能的完整工作流执行

**检查点**：
- `screen-map.json` 存在
- screen 数量 > 0

**轻量校验**：
- 每个 screen 的 `task_refs` 中的 task_id 在 `task-inventory.json` 中存在
- 发现问题 → 列出不一致项，询问用户是否继续

**自动模式检查点**：screen 数 = 0 → ERROR（停）；task_refs 引用断裂 → ERROR（停）；其余不一致 → WARNING 记日志继续。

**角色拆分**：检查点通过后，运行预置脚本生成按角色拆分文件（供设计师按角色查阅）：

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_screen_map_split.py <BASE>
```

---

## Phase 4-8 预置脚本优先（自动模式）

自动模式下，Phase 4-8 优先使用预置脚本（位于 `${CLAUDE_PLUGIN_ROOT}/scripts/`）：

```
检查 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_xxx.py 是否存在：
  存在 → python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_xxx.py <BASE> --mode auto
  不存在 → 回退到 LLM 临场生成脚本（向后兼容）
```

预置脚本的优势：
- **零语法错误**：不存在 `gaps[:30)` 等括号混用
- **字段名统一**：screen-map 用 `tasks`，flow 用 `nodes`（不再误读 `task_refs` / `steps`）
- **pipeline-decisions 去重**：按 phase 名替换，重跑不产生重复条目

---

## Phase 4：use-case

**执行**：
1. 检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_use_cases.py` 是否存在
2. 存在 → 执行预置脚本；不存在 → 加载 `${CLAUDE_PLUGIN_ROOT}/skills/use-case.md` 按工作流执行

**检查点**：
- `use-case-tree.json` 存在

**轻量校验**：
- 每个 task 至少有 1 条用例
- 发现无用例的 task → 列出，询问用户是否继续

**自动模式检查点**：use-case-tree.json 不存在 → ERROR（停）；部分 task 无用例 → WARNING 记日志继续。

---

## Phase 5：feature-gap

**执行**：
1. 检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_feature_gap.py` 是否存在
2. 存在 → 执行预置脚本；不存在 → 加载 `${CLAUDE_PLUGIN_ROOT}/skills/feature-gap.md` 按工作流执行

**检查点**：
- `gap-tasks.json` 存在

**自动模式检查点**：gap-tasks.json 不存在 → ERROR（停）；缺口任务自动生成 → PASS 继续。

---

## Phase 6：feature-prune

**执行**：
1. 检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_feature_prune.py` 是否存在
2. 存在 → 执行预置脚本；不存在 → 加载 `${CLAUDE_PLUGIN_ROOT}/skills/feature-prune.md` 按工作流执行

**检查点**：
- `prune-decisions.json` 存在

**轻量校验**：
- feature-gap 报缺口的 task 被 feature-prune 标 CUT → 标记矛盾
- 发现矛盾 → 列出，询问用户是否修正（在 design-audit 终审中会再次完整检查）

**自动模式检查点**：prune-decisions.json 不存在 → ERROR（停）；高频功能被 CUT 且被业务流引用 → ERROR（停，安全护栏）；gap-prune 矛盾 → WARNING 记日志继续。

---

## Phase 7：ui-design

**执行**：
1. 检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_ui_design.py` 是否存在
2. 存在 → 执行预置脚本；不存在 → 加载 `${CLAUDE_PLUGIN_ROOT}/skills/ui-design.md` 按工作流执行

**检查点**：
- `ui-design-spec.md` 存在

**轻量校验**：
- 每个 CORE 任务（prune-decisions 中标为 CORE）在 UI 设计中有体现
- 发现遗漏 → 列出，询问用户是否继续

**自动模式检查点**：ui-design-spec.md 不存在 → ERROR（停）；CORE 任务 UI 覆盖率 < 50% → WARNING 记日志继续。

---

## Phase 8：design-audit full（终审）

**执行**：
1. 检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_design_audit.py` 是否存在
2. 存在 → 执行预置脚本；不存在 → 加载 `${CLAUDE_PLUGIN_ROOT}/skills/design-audit.md` 按 full 模式执行完整三合一校验

**自动模式检查点**：审计正常执行，所有结果写入报告。CONFLICT 级问题在摘要中高亮标注。自动模式下终审不停，但摘要中列出所有积累的 WARNING 条目总数。

**输出**：终审报告 + 全流程执行摘要

---

## 全流程执行摘要（强制输出）

所有阶段完成后，在对话中输出全流程摘要：

```
## 产品设计全流程执行摘要

> 执行模式: {full/resume}
> 执行时间: {开始时间} — {结束时间}

### 各阶段状态

| 阶段 | 状态 | 检查点 | 备注 |
|------|------|--------|------|
| concept | 完成/跳过 | — | {备注} |
| product-map | 完成 | task 数: X | — |
| screen-map | 完成 | screen 数: X | 校验: X 项通过 |
| use-case | 完成 | use-case 数: X | 校验: X task 有用例 |
| feature-gap | 完成 | gap 数: X | — |
| feature-prune | 完成 | CORE/DEFER/CUT: X/X/X | 校验: 无矛盾/X 处矛盾 |
| ui-design | 完成 | — | 校验: CORE 覆盖 XX% |
| design-audit | 完成 | 见终审报告 | — |

### 终审评分

- 逆向追溯：X ORPHAN
- 覆盖洪泛：覆盖率 XX%
- 横向一致性：X CONFLICT / X WARNING

### 产出文件

> 全部产出位于 `.allforai/` 目录下
> 终审报告: `.allforai/design-audit/audit-report.md`
```

---

## 铁律

1. **每阶段加载对应 skill** — 不跳步骤，不简化流程，完整执行每个技能的工作流
2. **检查点必须验证** — 每个阶段结束后验证产出存在性，失败时向用户报告
3. **用户可在任意阶段中止** — 检查点失败或用户主动中止时，保存已有产出，输出部分摘要
4. **轻量校验不替代终审** — 阶段间的轻量校验仅做快速检查，完整校验由 Phase 8 design-audit 负责
5. **只读不改上游** — 后序阶段发现上游问题时只报告，不自动回退修改上游产物
