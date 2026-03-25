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

> 详见 ./docs/schemas/journey-emotion-schema.md

---

## 定位

```
product-map（功能地图）    journey-emotion（旅程情绪图）    experience-map（体验地图）
谁用？做什么？流程如何？    每个节点的情绪、风险、设计提示    汇总为完整体验地图
任务层 + 流程层语义        情绪层语义（人工确认）            体验层语义
```

**前提**：必须先执行 `product-map`，生成 `.allforai/product-map/business-flows.json` 和 `.allforai/product-map/role-profiles.json`。

**关键原则**：**本步骤要求人工确认后才能继续进入 experience-map。** LLM 生成的情绪标注基于语义推理，但用户最了解实际业务场景，审阅确认后才可用于下游。

---

## 快速开始

```
/journey-emotion           # 完整流程（Step 1-5）
/journey-emotion refresh   # 清空决策缓存，从头重新执行
```

---

## 增强协议（网络搜索 + 4D+6V + XV）

> 详见 `./docs/skill-commons.md`「统一验收方法论」。

**网络搜索**：Step 2 生成情绪标注时，对 risk=high/critical 节点搜索同类产品的用户体验研究，作为情绪推理的 D2 证据（如搜索「payment anxiety UX research」「form abandonment rate」），结果写入 `source_refs`。

**4D+6V 重点**：每个 emotion_node 附带 `source_refs`（D2 证据来源）和 `reasoning`（D4 为什么是这个情绪而非其他）；risk=high/critical 节点覆盖至少 4/6 视角（user 体验如何？business 会流失吗？tech 有超时风险吗？ux 有缓解方案吗？data 能监测情绪信号吗？risk 有合规问题吗？）。

**XV**（可选）：将情绪标注摘要发送给第二个模型独立评审，重点审查 intensity 分布是否合理（不应全部集中在 3-5 的安全区间）。

---

## 下游基线定义

> 详见 `./docs/skill-commons.md`「上游基线验收」。

journey-emotion 的产出同时是 experience-map 的**验收基线**。experience-map 生成后，LLM 加载 journey-emotion-map.json 作为上下文，**以 LLM 判断力（而非机械规则）**审查下游产物是否忠实反映了情绪意图。

**LLM 验收视角**（experience-map 的 Step 3 验收 Loop 中执行）：

LLM 同时持有两份数据 — journey-emotion-map.json（情绪基线）和 experience-map.json（设计产物），逐条操作线对照审查：

1. **情绪意图落地了吗？** — 每个 emotion_node 的 design_hint 是否在对应 screen 的 `emotion_design` 和 `interaction_pattern` 中有实质性体现？不是照抄文字，而是判断设计是否回应了情绪需求
2. **高风险节点有保护吗？** — risk=high/critical 的节点，对应 screen 的设计是否考虑了防错、确认、可逆性？
3. **情绪弧线连贯吗？** — 操作线中情绪从 anxious → delighted 的变化，是否在界面序列中有对应的体验递进？还是所有界面千篇一律？
4. **旅程线完整吗？** — 每条 journey_line 在 experience-map 中有对应的 operation_line 吗？

**不通过 → LLM 修正对应 screen → 重新验收（Loop）**

**这意味着**：journey-emotion 的质量直接决定 experience-map 验收的精度。情绪标注越具体，下游验收越能发现「设计未回应情绪需求」的问题。反过来，如果情绪标注全是 neutral/intensity=3，验收就失去了基线，等于没验。

---

## 生成方式

LLM 直接分析业务流节点，理解每个步骤的用户心理状态后标注情绪。情绪推理需要理解场景语境（如"支付"常伴随焦虑，"完成学习"带来满足感），这是 LLM 的语义理解能力，不适合用规则脚本。

**跨角色流拆分规则**：每条 journey_line 属于单一角色（`role` 字段为单值）。当业务流类型为 `cross_role` 时，按参与角色拆分为多条 journey_line，每条只包含该角色作为 actor 的节点。例如 F001（R2 生成→R2 审核→R2 发布→R1 浏览）拆为：
- JL01a (role=R2, source_flow=F001): 生成→审核→发布
- JL01b (role=R1, source_flow=F001): 浏览新场景包

拆分后各线独立评估情绪弧线和 Peak-End Rule。`source_flow` 相同但 `role` 不同，下游可按 `source_flow` 关联回原始跨角色流。

**输出 schema 约束**（详见 `docs/schemas/journey-emotion-schema.md`）：
- 顶层 key 必须是 `journey_lines`（数组）
- 子节点 key 必须是 `emotion_nodes`（数组）
- 每个 journey_line 必须有 `source_flow` 字段
- 每条 journey_line 的所有 emotion_nodes 必须属于同一角色（与 `role` 字段一致）
- 情绪值应基于场景语境推理，不应全部为 neutral

---

## 工作流

```
前置检查：
  .allforai/product-concept/concept-baseline.json  自动加载（推拉协议 §三.A）→ 不存在则 WARNING，不阻塞
  .allforai/product-map/business-flows.json   必须存在，否则终止
  .allforai/product-map/role-profiles.json     必须存在，否则终止
  .allforai/experience-map/journey-emotion-decisions.json  若存在则加载，跳过已确认项

Step 1: 加载产品地图数据
      读取 concept-baseline.json（产品定位、角色、治理风格 — 背景知识）
      读取 role-profiles.json（角色列表）
      读取 business-flows.json（业务流节点）
      ↓
Step 2: LLM 分析业务流节点，生成情绪标注
      LLM 理解每个节点的场景语境，推理用户情绪
      输出：每个节点的 emotion / intensity / risk / design_hint
      ↓
Step 2.5: LLM 自审验证（Loop）
      LLM 切换为审查者视角，用上游基线（business-flows）+ 4D+6V + 闭环 审查
      不通过 → 修正 → 重审（最多 3 轮）
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
  不存在 → 提示：「请先执行 product-map 工作流生成功能地图，再执行 journey-emotion 工作流」，终止

检查 .allforai/product-map/role-profiles.json：
  存在 → 加载角色数据
  不存在 → 提示：「请先执行 product-map 工作流生成功能地图，再执行 journey-emotion 工作流」，终止

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

### Step 2：LLM 分析业务流节点，生成情绪标注

LLM 逐条业务流分析，为每个节点推理情绪标注。**不使用默认值填充**，而是根据场景语境判断：

**推理维度**：
- **动作本身的心理负荷**：填表→中性、支付→焦虑、完成学习→满足、等待审核→焦虑
- **角色的使用频率**：高频操作应更流畅（低焦虑），低频操作允许更多引导
- **业务流中的位置**：开头通常中性、高潮（核心价值交付）通常愉悦、结尾需要正向闭合
- **风险等级**：涉及金钱/数据删除/权限变更 → risk 升高
- **design_hint**：针对情绪给出具体设计建议（不留空）

**输出结构**：

```json
{
  "id": "JL01",
  "name": "场景化学习链路",
  "role": "R1",
  "source_flow": "F002",
  "emotion_nodes": [
    {
      "step": 1,
      "action": "浏览场景包列表",
      "emotion": "neutral",
      "intensity": 4,
      "risk": "medium",
      "design_hint": "场景包数量多时易迷失，按场景类型分类+个性化推荐减少决策疲劳"
    }
  ]
}
```

**emotion 可选值**：`delighted` / `satisfied` / `neutral` / `frustrated` / `anxious` / `angry`

**intensity 范围**：1（最弱）— 8（最强）

**risk 可选值**：`low` / `medium` / `high` / `critical`

**design_hint**：必填，1-2 句话，说明针对该情绪的具体设计策略

---

### Step 2.5：LLM 自审验证（Loop）

LLM 生成情绪标注后，切换到审查者视角，用上游基线 + 4D/6V/闭环 审查自己的产出。**所有验证逻辑由 LLM 判断，不是规则匹配。**

**上游基线对照**（用 business-flows.json 验证 journey-emotion）：

LLM 同时持有 business-flows.json（上游）和刚生成的情绪标注（当前产出），对照审查：

1. **覆盖完整性** — 每条业务流的每个节点都有情绪标注吗？有没有遗漏的节点？
2. **角色一致性** — 情绪标注的角色与业务流节点的角色匹配吗？
3. **流程语境匹配** — 情绪推理是否考虑了节点在业务流中的位置（开头/高潮/收尾）？
4. **independent_operations 覆盖** — business-flows 中不在任何流内的独立任务，是否也有对应旅程线？

**4D 追问**（对每条旅程线）：

- **D1 结论**：这条旅程线的情绪弧线整体合理吗？是否有「全 neutral」或「全 anxious」的单调分布？
- **D2 证据**：risk=high/critical 的标注有场景依据吗？还是随意赋值？（网络搜索同类场景的用户研究补充证据）
- **D3 约束**：是否遗漏了该业务场景的特殊约束（如法规要求、支付合规、数据隐私）？
- **D4 决策**：为什么选择这个 emotion 而非其他？（如「选 anxious 而非 frustrated」的理由）

**6V 审查**（对 risk=high/critical 节点重点审查）：

LLM 从 6 个视角审视该节点的情绪标注是否全面：
- user：用户真实感受是什么？
- business：此节点情绪问题会导致流失/投诉吗？
- tech：是否存在技术层面的等待/超时导致情绪恶化？
- ux：有缓解该情绪的交互手段吗？design_hint 是否具体可落地？
- data：能通过什么数据指标监测此节点的用户情绪？
- risk：是否存在安全/合规风险加剧情绪？

**闭环审计**：

| 闭环类型 | 追问 |
|---------|------|
| **映射闭环** | 每个 negative emotion（anxious/frustrated/angry）是否有对应的 design_hint 缓解方案？有负面就要有缓解 |
| **导航闭环** | 情绪弧线是否有正向闭合？旅程线不应以 anxious/frustrated 结尾（除非业务本身如此） |
| **异常闭环** | 业务流中有异常分支（拒绝/失败/超时）的节点，是否标注了对应的负面情绪和 design_hint？ |

**Loop 机制**：

```
LLM 生成情绪标注 → 自审验证
  全部通过 → Step 3
  有问题 →
    列出具体问题（哪些节点标注不合理、哪些闭环断裂）
    LLM 修正对应节点
    → 重新自审（最多 3 轮）
  3 轮后仍不通过 → 记录剩余问题，WARNING 继续到 Step 3（人工审阅可弥补）
```

---

### Step 3：逐条展示旅程线，用户审阅

对每条旅程线，以可读表格形式展示：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```
旅程线：F001 异常处理流程

| # | 角色 | 动作 | emotion | intensity | risk | design_hint |
|---|------|------|---------|-----------|------|-------------|
| 1 | 用户 | 提交撤销申请 | neutral | 3 | low | |
| 2 | 管理员 | 收到撤销通知 | neutral | 3 | low | |
| 3 | 管理员 | 审核撤销申请 | neutral | 3 | low | |
| 4 | 用户 | 查看撤销结果 | neutral | 3 | low | |
```

**用户确认**：请审阅每个节点的情绪标注，根据实际业务场景调整：

- **emotion**：用户在此节点的真实情绪是什么？（例：等待撤销结果时用户通常是 anxious 而非 neutral）
- **intensity**：情绪强度是否准确？（例：被拒绝撤销时 intensity 应为 4-5）
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
    "flow_name": "异常处理流程",
    "node_seq": 4,
    "field": "emotion",
    "original_value": "neutral",
    "new_value": "anxious",
    "decision": "modified",
    "reason": "用户等待撤销结果时通常焦虑",
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
  "journey_lines": [
    {
      "id": "JL01",
      "name": "异常处理流程",
      "role": "R001",
      "source_flow": "F001",
      "emotion_nodes": [
        {
          "step": 1,
          "action": "提交撤销申请",
          "role": "R001",
          "emotion": "frustrated",
          "intensity": 4,
          "risk": "medium",
          "design_hint": "简化撤销表单，减少用户填写负担"
        }
      ],
      "human_decision": true
    }
  ],
  "decision_log": [],
  "generated_at": "..."
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
| **Step 3 旅程线审阅** | 逐条展示，向用户确认 | 自动确认，记入 decisions.json（`decision: "auto_confirmed"`） |

**安全护栏**（自动模式下仍然停下来问用户）：
- ERROR 级验证失败（business-flows.json 解析失败、节点引用断裂）
- **risk=critical 节点**：旅程线中含 `risk: "critical"` 的节点时，该旅程线必须停下展示并 向用户确认，不可 auto_confirmed（critical 节点涉及支付/删除/权限变更，情绪误判会级联传播到 micro-interactions 和设计约束）

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

### 执行失败保护

- 任何步骤遇到不可恢复错误 → 写入 `.allforai/experience-map/journey-emotion-error.json`，包含 `{"error": "...", "step": "...", "timestamp": "..."}`。

### 零结果处理
- **business-flows.json 无业务流**：提示「功能地图中未定义业务流，请先执行 product-map 工作流 补充 business-flows」，终止。
- **某业务流节点为空**：标注警告「流 {flow_id} ({flow_name}) 无节点定义，已跳过」，不静默跳过。

### 上游过期检测
- **`business-flows.json`**：加载时比较 `generated_at` 与 `journey-emotion-decisions.json` 最新 `decided_at`。上游更新 → 警告「business-flows 在 journey-emotion 上次运行后被更新，建议重新执行 journey-emotion 工作流 refresh」。
- 仅警告不阻断。

---

## 3 条铁律

### 1. 人工确认是必要步骤

LLM 的情绪推理基于语义理解，但情绪标注高度依赖业务上下文，必须经用户审阅调整后才可用于下游 experience-map。自动模式除外。

### 2. 以功能地图为唯一数据源

只从 business-flows.json 和 role-profiles.json 推导旅程节点，不引入两者之外的流程。发现遗漏流程，先更新 product-map，再重跑 journey-emotion。

### 3. 只标注不执行

journey-emotion 只输出情绪标注数据，不触发任何设计变更或代码生成。设计决策由下游 experience-map 和 ui-design 负责。
