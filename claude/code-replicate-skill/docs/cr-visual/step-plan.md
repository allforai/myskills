# Step 0: 任务规划

> 本文档由 cr-visual orchestrator 派遣的 **plan agent** 加载。
> 职责：基于截图 + 源码 + interaction-recordings，生成细粒度任务清单。
> **本 agent 不执行任何对比/修复**，只负责规划。

## 输入

- `screens[]`（来自 capture agent 的截图路径映射）
- `experience-map.json`（screen 定义 + components + actions）
- `interaction-recordings.json`（如有 — 提取 linkage_verify 步骤）
- 目标项目源码路径（用于扫描数据绑定控件）

## 规划协议

对每个 screen，执行以下 3 步枚举：

### 1. 结构任务（始终创建）

每个 screen 固定一个 structural subtask：

```json
{"type": "structural", "screen": "订单管理", "status": "pending"}
```

### 2. 数据完整性任务（逐控件枚举）

LLM 读目标项目中该 screen 对应的页面/组件源码，找出所有数据绑定控件：

```
扫描方式：
1. 读页面组件源码 → 找所有含数据绑定的控件标签
   - Table/DataGrid/List/Tree → 绑定了 :data / :items / :rows 等
   - ComboBox/Select/Dropdown → 绑定了 :options / :items
   - Label/Badge/Counter → 绑定了 {{ variable }} 或 :text
   - Chart/Graph → 绑定了 :data / :series
2. 每个绑定控件 = 一个 subtask
3. 记录控件类型 + 在页面中的位置描述 + 数据源（变量名/API）
```

输出：
```json
{
  "type": "data_integrity",
  "screen": "订单管理",
  "control_type": "DataGrid",
  "control_id": "订单列表",
  "data_source": "orders (from GET /api/orders)",
  "status": "pending"
}
```

**无数据绑定控件的 screen → 不创建 data_integrity subtask**（节省 agent 派遣）。

### 3. 联动任务（逐联动对枚举）

从 `interaction-recordings.json` 提取该 screen 相关的 `linkage_verify` 步骤：

```
每个 linkage_verify 中的每个 expected_effect = 一个 subtask
```

如果 interaction-recordings 不存在或该 screen 无 linkage_verify → 额外扫描源码：

```
补充扫描（降级模式）：
1. 读页面组件源码 → 找 onChange/onSelect/onCheck 等事件处理
2. 事件处理内部是否修改了其他控件的数据/状态？
3. 是 → 创建 linkage subtask（标记 source: "code_scan" 而非 "interaction_recordings"）
```

输出：
```json
{
  "type": "linkage",
  "screen": "订单管理",
  "trigger_control": "状态筛选 ComboBox",
  "target_control": "订单列表 DataGrid",
  "effect_type": "data_filter",
  "source": "interaction_recordings | code_scan",
  "status": "pending"
}
```

**无联动关系的 screen → 不创建 linkage subtask**。

## 输出

写入 `.allforai/code-replicate/visual-task-plan.json`：

```json
{
  "planned_at": "ISO8601",
  "summary": {
    "total_screens": 20,
    "total_subtasks": 67,
    "by_type": {
      "structural": 20,
      "data_integrity": 35,
      "linkage": 12
    },
    "screens_with_no_data_controls": ["登录页", "关于页"],
    "screens_with_no_linkage": ["用户列表", "设置页"]
  },
  "tasks": [
    {
      "screen": "订单管理",
      "subtasks": [
        {"id": "VT-001-S", "type": "structural", "status": "pending"},
        {"id": "VT-001-D1", "type": "data_integrity", "control_type": "DataGrid", "control_id": "订单列表", "data_source": "GET /api/orders", "status": "pending"},
        {"id": "VT-001-D2", "type": "data_integrity", "control_type": "ComboBox", "control_id": "状态筛选", "data_source": "GET /api/order-statuses", "status": "pending"},
        {"id": "VT-001-D3", "type": "data_integrity", "control_type": "Label", "control_id": "总金额", "data_source": "computed: sum(orders.amount)", "status": "pending"},
        {"id": "VT-001-L1", "type": "linkage", "trigger_control": "状态筛选", "target_control": "订单列表", "effect_type": "data_filter", "status": "pending"}
      ]
    }
  ]
}
```

## 规划完成后

orchestrator 读取 visual-task-plan.json：
1. 展示任务摘要给用户（`总共 20 screens, 67 subtasks: 20 结构 + 35 数据完整性 + 12 联动`）
2. 按 subtask 类型分组派遣 agent
3. 每个 agent 完成后更新对应 subtask 的 status → completed / failed / skipped
4. 最终验收：检查是否有 pending 的 subtask → 有则补执行
