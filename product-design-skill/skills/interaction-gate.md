---
name: interaction-gate
description: >
  Phase 4.5 — Interaction Quality Gate. Use when the user asks to "run interaction gate",
  "validate usability", "interaction quality", "operation line check", "usability gate",
  "交互质量门", "可用性验证", "操作线检查", "交互评分",
  or mentions evaluating interaction quality of operation lines,
  scoring usability dimensions, or running a quality gate before UI design.
  Requires experience-map to have been run first.
version: "1.0.0"
---

# Interaction Gate — 交互质量门

> 以体验地图为输入，对每条操作线进行可用性评分，不达标线需调整后方可进入 UI 设计

## 目标

以 `experience-map.json`（必须）为输入，对所有操作线进行交互质量评估：

- **JSON 机器版**：完整字段，每条操作线含四维评分与问题列表，供下游 ui-design 和自动化使用
- **人类确认**：以可读表格形式展示逐线评分与问题，供用户审阅并决策

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/schemas/interaction-gate-schema.md

---

## 定位

```
experience-map（体验地图）    interaction-gate（交互质量门）    ui-design（UI 设计）
汇总体验层语义                每条操作线的可用性评分与问题        基于已验证操作线生成 UI
体验层语义                    交互质量层语义（质量关卡）          视觉层语义
```

**前提**：必须先运行 `experience-map`，生成 `.allforai/experience-map/experience-map.json`。

**关键原则**：**评分低于阈值的操作线需与用户讨论是否调整体验地图或接受现状，方可继续。**

---

## 快速开始

```
/interaction-gate               # 完整流程（Step 1-6），默认阈值 70
/interaction-gate --threshold 80  # 自定义阈值
```

---

## 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| step_count | 30pts | 操作步数：步数越少越好，超过合理范围扣分 |
| context_switches | 25pts | 上下文切换：角色/页面/模态切换次数，越少越好 |
| wait_feedback | 25pts | 等待反馈：异步操作是否有明确的等待状态与反馈机制 |
| thumb_zone | 20pts | 拇指区：移动端高频操作是否落在拇指可及区域 |

**总分 = step_count + context_switches + wait_feedback + thumb_zone**（满分 100）

**默认阈值**：70 分。低于阈值的操作线标记为 `fail`，需用户决策。

---

## 预置脚本（优先使用）

检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_interaction_gate.py` 是否存在：
- **存在** → `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_interaction_gate.py <BASE> [--threshold 70]`
- **不存在** → 回退到 LLM 生成（向后兼容）

预置脚本读取 experience-map.json，对每条操作线执行四维评分，输出 interaction-gate.json 并自动回填 quality_score 到 experience-map.json。

---

## 工作流

```
前置检查：
  .allforai/experience-map/experience-map.json   必须存在，否则终止

Step 1: 加载体验地图数据
      读取 experience-map.json（所有操作线）
      ↓
Step 2: 运行 gen_interaction_gate.py 评估所有操作线
      脚本对每条操作线执行四维评分
      ↓
Step 3: 展示结果 — 逐线评分与问题表格
      以可读表格形式展示每条操作线的评分和问题
      ↓
Step 4: 不达标线讨论
      若有操作线评分 < threshold，与用户讨论：
        a) 调整 experience-map 后重跑
        b) 接受当前评分，继续
      ↓
Step 5: 回填 quality_score 到 experience-map.json
      脚本自动完成，将每条操作线的总分写入 experience-map.json
      ↓
Step 6: 保存 interaction-gate.json
      输出最终质量门评估结果
```

---

### 前置检查

```
检查 .allforai/experience-map/experience-map.json：
  存在 → 加载操作线数据
  不存在 → 提示：「请先运行 /experience-map 生成体验地图，再运行 /interaction-gate」，终止
```

---

### Step 1：加载体验地图数据

读取 `experience-map.json` 获取所有操作线（operation lines）及其节点信息。

**输出**：内存中的操作线列表，用于 Step 2 脚本输入。

---

### Step 2：运行脚本评估所有操作线

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_interaction_gate.py <BASE> [--threshold 70]
```

脚本读取 `experience-map.json`，对每条操作线的四个维度独立评分：

```json
{
  "line_id": "OL001",
  "line_name": "买家下单流程",
  "scores": {
    "step_count": 28,
    "context_switches": 20,
    "wait_feedback": 22,
    "thumb_zone": 18
  },
  "total_score": 88,
  "result": "pass",
  "issues": []
}
```

**result 取值**：`pass`（total_score >= threshold）/ `fail`（total_score < threshold）

---

### Step 3：展示结果 — 逐线评分与问题表格

以可读表格形式展示所有操作线的评分：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 experience-map 分析结果决定，不限行业。

```
交互质量门评估结果（阈值：70）

| 操作线 | step_count (30) | context_switches (25) | wait_feedback (25) | thumb_zone (20) | 总分 | 结果 |
|--------|----------------|-----------------------|--------------------|-----------------|------|------|
| OL001 买家下单流程 | 28 | 20 | 22 | 18 | 88 | PASS |
| OL002 商户审核流程 | 18 | 15 | 10 | 12 | 55 | FAIL |
| OL003 退款申请流程 | 25 | 22 | 20 | 16 | 83 | PASS |
```

对于 `FAIL` 的操作线，展示具体问题：

```
OL002 商户审核流程（55 分，未达标）：
  - [wait_feedback] 审核等待无进度反馈，用户无法感知处理状态
  - [step_count] 审核需 8 步操作，建议合并为 5 步以内
  - [context_switches] 审核过程中切换 3 个不同页面，建议减少为 1 次切换
```

---

### Step 4：不达标线讨论

若有操作线评分低于阈值，逐条与用户讨论：

**用户确认**：对于每条不达标的操作线，请选择：

- **a) 调整体验地图**：根据问题建议修改 experience-map 中的操作线定义，然后重新运行 `/interaction-gate`
- **b) 接受当前评分**：标记为 `accepted`，继续进入下游 UI 设计

所有不达标线处理完毕后方可继续。

---

### Step 5：回填 quality_score 到 experience-map.json

脚本自动将每条操作线的总分写入 `experience-map.json` 对应节点的 `quality_score` 字段。此步骤由 `gen_interaction_gate.py` 在 Step 2 执行时自动完成。

---

### Step 6：保存 interaction-gate.json

输出最终质量门评估文件：

```json
{
  "version": "1.0.0",
  "generated_at": "...",
  "threshold": 70,
  "summary": {
    "total_lines": 8,
    "passed": 6,
    "failed": 2,
    "accepted": 1,
    "adjusted": 1,
    "avg_score": 78.5
  },
  "lines": [
    {
      "line_id": "OL001",
      "line_name": "买家下单流程",
      "scores": {
        "step_count": 28,
        "context_switches": 20,
        "wait_feedback": 22,
        "thumb_zone": 18
      },
      "total_score": 88,
      "result": "pass",
      "issues": []
    },
    {
      "line_id": "OL002",
      "line_name": "商户审核流程",
      "scores": {
        "step_count": 18,
        "context_switches": 15,
        "wait_feedback": 10,
        "thumb_zone": 12
      },
      "total_score": 55,
      "result": "fail",
      "disposition": "accepted",
      "issues": [
        {
          "dimension": "wait_feedback",
          "detail": "审核等待无进度反馈，用户无法感知处理状态",
          "suggestion": "增加审核进度条和预计时间提示"
        }
      ]
    }
  ]
}
```

---

## 全自动模式

**激活条件**（同时满足）：
1. `.allforai/product-concept/product-concept.json` 存在且含 `pipeline_preferences` 字段
2. 上下文含 `__orchestrator_auto: true`（由 `/product-design full` 编排器传入）

**未同时满足** → 保持标准交互模式（当前行为不变）。

**行为变化**：

| 步骤 | 标准模式 | 全自动模式 |
|------|----------|-----------|
| **Step 4 不达标线讨论** | 逐条展示，AskUserQuestion 确认 | 自动接受所有不达标线（`disposition: "auto_accepted"`） |

**安全护栏**（自动模式下仍然停下来问用户）：
- ERROR 级验证失败（experience-map.json 解析失败、操作线引用断裂）
- **评分 < 50 的操作线**：总分低于 50 意味着至少两个维度接近零分，属于严重 UX 缺陷，必须停下展示并 AskUserQuestion 确认处置方式，不可 auto_accepted

---

## 输出文件结构

```
.allforai/experience-map/
├── interaction-gate.json        # 机器可读：交互质量门评估结果
└── experience-map.json          # 已回填 quality_score 字段（原地更新）
```

---

## 防御性规范

### 加载校验
- **`experience-map.json`**：前置加载时验证 JSON 合法性。解析失败 → 提示用户重新运行 `/experience-map`，终止执行。

### 零结果处理
- **experience-map.json 无操作线**：提示「体验地图中未定义操作线，请先运行 /experience-map 补充操作线」，终止。

### 上游过期检测
- **`experience-map.json`**：加载时比较 `generated_at` 与已有 `interaction-gate.json` 的 `generated_at`。上游更新 → 警告「experience-map 在 interaction-gate 上次运行后被更新，建议重新运行 /interaction-gate」。
- 仅警告不阻断。

---

## 3 条铁律

### 1. 质量门是拦截点而非建议

不达标操作线必须经用户明确决策（调整或接受）后才可继续。不允许静默跳过不达标线。

### 2. 以体验地图为唯一数据源

只从 experience-map.json 推导操作线评分，不引入体验地图之外的流程。发现遗漏操作线，先更新 experience-map，再重跑 interaction-gate。

### 3. 只评估不修改

interaction-gate 只输出评分与问题数据（及回填 quality_score），不触发任何设计变更或代码生成。操作线调整由用户决策，设计变更由下游 ui-design 负责。
