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

### 自适应维度选择

LLM 扫描 `.allforai/` 产物，根据**实际存在的产物**决定启用哪些验证维度：

```
检查 task-inventory.json     → 存在? → Read static-dimensions.md → 启用 F1
检查 source-summary.data_entities → 非空? → 启用 F2
检查 business-flows.json     → 存在? → 启用 F3
检查 role-profiles.json      → 存在? → 启用 F4
检查 use-case-tree.json      → 存在? → 启用 F5
检查 source-summary.abstractions → 非空? → 启用 F6
检查 constraints.json        → 存在? → 启用 F7
检查 infrastructure-profile.json → 存在? → 启用 F8

检查 experience-map.json     → 存在? → Read ui-dimensions.md → 启用 U1-U6

检查 目标项目可构建?         → Read runtime-verification.md → 启用 R1
检查 test-vectors.json       → 存在? → 启用 R3
检查 stack-mapping compatibility: exact → 启用 R4
检查 infrastructure-profile 含数据持久化? → 启用 R5 行为场景

检查 infrastructure-profile 含事件总线? → F9 事件覆盖启用
检查 infrastructure-profile 含数据持久化? → F10 启用（在 static-dimensions.md 中）
检查 infrastructure-profile 含 cannot_substitute? → Read infra-critical-dimensions.md → 启用 I1-I5
检查 project_archetype 含核心算法? → Read algorithm-dimensions.md → 启用 A1-A3
检查 project_archetype 含 ABI 兼容? → Read abi-dimensions.md → 启用 B1-B4
```

**archetype 判断由 LLM 语义理解** — 读 `replicate-config.project_archetype` 的自由文本描述，判断是否涉及算法/ABI。不靠关键词匹配。

**不硬编码"前端用 U 维度、后端用 F 维度"** — 纯粹按产物存在性决定。一个有 experience-map 的后端 BFF 项目也会启用 U 维度。一个有本地数据库的前端 App 也会启用 F2。

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
静态分 = (有效 F* + 有效 U* + 有效 I* + 有效 A* + 有效 B* 之和) / 有效维度数
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
