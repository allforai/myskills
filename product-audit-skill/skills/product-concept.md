---
name: product-concept
description: >
  Use when the user wants to "define a product concept", "start a new product from scratch",
  "figure out what to build", "validate a product idea", "产品概念", "产品定义",
  "我想做一个...", "这个产品应该怎么设计",
  or needs to discover what product to build before writing code.
version: "1.2.0"
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
  → WebSearch 搜索互联网（多角度、多轮）
  → 找到相关产品 / 商业模式 / 行业文章 / 用户真实反馈
  → 提炼为 2-4 个 AskUserQuestion 选择题
  → 用户选择
  → 基于选择结果，再次搜索更精准的信息
  → 范围缩小，进入下一轮或下一 Step
```

**铁律：不问开放题，只问选择题。** 所有问题都基于搜索结果生成选项，用户只需选择。

### "其他"响应处理流程

当用户选择"其他"并提供自定义输入时：

1. **不要直接采纳** — 用户输入可能模糊或不完整
2. **基于用户新输入 WebSearch** — 以用户提供的关键词为线索重新搜索
3. **生成新的选择题** — 基于新搜索结果提炼 2-4 个更精准的选项
4. **将用户原始输入融入选项** — 确保用户的意图被选项覆盖
5. 重复此循环直到用户从预设选项中确认

---

## 搜索策略 — 互联网是你的产品顾问

搜索是本技能的核心能力。AI 不是凭已有知识回答，而是**实时搜索互联网，用最新的行业数据为用户决策提供依据**。每个 Step 至少搜索 2-3 轮，每轮搜索角度不同。

### 每步搜索指南

| 步骤 | 搜索什么 | 搜索关键词策略 | 最低搜索轮数 |
|------|----------|---------------|-------------|
| **Step 0 Phase A** | 问题本质：该领域的学术研究、行业报告、问题根因分析 | `"{问题域}" 行业痛点 / "{问题域}" market size / "{问题域}" 用户研究` | 2 轮 |
| **Step 0 Phase B** | 竞品全景：直接竞品、间接竞品、已失败的产品 | `"{问题域}" 竞品分析 / "{问题域}" alternatives / "{竞品名}" vs / "{问题域}" startup failed why` | 3 轮 |
| **Step 1** | 用户画像：该类产品的真实用户构成、用户论坛中的抱怨、社区讨论 | `"{产品类型}" 用户画像 / "{竞品名}" user reviews / "{问题域}" Reddit OR forum / "{竞品名}" complaints` | 2 轮 |
| **Step 2** | 商业模式：行业收费模式、定价策略、成功指标、融资信息 | `"{产品类型}" pricing model / "{竞品名}" business model / "{行业}" SaaS metrics / "{竞品名}" revenue` | 2 轮 |
| **Step 3** | 定位验证：蓝海/红海分析、差异化案例、行业趋势预测 | `"{产品类型}" market positioning / "{行业}" trends 2025 2026 / "{产品类型}" blue ocean` | 1 轮 |

### 搜索技巧

1. **多语言搜索**：中文搜一轮 + 英文搜一轮，信息互补（中文找本土竞品和用户反馈，英文找全球视野和方法论）
2. **逐层聚焦**：第一轮宽泛搜（行业概况），第二轮基于用户选择精准搜（具体竞品/模式），第三轮验证搜（反面证据）
3. **找反面证据**：主动搜索"为什么 XX 失败了"/"XX 的缺点"/"XX 用户流失原因"，避免确认偏误
4. **找真实用户声音**：搜索 Reddit、知乎、Product Hunt、App Store 评论，获取用户真实痛点而非营销话术
5. **时效性优先**：优先使用 2024-2026 的搜索结果，过时数据标注时间

### 搜索结果处理

- **高质量来源**（优先引用）：官方文档、行业报告（Gartner/McKinsey/CB Insights）、学术论文、权威媒体
- **中等质量来源**（交叉验证后引用）：博客、Medium 文章、个人分析
- **用户声音来源**（作为痛点证据）：Reddit、知乎、Product Hunt、论坛、App Store 评论
- **低质量来源**（仅参考不引用）：无署名文章、明显的 SEO 内容、过时信息
- **搜索失败处理**：如果某个方向搜不到有价值的结果，换关键词再搜一轮；如果仍无结果，如实告知用户"该方向公开信息较少"，不编造

### 搜索结果→选项的转化规则

搜索到的信息不是直接丢给用户，而是**提炼为可选择的选项**：
- 从 5-10 条搜索结果中提取共性模式 → 归纳为 2-4 个选项
- 每个选项附带简要依据（"根据 XX 报告..."/"XX 竞品的做法是..."）
- 如果搜索结果高度一致（行业共识），选项中标注"行业主流做法"
- 如果搜索结果分歧明显，选项中标注各自的支持证据

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

**Phase A — 第一性原理拆解**（在搜索竞品之前）

不急于看别人怎么做，先拆解问题本质：
1. 从用户描述中提取**最底层的需求**（不是"我要做一个 XX 平台"，而是"某类人在某场景下无法完成某件事"）
2. **AskUserQuestion** 选择题："你描述的核心问题，本质上更接近哪一类？"（基于需求层次生成 2-4 个抽象选项，如"信息不对称"/"流程效率低"/"信任成本高"/"协作断裂"）
3. 锁定问题本质后，才进入竞品搜索 — 避免被现有产品形态锁死想象力

**Phase B — 竞品搜索 + 机会树收敛**

使用 Opportunity Solution Tree 结构组织发现过程：

```
期望成果（Outcome）：用户描述 + Phase A 锁定的问题本质
  → 机会空间（Opportunities）：WebSearch 发现的行业痛点
    → 现有方案（Solutions）：搜索到的竞品如何解决这些痛点
```

4. **WebSearch 搜索**相关行业、产品、竞品
5. 找到 3-5 个最相关的现有产品，按机会树组织（哪个痛点 → 哪个竞品在解决）
6. **AskUserQuestion** 选择题：
   - "你的想法更接近哪个产品？"（列出搜索到的竞品，附简要描述）
   - "哪些特点是你想要的？"（从竞品中提取差异化特征）
   - "你要解决的 核心问题是什么？"（基于机会树中的痛点生成选项）
7. 输出：`problem-domain.json`（问题本质、机会树、竞品列表、核心问题）
8. → 用户确认

---

### Step 1: 角色与价值 — 谁用？谁运营？他们得到什么？

输入：Step 0 锁定的方向

**Phase A — 消费侧角色**

1. **WebSearch 搜索**该类产品的典型用户构成
2. 基于搜索结果 + JTBD/VPC 框架，推导角色列表
3. **AskUserQuestion** 选择题（选项基于行为事实，不基于观点预测 — Mom Test 原则）：
   - "这些角色里哪些是你的目标用户？"（多选）
   - 对每个选中角色："这个角色现在怎么解决这个问题？"（基于搜索到的现有替代方案生成选项，而非问"你觉得痛不痛"）
   - "这个角色使用你的产品后，行为会发生什么变化？"（Gains 选项，聚焦可观测的行为改变）
4. 延续 Step 0 的机会树，将每个角色的痛点映射为具体的**机会 → 方案**分支：
   ```
   角色 A 的痛点 1（机会）→ 我们的方案 X（Pain Reliever）
   角色 A 的痛点 2（机会）→ 我们的方案 Y（Pain Reliever）
   ```
5. 结构化为 VPC 格式：每角色的 Jobs / Pains / Gains → Pain Relievers / Gain Creators

**Phase B — 生产侧角色闭环检查（强制）**

消费侧角色确认后，必须追问生产/运营侧角色。产品是一个闭环：有人消费内容/服务，就必须有人生产和运营。

6. **反推生产侧角色**：从 Step 2 的 `cost_structure`（或当前已知的产品特征）反推：
   - 成本项"内容制作" → 谁来创建内容？（内容运营/编辑）
   - 成本项"运营成本" → 谁来管理系统？（系统管理员）
   - 关键指标需要有人监控 → 谁来看数据？（数据分析/运营）
   - 付费模式需要管理 → 谁来处理订阅/退款？（客服/财务）
7. **AskUserQuestion** 选择题：
   - "产品运营需要哪些后台角色？"（基于反推结果生成选项，多选）
   - 对每个选中角色：简化版 VPC（Jobs + 核心工具需求，不需要 Pains/Gains 深度展开）
8. 输出：`role-value-map.json`（消费侧 + 生产侧角色合并）
9. → 用户确认

---

### Step 2: 商业模式 — 怎么活下去？

输入：Step 0-1 的确认结果

1. **WebSearch 搜索**该行业主流商业模式
2. **AskUserQuestion** 选择题：
   - "收费模式？"（订阅/按量/免费增值/一次性/平台抽成...基于行业搜索）
   - "你的核心竞争力是什么？"（基于竞品分析生成差异化选项）
   - "成功的关键指标是什么？"（基于行业标准生成选项）
3. 用 Lean Canvas 结构化：Revenue / Cost / Key Metrics / Unfair Advantage / Channels
4. **Build Trap 防护**：审查 key_metrics，确保每个指标都是 **outcome**（用户行为变化），不是 output（功能数量）。例如：
   - "月活跃用户数" ✓（outcome：用户持续使用）
   - "完成交易的平均时间缩短 30%" ✓（outcome：效率提升）
   - "上线 20 个功能" ✗（output：产出物数量，不反映价值）
   - "代码覆盖率 90%" ✗（output：工程指标，用户无感）
5. 输出：`business-model.json`
6. → 用户确认

---

### Step 3: 概念结晶 — 输出产品概念文档

输入：Step 0-2 的所有确认结果

1. 综合生成结构化产品概念
2. 生成 ERRC 竞品定位矩阵（基于 Step 0 的竞品 + Step 1 的价值差异），每项标注 **Kano 分类**：
   - **Must-have**（基本型）：没有就不及格，有了不加分 — 通常出现在 ERRC 的 reduce（降低但不能没有）
   - **Performance**（期望型）：越多越好，线性满意 — 通常出现在 ERRC 的 raise
   - **Delighter**（兴奋型）：没有不扣分，有了惊喜 — 通常出现在 ERRC 的 create
   - ERRC 的 eliminate 项天然不属于任何 Kano 分类（行业认为必要但我们判定非必要）
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
      "role_type": "consumer | producer | admin",
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
      "reduce": [{ "item": "降低投入的", "kano": "must-have" }],
      "raise": [{ "item": "超出行业水平的", "kano": "performance" }],
      "create": [{ "item": "行业从未有过的", "kano": "delighter" }]
    }
  },
  "frameworks_referenced": ["Lean Canvas", "VPC", "JTBD", "Blue Ocean ERRC", "Kano Model", "Opportunity Solution Tree", "First Principles", "Mom Test", "Build Trap / Product Kata"],
  "search_sources": ["搜索过程中参考的 URL"]
}
```

### `problem-domain.json`（Step 0 输出）

```json
{
  "generated_at": "ISO timestamp",
  "user_input": "用户原始输入",
  "problem_essence": "第一性原理拆解出的问题本质",
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
  "unique_positioning": "基于竞品分析得出的差异化定位",
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
      "role_type": "consumer | producer | admin",
      "description": "角色简要描述（年龄段、典型特征等）",
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

**`role_type` 说明**：
- `consumer`：消费侧角色（使用产品的最终用户）
- `producer`：生产侧角色（创建/管理内容或服务）
- `admin`：管理侧角色（系统管理、数据分析、客服）

生产侧和管理侧角色的 VPC 可以简化：`pains`/`gains` 可省略，重点填写 `jobs`。

### `business-model.json`（Step 2 输出）

```json
{
  "generated_at": "ISO timestamp",
  "revenue_streams": ["收入来源"],
  "cost_structure": ["成本结构"],
  "channels": ["获客渠道"],
  "key_metrics": [
    {
      "metric": "指标名",
      "type": "outcome",
      "target": "目标值",
      "why": "为什么选这个指标"
    }
  ],
  "unfair_advantage": "不可复制优势",
  "build_trap_check": "Build Trap 审查结果：确认所有指标均为 outcome",
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

## 写入时机

**用户确认后才写入磁盘。** 每个 Step 完成后，先在对话中展示结果摘要，等用户确认（confirmed）后才把 JSON 文件写入 `.allforai/product-concept/` 目录。未确认的结果只存在于对话上下文中，不落盘。

---

## 输出文件结构

```
.allforai/product-concept/
├── problem-domain.json          # Step 0: 问题域 + 竞品列表 + 核心问题
├── role-value-map.json          # Step 1: 角色价值地图（VPC 格式）
├── business-model.json          # Step 2: 商业模式（Lean Canvas）
├── product-concept.json         # Step 3: 结构化产品概念（机器可读）
├── product-concept-report.md    # Step 3: 产品概念报告（人类可读）
└── concept-decisions.json       # 决策日志（增量复用）
```

---

## 10 条铁律

### 1. 只问选择题，不问开放题

所有问题都基于搜索结果生成选项。用户只需选择，不需要从零思考。如果用户选择"其他"并提供自定义输入，必须走「其他响应处理流程」：基于新输入 WebSearch → 生成新选择题 → 用户从新选项中确认。不可直接采纳未经搜索验证的自由输入。

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

### 7. 选项基于行为，不基于观点（Mom Test）

所有选择题的选项必须基于**可观测的行为事实**（"用户现在怎么做"/"行为会如何改变"），不基于观点预测（"你觉得这个功能好不好"/"你会不会用"）。观点廉价且不可靠，行为才是真相。

### 8. 指标必须是成果，不是产出（Build Trap）

`key_metrics` 中的每个指标必须是 **outcome**（用户行为变化、业务结果），不是 output（功能数量、代码指标）。如果用户提出 output 型指标，引导其转化为背后的 outcome。这条规则防止产品陷入"不断堆功能但不创造价值"的构建陷阱。

### 9. 先拆本质，再看竞品（First Principles）

Step 0 必须先拆解问题的第一性原理（用户最底层的需求是什么），再搜索竞品。禁止跳过本质拆解直接进入竞品对标 — 否则产品定义会被现有产品的形态锁死，只能做"更好的 XX"而非真正的创新。

### 10. 角色闭环 — 有消费就有生产（Role Closure）

Step 1 不能只定义"谁用产品"，还必须定义"谁运营产品"。产品是一个闭环系统：有人消费内容/服务，就必须有人生产内容、管理系统、监控数据。具体检查：`cost_structure` 中每个成本项必须有对应角色负责；`key_metrics` 中每个指标必须有角色能看到和分析。只有消费侧角色没有生产侧角色的概念文档是不完整的。
