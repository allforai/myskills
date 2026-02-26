# 信息保真方法论（提高维度 + 多视角）

> 目标：降低 `concept → map → screen → use-case → gap → prune → ui-design → audit` 的信息丢失与失真。

## 核心思想

信息从上游传到下游时，若只传「结论」，会不可避免地被压缩。为避免失真，统一采用两条原则：

1. **提高维度（4D）**：每条关键结论都携带上下文，而不是只有一句话结果。
2. **多视角（6V）**：同一对象至少从多个独立视角描述，避免单视角偏见。

---

## 一、4D 信息卡（提高维度）

每个关键对象（任务/界面/用例/决策）建议带 4 层信息：

- **D1 结论层**：是什么（结论本身）
- **D2 证据层**：基于什么（来源与事实）
- **D3 约束层**：边界是什么（业务/技术/合规）
- **D4 决策层**：为什么这么定（取舍与理由）

建议最小字段（跨阶段通用）：

```json
{
  "source_refs": ["来源URL或产物ID"],
  "assumptions": ["关键假设"],
  "constraints": {
    "business": ["..."],
    "technical": ["..."],
    "risk": ["..."]
  },
  "decision_rationale": "为什么这么定",
  "confidence": 0.0,
  "owner": "角色或负责人"
}
```

---

## 二、6V 视角矩阵（多视角）

建议统一 6 个视角（可按阶段裁剪）：

- `user`：用户价值
- `business`：业务价值
- `tech`：技术可行
- `ux`：体验可用
- `data`：可观测与指标
- `risk`：风险与合规

建议最小结构：

```json
{
  "viewpoints": {
    "user": {"success": "...", "risk": "...", "validation": "..."},
    "business": {"success": "...", "risk": "...", "validation": "..."},
    "tech": {"success": "...", "risk": "...", "validation": "..."},
    "ux": {"success": "...", "risk": "...", "validation": "..."},
    "data": {"success": "...", "risk": "...", "validation": "..."},
    "risk": {"success": "...", "risk": "...", "validation": "..."}
  }
}
```

---

## 三、在 8 阶段中的最小落地

- `product-concept`：结论外必须附带「证据 + 假设 + 反假设」。
- `product-map`：每个任务附 `decision_rationale` 与至少 4 个视角。
- `screen-map`：每个界面附「用户目标 + 失败恢复 + 风险提示」。
- `use-case`：每条用例补「业务成功 + 技术成功 + 体验成功」三重 then。
- `feature-gap`：缺口按视角分类（user/business/tech/ux/data/risk）。
- `feature-prune`：每个 `DEFER/CUT` 必须有替代路径和延迟成本说明。
- `ui-design`：每个关键界面保留设计决策理由与可访问性约束。
- `design-audit`：新增「追溯完整率 + 视角覆盖率」门禁。

---

## 四、推荐门禁指标

1. **Traceability 完整率**：下游对象能追溯到上游证据的比例，建议 `>= 95%`。
2. **Viewpoint 覆盖率**：关键对象覆盖至少 4/6 视角的比例，建议 `>= 90%`。

这两个指标可作为现有 ORPHAN / COVERAGE / CONFLICT 的补充门禁。
