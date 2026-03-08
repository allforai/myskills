---
name: market-validate
description: >
  Market validation for product concepts: competitive landscape analysis,
  role & demand verification, business model stress testing.
  Uses Brave search + cross-model validation. Runs after /product-concept,
  before /product-map. 产品概念市场验证：竞品格局分析、角色需求验证、
  商业模式压力测试。使用 Brave 搜索 + 跨模型验证。
  在 /product-concept 之后、/product-map 之前执行。
version: "1.0.0"
---

# Market Validate — 产品概念市场验证

> 用真实市场数据验证产品概念，在投入详细产品地图之前发现风险

## 目标

以 `product-concept.json` 为输入，通过互联网搜索和跨模型分析，回答三个问题：

1. **市场真实吗？** — 竞品格局、市场趋势、替代方案是否支撑产品假设？
2. **角色存在吗？** — 每个假设角色的痛点是否真实、频次是否足够？
3. **模式成立吗？** — 商业模式、定价基准、单位经济学是否可行？

验证结果只呈现证据和风险，不替用户做 Go/No-Go 决策。

---

## 定位

```
product-concept（战略层）    market-validate（验证层）       product-map（运营层）
帮什么人解决什么问题？       概念假设是否经得起市场检验？     产品有什么功能？任务是否完整？
输出产品概念文档              输出市场验证报告                输出产品地图
```

**前提**：必须先运行 `product-concept`，生成 `.allforai/product-concept/product-concept.json`。

---

## 快速开始

```
/market-validate              # 完整验证（Step 1-5）
/market-validate quick        # 跳过 Step 4 商业模式压力测试
/market-validate refresh      # 忽略已有缓存，重新验证
```

## 增强协议（Brave Search + XV）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**Brave Search 关键词**：`"{problem_domain}" market size 2025 2026`、`"{problem_domain}" competitor landscape`、`"{role}" pain points reddit forum`、`"{business_model}" pricing benchmark SaaS`

**XV 交叉验证**：Step 3 角色验证和 Step 4 商业模式验证均使用不同模型家族交叉验证（详见各步骤说明）。

---

## 工作流（5 Step）

### Step 1: 加载产品概念

输入：`.allforai/product-concept/product-concept.json`

1. 检测文件是否存在
   - 不存在 → **AskUserQuestion**：「产品概念文件不存在，请先运行 `/product-concept` 生成产品概念。是否现在运行？」
   - 存在 → 继续
2. 加载并提取关键字段：
   - `problem_domain` — 问题域
   - `roles[]` — 角色列表（消费侧 + 生产侧）
   - `business_model` — 商业模式（收费模式、成本结构、关键指标）
   - `product_mechanisms` — 产品机制决策
3. 检测已有验证缓存 `.allforai/market-validate/market-validation.json`：
   - 存在且 `concept_ref` 匹配 → 展示上次验证摘要，**AskUserQuestion**：「已有验证结果，是否复用？（1）复用并跳到 Step 5 查看结论（2）重新验证」
   - 不存在或不匹配 → 继续完整流程
4. 展示概念摘要，确认验证范围

---

### Step 2: 市场趋势与竞品验证

输入：Step 1 提取的 `problem_domain` + `product_mechanisms`

**Phase A — 市场趋势搜索**

使用 `mcp__plugin_product-design_ai-gateway__brave_web_search` 执行多轮搜索：

| 搜索轮次 | 关键词策略 | 目标 |
|---------|-----------|------|
| 第 1 轮 | `"{problem_domain}" market trends 2025 2026` | 市场趋势方向 |
| 第 2 轮 | `"{problem_domain}" market size TAM SAM` | 市场规模指标 |
| 第 3 轮 | `"{problem_domain}" user complaints reddit forum app store` | 用户真实痛点 |

**Phase B — 竞品搜索**

| 搜索轮次 | 关键词策略 | 目标 |
|---------|-----------|------|
| 第 1 轮 | `"{problem_domain}" competitors alternatives` | 直接竞品 |
| 第 2 轮 | `"{竞品名}" vs comparison pricing` | 竞品对比 |
| 第 3 轮 | `"{problem_domain}" startup failed why` | 失败案例 |

**Phase C — 结构化分析**

使用 `mcp__plugin_product-design_ai-gateway__ask_model` 将搜索结果结构化：

```
ask_model(task_type="competitive_analysis", model_family="gemini")
```

发送内容：搜索结果摘要 + 问题域描述

输出结构：

- **competitor_matrix[]** — 至少 3 个直接竞品 + 2 个替代方案
  - `name` — 竞品名称
  - `positioning` — 市场定位
  - `pricing` — 定价模式
  - `strengths[]` — 优势
  - `weaknesses[]` — 劣势
  - `source_url` — 来源 URL（无来源标记 `[UNVERIFIED]`）
- **market_signals** — 市场信号
  - `trend_direction` — 上升/平稳/下降
  - `maturity` — 新兴/成长/成熟/衰退
  - `user_demand_evidence[]` — 用户需求证据（附来源 URL）
  - `market_size_indicators` — 市场规模指标（附来源 URL）
- **alternative_solutions[]** — 用户现有替代方案
  - `description` — 方案描述
  - `user_segment` — 使用人群
  - `limitations[]` — 局限性
  - `source_url` — 来源 URL

写入：`.allforai/market-validate/competitor-matrix.json`

→ 展示竞品矩阵摘要，用户确认

---

### Step 3: 角色与需求验证

输入：Step 1 提取的 `roles[]` + Step 2 的市场数据

对每个角色执行验证循环：

**Phase A — 角色存在性搜索**

使用 `mcp__plugin_product-design_ai-gateway__brave_web_search`：

| 搜索轮次 | 关键词策略 |
|---------|-----------|
| 第 1 轮 | `"{role_description}" pain points challenges` |
| 第 2 轮 | `"{role_name}" workflow problems reddit` |
| 第 3 轮 | `"{role_name}" daily tasks frustrations forum` |

**Phase B — 主模型分析**

使用 `mcp__plugin_product-design_ai-gateway__ask_model` 分析角色可行性：

```
ask_model(task_type="role_validation", model_family="gpt")
```

发送内容：角色定义 + 搜索结果 + 竞品中该角色的情况

输出每角色：
- `role_id` — 角色 ID（对齐 product-concept）
- `role_name` — 角色名称
- `viability_score` — 可行性评分（1-5）
  - 5 = 大量证据支撑，痛点频繁且强烈
  - 4 = 较多证据，痛点真实但不够频繁
  - 3 = 一般证据，痛点存在但可能不强烈
  - 2 = 少量证据，痛点可能被高估
  - 1 = 几乎无证据，角色假设可能不成立
- `evidence[]` — 支撑证据（每条附 `source_url`，无来源标记 `[UNVERIFIED]`）
- `risks[]` — 该角色的风险点

**Phase C — 跨模型交叉验证（铁律 4）**

使用不同模型家族交叉验证，避免单一模型偏见：

```
ask_model(task_type="role_cross_validation", model_family="gemini")
```

发送内容：Phase B 的分析结果 + 原始搜索数据

交叉验证关注点：
- Phase B 的评分是否过于乐观/悲观？
- 是否遗漏了关键风险？
- 是否存在 Phase B 未发现的反面证据？

将交叉验证结果合并到最终输出，标注分歧点。

→ 展示角色验证摘要表，用户确认

---

### Step 4: 商业模式压力测试

输入：Step 1 提取的 `business_model` + Step 2-3 的验证数据

**Phase A — 定价基准搜索**

使用 `mcp__plugin_product-design_ai-gateway__brave_web_search`：

| 搜索轮次 | 关键词策略 |
|---------|-----------|
| 第 1 轮 | `"{product_type}" pricing model benchmark` |
| 第 2 轮 | `"{competitor_name}" pricing plans revenue` |
| 第 3 轮 | `"{business_model_type}" unit economics SaaS metrics` |
| 第 4 轮 | `"{problem_domain}" willingness to pay survey` |

**Phase B — 压力测试分析**

使用 `mcp__plugin_product-design_ai-gateway__ask_model` 进行压力测试：

```
ask_model(task_type="business_model_stress_test", model_family="gpt")
```

发送内容：商业模式定义 + 定价基准搜索结果 + 竞品定价信息

压力测试维度：

1. **收入模式可行性** — 该收费模式在同类产品中是否被验证？
2. **成本结构现实性** — 关键成本项（人力/基础设施/获客）是否有行业基准支撑？
3. **单位经济学可行性** — LTV/CAC 比率、毛利率是否在合理区间？
4. **支付意愿证据** — 目标用户是否有为类似产品付费的历史？

**Phase C — 跨模型验证**

```
ask_model(task_type="business_model_cross_validation", model_family="gemini")
```

发送内容：Phase B 的分析结果 + 定价基准数据

输出：
- `model_viability_score` — 模式可行性评分（1-10）
- `pricing_benchmarks[]` — 定价基准数据（附来源 URL）
- `cost_risks[]` — 成本风险点
- `unit_economics` — 单位经济学估算
  - `estimated_ltv_range` — LTV 估算范围
  - `estimated_cac_range` — CAC 估算范围
  - `gross_margin_benchmark` — 行业毛利率基准
- `willingness_to_pay_evidence[]` — 支付意愿证据

→ 展示商业模式压力测试摘要，用户确认

---

### Step 5: 汇总与建议

输入：Step 2-4 的全部验证结果

**Phase A — 聚合计算**

1. 汇总所有验证维度，计算 `overall_confidence`（1-10）：
   - 竞品矩阵覆盖度（≥5 个竞品/替代方案 → 加分）
   - 角色平均可行性评分（均值 ≥4 → 加分）
   - 商业模式可行性评分（≥7 → 加分）
   - 跨模型一致性（分歧少 → 加分）
   - 证据有来源比例（≥80% → 加分）

2. 分类整理：
   - `validated_assumptions[]` — 被证据确认的假设
   - `risky_assumptions[]` — 缺乏证据或被反驳的假设
   - `pivot_suggestions[]` — 如果 `overall_confidence < 5`，生成方向调整建议
   - `recommended_refinements[]` — 在进入 product-map 前建议的概念调整

**Phase B — 用户决策**

展示验证摘要：

```
╔══════════════════════════════════════════════╗
║  市场验证报告摘要                              ║
╠══════════════════════════════════════════════╣
║  综合信心指数: 7/10                            ║
║  竞品覆盖: 5 个（3 直接 + 2 替代）              ║
║  角色验证: 3/4 角色可行性 ≥4                    ║
║  商业模式: 可行性 7/10                          ║
║                                              ║
║  已验证假设: 6 条                              ║
║  高风险假设: 2 条                              ║
║  建议调整: 3 条                                ║
╚══════════════════════════════════════════════╝
```

**AskUserQuestion**（单选）：

问题：「验证结果已汇总，请选择下一步操作：」

| 编号 | 选项 | 说明 |
|------|------|------|
| 1 | 确认，进入 product-map | 对验证结果满意，继续推进 |
| 2 | 查看详细报告后再决定 | 展开完整验证数据 |
| 3 | 回到 product-concept 调整 | 根据风险假设调整产品概念 |

**Phase C — 写入输出**

写入 `.allforai/market-validate/` 目录：

1. `market-validation.json` — 完整结构化验证结果（机器可读）
2. `competitor-matrix.json` — 详细竞品分析（Step 2 已写入，此处更新汇总标记）
3. `validation-report.md` — 人类可读验证报告

---

## 输出文件结构

```
.allforai/market-validate/
├── market-validation.json    # 完整结构化验证结果
├── competitor-matrix.json    # 详细竞品分析
└── validation-report.md      # 人类可读验证报告
```

### market-validation.json Schema

```json
{
  "version": "1.0.0",
  "generated_at": "ISO8601",
  "concept_ref": "product-concept.json",
  "market_validation": {
    "competitor_matrix": [
      {
        "name": "竞品名称",
        "positioning": "市场定位",
        "pricing": "定价模式",
        "strengths": ["优势1"],
        "weaknesses": ["劣势1"],
        "source_url": "https://..."
      }
    ],
    "market_signals": {
      "trend_direction": "rising | stable | declining",
      "maturity": "emerging | growing | mature | declining",
      "user_demand_evidence": [
        { "description": "...", "source_url": "https://..." }
      ],
      "market_size_indicators": {
        "description": "...",
        "source_url": "https://..."
      }
    },
    "alternative_solutions": [
      {
        "description": "用户现有替代方案",
        "user_segment": "使用人群",
        "limitations": ["局限性"],
        "source_url": "https://..."
      }
    ]
  },
  "role_validation": [
    {
      "role_id": "R1",
      "role_name": "角色名称",
      "viability_score": 4,
      "evidence": [
        { "description": "...", "source_url": "https://..." }
      ],
      "risks": ["风险1"],
      "cross_model_review": {
        "model_family": "gemini",
        "score_adjustment": 0,
        "additional_risks": [],
        "disagreements": []
      }
    }
  ],
  "business_model_validation": {
    "model_viability_score": 7,
    "pricing_benchmarks": [
      { "competitor": "...", "pricing": "...", "source_url": "https://..." }
    ],
    "cost_risks": ["成本风险1"],
    "unit_economics": {
      "estimated_ltv_range": "$X - $Y",
      "estimated_cac_range": "$X - $Y",
      "gross_margin_benchmark": "XX%",
      "source_urls": ["https://..."]
    },
    "willingness_to_pay_evidence": [
      { "description": "...", "source_url": "https://..." }
    ]
  },
  "summary": {
    "overall_confidence": 7,
    "validated_assumptions": [
      { "assumption": "...", "evidence_summary": "...", "source_urls": ["..."] }
    ],
    "risky_assumptions": [
      { "assumption": "...", "risk_description": "...", "evidence_gap": "..." }
    ],
    "pivot_suggestions": [
      { "direction": "...", "rationale": "...", "evidence": "..." }
    ],
    "recommended_refinements": [
      { "area": "...", "suggestion": "...", "priority": "high | medium | low" }
    ]
  }
}
```

### validation-report.md 模板

```markdown
# 市场验证报告

## 综合评估
- 信心指数: X/10
- 验证日期: YYYY-MM-DD

## 竞品格局
（竞品矩阵表格 + 关键发现）

## 角色验证
（每角色可行性评分 + 关键证据 + 风险）

## 商业模式
（可行性评分 + 定价基准 + 风险点）

## 结论与建议
- 已验证假设
- 高风险假设
- 建议调整
```

> 注意：Markdown 报告是人类可读摘要，不重复 JSON 中的完整数据。

---

## 写入时机

**用户确认后才写入磁盘。** Step 2-4 各产出中间结果，Step 5 汇总后展示摘要，等用户确认后才将全部文件写入 `.allforai/market-validate/` 目录。

---

## 防御性规范

> 通用模式定义见 `docs/defensive-patterns.md`，以下为本技能的具体应用。

### 加载校验
- **`product-concept.json`**：加载时验证 JSON 合法性。解析失败 → 提示用户重新运行 `/product-concept`。
- **必需字段检查**：`problem_domain`、`roles`、`business_model` 缺一不可。缺失 → 提示用户补全产品概念。

### 零结果处理
- **Brave Search 连续 3 轮无有用结果**：切换为 ask_model 纯分析模式 — 基于 AI 知识分析，标记 `evidence_mode: "model_only"`，告知用户「该方向公开信息较少，已切换为模型分析模式，结论仅供参考」。
- **竞品搜索不足 3 个直接竞品**：扩大搜索范围（间接竞品、相邻领域），如仍不足 → 标记 `competitor_coverage: "insufficient"`，在报告中明确说明。

### Brave Search 故障
- **工具不可用**：告知用户「Brave Search 暂不可用」→ 提供选项：(a) 仅使用 ask_model 进行分析（标记 `evidence_mode: "model_only"`）(b) 用户手动提供竞品信息和市场数据。
- **工具正常但无有用结果**：按搜索策略换关键词重试一轮 → 仍无结果 → 告知用户「该方向公开信息较少」，继续流程。

### 上游过期检测
- 加载 `product-concept.json` 时记录 `generated_at` 时间戳。
- 如果 `market-validation.json` 已存在且其 `concept_ref` 的 `generated_at` 与当前概念文件不同 → 提示「产品概念已更新，建议重新验证」。

---

## 铁律

### 1. 每条结论必须附带来源 URL，无来源标记 `[UNVERIFIED]`

所有搜索结果和分析结论必须附带 `source_url`。来自 ask_model 的分析结论如无搜索来源支撑，标记 `[UNVERIFIED]`。不编造 URL。

### 2. 不替用户做 Go/No-Go 决策，只呈现证据和风险

验证结果只展示数据、证据、评分和风险。`overall_confidence` 是参考指标，不是决策结论。最终是否继续推进产品由用户决定。

### 3. 竞品矩阵至少覆盖 3 个直接竞品 + 2 个替代方案

直接竞品：解决相同问题域的产品。替代方案：用户当前解决同一问题的其他方式（包括手工流程、Excel、竞品的某个功能模块等）。不足时扩大搜索范围，实在不足则标记 `competitor_coverage: "insufficient"` 并说明原因。

### 4. 角色验证必须用不同模型交叉验证

Step 3 Phase B 使用一个模型家族（如 gpt）分析，Phase C 必须使用不同模型家族（如 gemini）交叉验证。两个模型的评分差异 ≥2 分时，在输出中标注分歧并由主模型裁决。

### 5. 商业模式压力测试必须包含定价基准数据

Step 4 必须搜索并呈现至少 3 个竞品的定价信息作为基准。如搜索不到具体定价数据，必须标记 `pricing_data: "limited"` 并说明信息来源限制。
