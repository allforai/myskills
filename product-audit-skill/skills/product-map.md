---
name: product-map
description: >
  Use when the user asks to "map the product", "list all features", "identify user roles",
  "build a product map", "understand the product",
  "产品地图", "功能点梳理", "用户角色识别", "建立产品地图",
  "列出所有功能", "产品现状分析", "理解产品结构",
  or mentions mapping product features, understanding user tasks,
  understanding what a product does, mapping features by user role, doing an initial product inventory,
  or building a foundation for feature gap detection, pruning, or seed data generation.
version: "2.1.0"
---

# Product Map — 产品地图梳理

> 读代码了解现状，用 PM 语言呈现，建立"现状 + 期望"的完整产品地图

## 目标

以代码为输入、以 PM 视角为准绳，梳理产品的完整现状：

1. **谁在用** — 识别用户角色，明确权限边界和 KPI
2. **做了什么** — 按角色提取核心任务，标注频次、风险、跨部门依赖、异常与验收标准
3. **有没有问题** — 检测任务级冲突、规则矛盾、CRUD 缺口
4. **受什么约束** — 识别合规、审计、业务约束

---

## 定位

```
product-map（现状+方向）      screen-map（可选增强）        feature-gap（对齐视角）      feature-prune（决策视角）
项目现在有什么？应该有什么？   界面、按钮、异常状态梳理        地图说有的，现在有没有？      地图里有的，该不该留？
代码读现状，PM 定方向          以 task-inventory 为输入     以 product-map 为基准        以 product-map 为锚点
输出产品地图（PM 语言呈现）    输出界面交互地图              输出缺口报告                 输出剪枝报告
```

**核心定位**：读代码了解现状，用 PM 语言呈现，让 PM 确认并补充业务视角，最终形成"现状 + 期望"的完整产品地图，用于指导项目未来发展方向。

**后续技能依赖**：`feature-gap`、`feature-prune`、`seed-forge` 均以 `.allforai/product-map/product-map.json` 为输入基准，无需重复分析。界面交互细节由 `screen-map` 技能（可选）单独梳理。

---

## 快速开始

```
/product-map              # 完整流程（Step 0-6，无界面梳理）
/product-map quick        # 跳过冲突检测（Step 4）和约束识别（Step 5）
/product-map refresh      # 重新采集，忽略已有缓存
/product-map scope 退款管理  # 只梳理指定功能模块
```

---

## 工作流

```
Step 0: 项目画像
      读代码，提取技术栈、路由结构、权限系统、菜单配置
      转换为产品语言：有哪些功能模块、有哪些用户角色（草稿）
      → 用户确认画像是否准确
      ↓
Step 1: 用户角色识别
      从代码推导角色（权限枚举、守卫、角色配置）→ 转换为 PM 语言描述
      每角色：角色名 / 职责描述 / 权限边界 / KPI
      PM 可补充代码未体现的角色、删除已废弃的角色
      → 用户确认，生成 role-profiles.json
      ↓
Step 2: 核心任务提取（按角色展开）
      从代码提取每个角色的操作（路由、菜单项、权限点）→ 转换为业务任务描述
      每条任务使用完整功能点描述模板（见下方 Schema）
      PM 可补充代码没有的任务（期望方向）、标记代码有但业务不需要的任务
      → 用户确认任务清单，生成 task-inventory.json
      ↓
Step 3: 业务流建模（所有模式均不可跳过）
      自动识别候选流 + 用户补充跨系统链路
      检测流缺口：MISSING_TASK / BROKEN_HANDOFF / ORPHAN_TASK / MISSING_TERMINAL
      → 用户确认，生成 business-flows.json + business-flows-report.md
      ↓
Step 4: 冲突 & 冗余检测（quick 模式跳过）
      检测任务级冲突：两个任务的 rules 或状态流转互相矛盾
      检测 CRUD 缺口：任务的 main_flow 缺少必要操作类型
      只标记，不修改，最终决定由用户做出
      → 用户确认，排除误报，生成 conflict-report.json
      ↓
Step 5: 约束识别（quick 模式跳过）
      合规/审计要求（留痕、可追溯、保留期限、导出审批）
      业务约束（不可逆操作、金额对账一致性、审批分级）
      → 用户确认，生成 constraints.json
      ↓
Step 6: 输出产品地图报告
      汇总所有已确认数据，生成 product-map.json 和 product-map-report.md
      ↓
Step 7: 校验
      完整性扫描 + 冲突重扫 + 竞品差异（Web 搜索）
      → 用户确认，生成 validation-report.json + validation-report.md
```

**核心原则：每个 Step 结束都有用户确认，用户是权威。**

---

### Step 0：项目画像

两类输入并行，相互补充：

| 类型 | 来源 | 说明 |
|------|------|------|
| 工程输入 | 代码（路由、菜单、权限配置、页面组件） | 了解项目现状，提取已有功能点 |
| 产品输入 | PRD、用户故事、原型图描述、PM 口述 | 补充业务语义，确认方向，标记差距 |

代码告诉我们**现在有什么**，PM 确认**应该有什么**。两者的差距就是需要改进的方向。

读取代码中的路由配置、菜单定义、权限枚举和守卫，将工程结构转换为产品语言：

- 有哪些功能模块（菜单项 → 功能区）
- 有哪些用户角色（权限枚举 → 角色草稿）
- 大致的操作入口分布

若用户提供 PRD 或原型图描述，同步读取，标记代码中尚未实现的功能模块（`status: user_added`）和已废弃的模块（`status: user_removed`）。

生成 `role-profiles.json` **草稿**（仅在对话中展示，Step 1 用户确认后才写入磁盘）。

**竞品提问**（画像确认前，先问一句）：

> 这个产品主要对标哪些竞品？（例如：Shopify、有赞、微盟；或「暂时没有参照」也可以）

根据用户回答：
- **有竞品**：记录名字列表，生成 `competitor-profile.json` 草稿（只写名字，不做分析），Step 7 再做 Web 搜索
- **无竞品**：记录 `competitors: []`，`analysis_status` 设为 `"skipped"`，Step 7 只做完整性 + 冲突校验，跳过竞品差异部分

生成 `competitor-profile.json` 草稿：

```json
{
  "competitors": ["Shopify", "有赞"],
  "analysis_status": "pending",
  "analyzed_at": null
}
```

> 草稿此时只写入名字，Step 7 执行完后补全竞品功能数据，`analysis_status` 改为 `"completed"`。
> `analysis_status` 取值：`"pending"`（待分析）/ `"skipped"`（无竞品，Step 7 跳过竞品差异）/ `"completed"`（已完成）

**用户确认**：这个项目的功能全景对吗？有没有遗漏的模块？

---

### Step 1：用户角色识别

从代码中的权限枚举、路由守卫、角色配置推导角色，补充业务语义：

```json
{
  "roles": [
    {
      "id": "R001",
      "name": "客服专员",
      "description": "处理客户投诉、退款申请、订单异常",
      "permission_boundary": ["退款申请", "订单查询", "用户信息查询（脱敏）"],
      "kpi": ["处理时效 < 2h", "退款错误率 < 0.1%"],
      "status": "confirmed"
    }
  ]
}
```

PM 可补充代码未体现的角色（业务上存在但权限系统未区分），也可删除已废弃角色。

**用户确认**：角色列表完整吗？职责描述准确吗？权限边界有没有遗漏？

输出：`.allforai/product-map/role-profiles.json`

---

### Step 2：核心任务提取

按角色展开，从路由、菜单项、权限点提取任务，转换为业务语言。每个任务使用完整功能点描述模板：

```json
{
  "tasks": [
    {
      "id": "T001",
      "task_name": "创建并提交退款单",
      "value": "把退款申请从线下表格改为系统闭环，减少漏审与重复退款",
      "owner_role": "R001",
      "approver_role": "R002",
      "viewer_roles": ["R003"],
      "frequency": "高",
      "risk_level": "高",
      "cross_dept": true,
      "cross_dept_roles": ["财务", "仓储"],
      "sla": "24h 内处理",
      "prerequisites": ["已有订单", "有退款申请权限", "订单状态为已支付"],
      "main_flow": [
        "选择订单",
        "自动带出支付信息",
        "填写退款原因与金额",
        "校验（≤ 可退金额）",
        "提交 → 进入财务待审",
        "通知财务审核"
      ],
      "rules": [
        "同订单同原因 30 分钟内幂等，不重复创建",
        "金额变更需二次确认弹窗",
        "金额 ≥ 5000 触发主管复核流程"
      ],
      "inputs": {
        "fields": ["订单编号", "退款原因", "退款金额"],
        "defaults": { "退款金额": "原支付金额" }
      },
      "outputs": {
        "states": ["财务待审"],
        "messages": ["退款单已提交，财务将在 24h 内处理"],
        "records": ["退款单据"],
        "notifications": ["财务审核通知"]
      },
      "exceptions": [
        "订单已全额退款 → 提示不可重复退款",
        "支付信息缺失 → 提示联系技术支持",
        "权限不足 → 提示申请权限",
        "审批超时 48h → 自动升级到上级"
      ],
      "audit": {
        "recorded_actions": ["创建", "修改", "提交", "审批", "驳回"],
        "fields_logged": ["退款金额变更前后值", "退款原因", "操作人", "时间"]
      },
      "acceptance_criteria": [
        "超额退款不可提交并提示可退金额",
        "30 分钟内重复提交自动去重",
        "金额 ≥ 5000 触发复核流程",
        "操作日志包含变更前后值"
      ],
      "status": "confirmed",
      "flags": []
    }
  ]
}
```

**任务字段说明**：

| 字段 | 说明 |
|------|------|
| `task_name` | 动词 + 对象 + 结果（可操作动作，不用空词） |
| `value` | 解决什么问题/提升什么指标（一句话） |
| `owner_role` | 主操作角色 |
| `approver_role` | 审批角色（无审批流则省略） |
| `viewer_roles` | 只读角色列表 |
| `prerequisites` | 权限/数据状态/依赖配置前置条件 |
| `main_flow` | 3–8 步，写到"可操作"粒度 |
| `rules` | 校验、权限、状态流转、计算口径 |
| `inputs` | 输入字段和默认值 |
| `outputs` | 输出状态、消息、单据、通知 |
| `exceptions` | 失败提示/修复；撤回/幂等/重复提交；不可逆说明 |
| `audit` | 哪些操作被记录、记录哪些字段 |
| `acceptance_criteria` | 5–10 条可验证的验收标准 |

`status` 取值：`confirmed` / `user_added` / `user_removed`
`flags` 取值：`CONFLICT` / `CRUD_INCOMPLETE`（空表示无问题）

**用户确认**：任务清单完整吗？字段描述准确吗？有没有代码里没有但业务上需要的任务？

输出：`.allforai/product-map/task-inventory.json`

---

### Step 3：业务流建模

Step 2 完成后执行，所有模式均不可跳过。

#### 候选流自动识别

Claude 分析 `task-inventory.json`，寻找任务间的状态衔接关系：若任务 A 的 `outputs.states` 与任务 B 的 `prerequisites` 匹配，视为候选流节点对，自动组合成候选业务流，展示给用户确认。

#### 跨系统引用

若业务流涉及其他系统（如用户 App → 商户后台），用户可提供其他系统的 `task-inventory.json` 路径：

```
如果这条业务流涉及其他系统，请提供对应系统的 task-inventory 路径：
/path/to/other-system/.allforai/product-map/task-inventory.json
未提供时，跨系统节点标记为 gap_type: "UNVERIFIED"，不阻断流程。
```

`task_ref` 格式规则：

| 格式 | 含义 |
|------|------|
| `T001` | 当前系统的 T001 |
| `merchant-backend:T015` | merchant-backend 系统的 T015 |

#### 流级缺口类型

| Flag | 含义 |
|------|------|
| `MISSING_TASK` | 流节点引用的 task 在对应系统不存在 |
| `BROKEN_HANDOFF` | 节点间有 handoff，但下游 task 的 prerequisites 对不上 |
| `ORPHAN_TASK` | task 存在但没被任何流引用（独立功能或遗漏建模） |
| `MISSING_TERMINAL` | 流没有用户侧可感知的终止节点 |

#### 用户确认

展示候选流 + 识别到的缺口，用户可：
- 确认/修改候选流
- 补充未被识别的跨系统节点
- 标记孤立任务是否需要加入流

确认后写入 `business-flows.json` 和 `business-flows-report.md`。

#### `business-flows.json` Schema

```json
{
  "generated_at": "2026-02-25T10:00:00Z",
  "systems": {
    "current": "user-app",
    "linked": [
      {
        "name": "merchant-backend",
        "task_inventory_path": "/path/to/.allforai/product-map/task-inventory.json",
        "loaded": true
      }
    ]
  },
  "flows": [
    {
      "id": "F001",
      "name": "售后全链路",
      "description": "用户发起售后申请到最终处理完成的完整业务链路",
      "systems_involved": ["user-app", "merchant-backend"],
      "nodes": [
        {
          "seq": 1,
          "name": "用户发起售后申请",
          "task_ref": "user-app:T001",
          "role": "买家",
          "handoff": null,
          "gap": false
        },
        {
          "seq": 2,
          "name": "商户收到售后通知",
          "task_ref": "merchant-backend:T015",
          "role": "商户",
          "handoff": {
            "mechanism": "webhook",
            "data": ["售后单 ID", "买家 ID", "金额", "原因"]
          },
          "gap": false
        },
        {
          "seq": 3,
          "name": "商户处理售后申请",
          "task_ref": "merchant-backend:T016",
          "role": "商户",
          "handoff": null,
          "gap": false
        },
        {
          "seq": 4,
          "name": "用户查看处理结果",
          "task_ref": "user-app:T002",
          "role": "买家",
          "handoff": null,
          "gap": true,
          "gap_type": "MISSING_TASK",
          "gap_detail": "user-app task-inventory 中不存在 T002"
        }
      ],
      "gap_count": 1,
      "confirmed": false
    }
  ],
  "summary": {
    "flow_count": 2,
    "flow_gaps": 1,
    "orphan_tasks": ["T008"]
  }
}
```

#### `business-flows-report.md` 结构（摘要级）

```
# 业务流报告

2 条业务流 · 1 个流缺口 · 1 个孤立任务

## 业务流列表
- F001 售后全链路（user-app + merchant-backend）— 1 个缺口
- F002 订单支付链路（user-app）— 0 个缺口

## 流缺口
- F001 节点4：user-app:T002（用户查看处理结果）— MISSING_TASK

## 孤立任务（未被任何流引用）
- T008 批量导出订单 — 请确认是否需要加入某条流

> 完整数据见 .allforai/product-map/business-flows.json
```

输出：`.allforai/product-map/business-flows.json`、`.allforai/product-map/business-flows-report.md`

---

### Step 4：冲突 & 冗余检测

基于已确认的任务，**仅检测任务级问题**：

**任务级冲突（保留）**：
- 两个任务的 `rules` 或状态流转互相矛盾（业务冲突）
- `main_flow` 缺少必要操作类型（CRUD 缺口：有新增无查看、有创建无撤回等）

**界面级问题（不在此处检测，移至 screen-map）**：
- 同一操作在多个界面重复 → 由 screen-map 的 `REDUNDANT_ENTRY` flag 处理
- 高风险操作没有二次确认 → 由 screen-map 的 `HIGH_RISK_NO_CONFIRM` flag 处理

只标记，不修改，最终决定由用户做出。

```json
{
  "conflicts": [
    {
      "id": "C001",
      "type": "CONFLICT",
      "description": "T001 要求金额提交后不可修改，T003 退款编辑允许修改金额",
      "affected_tasks": ["T001", "T003"],
      "severity": "高",
      "confirmed": false
    }
  ],
  "crud_gaps": [
    {
      "id": "CG001",
      "type": "CRUD_INCOMPLETE",
      "description": "T001 main_flow 只有创建和提交，缺少撤回/修改流程",
      "affected_tasks": ["T001"],
      "severity": "中",
      "confirmed": false
    }
  ]
}
```

**用户确认**：检测结果有没有误报？哪些问题需要处理？

输出：`.allforai/product-map/conflict-report.json`

---

### Step 5：约束识别

识别两类约束：

**合规/审计要求**：操作留痕、数据可追溯、保留期限、导出需审批等

**业务约束**：不可逆操作、金额对账一致性、审批分级、SLA 硬限制等

```json
{
  "constraints": [
    {
      "id": "CN001",
      "type": "business",
      "description": "退款金额不可超过原订单金额",
      "affected_tasks": ["T001"],
      "enforcement": "hard",
      "confirmed": true
    },
    {
      "id": "CN002",
      "type": "compliance",
      "description": "所有退款操作必须留存操作日志，保留 3 年",
      "affected_tasks": ["T001", "T003"],
      "enforcement": "hard",
      "confirmed": true
    }
  ]
}
```

**用户确认**：约束识别完整吗？有没有遗漏的隐性规则？

输出：`.allforai/product-map/constraints.json`

---

### Step 6：输出产品地图报告

汇总前步骤的所有已确认数据，生成两个文件。

#### `product-map.json` — 结构化汇总（供下游技能加载）

```json
{
  "generated_at": "2026-02-24T10:00:00Z",
  "version": "2.1.0",
  "scope": "full",
  "summary": {
    "role_count": 3,
    "task_count": 24,
    "flow_count": 2,
    "flow_gaps": 1,
    "conflict_count": 1,
    "constraint_count": 5,
    "validation_issues": 5,
    "competitor_gaps": 3
  },
  "roles": [...],        // 来自 role-profiles.json
  "tasks": [...],        // 来自 task-inventory.json（使用新扩展 schema）
  "conflicts": [...],    // 来自 conflict-report.json（quick 模式为空数组）
  "constraints": [...]   // 来自 constraints.json（quick 模式为空数组）
}
```

`summary` 字段供下游技能（feature-gap、feature-prune、seed-forge）快速获取产品规模，无需遍历全部数组。

`feature-gap`、`feature-prune`、`seed-forge` 均以此文件为唯一输入，无需重新分析代码。

#### `product-map-report.md` — 可读摘要（给人看）

报告结构：

```
# 产品地图摘要

角色 X 个 · 任务 X 个 · 高频任务 X 个 · 冲突 X 个 · 约束 X 条

## 角色总览
| 角色 | 职责 | KPI |
|------|------|-----|
| （每角色一行） | | |

## 高频任务（Top 20%）
- T001 任务名（高频 / 高风险 / 跨部门）
- T005 任务名（高频 / 低风险）

## 冲突摘要
- C001 描述（高）

## 业务约束摘要
- CN001 描述（硬约束）

## 下一步建议
- 运行 /screen-map 梳理界面、按钮和异常状态（可选）
- 运行 /use-case 生成用例集（可选）
- 运行 /feature-gap 检测功能缺口
- 运行 /feature-prune 评估功能去留

> 完整数据见 .allforai/product-map/product-map.json
```

输出：`.allforai/product-map/product-map.json`、`.allforai/product-map/product-map-report.md`

---

### Step 7：校验

Step 6 完成后必须执行，所有模式均不可跳过。分三部分顺序执行，完成后统一展示，一次用户确认。

#### Part 1：完整性扫描

遍历 `task-inventory.json` 所有任务，逐项检查字段完整性：

| 检查项 | Flag |
|--------|------|
| `exceptions` 为空或缺失 | `MISSING_EXCEPTIONS` |
| `acceptance_criteria` 少于 3 条 | `THIN_AC` |
| `rules` 为空 | `MISSING_RULES` |
| 高频任务缺少 CRUD 中某类操作 | `HIGH_FREQ_CRUD_GAP` |
| `value` 字段缺失 | `MISSING_VALUE` |

#### Part 2：冲突重扫

基于完整地图重扫，比 Step 4 覆盖更广：

| 冲突类型 | Flag | 说明 |
|----------|------|------|
| 跨角色规则矛盾 | `CROSS_ROLE_CONFLICT` | A 角色的规则和 B 角色的规则互相冲突 |
| 状态流转死锁 | `STATE_DEADLOCK` | 任务 A 的输出状态被任务 B 的规则拒绝 |
| 幂等规则不一致 | `IDEMPOTENCY_CONFLICT` | 两个任务对同一对象的幂等规则不一致 |

#### Part 3：竞品差异（`competitors` 非空时执行）

Web 搜索加载各竞品功能概况，与完整任务清单做 diff，生成三列：

Web 搜索策略：优先访问竞品官方功能页、官方帮助文档目录，其次参考第三方对比评测。
对比粒度：以任务清单中的 task_name 为基准单位。
搜索失败处理：若某竞品数据无法获取，记录 `"data_source": "unavailable"`，不中断 Part 3，其余竞品继续分析。

| 列 | 含义 | 用户决策 |
|----|------|----------|
| `we_have_they_dont` | 我们有竞品没有 | 确认是否作为差异化保留 |
| `they_have_we_dont` | 竞品有我们没有 | 评估是否补齐 |
| `both_have_different_approach` | 都有但做法不同 | 确认设计分歧方向 |

Web 搜索完成后，将竞品功能数据补全到 `competitor-profile.json`，`analysis_status` 改为 `"completed"`。

#### 用户确认

三部分结果合并展示，用户确认：
- 哪些完整性问题是真实问题（vs 误报）
- 哪些冲突需要处理
- 哪些竞品差距需要跟进

确认后将结果写入 `validation-report.json` 和 `validation-report.md`。

#### `validation-report.json` Schema

```json
{
  "generated_at": "2026-02-24T12:00:00Z",
  "summary": {
    "completeness_issues": 3,
    "conflict_issues": 2,
    "competitor_gaps": 4
  },
  "completeness": [
    {
      "task_id": "T001",
      "task_name": "创建并提交退款单",
      "flags": ["THIN_AC"],
      "detail": "acceptance_criteria 只有 2 条，建议补充到 5 条以上",
      "confirmed": false
    }
  ],
  "conflicts": [
    {
      "id": "V001",
      "type": "CROSS_ROLE_CONFLICT",
      "description": "T001 规定退款金额提交后不可修改，T007（财务审核）允许审核时调整金额",
      "affected_tasks": ["T001", "T007"],
      "severity": "高",
      "confirmed": false
    }
  ],
  "competitor_diff": {
    "competitors_analyzed": ["Shopify", "有赞"],
    "we_have_they_dont": [
      {
        "feature": "退款单幂等去重",
        "our_task": "T001",
        "note": "差异化优势，建议保留",
        "confirmed": false,
        "decision": null
        // 有效值: "keep_as_differentiator"（保留为差异化优势）| "reconsider"（重新评估是否值得维护）
      }
    ],
    "they_have_we_dont": [
      {
        "feature": "批量退款",
        "competitor": "有赞",
        "note": "高频场景，建议评估是否补齐",
        "confirmed": false,
        "decision": null
        // 有效值: "add_to_backlog"（纳入待办，评估补齐）| "skip"（明确不做）
      }
    ],
    "both_have_different_approach": [
      {
        "feature": "审批流",
        "our_approach": "固定两级审批",
        "their_approach": "动态多级审批（有赞）",
        "note": "设计分歧，需确认方向",
        "confirmed": false,
        "decision": null
        // 有效值: "keep_current"（保持现有方案）| "adopt_competitor"（采纳竞品方案）| "custom"（另立方案）
      }
    ]
  }
}
```

#### `validation-report.md` 结构（摘要级，人类可读）

```
# 产品地图校验报告

校验问题 X 个（完整性 X / 冲突 X）· 竞品差距：竞品有我没有 X 个 / 我有竞品没有 X 个 / 做法不同 X 个

## 完整性问题
- T001 THIN_AC：acceptance_criteria 只有 2 条
- T005 MISSING_EXCEPTIONS：exceptions 为空

## 冲突问题
- V001 CROSS_ROLE_CONFLICT（高）：T001 vs T007，退款金额修改规则矛盾

## 竞品差异
### 竞品有我们没有（潜在缺口）
- 批量退款（有赞）— 高频场景，建议评估

### 我们有竞品没有（差异化）
- 退款单幂等去重 — 差异化优势，建议保留

### 做法不同（设计分歧）
- 审批流：我们固定两级 vs 有赞动态多级 — 需确认方向

> 完整数据见 .allforai/product-map/validation-report.json
```

输出：`.allforai/product-map/validation-report.json`、`.allforai/product-map/validation-report.md`、`.allforai/product-map/competitor-profile.json`（补全）

---

## 输出文件结构

```
.allforai/product-map/
├── role-profiles.json          # Step 1: 角色画像
├── task-inventory.json         # Step 2: 任务清单（完整功能点描述）
├── business-flows.json         # Step 3: 业务流（跨角色/跨系统链路）
├── business-flows-report.md    # Step 3: 业务流摘要（人类可读）
├── conflict-report.json        # Step 4: 任务级冲突检测结果
├── constraints.json            # Step 5: 业务约束清单
├── product-map.json            # Step 6: 汇总文件（供其他技能加载）
├── product-map-report.md       # Step 6: 可读报告
├── product-map-decisions.json  # 用户决策日志（增量复用）
├── competitor-profile.json       # Step 0 写草稿，Step 7 补全竞品功能数据
├── validation-report.json        # Step 7：三合一校验结果（机器可读）
└── validation-report.md          # Step 7：校验摘要（人类可读）
```

---

## 5 条铁律

### 1. 产品语言输出

输出全程使用业务语言，不出现接口地址、组件名、代码路径、前后端区分等工程术语。工程细节止于分析过程，不进入产品地图。

### 2. 角色为主线，任务必须完整

从"谁来用"出发，自顶向下展开。每个任务必须归属至少一个角色，且必须包含 `exceptions`（异常列表）和 `acceptance_criteria`（验收标准）——这是功能完整性的核心体现。不挂靠任何角色的任务标记为 `ORPHAN`，由用户决定去留。

### 3. 频次决定主次，任务分类驱动优先级

每个任务按 `frequency`（高/中/低）和 `risk_level`（高/中/低）分类。高频任务优先保证完整性，高风险任务优先保证约束和审计覆盖。频次和风险由代码中的操作分布和业务规则客观推导，PM 可调整但需说明理由。

### 4. 只标不改，用户是权威

检测到 `CONFLICT` / `CRUD_INCOMPLETE`，只标记报告，不执行任何修改，最终决定由用户做出。PM 补充的业务视角无条件纳入；代码里有但 PM 说不需要的任务，标记 `user_removed`，不强行保留。

### 5. 完整功能地图不依赖界面梳理

产品地图独立可运行，提供完整的功能语义：谁用、做什么、怎么做、有何异常、如何验收。`screen-map` 是可选增强层，梳理界面、按钮和异常状态；`feature-gap Step 2/3` 需要 screen-map 数据，但 `feature-gap Step 1`、`feature-prune`、`seed-forge` 可直接基于产品地图运行。

### 6. Step 7 校验不可跳过

Step 7 是地图质量保障，在所有模式（包括 `quick`）下必须执行。校验发现的问题只报告，由用户决定处理优先级；竞品差异只供参考，用户有权忽略。`validation-report.json` 中每条问题的 `confirmed` 字段记录用户决策，下次运行自动跳过已确认项。

### 7. Step 3 业务流建模不可跳过

Step 3 是链路完整性的基础，在所有模式（包括 `quick`）下必须执行。若当前系统没有任何跨角色或跨系统的业务链路，可以生成空流列表，但步骤本身必须执行以确认这一判断。

### 每步确认，增量复用

每个 Step 完成后展示摘要，等待用户确认后才进入下一步，不跳步不合并。用户确认结果写入 `product-map-decisions.json`，下次运行自动复用，不重复询问已确认项。`refresh` 命令才清空决策缓存重跑。
