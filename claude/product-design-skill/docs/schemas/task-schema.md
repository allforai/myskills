# 任务 Schema（task-inventory.json）

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

**强制约束**：`tasks` 字段必须是**数组**（`[task, ...]`），不可使用 `{task_id: task}` 的 dict 格式。下游所有脚本（`_common.py`、`gen_experience_map.py` 等）均以数组格式为规范输入。

```json
{
  "tasks": [
    {
      "id": "T001",
      "name": "创建并提交撤销工单",
      "value": "把撤销申请从线下表格改为系统闭环，减少漏审与重复撤销",
      "owner_role": "R001",
      "approver_role": "R002",
      "viewer_roles": ["R003"],
      "frequency": "高",
      "risk_level": "高",
      "cross_dept": true,
      "cross_dept_roles": ["财务", "仓储"],
      "sla": "24h 内处理",
      "prerequisites": ["已有工单记录", "有撤销申请权限", "工单状态为已确认"],
      "main_flow": [
        "选择工单记录",
        "自动带出关联信息",
        "填写撤销原因与金额",
        "校验（≤ 可撤销金额）",
        "提交 → 进入财务待审",
        "通知财务审核"
      ],
      "rules": [
        "同工单同原因 30 分钟内幂等，不重复创建",
        "金额变更需二次确认弹窗",
        "金额 ≥ 5000 触发主管复核流程"
      ],
      "config_items": [
        {"param": "幂等窗口时长", "current": "30分钟", "config_level": "general_config"},
        {"param": "触发复核的金额阈值", "current": "5000", "config_level": "general_config"}
      ],
      "inputs": {
        "fields": ["工单编号", "撤销原因", "撤销金额"],
        "defaults": { "撤销金额": "原确认金额" }
      },
      "outputs": {
        "states": ["财务待审"],
        "messages": ["撤销工单已提交，财务将在 24h 内处理"],
        "records": ["撤销工单"],
        "notifications": ["财务审核通知"]
      },
      "exceptions": [
        "工单已全额撤销 → 提示不可重复撤销",
        "支付信息缺失 → 提示联系技术支持",
        "权限不足 → 提示申请权限",
        "审批超时 48h → 自动升级到上级"
      ],
      "audit": {
        "recorded_actions": ["创建", "修改", "提交", "审批", "驳回"],
        "fields_logged": ["撤销金额变更前后值", "撤销原因", "操作人", "时间"]
      },
      "acceptance_criteria": [
        "超额撤销不可提交并提示可撤销金额",
        "30 分钟内重复提交自动去重",
        "金额 ≥ 5000 触发复核流程",
        "操作日志包含变更前后值"
      ],
      "category": "basic",
      "status": "confirmed",
      "flags": []
    }
  ]
}
```

## 任务字段说明

| 字段 | 层级 | 说明 |
|------|------|------|
| `id` | required | 全局唯一任务标识（如 T001） |
| `name` | required | 动词 + 对象 + 结果（可操作动作，不用空词） |
| `owner_role` | required | 主操作角色 |
| `frequency` | required | 高/中/低 |
| `risk_level` | required | 高/中/低 |
| `main_flow` | required | 3–8 步，写到"可操作"粒度 |
| `status` | required | 任务状态：`confirmed` / `user_added` / `user_removed` |
| `category` | required | `basic`（基本功能）/ `core`（核心功能），见下方分类规则 |
| `value` | recommended | 解决什么问题/提升什么指标（一句话） |
| `approver_role` | recommended | 审批角色（无审批流则省略） |
| `viewer_roles` | recommended | 只读角色列表 |
| `cross_dept` | recommended | 是否跨部门（boolean） |
| `cross_dept_roles` | recommended | 跨部门涉及的角色列表 |
| `sla` | recommended | 服务等级目标时限 |
| `prerequisites` | recommended | 权限/数据状态/依赖配置前置条件 |
| `rules` | recommended | 校验、权限、状态流转、计算口径 |
| `config_items` | recommended | 可配置参数列表（见下方「配置级别」章节） |
| `inputs` | recommended | 输入字段和默认值 |
| `outputs` | recommended | 输出状态、消息、单据、通知 |
| `exceptions` | recommended | 失败提示/修复；撤回/幂等/重复提交；不可逆说明 |
| `audit` | recommended | 哪些操作被记录、记录哪些字段 |
| `acceptance_criteria` | recommended | 3–10 条可验证的验收标准 |
| `flags` | metadata | 问题标记：`CONFLICT` / `CRUD_INCOMPLETE`（空表示无问题） |
