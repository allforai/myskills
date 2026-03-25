# 业务流 Schema（business-flows.json）

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

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
      "name": "异常处理全链路",
      "description": "用户发起异常处理申请到最终处理完成的完整业务链路",
      "systems_involved": ["user-app", "merchant-backend"],
      "nodes": [
        {
          "seq": 1,
          "name": "用户发起异常处理申请",
          "task_ref": "user-app:T001",
          "role": "终端用户",
          "handoff": null,
          "gap": false
        },
        {
          "seq": 2,
          "name": "服务提供者收到异常处理通知",
          "task_ref": "merchant-backend:T015",
          "role": "服务提供者",
          "handoff": {
            "mechanism": "webhook",
            "data": ["工单 ID", "用户 ID", "金额", "原因"]
          },
          "gap": false
        }
      ],
      "gap_count": 0,
      "confirmed": false
    }
  ],
  "summary": {
    "flow_count": 2,
    "flow_gaps": 1,
    "orphan_tasks": ["T008"],
    "independent_operations": ["T025", "T030"]
  }
}
```

## `business-flows-report.md` 结构（摘要级）

```
# 业务流报告

2 条业务流 · 1 个流缺口 · 1 个孤立任务 · 2 个独立操作

## 业务流列表
- F001 异常处理全链路（user-app + merchant-backend）— 1 个缺口
- F002 工单提交链路（user-app）— 0 个缺口

## 流缺口
- F001 节点4：user-app:T002（用户查看处理结果）— MISSING_TASK

## 孤立任务（可能遗漏建模，需确认）
- T008 批量导出记录 — 请确认是否需要加入某条流

## 独立操作（无需纳入流）
- T025 管理收货地址
- T030 修改个人资料

> 完整数据见 .allforai/product-map/business-flows.json
```
