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
version: "2.1.0"
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
```

---

## 工作流

```
前置：加载 .allforai/product-map/product-map.json
      若文件不存在 → 提示用户先运行 /product-map，终止
      ↓
Step 1: 任务完整性检查
      基于 .allforai/product-map/task-inventory.json
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
```

---

### Step 1：任务完整性检查

遍历 `.allforai/product-map/task-inventory.json` 中每个任务，逐一检查：

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

输出：`.allforai/feature-gap/screen-gaps.json`

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

---

### Step 5：业务流链路完整性检查（需 business-flows.json）

**前置检查：** 若 `.allforai/product-map/business-flows.json` 不存在，跳过此步骤，提示先运行 `/product-map`。

读取 `business-flows.json`，执行两项检查：

**检查 1：孤立任务（ORPHAN_TASK）**

遍历 `task-inventory.json` 所有任务，检查是否被任意流的节点引用。未被引用的任务标记为 `ORPHAN_TASK`，供用户判断是独立功能还是遗漏建模。

**检查 2：流终止节点（MISSING_TERMINAL）**

遍历每条流的节点，检查是否存在面向用户的终止节点（`role` 为最终用户角色 + 该节点的 task 有 `outputs.messages` 或 `outputs.states`）。若无，标记 `MISSING_TERMINAL`。

输出：`.allforai/feature-gap/flow-gaps.json`

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
