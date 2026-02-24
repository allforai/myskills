# product-map 业务流层 设计文档

**日期**：2026-02-25
**版本影响**：v2.3.0 → v2.4.0

---

## 背景

当前 product-map 以角色为中心展开任务，缺少跨角色、跨系统的业务链路视角。典型场景：用户在 App 申请售后 → 商户后台收到并处理 → 用户 App 看到结果。这条链路横跨两个独立系统，现有数据模型无法显式表达，导致：

1. 完整性校验只能在单任务粒度进行，无法发现链路断点
2. 测试用例只有单角色视角，缺少端到端场景
3. 需求评审时看不到跨系统的依赖关系

---

## 设计目标

- 在 task-inventory 之上新增「业务流」组合层，把跨角色/跨系统的 tasks 串成链路
- 支持跨 product-map 运行引用（`系统名:task_id` 格式）
- 流节点自动检测缺口，为下游完整性校验和测试用例生成提供链路视角
- 不破坏现有 task-inventory 结构，流是组合层而非替代层

---

## 核心概念

### 业务流 vs 任务

```
task-inventory（单系统、单角色）     business-flows（跨系统、跨角色）
─────────────────────────────        ─────────────────────────────────
T001  用户申请售后      [user-app]    F001  售后全链路
T015  商户收到通知  [merchant-backend]      节点1 → user-app:T001
T016  商户处理售后  [merchant-backend]      节点2 → merchant-backend:T015
T002  用户查看结果      [user-app]          节点3 → merchant-backend:T016
                                            节点4 → user-app:T002（缺口）
```

tasks 是原子操作，flows 是业务链路。两者通过 `task_ref` 关联，tasks 不变。

---

## 数据模型

### `business-flows.json` Schema

```json
{
  "generated_at": "2026-02-25T10:00:00Z",
  "systems": {
    "current": "user-app",
    "linked": [
      {
        "name": "merchant-backend",
        "task_inventory_path": "/path/to/merchant-app/.allforai/product-map/task-inventory.json",
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
    "flow_count": 3,
    "flow_gaps": 2,
    "orphan_tasks": ["T008", "T012"]
  }
}
```

### `task_ref` 格式规则

| 格式 | 含义 |
|------|------|
| `T001` | 当前系统的 T001 |
| `user-app:T001` | user-app 系统的 T001 |
| `merchant-backend:T015` | merchant-backend 系统的 T015 |

---

## 流级缺口类型

| Flag | 含义 |
|------|------|
| `MISSING_TASK` | 流节点引用的 task 在对应系统不存在 |
| `BROKEN_HANDOFF` | 节点间有 handoff，但下游 task 的 prerequisites 对不上 |
| `ORPHAN_TASK` | task 存在但没被任何流引用 |
| `MISSING_TERMINAL` | 流没有终止节点（用户侧无最终可见结果） |

---

## 工作流变更

### 新流程

```
full:   Step 0 → Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6 → Step 7
quick:  Step 0 → Step 1 → Step 2 → Step 3 → Step 6 → Step 7
```

Step 3 在所有模式下必须执行（与 Step 7 同级强制）。

### Step 3：业务流建模（新增）

Step 2 完成后执行。

**执行过程：**

1. 加载本系统 `task-inventory.json`
2. 若用户提供其他系统的 `task-inventory` 路径，一并加载（用于验证跨系统 task_ref）
3. Claude 自动识别候选流：基于 `outputs.states` ↔ `prerequisites` 关联，发现潜在的任务链
4. 展示候选流 + 识别到的缺口，用户确认/修改/补充
5. 用户确认后写入 `business-flows.json` 和 `business-flows-report.md`

**跨系统引用说明（对用户）：**

```
如果这个系统的业务流涉及其他系统，请提供对应系统的 task-inventory 路径，例如：
/path/to/merchant-app/.allforai/product-map/task-inventory.json
未提供时，跨系统节点的 task_ref 标记为 gap_type: UNVERIFIED。
```

---

## `business-flows-report.md` 结构（摘要级）

```
# 业务流报告

3 条业务流 · 2 个流缺口 · 2 个孤立任务

## 业务流列表
- F001 售后全链路（user-app + merchant-backend）— 1 个缺口
- F002 订单支付链路（user-app + payment-service）— 0 个缺口
- F003 商品上架审核（merchant-backend + admin）— 1 个缺口

## 流缺口
- F001 节点4：user-app:T002（用户查看处理结果）— MISSING_TASK
- F003 节点2：admin:T009（平台审核商品）— MISSING_TASK

## 孤立任务（未被任何流引用）
- T008 批量导出订单 — 独立功能或遗漏建模？
- T012 系统通知设置 — 独立功能或遗漏建模？

> 完整数据见 .allforai/product-map/business-flows.json
```

---

## 对下游技能的影响

### feature-gap 新增：链路完整性检查

- 读取 `business-flows.json`，沿每条流检查节点是否都有对应完整 task
- 新增 flag：`ORPHAN_TASK`（task 存在但不在任何流中）、`MISSING_TERMINAL`

### use-case 新增：端到端用例

- 沿流生成跨角色/跨系统的 E2E 用例
- 示例：

```
E2E-F001-01  售后全链路_正常流
  Given 用户有已完成订单
  When  用户提交售后申请（user-app:T001）
  And   商户收到通知并处理（merchant-backend:T015 → T016）
  Then  用户在 App 看到处理结果（user-app:T002）
```

### product-map.json summary 新增字段

```json
"summary": {
  "role_count": 3,
  "task_count": 24,
  "flow_count": 3,
  "flow_gaps": 2,
  "conflict_count": 1,
  "constraint_count": 5,
  "validation_issues": 5,
  "competitor_gaps": 3
}
```

---

## 输出文件变更

### 新增文件

```
.allforai/product-map/
├── business-flows.json       # Step 3：业务流（机器可读）
└── business-flows-report.md  # Step 3：业务流摘要（人类可读）
```

---

## 版本说明

- 版本：v2.3.0 → v2.4.0
- Breaking change：`product-map.json` summary 新增 `flow_count`、`flow_gaps` 字段（向后兼容）
- 新增输出文件：`business-flows.json`、`business-flows-report.md`
- 下游技能（feature-gap、use-case）按需读取，不强制依赖
