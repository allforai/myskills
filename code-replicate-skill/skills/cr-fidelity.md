---
name: cr-fidelity
description: >
  Use when user wants to "verify replication fidelity", "还原度验证", "检查复刻质量",
  "compare source vs target", "fidelity check", "复刻对比", "还原度不够",
  "check if migration is complete", or mentions verifying that target code
  faithfully reproduces source code behavior after code-replicate + dev-forge.
---

# 还原度验证 — CR Fidelity v1.0

> 源码 vs 目标代码的业务行为还原度闭环验证

## 定位

code-replicate 提取产物 → dev-forge 生成目标代码 → **cr-fidelity 验证还原度**。
不达标则自动分析差距 → 生成修复任务 → 执行修复 → 重测，直到达标或收敛。

---

## 三阶段流程

| 阶段 | 名称 | 说明 |
|------|------|------|
| A | Analyze | 多维度对比源码 vs 目标代码，输出评分 + 差距清单 |
| B | Fix | 按差距清单生成修复任务 → 执行修复 |
| C | Re-verify | 重新评分，不达标则回到 B，达标则输出终报 |

`full` 模式 = A → B → C 闭环（最多 3 轮）
`analyze` 模式 = 仅 A
`fix` 模式 = 仅 B（基于上次 A 的差距清单）

---

## 阶段 A: 多维度分析

### 输入

LLM 同时持有三份数据：

1. **source-summary.json** — 源码模块结构、抽象模式、横切关注点
2. **.allforai/ 产物** — task-inventory、business-flows、role-profiles、experience-map、use-case-tree、constraints
3. **目标代码** — dev-forge 生成的实际代码文件

### 分析维度

LLM 从以下维度逐一对比，**每个维度独立评分 0-100**：

#### F1 — API 表面还原

对比产物中 task-inventory 的 inputs/outputs 与目标代码中实际实现的 API 端点：
- 每个 task 是否有对应的端点/handler/controller？
- 输入参数（字段名、类型、必填性）是否一致？
- 输出响应（字段名、类型、状态码）是否一致？
- 评分 = 匹配 task 数 / 总 task 数 × 100

#### F2 — 数据模型还原

对比 source-summary.data_entities 与目标代码中实际定义的实体/模型：
- 每个源码实体是否有对应的目标实体？
- 字段名称和类型是否匹配？
- 关系（1:N, N:M）是否保留？
- 评分 = 匹配字段数 / 总字段数 × 100

#### F3 — 业务流还原

对比 business-flows 与目标代码中实际的调用链：
- 每个 flow 的节点顺序是否在目标代码中可追踪？
- 跨模块调用（handoff）是否实现？
- 事务边界是否保留？
- 评分 = 可追踪 flow 数 / 总 flow 数 × 100

#### F4 — 角色权限还原

对比 role-profiles 与目标代码中实际的认证/授权实现：
- 每个角色是否在目标代码的 RBAC/权限系统中定义？
- 权限边界是否与源码一致？
- 评分 = 已实现角色数 / 总角色数 × 100

#### F5 — 异常处理还原

对比 use-case-tree 中 type=exception/boundary 的用例与目标代码中的错误处理：
- 每个异常用例是否有对应的 try-catch / error handler？
- 错误消息和状态码是否与 acceptance_criteria 一致？
- 评分 = 已处理异常数 / 总异常用例数 × 100

#### F6 — 抽象复用还原

对比 source-summary.abstractions 与目标代码中实际的共享工具/基类：
- 每个高复用抽象（consumer_count > 3）是否有目标等价物？
- 消费模块是否确实使用了共享工具而非内联重复代码？
- 评分 = 已复用抽象数 / 总高复用抽象数 × 100

#### F7 — 约束执行还原（仅 exact 保真度）

对比 constraints.json 与目标代码中的约束实现：
- 每个 enforcement=hard 的约束是否有代码执行？
- 评分 = 已实现约束数 / 总 hard 约束数 × 100

### 注意力还原（仅 consumer/mixed 模式）

如果 experience_priority.mode = consumer 或 mixed，额外检查：
- Phase 4b.5 标记的 `_attention_flags` 是否在目标 UI 中被解决？
- 操作步骤数是否在合理范围？

### 综合评分

```
总分 = (F1 + F2 + F3 + F4 + F5 + F6 + F7) / 有效维度数
```

- F7 仅 exact 模式有效；非 exact 模式有效维度 = 6
- 注意力还原不计入总分，但列入 warnings

### 输出

写入 `.allforai/code-replicate/fidelity-report.json`：

```json
{
  "generated_at": "ISO8601",
  "round": 1,
  "threshold": 90,
  "overall_score": 78,
  "passed": false,
  "dimensions": {
    "F1_api_surface": {"score": 85, "total": 50, "matched": 42, "gaps": [...]},
    "F2_data_model": {"score": 90, "total": 30, "matched": 27, "gaps": [...]},
    "F3_business_flow": {"score": 70, "total": 20, "matched": 14, "gaps": [...]},
    "F4_role_permission": {"score": 100, "total": 5, "matched": 5, "gaps": []},
    "F5_exception_handling": {"score": 55, "total": 40, "matched": 22, "gaps": [...]},
    "F6_abstraction_reuse": {"score": 80, "total": 5, "matched": 4, "gaps": [...]},
    "F7_constraint": null
  },
  "attention_warnings": [...],
  "fix_tasks": [...]
}
```

同时生成 `.allforai/code-replicate/fidelity-report.md`（人类可读摘要）。

---

## 阶段 B: 差距修复

### 差距分类

LLM 将 gaps 分为三类：

| 类别 | 含义 | 处理 |
|------|------|------|
| `CODE_FIX` | 目标代码缺少实现或实现错误 | 直接修改目标代码 |
| `ARTIFACT_GAP` | .allforai 产物遗漏导致 dev-forge 未生成 | 回到 Phase 3 补充产物 → 重新 design-to-spec |
| `DESIGN_DECISION` | 架构差异导致，需要人工决策 | 写入报告 warnings，不自动修复 |

### 修复执行

1. **CODE_FIX** — LLM 直接读差距描述 + 目标代码 → 修改代码：
   - 补充缺失的 API handler
   - 补充缺失的异常处理
   - 补充缺失的权限检查
   - 将内联重复代码提取为共享工具

2. **ARTIFACT_GAP** — LLM 回到 extraction-plan 补充片段：
   - 补充遗漏的 task/flow/use-case
   - 重新 merge + validate
   - 提示用户重新执行 `/design-to-spec` → `/task-execute`（如果影响范围大）

3. **DESIGN_DECISION** — 不自动处理，记录到报告

### 修复范围控制

- 每轮最多修复 **20 个 CODE_FIX** + **5 个 ARTIFACT_GAP**
- 超出则按 score 影响排序，优先修复低分维度的 gaps
- DESIGN_DECISION 计入总分但不修复（用户自行决策后重测）

---

## 阶段 C: 重测循环

### 收敛控制（CG-F）

```
闭环循环:
  Round 1: Analyze → 评分 78 → Fix 15 gaps → Re-analyze
  Round 2: Re-analyze → 评分 88 → Fix 5 gaps → Re-analyze
  Round 3: Re-analyze → 评分 93 → 达标 ✓

收敛条件:
  - 达标: overall_score ≥ threshold → 输出终报，退出
  - 最多 3 轮
  - 每轮 score 必须 > 上一轮（单调递增）
  - 违反单调递增（分数不升反降）→ 停止，输出当前最高分的报告
  - 第 3 轮仍未达标 → 输出报告 + 剩余 gaps 清单，建议人工介入
```

### 终报输出

`fidelity-report.json` 和 `fidelity-report.md` 更新为最终轮结果，包含：
- 各维度最终评分
- 已修复的 gaps（含 diff 摘要）
- 未修复的 gaps（DESIGN_DECISION + 超限项）
- 各轮评分变化趋势
- 下一步建议

---

## 与上下游的关系

```
/code-replicate    → .allforai/ 产物（source of truth for business intent）
    ↓
/design-to-spec    → 规格文档
/task-execute      → 目标代码
    ↓
/cr-fidelity       → 还原度闭环 ← 本技能
    ↓
  达标 → /product-verify（dev-forge 的产品验收）
  不达标 → 继续修复 or 人工决策
```

---

## 加载核心协议

> 核心协议详见 ${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md
