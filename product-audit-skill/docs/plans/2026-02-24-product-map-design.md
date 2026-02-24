# product-map 技能设计文档

**日期**: 2026-02-24
**状态**: 已确认，待实现

---

## 背景与动机

`product-audit-skill` 现有 `feature-audit` 和 `feature-prune` 均从工程视角出发。缺少一个**产品经理视角**的基础层：这个产品有哪些用户？每个用户能做什么？做这些事时有什么约束？

`product-map` 是产品经理用来梳理、描述、确认自己产品全貌的工具。它输出的产品地图作为其他技能（`feature-audit`、`feature-prune`）的输入基准——"PM 期望的产品是什么样的"。

---

## 定位

```
product-map（现状+方向）      feature-audit（对齐视角）    feature-prune（决策视角）
项目现在有什么？应该有什么？   代码做没做？                 该不该做？
代码读现状，PM 定方向          以 product-map 为基准        以 product-map 为锚点
输出产品地图（PM语言呈现）     输出差距报告                 输出剪枝报告
```

**核心定位**：读代码了解现状，用 PM 语言呈现，让 PM 确认并补充业务视角，最终形成"现状 + 期望"的完整产品地图，用于指导项目未来发展方向。

输出全程使用业务语言，不出现接口地址、组件名等工程术语。

---

## 输入来源（双输入）

两类输入并行，相互补充：

| 类型 | 来源 | 说明 |
|------|------|------|
| 工程输入 | 代码（路由、菜单、权限配置、页面组件） | 了解项目现状，提取已有功能点 |
| 产品输入 | PRD、用户故事、原型图描述、PM 口述 | 补充业务语义，确认方向，标记差距 |

代码告诉我们**现在有什么**，PM 确认**应该有什么**。两者的差距就是需要改进的方向。

---

## 核心数据结构

```
角色（Role）
 └── 任务（Task）          ← 用户能做什么，说到底是增删改查
       └── 界面（Screen）  ← 在哪个页面做
             └── 按钮（Action）  ← 具体操作入口，C/R/U/D 分类
```

每个任务归属于角色，每个任务对应一或多个界面，每个界面上有若干按钮。按钮是最小粒度，CRUD 是否完整是功能点是否完整的直接判断依据。

---

## 工作流

```
Step 0: 项目画像
    从代码提取技术栈、路由结构、权限系统、菜单配置
    转换为产品语言：有哪些功能模块、有哪些用户角色
    → 用户确认画像是否准确
    ↓
Step 1: 用户角色识别
    从代码推导角色（权限枚举、守卫、角色配置）→ 转换为 PM 语言描述
    每角色：角色名 / 职责描述 / 权限边界 / KPI
    PM 可补充代码未体现的角色、删除已废弃的角色
    → 用户确认/补充/删除
    ↓
Step 2: 核心任务提取（按角色展开）
    从代码提取每个角色的操作（路由、菜单项、权限点）→ 转换为业务任务描述
    每条任务结构：
      task_name / owner_role / trigger / frequency / risk_level
      cross_dept / cross_dept_roles / sla / success_criteria / exceptions
    PM 可补充代码没有的任务（期望方向）、标记代码有但业务不需要的任务
    → 用户确认任务清单，可补充遗漏 / 标记多余 / 标记冲突
    ↓
Step 3: 界面与按钮梳理（按任务展开）
    从代码提取页面和操作按钮 → 转换为产品语言描述
    每个界面：
      名称 / 核心目的（这个页面最重要的事）/ 进入路径
    每个按钮：按钮文字 / CRUD 类型 / 可操作角色 / 是否需要二次确认 / 操作频次
    帕累托分析：
      按频次排序所有按钮，找出前 20% 高频操作
      高频操作自动成为 primary_action 候选
      检测高频操作的可达性：需要几步才能触发？是否被埋在次级菜单？
    PM 可标注：调整频次评估、标记操作层级是否合理、标记多余按钮
    → 用户确认，可补充遗漏按钮 / 标记多余按钮
    ↓
Step 4: 冲突 & 冗余检测
    基于已确认的任务和按钮，分析：
      - 同一操作在多个界面重复（冗余入口）
      - 高风险操作没有二次确认（安全缺口）
      - 两个任务的业务逻辑互相矛盾（业务冲突）
      - CRUD 不完整（有新增无删除、有列表无详情等）
    → 用户确认，排除误报
    ↓
Step 5: 约束识别
    合规/审计要求（留痕、可追溯、保留期限、导出审批）
    业务约束（不可逆操作、金额对账一致性、审批分级）
    → 用户确认
    ↓
Step 6: 输出产品地图报告
```

**核心原则：每个 Step 结束都有用户确认，用户是权威。**

---

## 输出文件结构

```
your-project/
└── .product-map/
    ├── role-profiles.json         # Step 1: 角色画像
    ├── task-inventory.json        # Step 2: 任务清单
    ├── screen-map.json            # Step 3: 界面地图（含按钮）+ 反查索引
    ├── conflict-report.json       # Step 4: 冲突&冗余检测结果
    ├── constraints.json           # Step 5: 约束清单
    ├── product-map.json           # 汇总：供 feature-audit / feature-prune 加载
    ├── product-map-report.md      # 可读报告（给人看）
    └── product-map-decisions.json # 用户决策日志（增量运行复用）
```

---

### `role-profiles.json`

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

---

### `task-inventory.json`

```json
{
  "tasks": [
    {
      "id": "T001",
      "task_name": "创建退款单",
      "owner_role": "R001",
      "trigger": "客户申请退款",
      "frequency": "高",
      "risk_level": "高",
      "cross_dept": true,
      "cross_dept_roles": ["财务", "仓储"],
      "sla": "2h 内处理",
      "success_criteria": "退款单已提交，财务收到通知",
      "exceptions": ["重复退款单", "金额超限需上级审批", "商品已销毁"],
      "status": "confirmed",
      "flags": []
    }
  ]
}
```

`status` 取值：`confirmed` / `user_added` / `user_removed`
`flags` 取值：`CONFLICT` / `REDUNDANT`（空表示无问题）

---

### `screen-map.json`

```json
{
  "screens": [
    {
      "id": "S001",
      "name": "退款申请页",
      "description": "客服填写退款原因、金额，提交退款申请",
      "primary_purpose": "让客服快速、准确地提交退款申请",
      "primary_action": "提交退款申请",
      "entry_point": "订单详情页 → 申请退款按钮",
      "tasks": ["T001"],
      "actions": [
        {
          "label": "提交退款申请",
          "crud": "C",
          "frequency": "高",
          "click_depth": 1,
          "is_primary": true,
          "roles": ["R001"],
          "requires_confirm": false
        },
        {
          "label": "撤回退款",
          "crud": "D",
          "frequency": "低",
          "click_depth": 2,
          "is_primary": false,
          "roles": ["R001", "R002"],
          "requires_confirm": true
        }
      ],
      "pareto": {
        "high_freq_actions": ["提交退款申请"],
        "low_freq_buried": [],
        "high_freq_buried": []
      },
      "flags": []
    },
    {
      "id": "S002",
      "name": "数据总览页",
      "description": "展示核心业务指标、待处理任务数、异常告警",
      "primary_purpose": "让管理者在 30 秒内判断业务是否健康",
      "primary_action": "查看核心指标",
      "entry_point": "登录后默认首页",
      "tasks": ["T002", "T003", "T004", "T005", "T006", "T007"],
      "actions": [
        { "label": "导出报表", "crud": "R", "frequency": "低", "click_depth": 1, "is_primary": false, "roles": ["R002"], "requires_confirm": false },
        { "label": "标记已读", "crud": "U", "frequency": "高", "click_depth": 3, "is_primary": false, "roles": ["R001", "R002"], "requires_confirm": false }
      ],
      "pareto": {
        "high_freq_actions": ["标记已读"],
        "low_freq_buried": [],
        "high_freq_buried": ["标记已读"]
      },
      "flags": ["OVERLOADED", "HIGH_FREQ_BURIED"]
    }
  ],
  "summary": {
    "total_screens": 24,
    "orphan_screens": 2,
    "overloaded_screens": 1,
    "action_issues": {
      "incomplete_crud": 4,
      "high_risk_no_confirm": 2
    }
  }
}
```

**界面核心字段说明**：

| 字段 | 含义 |
|------|------|
| `primary_purpose` | 这个页面最重要的目标是什么（一句话，用户视角） |
| `primary_action` | 页面上最核心的操作，视觉上应该最突出 |

**界面核心字段说明**：

| 字段 | 含义 |
|------|------|
| `primary_purpose` | 这个页面最重要的目标（用户视角一句话） |
| `primary_action` | 频次最高的操作，由帕累托分析自动推导，PM 可调整 |

**`actions` 字段说明**：

| 字段 | 含义 |
|------|------|
| `label` | 按钮文字（界面上显示的） |
| `crud` | `C` 新增 / `R` 查看 / `U` 修改 / `D` 删除 |
| `frequency` | 操作频次：高 / 中 / 低（PM 评估或从埋点数据推导） |
| `click_depth` | 触达该按钮需要几次点击（1=直接可见，2=需要展开，3+=深度隐藏） |
| `is_primary` | 由频次自动推导（`frequency=高` 且 `click_depth=1` 的操作），PM 可覆盖 |
| `roles` | 哪些角色可见/可操作此按钮 |
| `requires_confirm` | 是否需要二次确认弹窗 |

**`pareto` 分析字段**：

| 字段 | 含义 |
|------|------|
| `high_freq_actions` | 该页面频次为"高"的所有操作 |
| `high_freq_buried` | 高频但 `click_depth >= 2` 的操作（需要优化） |
| `low_freq_buried` | 低频且被埋深的操作（合理，无需处理） |

**`flags` 取值**：

| 标记 | 含义 |
|------|------|
| `OVERLOADED` | 单页任务数超过阈值（默认 5），职责过重 |
| `HIGH_FREQ_BURIED` | 高频操作被埋在次级菜单，用户需多次点击才能触达 |
| `PRIMARY_MISMATCH` | `primary_action` 不是频次最高的操作，主次不符 |
| `ORPHAN` | 没有任何任务关联，疑似废弃页面 |
| `NO_ENTRY` | 没有任何其他页面指向此页（孤立入口） |

**帕累托衍生检测**：

| 检测 | 逻辑 | 意义 |
|------|------|------|
| 高频操作可达性 | `frequency=高` + `click_depth >= 2` → `HIGH_FREQ_BURIED` | 用户最常做的事不应被埋深 |
| 主操作频次一致性 | `primary_action` 不是频次最高的操作 → `PRIMARY_MISMATCH` | 主操作应由频次决定，不靠感觉 |
| CRUD 完整性 | 同一任务的按钮是否覆盖了所有必要操作 | 功能是否完整 |
| 高风险无确认 | `task.risk_level=高` + `action.requires_confirm=false` | 操作安全性 |

---

### `conflict-report.json`

```json
{
  "conflicts": [
    {
      "id": "C001",
      "type": "CONFLICT",
      "tasks": ["T001", "T003"],
      "description": "T001 创建退款单要求金额提交后不可修改，T003 退款单编辑允许修改金额",
      "severity": "高",
      "confirmed": false
    }
  ],
  "redundancies": [
    {
      "id": "RD001",
      "type": "REDUNDANT",
      "screens": ["S005", "S009"],
      "description": "两个页面均有'标记订单完成'按钮，业务逻辑相同，入口不同",
      "confirmed": false
    }
  ]
}
```

---

## 命令设计

```bash
/product-map              # 完整流程（Step 0-6）
/product-map quick        # 跳过冲突检测（Step 4）和约束识别（Step 5）
/product-map refresh      # 重新采集，忽略已有缓存
/product-map scope 退款管理  # 只梳理指定功能模块
```

---

## 与现有技能的集成

`product-map` 输出 PM 对产品的期望描述。`feature-audit` 和 `feature-prune` 以此为基准，与代码实现做对比。

### feature-audit 加载逻辑

```
if .product-map/product-map.json exists:
    以 PM 定义的任务清单为"计划功能"基准
    跳过从代码推导功能清单的步骤
    提示用户："检测到 product-map（生成于 XX），以 PM 定义为基准"
else:
    执行原有流程（从 PRD/代码推导）
```

### feature-prune 加载逻辑

```
if .product-map/product-map.json exists:
    直接加载角色、任务、场景数据，跳过 Step 0-1
    提示用户："检测到 product-map（生成于 XX），从 Step 2 开始"
else:
    执行原有 Step 0-1 流程
```

---

## 5 条铁律

### 1. 代码读现状，产品语言呈现

从代码提取现状，但所有输出字段使用业务语言。不出现接口地址、组件名、代码路径、前后端区分。工程细节止于分析过程，不进入产品地图。

### 2. 角色为主线

从"谁来用"出发。每个任务必须归属至少一个角色，每个界面必须关联至少一个任务。

### 3. 频次决定主次，二八原则驱动界面判断

每个功能点最终落到按钮（Action）。主操作由频次客观推导，不靠感觉：`frequency=高` 且 `click_depth=1` 的操作自动成为 `primary_action` 候选，PM 可调整但需说明理由。

高频操作被埋深（`click_depth >= 2`）是界面问题的直接信号——用户最常做的事应该最容易触达。CRUD 是否完整是功能是否完整的直接标准。

### 4. 只标不改

检测到 CONFLICT / REDUNDANT / OVERLOADED，只标记报告，不执行任何修改，最终决定由用户做出。

### 5. 增量友好

`product-map-decisions.json` 持久化用户确认结果，`refresh` 命令才清空重跑。

---

## 新增文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `skills/product-map.md` | 技能文件 | 主技能描述、工作流、铁律 |
| `commands/product-map.md` | 命令文件 | `/product-map` 命令入口 |
| `docs/product-map/overview.md` | 文档 | 技能总览 |
| `docs/product-map/roles.md` | 文档 | Step 1 角色识别详细说明 |
| `docs/product-map/tasks.md` | 文档 | Step 2 任务提取详细说明 |
| `docs/product-map/screens.md` | 文档 | Step 3 界面与按钮梳理详细说明 |
| `docs/product-map/conflicts.md` | 文档 | Step 4 冲突检测详细说明 |
| `docs/product-map/constraints.md` | 文档 | Step 5 约束识别详细说明 |
| `docs/product-map/report.md` | 文档 | Step 6 报告生成详细说明 |
| `examples/role-profiles.json` | 示例 | 角色画像示例 |
| `examples/task-inventory.json` | 示例 | 任务清单示例 |
| `examples/screen-map.json` | 示例 | 界面地图示例（含按钮） |
| `examples/conflict-report.json` | 示例 | 冲突报告示例 |
| `examples/product-map.json` | 示例 | 完整汇总输出示例 |

## 修改文件清单

| 文件 | 修改说明 |
|------|------|
| `skills/feature-audit.md` | Step 0 增加 product-map 检测和加载逻辑 |
| `skills/feature-prune.md` | Step 0-1 增加 product-map 检测和加载逻辑 |
| `SKILL.md` | 更新技能列表，加入 product-map |
| `README.md` | 更新文档，加入 product-map 说明 |
| `.claude-plugin/plugin.json` | 注册新技能和命令 |
