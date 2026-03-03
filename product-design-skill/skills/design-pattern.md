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
