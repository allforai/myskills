# 校验报告 Schema（validation-report.json）

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "generated_at": "2026-02-24T12:00:00Z",
  "summary": {
    "error_issues": 0,
    "warning_issues": 3,
    "info_issues": 15,
    "conflict_issues": 2,
    "competitor_gaps": 4
  },
  "completeness": [
    {
      "task_id": "T001",
      "name": "创建并提交撤销工单",
      "level": "WARNING",
      "flags": ["THIN_AC"],
      "detail": "acceptance_criteria 只有 2 条，建议补充到 3 条以上",
      "confirmed": false
    }
  ],
  "conflicts": [
    {
      "id": "V001",
      "type": "CROSS_ROLE_CONFLICT",
      "description": "T001 规定撤销金额提交后不可修改，T007（财务审核）允许审核时调整金额",
      "affected_tasks": ["T001", "T007"],
      "severity": "高",
      "confirmed": false
    }
  ],
  "competitor_diff": {
    "comparison_scope": "platform_features",
    "competitors_analyzed": ["竞品A", "竞品B"],
    "we_have_they_dont": [
      {
        "feature": "撤销工单幂等去重",
        "our_task": "T001",
        "note": "差异化优势，建议保留",
        "confirmed": false,
        "decision": null
      }
    ],
    "they_have_we_dont": [
      {
        "feature": "批量撤销",
        "competitor": "竞品B",
        "note": "高频场景，建议评估是否补齐",
        "confirmed": false,
        "decision": null
      }
    ],
    "both_have_different_approach": [
      {
        "feature": "审批流",
        "our_approach": "固定两级审批",
        "their_approach": "动态多级审批（竞品B）",
        "note": "设计分歧，需确认方向",
        "confirmed": false,
        "decision": null
      }
    ]
  }
}
```

**decision 有效值**：
- `we_have_they_dont`: `"keep_as_differentiator"` | `"reconsider"`
- `they_have_we_dont`: `"add_to_backlog"` | `"skip"`
- `both_have_different_approach`: `"keep_current"` | `"adopt_competitor"` | `"custom"`

## `validation-report.md` 结构（摘要级，人类可读）

```
# 产品地图校验报告

ERROR X 个 · WARNING X 个 · INFO X 个（统计） · 冲突 X 个
竞品差距：竞品有我没有 X 个 / 我有竞品没有 X 个 / 做法不同 X 个

## ERROR 级问题（必须修复）
（无则显示「无 ERROR 级问题」）

## WARNING 级问题（建议修复）
- T001 THIN_AC：acceptance_criteria 只有 2 条
- T005 MISSING_EXCEPTIONS：exceptions 为空

## INFO 统计
- 另有 X 个中低频任务缺少 exceptions
- 另有 X 个中低频任务缺少 value

## 冲突问题
- V001 CROSS_ROLE_CONFLICT（高）：T001 vs T007，撤销金额修改规则矛盾

## 竞品差异（对比维度：{comparison_scope}）
### 竞品有我们没有（潜在缺口）
- 批量撤销（竞品B）— 高频场景，建议评估

### 我们有竞品没有（差异化）
- 撤销工单幂等去重 — 差异化优势，建议保留

### 做法不同（设计分歧）
- 审批流：我们固定两级 vs 竞品B动态多级 — 需确认方向

> 完整数据见 .allforai/product-map/validation-report.json
```
