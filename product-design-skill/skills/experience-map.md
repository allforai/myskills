---
name: experience-map
description: >
  Phase 4 — Experience Map Generation. Use when the user asks to "generate experience map",
  "map experience", "operation lines", "experience-map", "体验地图", "操作线",
  "体验线路", "节点屏幕", "operation line mapping",
  or mentions generating operation lines from journey emotions,
  mapping nodes to screens, building experience maps from journey-emotion-map.
  Replaces the former screen-map skill with a richer experience-oriented structure.
  Requires journey-emotion and product-map to have been run first.
version: "1.0.0"
---

# Experience Map — 体验地图

> 以旅程情绪图和任务清单为输入，生成操作线 > 节点 > 屏幕的完整体验地图

## 目标

以 `journey-emotion-map.json`（必须）和 `task-inventory.json`（必须）为输入，生成体验地图：

- **JSON 机器版**：完整字段，operation_lines > nodes > screens 三层结构，供下游 ui-design 和自动化使用
- **Markdown 人类版**：以可读摘要形式展示操作线、节点、屏幕统计

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/schemas/experience-map-schema.md

---

## 定位

```
journey-emotion（旅程情绪图）    experience-map（体验地图）       ui-design（界面设计）
每个节点的情绪、风险、设计提示    操作线 > 节点 > 屏幕结构          基于体验地图生成设计规格
情绪层语义（人工确认）           体验层语义（结构化映射）           视觉层语义
```

**前提**：必须先运行 `journey-emotion`，生成 `.allforai/experience-map/journey-emotion-map.json`；必须先运行 `product-map`，生成 `.allforai/product-map/task-inventory.json`。

---

## 快速开始

```
/experience-map              # 完整流程（Step 1-5）
/experience-map refresh      # 清空缓存，从头重新运行
/experience-map --variants 3    # 生成 3 套信息架构方案，对比后选择
```

**参数**：
- `--variants N`：生成 N 套不同的信息架构方案（默认 1，最大 5）。N ≥ 2 时进入 variants 模式。

---

## 生成方式

LLM 直接分析 journey-emotion-map + task-inventory，理解交互场景语境后设计屏幕结构。

可选辅助脚本：`${CLAUDE_PLUGIN_ROOT}/scripts/gen_experience_map.py`（用于机械映射基础结构，LLM 可在其输出上增强）。

**输出 schema 约束**（详见 `docs/schemas/experience-map-schema.md`）：
- 顶层 key 必须是 `operation_lines`（数组）+ `screen_index`（对象）
- 每个 operation_line 包含 `id`、`name`、`source_journey`、`role`、`nodes`
- 每个 node 包含 `seq`、`id`、`action`、`screens`（screen 对象数组）
- 每个 screen 包含 `id`、`name`、`interaction_type`、`tasks`、`actions`、`vo_actions`、`data_fields`

---

## 工作流

```
前置检查：
  .allforai/experience-map/journey-emotion-map.json   必须存在，否则终止
  .allforai/product-map/task-inventory.json            必须存在，否则终止
  .allforai/product-map/role-profiles.json             可选加载（角色信息增强）
  .allforai/product-map/business-flows.json            可选加载（业务流增强）

Step 1: 加载前置数据
      读取 journey-emotion-map.json（旅程情绪图）
      读取 task-inventory.json（任务清单）
      读取 role-profiles.json（角色列表，可选）
      读取 business-flows.json（业务流，可选）
      ↓
Step 2: 生成体验地图
      LLM 从旅程情绪图提取操作线，理解交互语境后映射任务到节点和屏幕
      生成 operation_lines > nodes > screens 三层结构（可选用辅助脚本加速基础映射）
      ↓
Step 3: 向用户展示结果摘要，用户审阅
      展示操作线列表、节点数、屏幕数统计
      用户可调整操作线分组、节点归属、屏幕命名
      → 用户确认
      ↓
Step 4: 自动触发 interaction-quality-gate（Phase 4.5）
      体验地图生成完毕后，自动调用 interaction-quality-gate 技能
      执行交互质量检查
      ↓
Step 5: 输出 experience-map-report.md
      汇总体验地图数据，生成人类可读报告
```

**核心原则：Step 3 结束有用户确认，用户是权威。**

---

### 前置检查

```
检查 .allforai/experience-map/journey-emotion-map.json：
  存在 → 加载旅程情绪图数据
  不存在 → 提示：「请先运行 /journey-emotion 生成旅程情绪图，再运行 /experience-map」，终止

检查 .allforai/product-map/task-inventory.json：
  存在 → 加载任务清单数据
  不存在 → 提示：「请先运行 /product-map 生成任务清单，再运行 /experience-map」，终止

检查 .allforai/product-map/role-profiles.json：
  存在 → 加载角色数据（增强操作线的角色信息）
  不存在 → 跳过，不影响主流程

检查 .allforai/product-map/business-flows.json：
  存在 → 加载业务流数据（增强操作线的流程上下文）
  不存在 → 跳过，不影响主流程

检查 .allforai/product-map/view-objects.json：
  存在 → 加载 VO 数据（绑定真实字段，优先于任务名推导）
  不存在 → 跳过，回退到任务名推导（向后兼容）

检查 .allforai/product-map/entity-model.json：
  存在 → 加载实体数据（增强屏幕名称和交互类型推导）
  不存在 → 跳过，不影响主流程
```

---

### Step 1：加载前置数据

读取 `journey-emotion-map.json` 获取旅程情绪图（旅程线、节点、情绪标注）。
读取 `task-inventory.json` 获取任务清单（任务 ID、名称、CRUD 类型、模块归属）。
可选读取 `role-profiles.json`（角色列表）和 `business-flows.json`（业务流）。
可选读取 `view-objects.json`（视图对象，优先使用 VO 绑定真实字段）
可选读取 `entity-model.json`（实体模型）

**输出**：内存中的旅程-任务关联数据，用于 Step 2 脚本输入。

---

### Step 2：运行脚本生成体验地图

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_experience_map.py <BASE>
```

脚本读取 `journey-emotion-map.json` 和 `task-inventory.json`，生成 operation_lines > nodes > screens 三层结构。
每个屏幕自动推导 `implementation_contract`（pattern + forbidden + required_behaviors），确保设计意图传递到代码层。

当 view-objects.json 存在时，脚本优先使用 VO 数据绑定屏幕字段（名称、交互类型、数据字段、操作按钮），
无 VO 时回退到任务名推导（向后兼容）。

```json
{
  "version": "1.0.0",
  "generated_at": "...",
  "summary": {
    "operation_line_count": 5,
    "total_nodes": 18,
    "total_screens": 32,
    "high_risk_nodes": 4,
    "negative_emotion_nodes": 6
  },
  "operation_lines": [
    {
      "line_id": "OL001",
      "line_name": "售后退款操作线",
      "flow_ref": "F001",
      "actor": "买家",
      "nodes": [
        {
          "node_id": "N001",
          "node_seq": 1,
          "task_ref": "T001",
          "action": "提交退款申请",
          "emotion": "frustrated",
          "intensity": 4,
          "risk": "medium",
          "design_hint": "简化退款表单，减少用户填写负担",
          "screens": [
            {
              "screen_id": "S001",
              "screen_name": "退款申请页",
              "purpose": "用户填写退款原因和上传凭证",
              "interaction_type": "MG3-L",
              "vo_ref": "VO001",
              "api_ref": "API001",
              "data_fields": ["refund_reason", "evidence_images", "order_id"],
              "flow_context": {"prev": ["S000"], "next": ["S002"], "entry_points": ["订单详情"], "exit_points": ["退款进度"]},
              "states": {"empty": "暂无退款记录", "loading": "加载中...", "error": "提交失败，请重试", "success": "退款申请已提交"}
            }
          ]
        }
      ]
    }
  ]
}
```

---

### Step 3：向用户展示结果摘要，用户审阅

以可读形式展示体验地图摘要：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 journey-emotion-map 分析结果决定，不限行业。

```
体验地图摘要

操作线 5 条 · 节点 18 个 · 屏幕 32 个
高风险节点 4 个 · 负面情绪节点 6 个

操作线列表：
| # | 操作线 | 角色 | 节点数 | 屏幕数 | 高风险 | 负面情绪 |
|---|--------|------|--------|--------|--------|----------|
| 1 | 售后退款操作线 | 买家 | 4 | 8 | 1 | 2 |
| 2 | 订单管理操作线 | 商户 | 5 | 10 | 2 | 1 |
| 3 | ... | ... | ... | ... | ... | ... |
```

**用户确认**：请审阅操作线划分是否合理，节点-屏幕映射是否完整。

---

### Step 4：自动触发 interaction-quality-gate

体验地图生成并经用户确认后，自动调用 `interaction-quality-gate`（Phase 4.5）执行交互质量检查。

---

### Step 5：输出 experience-map-report.md

汇总体验地图数据，生成人类可读报告：

```
# 体验地图报告

操作线 X 条 · 节点 X 个 · 屏幕 X 个
高风险节点 X 个 · 负面情绪节点 X 个

## 操作线总览
（按操作线展示节点和屏幕摘要）

## 高风险节点
（列出所有 risk=high/critical 的节点及其设计提示）

## 负面情绪节点
（列出所有 emotion 为 frustrated/anxious/angry 的节点）

> 完整数据见 .allforai/experience-map/experience-map.json
```

输出：`.allforai/experience-map/experience-map-report.md`

---

### Variants 模式（--variants N）

当指定 `--variants N`（N ≥ 2）时，生成 N 套不同的信息架构方案：

**Step 2v: 多方案发散**
- 每套方案采用不同的信息架构策略：
  - 方案 A：任务驱动型（按用户任务组织界面）
  - 方案 B：对象驱动型（按数据实体组织界面）
  - 方案 C：流程驱动型（按业务流程组织界面）
  - 方案 D：角色驱动型（按角色工作台组织界面）
  - 方案 E：混合型（高频任务前置 + 对象导航）
- 使用 Agent 并发生成 N 套 experience-map
- 每套方案输出到 `.allforai/experience-map/variants/variant-{n}/`

**Step 2v.1: 对抗式评审**
- 如果 OPENROUTER_API_KEY 可用，使用 ask_model 从 5 个视角评审每套方案：
  - 用户视角：新手能否快速上手？
  - 效率视角：高频操作路径是否最短？
  - 扩展视角：新功能加入时架构是否稳定？
  - 一致性视角：跨角色体验是否统一？
  - 认知视角：信息层级是否符合心智模型？
- 输出对比矩阵 + 推荐方案

**Step 2v.2: 用户选择**
- AskUserQuestion 展示对比矩阵
- 用户选择一个方案（或混合多方案优点）
- 选中方案复制到 `.allforai/experience-map/` 主目录
- 记录选择到 experience-map-decisions.json

---

## 全自动模式

**激活条件**（同时满足）：
1. `.allforai/product-concept/product-concept.json` 存在且含 `pipeline_preferences` 字段
2. 上下文含 `__orchestrator_auto: true`（由 `/product-design full` 编排器传入）

**未同时满足** → 保持标准交互模式（当前行为不变）。

**行为变化**：

| 步骤 | 标准模式 | 全自动模式 |
|------|----------|-----------|
| **Step 3 结果审阅** | AskUserQuestion 确认 | 自动确认，记入 decisions.json（`decision: "auto_confirmed"`） |
| **--variants 模式** | 生成 N 套方案 → 对抗式评审 → 用户选择 | 自动选择推荐方案（评审得分最高），记入 decisions.json |

**安全护栏**（自动模式下仍然停下来问用户）：
- ERROR 级验证失败（journey-emotion-map.json 解析失败、task_refs 引用断裂）

---

## 输出文件结构

```
.allforai/experience-map/
├── experience-map.json              # 机器可读：操作线 > 节点 > 屏幕完整结构（含 implementation_contract）
├── experience-map-report.md         # 人类可读：体验地图摘要报告
├── experience-map-decisions.json    # variants 模式选择记录
├── journey-emotion-map.json         # 上游输入（由 journey-emotion 生成）
├── journey-emotion-decisions.json   # 上游输入（由 journey-emotion 生成）
├── variants/                        # --variants 模式
│   ├── variant-1/                   # 方案 A
│   │   └── experience-map.json
│   ├── variant-2/                   # 方案 B
│   │   └── experience-map.json
│   └── comparison-matrix.json       # 对比矩阵 + 评审结果
```

---

## 防御性规范

### 加载校验
- **`journey-emotion-map.json`**：前置加载时验证 JSON 合法性。解析失败 → 提示用户重新运行 `/journey-emotion`，终止执行。
- **`task-inventory.json`**：前置加载时验证 JSON 合法性。解析失败 → 提示用户重新运行 `/product-map`，终止执行。

### 零结果处理
- **journey-emotion-map.json 无旅程线**：提示「旅程情绪图中未定义任何旅程线，请先运行 /journey-emotion 补充旅程数据」，终止。
- **生成 0 个操作线**：标注警告「未能从旅程情绪图生成任何操作线，请检查 journey-emotion-map.json 数据完整性」，终止。

### 上游过期检测
- **`journey-emotion-map.json`**：加载时比较 `generated_at` 与已有 `experience-map.json` 的 `generated_at`。上游更新 → 警告「journey-emotion-map 在 experience-map 上次运行后被更新，建议重新运行 /experience-map refresh」。
- 仅警告不阻断。

---

## 3 条铁律

### 1. 以旅程情绪图为核心输入

操作线的划分和节点的情绪/风险标注来自 journey-emotion-map.json，不凭空创造。发现遗漏旅程线，先更新 journey-emotion，再重跑 experience-map。

### 2. 三层结构严格对齐

operation_lines > nodes > screens 三层结构必须完整对齐。每个操作线至少有一个节点，每个节点至少有一个屏幕。不允许空操作线或空节点。

### 3. 只生成不设计

experience-map 只输出体验结构数据，不触发任何设计变更或代码生成。屏幕的具体设计由下游 ui-design 负责。
