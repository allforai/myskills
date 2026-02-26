---
name: feature-prune
description: >
  Use when the user asks to "prune features", "cut unnecessary features",
  "what's redundant", "simplify the product", "what can we remove",
  "功能剪枝", "砍功能", "精简产品", "哪些功能可以去掉", "过度设计",
  "功能太多了", "哪些功能没人用", "功能优先级", "该不该做",
  or mentions removing bloat, deferring low-value features,
  or deciding what to keep vs cut in the current product.
  Requires product-map to have been run first.
version: "2.2.0"
---

# 功能剪枝

> 产品地图里有的，哪些该留、哪些该推迟、哪些该砍？

## 目标

以 `product-map` 为基准，对每个功能点做去留决策：

1. **该不该有？** — 是否服务于核心用户场景？
2. **现在该做吗？** — 当前阶段是否必要？
3. **做得是不是太多了？** — 复杂度是否远超实际使用频次？

最终输出三类标记：`CORE`（必须保留）/ `DEFER`（推迟）/ `CUT`（移除）。

最终决定权归用户，Claude 只提供分析依据。

---

## 定位

```
product-map（现状+方向）   功能查漏（查缺口）          功能剪枝（查多余）
产品应该长什么样           地图说有的，现在有没有        地图里有的，该不该留
基础层                    基于 product-map           基于 product-map
```

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/product-map.json`。

---

## 快速开始

```
/feature-prune           # 完整剪枝（频次+场景+竞品）
/feature-prune quick     # 快速剪枝，跳过 Step 3（竞品参考），运行 Step 1 → Step 2 → Step 4 → Step 5。
/feature-prune scope 用户管理  # 只剪枝指定模块
/feature-prune refresh  # 清除决策缓存，完整重跑
```

## 动态趋势补充（WebSearch）

除经典理论外，建议在本技能执行时补充近 12–24 个月的优先级与取舍实践：

- 搜索关键词示例：`"RICE prioritization" + 产品类型 + "case study" + 2025`
- 搜索关键词示例：`"feature pruning" + "product strategy" + "real examples"`
- 来源优先级：官方规范/权威研究 > 一线团队实践 > 社区经验
- 决策留痕：记录 `ADOPT|REJECT|DEFER` 与理由，避免只参考不落地

建议将来源写入：`.allforai/product-design/trend-sources.json`（跨阶段共用）。

## 中段经理理论支持（可选增强）

为让 CORE / DEFER / CUT 决策具备可审计的管理依据，可在现有流程上叠加以下框架：

| 理论/框架 | 对应步骤 | 落地方式 |
|-----------|----------|----------|
| RICE（Reach/Impact/Confidence/Effort） | Step 1/4 | 为候选任务补充 RICE 分，作为 DEFER 与 CUT 的量化依据 |
| MoSCoW | Step 4 | 将用户最终决策映射为 Must/Should/Could/Won't，便于迭代计划沟通 |
| Kano | Step 2/3 | 区分基本型/期望型/兴奋型，避免误砍高价值低频功能 |
| Cost of Delay | Step 4/5 | 对 DEFER 项补充延迟成本说明，防止长期积压变成隐形风险 |

> 原有 CORE / DEFER / CUT 机制保持不变；上述框架仅增加解释力，不改变默认执行路径。

**scope 模式**：运行与 full 相同的 Step 序列，但仅处理 `task-inventory.json` 中 `task_name` 包含指定关键词的任务。前提：`frequency-tier.json` 已存在（需先跑过一次 full 或 quick）。

**refresh 模式**：将 `prune-decisions.json` 重命名为 `.bak` 备份，从 Step 1 开始完整重新运行，忽略所有已有决策缓存。

---

## 工作流

```
前置：两阶段加载
      Phase 1 — 加载索引：
        检查 .allforai/product-map/task-index.json
          存在 → 加载索引（< 5KB），获取任务 id/task_name/frequency/owner_role/risk_level + 模块分组
          不存在 → 回退到 Phase 2 全量加载（向后兼容）
      Phase 2 — 按需加载完整数据：
        加载 .allforai/product-map/product-map.json
        若 product-map.json 也不存在 → 提示用户先运行 /product-map，终止
      ↓
Step 1: 频次过滤（帕累托）
      ↓ 用户确认频次评估
Step 2: 场景对齐
      基于 .allforai/screen-map/screen-map.json（若不存在则跳过，说明原因）
      ↓ 用户确认场景归属
Step 3: 竞品参考（可选）
      ↓ 用户确认参考结论
Step 4: 用户分类决策（CORE / DEFER / CUT）
      ↓
Step 5: 生成剪枝任务清单
```

---

### Step 1：频次过滤（帕累托）

**数据加载**：若 `task-index.json` 存在，直接读取索引中每个任务的 `frequency` 字段完成分层（索引已含 frequency，无需加载 50KB+ 的 task-inventory.json）。若索引不存在，回退到读取 `task-inventory.json`。若 `screen-map.json` 存在，同时读取按钮级别的频次数据；若不存在，仅按任务级别分层。

按频次分层：

| 频次 | 占比目标 | 策略 |
|------|----------|------|
| 高频 | ~20% 的功能 | 受保护，轻易不砍 |
| 中频 | ~30% 的功能 | 评估场景价值再决定 |
| 低频 | ~50% 的功能 | 重点剪枝候选 |

**低频功能自动进入剪枝候选名单**，但不自动标记 CUT，等待 Step 2 场景对齐验证。

输出：`.allforai/feature-prune/frequency-tier.json`

```json
[
  {
    "task_id": "T001",
    "task_name": "{任务名}",
    "frequency": "高 | 中 | 低",
    "tier": "protected | candidate | review",
    "data_points": "频次判定依据"
  }
]
```

- `protected`：高频，受保护不剪枝
- `candidate`：低频，进入剪枝候选
- `review`：中频，需进一步评估

---

### Step 2：场景对齐

**数据加载**：Step 1 已将任务分为 `protected`（高频）、`candidate`（低频）和 `review`（中频）三层。Step 2 只需对 `candidate` 和 `review` 任务做深度分析，此时才按需加载这些任务的完整数据（从 `task-inventory.json` 中仅读取对应任务 ID 的条目），避免全量加载。

**前置检查**：`.allforai/screen-map/screen-map.json` 是否存在
- 不存在 → 跳过 Step 2，在报告中注明：「Step 2 已跳过，需先运行 /screen-map 生成界面地图。场景对齐分析无法执行，请直接进入 Step 3。」
- 存在 → 对剪枝候选中的每个功能执行以下检查

对 `candidate`（低频）和 `review`（中频）两个分层中的每个功能，检查：

**问题 A：是否服务于核心场景？**

**场景匹配方法**：读取 `screen-map.json` 中每个界面的 `primary_action` 和 `pareto.high_freq_actions`。任务的主操作出现在高频操作列表中 → 核心场景；出现在界面但非高频 → 次要场景；未出现在任何界面 → 无对应场景。若 `screen-map.json` 不存在，跳过此问题，仅标注「需 screen-map」。

将功能与 `.allforai/screen-map/screen-map.json` 中的界面数据对比：

| 场景关联 | 含义 |
|----------|------|
| 直接服务核心场景 | 保留理由充分，倾向 CORE |
| 服务次要场景 | 评估场景价值，倾向 DEFER |
| 无场景关联 | 无法说明存在理由，倾向 CUT |

**问题 B：复杂度是否与频次匹配？**

**复杂度推导**：从 `task-inventory.json` 综合评估 — `main_flow` 步骤数 ≥ 5 或 `rules` 数量 ≥ 3 或 `exceptions` 数量 ≥ 3 → 高复杂度；步骤数 ≤ 2 且 rules ≤ 1 → 低复杂度；其余为中复杂度。

| 情况 | 判断 |
|------|------|
| 高频 + 实现简单 | CORE |
| 低频 + 实现复杂 | CUT 候选（投入产出严重失衡） |
| 低频 + 实现简单 | DEFER 候选（暂时保留，后续观察） |
| 高频 + 实现复杂 | 保留，但可考虑简化实现 |

**问题 C：跨部门依赖是否值得？**

`cross_dept=true` 的低频任务，维护成本高、使用频次低，优先剪枝候选。

输出：`.allforai/feature-prune/scenario-alignment.json`

```json
[
  {
    "task_id": "T001",
    "task_name": "{任务名}",
    "tier": "candidate",
    "question_a": "core | secondary | none",
    "question_b": "match | over_engineered | under_served",
    "question_c": "standalone | dependent",
    "preliminary_decision": "CORE | DEFER | CUT",
    "reason": "综合判定理由"
  }
]
```

---

### Step 3：竞品参考（可选，quick 模式跳过）

对标同类产品同阶段的功能范围。仅作参考，不作为唯一判断依据。

**操作方法**：
1. 询问用户提供 1–3 个同类竞品名称（若用户不确定，通过 WebSearch 搜索「{行业} + {产品类型} + alternatives」获取）
2. 通过 WebSearch 查询每个竞品的公开功能列表（官网 feature page、changelog、帮助文档）
3. 将竞品功能与当前产品 task-inventory 逐一对照，标注：竞品有/我们也有、竞品有/我们没有、我们有/竞品没有
4. 竞品普遍没有的功能 → 支持 CUT/DEFER 判断；竞品普遍有的功能 → 支持 CORE 判断

| 对比结果 | 参考意义 |
|----------|----------|
| 竞品同阶段普遍有 | 砍掉有竞争风险，提示用户注意 |
| 竞品同阶段普遍没有 | 可能是差异化，也可能是过早投入 |
| 竞品有但用法不同 | 记录差异，由用户判断 |

输出：`.allforai/feature-prune/competitive-ref.json`

```json
{
  "competitors": ["竞品A", "竞品B"],
  "analysis_date": "2024-01-15",
  "features": [
    {
      "task_id": "T001",
      "task_name": "{任务名}",
      "competitor_coverage": "all_have | some_have | none_have",
      "notes": "备注"
    }
  ]
}
```

---

### Step 4：用户分类决策

展示每个功能的分析依据，用户逐条做出最终决定：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 feature-prune 分析结果决定，不限行业。

```
功能：退款单批量导出
频次：低
场景关联：财务对账（次要场景）
竞品：同类产品早期均无此功能
复杂度：中

建议：DEFER
理由：低频 + 非核心场景 + 竞品同阶段无 + 实现成本中等

用户决定：[ CORE ] [ DEFER ] [ CUT ] [ 跳过，稍后再决定 ]
```

**三类标记含义**：

| 标记 | 含义 | 后续行动 |
|------|------|----------|
| `CORE` | 必须保留，核心竞争力或高频刚需 | 无需操作 |
| `DEFER` | 有价值但当前阶段非必需 | 从当前迭代移除，记录到 backlog |
| `CUT` | 不服务核心场景或复杂度远超价值 | 标记移除，生成清理任务 |

输出：`.allforai/feature-prune/prune-decisions.json`

---

### Step 5：生成剪枝任务清单

将 `DEFER` 和 `CUT` 的决定转换为可执行任务：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 feature-prune 分析结果决定，不限行业。

```json
{
  "id": "PRUNE-001",
  "title": "退款单批量导出 → DEFER",
  "decision": "DEFER",
  "affected_tasks": ["T012"],
  "affected_screens": ["S008"],
  "reason": "低频（月均 2 次），非核心场景，当前阶段竞品均无",
  "action": "从当前迭代移除，迁移到 backlog，6 个月后重新评估",
  "risk": "低（财务可用手动导出替代）"
}
```

```json
{
  "id": "PRUNE-002",
  "title": "数据总览页「自定义仪表盘」→ CUT",
  "decision": "CUT",
  "affected_tasks": ["T015", "T016"],
  "affected_screens": ["S002"],
  "reason": "低频 + 实现复杂 + 无场景关联，过度设计",
  "action": "移除相关功能点，通知开发团队清理代码",
  "risk": "低（无用户反馈依赖此功能）"
}
```

输出：
- `.allforai/feature-prune/prune-tasks.json` — 剪枝任务清单
- `.allforai/feature-prune/prune-report.md` — 可读报告
- 读取 Step 4 的 `prune-decisions.json`，不修改

---

## 输出文件结构

```
.allforai/feature-prune/
├── frequency-tier.json      # Step 1: 频次分层结果
├── scenario-alignment.json  # Step 2: 场景对齐结果
├── competitive-ref.json     # Step 3: 竞品参考（可选）
├── prune-decisions.json     # Step 4: 用户分类决策日志
├── prune-tasks.json         # Step 5: 剪枝任务清单
└── prune-report.md          # 可读报告
```

### decisions.json 通用格式

```json
[
  {
    "step": "Step 4",
    "item_id": "T001",
    "item_name": "{任务名}",
    "decision": "CORE | DEFER | CUT",
    "reason": "用户决策理由",
    "decided_at": "2024-01-15T10:30:00Z"
  }
]
```

**加载逻辑**：每次运行前检查 decisions.json，已有决策的条目跳过确认直接沿用。`/feature-prune refresh` 将 decisions.json 重命名为 `.bak` 后重新运行。

---

## 防御性规范

> 通用模式定义见 `docs/defensive-patterns.md`，以下为本技能的具体应用。

### 加载校验
- **`prune-decisions.json`**：加载时用 `python -m json.tool` 验证 JSON 合法性。解析失败 → 检查 `.bak` → 提示恢复或重新运行 `/feature-prune refresh`。
- **`frequency-tier.json`**（scope 模式前提）：加载时验证 JSON 合法性。解析失败或不存在 → 明确提示「需先运行 /feature-prune full 或 /feature-prune quick 生成频次分层数据」，终止 scope 模式。

### 零结果处理
- **全部任务为 CORE（无可剪枝项）**：✓ 明确告知「所有任务均为核心功能（高频或核心场景关联），无剪枝建议（共评估 {N} 个任务）」。
- **scope 模式匹配 0 任务**：明确告知「关键词 "{关键词}" 未匹配任何任务」，列出 frequency-tier.json 中现有任务名称供参考。

### 规模自适应
- **阈值**：以任务数为计量对象。small ≤30 / medium 31–80 / large >80。
- **small**（≤30 任务）：逐任务展示 CORE/DEFER/CUT 建议，逐步确认。
- **medium**（31–80 任务）：按模块分组展示模块级摘要，用户确认模块级。
- **large**（>80 任务）：按模块 × 频次矩阵展示 — 高频自动 CORE，低频+低风险建议 CUT，用户确认边界项（中频或有争议项）。

### CUT 决策安全检查
- **业务流引用检查**：CUT 决策生效前，检查 `business-flows.json` 是否引用该任务 → 有引用 → ⚠ 警告「任务 {task_id} ({task_name}) 被业务流 {flow_name} 引用，CUT 将导致该流断裂」，要求用户二次确认。
- **CUT 高频任务保护**：若用户尝试 CUT `frequency=高` 的任务 → ⚠ 强提示「此任务为高频功能，CUT 影响范围大」，不阻断但确保用户知情。

### WebSearch 故障
- **Step 3 竞品搜索**：工具不可用 → 告知用户「⚠ WebSearch 暂不可用，竞品参考分析无法执行」→ 跳过 Step 3，在报告中标注「竞品参考：未执行（WebSearch 不可用）」。
- **某竞品搜索无结果**：告知用户「竞品 {名称} 公开功能信息较少」，继续分析其余竞品。

### 上游过期检测
- **`task-index.json` / `task-inventory.json`**：加载时比较 `generated_at` 与 `prune-decisions.json` 最新 `decided_at`。上游更新 → ⚠ 警告「task-inventory 在 feature-prune 上次运行后被更新，频次数据可能过期，建议重新运行 /feature-prune refresh」。
- 仅警告不阻断。

---

## 5 条铁律

### 1. 频次是客观依据，不靠感觉

所有剪枝建议必须引用 `product-map` 中的 `frequency` 数据。不能仅凭"感觉没人用"提出剪枝建议。

### 2. 只剪不加

只讨论该不该保留，绝不建议应该增加什么。发现功能缺口请使用 `feature-gap`（功能查漏）。

### 3. CUT 是建议不是执行

标记 `CUT` 只是建议，不触发任何代码删除。实际删除由开发团队根据任务清单执行。

### 4. 用户是最终决策者

Claude 的分类（CORE/DEFER/CUT）是基于数据的建议，用户可以全部推翻。用户说"这个低频功能是战略必要的"，无条件尊重，标记为 `CORE`。

### 5. 高频功能受保护

`frequency=高` 的任务和按钮，不进入剪枝候选，除非用户主动发起。
