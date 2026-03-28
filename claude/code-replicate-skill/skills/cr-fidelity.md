---
name: cr-fidelity
description: >
  Use when user wants to "verify replication fidelity", "还原度验证", "检查复刻质量",
  "compare source vs target", "fidelity check", "复刻对比", "还原度不够",
  "check if migration is complete", or mentions verifying that target code
  faithfully reproduces source code behavior after code-replicate + dev-forge.
---

# 还原度验证 — CR Fidelity v2.0

> 源码 vs 目标代码的还原度闭环验证。自适应维度 — 有什么产物就验什么。

> **编码规范**：所有产物文件 UTF-8 写入，JSON `ensure_ascii=False`。读取已有产物发现乱码（鈥/瀹/鐢）先清洗再写回。

## 流程

| 阶段 | 名称 | 说明 |
|------|------|------|
| 0 | 准备 | 构建追溯索引 + 自适应维度选择 |
| A | 静态分析 | 按选中维度逐一评分 |
| A2 | 运行时验证 | 构建 → 冒烟 → 测试向量 → 协议兼容 |
| B | 修复 | 按差距清单修复（运行时优先） |
| C | 重测 | 重新评分，不达标回到 B |

`full` = 0 → A → A2 → B → C 闭环（最多 3 轮）
`analyze` = 0 → A → A2
`fix` = B → C（基于上次分析）

---

## 阶段 0: 准备

### 构建追溯索引

> 同之前定义：读 dev-forge 追溯文件 → fidelity-index.json + 抽象继承链索引

### 自适应维度选择（LLM 推理版）

LLM 扫描 `.allforai/` 产物，对每个维度族（F/U/I/A/B）输出**适用性论证**，写入 fidelity-report.json 的 `dimension_reasoning[]`：

```json
{
  "dimension_reasoning": [
    {
      "dimension_group": "F",
      "applicable": true,
      "reasoning": "task-inventory.json 含 45 个 task，business-flows.json 含 12 条流程。后端业务逻辑是本项目的核心价值层。",
      "artifacts_examined": ["task-inventory.json", "business-flows.json", "role-profiles.json"],
      "risk_if_skipped": "high — 45 个 API 端点 + 12 条业务流将逃逸评估",
      "weight": 1.0
    },
    {
      "dimension_group": "U",
      "applicable": true,
      "reasoning": "experience-map.json 含 12 个 screen，其中 8 个有 components 和 actions。目标是 WPF 桌面应用，UI 是用户价值的主要载体。",
      "artifacts_examined": ["experience-map.json", "source-summary.json"],
      "risk_if_skipped": "high — 12 个 screen、40+ 个组件将逃逸评估",
      "weight": 1.2
    }
  ]
}
```

**产物存在性仍是起点**——LLM 检查各产物文件是否存在，但不机械映射。对每个维度族：
1. 检查相关产物是否存在
2. 评估该维度族对**本项目**的重要性
3. 输出 reasoning + risk_if_skipped + weight

**自相矛盾检测**：
- 如果 `risk_if_skipped = high` 且 `applicable = false` → 触发 CONTRADICTION 警告
- LLM 必须重新审视一次（one-shot）：重新得出相同结论 → `contradiction_acknowledged: true`，决策生效

**动态权重**：
- LLM 根据项目特征为每个维度族分配 weight（默认 1.0）
- 纯 API 后端 → F weight 高，U weight 低或 N/A
- UI 密集型应用 → U weight 提升至 1.2+，F weight 保持 1.0
- 权重和 reasoning 持久化到 fidelity-report.json，可追溯

**不允许静默跳过**：每个维度族必须出现在 `dimension_reasoning[]` 中——要么 `applicable: true`（评分），要么 `applicable: false`（带 reasoning 和 risk 评估）。报告中不得有维度族缺席。

读取各维度详细规则的方式不变：
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/static-dimensions.md（F1-F10）
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/ui-dimensions.md（U1-U6）
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/runtime-verification.md（R1-R5）
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/infra-critical-dimensions.md（I1-I5）
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/algorithm-dimensions.md（A1-A3）
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/abi-dimensions.md（B1-B4）

### 输入（三层加载）

**常驻层**（~30KB）：source-summary 摘要, product-map summary, stack-mapping platform_adaptation, fidelity-index, fidelity-report

**维度层**（按需拉取）：
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/static-dimensions.md
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/ui-dimensions.md
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/runtime-verification.md

**目标代码层**：通过 fidelity-index 精准读取，不全量扫描

---

## 阶段 A: 静态分析

LLM 按阶段 0 选中的维度逐一评分。

**F 维度**（代码/业务层）：
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/static-dimensions.md

**U 维度**（UI 层，仅 experience-map 存在时）：
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/ui-dimensions.md

**A 维度**（算法一致性，仅 archetype 含核心算法时）：
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/algorithm-dimensions.md

**I 维度**（关键基础设施，仅 infrastructure-profile 含 cannot_substitute 组件时）：
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/infra-critical-dimensions.md

**B 维度**（ABI 兼容性，仅 archetype 为 SDK/Library 时）：
> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/abi-dimensions.md

**注意力还原**（仅 consumer/mixed 且 experience-map 存在时）：
- 如果 `platform_adaptation` 存在 → 使用 `attention_threshold_override`
- 否则使用默认阈值
- 不计入总分，列入 warnings

---

## 阶段 A2: 运行时验证

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/runtime-verification.md

---

## 阶段 B + C: 修复闭环

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity/repair-protocol.md

---

## 综合评分

```
静态分 = sum(维度分_i × weight_i) / sum(weight_i)
  — weight_i 来自 dimension_reasoning[].weight
  — N/A 维度（总数为 0）不参与计算

运行时分 = (有效 R* 之和) / 有效运行时维度数

综合分 = 静态分 × 0.5 + 运行时分 × 0.5

特殊规则：I 维度（关键基础设施）有任何一个评 0 分
  → 综合分标记为 CRITICAL_INFRA_FAILURE
  → 不管其他维度多高分，报告首行标红警告
  → 修复阶段优先处理 I 维度的 gap
```

---

## 输出

写入 `.allforai/code-replicate/fidelity-report.json` + `fidelity-report.md`

---

## 与上下游的关系

```
code-replicate 路径（复刻）：
  /code-replicate → /design-to-spec → /task-execute
      ↓
  /cr-fidelity（代码级还原度 — 复刻专属，不是测试）
      ↓
  /product-verify（功能验收 — 两条路径共用）
      ↓
  /testforge（测试质量 — 两条路径共用）
      ↓
  /cr-visual（视觉还原度 — 测试全绿后，App 稳定运行时截图对比）

product-design 路径（创建）：
  /product-design → /design-to-spec → /task-execute
      ↓
  /product-verify → /testforge
```

**cr-fidelity 是复刻路径的专属环节**，验证"目标代码是否还原了源码"。
product-verify 和 testforge 是**两条路径共用的**，不关心产物来源。
cr-fidelity **不做测试** — 修复后的验证是重新评分（re-score），不是跑测试。

---

## 加载核心协议

> 核心协议详见 ${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md
