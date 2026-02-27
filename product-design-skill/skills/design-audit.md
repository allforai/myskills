---
name: design-audit
description: >
  Use when the user asks to "verify design consistency", "audit design pipeline",
  "check design coverage", "trace design artifacts", "design-audit", "设计审计",
  "设计校验", "链路一致性", "覆盖率检查", "逆向追溯", "洪泛验证",
  or mentions cross-layer verification, design traceability, artifact consistency.
  Requires product-map to have been run first.
version: "1.0.0"
---

# Design Audit — 设计审计

> 跨层校验产品设计全链路一致性：逆向追溯、覆盖洪泛、横向一致性。

## 目标

以 `product-map` 为锚点，从三个维度校验设计产物链路：

1. **逆向追溯（Trace）** — 每个下游产物是否有上游源头？
2. **覆盖洪泛（Coverage）** — 每个上游节点是否被下游完整消费？
3. **横向一致性（Cross-check）** — 相邻层之间有无矛盾？
4. **信息保真（Fidelity）** — 关键对象是否可追溯且具备多视角覆盖？

发现问题只报告，不修改任何上游产物。

---

## 定位

```
product-map（锚点）
    ↓ 逆向追溯（从下往上）
    screen-map ← use-case ← feature-gap ← feature-prune ← ui-design
    ↓ 覆盖洪泛（从上往下）
    task → screen → use-case → gap → prune → ui-design
    ↓ 横向一致性（相邻层对比）
    gap × prune / ui-design × prune / frequency × depth / use-case × screen
```

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/product-map.json`。

---

## 快速开始

```
/design-audit              # 三合一全量校验
/design-audit trace        # 仅逆向追溯
/design-audit coverage     # 仅覆盖洪泛
/design-audit cross        # 仅横向一致性
/design-audit role 客服专员  # 指定角色全链路校验
```

## 增强协议（WebSearch + 4D+6V + XV）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：`"usability heuristic evaluation" + "case study" + 2025`、`"design audit checklist" + 产品类型 + "real project"`、`"WCAG 2.2 compliance" + "UI audit"`

**4D+6V 重点**：`fidelity_score` 作为量化指标；补充 Traceability 完整率（建议 `>= 95%`）和 Viewpoint 覆盖率（建议 `>= 90%`）两项门禁；CONFLICT/ORPHAN 问题附带 `source_refs` 与 `decision_rationale`。

**XV 交叉验证**（Step 3 横向一致性检测后）：

| 验证点 | task_type | 发送内容 | 写入字段 |
|--------|-----------|----------|----------|
| 跨层矛盾验证 | `cross_layer_validation`→gpt | 审计摘要：CONFLICT/ORPHAN/GAP 问题列表 + 典型矛盾案例 | cross_model_review.additional_contradictions |
| 覆盖盲区分析 | `coverage_analysis`→deepseek | 审计摘要：覆盖率统计 + 未覆盖任务列表 + 可用层信息 | cross_model_review.coverage_blindspots |

自动写入：遗漏的跨层矛盾（审计自身未检测到的层间不一致、隐性依赖断裂）、覆盖盲区（系统性遗漏模式、特定角色或模块的覆盖偏低区域）。

## 尾段理论支持（可选增强）

为让设计审计从“规则检查”升级为“体验质量治理”，可在现有三维校验上叠加：

| 理论/框架 | 对应步骤 | 落地方式 |
|-----------|----------|----------|
| Nielsen 可用性启发式 | Step 3 | 将 cross-check 结果映射为可用性问题类型（可见性、一致性、错误预防等） |
| ISO 9241-11（有效性/效率/满意度） | Step 2/4 | 将覆盖率与冲突结果翻译为可用性质量指标，便于发布评审 |
| WCAG 可访问性原则 | Step 3/4 | 对 UI 相关冲突补充可访问性风险标注（对比度、反馈可感知、可操作性） |
| 一致性与认知负荷原则 | Step 1/3 | 对 ORPHAN/BROKEN_REF/高频埋深给出认知成本解释，支撑优先级排序 |

> 说明：此增强不改变现有输出结构，仅增加审计结论的理论可解释性。

---

## 全自动模式

**激活条件**（同时满足）：
1. `.allforai/product-concept/product-concept.json` 存在且含 `pipeline_preferences` 字段
2. 上下文含 `__orchestrator_auto: true`（由 `/product-design full` 编排器传入）

**未同时满足** → 保持标准交互模式（当前行为不变）。

**行为变化**：

| 步骤 | 标准模式 | 全自动模式 |
|------|----------|-----------|
| **Step 1 逆向追溯确认** | AskUserQuestion 确认 | 自动确认，所有 ORPHAN 问题记入 `pipeline-decisions.json`（`decision: "auto_confirmed"`） |
| **Step 2 覆盖洪泛确认** | AskUserQuestion 确认 | 自动确认，所有 GAP 问题记入 `pipeline-decisions.json` |
| **Step 3 横向一致性确认** | AskUserQuestion 确认 | 自动确认，所有 CONFLICT / WARNING / BROKEN_REF 记入 `pipeline-decisions.json` |
| **Step 3.5 保真门禁** | AskUserQuestion 确认 | 低于阈值 → WARNING 记入日志（不停），达到阈值 → PASS 自动继续 |
| **Step 4 报告确认** | AskUserQuestion 确认 | 自动确认 |

**安全护栏**（自动模式下仍然停下来问用户）：
- ERROR 级验证失败（product-map.json 损坏、必须层缺失）

---

## 工作流

```
前置：两阶段加载 + 产物探测
      Phase 1 — 加载索引：task-index / screen-index / flow-index
      Phase 2 — 探测已有产物：
        .allforai/product-map/   → 必须存在
        .allforai/screen-map/    → 必须（不存在则自动运行 screen-map 生成）
        .allforai/use-case/      → 可选
        .allforai/feature-gap/   → 可选
        .allforai/feature-prune/ → 可选
        .allforai/ui-design/     → 可选
      标记 available_layers[]，仅校验已有层
      ↓
Step 1: 逆向追溯（Trace）
      从下游往上游反查，每个产物是否有源头
      ↓ 用户确认
Step 2: 覆盖洪泛（Coverage）
      从上游往下游洪泛，每个节点是否被完整消费
      ↓ 用户确认
Step 3: 横向一致性（Cross-check）
      相邻层之间的矛盾检测
      ↓ 用户确认
Step 3.5: 信息保真门禁（Fidelity）
      统计追溯完整率与视角覆盖率
      ↓ 用户确认
Step 4: 汇总报告
      合并三维度结果，输出 JSON + Markdown
```

---

### 前置：两阶段加载 + 产物探测

**Phase 1 — 加载索引**（始终安全，< 5KB）：

| 索引文件 | 路径 |
|----------|------|
| task-index | `.allforai/product-map/task-index.json` |
| screen-index | `.allforai/screen-map/screen-index.json` |
| flow-index | `.allforai/product-map/flow-index.json` |

任一索引存在 → 加载索引，按需决定是否加载完整数据。
所有索引不存在 → 回退全量加载 `product-map.json`。

**Phase 2 — 产物探测**：

检查以下目录/文件是否存在，构建 `available_layers[]`：

| 层 | 必须/可选 | 检测文件 |
|----|----------|----------|
| product-map | 必须 | `.allforai/product-map/product-map.json` |
| screen-map | 必须（不存在则自动运行 screen-map） | `.allforai/screen-map/screen-map.json` |
| use-case | 可选 | `.allforai/use-case/use-case-tree.json` |
| feature-gap | 可选 | `.allforai/feature-gap/gap-tasks.json` |
| feature-prune | 可选 | `.allforai/feature-prune/prune-decisions.json` |
| ui-design | 可选 | `.allforai/ui-design/ui-design-spec.md` |

- `product-map` 不存在 → 输出「请先运行 /product-map 建立产品地图」，**立即终止**
- 可选层不存在 → 跳过相关校验项，在报告中标注「层缺失，已跳过」

**`role` 模式额外处理**：从 `task-index.json` 按 `owner_role` 筛选匹配任务 ID 列表，后续所有校验仅涉及这些任务及其关联产物。

---

### Step 1：逆向追溯（Trace）

从下游产物往上游反查，验证每个产物项是否有合法的上游引用。

| # | 校验 | 条件 | 逻辑 |
|---|------|------|------|
| T1 | screen → task | screen-map 存在 | 每个 screen 的 `task_refs` 中的 task_id 必须在 task-inventory 中存在 |
| T2 | use-case → task | use-case 存在 | 每条 use-case 的 `task_id` 必须在 task-inventory 中存在 |
| T3 | use-case → screen | use-case + screen-map 存在 | 每条 use-case 的 `screen_ref` 必须在 screen-map 中存在 |
| T4 | gap-finding → task | feature-gap 存在 | 每个 gap 的 `task_id` 必须在 task-inventory 中存在 |
| T5 | prune-decision → task | feature-prune 存在 | 每个 prune 决策的 `task_id` 必须在 task-inventory 中存在 |

**执行逻辑**：

1. 仅执行条件满足（相关层在 `available_layers[]` 中）的校验项
2. 逐条检查引用关系，标记结果
3. 向用户展示结果摘要，等待确认

**结果标记**：

| 标记 | 含义 |
|------|------|
| `PASS` | 引用合法，上游源头存在 |
| `ORPHAN` | 无源头，下游产物引用了不存在的上游 ID |

每个 orphan 项列出：check_id、source 层、item_id、item_name、缺失的上游 ID。

---

### Step 2：覆盖洪泛（Coverage）

从上游 task-inventory 往下游洪泛，验证每个任务是否被下游层完整消费。

| # | 校验 | 条件 | 逻辑 |
|---|------|------|------|
| C1 | task → screen | screen-map 存在 | 每个 task 至少有一个 screen 引用它（通过 screen 的 `task_refs` 反查） |
| C2 | task → use-case | use-case 存在 | 每个 task 至少有一条正常流用例 |
| C3 | task → gap-checked | feature-gap 存在 | 每个 task 在 gap 报告中被检查过 |
| C4 | task → prune-decided | feature-prune 存在 | 每个 task 有 prune 决策（CORE/DEFER/CUT） |
| C5 | CORE task → ui-design | feature-prune + ui-design 存在 | 每个 CORE 任务在 UI 设计中有体现（检查 ui-design-spec.md 中是否提及该任务名或关联界面） |
| C6 | role → full journey | screen-map + use-case 存在 | 按角色追踪：tasks → screens → use-cases，检测断链（某任务有 screen 但无 use-case，或反过来） |

**执行逻辑**：

1. 仅执行条件满足的校验项
2. 遍历 task-inventory 中每个任务（`role` 模式下仅遍历指定角色的任务）
3. 逐条检查是否被下游消费
4. 统计覆盖率百分比：`covered / total × 100%`
5. 向用户展示结果摘要，等待确认

**结果标记**：

| 标记 | 含义 |
|------|------|
| `COVERED` | 任务被下游层完整消费 |
| `GAP` | 任务未被某下游层消费 |

每个 gap 项列出：check_id、task_id、task_name、missing_in（缺失的下游层）。

---

### Step 3：横向一致性（Cross-check）

相邻层之间的矛盾和不一致检测。

| # | 校验 | 条件 | 逻辑 |
|---|------|------|------|
| X1 | gap × prune 矛盾 | gap + prune 存在 | gap 报缺口的 task 被 prune 标 CUT → CONFLICT（gap 说缺，prune 说砍，矛盾） |
| X2 | ui-design × prune CUT | ui-design + prune 存在 | UI 包含 CUT 功能的界面 → CONFLICT（已砍的功能不应出现在 UI 设计中） |
| X3 | 频次 × 点击深度 | product-map + screen-map 存在 | 高频任务（frequency=高）在 screen-map 中 click_depth ≥ 3 → WARNING（高频操作被埋深） |
| X4 | use-case screen_ref | use-case + screen-map 存在 | 用例引用的 `screen_ref` 在 screen-map 中不存在 → BROKEN_REF |

**执行逻辑**：

1. 仅执行条件满足的校验项
2. 逐条检查相邻层之间的一致性
3. 向用户展示结果摘要，等待确认

**结果标记**：

| 标记 | 含义 | 严重度 |
|------|------|--------|
| `OK` | 无矛盾 | — |
| `CONFLICT` | 跨层矛盾，必须修复 | 最高 |
| `WARNING` | 设计合理性风险 | 中 |
| `BROKEN_REF` | 引用断裂 | 中 |

---

### Step 3.5：信息保真门禁（Fidelity）

在不改变现有主流程的前提下，补充两项统计门禁：

| # | 门禁 | 逻辑 | 建议阈值 |
|---|------|------|----------|
| F1 | Traceability 完整率 | 关键下游对象中，可追溯到上游证据/引用的比例 | ≥ 95% |
| F2 | Viewpoint 覆盖率 | 关键对象中，覆盖至少 4/6 视角（user/business/tech/ux/data/risk）的比例 | ≥ 90% |

**结果标记**：

| 标记 | 含义 |
|------|------|
| `PASS` | 达到阈值 |
| `BELOW_THRESHOLD` | 未达到阈值，建议回到上游补充上下文 |

---

### Step 4：汇总报告

合并三个维度的校验结果，生成最终报告。

**输出文件**：
- `.allforai/design-audit/audit-report.json` — 全量校验结果（机器可读）
- `.allforai/design-audit/audit-report.md` — 人类可读摘要

**JSON Schema**：

```json
{
  "generated_at": "ISO8601",
  "mode": "full|trace|coverage|cross|role",
  "role_filter": "角色名（仅 role 模式）",
  "available_layers": ["product-map", "screen-map", "..."],
  "summary": {
    "trace": { "total": 0, "pass": 0, "orphan": 0 },
    "coverage": { "total": 0, "covered": 0, "gap": 0, "rate": "0%" },
    "cross": { "total": 0, "ok": 0, "conflict": 0, "warning": 0, "broken_ref": 0 },
    "fidelity": {
      "traceability_rate": "0%",
      "traceability_status": "PASS|BELOW_THRESHOLD",
      "viewpoint_coverage_rate": "0%",
      "viewpoint_status": "PASS|BELOW_THRESHOLD"
    }
  },
  "trace_issues": [
    {
      "check_id": "T1",
      "type": "ORPHAN",
      "source": "screen-map",
      "item_id": "S003",
      "item_name": "界面名",
      "missing_ref": "T999",
      "detail": "screen S003 引用了不存在的 task T999"
    }
  ],
  "coverage_issues": [
    {
      "check_id": "C2",
      "type": "GAP",
      "task_id": "T015",
      "task_name": "任务名",
      "missing_in": "use-case",
      "detail": "任务 T015 没有对应的用例"
    }
  ],
  "cross_issues": [
    {
      "check_id": "X1",
      "type": "CONFLICT",
      "task_id": "T008",
      "task_name": "任务名",
      "detail": "feature-gap 报此任务有缺口，但 feature-prune 标为 CUT"
    }
  ]
}
```

**Markdown 报告结构**：

```markdown
# 设计审计报告

## 摘要

- 执行模式：{mode}
- 可用层：{available_layers}
- 逆向追溯：X 项检查，X PASS，X ORPHAN
- 覆盖洪泛：X 项检查，X COVERED，X GAP，覆盖率 XX%
- 横向一致性：X 项检查，X OK，X CONFLICT，X WARNING，X BROKEN_REF
- 信息保真：追溯完整率 XX%（PASS/BELOW_THRESHOLD） · 视角覆盖率 XX%（PASS/BELOW_THRESHOLD）

## 问题清单（按严重度排序）

### CONFLICT（跨层矛盾）
| # | 检查项 | 任务 | 说明 |
|---|--------|------|------|
| ... | ... | ... | ... |

### ORPHAN（无源头）
| # | 检查项 | 来源层 | 项目 | 说明 |
|---|--------|--------|------|------|
| ... | ... | ... | ... | ... |

### GAP（未覆盖）
| # | 检查项 | 任务 | 缺失层 | 说明 |
|---|--------|------|--------|------|
| ... | ... | ... | ... | ... |

### WARNING（风险）
| # | 检查项 | 任务 | 说明 |
|---|--------|------|------|
| ... | ... | ... | ... |

### BROKEN_REF（引用断裂）
| # | 检查项 | 来源 | 说明 |
|---|--------|------|------|
| ... | ... | ... | ... |
```

---

## 预置脚本（优先使用）

检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_design_audit.py` 是否存在：
- **存在** → `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_design_audit.py <BASE> --mode auto`
- **不存在** → 回退到 LLM 生成脚本（向后兼容）

预置脚本保证 schema 一致性和零语法错误。关键修复：
- 修复 `gaps[:30)` 语法错误（括号混用 → `gaps[:30]`）
- 使用 `_common.get_screen_tasks()` 统一读取界面任务引用
- pipeline-decisions 按 phase 去重，防止重跑产生重复条目

---

## 输出文件结构

```
.allforai/design-audit/
├── audit-report.json     # 全量校验结果（机器可读）
└── audit-report.md       # 人类可读摘要
```

---

## 防御性规范

> 通用模式定义见 `docs/defensive-patterns.md`，以下为本技能的具体应用。

### 加载校验
- **所有上游产物（6 层）**：加载每个层的 JSON 文件时用 `python -m json.tool` 验证合法性。单个文件解析失败 → 该层标记为「不可用（JSON 损坏）」，从 `available_layers[]` 中移除，跳过相关校验项。不因单个文件损坏中断整体审计。
- **`product-map.json`**（必须层）：解析失败 → 告知用户「product-map.json 损坏，请重新运行 /product-map」，**终止审计**。

### 零结果处理
- **全部检查通过 0 问题**：✓ 明确告知「设计审计通过 — 所有校验项均 PASS（逆向追溯 {N} 项 / 覆盖洪泛 {M} 项 / 横向一致性 {K} 项）」。
- **某维度 0 检查项**（因层缺失全部跳过）：标注「{维度名} 无可执行校验项（可用层不足），已跳过」，不报错。

### 规模自适应
- **阈值**：以任务数为计量对象。small ≤30 / medium 31–80 / large >80。
- **small**（≤30 任务）：完整详细报告 — 所有维度的每条检查结果逐一列出。
- **medium**（31–80 任务）：按严重度分层展示 — HIGH/CONFLICT 详细、MEDIUM/WARNING 摘要、LOW/INFO 仅统计。
- **large**（>80 任务）：统计总览 + 仅展开 HIGH/CONFLICT 级问题，其余按类型折叠为统计数字。

### WebSearch 故障
- **趋势搜索**（动态趋势补充）：工具不可用或无有用结果 → 跳过趋势补充，不影响审计主流程。

### 上游过期检测
- **逐层时间戳比较**：加载每个上游产物时读取 `generated_at`，与审计运行时间比较。若某层在其前序层更新之后未被刷新 → ⚠ 警告「{层名} 的 generated_at ({时间}) 早于其上游 {上游层名} 的 generated_at ({时间})，该层数据可能过期」。
- **报告中标注过期层**：在审计报告的摘要部分列出所有检测到的过期层，供用户决定是否先刷新再审计。
- 仅警告不阻断。

---

## 5 条铁律

### 1. 只读不改

审计只报告问题，不修改任何上游产物。发现 ORPHAN 或 CONFLICT 后，由用户决定回哪一层修复。

### 2. 已有产物决定校验范围

缺失的层自动跳过对应的校验项，不报错、不要求用户先运行缺失的技能。报告中标注「层缺失，已跳过」即可。

### 3. product-map 是锚点

所有追溯和洪泛以 product-map 的 task-inventory 为根。task-inventory 中的任务是唯一的真值来源。

### 4. 按严重度排序

问题清单始终按以下顺序排列：CONFLICT > ORPHAN > GAP > WARNING > BROKEN_REF。同级别内按 task_id 排序。

### 5. 幂等

多次运行结果一致。不产生副作用，不缓存决策，不依赖上次运行结果。每次运行都是全新的独立校验。
