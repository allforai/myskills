# 信息保真方法论（提高维度 + 多视角 + 跨模型）

> 目标：降低 `concept → map → screen → use-case → gap → prune → ui-design → audit` 的信息丢失与失真。

## 核心思想

信息从上游传到下游时，若只传「结论」，会不可避免地被压缩。为避免失真，统一采用三条原则：

1. **提高维度（4D）**：每条关键结论都携带上下文，而不是只有一句话结果。
2. **多视角（6V）**：同一对象至少从多个独立视角描述，避免单视角偏见。
3. **跨模型验证（XV）**：用不同 AI 模型交叉审视同一产物，弥补单一模型的知识偏差和推理盲区。

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

## 三、XV 跨模型验证

### 原理

4D 和 6V 提升了**单模型输出的信息密度**，但无法消除单一模型的系统性偏差 — 训练数据的知识偏向、推理路径的盲区、文化语境的局限。XV 通过引入第二个独立模型对关键产物进行审视，实现"换人看"效果：

- **知识互补**：不同模型在不同领域的训练深度各异，交叉验证可发现单模型遗漏的行业知识和边界条件。
- **推理多样性**：不同模型的推理风格（严谨/发散/结构化）可互相补充，降低单一推理路径的系统偏差。
- **置信度校准**：当两个模型对同一结论一致时，置信度提升；不一致时，暴露需要人工关注的争议点。

### 自动化策略

XV 验证完全自动、完全可选：

- **工具检测**：每个阶段在指定 Step 完成后，检测 `mcp__openrouter__ask_model` 工具是否可用。
- **可用时**：自动发起交叉验证调用，将结果写入产出的 `cross_model_review` 字段。不停下来询问用户。
- **不可用或调用失败时**：自动跳过，不阻塞流程，不生成 `cross_model_review` 字段。产出与未启用 XV 时完全一致。

### 调用方式

使用 `mcp__openrouter__ask_model` 工具，传入：

| 参数 | 说明 |
|------|------|
| `task_type` | 匹配 `defaults.ts` 中的路由键，自动选择模型（如 `competitive_analysis` → gemini） |
| `message` | 发送给验证模型的提示，包含当前阶段的关键产物摘要和验证问题 |

每阶段通常发起 2 次调用（不同 task_type），覆盖不同验证维度。

### 输出字段

验证结果统一写入产出 JSON 的顶层 `cross_model_review` 对象：

```json
{
  "cross_model_review": {
    "generated_at": "ISO timestamp",
    "reviews": [
      {
        "task_type": "competitive_analysis",
        "model_used": "gemini",
        "findings": ["发现1", "发现2"],
        "confidence": "high | medium | low"
      }
    ]
  }
}
```

---

## 四、在 8 阶段中的最小落地

- `product-concept`：结论外必须附带「证据 + 假设 + 反假设」。XV：Step 4 后由 gemini 挑战假设、gpt 验证用户画像。
- `product-map`：每个任务附 `decision_rationale` 与至少 4 个视角。XV：Step 5 后由 gemini 审查任务完整性、gpt 检测隐藏冲突。
- `screen-map`：每个界面附「用户目标 + 失败恢复 + 风险提示」。XV：Step 2 后由 gpt 审查 UX 一致性、gemini 检查无障碍缺陷。
- `use-case`：每条用例补「业务成功 + 技术成功 + 体验成功」三重 then。XV：Step 3 后由 deepseek 补充边界条件、gpt 审查验收标准。
- `feature-gap`：缺口按视角分类（user/business/tech/ux/data/risk）。XV：Step 4 后由 gemini 验证旅程断点、gpt 修正优先级。
- `feature-prune`：每个 `DEFER/CUT` 必须有替代路径和延迟成本说明。XV：Step 4 后由 deepseek 挑战误剪、gemini 补充竞品参照。
- `ui-design`：每个关键界面保留设计决策理由与可访问性约束。XV：Step 4 后由 gpt 审查视觉层级、gemini 检测一致性缺陷。
- `design-audit`：新增「追溯完整率 + 视角覆盖率」门禁。XV：Step 3 后由 gpt 验证跨层矛盾、deepseek 补充覆盖盲区。

---

## 五、推荐门禁指标

1. **Traceability 完整率**：下游对象能追溯到上游证据的比例，建议 `>= 95%`。
2. **Viewpoint 覆盖率**：关键对象覆盖至少 4/6 视角的比例，建议 `>= 90%`。

这两个指标可作为现有 ORPHAN / COVERAGE / CONFLICT 的补充门禁。
