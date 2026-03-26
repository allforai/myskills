---
name: cr-visual
description: >
  Use when user wants to "compare UI visually", "视觉还原", "截图对比",
  "UI 还原度", "看看界面像不像", "visual comparison", "screenshot diff",
  or mentions comparing source and target app screenshots for UI fidelity.
---

# 视觉还原度 — CR Visual v2.0（Sub-Agent 架构）

> 源 App vs 目标 App 逐屏截图/录像 → 对比 → 修复 → 重新对比 → 直到视觉一致

## 定位

cr-visual 是复刻流程的**最后一步** — 在 cr-fidelity + product-verify + testforge 全部通过后执行。

```
/cr-fidelity → /product-verify → /testforge → /cr-visual（这里）
```

**前置条件**：测试全绿，App 能稳定运行。

## 模式

- `full` = 采集 → 对比 → 报告 → 修复闭环（最多 30 轮）
- `analyze` = 采集 → 对比 → 报告（不修代码）
- `fix` = 基于上次报告修复

## Sub-Agent 架构

> **为什么拆分**：单 agent 同时处理截图采集、结构对比、数据审计、联动验证、报告生成、修复循环 → 注意力稀释，后面的步骤（数据完整性、联动）容易被忽略。拆分后每个 agent 只专注一件事。

```
cr-visual orchestrator（本文件）
  ├── capture agent ────── Steps 1-3（截图采集）
  ├── 逐 screen 并行派遣：
  │   ├── structural agent ── Step 4（结构对比）
  │   ├── data-integrity agent ── Step 4.5（数据完整性审计）
  │   └── linkage agent ──── Step 4.6（联动验证，有 linkage_verify 时）
  ├── report agent ────── Step 5（合并评分 + 生成报告）
  └── repair agent ────── Steps 6-7（修复闭环，仅 full/fix 模式）
```

## 自动排除规则

**平台差异**：`stack-mapping.json` 含 `platform_adaptation` → 符合 `ux_transformations` 的差异自动标记 `not_a_gap`。

**多角色**：`role-view-matrix.json` 存在 → 逐角色截图并分别对比。

**交互行为**：`interaction-recordings.json` 存在 → 执行同样的业务流程链，五层验证：
1. 静态页面：截图对比
2. CRUD 全状态：flow 链覆盖生命周期
3. 动态效果：录像对比
4. API 日志：请求对比
5. 综合：里程碑截图 + API 都一致 = high

---

## 执行协议：规划 → 执行 → 验收

### Phase A: 截图采集

```
1. Read ${CLAUDE_PLUGIN_ROOT}/docs/cr-visual/step-capture.md
2. 派遣 capture Agent：
   - 输入：experience-map.json, route-map.json, replicate-config.json
   - 输出：screens[] 截图路径映射
   - 失败条件：无可用截图 → 报错退出
```

### Phase B: 任务规划（关键新增）

> 不直接跳到对比。先枚举"要做什么"，生成显式任务清单。

```
1. Read ${CLAUDE_PLUGIN_ROOT}/docs/cr-visual/step-plan.md
2. 派遣 plan Agent：
   - 输入：screens[] + experience-map + interaction-recordings + 目标源码路径
   - 执行：逐 screen 扫描源码，枚举数据绑定控件 + 联动关系
   - 输出：visual-task-plan.json（每个 screen 的 subtask 清单）
3. 展示任务摘要：「20 screens, 67 subtasks: 20 结构 + 35 数据完整性 + 12 联动」
```

### Phase C: 按清单执行（任务驱动派遣）

读 visual-task-plan.json，按 subtask 类型分组派遣 Agent：

```
对每个 screen（或每批 5 个 screen）：

Agent 1 — structural（始终派遣）:
  Read ${CLAUDE_PLUGIN_ROOT}/docs/cr-visual/step-structural.md
  输入：source + target 截图 + platform_adaptation
  输出：structural_score + differences
  完成后：更新 task-plan 中 VT-xxx-S 的 status → completed

Agent 2 — data-integrity（仅该 screen 有 data_integrity subtask 时派遣）:
  Read ${CLAUDE_PLUGIN_ROOT}/docs/cr-visual/step-data-integrity.md
  输入：source + target 截图 + 目标代码 + **该 screen 的控件清单**（来自 task-plan）
  输出：data_integrity_score + data_integrity_gaps[]
  完成后：逐个更新 VT-xxx-D* 的 status
  该 screen 无 data_integrity subtask → 不派遣（节省 agent）

Agent 3 — linkage（仅该 screen 有 linkage subtask 时派遣）:
  Read ${CLAUDE_PLUGIN_ROOT}/docs/cr-visual/step-linkage.md
  输入：linkage subtask 清单 + 目标 App URL
  输出：linkage_score + linkage_results[]
  完成后：逐个更新 VT-xxx-L* 的 status
  该 screen 无 linkage subtask → 不派遣

并行策略：同一 screen 的 3 个 agent 并行；structural 无依赖，
data-integrity 和 linkage 可能需要操作目标 App → 同 screen 串行或按需协调。
```

### Phase D: 验收（杜绝遗漏）

```
1. 读 visual-task-plan.json → 检查所有 subtask 的 status
2. 统计：
   - completed: N
   - failed: M（对比失败，需修复）
   - skipped: K（附跳过原因）
   - pending: P（不应存在 — 有则说明 agent 漏执行了）
3. pending > 0 → 补派 agent 执行遗漏的 subtask
4. 全部非 pending 后 → 进入报告阶段
```

### Phase E: 合并评分 + 报告

```
Read ${CLAUDE_PLUGIN_ROOT}/docs/cr-visual/step-report.md
合并公式：
  final_score = structural_score - data_integrity_penalties - linkage_penalties
  final_score = max(0, final_score)
  match_level: ≥90 → high | ≥60 → medium | ≥30 → low | <30 → mismatch

写入：visual-report.json + visual-report.md
报告中附上任务完成率：「67/67 subtasks completed, 0 skipped」
```

### Phase F: 修复闭环（仅 full/fix 模式）

```
Read ${CLAUDE_PLUGIN_ROOT}/docs/cr-visual/step-repair.md
派遣 repair Agent：
  输入：visual-report.json + visual-task-plan.json
  修复优先级：按 subtask 的 failed 状态逐个修复
  每修完一个 subtask → 重新截图 → 重新对比 → 更新 task-plan status
  退出：全部 subtask completed 且 score = high，或 30 轮上限
```

---

## 注意力保障机制

| 机制 | 效果 |
|------|------|
| **任务清单驱动** | agent 按清单执行，不存在"忘了检查"的可能 |
| **验收阶段检查 pending** | 遗漏的 subtask 被自动发现并补执行 |
| 每个 agent 只加载自己的 step-*.md | 上下文窄，专注度高 |
| **按需派遣**（无控件 → 不派 agent） | 减少无效工作 |
| structural / data-integrity / linkage 并行 | 互不干扰，各自深度执行 |
| repair agent 按 subtask 逐个修复 | 不可能遗漏待修项 |

---

## 局限性

- LLM 的视觉对比是**主观的** — 报告附截图路径，用户应复核
- 需要 App 能运行且可导航到各页面（需要测试账号/数据）
- 移动端截图依赖平台对应的 UI 自动化工具或用户手动截图
- 交互行为对比依赖 `interaction-recordings.json` — 无此文件时仅做静态截图对比

---

## 加载核心协议

> 核心协议详见 ${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md
