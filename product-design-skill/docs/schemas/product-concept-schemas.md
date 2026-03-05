# 产品概念输出 JSON Schema

## 输出 JSON Schema

### `product-concept.json`

```json
{
  "version": "1.0.0",
  "mode": "forward | reverse",
  "mission": "一句话产品使命",
  "top_problems": [
    {
      "id": "P1",
      "description": "问题描述",
      "severity": "critical | high | medium",
      "current_alternatives": "用户现在怎么解决这个问题",
      "evidence": "搜索来源 URL"
    }
  ],
  "roles": [
    {
      "role_id": "R1",
      "role_name": "角色名",
      "role_type": "consumer | producer | admin",
      "impl_group": "end_user | operator | super_admin",
      "jobs": [{ "type": "functional | emotional | social", "description": "..." }],
      "pains": ["痛点1", "痛点2"],
      "gains": ["期望收益1", "期望收益2"],
      "pain_relievers": ["产品如何缓解痛点"],
      "gain_creators": ["产品如何创造收益"]
    }
  ],
  "business_model": {
    "revenue_streams": ["收入来源"],
    "cost_structure": ["成本结构"],
    "channels": ["获客渠道"],
    "key_metrics": ["关键指标"],
    "unfair_advantage": "不可复制优势"
  },
  "competitive_position": {
    "competitors": [
      { "name": "竞品名", "url": "来源", "strengths": ["..."], "weaknesses": ["..."] }
    ],
    "errc": {
      "eliminate": ["行业标配但我们不做的"],
      "reduce": [{ "item": "降低投入的", "kano": "must-have" }],
      "raise": [{ "item": "超出行业水平的", "kano": "performance" }],
      "create": [{ "item": "行业从未有过的", "kano": "delighter" }]
    }
  },
  "pipeline_preferences": {
    "ui_style": "material-design-3 | apple-hig | fluent-design | flat-minimal | glassmorphism | ant-design | shadcn-tailwind | undecided",
    "competitors": ["竞品A", "竞品B"],
    "scope_strategy": "aggressive | balanced | conservative | undecided",
    "stitch_ui": true | false | "undecided"
  },
  "frameworks_referenced": ["Lean Canvas", "VPC", "JTBD", "Blue Ocean ERRC", "Kano Model", "Opportunity Solution Tree", "First Principles", "Mom Test", "Build Trap / Product Kata"],
  "search_sources": ["搜索过程中参考的 URL"]
}
```

> `stitch_ui` — 是否在 ui-design 阶段调用 Google Stitch 生成视觉稿。`true` 需要 Google Cloud OAuth 认证（`npx -y @_davideast/stitch-mcp init`）。

### `problem-domain.json`（Step 0 输出）

```json
{
  "generated_at": "ISO timestamp",
  "user_input": "用户原始输入",
  "problem_essence": "第一性原理拆解出的问题本质",
  "problem_domain": "问题域描述",
  "top_problems": [
    {
      "id": "P1",
      "description": "问题描述",
      "severity": "critical | high | medium",
      "current_alternatives": "用户现在怎么解决这个问题",
      "evidence": "搜索来源 URL"
    }
  ],
  "competitors": [
    { "name": "竞品名", "url": "来源", "description": "简要描述", "key_features": ["..."] }
  ],
  "selected_traits": ["用户选中的差异化特征"],
  "unique_positioning": "基于竞品分析得出的差异化定位",
  "confirmed": false
}
```

### `role-value-map.json`（Step 1 输出）

```json
{
  "generated_at": "ISO timestamp",
  "roles": [
    {
      "role_id": "R1",
      "role_name": "角色名",
      "role_type": "consumer | producer | admin",
      "impl_group": "实现时归属的系统角色（如 'operator' / 'super_admin'）",
      "description": "角色简要描述（年龄段、典型特征等）",
      "jobs": [{ "type": "functional | emotional | social", "description": "..." }],
      "pains": ["痛点1", "痛点2"],
      "gains": ["期望收益1", "期望收益2"],
      "pain_relievers": ["产品如何缓解痛点"],
      "gain_creators": ["产品如何创造收益"]
    }
  ],
  "impl_groups": [
    {
      "group_id": "operator",
      "group_name": "运营后台用户",
      "concept_roles": ["R4", "R5", "R6"],
      "note": "共享一个后台界面，通过权限标签区分功能入口"
    }
  ],
  "confirmed": false
}
```

**字段说明**：
- `role_type`：`consumer`（消费侧）/ `producer`（生产侧）/ `admin`（管理侧）
- `impl_group`：实现时归属的系统角色。概念层按职责细分确保需求不遗漏，实现层按权限合并减少开发复杂度。消费侧角色通常 `impl_group` 为 `"end_user"`
- `impl_groups`：实现角色分组汇总，标注哪些概念角色共享一个后台

生产侧和管理侧角色的 VPC 可以简化：`pains`/`gains` 可省略，重点填写 `jobs`。

### `business-model.json`（Step 2 输出）

```json
{
  "generated_at": "ISO timestamp",
  "revenue_streams": ["收入来源"],
  "cost_structure": ["成本结构"],
  "channels": ["获客渠道"],
  "key_metrics": [
    {
      "metric": "指标名",
      "type": "outcome",
      "target": "目标值",
      "why": "为什么选这个指标"
    }
  ],
  "unfair_advantage": "不可复制优势",
  "build_trap_check": "Build Trap 审查结果：确认所有指标均为 outcome",
  "confirmed": false
}
```

### `product-mechanisms.json`（Step 3 输出）

```json
{
  "generated_at": "ISO timestamp",
  "mechanisms": [
    {
      "id": "MEC1",
      "module": "场景库",
      "decision_point": "内容生产方式",
      "chosen": "AI生成 + 人工审核",
      "alternatives_considered": ["纯人工编辑", "实时生成", "实时生成+缓存"],
      "impact": [
        "需要 AI 生成管线 + 审核队列",
        "R4（内容运营）职责变为审核为主、编辑为辅",
        "R5（AI 训练师）需要管理生成 prompt 质量"
      ],
      "evidence": "搜索来源 URL（可选）"
    }
  ],
  "confirmed": false
}
```

### `concept-decisions.json`（决策日志）

```json
[
  {
    "step": "Step 0",
    "item_id": "P1",
    "item_name": "描述",
    "decision": "confirmed | modified | deferred",
    "reason": "用户备注（可选）",
    "decided_at": "ISO timestamp"
  }
]
```
