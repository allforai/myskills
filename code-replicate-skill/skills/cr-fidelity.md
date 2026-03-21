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

### 前置步骤：构建追溯索引

在开始维度分析前，LLM 先构建 **source→target 追溯索引**，解决跨栈名称映射问题：

1. **读 dev-forge 追溯文件**（如果存在）：
   - `.allforai/project-forge/*/tasks.json` — 包含 `_Source: T001` 追溯引用
   - `.allforai/project-forge/*/design.json` — 包含 API endpoint 与 task 的映射
   - 如果存在 → 直接用追溯引用建立 task ID → 目标文件的映射

2. **无追溯文件时自建索引**（降级模式）：
   - 读 stack-mapping.json 的 auto_mapped / abstraction_mapping 理解命名转换规则
   - 用 Glob 扫描目标代码目录结构 → 建立目标子项目/模块清单
   - 用 Grep 批量搜索 task name 关键词（支持跨语言：中文→英文翻译后搜索）
   - 输出 `fidelity-index.json`：`{ "T001": ["src/.../AppointmentsViewModel.cs:CreateAppointment"], ... }`

3. **抽象继承链索引**：
   - Grep 搜索 source-summary.abstractions 中每个抽象的 target_equivalent（如 `BaseViewModel`）
   - 找到后读该文件，提取其提供的公共方法清单
   - 后续维度分析时，如果某功能在具体文件中找不到但基类提供了 → 标记为"基类覆盖"而非 gap

追溯索引构建完成后缓存在 `fidelity-index.json` 中，后续轮次直接复用（增量更新修改的部分）。

### 输入

LLM 分三层加载数据（避免 context 爆炸）：

**常驻层**（全程持有，~30KB）：
- source-summary.json 的 project + modules 列表（不含 key_files 内容）
- product-map.json 的 summary + experience_priority
- stack-mapping.json 的 `platform_adaptation`（如果存在 — 跨平台迁移时调整评估标准）
- fidelity-index.json（追溯索引 — task→文件映射）
- fidelity-report.json（上一轮结果，首轮为空）

**产物层**（按维度按需加载）：
- 分析 F1 时加载 task-inventory.json
- 分析 F2 时加载 source-summary.data_entities
- 分析 F3 时加载 business-flows.json
- 依此类推 — 每个维度只加载需要的产物

**目标代码层**（通过追溯索引精准读取）：
- 不再逐模块全量搜索 — 通过 fidelity-index 直接定位目标文件
- 每个 task/entity/flow 只读对应的 1-2 个目标文件
- **并行度优化**：同一子项目的多个 task 可以批量读取该子项目的关键文件

### 分析维度

LLM 从以下维度逐一对比，**每个维度独立评分 0-100**。

**评分规则**（消除主观性）：
- 每个维度的"总数"来自 .allforai/ 产物（确定性来源）
- "匹配数"由 LLM 通过 fidelity-index 定位目标文件后逐项查证
- 每个 gap 必须记录 `evidence`：产物条目 ID + 目标文件搜索结果
- **总数为 0 的维度**自动标记为 N/A，不计入综合评分
- **基类覆盖**的功能算作匹配（不是 gap）— 在 evidence 中标注 `via: BaseViewModel`：

#### F1 — API 表面还原

对比产物中 task-inventory 的 inputs/outputs 与目标代码中实际实现的 API 端点：
- 每个 task 是否有对应的端点/handler/controller？
- 输入参数（字段名、类型、必填性）是否一致？
- 输出响应（字段名、类型、状态码）是否一致？
- **路由模型一致性**：如果源码使用配置式路由（如 nginx.conf location 块），目标使用代码式路由（如 Gin router），检查路由优先级和路径参数映射是否等价。路由冲突（源码无冲突但目标有冲突）标记为 gap
- 如果 `platform_adaptation.skip_source_features` 存在，排除相关 task 后再计分
- 评分 = 匹配 task 数 / 有效 task 数 × 100

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

如果 experience_priority.mode = consumer 或 mixed，额外检查注意力负载。

**平台适配**：如果 stack-mapping.json 含 `platform_adaptation`：
- 使用 `attention_threshold_override` 的阈值替代默认移动端阈值
- `skip_source_features` 中的功能从所有维度的 total 中排除（不计入评分基数）
- `experience_priority_override` 覆盖 product-map 中的 experience_priority（调整消费端成熟度评估标准）

**无 platform_adaptation 时**（同平台迁移）：使用默认阈值（移动端 7 步、3 次上下文切换）

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
| `ARTIFACT_GAP` | .allforai 产物遗漏导致 dev-forge 未生成 | cr-fidelity 内部补充产物（见下文） |
| `DESIGN_DECISION` | 架构差异导致，需要人工决策 | 写入报告 warnings，不自动修复 |

### CODE_FIX 修复安全协议

**按维度批量修复**（不逐个修复 + 逐个测试，避免超大项目测试时间爆炸）：

1. **批量修改**：同一维度（如 F5）的所有 CODE_FIX 一次性全部修改
2. **批量测试**：该维度全部修改完成后，跑一次测试（`dotnet test` / `npm test` / 对应框架测试命令）
3. **测试结果处理**：
   - 全部通过 → 该维度修复完成，进入下一维度
   - 部分失败 → 逐个回滚最近修改的文件，每回滚一个重跑测试，直到测试通过
   - 被回滚的 gap → 重分类为 `DESIGN_DECISION`
4. **无测试项目**：如果目标代码没有测试框架，跳过测试步骤，在 report 中标注 `untested_fixes`

### ARTIFACT_GAP 修复

cr-fidelity 内部处理，**不要求用户退出重跑 `/code-replicate`**：

1. LLM 读 extraction-plan.json 定位遗漏来源
2. LLM 读源码对应文件，生成补充片段 → 写入 fragments/
3. 调用 merge 脚本重新合并对应产物
4. 调用 `cr_validate.py` 校验补充后的产物
5. 如果补充项影响 design-to-spec 已生成的规格（新增了 task 或 flow）：
   - 少量（≤3 个新 task）→ cr-fidelity 直接在目标代码中补充实现
   - 大量（>3 个新 task）→ 标记为 `DESIGN_DECISION`，建议用户重跑 `/design-to-spec`

### DESIGN_DECISION 处理

不自动修复，但记录足够信息让用户决策：
- 具体的差异描述（源码做了什么 vs 目标缺了什么）
- 推荐的解决方向
- 如果用户决策后需要重测，执行 `/cr-fidelity fix`

### 修复范围控制

- 每轮最多修复 **20 个 CODE_FIX** + **5 个 ARTIFACT_GAP**
- 超出则按 score 影响排序，优先修复**最低分维度**的 gaps
- DESIGN_DECISION 不计入修复额度

---

## 阶段 C: 重测循环

### 重测策略（区分 CODE_FIX 和 ARTIFACT_GAP）

**纯 CODE_FIX 轮（本轮无 ARTIFACT_GAP）** → 增量重测：
1. 记录 Round N 修改了哪些文件（`modified_files` 列表）
2. 更新 fidelity-index.json 中受影响的映射
3. Round N+1 只重新评估：
   - 修改的文件所属维度 → 重新评分
   - 其他维度保持上轮分数（基线未变）

**含 ARTIFACT_GAP 轮（本轮补充了产物）** → 全量重测：
- 产物基线变了（task 总数变了、flow 变了）→ 所有维度必须重新评分
- 更新 fidelity-index.json（新增的 task 需要新建追溯映射）
- 新增但未实现的 task → 直接计为 gap（不需要在目标代码中搜索）

### 收敛控制（CG-F）

```
闭环循环:
  Round 1: Analyze → 评分 78 → Fix 15 gaps (12 CODE_FIX + 3 ARTIFACT_GAP) → 全量重测
  Round 2: Re-analyze → 评分 88 → Fix 5 gaps (5 CODE_FIX) → 增量重测
  Round 3: Re-analyze → 评分 93 → 达标 ✓

收敛条件:
  - 达标: overall_score ≥ threshold → 输出终报，退出
  - 最多 3 轮
  - 每轮总修复 gap 数必须 > 0（有在进步）
  - 跨维度回归处理:
    · 本轮修改了文件集合 S
    · 重测时发现维度 Fx 分数下降 > 5 分
    · 找出 S 中属于 Fx 检查范围的文件子集 S_fx
    · 回滚 S_fx 中所有修改 → 重跑 Fx 单维度评分 → 确认恢复
    · 被回滚文件关联的 gap 重分类为 DESIGN_DECISION
    · 其他维度的修改保留
  - 第 3 轮仍未达标 → 输出报告 + 剩余 gaps，建议人工介入
```

**跨维度回归的核心逻辑**：不是按"维度"回滚，而是按"文件"回滚 — 找到导致回归的文件集合，精确回滚这些文件的修改。

### 终报输出

`fidelity-report.json` 和 `fidelity-report.md` 更新为最终轮结果，包含：
- 各维度最终评分 + 各轮变化趋势
- 已修复的 gaps（含修改的文件和 diff 摘要）
- 未修复的 gaps（DESIGN_DECISION + 超限项 + 连锁回滚项）
- 各轮修复记录
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
    ↓                  ↑
    ↓              ARTIFACT_GAP → 内部补充产物 + merge + 直接实现
    ↓              CODE_FIX → 直接修改目标代码 + 跑测试
    ↓              DESIGN_DECISION → 记录 → 用户决策 → /cr-fidelity fix
    ↓
  达标 → /product-verify（dev-forge 的产品验收）
```

---

## 加载核心协议

> 核心协议详见 ${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md
