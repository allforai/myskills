---
name: journey-emotion
description: >
  Phase 3 — Emotion Journey Mapping. Use when the user asks to "generate emotion map",
  "map user emotions", "journey emotion", "emotion journey", "human decision point",
  "体验情绪", "情绪旅程", "旅程情绪图", "情绪地图", "决策点标注",
  or mentions mapping emotional highs/lows across user journeys,
  identifying risk points and design hints per journey node.
  This step requires human confirmation before proceeding to experience-map.
  Requires product-map to have been run first.
version: "1.0.0"
---

# Journey Emotion — 旅程情绪图

> 以功能地图为输入，为每条业务流的关键节点标注情绪、强度、风险与设计提示

## 目标

以 `business-flows.json`（必须）和 `role-profiles.json`（必须）为输入，生成旅程情绪图：

- **JSON 机器版**：完整字段，每条旅程线的每个节点含 emotion / intensity / risk / design_hint，供下游 experience-map 和自动化使用
- **人类确认**：以可读表格形式展示，供用户逐条审阅并调整

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/schemas/journey-emotion-schema.md

---

## 定位

```
product-map（功能地图）    journey-emotion（旅程情绪图）    experience-map（体验地图）
谁用？做什么？流程如何？    每个节点的情绪、风险、设计提示    汇总为完整体验地图
任务层 + 流程层语义        情绪层语义（人工确认）            体验层语义
```

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/business-flows.json` 和 `.allforai/product-map/role-profiles.json`。

**关键原则**：**本步骤要求人工确认后才能继续进入 experience-map。** 脚本生成的是初始中性/默认值，用户必须审阅并根据实际业务场景进行定制。

---

## 快速开始

```
/journey-emotion           # 完整流程（Step 1-5）
/journey-emotion refresh   # 清空决策缓存，从头重新运行
```

---

## 预置脚本（优先使用）

检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_journey_emotion.py` 是否存在：
- **存在** → `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_journey_emotion.py <BASE>`
- **不存在** → 回退到 LLM 生成（向后兼容）

预置脚本生成初始情绪图，所有节点默认为中性情绪（neutral / intensity=3）。**脚本输出仅为初始值，必须经用户审阅调整后才视为有效。**

---

## 工作流

```
前置检查：
  .allforai/product-map/business-flows.json   必须存在，否则终止
  .allforai/product-map/role-profiles.json     必须存在，否则终止
  .allforai/experience-map/journey-emotion-decisions.json  若存在则加载，跳过已确认项

Step 1: 加载产品地图数据
      读取 role-profiles.json（角色列表）
      读取 business-flows.json（业务流节点）
      ↓
Step 2: 运行 gen_journey_emotion.py 生成初始情绪图
      脚本为每条业务流的每个节点生成默认情绪标注
      默认值：emotion=neutral, intensity=3, risk=low, design_hint=""
      ↓
Step 3: 逐条展示旅程线，用户审阅
      每条旅程线以表格形式展示：
      | 节点 | 角色 | 动作 | emotion | intensity | risk | design_hint |
      用户可逐行调整 emotion / intensity / risk / design_hint
      情绪悬崖检测：相邻节点 intensity 差值 ≥ 4 → 标记 ⚠ WARNING「情绪悬崖：N01→N02 (8→3)」
      → 用户确认当前旅程线
      ↓
Step 4: 记录用户调整到 decision_log
      所有用户修改写入 journey-emotion-decisions.json
      ↓
Step 5: 保存最终 journey-emotion-map.json
      合并脚本初始值 + 用户调整，输出最终文件
```

**核心原则：Step 3 是人工决策点，用户是权威。脚本生成的默认值仅为起点。**

---

### 前置检查

```
检查 .allforai/product-map/business-flows.json：
  存在 → 加载业务流数据
  不存在 → 提示：「请先运行 /product-map 生成功能地图，再运行 /journey-emotion」，终止

检查 .allforai/product-map/role-profiles.json：
  存在 → 加载角色数据
  不存在 → 提示：「请先运行 /product-map 生成功能地图，再运行 /journey-emotion」，终止

检查 .allforai/experience-map/journey-emotion-decisions.json：
  存在 → 加载已有决策，跳过已确认的旅程线
  不存在 → 首次运行，全部旅程线需确认
```

---

### Step 1：加载产品地图数据

读取 `role-profiles.json` 获取角色列表（id / name / description）。
读取 `business-flows.json` 获取所有业务流及其节点。

**输出**：内存中的角色-业务流关联数据，用于 Step 2 脚本输入。

---

### Step 2：运行脚本生成初始情绪图

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_journey_emotion.py <BASE>
```

脚本读取 `business-flows.json`，为每条流的每个节点生成默认情绪标注：

```json
{
  "flow_id": "F001",
  "flow_name": "售后退款流程",
  "journey_nodes": [
    {
      "node_seq": 1,
      "task_ref": "T001",
      "actor": "买家",
      "action": "提交退款申请",
      "emotion": "neutral",
      "intensity": 3,
      "risk": "low",
      "design_hint": ""
    }
  ]
}
```

**emotion 可选值**：`delighted` / `satisfied` / `neutral` / `frustrated` / `anxious` / `angry`

**intensity 范围**：1（最弱）— 5（最强）

**risk 可选值**：`low` / `medium` / `high` / `critical`

---

### Step 3：逐条展示旅程线，用户审阅

对每条旅程线，以可读表格形式展示：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```
旅程线：F001 售后退款流程

| # | 角色 | 动作 | emotion | intensity | risk | design_hint |
|---|------|------|---------|-----------|------|-------------|
| 1 | 买家 | 提交退款申请 | neutral | 3 | low | |
| 2 | 商户 | 收到退款通知 | neutral | 3 | low | |
| 3 | 商户 | 审核退款申请 | neutral | 3 | low | |
| 4 | 买家 | 查看退款结果 | neutral | 3 | low | |
```

**用户确认**：请审阅每个节点的情绪标注，根据实际业务场景调整：

- **emotion**：用户在此节点的真实情绪是什么？（例：等待退款结果时用户通常是 anxious 而非 neutral）
- **intensity**：情绪强度是否准确？（例：被拒绝退款时 intensity 应为 4-5）
- **risk**：此节点是否存在流失/投诉风险？（例：审核超时节点 risk 应为 high）
- **design_hint**：针对该情绪/风险，有什么设计建议？（例：「增加进度条缓解焦虑」「超时自动提醒」）

**情绪悬崖检测**：展示表格后，检查相邻节点 intensity 差值。差值 ≥ 4 时标记 WARNING：

```
⚠ 情绪悬崖：节点 3→4 intensity 从 8 骤降到 3，体验可能断裂。请确认是否合理或需调整中间节点。
```

逐条旅程线确认，确认后进入下一条。

---

### Step 4：记录用户调整到 decision_log

所有用户修改写入 `journey-emotion-decisions.json`：

```json
[
  {
    "step": "Step 3",
    "flow_id": "F001",
    "flow_name": "售后退款流程",
    "node_seq": 4,
    "field": "emotion",
    "original_value": "neutral",
    "new_value": "anxious",
    "decision": "modified",
    "reason": "用户等待退款结果时通常焦虑",
    "decided_at": "2026-03-07T10:30:00Z"
  }
]
```

**加载逻辑**：每次运行 Step 3 前检查 decisions.json，已 `confirmed` 的旅程线跳过确认直接沿用。`/journey-emotion refresh` 清空缓存重跑。

---

### Step 5：保存最终 journey-emotion-map.json

合并脚本初始值与用户调整，输出最终文件：

```json
{
  "version": "1.0.0",
  "generated_at": "...",
  "summary": {
    "flow_count": 5,
    "total_nodes": 28,
    "high_risk_nodes": 4,
    "negative_emotion_nodes": 8,
    "human_reviewed": true
  },
  "journeys": [
    {
      "flow_id": "F001",
      "flow_name": "售后退款流程",
      "journey_nodes": [
        {
          "node_seq": 1,
          "task_ref": "T001",
          "actor": "买家",
          "action": "提交退款申请",
          "emotion": "frustrated",
          "intensity": 4,
          "risk": "medium",
          "design_hint": "简化退款表单，减少用户填写负担"
        }
      ]
    }
  ],
  "decision_log_ref": "journey-emotion-decisions.json"
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
| **Step 3 旅程线审阅** | 逐条展示，AskUserQuestion 确认 | 自动确认，记入 decisions.json（`decision: "auto_confirmed"`） |

**安全护栏**（自动模式下仍然停下来问用户）：
- ERROR 级验证失败（business-flows.json 解析失败、节点引用断裂）
- **risk=critical 节点**：旅程线中含 `risk: "critical"` 的节点时，该旅程线必须停下展示并 AskUserQuestion 确认，不可 auto_confirmed（critical 节点涉及支付/删除/权限变更，情绪误判会级联传播到 micro-interactions 和设计约束）

---

## 输出文件结构

```
.allforai/experience-map/
├── journey-emotion-map.json          # 机器可读：完整旅程情绪图
└── journey-emotion-decisions.json    # 用户决策日志（增量复用）
```

---

## 防御性规范

### 加载校验
- **`business-flows.json`**：前置加载时验证 JSON 合法性。解析失败 → 提示用户重新运行 `/product-map`，终止执行。
- **`role-profiles.json`**：前置加载时验证 JSON 合法性。解析失败 → 提示用户重新运行 `/product-map`，终止执行。
- **`journey-emotion-decisions.json`**：加载时验证 JSON 合法性。解析失败 → 检查 `.bak` → 提示恢复或重新运行 `/journey-emotion refresh`。

### 零结果处理
- **business-flows.json 无业务流**：提示「功能地图中未定义业务流，请先运行 /product-map 补充 business-flows」，终止。
- **某业务流节点为空**：标注警告「流 {flow_id} ({flow_name}) 无节点定义，已跳过」，不静默跳过。

### 上游过期检测
- **`business-flows.json`**：加载时比较 `generated_at` 与 `journey-emotion-decisions.json` 最新 `decided_at`。上游更新 → 警告「business-flows 在 journey-emotion 上次运行后被更新，建议重新运行 /journey-emotion refresh」。
- 仅警告不阻断。

---

## 3 条铁律

### 1. 人工确认是必要步骤

脚本生成的默认值（neutral / intensity=3）仅为起点。情绪标注高度依赖业务上下文，必须经用户审阅调整后才可用于下游 experience-map。自动模式除外。

### 2. 以功能地图为唯一数据源

只从 business-flows.json 和 role-profiles.json 推导旅程节点，不引入两者之外的流程。发现遗漏流程，先更新 product-map，再重跑 journey-emotion。

### 3. 只标注不执行

journey-emotion 只输出情绪标注数据，不触发任何设计变更或代码生成。设计决策由下游 experience-map 和 ui-design 负责。
