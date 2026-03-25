---
name: feature-gap
description: >
  Use when the user asks to "find missing features", "check feature gaps",
  "what's incomplete", "verify user journeys", "check CRUD completeness",
  "check state machine completeness", "feature-gap", "功能查漏", "查漏补缺",
  "找缺口", "功能是否完整", "旅程是否走通", "状态机", "状态转换", "死端状态",
  "哪些功能没做完", "缺少什么功能", "用户路径有没有断点",
  or mentions gap detection, missing screens, broken user journeys,
  incomplete CRUD, or features that exist in product-map but not in reality.
  Requires product-map to have been run first.
version: "2.3.0"
---

# Feature Gap — 功能查漏

> 产品地图说应该有的，现在有没有？用户路径走得通吗？

## 目标

以 `product-map` 为基准，回答两个问题：

1. **有没有？** — 产品地图中每个任务、界面、按钮，是否真实存在？
2. **走得通吗？** — 每个角色从进入到完成任务，路径是否完整不断？

发现缺口，生成任务清单。不建议添加任何不在产品地图中的功能。

当 `product-map.json` 中的 `experience_priority.mode = consumer` 或 `mixed` 时，还要额外回答第三个问题：

3. **像成熟用户产品吗？** — 用户端是否只有概念映射和功能壳子，还是已经具备主线、反馈、状态系统和持续关系

---

## 定位

```
product-map（现状+方向）   功能查漏（查缺口）
产品应该长什么样           地图说有的，现在有没有
基础层                    基于 product-map
```

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/product-map.json`。

若 `product-map.json` 含 `experience_priority`，feature-gap 必须继承该字段，切换不同的查漏标准。

---

## 快速开始

```
/feature-gap           # 完整查漏（任务+界面+旅程）
/feature-gap quick     # 只查任务和 CRUD，跳过旅程验证
/feature-gap journey   # 只验证用户旅程路径
/feature-gap role 运营专员  # 只查指定角色的功能缺口
/feature-gap refresh    # 清除决策缓存，完整重跑
```

## 增强协议（WebSearch + 4D+6V + XV）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：`”user journey gap analysis” + 行业词 + 2025`、`”service blueprint” + “failure recovery” + 产品类型`

**4D+6V 重点**：缺口附带频次+来源；按 6 视角归类（`user/business/tech/ux/data/risk`），避免只按技术表象分组；高优先级缺口明确”哪一层信息丢失/失真”及其上游来源。

**XV 交叉验证**（Step 4 生成缺口任务清单后）：

| 验证点 | task_type | 发送内容 | 写入字段 |
|--------|-----------|----------|----------|
| 旅程断点验证 | `journey_validation`→gemini | 缺口列表 + 用户旅程评分 + 业务流摘要 | cross_model_review.overlooked_journey_breaks |
| 缺口优先级修正 | `gap_prioritization`→gpt | 缺口任务清单 + 频次/风险分布 + 优先级排序 | cross_model_review.priority_adjustments |
| 状态图完整性验证 | `state_machine_validation`→gemini | 状态图 + 实体列表 + 业务流摘要 | cross_model_review.state_machine_gaps |

自动写入：被忽略的旅程断点（跨角色交接失配、异步流程断裂）、优先级修正建议（低频高风险缺口是否应提升、高频低影响缺口是否过度排序）。

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

**quick 模式**：Step 1 → Step 4（跳过 Step 2 界面检查、Step 3 旅程验证、Step 5 业务流检查、Step 6 状态机检查）。

**refresh 模式**：将 `gap-decisions.json` 重命名为 `.bak` 备份，从 Step 1 开始完整重新运行，忽略所有已有决策缓存。

---

## 全自动模式

**激活条件**（同时满足）：
1. `.allforai/product-concept/product-concept.json` 存在且含 `pipeline_preferences` 字段
2. 上下文含 `__orchestrator_auto: true`（由 `/product-design full` 编排器传入）

**未同时满足** → 保持标准交互模式（当前行为不变）。

**行为变化**：

| 步骤 | 标准模式 | 全自动模式 |
|------|----------|-----------|
| **Step 1 任务完整性确认** | AskUserQuestion 确认 | 自动确认，记入 `pipeline-decisions.json`（`decision: "auto_confirmed"`） |
| **Step 2 界面完整性确认** | AskUserQuestion 确认 | 自动确认 |
| **Step 3 旅程验证确认** | AskUserQuestion 确认 | 自动确认 |
| **Step 4 缺口清单确认** | AskUserQuestion 确认 | 自动确认（缺口任务自动生成，不等用户调整优先级） |
| **Step 5 业务流确认** | AskUserQuestion 确认 | 自动确认 |
| **Step 6 交互类型完整性确认** | AskUserQuestion 确认 | 自动确认（前置条件不满足 → 提示用户重跑上游） |
| **Step 7 状态机确认** | AskUserQuestion 确认 | 自动确认 |

**安全护栏**（自动模式下仍然停下来问用户）：
- ERROR 级验证失败（必须文件不存在、引用断裂）

---

## 工作流

```
前置：
      概念蒸馏基线（推拉协议 §三.A）：
        .allforai/product-concept/concept-baseline.json → 自动加载，不存在则 WARNING
      两阶段数据加载：
      Phase 1 — 加载索引（< 5KB）：
        检查 task-index.json → 获取任务 id/name/frequency/owner_role/risk_level + 模块分组
        检查 screen-index（embedded in experience-map.json） → 获取界面 id/name/task_refs/action_count/has_gaps + 模块分组
        检查 flow-index.json → 获取业务流 id/name/node_count/gap_count/roles
        任一索引不存在 → 对应数据回退到 Phase 2 全量加载（向后兼容）
      Phase 2 — 按需加载完整数据：
        加载 .allforai/product-map/product-map.json
        若 product-map.json 也不存在 → 提示用户先运行 /product-map，终止
      ↓
Step 1: 任务完整性检查
      基于 .allforai/product-map/task-inventory.json
      若 product-map.json 的 `experience_priority.mode = consumer|mixed`
      → 额外开启用户端成熟度缺口扫描
      role 模式：从 task-index.json 筛选指定角色的任务 ID，仅加载这些任务的完整数据
      ↓ 用户确认
Step 2: 界面与按钮完整性检查
      基于 .allforai/experience-map/experience-map.json
      若 .allforai/experience-map/experience-map.json 不存在 → 自动运行 experience-map 技能生成体验地图，然后继续 Step 2
      ↓ 用户确认
Step 3: 用户旅程验证
      基于 .allforai/experience-map/experience-map.json
      （Step 2 已保证 experience-map 存在）
      ↓ 用户确认
Step 4: 生成缺口任务清单
      ↓ 用户确认
Step 5: 业务流链路完整性检查
      flow-index.json 存在且所有流的 gap_count == 0 → 跳过全量加载，直接报告「无流级缺口」
      否则加载 .allforai/product-map/business-flows.json
      若 business-flows.json 不存在 → 跳过 Step 5，提示用户运行 /product-map
      ↓ 用户确认
Step 6: 交互类型完整性检查
      基于 experience-map.json 的 interaction_type 字段
      若 experience-map 不存在或无 interaction_type → 跳过此步骤
      ↓ 用户确认
Step 7: 状态机完整性检查（quick / journey 模式跳过）
      从任务数据中提取业务实体和状态，构建状态转换图
      检测死端/不可达/无恢复路径/无逆向转换/孤儿实体
      ↓ 用户确认
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
| 用户端闭环（consumer/mixed） | 用户端核心任务是否只描述一次性动作，没有反馈、结果可见、下一步引导 |
| 持续关系（consumer/mixed） | 用户端核心任务是否完全缺少历史、提醒、进度、通知、订阅、推荐等持续关系线索 |

分类结果：

| 分类 | 含义 |
|------|------|
| `COMPLETE` | 任务完整，无缺口 |
| `CRUD_INCOMPLETE` | `main_flow` 缺少必要的增删改查步骤 |
| `NO_EXCEPTIONS` | `exceptions` 为空，异常设计缺失 |
| `NO_ACCEPTANCE_CRITERIA` | `acceptance_criteria` 为空，验收标准缺失 |
| `HIGH_FREQ_BURIED` | 高频任务前置条件过于复杂，可达性存疑 |
| `NO_RULES` | `rules` 为空，任务约束未定义 |
| `NO_USER_LOOP` | 用户端任务只有动作，没有反馈闭环或下一步引导 |
| `NO_CONTINUITY_HOOK` | 用户端任务缺少回访/持续关系触点 |

输出：`.allforai/feature-gap/task-gaps.json`

```json
[
  {
    "task_id": "T001",
    "name": "{任务名}",
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

**前置检查**：
- `.allforai/product-concept/concept-baseline.json` 自动加载（推拉协议 §三.A）→ 不存在则 WARNING，不阻塞
- `.allforai/experience-map/experience-map.json` 是否存在
  - 不存在 → 自动加载并执行 `${CLAUDE_PLUGIN_ROOT}/skills/experience-map.md` 的完整工作流生成体验地图，完成后继续 Step 2
  - 存在 → 直接进入检查
- 从 `operation_lines[].nodes[].screens[]` 提取界面，遍历每个界面，检查以下项目

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
| 用户端首页主线（consumer/mixed） | 首页/入口页是否只有功能入口拼盘，没有明确主线任务或状态总览 |
| 用户端下一步引导（consumer/mixed） | 核心界面是否缺少“下一步做什么”的明确引导 |
| 用户端持续关系入口（consumer/mixed） | 是否缺少历史/提醒/通知/最近活动/进度等相关入口 |

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
| `NO_SCREEN` | 任务在 task-inventory 中存在，但 experience-map 中无对应界面 |
| `ENTRY_BROKEN` | 界面存在但从主导航无法到达（入口链路断裂） |
| `NO_PRIMARY_JOURNEY` | 用户端首页缺少明确主线任务或状态总览 |
| `NO_NEXT_STEP_GUIDANCE` | 核心界面缺少下一步引导，用户做完动作后容易失焦 |
| `NO_CONTINUITY_ENTRY` | 用户端缺少历史/提醒/通知/最近活动/进度等持续关系入口 |

输出：`.allforai/feature-gap/screen-gaps.json`

```json
[
  {
    "id": "S001",
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

**前置检查**：`.allforai/experience-map/experience-map.json` 是否存在
- 不存在 → 自动加载并执行 `${CLAUDE_PLUGIN_ROOT}/skills/experience-map.md` 的完整工作流生成体验地图（若 Step 2 已触发自动运行，此处 experience-map 必已存在）
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

若 `experience_priority.mode = consumer` 或 `mixed`，还需额外判断：

- 完成核心动作后，用户是否知道接下来做什么
- 结果是否可见，且能回到后续使用链路
- 旅程是否只停在“一次完成”，没有任何持续关系

输出：`.allforai/feature-gap/journey-gaps.json`

```json
[
  {
    "role": "{角色名}",
    "task_id": "T001",
    "name": "{任务名}",
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
3. `SILENT_FAILURE` / `UNHANDLED_EXCEPTION` / `DEAD_END_STATE` / `NO_ERROR_RECOVERY`（操作失败无反馈 / 用户卡住 / 异常无恢复）
4. `HIGH_RISK_NO_CONFIRM`（安全问题）
5. `CRUD_INCOMPLETE` / `NO_EXCEPTIONS` / `NO_ACCEPTANCE_CRITERIA` / `UNREACHABLE_STATE`
6. `NO_USER_LOOP` / `NO_CONTINUITY_HOOK` / `NO_PRIMARY_JOURNEY` / `NO_NEXT_STEP_GUIDANCE` / `NO_CONTINUITY_ENTRY`
7. `NO_REVERSE_TRANSITION` / 孤儿界面清理
8. `ORPHAN_ENTITY`（建模不充分，低优先级）

每条任务格式：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 feature-gap 分析结果决定，不限行业。

```json
{
  "id": "GAP-001",
  "title": "工单提交页「提交」按钮无失败反馈（SILENT_FAILURE）",
  "type": "SILENT_FAILURE",
  "priority": "高",
  "affected_roles": ["运营专员"],
  "affected_tasks": ["T001"],
  "affected_screens": ["S001"],
  "description": "「提交工单」按钮 on_failure 未定义，提交失败时用户无任何错误提示",
  "frequency_impact": "高频任务，影响所有运营专员日常工作"
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
- 交互类型缺口：X 个（高 X / 中 X / 低 X）
- 状态机缺口：X 个

## 缺口任务清单（按优先级排序）
| 优先级 | 任务 | 缺口类型 | 描述 |
|--------|------|---------|------|
| P0 | ... | ... | ... |

## Flag 统计
| Flag | 数量 | 影响 |
|------|------|------|
| ... | ... | ... |

## 交互类型完整性（Step 6）
| 类型 | 实体/界面 | 缺失项 | 严重度 |
|------|----------|--------|--------|
| ... | ... | ... | ... |
```

> **搜索驱动原则**：展示缺口分析结果前，先 WebSearch 搜索「{产品类型} feature completeness checklist」和「{行业} common missing features」，用搜索结果交叉验证缺口检测的覆盖面。

**用户确认**：缺口优先级排序合理吗？有需要调整优先级或移除的缺口吗？

若 `experience_priority.mode = consumer` 或 `mixed`，必须额外确认：

- 用户端缺口是否停留在“功能存在性”视角，遗漏了成熟度缺口
- 是否已经识别出首页主线、持续关系、下一步引导、结果反馈相关缺口

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

### Step 6：交互类型完整性检查

**目标**：基于 `interaction-types.md` 的类型定义，检测每种交互类型是否具备必要的交互能力。

**前置检查**：
1. `.allforai/experience-map/experience-map.json` 是否存在
   - 不存在 → 提示「请先运行 /experience-map 生成体验地图」，终止
2. experience-map 中每个 screen（`operation_lines[].nodes[].screens[]`）是否含 `interaction_type` 字段
   - 缺失 → 提示「experience-map 未标注 interaction_type，请运行 /experience-map refresh 重新生成」，终止

---

#### 类型完整性规则

从 `${CLAUDE_PLUGIN_ROOT}/docs/interaction-types.md` 提取以下规则：

| 类型 | 必须具备 | 检测逻辑 |
|------|----------|----------|
| **MG2 CRUD实体集群** | L(列表) + C(新建) + E(编辑)，D(详情)可选 | 同一实体的 screen 集合必须覆盖 MG2-L/C/E |
| **MG2-ST 状态流转** | 状态操作界面 | 若实体有状态字段，必须有状态操作入口 |
| **MG3 状态机驱动** | 每种状态有合法触发操作 | 状态机的所有非终止状态必须有出边 |
| **MG4 审批流** | 待审队列 + 详情 + 批准 + 驳回 | 必须有 approve + reject 操作 |
| **MG5 主从详情** | 主实体 + ≥1个子实体Tab | screen 必须有嵌套子实体列表 |
| **MG6 树形管理** | 树结构 + 新建(含父节点) + 删除(含子节点处理) | 必须有 tree 相关操作 |
| **EC1 内容详情** | 图片浏览 + 规格选择 + 收藏/获取 | 必须有 select-variant + add-to-collection/acquire |
| **EC2 待处理列表** | 数量修改 + 删除 + 确认提交 | 必须有 update-quantity + remove + submit |
| **WK1 对话/IM** | 发送消息 + 历史加载 | 必须有 send-message + load-history |
| **WK3 文档编辑** | 协同编辑 + 版本历史 | 必须有 collaborative + version-history |
| **WK5 看板** | 卡片创建 + 跨列拖拽 + 列管理 | 必须有 create-card + drag-card |
| **SB1 审核型提交** | 草稿 + 提交 + 查看状态 + 驳回后重提 | 必须有 draft + submit + view-status |

---

#### 检测逻辑

```python
# 伪代码示意
def check_type_completeness(screens, interaction_types_def):
    gaps = []
    
    # 按 interaction_type 分组
    by_type = group_by(screens, 'interaction_type')
    
    for type_key, type_screens in by_type.items():
        
        # MG2 完整性检测
        if type_key.startswith('MG2'):
            entity_screens = group_by(type_screens, 'entity')
            for entity, screens in entity_screens.items():
                sub_types = [s.get('sub_type', '') for s in screens]
                has_L = any('MG2-L' in st for st in sub_types)
                has_C = any('MG2-C' in st for st in sub_types)
                has_E = any('MG2-E' in st for st in sub_types)
                
                if not has_L:
                    gaps.append({
                        'type': type_key,
                        'entity': entity,
                        'missing': 'MG2-L(列表)',
                        'severity': 'high'
                    })
                if not has_C:
                    gaps.append({
                        'type': type_key,
                        'entity': entity,
                        'missing': 'MG2-C(新建)',
                        'severity': 'high'
                    })
                if not has_E:
                    gaps.append({
                        'type': type_key,
                        'entity': entity,
                        'missing': 'MG2-E(编辑)',
                        'severity': 'high'
                    })
        
        # MG3 状态机完整性
        elif type_key == 'MG3':
            for screen in type_screens:
                states = screen.get('entity_states', [])
                actions = screen.get('actions', [])
                unreachable = find_unreachable_states(states, actions)
                if unreachable:
                    gaps.append({
                        'type': 'MG3',
                        'screen': screen['id'],
                        'missing': f'状态 {unreachable} 无触发操作',
                        'severity': 'medium'
                    })
        
        # EC1 内容详情完整性
        elif type_key == 'EC1':
            for screen in type_screens:
                actions = [a.get('action') for a in screen.get('actions', [])]
                if 'select-variant' not in actions:
                    gaps.append({
                        'type': 'EC1',
                        'screen': screen['id'],
                        'missing': '规格选择(select-variant)',
                        'severity': 'high'
                    })
                if 'add-to-collection' not in actions and 'acquire' not in actions:
                    gaps.append({
                        'type': 'EC1',
                        'screen': screen['id'],
                        'missing': '收藏/获取操作',
                        'severity': 'high'
                    })
    
    return gaps
```

---

#### 输出格式

输出：`.allforai/feature-gap/type-gaps.json`

```json
{
  "generated_at": "ISO8601",
  "total_types_checked": 12,
  "complete_types": 8,
  "incomplete_types": 4,
  "gaps": [
    {
      "type": "MG2",
      "entity": "内容条目",
      "existing_screens": ["MG2-L(列表)", "MG2-D(详情)"],
      "missing": ["MG2-C(新建)", "MG2-E(编辑)"],
      "severity": "high",
      "recommendation": "CRUD 实体缺少新建和编辑入口，建议补充"
    },
    {
      "type": "MG3",
      "entity": "工单",
      "screen": "S015",
      "missing": ["pending→processing 的触发操作"],
      "severity": "medium",
      "recommendation": "检查状态机定义，确认 pending 状态的用户操作入口"
    },
    {
      "type": "EC1",
      "screen": "S020",
      "missing": ["规格选择(select-variant)"],
      "severity": "high",
      "recommendation": "内容详情页缺少规格选择功能，无法完成选择决策"
    }
  ]
}
```

---

#### 与现有流程集成

- **quick / journey 模式**：跳过 Step 6
- **role 模式**：仅检查指定角色关联的 screen
- **检测时机**：在 Step 6（状态机检查）之后，作为功能完整性的补充维度

**用户确认**：展示类型完整性摘要（检查 N 种类型，M 个缺口），用户确认后写入 decisions。

---

### Step 7：状态机完整性检查（quick / journey 模式跳过）

**目标**：从任务数据中提取业务实体的状态转换图，检测死端、不可达、无恢复路径等完整性问题。

---

### Step 6.5：状态闭环验证（增强版，通用）

**目标**：验证每个状态从产生到流转形成完整闭环，不依赖特定行业

**工作流程**：

1. **提取状态生产者**（通用）：
   - 扫描所有任务的 `outputs.states`
   - 不预设状态语义，仅提取状态名称
   - 构建 `{state_name: [producer_task_ids]}` 映射

2. **提取状态消费者**（通用）：
   - 扫描所有任务的 `prerequisites`
   - 扫描所有业务流节点的 `prerequisites`
   - 构建 `{state_name: [consumer_task_ids]}` 映射

3. **供需匹配分析**（通用规则）：
   - **孤儿状态**：有生产无消费（任何领域都应该避免）
   - **幽灵状态**：有消费无生产（任何领域都零容忍）
   - **语义鸿沟**：名称不同但语义相似（NLP 相似度>0.8）

4. **状态流转路径追踪**（新增，通用）：
   - 对每个状态，构建完整的流转路径图
   - **路径起点**：生产者任务的 outputs.states
   - **路径中间**：业务流中的状态转换节点
   - **路径终点**：消费者任务的 prerequisites 或终止状态
   - **检测断裂**：路径中间是否有缺失节点
   - **检测死循环**：状态 A→B→A 的无限循环（无终止状态）
   - **检测分支缺失**：状态转换是否有未处理的分支（如"审核通过"有处理，但"审核拒绝"无处理）

4. **创新概念状态验证**（若 `innovation_mode=active`）：
   - 读取 `adversarial-concepts.json` 的 `state_machine`
   - 验证实现的状态流转是否符合定义
   - **不检查具体状态名称**，只检查：
     - 是否有初始状态
     - 是否有终止状态
     - 关键转换是否存在
     - 异常恢复路径是否存在

**输出 Schema**（通用）：
```json
{
  "orphan_states": [
    {
      "state": "状态 X",
      "producers": ["T001"],
      "consumers": [],
      "severity": "高",
      "business_impact": "该状态产生后无后续流转，形成数据孤岛"
    }
  ],
  "ghost_states": [
    {
      "state": "状态 Y",
      "producers": [],
      "consumers": ["T002"],
      "severity": "高",
      "business_impact": "该状态被引用但无产生来源，永远无法触发"
    }
  ],
  "semantic_gaps": [
    {
      "state_a": "状态 A",
      "state_b": "状态 B",
      "similarity": 0.85,
      "suggestion": "建议确认是否为同一状态的不同命名"
    }
  ],
  "innovation_state_gaps": [
    {
      "concept_id": "IC001",
      "entity": "实体名",
      "gap_type": "MISSING_TRANSITION | MISSING_INITIAL | MISSING_TERMINAL | NO_ERROR_RECOVERY",
      "expected": "期望的状态流转",
      "actual": "实际检测到的状态流转",
      "severity": "高"
    }
  ]
}
```

**严重度判定**（通用规则）：
- 孤儿状态（core 创新概念相关）：高
- 孤儿状态（常规功能）：中
- 幽灵状态：高（任何领域都零容忍）
- 语义鸿沟：中（建议修复）
- 创新概念状态缺口：高（必须修复）

**输出文件**：
- `.allforai/feature-gap/state-cycle-gaps.json`（新增）

**实体提取**：扫描 `task-inventory.json` 中所有任务的 `name`，提取业务实体：
- 含「管理/创建/审核/处理/编辑/删除/查看 X」→ 实体 X
- 同一实体被 2+ 个任务引用才纳入检查（避免单一引用的噪声实体）

**状态提取**：从以下字段中 NLP 提取每个实体的状态：
- `main_flow`：步骤中的状态变更语义（如「状态变为已审核」）
- `outputs.states`：任务输出中的目标状态
- `prerequisites`：前置条件中隐含的起始状态
- `exceptions`：异常处理中的错误状态
- `rules`：业务规则中的约束状态
- `handoff.mechanism`：交接机制中的转换触发

**构建状态图**：每个实体独立构建：

```json
{
  "generated_at": "ISO8601",
  "entities": {
    "工单": {
      "name": "工单",
      "source_tasks": ["T034"],
      "states": ["待审核", "审核中", "已完成", "已拒绝"],
      "transitions": [
        {"from": "待审核", "to": "审核中", "trigger": "开始审核", "source_task": "T034"}
      ],
      "initial_state": "待审核",
      "terminal_states": ["已完成"]
    }
  }
}
```

输出中间产物：`.allforai/feature-gap/state-graph.json`

**5 项完整性检查**：

| Flag | 含义 | 严重级 |
|------|------|--------|
| `UNREACHABLE_STATE` | 从 initial_state 出发无法到达 | 高 |
| `DEAD_END_STATE` | 非终止状态但无出边（用户卡住） | 高 |
| `NO_REVERSE_TRANSITION` | A→B 存在但无回退路径（如驳回后无法重提） | 中 |
| `NO_ERROR_RECOVERY` | 异常状态无出边回到正常流 | 高 |
| `ORPHAN_ENTITY` | 实体仅 1 个状态，建模不充分 | 低 |

**检查逻辑**：
1. **UNREACHABLE_STATE**：从 `initial_state` 做 BFS，未被访问到的状态标记
2. **DEAD_END_STATE**：非 `terminal_states` 中的状态，且无出边（无以该状态为 `from` 的 transition）
3. **NO_REVERSE_TRANSITION**：存在 A→B 但不存在 B→A（直接或多跳），且 A 非 `initial_state`、B 非 `terminal_state`
4. **NO_ERROR_RECOVERY**：从 `exceptions` 提取的错误状态，无出边回到非错误状态
5. **ORPHAN_ENTITY**：实体的 `states` 数组长度 ≤ 1

输出：`.allforai/feature-gap/state-gaps.json`

```json
[
  {
    "entity": "工单",
    "gaps": ["NO_REVERSE_TRANSITION"],
    "state_count": 4,
    "transition_count": 3,
    "affected_tasks": ["T034"],
    "details": {
      "dead_ends": [],
      "unreachable": [],
      "missing_reverse": [{"from": "待审核", "to": "审核中"}],
      "no_error_recovery": [],
      "orphan": false
    },
    "severity": "中"
  }
]
```

**用户确认**：展示状态图摘要（每个实体的状态数/转换数/缺口数）和缺口详情，用户确认后写入 decisions。

---

## 生成方式

LLM 直接分析 task-inventory + experience-map + business-flows，理解业务语义后检测功能缺口。缺口检测需要理解业务上下文（如"操作失败后用户应该能重试"是语义推理，脚本只能做字段存在性检查），因此由 LLM 主导。

缺口检测完全由 LLM 执行：结构扫描、语义分析、优先级判断和修复建议均基于 LLM 对业务上下文的理解。

**输出 schema 约束**：
- `gap-tasks.json` 必须是 `{"gaps": [...], "summary": {...}}` 对象格式（不允许裸数组）
- 每个 gap 必须有 `priority`（P0/P1/P2）、`gap_type`、`affected_tasks`

**XV 交叉验证（v3.3.0+）**：脚本自动执行 XV 交叉验证（需 `OPENROUTER_API_KEY` 环境变量）。通过 Python `urllib.request` 直连 OpenRouter API，不依赖 MCP。高严重度发现自动修正数据（追加缺口任务 / 调整优先级 / 标记重复），结果写入 `gap-tasks.json` 的 `cross_model_review` 字段。无 API Key 时静默跳过。

### 执行失败保护

- 任何步骤遇到不可恢复错误（JSON 解析失败、必须文件缺失、LLM 生成结果不合法）→ 写入 `.allforai/feature-gap/feature-gap-error.json`，包含 `{"error": "...", "step": "...", "timestamp": "..."}`，确保编排器能检测到失败而非静默空目录。

---

## 输出文件结构

```
.allforai/feature-gap/
├── task-gaps.json        # Step 1: 任务完整性检查结果
├── screen-gaps.json      # Step 2: 界面与按钮完整性检查结果（需 experience-map）
├── journey-gaps.json     # Step 3: 用户旅程验证结果（需 experience-map）
├── gap-tasks.json        # Step 4: 缺口任务清单（按优先级排序）
├── gap-tasks-high.json   # 高优先级缺口（人类阅读用）
├── gap-tasks-medium.json # 中优先级缺口
├── gap-tasks-low.json    # 低优先级缺口
├── gap-report.md         # 可读报告
├── gap-decisions.json    # 用户确认记录（增量运行复用）
├── flow-gaps.json        # Step 5: 业务流链路完整性检查结果（需 business-flows.json）
├── type-gaps.json        # Step 6: 交互类型完整性检查结果（需 experience-map interaction_type）
├── state-graph.json      # Step 7: 状态转换图中间产物（Claude 运行时生成）
└── state-gaps.json       # Step 7: 状态机完整性检查结果
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
- **两个索引文件**（`task-index.json`、`flow-index.json`）+ **screen-index（embedded in experience-map.json）**：加载时验证 JSON 合法性。单个索引解析失败 → 该索引回退到全量加载对应完整文件，其余索引不受影响。

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
- **`experience-map.json`**：同理。上游更新 → ⚠ 警告「experience-map 已更新，Step 2/3 结果可能过期」。
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

但当 `experience_priority.mode = consumer` 或 `mixed` 时，必须把“成熟度缺口”视为产品地图内生要求，而不是额外加戏：如果 product-map 已经判定用户端是主价值面，就必须检查它是否仍然只是概念壳子。

### 2. 频次+类别决定优先级

缺口任务的优先级由 `frequency` 和 `category` 共同决定。高频任务的缺口排在前面；`category=core` 的低频任务优先级不低于「中」（核心功能即使低频也需关注）。`SILENT_FAILURE` 和 `UNHANDLED_EXCEPTION` 因用户感知最差，优先级与高频缺口同级。

### 3. 用户确认每个分类

`CRUD_INCOMPLETE`、`ORPHAN_SCREEN`、`UNHANDLED_EXCEPTION` 等分类由 Claude 初步判断，用户逐条确认。用户说"这是故意的"，则标记为 `DEFERRED`，不进入任务清单。

### 4. 只查不加

报告只描述"缺什么"，不描述"应该怎么做"。实现方案由开发团队决定，不在此技能范围内。
