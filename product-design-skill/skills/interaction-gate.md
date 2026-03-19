---
name: interaction-gate
description: >
  Phase 4.5 — Interaction Quality Gate. Use when the user asks to "run interaction gate",
  "validate usability", "interaction quality", "operation line check", "usability gate",
  "交互质量门", "可用性验证", "操作线检查", "交互评分",
  or mentions evaluating interaction quality of operation lines,
  scoring usability dimensions, or running a quality gate before UI design.
  Requires experience-map to have been run first.
version: "1.1.0"
---

# Interaction Gate — 交互质量门

> 以体验地图为输入，对每条操作线进行可用性评分，不达标线需调整后方可进入 UI 设计

## 目标

以 `experience-map.json`（必须）为输入，对所有操作线进行交互质量评估：

- **JSON 机器版**：完整字段，每条操作线含四维评分与问题列表，供下游 ui-design 和自动化使用
- **人类确认**：以可读表格形式展示逐线评分与问题，供用户审阅并决策

当 `product-map.json` 中的 `experience_priority.mode = consumer` 或 `mixed` 时，interaction-gate 还必须额外评估：这些操作线是否已经达到成熟用户产品所需的主线清晰度、下一步引导、反馈完整性与低注意力可用性。

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/schemas/interaction-gate-schema.md

---

## 定位

```
experience-map（体验地图）    interaction-gate（交互质量门）    ui-design（UI 设计）
汇总体验层语义                每条操作线的可用性评分与问题        基于已验证操作线生成 UI
体验层语义                    交互质量层语义（质量关卡）          视觉层语义
```

**前提**：必须先运行 `experience-map`，生成 `.allforai/experience-map/experience-map.json`。

若 `.allforai/product-map/product-map.json` 含 `experience_priority`，interaction-gate 必须继承该字段，切换不同的门禁标准。

**关键原则**：**评分低于阈值的操作线需与用户讨论是否调整体验地图或接受现状，方可继续。**

---

## 快速开始

```
/interaction-gate               # 完整流程（Step 1-6），默认阈值 70
/interaction-gate --threshold 80  # 自定义阈值
```

---

## 增强协议（4D+6V）

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/skill-commons.md`「统一验收方法论」。

**4D+6V 重点**：每条操作线的评分附带 D2 证据（screen 的 actions 数量、flow_context 切换次数等可追溯依据）和 D4 决策理由（为什么给这个分数而非更高/更低）；fail 操作线的 issues 覆盖至少 3/6 视角——user: 用户能顺畅完成吗？business: 会导致转化流失吗？ux: 认知负荷是否过重？tech: 有技术层面的等待瓶颈吗？

---

## 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| step_count | 30pts | 操作步数：步数越少越好，超过合理范围扣分 |
| context_switches | 25pts | 上下文切换：角色/页面/模态切换次数，越少越好 |
| wait_feedback | 25pts | 等待反馈：异步操作是否有明确的等待状态与反馈机制 |
| thumb_zone | 20pts | 拇指区：移动端高频操作是否落在拇指可及区域 |

当 `experience_priority.mode = consumer` 或 `mixed` 时，四维评分之外还必须额外审查：

- 主线清晰度：用户是否在 2 秒内知道当前线的核心目标
- 下一步引导：完成当前动作后是否知道接下来做什么
- 持续关系：流程是否只停在一次完成，而没有回访/持续使用线索
- 低注意力适配：移动端场景下是否需要过多记忆与来回跳转

**总分 = step_count + context_switches + wait_feedback + thumb_zone**（满分 100）

**默认阈值**：70 分。低于阈值的操作线标记为 `fail`，需用户决策。

---

## 生成方式

LLM 直接分析 experience-map.json 中的所有操作线，对每条线执行四维评分（step_count / context_switches / wait_feedback / thumb_zone）。交互质量评估需要理解用户认知负荷、上下文切换的心理成本等语义因素，脚本只能做机械计数。

交互质量评估完全由 LLM 执行：评分、问题诊断、改进建议均基于 LLM 对用户认知负荷和交互语义的理解。

**输出文件名约束**：主产物必须为 `interaction-gate.json`（写入 `.allforai/experience-map/`），不可使用其他命名。

### 执行失败保护

- 任何步骤遇到不可恢复错误 → 写入 `.allforai/experience-map/interaction-gate-error.json`，包含 `{"error": "...", "step": "...", "timestamp": "..."}`。

---

## 工作流

```
前置检查：
  .allforai/product-concept/concept-baseline.json  自动加载（推拉协议 §三.A）→ 不存在则 WARNING，不阻塞
  .allforai/experience-map/experience-map.json   必须存在，否则终止
  .allforai/product-map/product-map.json         若存在且含 `experience_priority.mode = consumer|mixed` → 启用用户端附加门禁

Step 1: 加载体验地图数据
      读取 concept-baseline.json（产品定位、角色粒度 — 背景知识）
      读取 experience-map.json（所有操作线）
      ↓
Step 2: LLM 评估所有操作线
      对每条操作线执行四维评分
      ↓
Step 2.5: LLM 自审验证（Loop）
      LLM 切换为审查者视角，用上游基线（experience-map）对照审查评分合理性
      不通过 → 修正评分 → 重审（最多 2 轮）
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

### Step 2：LLM 评估所有操作线

分析 `experience-map.json`，对每条操作线的四个维度独立评分：

```json
{
  "line_id": "OL001",
  "line_name": "用户提交任务流程",
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

### Step 2.5：LLM 自审验证（Loop）

LLM 评分后，切换到审查者视角，用上游基线 + 自身一致性审查评分合理性。**所有验证由 LLM 判断。**

**上游基线对照**（用 experience-map.json 验证评分）：

LLM 同时持有 experience-map.json（上游，含 screens 的 components/actions/states 等设计细节）和评分结果（当前产出），对照审查：

1. **评分与设计复杂度一致吗？** — 一个只有 2 个 screen、每个 screen 仅 1-2 个 action 的操作线，step_count 不应低于 25/30；反之一个 8 步、跨 4 个 screen 的操作线，step_count 不应高于 20/30
2. **context_switches 与 flow_context 一致吗？** — 操作线中 screen 的 platform 切换、角色切换、模态弹窗数量应与 context_switches 评分对应
3. **wait_feedback 与 states 一致吗？** — screen 定义了 loading/error 状态处理的操作线应比没有定义的评分更高
4. **thumb_zone 与 platform 一致吗？** — desktop-web 操作线的 thumb_zone 权重应被合理调整（桌面端无拇指区约束）

若 `experience_priority.mode = consumer` 或 `mixed`，再额外审查：

5. **主线是否明确？** — 首页/入口页是否把主线动作埋没在功能入口拼盘中
6. **下一步是否明确？** — 完成动作后是否有清晰的后续引导或结果回流
7. **持续关系是否存在？** — 是否完全缺少进度、历史、提醒、通知、最近活动等回访线索

**自身一致性审查**：

- 评分分布是否合理？不应出现所有操作线都是 85-90 的「安全区间聚集」
- 同类操作线（如两条 CRUD 管理线）的评分差异是否有合理解释？
- issues 列表是否与低分维度对应？（不应出现某维度扣分但 issues 中无相关问题的情况）

**Loop 机制**：

```
LLM 评分 → 自审验证
  通过 → Step 3
  不通过 →
    列出具体问题（哪些评分与设计不一致、哪些评分分布异常）
    LLM 修正对应操作线的评分和 issues
    → 重新自审（最多 2 轮）
  2 轮后仍不通过 → 记录剩余问题，WARNING 继续
```

---

### Step 3：展示结果 — 逐线评分与问题表格

以可读表格形式展示所有操作线的评分：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 experience-map 分析结果决定，不限行业。

```
交互质量门评估结果（阈值：70）

| 操作线 | step_count (30) | context_switches (25) | wait_feedback (25) | thumb_zone (20) | 总分 | 结果 |
|--------|----------------|-----------------------|--------------------|-----------------|------|------|
| OL001 用户提交任务流程 | 28 | 20 | 22 | 18 | 88 | PASS |
| OL002 管理员审核流程 | 18 | 15 | 10 | 12 | 55 | FAIL |
| OL003 撤销申请流程 | 25 | 22 | 20 | 16 | 83 | PASS |
```

对于 `FAIL` 的操作线，展示具体问题：

```
OL002 管理员审核流程（55 分，未达标）：
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

将每条操作线的总分写入 `experience-map.json` 对应节点的 `quality_score` 字段。

---

### Step 6：保存 interaction-gate.json

输出最终质量门评估文件：

```json
{
  "version": "1.1.0",
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
      "line_name": "用户提交任务流程",
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
      "line_name": "管理员审核流程",
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
