---
name: feature-gap
description: >
  Use when the user asks to "find missing features", "check feature gaps",
  "what's incomplete", "verify user journeys", "check CRUD completeness",
  "feature-gap", "功能查漏", "查漏补缺", "找缺口", "功能是否完整", "旅程是否走通",
  "哪些功能没做完", "缺少什么功能", "用户路径有没有断点",
  or mentions gap detection, missing screens, broken user journeys,
  incomplete CRUD, or features that exist in product-map but not in reality.
  Requires product-map to have been run first.
version: "2.2.0"
---

# Feature Gap — 功能查漏

> 产品地图说应该有的，现在有没有？用户路径走得通吗？

## 目标

以 `product-map` 为基准，回答两个问题：

1. **有没有？** — 产品地图中每个任务、界面、按钮，是否真实存在？
2. **走得通吗？** — 每个角色从进入到完成任务，路径是否完整不断？

发现缺口，生成任务清单。不建议添加任何不在产品地图中的功能。

---

## 定位

```
product-map（现状+方向）   功能查漏（查缺口）          功能剪枝（查多余）
产品应该长什么样           地图说有的，现在有没有        地图里有的，该不该留
基础层                    基于 product-map           基于 product-map
```

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/product-map.json`。

---

## 快速开始

```
/feature-gap           # 完整查漏（任务+界面+旅程）
/feature-gap quick     # 只查任务和 CRUD，跳过旅程验证
/feature-gap journey   # 只验证用户旅程路径
/feature-gap role 客服专员  # 只查指定角色的功能缺口
/feature-gap refresh    # 清除决策缓存，完整重跑
```

## 动态趋势补充（WebSearch）

除经典理论外，建议在本技能执行时补充近 12–24 个月的缺口治理与旅程修复案例：

- 搜索关键词示例：`"user journey gap analysis" + 行业词 + 2025`
- 搜索关键词示例：`"service blueprint" + "failure recovery" + 产品类型`
- 来源优先级：官方规范/权威研究 > 一线团队实践 > 社区经验
- 决策留痕：记录 `ADOPT|REJECT|DEFER` 与理由，避免“收集后无决策”

建议将来源写入：`.allforai/product-design/trend-sources.json`（跨阶段共用）。

## 信息保真增强（4D + 6V）

执行本阶段时，建议同步参考：`docs/information-fidelity.md`。

- 缺口项除 `type` 外建议补充：`source_refs`、`constraints`、`decision_rationale`。
- 缺口建议按 6 视角归类（`user/business/tech/ux/data/risk`），避免只按技术表象分组。
- 对高优先级缺口，建议明确”哪一层信息丢失/失真”及其上游来源。

## 跨模型交叉验证（可选增强）

当 `mcp__openrouter__ask_model` 工具可用时，在 Step 4（生成缺口任务清单）完成后自动发起交叉验证，结果直接写入产出的 `cross_model_review` 字段。

| 验证点 | task_type | 发送内容 | 写入字段 |
|--------|-----------|----------|----------|
| 旅程断点验证 | `journey_validation`→gemini | 缺口列表 + 用户旅程评分 + 业务流摘要 | cross_model_review.overlooked_journey_breaks |
| 缺口优先级修正 | `gap_prioritization`→gpt | 缺口任务清单 + 频次/风险分布 + 优先级排序 | cross_model_review.priority_adjustments |

**自动写入内容**：被忽略的旅程断点（跨角色交接失配、异步流程断裂）、优先级修正建议（低频高风险缺口是否应提升、高频低影响缺口是否过度排序）。

工具不可用或调用失败时，自动跳过，不阻塞流程，不生成 `cross_model_review` 字段。

## 中段经理理论支持（可选增强）

为让“查漏”结果更适合产品管理协同，可在现有检查项上叠加以下框架：

| 理论/框架 | 对应步骤 | 落地方式 |
|-----------|----------|----------|
| INVEST（用户故事质量） | Step 1 | 将 `NO_RULES` / `NO_ACCEPTANCE_CRITERIA` 归因为故事不可测试或不可协商，便于回写需求质量 |
| DoR / DoD | Step 1/4 | 将任务完整性检查映射为 Ready/Done 门禁，缺口任务直接对齐迭代准入标准 |
| 风险矩阵（Impact × Probability） | Step 4 | 缺口优先级除 frequency 外，增加风险评分，避免低频高风险缺口被延后 |
| 服务蓝图（Service Blueprint） | Step 3/5 | 旅程断点与跨系统流断点对应前台/后台交接失配，便于跨团队协作修复 |

> 上述增强不改变原有“只查不加”原则，仅提升缺口分类的管理可解释性。

---

## 模式说明

**quick 模式**：Step 1 → Step 4（跳过 Step 2 界面检查、Step 3 旅程验证、Step 5 业务流检查）。

**refresh 模式**：将 `gap-decisions.json` 重命名为 `.bak` 备份，从 Step 1 开始完整重新运行，忽略所有已有决策缓存。

---

## 工作流

```
前置：两阶段加载
      Phase 1 — 加载索引（< 5KB）：
        检查 task-index.json → 获取任务 id/task_name/frequency/owner_role/risk_level + 模块分组
        检查 screen-index.json → 获取界面 id/name/task_refs/action_count/has_gaps + 模块分组
        检查 flow-index.json → 获取业务流 id/name/node_count/gap_count/roles
        任一索引不存在 → 对应数据回退到 Phase 2 全量加载（向后兼容）
      Phase 2 — 按需加载完整数据：
        加载 .allforai/product-map/product-map.json
        若 product-map.json 也不存在 → 提示用户先运行 /product-map，终止
      ↓
Step 1: 任务完整性检查
      基于 .allforai/product-map/task-inventory.json
      role 模式：从 task-index.json 筛选指定角色的任务 ID，仅加载这些任务的完整数据
      ↓ 用户确认
Step 2: 界面与按钮完整性检查
      基于 .allforai/screen-map/screen-map.json
      若 .allforai/screen-map/screen-map.json 不存在 → 跳过 Step 2，提示用户运行 /screen-map
      ↓ 用户确认（或跳过）
Step 3: 用户旅程验证
      基于 .allforai/screen-map/screen-map.json
      若 .allforai/screen-map/screen-map.json 不存在 → 跳过 Step 3，提示用户运行 /screen-map
      ↓ 用户确认（或跳过）
Step 4: 生成缺口任务清单
      ↓ 用户确认
Step 5: 业务流链路完整性检查
      flow-index.json 存在且所有流的 gap_count == 0 → 跳过全量加载，直接报告「无流级缺口」
      否则加载 .allforai/product-map/business-flows.json
      若 business-flows.json 不存在 → 跳过 Step 5，提示用户运行 /product-map
```

---

### Step 1：任务完整性检查

**数据加载**：`role` 模式下，先从 `task-index.json` 按 `owner_role` 筛选匹配任务 ID 列表，然后仅加载这些任务的完整数据（从 `task-inventory.json` 中按 ID 读取），避免全量加载。其他模式或索引不存在时，加载全量 `task-inventory.json`。

遍历任务数据中每个任务，逐一检查：

| 检查项 | 说明 |
|--------|------|
| exceptions 已填写 | 任务的 `exceptions` 是否为空（空 = 异常设计缺失） |
| acceptance_criteria 已填写 | 任务的 `acceptance_criteria` 是否为空（空 = 验收标准缺失） |
| main_flow CRUD 完整 | 同一任务下的 `main_flow` 步骤，增删改查是否齐全（根据任务性质判断应该有哪些） |
| 高频可达 | `frequency=高` 的任务，`prerequisites` 是否过于复杂，是否可达 |
| 规则完整性 | `rules` 字段是否有覆盖任务的核心约束 |

分类结果：

| 分类 | 含义 |
|------|------|
| `COMPLETE` | 任务完整，无缺口 |
| `CRUD_INCOMPLETE` | `main_flow` 缺少必要的增删改查步骤 |
| `NO_EXCEPTIONS` | `exceptions` 为空，异常设计缺失 |
| `NO_ACCEPTANCE_CRITERIA` | `acceptance_criteria` 为空，验收标准缺失 |
| `HIGH_FREQ_BURIED` | 高频任务前置条件过于复杂，可达性存疑 |
| `NO_RULES` | `rules` 为空，任务约束未定义 |

输出：`.allforai/feature-gap/task-gaps.json`

```json
[
  {
    "task_id": "T001",
    "task_name": "{任务名}",
    "frequency": "高 | 中 | 低",
    "gaps": ["CRUD_INCOMPLETE", "NO_EXCEPTIONS"],
    "details": {
      "crud_missing": ["删除"],
      "exceptions_count": 0,
      "acceptance_criteria_count": 0,
      "rules_count": 0,
      "high_freq_buried": false
    }
  }
]
```

---

### Step 2：界面与按钮完整性检查

**前置检查**：`.allforai/screen-map/screen-map.json` 是否存在
- 不存在 → 跳过 Step 2，在报告中注明：「Step 2 已跳过，需先运行 /screen-map 生成界面地图」
- 存在 → 遍历每个界面，检查以下项目

| 检查项 | 说明 |
|--------|------|
| 主操作存在 | 是否有 `is_primary=true` 的按钮 |
| 主操作频次匹配 | `primary_action` 是否确实是频次最高的操作 |
| 高风险有确认 | `task.risk_level=高` 的任务对应按钮，`requires_confirm` 是否为 true |
| 角色权限一致 | 按钮的 `roles` 与任务的 `owner_role` 是否一致 |
| 孤儿界面 | 界面存在但没有任务关联（`tasks` 为空） |
| 操作有失败反馈 | C/U/D 按钮的 `on_failure` 是否已定义（`SILENT_FAILURE` 检测） |
| 表单有校验规则 | 表单提交按钮的 `validation_rules` 是否为空（`MISSING_VALIDATION` 检测） |
| 列表有空状态 | 列表/表格界面的 `states.empty` 是否已定义（`NO_EMPTY_STATE` 检测） |
| 异常有界面响应 | task.exceptions 中每条异常，`exception_flows` 是否有对应（`UNHANDLED_EXCEPTION` 检测） |

分类结果：

| 分类 | 含义 |
|------|------|
| `NO_PRIMARY` | 界面没有主操作，用户不知道该做什么 |
| `PRIMARY_MISMATCH` | 主操作不是最高频的操作 |
| `HIGH_RISK_NO_CONFIRM` | 高风险操作缺少二次确认 |
| `ROLE_MISMATCH` | 按钮权限与任务角色不一致 |
| `ORPHAN_SCREEN` | 界面没有关联任何任务，疑似废弃 |
| `SILENT_FAILURE` | C/U/D 按钮无 `on_failure`，操作失败无反馈 |
| `MISSING_VALIDATION` | 表单提交按钮无 `validation_rules`，缺少前端校验 |
| `NO_EMPTY_STATE` | 列表界面无 `states.empty`，空数据无处理 |
| `UNHANDLED_EXCEPTION` | task.exceptions 中有异常，但界面无对应 `exception_flows` |
| `NO_SCREEN` | 任务在 task-inventory 中存在，但 screen-map 中无对应界面 |
| `ENTRY_BROKEN` | 界面存在但从主导航无法到达（入口链路断裂） |

输出：`.allforai/feature-gap/screen-gaps.json`

```json
[
  {
    "screen_id": "S001",
    "screen_name": "{界面名}",
    "gaps": ["NO_PRIMARY", "SILENT_FAILURE"],
    "details": [
      {
        "flag": "SILENT_FAILURE",
        "description": "「{按钮名}」按钮 on_failure 未定义",
        "affected_tasks": ["T001"],
        "severity": "高 | 中 | 低"
      }
    ]
  }
]
```

---

### Step 3：用户旅程验证

**前置检查**：`.allforai/screen-map/screen-map.json` 是否存在
- 不存在 → 跳过 Step 3，在报告中注明：「Step 3 已跳过，需先运行 /screen-map 生成界面地图」
- 存在 → 按角色逐一走完整路径，验证四个节点

```
入口存在？  →  主操作可触达？  →  操作有反馈？  →  结果可见？
（能找到）     （click_depth=1）  （on_failure 或成功提示）  （列表/详情更新）
```

每个旅程评分 X/4，标注断点位置。

评分说明：

| 分数 | 含义 |
|------|------|
| 4/4 | 旅程完整 |
| 3/4 | 轻微缺口，可用但体验差 |
| 2/4 | 旅程中断，主要功能受影响 |
| 1/4 | 严重缺口，功能基本不可用 |
| 0/4 | 完全不可用 |

**旅程验证新增节点**：Step 3 中「操作有反馈」节点现检查 `on_failure` 是否定义，而非仅检查成功提示。若 `on_failure` 缺失，旅程在此节点断开。

输出：`.allforai/feature-gap/journey-gaps.json`

```json
[
  {
    "role": "{角色名}",
    "task_id": "T001",
    "task_name": "{任务名}",
    "score": "3/4",
    "breakpoints": [
      {
        "node": "操作有反馈",
        "issue": "on_failure 未定义",
        "affected_screen": "S001"
      }
    ]
  }
]
```

---

### Step 4：生成缺口任务清单

将所有确认缺口转换为可执行任务，按优先级排序：

**优先级规则**（由高到低）：
1. 高频任务的缺口（影响最多用户）
2. 旅程断点（0-1/4 评分）
3. `SILENT_FAILURE` / `UNHANDLED_EXCEPTION`（操作失败无反馈，用户感知最差）
4. `HIGH_RISK_NO_CONFIRM`（安全问题）
5. `CRUD_INCOMPLETE` / `NO_EXCEPTIONS` / `NO_ACCEPTANCE_CRITERIA`
6. 孤儿界面清理

每条任务格式：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 feature-gap 分析结果决定，不限行业。

```json
{
  "id": "GAP-001",
  "title": "退款申请页「提交」按钮无失败反馈（SILENT_FAILURE）",
  "type": "SILENT_FAILURE",
  "priority": "高",
  "affected_roles": ["客服专员"],
  "affected_tasks": ["T001"],
  "affected_screens": ["S001"],
  "description": "「提交退款申请」按钮 on_failure 未定义，提交失败时用户无任何错误提示",
  "frequency_impact": "高频任务，影响所有客服日常工作"
}
```

输出：
- `.allforai/feature-gap/gap-tasks.json` — 缺口任务清单
- `.allforai/feature-gap/gap-report.md` — 可读报告
- `.allforai/feature-gap/gap-decisions.json` — 用户确认记录

**gap-report.md 结构**：

```markdown
# 功能缺口报告

## 摘要
- 任务缺口：X 个（高 X / 中 X / 低 X）
- 界面缺口：X 个
- 旅程缺口：X 个
- 业务流缺口：X 个

## 缺口任务清单（按优先级排序）
| 优先级 | 任务 | 缺口类型 | 描述 |
|--------|------|---------|------|
| P0 | ... | ... | ... |

## Flag 统计
| Flag | 数量 | 影响 |
|------|------|------|
| ... | ... | ... |
```

**用户确认**：缺口优先级排序合理吗？有需要调整优先级或移除的缺口吗？

---

### Step 5：业务流链路完整性检查（需 business-flows.json）

**快速预检（索引优化）**：若 `flow-index.json` 存在，先检查所有流的 `gap_count`。若所有流 `gap_count == 0`，可跳过全量加载 `business-flows.json`，直接报告「索引显示无流级缺口，跳过全量检查」。若存在 `gap_count > 0` 的流，继续加载完整数据做详细检查。

**前置检查：** 若 `.allforai/product-map/business-flows.json` 不存在（且 `flow-index.json` 也不存在），跳过此步骤，提示先运行 `/product-map`。

读取 `business-flows.json`，执行两项检查：

**检查 1：孤立任务（ORPHAN_TASK）**

遍历 `task-inventory.json` 所有任务，检查是否被任意流的节点引用。未被引用的任务标记为 `ORPHAN_TASK`，供用户判断是独立功能还是遗漏建模。

**检查 2：流终止节点（MISSING_TERMINAL）**

遍历每条流的节点，检查是否存在面向用户的终止节点（`role` 为最终用户角色 + 该节点的 task 有 `outputs.messages` 或 `outputs.states`）。若无，标记 `MISSING_TERMINAL`。

输出：`.allforai/feature-gap/flow-gaps.json`

```json
[
  {
    "flow_id": "F001",
    "flow_name": "{业务流名称}",
    "gap_type": "ORPHAN_TASK | MISSING_TERMINAL",
    "description": "描述",
    "affected_tasks": ["T001", "T008"],
    "severity": "高 | 中 | 低"
  }
]
```

---

## 输出文件结构

```
.allforai/feature-gap/
├── task-gaps.json        # Step 1: 任务完整性检查结果
├── screen-gaps.json      # Step 2: 界面与按钮完整性检查结果（需 screen-map）
├── journey-gaps.json     # Step 3: 用户旅程验证结果（需 screen-map）
├── gap-tasks.json        # Step 4: 缺口任务清单（按优先级排序）
├── gap-report.md         # 可读报告
├── gap-decisions.json    # 用户确认记录（增量运行复用）
└── flow-gaps.json        # 业务流链路完整性检查结果（需 business-flows.json）
```

### decisions.json 通用格式

```json
[
  {
    "step": "Step 1",
    "item_id": "T001",
    "item_name": "描述",
    "decision": "confirmed | modified | deferred",
    "reason": "用户备注（可选）",
    "decided_at": "2024-01-15T10:30:00Z"
  }
]
```

- `confirmed`：确认为真实缺口
- `modified`：修改严重级别或描述后确认
- `deferred`：暂不处理，下次重新评估

**加载逻辑**：每个 Step 开始前检查 decisions.json，已 `confirmed` 的条目跳过确认直接沿用。

---

## 防御性规范

> 通用模式定义见 `docs/defensive-patterns.md`，以下为本技能的具体应用。

### 加载校验
- **`gap-decisions.json`**：加载时用 `python -m json.tool` 验证 JSON 合法性。解析失败 → 检查 `.bak` → 提示恢复或重新运行 `/feature-gap refresh`。
- **三个索引文件**（`task-index.json`、`screen-index.json`、`flow-index.json`）：加载时验证 JSON 合法性。单个索引解析失败 → 该索引回退到全量加载对应完整文件，其余索引不受影响。

### 零结果处理
- **全部检查通过 0 缺口**：✓ 明确告知「所有检查通过，未发现功能缺口（共检查 {N} 个任务 / {M} 个界面 / {K} 条旅程）」，不输出空报告。
- **Step 1 某任务所有检查项均 COMPLETE**：正常，不标记。
- **role 模式匹配 0 任务**：明确告知「角色 "{角色名}" 未匹配任何任务，请检查拼写或查看 role-profiles.json 中的角色列表」。

### 规模自适应
- **阈值**：以任务数为计量对象。small ≤30 / medium 31–80 / large >80。
- **small**（≤30 任务）：逐任务展示检查结果，逐条确认。
- **medium**（31–80 任务）：按模块摘要展示，仅展开有缺口项。
- **large**（>80 任务）：统计总览 + 仅展开高频/高风险缺口。

### WebSearch 故障
- **趋势搜索**（动态趋势补充）：工具不可用或无有用结果 → 跳过趋势补充，不影响缺口检测主流程。

### 上游过期检测
- **`task-index.json` / `task-inventory.json`**：加载时比较 `generated_at` 与 `gap-decisions.json` 最新 `decided_at`。上游更新 → ⚠ 警告。
- **`screen-index.json` / `screen-map.json`**：同理。上游更新 → ⚠ 警告「screen-map 已更新，Step 2/3 结果可能过期」。
- **`flow-index.json` / `business-flows.json`**：同理。上游更新 → ⚠ 警告「business-flows 已更新，Step 5 结果可能过期」。
- 仅警告不阻断。

### 跨步骤引用完整性
- **Step 3 旅程验证**：旅程引用的 `task_id` 必须存在于 `task-inventory.json`。断言失败 → 标记 `BROKEN_REF` + 警告用户「旅程 {journey_id} 引用的 task_id {id} 在 task-inventory 中不存在」。
- **Step 5 业务流检查**：流节点引用的 `task_ref` 必须存在于 `task-inventory.json`。断言失败 → 标记 `BROKEN_REF`。
- 不中断流程，但记录到报告中。

---

## 4 条铁律

### 1. 以产品地图为唯一基准

只检查 `product-map` 中已定义的任务。不引入产品地图之外的期望。发现产品地图之外的问题，先去更新产品地图，再重跑查漏。

### 2. 频次决定优先级

缺口任务的优先级由 `frequency` 决定。高频任务的缺口排在前面，低频任务的缺口排在后面。`SILENT_FAILURE` 和 `UNHANDLED_EXCEPTION` 因用户感知最差，优先级与高频缺口同级。

### 3. 用户确认每个分类

`CRUD_INCOMPLETE`、`ORPHAN_SCREEN`、`UNHANDLED_EXCEPTION` 等分类由 Claude 初步判断，用户逐条确认。用户说"这是故意的"，则标记为 `DEFERRED`，不进入任务清单。

### 4. 只查不加

报告只描述"缺什么"，不描述"应该怎么做"。实现方案由开发团队决定，不在此技能范围内。
