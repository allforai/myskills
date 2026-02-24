# Step 2: 必要性评估

> 对每个功能从三个维度评估必要性，给出 CORE / DEFER / CUT 初步分类。

---

## 1. 分类规则

| 分类 | 条件 | 含义 | 处理 |
|------|------|------|------|
| **CORE** | 核心场景必需 + 被依赖/复杂度合理 | 不可移除 | 保留 |
| **DEFER** | 有价值但当前阶段非必需 | 建议延后 | 标注推荐时机 |
| **CUT** | 无场景归属或复杂度远超价值 | 建议移除 | 从需求移除或归档 |

核心原则：**初步分类由算法给出，最终定性由用户确认。**

---

## 2. 三维评估模型

每个功能从三个维度打分，综合判定分类。

### Dimension A: 场景关联度

衡量该功能与用户场景的关联强度。

| Signal | Score | Meaning |
|--------|-------|---------|
| core_feature of 1+ scenarios | **strong** | Essential for user workflow |
| related_feature of 1+ scenarios | **medium** | Supporting but not essential |
| orphan (no scenario) | **weak** | No clear user need |

判定逻辑:
- 查找 Step 1 scenario-feature 映射，确认功能是否出现在任何场景的 `core_features` 或 `related_features` 中
- 出现在 `core_features` 中 → strong
- 仅出现在 `related_features` 中 → medium
- 不出现在任何场景中 → weak (orphan)

### Dimension B: 依赖程度

衡量该功能被其他功能或模块依赖的程度。

- Static analysis: Grep for feature's component/API references across codebase
- **High** (3+ dependents) → cannot prune safely
- **Medium** (1-2 dependents) → prune with caution
- **Low** (0 dependents) → safe to prune
- For planned-only features: dependency = low by definition

判定逻辑:
1. 对已实现功能 — 搜索其导出的 component、API endpoint、shared utility 在其他模块中的 import/调用次数
2. 对仅计划功能 — 尚未实现，无代码依赖，dependency 固定为 low
3. 对同时存在功能 — 同已实现功能处理

### Dimension C: 复杂度比

衡量功能的实现复杂度与其场景价值是否匹配。

Signals:
- `files_involved` — 涉及的文件数量
- `endpoints_count` — API 端点数量
- `special_tech` — 是否使用 WebSocket、cron、第三方集成、复杂状态管理等

Compare to scenario weight:
- High complexity + weak scenario → **excessive** (strong CUT signal)
- High complexity + strong scenario → **justified** (CORE)
- Low complexity + any scenario → **cheap** (keep，维护成本低)

判定阈值:

| 复杂度 | 条件 |
|--------|------|
| **high** | files_involved > 5 或 endpoints > 3 或 special_tech = true |
| **low** | files_involved <= 5 且 endpoints <= 3 且 special_tech = false |

---

## 3. 分类算法

基于三个维度的组合，给出初步分类:

```
strong scenario + any dependency + any complexity → CORE
medium scenario + high dependency               → CORE
medium scenario + low dependency + low complexity  → CORE
medium scenario + low dependency + high complexity → DEFER
weak scenario + high dependency                  → needs_confirmation
weak scenario + low dependency                   → CUT
planned_only + weak scenario                     → CUT
planned_only + medium scenario                   → DEFER
```

说明:
- `needs_confirmation` 不是最终分类，必须交由用户定性。场景弱但依赖高说明存在架构耦合，需要用户判断是功能本身重要还是耦合不合理。
- `planned_only` 指 source_type 为 planned 的功能（仅在需求文档中存在，代码未实现）。

---

## 4. 已实现功能的特殊处理

对 source_type 为 `implemented` 或 `both` 且被分类为 CUT 的功能:

1. 标记为 CUT 但附注 **"已实现"**
2. 包含复杂度信息（files_involved、endpoints_count），用于评估移除成本
3. **不直接建议删除代码** — 仅呈现分类结果，由用户决定是否移除

示例输出:

```
F-017 实时通知推送
  分类: CUT (已实现)
  场景关联度: weak (无场景归属)
  依赖程度: low (0 dependents)
  复杂度: high (WebSocket, 8 files, 2 endpoints)
  说明: 代码已存在，移除涉及 8 个文件。是否移除由用户决定。
```

原则：**算法只负责分类，不负责决定代码去留。**

---

## 5. 用户确认点

分类完成后，逐项向用户呈现结果并请求确认。

呈现格式:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
F-017 实时通知推送
  来源: implemented (仅代码中存在)
  场景关联度: weak — 未出现在任何场景中
  依赖程度: low — 0 个功能依赖此功能
  复杂度比: excessive — 8 files, 2 endpoints, WebSocket
  ─────────────────────────────────────
  初步分类: CUT
  理由: 无场景归属，复杂度高，0 个依赖
  ─────────────────────────────────────
  请确认: [CORE]  [DEFER]  [CUT]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

用户操作:
- 选择 `[CORE]` / `[DEFER]` / `[CUT]` 确认或修改分类
- 如果用户选择与算法建议不同的分类，记录用户的理由到 `prune-decisions.json`

```json
{
  "decisions": [
    {
      "feature_id": "F-017",
      "feature_name": "实时通知推送",
      "algorithm_classification": "CUT",
      "user_classification": "CORE",
      "user_reason": "v2.0 核心功能，已和客户确认需要",
      "decided_at": "2024-01-15",
      "decided_by": "user"
    }
  ]
}
```

---

## 6. 输出格式

输出文件: `assessment.json`

```json
{
  "assessments": [
    {
      "feature_id": "F-001",
      "feature_name": "用户登录",
      "source_type": "both",
      "classification": "CORE",
      "dimensions": {
        "scenario_relevance": "strong",
        "dependency": "high",
        "complexity_ratio": "justified"
      },
      "reasoning": "S-001(用户管理)的核心功能，被 F-002、F-003 等 5 个功能依赖",
      "evidence": "src/pages/Login.tsx:1, src/modules/auth/auth.controller.ts:15",
      "user_override": null,
      "confirmed_by_user": false
    }
  ],
  "summary": { "CORE": 12, "DEFER": 3, "CUT": 5 },
  "confirmed_by_user": false
}
```

字段说明:

| 字段 | 类型 | 说明 |
|------|------|------|
| `feature_id` | string | 功能 ID，F- 前缀 |
| `feature_name` | string | 功能名称 |
| `source_type` | enum | `planned` / `implemented` / `both` |
| `classification` | enum | CORE / DEFER / CUT |
| `dimensions` | object | 三维评估结果 |
| `dimensions.scenario_relevance` | enum | strong / medium / weak |
| `dimensions.dependency` | enum | high / medium / low |
| `dimensions.complexity_ratio` | enum | justified / cheap / excessive |
| `reasoning` | string | 分类理由，遵循词汇纪律 |
| `evidence` | string | 代码证据 (file:line)，planned-only 为 null |
| `user_override` | object \| null | 用户修改记录，包含 `original`、`reason` |
| `confirmed_by_user` | boolean | 全部确认后为 true，Step 3 才能执行 |

---

## 7. 词汇纪律

Reasoning 文本必须使用受控词汇，禁止主观判断词。

### 允许的表述:

| 场景 | 正确表述 | 说明 |
|------|---------|------|
| 场景关联 | "S-001 的核心功能" | 引用场景 ID |
| 场景关联 | "出现在 S-001、S-003 的 related_features 中" | 具体列出 |
| 无场景 | "未出现在任何场景中" | 客观事实 |
| 依赖 | "被 F-002、F-003 等 5 个功能依赖" | 列出依赖方 |
| 依赖 | "0 个功能依赖此功能" | 客观计数 |
| 复杂度 | "涉及 8 个文件、2 个端点，使用 WebSocket" | 客观数据 |

### 禁止的表述:

| 禁止 | 原因 | 替代 |
|------|------|------|
| "应该保留" | 主观判断 | "S-001 的核心功能" (让数据说话) |
| "建议移除" | 越权决策 | "无场景归属，0 个依赖" (呈现事实) |
| "不够重要" | 价值判断 | "未出现在任何场景中" (客观) |
| "这个功能很有价值" | 主观评价 | "出现在 3 个场景的 core_features 中" (数据) |
| "可以考虑" | 模糊建议 | 禁止使用，直接给出分类 |

---

## 8. 与其他步骤的关系

```
Step 1 (功能归类) ──→ Step 2 (必要性评估) ──→ 用户确认 ──→ Step 3 (精简方案)
                           │                      │
                           │                      └─→ prune-decisions.json (持久化)
                           │
                           └─→ assessment.json (输出)
```

Step 3 只处理 `confirmed_by_user: true` 的结果。未确认的结果会阻塞后续流程。

Step 1 提供的输入:
- 功能清单 (feature_id, feature_name, source_type)
- 场景-功能映射 (scenario → core_features, related_features)

Step 2 输出供 Step 3 使用:
- 每个功能的分类 (CORE / DEFER / CUT)
- 分类依据和证据
- 用户确认状态

---

> **铁律速查** — 详见 `${CLAUDE_PLUGIN_ROOT}/skills/feature-prune.md` 的铁律章节。
> 本步骤强相关：**用户定性**（所有分类最终由用户确认，算法仅给出初步建议）、**词汇纪律**（reasoning 只使用受控词汇，禁止主观判断词）。
