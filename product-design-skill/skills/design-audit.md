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
5. **模式一致性（Pattern Consistency）** — 相同功能模式是否使用了一致的设计套路？（仅当 pattern-catalog.json 存在时激活）
6. **行为一致性（Behavioral Consistency）** — 跨界面行为是否遵循已确认的行为规范？（仅当 behavioral-standards.json 存在时激活）
7. **交互类型一致性（Interaction Type Consistency）** — 相同交互类型的界面是否遵循统一的布局约束？（仅当 screen-map 含 interaction_type 时激活）

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
    ↓ 模式一致性（仅当 pattern-catalog.json 存在）
    pattern-catalog → ui-design-spec（_pattern_group 界面是否设计一致）
    ↓ 行为一致性（仅当 behavioral-standards.json 存在）
    behavioral-standards → ui-design-spec（界面是否遵循行为规范）
```

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/product-map.json`。

---

## 快速开始

```
/design-audit              # 三合一全量校验
/design-audit trace        # 仅逆向追溯
/design-audit coverage     # 仅覆盖洪泛
/design-audit cross        # 仅横向一致性
/design-audit pattern        # 仅模式一致性检查（需 pattern-catalog.json 存在）
/design-audit behavioral     # 仅行为一致性检查（需 behavioral-standards.json 存在）
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
| **Step 5 模式一致性** | AskUserQuestion 确认 | 自动执行（pattern-catalog.json 不存在 → 跳过），漂移问题记入日志 |
| **Step 5.5 创新保真审计** | AskUserQuestion 确认 | 自动执行（adversarial-concepts.json 不存在或无 core 概念 → 跳过），稀释/不完整问题记入日志 |
| **Step 5.6 行为一致性审计** | AskUserQuestion 确认 | 自动执行（behavioral-standards.json 不存在 → 跳过），漂移/违规问题记入日志 |
| **Step 5.7 交互类型一致性审计** | AskUserQuestion 确认 | 自动执行（前置条件不满足 → 提示用户重跑上游），布局漂移/类型不匹配问题记入日志 |
| **Step 6 报告确认** | AskUserQuestion 确认 | 自动确认 |

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
Step 5: 模式一致性（Pattern Consistency）
      仅当 pattern-catalog.json 存在时执行
      ↓ 自动
Step 5.5: 创新保真审计（Innovation Fidelity）
      仅当 adversarial-concepts.json 存在且含 core 概念时执行
      ↓ 自动
Step 5.6: 行为一致性审计（Behavioral Consistency）
      仅当 behavioral-standards.json 存在时执行
      ↓ 自动
Step 5.7: 交互类型一致性审计（Interaction Type Consistency）
      仅当 screen-map 含 interaction_type 字段时执行
      ↓ 自动
Step 6: 汇总报告
      合并所有维度结果，输出 JSON + Markdown
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

每个 gap 项列出：check_id、task_id、name、missing_in（缺失的下游层）。

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

> **搜索驱动原则**：展示审计结果前，先 WebSearch 搜索「design audit checklist {产品类型}」和「cross-layer consistency verification best practices」，用搜索结果补充审计维度。

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

### Step 5：模式一致性审计（Pattern Consistency）

> 目标：验证相同功能模式的界面/任务是否遵循了统一的设计套路。
> **前提**：`.allforai/design-pattern/pattern-catalog.json` 存在。不存在 → 跳过本步骤。

#### 检测项

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

#### 输出格式

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

---

### Step 5.5：创新保真审计（Innovation Fidelity）

> 目标：验证 product-concept 阶段定义的核心创新概念是否在全链路中存活且未被稀释。
> **前提**：`.allforai/product-concept/adversarial-concepts.json` 存在且含 `protection_level=core` 概念。不存在 → 跳过本步骤。

#### 检测项

**5.5a. 创新概念存活率**

对每个 `protection_level=core` 的创新概念：
- 在 `task-inventory.json` 中是否有 `innovation_task=true` 的对应任务？
- 在 `prune-decisions.json` 中是否被标为 CORE（未被 CUT/DEFER）？
- 在 `ui-design-spec.md/json` 中是否有专属设计节？
- 缺失任一层 → `INNOVATION_DILUTED`

**5.5b. 创新概念完整度**

对每个存活的核心创新概念：
- 其跨领域参考（adversarial_concept_ref）是否在 ui-design 中体现？
- 其保护级别是否在 feature-prune 决策中被尊重？
- 完整度不足 → `INNOVATION_INCOMPLETE`

#### 输出格式

```json
{
  "innovation_fidelity": {
    "status": "pass | issues_found | skipped",
    "core_concepts_total": 3,
    "survived": 3,
    "diluted": 0,
    "incomplete": 1,
    "issues": [
      {
        "type": "INNOVATION_DILUTED | INNOVATION_INCOMPLETE",
        "concept_id": "IC001",
        "concept_name": "...",
        "missing_in": ["ui-design"],
        "severity": "HIGH",
        "recommendation": "在 ui-design 中补充 IC001 专属设计节"
      }
    ]
  }
}
```

**严重度**：核心创新被稀释 → HIGH（产品差异化风险）。

---

### Step 5.6：行为一致性审计（Behavioral Consistency）

> 目标：验证所有界面是否遵循确认的行为规范。
> **前提**：`.allforai/behavioral-standards/behavioral-standards.json` 存在。不存在 → 跳过本步骤。

#### 检测项

**5.6a. 行为标准合规检查**

对 behavioral-standards.json 中每个 category：
- 读取该 category 标注的每个 screen 的 `_behavioral_standards` 方案
- 在 ui-design-spec.md/json 中检查该 screen 的设计是否匹配标准方案
- 不匹配 → `BEHAVIORAL_DRIFT`（行为漂移）

**5.6b. 破坏性操作确认合规**

对每个 screen 的 `crud=D` action 且 `requires_confirm=false`：
- 若 BC-DELETE-CONFIRM 标准为 `modal_confirm` →
  `BEHAVIORAL_VIOLATION`（界面违反已确认的行为规范）

#### 输出格式

```json
{
  "behavioral_consistency": {
    "status": "pass | issues_found | skipped",
    "total_categories_checked": 7,
    "compliant_screens": 18,
    "violating_screens": 2,
    "issues": [
      {
        "type": "BEHAVIORAL_DRIFT | BEHAVIORAL_VIOLATION",
        "category_id": "BC-DELETE-CONFIRM",
        "id": "S-05",
        "expected": "modal_confirm",
        "actual": "no_confirm",
        "severity": "MEDIUM",
        "recommendation": "添加模态确认弹窗"
      }
    ]
  }
}
```

**严重度分级**：
- `HIGH`：破坏性操作无确认（`BEHAVIORAL_VIOLATION`），用户数据安全风险
- `MEDIUM`：行为漂移（`BEHAVIORAL_DRIFT`），一致性体验受损
- `LOW`：细微偏差（加载方式略有不同），可接受

**输出处理**：
- 所有 issues 追加到 `audit-report.json` 的 `behavioral_consistency` 字段
- issues_found → 在 audit-report.md 中新增「行为一致性」章节展示违规列表
- 不阻塞流程，仅报告

---

### Step 5.7：交互类型一致性审计（Interaction Type Consistency）

> 目标：验证相同交互类型的界面是否遵循统一的布局约束和行为模式。

**前置检查**：
1. `.allforai/screen-map/screen-map.json` 是否存在
   - 不存在 → 提示「请先运行 /screen-map 生成界面地图」，终止
2. screen-map 中每个 screen 是否含 `interaction_type` 字段
   - 缺失 → 提示「screen-map 未标注 interaction_type，请运行 /screen-map refresh 重新生成」，终止

---

#### 检测项

**5.7a. 同类型界面布局一致性**

从 `${CLAUDE_PLUGIN_ROOT}/docs/interaction-types.md` 提取布局约束：

| 类型 | 布局约束 | 禁止项 |
|------|----------|--------|
| **MG1 只读列表** | 列表/表格/网格 | 表单、向导 |
| **MG2-L 列表** | 列表/表格 | 内嵌表单（新建应在独立页/弹窗） |
| **MG2-C 新建** | 表单页/弹窗 | — |
| **MG2-E 编辑** | 表单页/弹窗，必须回填旧值 | — |
| **MG3 状态机** | 状态标签（专用列）+ 操作下拉/Swipe | — |
| **MG5 主从详情** | 主实体区 + 子实体Tab | 无子实体的单层详情 |
| **MG6 树形管理** | 树形组件 + 编辑区联动 | — |
| **EC1 商品详情** | 图片轮播 + 规格选择 + 底部操作栏 | 无规格选择 |
| **EC2 购物车** | 列表 + 底部汇总区 | — |
| **WK1 对话/IM** | 消息流 + 底部输入框 | — |
| **WK5 看板** | 水平多列 + 卡片 | 单列列表 |

完整约束见 `interaction-types.md` 第 107-950 行各类型的「平台矩阵」。

**检测逻辑**：

```python
def check_layout_consistency(screens, layout_constraints):
    issues = []
    
    # 按 interaction_type 分组
    by_type = group_by(screens, 'interaction_type')
    
    for type_key, type_screens in by_type.items():
        constraints = layout_constraints.get(type_key, {})
        
        # 检查布局模式
        allowed_layouts = constraints.get('allowed_layouts', [])
        forbidden_layouts = constraints.get('forbidden_layouts', [])
        
        for screen in type_screens:
            layout = detect_layout_type(screen)  # 从 screen 结构推断
            
            # 检查禁止项
            if layout in forbidden_layouts:
                issues.append({
                    'type': 'LAYOUT_FORBIDDEN',
                    'id': screen['id'],
                    'screen_name': screen['name'],
                    'interaction_type': type_key,
                    'layout': layout,
                    'forbidden': forbidden_layouts,
                    'severity': 'HIGH',
                    'recommendation': f'{type_key} 不应使用 {layout} 布局'
                })
            
            # 检查允许项（可选，宽松模式）
            elif allowed_layouts and layout not in allowed_layouts:
                issues.append({
                    'type': 'LAYOUT_DRIFT',
                    'id': screen['id'],
                    'screen_name': screen['name'],
                    'interaction_type': type_key,
                    'layout': layout,
                    'allowed': allowed_layouts,
                    'severity': 'MEDIUM',
                    'recommendation': f'建议使用 {allowed_layouts} 之一'
                })
    
    return issues
```

---

**5.7b. 同类型界面布局偏差检测**

对同一 `interaction_type` 的多个 screen，检测布局偏差：

```python
def detect_layout_drift(type_screens):
    """检测同类界面的布局偏差"""
    layouts = [(s['id'], detect_layout_type(s)) for s in type_screens]
    
    # 所有布局是否一致
    unique_layouts = set(l[1] for l in layouts)
    
    if len(unique_layouts) > 1:
        return {
            'type': 'INCONSISTENT_LAYOUT',
            'screens': [l[0] for l in layouts],
            'layouts': list(unique_layouts),
            'severity': 'MEDIUM',
            'recommendation': '同类型界面应使用统一布局模式'
        }
    
    return None
```

示例：
- `MG2-L` 类型有 5 个 screen，其中 4 个用表格，1 个用卡片 → **LAYOUT_DRIFT**

---

**5.7c. 类型-上下文匹配度验证**

验证每个 screen 的 `interaction_type` 是否匹配「产品类型 × 用户属性 × 平台」的预设频率：

| 匹配度 | 检测 |
|--------|------|
| `excluded` 类型出现 | **TYPE_CONTEXT_MISMATCH**（该类型不应出现在此上下文） |
| `low` 类型占比过高 | **LOW_TYPE_OVERREPRESENTED**（低频类型超过 30%） |

```python
def check_type_context_match(screens, product_type, audience, platform):
    preset = load_type_preset(product_type, audience, platform)
    
    issues = []
    type_counts = Counter(s.get('interaction_type', '') for s in screens)
    total = len(screens)
    
    # 检查 excluded 类型
    for itype in preset.get('excluded', []):
        if type_counts.get(itype, 0) > 0:
            issues.append({
                'type': 'TYPE_CONTEXT_MISMATCH',
                'interaction_type': itype,
                'count': type_counts[itype],
                'severity': 'HIGH',
                'recommendation': f'{itype} 在 {product_type}/{audience}/{platform} 上下文中不应出现'
            })
    
    # 检查低频类型占比
    low_types = preset.get('低频', [])
    low_count = sum(type_counts.get(t, 0) for t in low_types)
    low_ratio = low_count / total if total > 0 else 0
    
    if low_ratio > 0.3:
        issues.append({
            'type': 'LOW_TYPE_OVERREPRESENTED',
            'low_type_ratio': f'{low_ratio:.1%}',
            'threshold': '30%',
            'severity': 'MEDIUM',
            'recommendation': '低频类型占比过高，考虑精简'
        })
    
    return issues
```

---

#### 输出格式

```json
{
  "interaction_type_consistency": {
    "status": "pass | issues_found | skipped",
    "total_types_checked": 12,
    "consistent_types": 10,
    "drift_types": 2,
    "issues": [
      {
        "type": "LAYOUT_FORBIDDEN",
        "id": "S015",
        "screen_name": "商品管理",
        "interaction_type": "MG1",
        "layout": "form",
        "forbidden": ["form", "wizard"],
        "severity": "HIGH",
        "recommendation": "MG1 只读列表不应使用表单布局"
      },
      {
        "type": "INCONSISTENT_LAYOUT",
        "interaction_type": "MG2-L",
        "screens": ["S010", "S011", "S012", "S013", "S014"],
        "layouts": ["table", "card"],
        "severity": "MEDIUM",
        "recommendation": "MG2-L 类型界面应统一布局（建议 table）"
      },
      {
        "type": "TYPE_CONTEXT_MISMATCH",
        "interaction_type": "MG4",
        "count": 3,
        "severity": "HIGH",
        "recommendation": "MG4(审批) 在 C端消费者/Mobile App 上下文中不应出现"
      }
    ]
  }
}
```

---

#### 严重度分级

| 严重度 | 问题类型 | 影响 |
|--------|----------|------|
| `HIGH` | LAYOUT_FORBIDDEN / TYPE_CONTEXT_MISMATCH | 用户认知混乱或上下文不匹配 |
| `MEDIUM` | INCONSISTENT_LAYOUT / LAYOUT_DRIFT | 一致性体验受损 |
| `LOW` | LOW_TYPE_OVERREPRESENTED | 可优化但不阻塞 |

---

#### 输出处理

- 所有 issues 追加到 `audit-report.json` 的 `interaction_type_consistency` 字段
- issues_found → 在 audit-report.md 中新增「交互类型一致性」章节展示问题列表
- 不阻塞流程，仅报告

---

### Step 6：汇总报告

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
    },
    "pattern_consistency": {
      "status": "pass|issues_found|skipped",
      "total_patterns_checked": 0,
      "clean_patterns": 0,
      "drift_patterns": 0
    },
    "innovation_fidelity": {
      "status": "pass|issues_found|skipped",
      "core_concepts_total": 0,
      "survived": 0,
      "diluted": 0,
      "incomplete": 0
    },
    "behavioral_consistency": {
      "status": "pass|issues_found|skipped",
      "total_categories_checked": 0,
      "compliant_screens": 0,
      "violating_screens": 0
    },
    "interaction_type_consistency": {
      "status": "pass|issues_found|skipped",
      "total_types_checked": 0,
      "consistent_types": 0,
      "drift_types": 0
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
      "name": "任务名",
      "missing_in": "use-case",
      "detail": "任务 T015 没有对应的用例"
    }
  ],
  "cross_issues": [
    {
      "check_id": "X1",
      "type": "CONFLICT",
      "task_id": "T008",
      "name": "任务名",
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
- 模式一致性：X 类模式检查，X 漂移（pass/issues_found/skipped）
- 创新保真：X 核心概念，X 存活，X 稀释，X 不完整（pass/issues_found/skipped）
- 行为一致性：X 类别检查，X 合规界面，X 违规界面（pass/issues_found/skipped）
- 交互类型一致性：X 种类型检查，X 漂移（pass/issues_found/skipped）

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

### LAYOUT_DRIFT（布局漂移）
| # | 类型 | 界面 | 布局偏差 | 建议 |
|---|------|------|----------|------|
| ... | ... | ... | ... | ... |

### TYPE_CONTEXT_MISMATCH（类型上下文不匹配）
| # | 类型 | 出现次数 | 上下文 | 建议 |
|---|------|----------|--------|------|
| ... | ... | ... | ... | ... |
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

### 5. category 一致性校验

校验 `task-inventory.json` 中所有任务是否标注了 `category`（basic/core）。缺失 category 的任务记为 WARNING。`category=basic` 的任务被 feature-prune 标 CUT 记为 CONFLICT（基本功能不应被剪除）。

### 6. 幂等

多次运行结果一致。不产生副作用，不缓存决策，不依赖上次运行结果。每次运行都是全新的独立校验。
