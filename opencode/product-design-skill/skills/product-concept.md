---
name: product-concept
description: >
  Use when the user wants to "define a product concept", "start a new product from scratch",
  "figure out what to build", "validate a product idea", "产品概念", "产品定义",
  "我想做一个...", "这个产品应该怎么设计",
  or needs to discover what product to build before writing code.
  Supports innovation boost mode with multi-model collaboration (OpenRouter MCP):
  assumption zeroing, innovation exploration, adversarial generation (disruptor/guardian/archaeologist/alchemist).
  从模糊想法到结构化产品概念：搜索 + 选择题引导，多模型协作创新（假设清零/创新探索/对抗性生成）。
version: "2.1.0"
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
| **发现模式**（forward） | 无代码，或用户主动触发 | Step 0→1→2→3→4 完整引导发现 |
| **提炼模式**（reverse） | 有代码，或已有 product-map | 从代码/product-map 反推 → 搜索验证 → 提炼概念 |

---

## 核心交互模式 — 搜索驱动的选择题

每个 Step 遵循循环：

```
用户输入（可以很模糊）
  → WebSearch 搜索互联网（多角度、多轮）
  → 找到相关产品 / 商业模式 / 行业文章 / 用户真实反馈
  → 提炼为 2-4 个 向用户提问选择题
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

## 增强协议（WebSearch + 4D+6V + XV + 闭环输入审计）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**闭环输入审计**（见 `docs/skill-commons.md` §八）：本技能每个 Step 的用户确认后执行闭环审计。重点关注**角色闭环**（有消费就有生产）和**商业闭环**（有收入就有成本）。发现 MUST 级缺失时，在下一轮提问中以选择题形式补问。

**WebSearch 关键词**：`”JTBD” + 行业词 + “case study” + 2025`、`”problem discovery” + 产品类型 + “user research”`、`”Blue Ocean” + 行业词 + “competitive landscape”`

**4D+6V 重点**：关键结论附带 `source_refs`、`assumptions`、`constraints`、`decision_rationale`；概念输出避免”只有结论无依据”，为下游 `product-map` 保留可追溯上下文。

**XV 交叉验证**（Step 4 概念结晶后）：

| 验证点 | task_type | 发送内容 | 写入字段 |
|--------|-----------|----------|----------|
| 假设挑战 | `competitive_analysis`→gemini | 概念摘要：核心问题 + 价值主张 + 关键假设 + ERRC 矩阵 | cross_model_review.assumption_challenges |
| 用户画像验证 | `user_persona_validation`→gpt | 角色列表 + VPC（Jobs/Pains/Gains） + 目标用户画像 | cross_model_review.persona_blindspots |

自动写入：假设挑战（哪些假设可能不成立）、盲区提示（被忽略的竞品或替代方案）、替代定位建议。

---

## 工作流 — 发现模式（5 Step）

### Step 0: 破题 — 锁定问题域

输入：用户的一句话描述（可以很模糊）

**Phase A — 第一性原理拆解**（在搜索竞品之前）

不急于看别人怎么做，先拆解问题本质：
1. 从用户描述中提取**最底层的需求**（不是"我要做一个 XX 平台"，而是"某类人在某场景下无法完成某件事"）
2. **向用户提问** 选择题："你描述的核心问题，本质上更接近哪一类？"（基于需求层次生成 2-4 个抽象选项，如"信息不对称"/"流程效率低"/"信任成本高"/"协作断裂"）
3. 锁定问题本质后，才进入竞品搜索 — 避免被现有产品形态锁死想象力

**Phase C — 假设清零（多模型并行，新增）**

在搜索竞品之前，先打破"行业共识"的束缚。使用 OpenRouter MCP 并行调用两个模型：

```
┌─────────────────────────────────────────────────────┐
│  并行调用（temperature 差异化）                       │
├─────────────────────────────────────────────────────┤
│  模型 A (gpt, temp=1.0): 挑战者                      │
│    → 列出该领域 5-10 条"行业共识"                      │
│    → 示例："协作工具必须有文件夹"、"社交产品必须有好友系统"│
│    → 输出：industry_assumptions[]                   │
│                                                     │
│  模型 B (gemini, temp=0.5): 守护者                   │
│    → 逐一质疑：这是物理定律还是人为约定？             │
│    → 物理定律 → 必须遵守（如网络延迟、信息熵）        │
│    → 人为约定 → 可以挑战（如文件夹、好友列表）        │
│    → 输出：constraint_classification[]              │
└─────────────────────────────────────────────────────┘
          ↓
主模型 (Claude): 整合者
  → 权衡两套意见，裁决分歧
  → 输出：assumption-zeroing.json
```

**向用户提问选择题**（假设清零后）：
- "以下行业共识中，哪些是你想挑战的？"（多选，来自 `constraint_classification` 中标记为"人为约定"的项）
- "如果去掉这些约束，你的产品可能有什么新形态？"（基于挑战选项生成 2-4 个创新方向）

**输出文件**：`.allforai/product-concept/assumption-zeroing.json`

**Phase B — 竞品搜索 + 机会树收敛（参考轨）**

使用 Opportunity Solution Tree 结构组织发现过程：

```
期望成果（Outcome）：用户描述 + Phase A 锁定的问题本质
  → 机会空间（Opportunities）：WebSearch 发现的行业痛点
    → 现有方案（Solutions）：搜索到的竞品如何解决这些痛点
```

4. **WebSearch 搜索**相关行业、产品、竞品
5. 找到 3-5 个最相关的现有产品，按机会树组织（哪个痛点 → 哪个竞品在解决）
6. **向用户提问** 选择题：
   - "你的想法更接近哪个产品？"（列出搜索到的竞品，附简要描述）
   - "哪些特点是你想要的？"（从竞品中提取差异化特征）
   - "你要解决的 核心问题是什么？"（基于机会树中的痛点生成选项）
7. 输出：`problem-domain.json`（问题本质、机会树、竞品列表、核心问题）
8. → 用户确认

**Phase B+ — 创新机会探索（多模型并行，新增）**

基于 Phase C 的"假设清零清单"，搜索无竞品约束的创新解决方案。使用 OpenRouter MCP 并行调用两个模型独立探索：

```
┌─────────────────────────────────────────────────────┐
│  并行调用（temperature=0.9，探索性）                   │
├─────────────────────────────────────────────────────┤
│  模型 A (gpt): 探索者                                │
│    → 基于清零清单搜索："如果没有 X 约束，问题如何解决？"│
│    → 每方向 3-4 轮深度搜索                            │
│    → 输出：innovation_opportunities_A[]             │
│                                                     │
│  模型 B (gemini): 探索者（独立）                      │
│    → 相同任务，独立搜索                             │
│    → 输出：innovation_opportunities_B[]             │
└─────────────────────────────────────────────────────┘
          ↓
主模型 (Claude): 整合者
  → 合并去重，标注分歧点
  → 输出：innovation-opportunities.json
```

**搜索关键词示例**：
- `"eliminate folder structure" + "content organization innovation"`
- `"frictionless onboarding" + "one-click setup"`
- `"alternative to friend list" + "social connection"`

**输出文件**：`.allforai/product-concept/innovation-opportunities.json`

**Schema**：
```json
{
  "generated_at": "ISO timestamp",
  "assumption_zeroing_ref": "assumption-zeroing.json",
  "opportunities": [
    {
      "id": "IO001",
      "direction": "创新方向描述",
      "assumption_challenged": "被挑战的假设 ID",
      "model_a_input": "模型 A 的方案",
      "model_b_input": "模型 B 的方案",
      "integrated_solution": "整合后的方案",
      "disagreements": ["分歧点（如有）"],
      "search_sources": ["URL1", "URL2"]
    }
  ],
  "search_rounds": 4
}
```

→ 用户确认创新机会方向

---

### Step 1: 角色与价值 — 谁用？谁运营？他们得到什么？

输入：Step 0 锁定的方向

**Phase A — 消费侧角色**

1. **WebSearch 搜索**该类产品的典型用户构成
2. 基于搜索结果 + JTBD/VPC 框架，推导角色列表
3. **向用户提问** 选择题（选项基于行为事实，不基于观点预测 — Mom Test 原则）：
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
   - 付费模式需要管理 → 谁来处理订阅/撤销？（客服/财务）
7. **向用户提问** 选择题：
   - "产品运营需要哪些后台角色？"（基于反推结果生成选项，多选）
   - 对每个选中角色：简化版 VPC（Jobs + 核心工具需求，不需要 Pains/Gains 深度展开）

**Phase C — 实现合并标注**

概念层按职责细分角色确保需求不遗漏，但实现层通常不需要这么多独立角色。在输出中标注实现合并建议：

8. 为每个生产侧角色添加 `impl_group` 字段，标注实现时归属哪个系统角色：
   ```
   概念角色（按职责细分）        实现角色（按权限合并）
   ─────────────────          ─────────────────
   内容运营    ──┐
   AI 训练师   ──┼──→         运营后台用户（权限区分）
   数据运营    ──┘
   系统管理员  ──────→         超级管理员
   ```
9. **原则**：概念层的角色粒度服务于需求完整性，实现层的角色粒度服务于权限系统设计。product-map 生成任务时按 `impl_group` 归组，同一 `impl_group` 的角色共享一个后台界面，通过权限标签区分功能入口。

10. 为每个实现角色添加 `app` 字段，标注该角色使用的**独立应用**（可部署单元）：
    ```
    impl_group → app 映射（问用户确认）
    ─────────────────────────────
    end_user       → website（或 mobile，若有独立 app）
    provider       → provider（服务提供者后台，独立部署）
    admin          → admin（总后台，独立部署）
    ```
    **`app` 的含义**：一个独立部署的前端应用，有自己的代码仓库（或子目录）、端口、路由。不同于 `platform`（设备类型）或 `role`（用户身份），`app` 决定界面**在哪个系统中实现**。

    同一个 `app` 内的多个角色通过权限区分功能入口；不同 `app` 之间的流转通过跨应用引用（而非同一界面）实现。

    **向用户提问**：展示推导出的 role→app 映射，让用户确认或修正。

**Phase D — 角色操作频度分析与屏幕粒度指导**

概念层完成角色定义后，为下游界面设计建立操作频度模型和屏幕粒度指导思想。这些不是"偏好"，而是从角色特征推导出的设计原则。

11. **操作频度分析**（每个实现角色）：

    基于角色的 `impl_group`、`app`、`platforms` 推导操作特征：

    | 角色特征 | 操作频度模型 | 屏幕粒度指导 |
    |---------|-------------|-------------|
    | 终端用户端 (end_user) + mobile | 高频少操作，注意力短，单手操作 | 每屏聚焦单一任务，纵深导航，减少跳转层级 |
    | 终端用户端 (end_user) + desktop | 中频中操作，多标签浏览 | 适度聚合相关功能，侧边栏辅助导航 |
    | 服务提供者后台 (provider) + desktop | 中频多操作，日常运营，效率优先 | **同页多功能**：列表+详情+操作在同一视图，减少页面跳转。常用操作前置，低频操作折叠 |
    | 管理后台 (admin) + desktop | 低频重操作，审核/配置/监控为主 | **仪表盘+工作台**模式：KPI 总览 + 待办队列 + 批量操作。配置类可深层嵌套 |

    **二八原则应用**：每个角色识别 top 20% 高频操作（从角色核心 jobs + 日常操作场景推导），这些操作必须在 1-2 次点击内可达。下游 product-map 生成 business-flows 后可进一步验证和细化。

12. **向用户提问**（多选确认）：展示每个角色的操作频度分析和屏幕粒度建议，让用户确认或调整。

13. 输出：`role-value-map.json`（消费侧 + 生产侧角色，含 `impl_group` + `app` + `operation_profile` 标注）

    ```json
    {
      "role_id": "R2",
      "role_name": "服务提供者后台用户",
      "impl_group": "provider",
      "app": "provider",
      "operation_profile": {
        "frequency": "medium",
        "density": "high",
        "screen_granularity": "multi_function_per_page",
        "high_frequency_tasks": ["工单处理", "资源管理", "消息回复"],
        "design_principle": "同页多功能，常用操作前置，列表+详情+操作在同一视图"
      }
    }
    ```

14. → 用户确认

---

### Step 2: 商业模式 — 怎么活下去？

输入：Step 0-1 的确认结果

1. **WebSearch 搜索**该行业主流商业模式
2. **向用户提问** 选择题：
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

### Step 3: 产品机制 — 核心功能怎么工作？

输入：Step 0-2 的确认结果

产品概念定义了 WHAT（解决什么问题）和 WHO（给谁用），但没有定义 HOW（核心功能以什么机制运作）。不同的机制选择会导致完全不同的功能地图。

**本步骤不涉及工程实现**（不讨论数据库/API/框架），只关注**产品机制**：用户和运营者视角下，核心功能是怎么工作的。

1. **识别机制决策点**：从 Step 0-2 的功能模块和角色中，找出存在多种可行方式的核心功能：
   - 内容生产方式（人工编辑 / AI生成+人工审核 / 实时生成 / 混合）
   - 个性化方式（用户自选 / 算法推荐 / 两者结合）
   - 社交机制（无社交 / 好友系统 / 排行榜 / 社区）
   - 付费边界（功能限制 / 用量限制 / 内容限制）
   - 等等 — 具体决策点因产品而异

2. **WebSearch 搜索**竞品在这些机制上的做法
3. **向用户提问** 选择题：对每个机制决策点生成 2-4 个选项（基于竞品做法和行业趋势）
4. 记录每个机制决策及其对功能模块的影响：
   - 选择 X → 需要 Y 模块 / 不需要 Z 模块
   - 选择 X → R4（内容运营）的工作量增大/减小
5. 输出：`product-mechanisms.json`
6. → 用户确认

**Phase A.5 — 产品治理风格（按业务流分级）**

不同的业务流需要不同的治理策略。治理风格决定了下游界面是否需要审核环节、表单复杂度、系统边界划分。这不是全局统一的——同一个产品中，资金相关流程可能需要严格审核，而内容发布可能允许先发后审。

7. **识别需要治理决策的业务流**：从 Step 0-2 的功能模块中，找出涉及以下场景的业务流：
   - 内容发布（条目上架、评价发布、广告投放等）
   - 资金操作（支付、提现、撤销等）
   - 身份准入（注册、入驻、认证等）
   - 权限变更（角色分配、权限调整等）

8. **对每个业务流，向用户提问选择题**：

   问题：「{业务流名称} 的治理风格？」

   | 编号 | 选项 | 说明 | 下游影响 |
   |------|------|------|---------|
   | 1 | 严格管控（事前审核） | 操作前必须经过审核/审批才能生效 | 需要审核队列屏幕、审核状态跟踪、审核员角色 |
   | 2 | 宽松高效（事后追究） | 操作直接生效，出问题后处理 | 需要举报/申诉通道、违规记录、自动监控 |
   | 3 | 分级管控 | 首次严格审核，信誉积累后自动通过 | 需要信誉体系、分级规则配置 |
   | 4 | 自动审核 | AI/规则自动判断，异常才人工介入 | 需要规则引擎配置、异常队列 |

9. **推导系统边界**：治理风格决定哪些功能在系统内、哪些是外部依赖：
   - 严格管控 → 准入流程在系统内完整实现（如注册时就收集完整资质信息）
   - 宽松高效 → 准入流程极简（如注册只需邀请码+基本信息），复杂认证交给外部系统或后续补充
   - **向用户提问** 确认：「以下功能是在本系统内实现还是依赖外部系统？」（基于治理风格推导的边界建议）

10. 输出：追加到 `product-mechanisms.json` 的 `governance_styles` 字段

    ```json
    "governance_styles": [
      {
        "flow_domain": "条目上架",
        "style": "auto_review",
        "rationale": "首次人工审核，信誉积累后自动通过",
        "downstream_implications": ["需要信誉评分系统", "需要自动审核规则配置"],
        "system_boundary": {
          "in_scope": ["条目信息填写", "审核状态展示"],
          "external": ["实名认证（第三方KYC）"]
        }
      }
    ]
    ```

11. → 用户确认

**Phase B — 对抗性生成（多模型并行，新增）**

使用 OpenRouter MCP 并行调用 4 个模型，扮演不同角色产生突破性创新方案：

```
┌─────────────────────────────────────────────────────────────────┐
│  并行调用（temperature 差异化）                                   │
├─────────────────────────────────────────────────────────────────┤
│  模型 A (gpt, temp=1.2): 颠覆者                                   │
│    → 针对每个核心机制，提出最激进的方案                           │
│    → 打破所有行业惯例                                            │
│    → 输出：3 个"疯狂"概念                                         │
│                                                                 │
│  模型 B (gemini, temp=0.3): 守护者                                │
│    → 找出违反物理/法律/人性底线的部分                            │
│    → 划定不可逾越的边界                                          │
│    → 输出：boundary-constraints.json                             │
│                                                                 │
│  模型 C (deepseek, temp=0.9): 考古学家                            │
│    → 从其他领域寻找相似问题的异类解法                            │
│    → 固定 3 个跨域案例                                            │
│    → 示例：                                                    │
│      - 问题本质="信任建立" → 游戏行业（公会系统）                 │
│      - 问题本质="信任建立" → 金融行业（担保机制）                 │
│      - 问题本质="信任建立" → 生物界（共生关系）                   │
│    → 输出：cross-domain-cases.json                               │
│                                                                 │
│  模型 D (qwen, temp=0.8): 预整合                                  │
│    → 初步整合 A/B/C 的输出                                        │
│    → 输出：pre-synthesis.json                                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
主模型 (Claude, temp=0.8): 炼金师
  → 读取 4 个模型的输出
  → 在边界内重释激进方案
  → 必须保留颠覆者的核心洞见（不许妥协成平庸方案）
  → 输出 3 个"陌生但可行"概念
  → 输出：adversarial-concepts.json
```

**向用户提问选择题**（对抗性生成后）：
- "这 3 个创新方案中，哪个最符合你的愿景？"（单选或多选）
- "每个方案的保护级别？"（AI 建议 + 用户确认）
  - **core** — 差异化核心功能，必须保留
  - **defensible** — 有防御价值，可讨论
  - **experimental** — 实验性功能，可推迟

### Step 2.5: 创新概念状态机定义（新增，通用版）

对每个 `protection_level="core"` 或 `"defensible"` 的创新概念，定义其状态机（不绑定特定行业）：

**指导问题**（通用描述）：
1. 这个创新机制涉及哪些核心业务实体？（如"场景"、"会话"、"赛季"等，避免使用行业特定术语）
2. 每个实体的生命周期状态有哪些？（初始状态 → 中间状态 → 终止状态）
3. 关键状态转换的触发条件是什么？
4. 异常状态如何处理？（如加载失败、网络中断等通用异常）

**输出**：
- 在 `adversarial-concepts.json` 的每个 concept 中增加 `state_machine` 字段
- 定义实体、状态、转换、完整性要求
- **原则**：只定义结构完整性，不验证具体业务逻辑

**保护级别要求**：
- `core` 级别创新概念：**必须**定义完整状态机
- `defensible` 级别：**建议**定义状态机
- `experimental` 级别：可选

**输出文件**：
- `.allforai/product-concept/boundary-constraints.json`
- `.allforai/product-concept/cross-domain-cases.json`
- `.allforai/product-concept/adversarial-concepts.json`（含 state_machine 字段）

**Schema（adversarial-concepts.json）**：
```json
{
  "generated_at": "ISO timestamp",
  "multi_model_collaboration": {
    "models_used": [
      { "role": "disruptor", "model_family": "gpt", "temperature": 1.2 },
      { "role": "guardian", "model_family": "gemini", "temperature": 0.3 },
      { "role": "archaeologist", "model_family": "deepseek", "temperature": 0.9 },
      { "role": "pre_synthesizer", "model_family": "qwen", "temperature": 0.8 }
    ],
    "integration_method": "main_model_synthesis",
    "disagreements": [
      {
        "topic": "分歧点描述",
        "model_a_view": "模型 A 观点",
        "model_b_view": "模型 B 观点",
        "integration_decision": "主模型的裁决",
        "rationale": "裁决理由"
      }
    ]
  },
  "concepts": [
    {
      "id": "IC001",
      "name": "创新概念名",
      "description": "详细描述",
      "source_mechanism": "MEC1",
      "disruptor_input": "颠覆者原始方案",
      "boundary_constraints": ["边界约束列表"],
      "cross_domain_references": ["跨域案例 ID"],
      "protection_level": "core | defensible | experimental",
      "feasibility_score": 3,
      "innovation_score": 9,
      "competitor_reference": "none | cross-domain | evolved",
      "state_machine": {
        "description": "创新机制的核心状态流转（通用描述，不绑定特定行业）",
        "key_entities": [
          {
            "name": "核心实体名",
            "lifecycle_description": "实体的生命周期描述",
            "critical_states": ["初始状态", "中间状态", "终止状态"],
            "initial_state": "初始状态",
            "terminal_states": ["终止状态"],
            "critical_transitions": [
              {
                "from": "状态 A",
                "to": "状态 B",
                "trigger": "触发条件",
                "business_meaning": "业务含义"
              }
            ]
          }
        ],
        "integrity_requirements": {
          "must_have_initial_state": true,
          "must_have_terminal_state": true,
          "must_have_error_recovery": true,
          "max_unreachable_states": 0,
          "must_have_timeout_transition": true,
          "must_have_compensation_path": true
        }
      }
    }
  ]
}
```

→ 用户确认创新概念及保护级别

---

### Step 3.5: 流水线偏好采集（Pipeline Preferences）

> 仅在用户意图执行完整流水线时触发（`/product-design full` 或用户明确表示要跑全程）。
> 单独运行 `/product-concept` 时**跳过此步骤**。
> 这些问题前置到概念阶段，下游技能自动消费，无需再问。

**触发条件**：用户明确表示要执行完整产品设计流水线（如 `/product-design full`、「帮我跑一遍全流程」等）。

**Q1 — UI 设计风格（仅终端用户端）**

> 管理后台的视觉风格由组件库决定（Ant Design / Element Plus / Shadcn 等），无需单独选择。
> Q1 仅对**终端用户端**（Web/App/小程序）提问。若产品只有管理后台没有终端用户端 → 跳过 Q1。

从 Step 1 识别的角色推断终端用户端类型。若有多个终端用户端（如 Web + Mobile），分别选择。

对每个终端用户端类型，向用户提问（单选）：

问题：「{终端用户端名称} 的视觉风格偏好？」

| 编号 | 选项 | 适用场景 |
|------|------|----------|
| 1 | Material Design 3 | Google 风，适合工具/效率类 |
| 2 | Apple HIG | 苹果风，适合消费/精品类 |
| 3 | Fluent Design | 微软风，适合企业/办公类 |
| 4 | Flat / Minimal | 极简，适合信息/内容类 |
| 5 | Glassmorphism | 玻璃拟态，适合时尚/社交类 |
| 6 | Shadcn / Tailwind | 开发者友好，适合 SaaS/技术产品 |
| 7 | 暂不确定 | 下游 ui-design 阶段再交互选择 |

> 若只有一个终端用户端，退化为单次提问。多端时合并为一次 向用户提问 逐端选择。

**Q2 — 竞品参考**

向用户提问（开放文本 + 预设）：

问题：「有哪些竞品想参考？（输入名称，逗号分隔；无则选"无"）」

| 编号 | 选项 |
|------|------|
| 1 | 无竞品参考 |
| （用户可输入自定义文本） | |

**Q3 — 功能范围策略**

向用户提问（单选）：

问题：「功能范围的取舍策略？」

| 编号 | 选项 | 说明 |
|------|------|------|
| 1 | 激进精简 | 只保留高频核心，低频一律推迟或移除 |
| 2 | 平衡取舍 | 高频保留，低频按场景判断 |
| 3 | 保守保全（推荐成熟产品） | 尽量保留，只砍明确无用的 |

**Q4（可选）— 高质量 UI 视觉稿**

检测 Stitch MCP 可用性：
- 检查 MCP 工具 `mcp__stitch__create_project` 是否可用
- 可用 → 提示「Stitch 已就绪（Google 认证有效）」
- 不可用 → 提示「Stitch 未配置。如需启用，运行 `npx -y @_davideast/stitch-mcp init` 完成 Google 认证。现在可跳过，后续在 ui-design 阶段仍可启用。」

向用户提问（单选）：

问题：「是否在 UI 设计阶段使用 Google Stitch 生成高质量视觉稿？」

| 编号 | 选项 | 说明 |
|------|------|------|
| 1 | 是，启用 Stitch（推荐） | 自动为核心界面生成视觉 UI（HTML/CSS + 截图），需 Google 认证 |
| 2 | 否，使用文字规格 | 生成 ui-design-spec.md + HTML 预览 + 组件规格，不调用 Stitch |
| 3 | 暂不确定 | 下游 ui-design 阶段再决定 |

**Q5 — 基础设施偏好**

向用户提问（多选，可多选 + 全不选）：

问题：「产品需要支持以下哪些基础能力？（多选，全不选则跳过）」

| 编号 | 选项 | 影响范围 |
|------|------|----------|
| 1 | 暗色模式（Dark Mode） | UI token 需双色系、experience-map 增加主题切换入口 |
| 2 | 主题/品牌切换 | UI token 需变量化、动态主题加载 |
| 3 | 多语言 / i18n | 所有文案需 key 化、布局需适应文本长度变化 |
| 4 | 跨平台（Web + App / 小程序） | experience-map 需多端界面、dev-forge 需多子项目 |
| 5 | 无障碍 / Accessibility | 组件需 ARIA 标注、对比度达标、键盘导航 |
| 6 | 离线支持 / PWA | 需 Service Worker / 本地缓存策略 |
| 7 | RTL 布局（阿拉伯语/希伯来语） | CSS 需 logical properties、图标需镜像 |

> 选中的项会影响下游所有阶段：experience-map（界面清单）、ui-design（token 体系）、dev-forge（技术选型 + 任务生成）。

**写入 `product-concept.json`**：

五个问题回答完毕后，将偏好写入 `pipeline_preferences` 字段：

```json
"pipeline_preferences": {
  "ui_styles": {
    "web-customer": "apple-hig",
    "mobile-native": "material-design-3"
  },
  "competitors": ["竞品A", "竞品B"] | [],
  "scope_strategy": "aggressive | balanced | conservative | undecided",
  "stitch_ui": true | false | "undecided",
  "infrastructure": ["dark-mode", "theme-switching", "i18n", "cross-platform", "a11y", "offline-pwa", "rtl"] | []
}
```

> `ui_styles` 仅包含终端用户端类型（admin/后台不需要，风格由组件库决定）。单终端用户端产品只有一个 key。下游 ui-design 按端类型读取对应风格。

> `pipeline_preferences` 的存在是下游自动模式的激活条件之一。选择「暂不确定」的项标记为 `"undecided"`，下游对应技能回退到交互模式。

---

### Step 4: 概念结晶 — 输出产品概念文档（创新增强）

输入：Step 0-3 的所有确认结果（含创新轨输出）

**合并参考轨 + 创新轨结果**：
1. 参考轨（Phase B）：竞品分析数据 → ERRC 的 reduce/raise 项
2. 创新轨（Phase C/B+/B）：假设清零 + 创新机会 + 对抗性生成 → ERRC 的 eliminate/create 项

**双评分系统**（每个 create 项）：
| 评分维度 | 含义 | 分值范围 |
|---------|------|---------|
| `feasibility_score` | 传统可行性（技术/成本/时间） | 0-10 |
| `innovation_score` | 突破性创新潜力 | 0-10 |

**保护级别**（AI 建议 + 用户确认）：
| 级别 | 含义 | 处理 |
|------|------|------|
| `core` | 差异化核心功能 | 直接保留 |
| `defensible` | 有防御价值 | 用户确认流程 |
| `experimental` | 实验性功能 | 可推迟 |

**新增字段**：`innovation_preferences`（独立于 `pipeline_preferences`）

```json
"innovation_preferences": {
  "innovation_mode": "deep",
  "risk_tolerance": "high",
  "protected_features": ["IC001", "IC003"],
  "multi_model_collaboration": {
    "enabled": true,
    "models_used": 7,
    "total_search_rounds": 12
  }
}
```

**输出文件**：
- `product-concept.json` — 机器可读，供 product-map 消费（含 innovation_preferences）
- `product-concept-report.md` — 人类可读报告（含创新方案摘要）
- `concept-decisions.json` — 决策日志（增量复用）

→ 用户确认最终文档（含创新方案及保护级别）

---

## 工作流 — 提炼模式（3 Step）

### Step 0: 代码/地图读取

- 如果有 `product-map.json` → 直接读取角色、任务、竞品信息
- 如果只有代码 → 快速扫描路由/权限/菜单，提取角色和功能模块
- 输出：从现状反推的初步概念草稿

### Step 1: 搜索验证

- 基于反推结果 **WebSearch 搜索**竞品和行业趋势
- **向用户提问**：验证反推的问题域、角色、价值是否准确
- 补充商业模式层（代码中通常没有）

### Step 2: 概念结晶

- 同发现模式 Step 4（跳过 Step 3 产品机制，因为代码已体现机制选择）

---

> **输出 JSON Schema 详见** ./docs/schemas/product-concept-schemas.md

---

## 写入时机

**用户确认后才写入磁盘。** 每个 Step 完成后，先在对话中展示结果摘要，等用户确认（confirmed）后才把 JSON 文件写入 `.allforai/product-concept/` 目录。未确认的结果只存在于对话上下文中，不落盘。

---

## 输出文件结构（创新增强版）

```
.allforai/product-concept/
├── problem-domain.json           # Step 0: 问题域 + 竞品列表 + 核心问题
├── assumption-zeroing.json       # Step 0 Phase C: 假设清零清单（多模型）★新增
├── innovation-opportunities.json # Step 0 Phase B+: 创新机会（多模型）★新增
├── role-value-map.json           # Step 1: 角色价值地图（VPC 格式，含 impl_group）
├── business-model.json           # Step 2: 商业模式（Lean Canvas）
├── product-mechanisms.json       # Step 3 Phase A: 产品机制决策
├── boundary-constraints.json     # Step 3 Phase B2: 边界约束（多模型）★新增
├── cross-domain-cases.json       # Step 3 Phase B3: 跨域案例（多模型）★新增
├── adversarial-concepts.json     # Step 3 Phase B4: 对抗性生成（多模型）★新增
├── product-concept.json          # Step 4: 结构化产品概念（含 innovation_preferences）
├── product-concept-report.md     # Step 4: 产品概念报告（人类可读）
└── concept-decisions.json        # 决策日志（增量复用）
```

**文件体积预估**（400 任务规模产品）：
- `assumption-zeroing.json`: ~2KB
- `innovation-opportunities.json`: ~5KB
- `boundary-constraints.json`: ~1KB
- `cross-domain-cases.json`: ~4KB
- `adversarial-concepts.json`: ~6KB

---

## 防御性规范

> 通用模式定义见 `docs/defensive-patterns.md`，以下为本技能的具体应用。

### 加载校验
- **`concept-decisions.json`**：加载时用 `python -m json.tool` 验证 JSON 合法性。解析失败 → 检查 `.bak` → 提示恢复或重新运行 `/product-concept`。

### 零结果处理
- **Step 0 用户无输入**：若用户未提供任何描述 → 用 向用户提问 引导：「请用一句话描述你想做的产品或想解决的问题」，不静默生成空结果。
- **WebSearch 连续 3 轮无有用结果**：切换为纯访谈模式 — 基于 AI 知识 + 用户输入推进，标记 `evidence_mode: "interview_only"`，告知用户「公开信息较少，已切换为访谈模式」。
- **用户连续 3 次选 Other 且搜索无有用结果**：提供手动输入选项 — 「看起来预设选项不符合你的想法，请直接输入你的描述」，跳出重搜循环。

### 规模自适应
- **不适用**。产品概念发现是单一产品粒度的对话流程，不涉及批量处理，无需规模分级。

### WebSearch 故障
- **工具不可用**：告知用户「⚠ WebSearch 暂不可用」→ 提供选项：(a) 切换为纯访谈模式（基于 AI 知识 + 用户输入），标记 `evidence_mode: "interview_only"` (b) 用户手动提供参考资料。
- **工具正常但无有用结果**：按搜索策略换关键词重试一轮 → 仍无结果 → 告知用户「该方向公开信息较少」，继续流程。
- 所有搜索步骤（Step 0–3）均适用此规则，不静默跳过任何搜索环节。

### 上游过期检测
- **不适用**。product-concept 是链路起点，无上游依赖。

### 执行失败保护

- 任何步骤遇到不可恢复错误 → 写入 `.allforai/product-concept/product-concept-error.json`，包含 `{"error": "...", "step": "...", "timestamp": "..."}`。

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

### 11. 多模型协作 — 并行调用 + 主模型整合（Innovation Boost）

创新增强模式下，使用 OpenRouter MCP 并行调用多个模型（假设清零 2 个 + 创新探索 2 个 + 对抗性生成 4 个 = 最多 8 个模型并行），主模型（Claude）作为整合者：
- **temperature 差异化**：颠覆者=1.2（高创造性），守护者=0.3（严谨），炼金师=0.8（平衡）
- **分歧处理**：模型间分歧由主模型裁决，记录 `disagreements` 字段
- **效果优先**：成本不设上限，追求最佳创新效果
- **输出留痕**：`multi_model_collaboration` 字段记录所有使用的模型及角色
