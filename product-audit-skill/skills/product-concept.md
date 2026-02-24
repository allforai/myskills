---
name: product-concept
description: >
  Use when the user wants to "define a product concept", "start a new product from scratch",
  "figure out what to build", "validate a product idea", "产品概念", "产品定义",
  "我想做一个...", "这个产品应该怎么设计",
  or needs to discover what product to build before writing code.
version: "1.0.0"
---

# Product Concept — 产品概念发现

> 从模糊想法到结构化产品概念：搜索 + 选择题引导，帮你发现心中的产品

## 目标

帮用户发现心中的产品：从模糊想法 → 结构化产品概念，通过搜索 + 选择题引导：

1. **锁定问题** — 你要帮什么人解决什么问题？
2. **定义角色与价值** — 谁用？他们得到什么？
3. **理清商业模式** — 怎么活下去？
4. **结晶输出** — 生成可被 product-map 消费的产品概念文档

---

## 定位

```
product-concept（战略层）        product-map（运营层）
帮什么人解决什么问题？            产品有什么功能？任务是否完整？
从问题推导，或从代码反推          从代码读现状
输出产品概念文档                  输出产品地图
```

**product-concept 是纯被依赖方**，只负责生成自己的输出文件到 `.allforai/product-concept/`。product-map 或其他下游技能如果需要参考产品概念，由它们自己决定是否读取。

---

## 双向运作模式

| 模式 | 触发条件 | 流程 |
|------|----------|------|
| **发现模式**（forward） | 无代码，或用户主动触发 | Step 0→1→2→3 完整引导发现 |
| **提炼模式**（reverse） | 有代码，或已有 product-map | 从代码/product-map 反推 → 搜索验证 → 提炼概念 |

---

## 核心交互模式 — 搜索驱动的选择题

每个 Step 遵循循环：

```
用户输入（可以很模糊）
  → WebSearch 搜索互联网
  → 找到相关产品 / 商业模式 / 行业文章
  → 提炼为 2-4 个 AskUserQuestion 选择题
  → 用户选择
  → 范围缩小，进入下一轮或下一 Step
```

**铁律：不问开放题，只问选择题。** 所有问题都基于搜索结果生成选项，用户只需选择。如果现有选项都不对，用户可以用"其他"自由输入，AI 再基于新输入搜索并生成新选择题。

---

## 快速开始

```
/product-concept              # 发现模式（Step 0→1→2→3）
/product-concept full         # 同上
/product-concept reverse      # 提炼模式（从现有代码/地图反推）
```

---

## 工作流 — 发现模式（4 Step）

### Step 0: 破题 — 锁定问题域

输入：用户的一句话描述（可以很模糊）

1. **WebSearch 搜索**相关行业、产品、竞品
2. 找到 3-5 个最相关的现有产品
3. **AskUserQuestion** 选择题：
   - "你的想法更接近哪个产品？"（列出搜索到的竞品，附简要描述）
   - "哪些特点是你想要的？"（从竞品中提取差异化特征）
   - "你要解决的 TOP 3 问题是什么？"（基于行业痛点生成选项）
4. 输出：`problem-domain.json`（问题域、初步竞品列表、TOP 3 问题）
5. → 用户确认

---

### Step 1: 角色与价值 — 谁用？他们得到什么？

输入：Step 0 锁定的方向

1. **WebSearch 搜索**该类产品的典型用户构成
2. 基于搜索结果 + JTBD/VPC 框架，推导角色列表
3. **AskUserQuestion** 选择题：
   - "这些角色里哪些是你的目标用户？"（多选）
   - 对每个选中角色："这个角色最痛的问题是哪些？"（基于行业搜索生成选项）
   - "这个角色使用你的产品后能获得什么？"（Gains 选项）
4. 结构化为 VPC 格式：每角色的 Jobs / Pains / Gains → Pain Relievers / Gain Creators
5. 输出：`role-value-map.json`
6. → 用户确认

---

### Step 2: 商业模式 — 怎么活下去？

输入：Step 0-1 的确认结果

1. **WebSearch 搜索**该行业主流商业模式
2. **AskUserQuestion** 选择题：
   - "收费模式？"（订阅/按量/免费增值/一次性/平台抽成...基于行业搜索）
   - "你的核心竞争力是什么？"（基于竞品分析生成差异化选项）
   - "成功的关键指标是什么？"（基于行业标准生成选项）
3. 用 Lean Canvas 结构化：Revenue / Cost / Key Metrics / Unfair Advantage / Channels
4. 输出：`business-model.json`
5. → 用户确认

---

### Step 3: 概念结晶 — 输出产品概念文档

输入：Step 0-2 的所有确认结果

1. 综合生成结构化产品概念
2. 生成 ERRC 竞品定位矩阵（基于 Step 0 的竞品 + Step 1 的价值差异）
3. 生成一句话产品使命
4. 输出：
   - `product-concept.json` — 机器可读，供 product-map 消费
   - `product-concept-report.md` — 人类可读报告
   - `concept-decisions.json` — 决策日志（增量复用）
5. → 用户确认最终文档

---

## 工作流 — 提炼模式（3 Step）

### Step 0: 代码/地图读取

- 如果有 `product-map.json` → 直接读取角色、任务、竞品信息
- 如果只有代码 → 快速扫描路由/权限/菜单，提取角色和功能模块
- 输出：从现状反推的初步概念草稿

### Step 1: 搜索验证

- 基于反推结果 **WebSearch 搜索**竞品和行业趋势
- **AskUserQuestion**：验证反推的问题域、角色、价值是否准确
- 补充商业模式层（代码中通常没有）

### Step 2: 概念结晶

- 同发现模式 Step 3

---

## 输出 JSON Schema

### `product-concept.json`

```json
{
  "version": "1.0.0",
  "mode": "forward | reverse",
  "mission": "一句话产品使命",
  "top_problems": [
    {
      "id": "P1",
      "description": "问题描述",
      "severity": "critical | high | medium",
      "current_alternatives": "用户现在怎么解决这个问题",
      "evidence": "搜索来源 URL"
    }
  ],
  "roles": [
    {
      "role_id": "R1",
      "role_name": "角色名",
      "jobs": [{ "type": "functional | emotional | social", "description": "..." }],
      "pains": ["痛点1", "痛点2"],
      "gains": ["期望收益1", "期望收益2"],
      "pain_relievers": ["产品如何缓解痛点"],
      "gain_creators": ["产品如何创造收益"]
    }
  ],
  "business_model": {
    "revenue_streams": ["收入来源"],
    "cost_structure": ["成本结构"],
    "channels": ["获客渠道"],
    "key_metrics": ["关键指标"],
    "unfair_advantage": "不可复制优势"
  },
  "competitive_position": {
    "competitors": [
      { "name": "竞品名", "url": "来源", "strengths": ["..."], "weaknesses": ["..."] }
    ],
    "errc": {
      "eliminate": ["行业标配但我们不做的"],
      "reduce": ["降低投入的"],
      "raise": ["超出行业水平的"],
      "create": ["行业从未有过的"]
    }
  },
  "frameworks_referenced": ["Lean Canvas", "VPC", "JTBD", "Blue Ocean ERRC"],
  "search_sources": ["搜索过程中参考的 URL"]
}
```

### `problem-domain.json`（Step 0 输出）

```json
{
  "generated_at": "ISO timestamp",
  "user_input": "用户原始输入",
  "problem_domain": "问题域描述",
  "top_problems": [
    {
      "id": "P1",
      "description": "问题描述",
      "severity": "critical | high | medium",
      "current_alternatives": "用户现在怎么解决这个问题",
      "evidence": "搜索来源 URL"
    }
  ],
  "competitors": [
    { "name": "竞品名", "url": "来源", "description": "简要描述", "key_features": ["..."] }
  ],
  "selected_traits": ["用户选中的差异化特征"],
  "confirmed": false
}
```

### `role-value-map.json`（Step 1 输出）

```json
{
  "generated_at": "ISO timestamp",
  "roles": [
    {
      "role_id": "R1",
      "role_name": "角色名",
      "jobs": [{ "type": "functional | emotional | social", "description": "..." }],
      "pains": ["痛点1", "痛点2"],
      "gains": ["期望收益1", "期望收益2"],
      "pain_relievers": ["产品如何缓解痛点"],
      "gain_creators": ["产品如何创造收益"]
    }
  ],
  "confirmed": false
}
```

### `business-model.json`（Step 2 输出）

```json
{
  "generated_at": "ISO timestamp",
  "revenue_streams": ["收入来源"],
  "cost_structure": ["成本结构"],
  "channels": ["获客渠道"],
  "key_metrics": ["关键指标"],
  "unfair_advantage": "不可复制优势",
  "confirmed": false
}
```

### `concept-decisions.json`（决策日志）

```json
[
  {
    "step": "Step 0",
    "item_id": "P1",
    "item_name": "描述",
    "decision": "confirmed | modified | deferred",
    "reason": "用户备注（可选）",
    "decided_at": "ISO timestamp"
  }
]
```

---

## 输出文件结构

```
.allforai/product-concept/
├── problem-domain.json          # Step 0: 问题域 + 竞品列表 + TOP 3 问题
├── role-value-map.json          # Step 1: 角色价值地图（VPC 格式）
├── business-model.json          # Step 2: 商业模式（Lean Canvas）
├── product-concept.json         # Step 3: 结构化产品概念（机器可读）
├── product-concept-report.md    # Step 3: 产品概念报告（人类可读）
└── concept-decisions.json       # 决策日志（增量复用）
```

---

## 6 条铁律

### 1. 只问选择题，不问开放题

所有问题都基于搜索结果生成选项。用户只需选择，不需要从零思考。如果现有选项都不对，用户可以用"其他"自由输入，AI 再基于新输入搜索并生成新选择题。

### 2. 搜索先行，选项后生

每轮提问前必须先 WebSearch 搜索互联网。选项必须基于搜索结果生成，不可凭空编造。搜索关键词从用户已确认的内容中提取，确保每轮搜索都更精准。

### 3. 每步确认，增量复用

每个 Step 完成后展示摘要，等待用户确认后才进入下一步。用户确认结果写入 `concept-decisions.json`，下次运行自动复用，不重复询问已确认项。

### 4. 产品语言输出

不出现技术术语（API、路由、组件等）。输出全程使用业务语言：用户、问题、价值、收入、竞争。

### 5. 只标不改

概念文档是建议，用户是权威。AI 基于搜索提供选项和结构化输出，最终决定权在用户。

### 6. 证据留痕

所有搜索来源 URL 记录在输出的 `search_sources` 字段和各条目的 `evidence` 字段中。结论可溯源。
